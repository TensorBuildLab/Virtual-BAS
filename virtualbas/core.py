"""EmuBAS orchestrator: couples the inner space (EnergyPlus) with the outer space.

One BAS sample (= one EnergyPlus zone time step) executes the following pipeline::

    EnergyPlus truth x_k ──► sensor models ──► observed y_k ──► BAS present values (hold on loss)
          ▲                                                         │
          │                                                         ▼
    EnergyPlus actuators ◄── actuator models / local loops ◄── BAS controllers (+ operator/AI overrides)
                              (faults, set-point translation)

Faults and events modify the sensor models, actuator models, BAS software and the EnergyPlus
physics through :class:`~virtualbas.realworld.faults.InjectionManager`. Everything is labelled.
"""
from __future__ import annotations

import copy
import datetime as dt
import json
import math
import queue
import threading
import time
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import numpy as np

from .bas.alarms import default_rules
from .bas.analytics import Analytics
from .bas.catalog import RHO_AIR, RHO_WATER, Catalog, build_catalog
from .bas.historian import LABEL_BITS, Historian
from .control.sequences import (AHUController, ControlConfig, PlantController, VAVController, geb_battery,
                                geb_zone_offsets, occupied, onpeak_window)
from .engine.runner import EnergyPlusEngine, EngineSpec, Sample
from .model.epjson import load_model, save_model
from .model.prepare import Manifest
from .realworld.faults import REGISTRY, Injection, InjectionContext, InjectionManager, Overlays, catalog as fault_catalog
from .realworld.occupancy import ZoneOccupancy
from .realworld.environment import OuterEnvironment
from .realworld.random_faults import RandomInjector
from .realworld.sensors import SENSOR_CLASSES, FaultOverlay, Sensor, SensorSpec

SPEEDS = {"realtime": 1.0, "1x": 1.0, "2x": 2.0, "10x": 10.0, "60x": 60.0, "360x": 360.0, "max": math.inf}
SOFT_KINDS = ("setpoint", "command", "virtual", "status")
ALL_TIERS = ("standard", "advanced", "next_gen")


def parse_speed(s: Any) -> float:
    if isinstance(s, (int, float)):
        return float(s) if s > 0 else math.inf
    s = str(s).lower().strip()
    if s in SPEEDS:
        return SPEEDS[s]
    if s.endswith("x"):
        s = s[:-1]
    try:
        v = float(s)
        return v if v > 0 else math.inf
    except ValueError:
        return math.inf


def _ok(x) -> bool:
    return x is not None and isinstance(x, (int, float)) and math.isfinite(x)


def _g0(d: dict[str, float], k: str) -> float:
    """Finite value of ``d[k]`` or 0."""
    v = d.get(k)
    return v if _ok(v) else 0.0


def parse_time(v: Any, ref: dt.datetime) -> dt.datetime | None:
    """Absolute ISO time, 'now', or a relative offset such as '+2h', '+3d', '+30m' (from ``ref``)."""
    if v is None or v == "":
        return None
    if isinstance(v, dt.datetime):
        return v
    if isinstance(v, dt.date):
        return dt.datetime(v.year, v.month, v.day)
    s = str(v).strip()
    if s == "now":
        return ref
    if s.startswith("+"):
        num, unit = float(s[1:-1]), s[-1]
        mult = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}[unit]
        return ref + dt.timedelta(seconds=num * mult)
    return dt.datetime.fromisoformat(s)


class Building:
    """A prepared building: model, manifest, point catalog and default configuration."""

    def __init__(self, path: str | Path):
        self.dir = Path(path)
        self.manifest = Manifest.load(self.dir / "manifest.json")
        self.catalog: Catalog = build_catalog(self.manifest)
        self.model_path = self.dir / "model.epJSON"
        self.weather_path = self.dir / self.manifest.weather_file
        cfg_file = self.dir / "building.yaml"
        self.config: dict[str, Any] = {}
        if cfg_file.exists():
            import yaml
            self.config = yaml.safe_load(cfg_file.read_text()) or {}
        model = json.loads(self.model_path.read_text())
        self.people_sched = {n: o.get("number_of_people_schedule_name") for n, o in model.get("People", {}).items()}
        self.light_sched = {n: o.get("schedule_name") for n, o in model.get("Lights", {}).items()}
        self.equip_sched = {n: o.get("schedule_name") for n, o in model.get("ElectricEquipment", {}).items()}
        self.year = int(self.manifest.options.get("year", 2023))

    @property
    def name(self) -> str:
        return self.config.get("name", self.dir.name)


@dataclass
class Override:
    value: float
    priority: int
    source: str
    expires: dt.datetime | None = None


class VirtualBAS:
    def __init__(self, building: str | Path | Building, out_dir: str | Path | None = None,
                 scenario: dict[str, Any] | None = None, speed: Any = "max", seed: int | None = None,
                 realism: float | None = None, record: bool = True, console: bool = False):
        self.b = building if isinstance(building, Building) else Building(building)
        sc = copy.deepcopy(scenario or {})
        self.scenario = sc
        self.seed = int(seed if seed is not None else sc.get("seed", 0))
        self.realism = float(realism if realism is not None else sc.get("realism", 1.0))
        self.rng = np.random.default_rng(self.seed)
        self.speed = parse_speed(sc.get("speed", speed) if speed == "max" and "speed" in sc else speed)
        self.cat = self.b.catalog
        ccfg = dict(self.b.config.get("control", {}))
        ccfg.update(sc.get("control", {}) or {})
        self.ccfg = ControlConfig.from_dict(ccfg)
        self.out_dir = Path(out_dir) if out_dir else None
        self.record = record and self.out_dir is not None
        self.console = console

        # ---------- run period
        opts = self.b.manifest.options
        y = self.b.year
        default_start = dt.datetime(y, int(opts.get("begin_month", 1)), int(opts.get("begin_day", 1)))
        default_end = dt.datetime(y, int(opts.get("end_month", 12)), int(opts.get("end_day", 31)))
        self.start_date = parse_time(sc.get("start"), default_start) or default_start
        self.end_date = parse_time(sc.get("end"), self.start_date) or default_end
        if self.start_date.year != y or self.end_date.year != y:
            self.start_date = self.start_date.replace(year=y)
            self.end_date = self.end_date.replace(year=y)

        # ---------- outer-space objects
        self.inj = InjectionManager()
        self.random = None
        rf = sc.get("random_faults")
        if rf:
            self.random = RandomInjector(rate_per_week=float(rf.get("rate_per_week", 2.0)), seed=int(rf.get("seed", self.seed + 7)))
            if rf.get("types"):
                self.random.menu = {k: v for k, v in self.random.menu.items() if k in rf["types"]}
                self.random.types = list(rf["types"])
        # exposed / recorded point tiers (standard = typical BAS today, advanced, next_gen); truth is always kept
        self.tiers = tuple(sc.get("point_tiers") or self.b.config.get("point_tiers") or ALL_TIERS)
        self._build_sensors(sc.get("sensors", {}))
        self._sensor_list = []
        for pid, sensor in self.sensors.items():
            eq = self.cat.points[pid].equip
            e = self.cat.equipment[eq]
            self._sensor_list.append((pid, sensor, eq, e.parent if e.type == "Zone" else None))
        self._build_controllers()
        env_cfg = dict(self.b.config.get("environment", {}) or {})
        env_cfg.update(sc.get("environment", {}) or {})
        self.env = OuterEnvironment(self, env_cfg)
        self.analytics = Analytics(self.cat)
        occ = sc.get("occupancy", {"stochastic": True})
        self.occ_stochastic = bool(occ.get("stochastic", True))
        self.occ_models: dict[str, ZoneOccupancy] = {}
        self.occ_mobility = float(occ.get("mobility", 0.3))
        self.occ_att_min = float(occ.get("attendance_min", 0.8))
        self.couple_loads = bool(occ.get("couple_plug_loads", False))
        self.alarms = default_rules(self.cat)
        self.overrides: dict[str, dict[int, Override]] = {}
        self.cmd_queue: queue.Queue = queue.Queue()
        self.step_hooks: list[Callable[["VirtualBAS", dt.datetime], None]] = []

        # ---------- runtime state
        self.pv: dict[str, float] = {}           # BAS present values
        self.pv_time: dict[str, dt.datetime] = {}
        self.obs: dict[str, float] = {}
        self.truth: dict[str, float] = {}
        self.cmd: dict[str, float] = {}
        self.labels: dict[str, int] = {}
        self.eplus_cmd: dict[str, float | None] = {}
        self.t: dt.datetime | None = None
        self.step_count = 0
        self.paused = bool(sc.get("start_paused", False))
        self.step_budget = 0
        self._cv = threading.Condition()
        self.lock = threading.RLock()   # guards outer-space state between the E+ thread and API threads
        self._wall_next: float | None = None
        self.finished = False
        self.warmup = True
        self.kpi = {"elec_kwh": 0.0, "gas_kwh": 0.0, "hvac_elec_kwh": 0.0, "unmet_occ_hours": 0.0,
                    "comfort_kh": 0.0, "co2_over_1000_h": 0.0, "steps": 0,
                    "cost_usd": 0.0, "co2_kg": 0.0, "pm25_over_15_h": 0.0, "tvoc_over_500_h": 0.0}
        if "GRID/IMPORT-PWR" in self.cat.points:
            self.kpi.update({"grid_import_kwh": 0.0, "grid_export_kwh": 0.0, "pv_kwh": 0.0, "unserved_kwh": 0.0})
        self._infil_base: dict[str, float] = {}
        self._last_frac: dict[str, float] = {}
        self._last_eplus_htg: dict[str, float] = {}
        self._last_sched: dict[str, float] = {}
        self.history_limit = 0
        self.wall_start = None

        # ---------- historian
        exposed = [p for p in self.cat.points.values() if p.tier in self.tiers or p.kind == "truth"]
        sensor_ids = [p.id for p in exposed if p.kind in ("sensor", "meter")]
        truth_ids = [p.id for p in self.cat.points.values() if p.kind in ("sensor", "meter", "truth")]
        soft_ids = [p.id for p in exposed if p.kind in SOFT_KINDS]
        self.sensor_ids, self.truth_ids, self.soft_ids = sensor_ids, truth_ids, soft_ids
        self.hist = Historian(self.out_dir if self.record else None, sensor_ids, truth_ids, soft_ids)

        # scenario injections
        self.lock = threading.RLock()
        for spec in sc.get("injections", []) or []:
            self.inject(spec, source=spec.get("source", "scenario"), ref=self.start_date)

        # ---------- engine
        self.engine = self._build_engine()

    # ================================================================== construction
    def _build_sensors(self, overrides: dict[str, Any]) -> None:
        self.sensors: dict[str, Sensor] = {}
        for p in self.cat.points.values():
            if p.kind not in ("sensor", "meter"):
                continue
            spec = copy.deepcopy(SENSOR_CLASSES.get(p.sensor_class, SensorSpec()))
            for key, val in (overrides.get(p.sensor_class, {}) or {}).items():
                setattr(spec, key, val)
            for key, val in (overrides.get(p.id, {}) or {}).items():
                setattr(spec, key, val)
            if p.unit == "%":
                spec.lo, spec.hi = 0.0, 100.0
            # independent, reproducible random stream per sensor (common random numbers across scenarios)
            srng = np.random.default_rng([self.seed, 1, zlib.crc32(p.id.encode())])
            self.sensors[p.id] = Sensor(p.id, spec, srng, self.realism)

    def _build_controllers(self) -> None:
        self._ahu_points = {e.id: self.cat.points_of(e.id) for e in self.cat.equipment_of_type("AHU")}
        self.vav: dict[str, VAVController] = {}
        self.ahu: dict[str, AHUController] = {}
        for e in self.cat.equipment.values():
            if e.type == "VAV":
                self.vav[e.id] = VAVController(e.id, e.meta["zone_equip"], e.meta["vmax_m3s"], e.meta["vmin_frac"], self.ccfg)
            elif e.type == "AHU":
                self.ahu[e.id] = AHUController(e.id, e.meta["design_flow_m3s"], e.meta["min_oa_m3s"], self.ccfg)
        self.plant = PlantController(self.ccfg)
        # zone equipment and distributed energy resources
        self.zone_units = [e for e in self.cat.equipment.values() if e.type in ("HeatPump", "PTAC", "Baseboard", "IdealLoads", "ERV")]
        self.pv_systems = self.cat.equipment_of_type("PVSystem")
        self.batteries = self.cat.equipment_of_type("Battery")
        self.der = bool(self.pv_systems or self.batteries) and "GRID/IMPORT-PWR" in self.cat.points
        self._pv_curtail: dict[str, float] = {}
        self._pv_last: dict[str, tuple[float, float]] = {}
        self._dark = False
        self._last_enable: dict[str, float] = {}
        self.geb_mode = ""
        # occupied set points (writable software points)
        self.zone_sp: dict[str, tuple[float, float]] = {}
        for e in self.cat.equipment_of_type("Zone"):
            self.zone_sp[e.id] = (self.ccfg.htg_occ, self.ccfg.clg_occ)

    def _build_engine(self) -> EnergyPlusEngine:
        spec = EngineSpec(variables=dict(self.cat.variables), meters=dict(self.cat.meters), actuators=dict(self.cat.actuators))
        # occupancy / internal gains support
        for pname, sched in self.b.people_sched.items():
            spec.internal[f"NPEOPLE|{pname}".upper()] = ("People Count Design Level", pname)
            if sched:
                spec.variables[f"SCHED|{sched}".upper()] = ("Schedule Value", sched)
        for lname, sched in self.b.light_sched.items():
            spec.internal[f"LIGHTDES|{lname}".upper()] = ("Lighting Power Design Level", lname)
            if sched:
                spec.variables[f"SCHED|{sched}".upper()] = ("Schedule Value", sched)
        for ename, sched in self.b.equip_sched.items():
            spec.internal[f"PLUGDES|{ename}".upper()] = ("Plug and Process Power Design Level", ename)
            if sched:
                spec.variables[f"SCHED|{sched}".upper()] = ("Schedule Value", sched)
        nat = self.b.manifest.native or {}
        for d in (list(nat.get("air_loops", {}).values()) + list(nat.get("zones", {}).values())
                  + list(nat.get("zone_equipment", {}).values()) + list(nat.get("water_heaters", {}).values())):
            for sched in d.values():
                if sched:
                    spec.variables[f"SCHED|{sched}".upper()] = ("Schedule Value", sched)
        for z in self.b.manifest.topo.zones.values():
            spec.internal[f"ZVOL|{z.name}".upper()] = ("Zone Air Volume", z.name)
            spec.internal[f"ZAREA|{z.name}".upper()] = ("Zone Floor Area", z.name)
            if z.infiltration or z.infiltration_window:
                spec.variables[f"INFIL|{z.name}".upper()] = ("Zone Infiltration Current Density Volume Flow Rate", z.name)
        for a in self.cat.equipment_of_type("AHU"):
            fan = a.meta.get("fan")
            if fan:
                spec.internal[f"FANDP|{fan}".upper()] = ("Fan Nominal Pressure Rise", fan)
                spec.internal[f"FANEFF|{fan}".upper()] = ("Fan Nominal Total Efficiency", fan)
        if self.out_dir:
            run_dir = self.out_dir / "eplus"
        else:
            import tempfile
            base = Path.cwd() / ".vbas_runs"
            base.mkdir(parents=True, exist_ok=True)
            run_dir = Path(tempfile.mkdtemp(prefix="run_", dir=base))
        run_dir.mkdir(parents=True, exist_ok=True)
        model = json.loads(self.b.model_path.read_text())
        rp = next(iter(model["RunPeriod"].values()))
        rp.update({"begin_month": self.start_date.month, "begin_day_of_month": self.start_date.day,
                   "end_month": self.end_date.month, "end_day_of_month": self.end_date.day,
                   "begin_year": self.b.year, "end_year": self.b.year})
        model_run = save_model(model, run_dir / "run.epJSON")
        self.run_dir = run_dir
        return EnergyPlusEngine(model_run, self.b.weather_path, run_dir, spec, self._on_step, year=self.b.year,
                                console=self.console)

    # ================================================================== public API (thread safe)
    def inject(self, spec: dict[str, Any], source: str = "human", ref: dt.datetime | None = None) -> Injection:
        with self.lock:
            return self._inject(spec, source, ref)

    def _inject(self, spec: dict[str, Any], source: str = "human", ref: dt.datetime | None = None) -> Injection:
        ref = ref or self.t or self.start_date
        spec = dict(spec)
        start = parse_time(spec.pop("start", "now"), ref) or ref
        end_v = spec.pop("end", None)
        dur = spec.pop("duration", None)
        end = parse_time(end_v, start) if end_v else (parse_time("+" + str(dur).lstrip("+"), start) if dur else None)
        target = spec.pop("target", "building")
        target = self._resolve_target(spec.get("type", ""), target)
        inj = Injection(type=spec.pop("type"), target=target, start=start, end=end,
                        profile=spec.pop("profile", "step"), ramp_s=float(spec.pop("ramp_s", 3600.0)),
                        period_s=float(spec.pop("period_s", 3600.0)), duty=float(spec.pop("duty", 0.5)),
                        params=spec.pop("params", {}) or {}, source=spec.pop("source", source),
                        note=spec.pop("note", ""), created=(self.t or ref).isoformat())
        self.inj.add(inj)
        return inj

    def _resolve_target(self, itype: str, target: str) -> str:
        kind = REGISTRY.get(itype)
        if kind is None:
            raise ValueError(f"Unknown injection type {itype}")
        if kind.target.startswith("point") and target not in self.cat.points:
            raise ValueError(f"Target point '{target}' not found")
        if kind.target.startswith("equip") and target not in self.cat.equipment:
            raise ValueError(f"Target equipment '{target}' not found")
        if kind.target.startswith("zone"):
            if target in self.cat.zone_of_equip:
                return self.cat.zone_of_equip[target]
            names = {z.upper(): z for z in self.b.manifest.topo.zones}
            if target.upper() in names:
                return names[target.upper()]
            if target in ("building", "*", "") and "building" in kind.target:
                return "*"
            raise ValueError(f"Target zone '{target}' not found")
        return target

    def clear(self, inj_id: str) -> bool:
        with self.lock:
            return self.inj.clear(inj_id, self.t or self.start_date)

    def set_random_rate(self, rate_per_week: float, seed: int | None = None) -> None:
        with self.lock:
            if rate_per_week <= 0:
                self.random = None
            else:
                self.random = RandomInjector(rate_per_week=float(rate_per_week), seed=int(seed if seed is not None else self.seed + 7))

    def write(self, point_id: str, value: float | None, priority: int = 8, source: str = "operator",
              duration_s: float | None = None) -> None:
        """BACnet-like priority-array write to a software point. ``value=None`` relinquishes."""
        if point_id not in self.cat.points or self.cat.points[point_id].kind not in SOFT_KINDS:
            raise ValueError(f"{point_id} is not a writable software point")
        with self.lock:
            self._write(point_id, value, priority, source, duration_s)

    def _write(self, point_id, value, priority, source, duration_s) -> None:
        slots = self.overrides.setdefault(point_id, {})
        if value is None:
            slots.pop(int(priority), None)
            return
        exp = (self.t + dt.timedelta(seconds=duration_s)) if (duration_s and self.t) else None
        slots[int(priority)] = Override(float(value), int(priority), source, exp)

    def set_speed(self, s: Any) -> None:
        self.speed = parse_speed(s)
        self._wall_next = None

    def pause(self) -> None:
        with self._cv:
            self.paused = True

    def resume(self) -> None:
        with self._cv:
            self.paused = False
            self._wall_next = None
            self._cv.notify_all()

    def step(self, n: int = 1) -> None:
        with self._cv:
            self.step_budget += int(n)
            self._cv.notify_all()

    def start(self) -> None:
        self.wall_start = time.time()
        self.engine.start()

    def run(self) -> dict[str, Any]:
        self.wall_start = time.time()
        self.engine.run_blocking()
        return self.finish()

    def wait(self) -> dict[str, Any]:
        self.engine.finished.wait()
        return self.finish()

    def stop(self) -> None:
        self.engine.stop()
        self.resume()

    def finish(self) -> dict[str, Any]:
        if not self.finished:
            self.finished = True
            meta = self.metadata()
            self.hist.close(meta)
            if self.out_dir:
                (self.out_dir / "points.json").write_text(json.dumps([p.to_dict() for p in self.cat.points.values()], indent=1))
                (self.out_dir / "injections_table.json").write_text(json.dumps(self.inj.table(), indent=1, default=str))
                (self.out_dir / "sensors.json").write_text(json.dumps(
                    {k: {"class": self.cat.points[k].sensor_class, **s.install_info()} for k, s in self.sensors.items()}, indent=1))
                (self.out_dir / "alarms.json").write_text(json.dumps(self.alarms.history, indent=1))
        return {"kpi": self.kpi, "exit_code": self.engine.exit_code, "error": repr(self.engine.error) if self.engine.error else None,
                "missing": self.engine.missing, "wall_s": (time.time() - self.wall_start) if self.wall_start else None,
                "steps": self.step_count}

    def metadata(self) -> dict[str, Any]:
        return {"building": self.b.name, "start": self.start_date, "end": self.end_date, "seed": self.seed,
                "realism": self.realism, "control": self.ccfg.__dict__, "scenario": self.scenario, "kpi": self.kpi,
                "label_bits": LABEL_BITS, "energyplus": self.b.manifest.energyplus_version,
                "timestep_s": self.engine.dt_seconds, "missing_handles": self.engine.missing}

    # ------------------------------------------------------------------ snapshot for GUI / agents
    def snapshot(self, include_truth: bool = False) -> dict[str, Any]:
        with self.lock:
            return self._snapshot(include_truth)

    def _snapshot(self, include_truth: bool = False) -> dict[str, Any]:
        pts = {}
        for pid in self.sensor_ids:
            v = self.pv.get(pid)
            stale = bool(self.labels.get(pid, 0) & (LABEL_BITS["missing"] | LABEL_BITS["comm_loss"]))
            pts[pid] = [None if v is None or not math.isfinite(v) else round(v, 3), stale]
        for pid in self.soft_ids:
            v = self.cmd.get(pid)
            pts[pid] = [None if v is None or not math.isfinite(v) else round(v, 3), False]
        out = {"time": self.t.isoformat() if self.t else None, "step": self.step_count, "warmup": self.warmup, "speed": self.speed if math.isfinite(self.speed) else "max",
               "paused": self.paused, "finished": self.engine.finished.is_set(), "start": self.start_date.isoformat(),
               "end": self.end_date.isoformat(), "points": pts, "kpi": self.kpi, "alarms": self.alarms.active(),
               "injections": [dict(i.to_dict(), severity=round(i.severity(self.t), 3) if self.t else 0)
                              for i in self.inj.injections.values()],
               "overrides": {k: {p: o.value for p, o in v.items()} for k, v in self.overrides.items() if v},
               "random_rate_per_week": self.random.rate_per_week if self.random is not None else 0.0}
        if include_truth:
            out["truth"] = {k: (None if not _ok(v) else round(v, 3)) for k, v in self.truth.items()}
        return out

    # ================================================================== the step
    def _drain(self) -> None:
        while True:
            try:
                fn = self.cmd_queue.get_nowait()
            except queue.Empty:
                break
            try:
                fn()
            except Exception as e:  # noqa: BLE001
                print("command failed:", e)

    def _pace(self, dt_s: float) -> None:
        with self._cv:
            while self.paused and self.step_budget <= 0 and not self.engine._stop_requested:
                self._cv.wait(timeout=0.2)
            if self.paused and self.step_budget > 0:
                self.step_budget -= 1
        if math.isfinite(self.speed) and not self.paused:
            now = time.time()
            if self._wall_next is None:
                self._wall_next = now
            self._wall_next += dt_s / self.speed
            delay = self._wall_next - now
            if delay > 0:
                # sleep in slices so speed changes / pause take effect quickly
                end = now + delay
                while time.time() < end and not self.engine._stop_requested:
                    time.sleep(min(0.1, end - time.time()))
                    if self.paused or self._wall_next is None:
                        break
            elif delay < -5:
                self._wall_next = now

    def _on_step(self, s: Sample) -> dict[str, float | None]:
        with self.lock:
            out, pace = self._step_locked(s)
        if pace:
            self._pace(s.dt_seconds)
        return out

    def _step_locked(self, s: Sample) -> tuple[dict[str, float | None], bool]:
        t, dts, raw = s.time, s.dt_seconds, s.values
        self.t = t
        warm = s.warmup
        self.warmup = warm
        if not warm:
            self._drain()
            if self.random is not None:
                for inj in self.random.poll(t, self.cat):
                    self.inj.add(inj)
        ctx = InjectionContext(time=t, outdoor_co2_base=self.b.manifest.options.get("outdoor_co2_ppm", 420.0))
        ov, active = self.inj.overlays(t, ctx) if not warm else (Overlays(), [])

        # ---------------- 1. truth
        truth: dict[str, float] = {}
        for pid, fn in self.cat.truth.items():
            try:
                truth[pid] = float(fn(raw, dts))
            except Exception:  # noqa: BLE001
                truth[pid] = math.nan
        self._surrogate_truth(truth, ov)
        self.env.step(t, dts, raw, truth, ov, warm, s.day_of_week)

        # ---------------- 2. sensors -> observations -> present values
        obs, labels = {}, {}
        lost_equips = ov.comm_loss
        LB = LABEL_BITS
        b_missing, b_stuck, b_spike, b_ovr, b_fb, b_fault, b_comm = (LB["missing"], LB["stuck"], LB["spike"], LB["override"],
                                                                    LB["false_binary"], LB["fault"], LB["comm_loss"])
        ideal = warm or self.realism <= 0
        osens = ov.sensor
        pv, pv_time, isfin = self.pv, self.pv_time, math.isfinite
        for pid, sensor, eq, zparent in self._sensor_list:
            x = truth.get(pid, math.nan)
            o = osens.get(pid)
            if ideal and (warm or o is None):
                y, lab = x, None
            else:
                y, lab = sensor.measure(x, dts, o)
            bits = 0
            if lab:
                if lab.get("missing"):
                    bits |= b_missing
                if lab.get("stuck"):
                    bits |= b_stuck
                if lab.get("spike"):
                    bits |= b_spike
                if lab.get("override"):
                    bits |= b_ovr
                if lab.get("false_on") or lab.get("false_off"):
                    bits |= b_fb
            if o is not None and (o.bias or o.gain or o.noise_std or o.p_gb or o.spike_prob):
                bits |= b_fault
            if lost_equips and (eq in lost_equips or (zparent is not None and zparent in lost_equips)):
                y = math.nan
                bits |= b_comm
            obs[pid] = y
            labels[pid] = bits
            if y == y and isfin(y):
                pv[pid] = y
                pv_time[pid] = t
            elif pid not in pv:
                pv[pid] = x if (x == x and isfin(x)) else math.nan

        # ---------------- 3. controllers (observed values only)
        cmd = self._control(t, s.day_of_week, dts, ov, raw)
        for hook in list(self.step_hooks):
            hook(self, t)
        cmd = self._apply_overrides(cmd, t)
        if not warm:
            self.analytics.step(t, dts, self.pv, cmd)

        # ---------------- 4. actuation (local loops, actuator faults, physics faults, occupancy)
        eplus = self._actuate(t, dts, raw, truth, cmd, ov, warm)
        self.engine.weather_offsets = {"tdb": ov.weather_add.get("tdb", 0.0), "rh": ov.weather_add.get("rh", 0.0),
                                       "solar_mult": ov.weather_mult.get("solar", 1.0)}

        self.obs, self.truth, self.cmd, self.labels = obs, truth, cmd, labels
        if warm:
            return eplus, False
        # ---------------- 5. KPIs, alarms, historian
        self._kpi(truth, cmd, dts, t, s.day_of_week)
        self.alarms.evaluate(t, self.pv, cmd)
        self.hist.record(t, obs, truth, cmd, labels, [(i.id, sv) for i, sv in active], archive=not ov.historian_outage)
        self.step_count += 1
        return eplus, True

    # ------------------------------------------------------------------ surrogates
    def _surrogate_truth(self, truth: dict[str, float], ov: Overlays) -> None:
        for a in self.cat.equipment_of_type("AHU"):
            vd = a.meta["design_flow_m3s"]
            v = truth.get(f"{a.id}/SA-F", 0.0)
            v = v if _ok(v) else 0.0
            frac = v / vd if vd else 0.0
            dsp_sp = self.cmd.get(f"{a.id}/DSP-SP", self.ccfg.dsp_design)
            if frac < 0.02:
                dsp = 0.0
            elif frac <= 1.0:
                dsp = dsp_sp
            else:
                dsp = dsp_sp / frac ** 2
            truth[f"{a.id}/DSP"] = dsp
            truth[f"{a.id}/FLT-DP"] = (100.0 + ov.filter_dp_add.get(a.id, 0.0)) * frac ** 2
            # fan vibration: imbalance grows with speed^2, bearing wear (efficiency loss) adds a broadband term
            if f"{a.id}/SF-VIB" in self.cat.points:
                wear = 1.0 - ov.fan_eff_mult.get(a.id, 1.0)
                truth[f"{a.id}/SF-VIB"] = (0.8 + 1.5 * min(1.2, frac) ** 2 + 12.0 * wear) if frac >= 0.02 else 0.05
        for p in self.cat.equipment_of_type("Pump"):
            if f"{p.id}/VIB" in self.cat.points:
                spd = truth.get(f"{p.id}/SPD", 0.0)
                spd = spd / 100.0 if _ok(spd) else 0.0
                truth[f"{p.id}/VIB"] = 0.6 + 1.2 * spd ** 2 if spd > 0.01 else 0.05
        for e in self.cat.equipment.values():
            if e.type in ("Chiller", "Boiler", "CoolingTower") and f"{e.id}/ALM" in self.cat.points:
                truth[f"{e.id}/ALM"] = 1.0 if e.id in ov.trips else 0.0
            if e.type == "Chiller" and f"{e.id}/EVAP-SAT-T" in self.cat.points:
                r = ov.fouling.get(e.id, 1.0)
                plr = truth.get(f"{e.id}/PLR", 0.0)
                plr = plr if _ok(plr) else 0.0
                lwt, cdl = truth.get(f"{e.id}/CHW-LWT", 7.0), truth.get(f"{e.id}/CDW-LWT", 30.0)
                if plr > 0.01 and _ok(lwt) and _ok(cdl):
                    te = lwt - (0.5 + 1.5 * plr) * (1.0 + 2.0 * (1.0 - r))
                    tc = cdl + (0.5 + 2.0 * plr) * (1.0 + 3.0 * (1.0 - r))
                else:
                    te = lwt if _ok(lwt) else 15.0
                    tc = cdl if _ok(cdl) else 20.0
                truth[f"{e.id}/EVAP-SAT-T"], truth[f"{e.id}/COND-SAT-T"] = te, tc
                truth[f"{e.id}/EVAP-P"] = math.exp(15.422 - 2661.0 / (te + 273.15))
                truth[f"{e.id}/COND-P"] = math.exp(15.422 - 2661.0 / (tc + 273.15))
            if e.type == "Boiler" and f"{e.id}/FLUE-T" in self.cat.points:
                r = ov.fouling.get(e.id, 1.0)
                plr = truth.get(f"{e.id}/FIRE-RATE", 0.0)
                plr = plr / 100.0 if _ok(plr) else 0.0
                lwt = truth.get(f"{e.id}/HW-LWT", 60.0)
                lwt = lwt if _ok(lwt) else 60.0
                truth[f"{e.id}/FLUE-T"] = (lwt + (20.0 + 60.0 * plr) * (1.0 + 1.5 * (1.0 / max(r, 0.05) - 1.0))
                                           if plr > 0.01 else 0.5 * (lwt + 25.0))
        for e in self.zone_units:
            if f"{e.id}/ALM" in self.cat.points:
                truth[f"{e.id}/ALM"] = 1.0 if (e.id in ov.trips or e.id in ov.erv_fan_failed) else 0.0
        for e in self.pv_systems:
            if f"{e.id}/ALM" in self.cat.points:
                truth[f"{e.id}/ALM"] = 1.0 if e.id in ov.inverter_trip else 0.0
        for e in self.batteries:
            if f"{e.id}/ALM" in self.cat.points:
                truth[f"{e.id}/ALM"] = 0.0
        if "GRID/OUTAGE" in self.cat.points:
            truth["GRID/OUTAGE"] = 1.0 if ov.grid_outage else 0.0
            imp = truth.get("GRID/IMPORT-PWR", 0.0)
            truth["GRID/UNSERVED-KW"] = max(0.0, imp) if (ov.grid_outage and _ok(imp)) else 0.0
        for e in self.cat.equipment_of_type("PlantLoop"):
            pre = e.id.split("-")[0]
            f = truth.get(f"{e.id}/{pre}-F", 0.0)
            f = f if _ok(f) else 0.0
            fd = e.meta["design_flow_m3s"] * 1000.0
            dpd = {"CHW": 120.0, "HW": 100.0, "CW": 60.0}.get(pre, 100.0)
            truth[f"{e.id}/{pre}-DP"] = dpd * (f / fd) ** 2 if fd else 0.0

    # ------------------------------------------------------------------ control
    def _native(self, raw: dict[str, float], sched: str | None) -> float | None:
        if not sched or self.ccfg.schedule_source != "native":
            return None
        v = raw.get(f"SCHED|{sched}".upper())
        return v if _ok(v) else None

    def _control(self, t: dt.datetime, dow: int, dts: float, ov: Overlays, raw: dict[str, float] | None = None) -> dict[str, float]:
        raw = raw or {}
        nat = self.b.manifest.native or {}
        cmd: dict[str, float] = {}
        cfg = self.ccfg
        pv = self.pv
        holiday = ov.holiday
        # AHU occupancy first (zones follow their AHU)
        ahu_occ, ahu_nat, ahu_minoa = {}, {}, {}
        for aid, ac in self.ahu.items():
            ln = self.cat.equipment[aid].eplus_name
            nf = self._native(raw, nat.get("air_loops", {}).get(ln, {}).get("fan_schedule"))
            nm = self._native(raw, nat.get("air_loops", {}).get(ln, {}).get("min_oa_schedule"))
            ahu_nat[aid] = None if nf is None else nf > 0
            ahu_minoa[aid] = None if nm is None else nm > 0
            base = occupied(cfg, t, dow, holiday) if ahu_nat[aid] is None else (ahu_nat[aid] and not holiday)
            occ = (base or aid in ov.force_occupied) and aid not in ov.force_unoccupied
            ahu_occ[aid] = occ
        geb = cfg.profile == "geb"
        dr = ov.dr_shed_kw is not None or _g0(pv, "GRID/DR-EVENT") > 0.5
        gdh = gdc = 0.0
        if geb:
            oat = pv.get("WX/OA-T-FC1H", math.nan)
            oat = oat if _ok(oat) else pv.get("WX/OA-T", math.nan)
            gdh, gdc, self.geb_mode = geb_zone_offsets(cfg, t, dow, self.env.cfg.tou, oat, dr, holiday)
        vav_out_by_ahu: dict[str, list[dict[str, float]]] = {a: [] for a in self.ahu}
        ztemps_by_ahu: dict[str, list[float]] = {a: [] for a in self.ahu}
        # zones: occupancy mode and active set points (follow the serving AHU's schedule)
        zone_sp: dict[str, tuple[float, float, bool]] = {}
        for zid in self.cat.zone_of_equip:
            aid = self.cat.equipment[zid].meta.get("ahu")
            occ = ahu_occ.get(aid, occupied(cfg, t, dow, holiday))
            h_occ, c_occ = self.zone_sp[zid]
            adj = max(-3.0, min(3.0, self._override_value(f"{zid}/ZN-T-ADJ", 0.0)))
            off = ov.setpoint_offset.get(zid, 0.0) + adj
            cmd[f"{zid}/ZN-T-ADJ"] = adj
            zn = nat.get("zones", {}).get(self.cat.zone_of_equip[zid], {})
            nh, nc = self._native(raw, zn.get("htg_schedule")), self._native(raw, zn.get("clg_schedule"))
            if nh is not None and not (occ and self.overrides.get(f"{zid}/OCC-HTG-SP")):
                hsp = nh + off
                if occ:
                    h_occ = nh
            else:
                hsp = (h_occ if occ else cfg.htg_unocc) + off
            if nc is not None and not (occ and self.overrides.get(f"{zid}/OCC-CLG-SP")):
                csp = nc + off
                if occ:
                    c_occ = nc
            else:
                csp = (c_occ if occ else cfg.clg_unocc) + off
            if geb and (occ or self.geb_mode == "dr"):
                hsp, csp = hsp + gdh, max(hsp + gdh + 1.0, csp + gdc)
            cmd[f"{zid}/HTG-SP"], cmd[f"{zid}/CLG-SP"] = hsp, csp
            cmd[f"{zid}/OCC-HTG-SP"], cmd[f"{zid}/OCC-CLG-SP"] = h_occ, c_occ
            cmd[f"{zid}/OCC-MODE"] = 1.0 if occ else 0.0
            zone_sp[zid] = (hsp, csp, occ)
            if aid in ztemps_by_ahu:
                ztemps_by_ahu[aid].append((pv.get(f"{zid}/ZN-T", math.nan), hsp, csp))
        # VAV boxes
        for vid, vc in self.vav.items():
            e = self.cat.equipment[vid]
            zid = e.meta["zone_equip"]
            aid = e.parent
            hsp, csp, occ = zone_sp[zid]
            tz = pv.get(f"{zid}/ZN-T", math.nan)
            fan_on = self.ahu[aid].mode > 0 if aid in self.ahu else True
            out = vc.step(tz, hsp, csp, fan_on, dts, gain_mult=ov.gain_mult.get(vid, 1.0),
                          frozen=vid in ov.frozen or vid in ov.comm_loss)
            for k, v in out.items():
                cmd[f"{vid}/{k}"] = v
            if aid in vav_out_by_ahu:
                vav_out_by_ahu[aid].append(out)
        # AHUs
        for aid, ac in self.ahu.items():
            apv = {p.name: pv[p.id] for p in self._ahu_points[aid] if p.id in pv}
            apv["OA-T"] = pv.get("WX/OA-T", math.nan)
            out = ac.step(t, dow, apv, ztemps_by_ahu[aid], vav_out_by_ahu[aid], dts, holiday=holiday,
                          force_occ=aid in ov.force_occupied, force_unocc=aid in ov.force_unoccupied,
                          econ_mode=ov.economizer.get(aid), sat_fixed=ov.sat_fixed.get(aid),
                          gain_mult=ov.gain_mult.get(aid, 1.0), frozen=aid in ov.frozen or aid in ov.comm_loss,
                          occ_native=ahu_nat.get(aid), min_oa_on=ahu_minoa.get(aid))
            for k, v in out.items():
                cmd[f"{aid}/{k}"] = v
        # plant
        ccv = [pv.get(f"{a}/CCV-POS", math.nan) for a in self.ahu]
        pout = self.plant.step(pv, ccv, dts)
        for k, v in pout.items():
            pre = k.split("-")[0]
            cmd[f"{pre}-SYS/{k}"] = v
        for e in self.cat.equipment.values():
            if e.type in ("Chiller", "Boiler"):
                cmd[f"{e.id}/EN-CMD"] = 1.0
        self._control_der(cmd, t, dow, ov, raw, nat, geb, dr)
        return cmd

    def _control_der(self, cmd, t, dow, ov: Overlays, raw, nat, geb: bool, dr: bool) -> None:
        """Zone equipment enables, battery dispatch and water-heater set points (observed values only)."""
        pv = self.pv
        shed = {x.strip() for x in self.ccfg.geb_dr_disable.split(",") if x.strip()} if geb and dr else set()
        for e in self.zone_units:
            if not e.meta.get("enable_schedule"):
                continue
            n = self._native(raw, nat.get("zone_equipment", {}).get(e.eplus_name, {}).get("avail_schedule"))
            en = (1.0 if n > 0 else 0.0) if n is not None else float(e.meta.get("enable_default", 1.0))
            if e.id in shed:
                en = 0.0
            cmd[f"{e.id}/ENABLE"] = en
            if e.type in ("HeatPump", "PTAC"):
                qh, qc = _g0(pv, f"{e.id}/HTG-Q"), _g0(pv, f"{e.id}/CLG-Q")
                run = pv.get(f"{e.id}/STS", 1.0)
                cmd[f"{e.id}/MODE"] = (-1.0 if en < 0.5 else 0.0 if (_ok(run) and run < 0.5) or max(qh, qc) < 0.02
                                       else 2.0 if qh > qc else 1.0)
        for e in self.batteries:
            lo = float(e.meta.get("min_soc") or 0.0)
            reserve = max(lo, self._override_value(f"{e.id}/RESERVE-SP", max(lo, self.ccfg.ess_reserve)))
            cmd[f"{e.id}/RESERVE-SP"] = reserve
            chg = dis = math.nan
            if geb:
                imp, exp_ = _g0(pv, "GRID/IMPORT-PWR"), _g0(pv, "GRID/EXPORT-PWR")
                need = imp + _g0(pv, f"{e.id}/DCHG-PWR")
                surplus = exp_ + _g0(pv, f"{e.id}/CHG-PWR") - imp
                win = onpeak_window(self.env.cfg.tou, t, dow, ov.holiday)
                hod = t.hour + t.minute / 60.0
                before = win is not None and win[0] - self.ccfg.ess_hold_h <= hod < win[0]
                chg, dis = geb_battery(self.ccfg, pv.get("GRID/TOU-PERIOD", math.nan), pv.get(f"{e.id}/SOC", math.nan),
                                       reserve, dr, need, surplus, before, float(e.meta.get("max_charge_kw") or 0.0),
                                       float(e.meta.get("max_discharge_kw") or 0.0))
            cmd[f"{e.id}/CHG-CMD"], cmd[f"{e.id}/DCHG-CMD"] = chg, dis
            cmd[f"{e.id}/MODE"] = 1.0 if (_ok(chg) or _ok(dis)) else 0.0
        for e in self.cat.equipment_of_type("WaterHeater"):
            if e.meta.get("sp_schedule"):
                n = self._native(raw, nat.get("water_heaters", {}).get(e.eplus_name, {}).get("sp_schedule"))
                cmd[f"{e.id}/TANK-SP"] = n if n is not None else self.b.manifest.commands.get(f"{e.eplus_name} SP", {}).get("default", 55.0)

    def _override_value(self, pid: str, default: float) -> float:
        slots = self.overrides.get(pid)
        if not slots:
            return default
        o = slots[min(slots)]
        if o.expires and self.t and self.t >= o.expires:
            return default
        return o.value

    def _apply_overrides(self, cmd: dict[str, float], t: dt.datetime) -> dict[str, float]:
        for pid, slots in list(self.overrides.items()):
            for pr in [p for p, o in slots.items() if o.expires and t >= o.expires]:
                slots.pop(pr)
            if not slots:
                continue
            best = slots[min(slots)]
            eq, name = pid.split("/", 1)
            if name == "OCC-HTG-SP" or name == "OCC-CLG-SP":
                h, c = self.zone_sp[eq]
                self.zone_sp[eq] = (best.value, c) if name == "OCC-HTG-SP" else (h, best.value)
            cmd[pid] = best.value
            if name in ("DA-F-SP",) and eq in self.cat.equipment:
                vmax = self.cat.equipment[eq].meta["vmax_m3s"]
                cmd[f"{eq}/DMPR-CMD"] = 100.0 * best.value / vmax
            if name == "DMPR-CMD" and eq in self.cat.equipment:
                vmax = self.cat.equipment[eq].meta["vmax_m3s"]
                cmd[f"{eq}/DA-F-SP"] = best.value / 100.0 * vmax
            if name in ("CHG-CMD", "DCHG-CMD") and eq in self.cat.equipment:
                cmd[f"{eq}/MODE"] = 1.0
        return cmd

    # ------------------------------------------------------------------ actuation
    def _sensor_error(self, pid: str, truth: dict[str, float], ov: Overlays) -> tuple[float, float, float | None, bool]:
        """Return (offset b, gain g, stuck/override value or None, unavailable) of a local-loop sensor.

        The deterministic sensor map is y = (1 + g) x + b with b = bias + drift (+ fault terms).
        """
        s = self.sensors.get(pid)
        o = ov.sensor.get(pid)
        eq = self.cat.points[pid].equip if pid in self.cat.points else ""
        if eq in ov.comm_loss or (o is not None and o.missing):
            return 0.0, 0.0, None, True
        if o is not None and (o.stuck or o.override is not None):
            v = o.override if o.override is not None else (s.state.stuck_value if s else None)
            if v is None:
                v = truth.get(pid, math.nan)
            return 0.0, 0.0, v, False
        if s is None:
            return 0.0, 0.0, None, False
        use_install = self.realism > 0
        b = (s.bias + s.state.drift if use_install else 0.0) + (o.bias if o else 0.0)
        g = (s.gain if use_install else 0.0) + (o.gain if o else 0.0)
        return b, g, None, False

    def _translate(self, pid: str, sp: float, truth: dict[str, float], ov: Overlays, lo: float, hi: float,
                   reverse: bool, key: str) -> float:
        """Local-loop emulation: set point handed to the ideal EnergyPlus local controller.

        A local loop that drives its *measured* value y = (1+g)x + b to the set point r drives the
        true value to x* = (r - b)/(1 + g). If the reading is stuck/overridden at v the integral
        action winds up and the actuator saturates: for a direct process (actuator up -> measured
        up) x* = hi if v < r else lo; for a reverse process (cooling) x* = lo if v > r else hi.
        If the reading is unavailable the controller holds its last output.
        """
        b, g, stuck, unavailable = self._sensor_error(pid, truth, ov)
        if unavailable:
            return self._last_sched.get(key, min(hi, max(lo, sp)))
        if stuck is not None and _ok(stuck):
            if reverse:
                val = lo if stuck > sp else hi
            else:
                val = hi if stuck < sp else lo
        else:
            val = (sp - b) / (1.0 + g) if abs(1.0 + g) > 1e-6 else sp
        val = min(hi, max(lo, val))
        self._last_sched[key] = val
        return val

    def _actuate(self, t, dts, raw, truth, cmd, ov: Overlays, warm: bool) -> dict[str, float | None]:
        A = self.cat.actuator
        sa = self.cat.schedule_actuator
        out: dict[str, float | None] = {}
        man = self.b.manifest
        topo = man.topo
        # ---------- grid outage: islanded operation or blackout (real-world physics, not BAS logic)
        dark = self._outage_state(truth, ov, warm)
        if dark:
            ov.light_mult["*"] = 0.0
            ov.plug_mult["*"] = 0.0
        # ---------- zones: thermostat (reheat local loop), occupancy, gains, infiltration
        for zid, zname in self.cat.zone_of_equip.items():
            z = topo.zones[zname]
            vid = self.cat.equipment[zid].parent
            hsp = cmd.get(f"{zid}/HTG-SP", self.ccfg.htg_occ)
            key = f"HTG|{zname}"
            ep_h = self._translate(f"{zid}/ZN-T", hsp, truth, ov, 5.0, 32.0, reverse=False, key=key)
            if vid in ov.reheat_open:
                ep_h = 26.0  # leaking/stuck-open valve: reheat until the zone reaches ~26 C
            if vid in ov.comm_loss or vid in ov.frozen:
                ep_h = self._last_eplus_htg.get(zname, ep_h)
            self._last_eplus_htg[zname] = ep_h
            out[A("Zone Temperature Control", "Heating Setpoint", zname)] = ep_h
            if vid in self.vav:
                # cooling is commanded explicitly through the terminal air-flow schedule
                out[A("Zone Temperature Control", "Cooling Setpoint", zname)] = 45.0
            else:
                # zone without a BAS-controlled terminal: thermostat local loop for cooling as well
                csp = cmd.get(f"{zid}/CLG-SP", self.ccfg.clg_occ)
                ep_c = self._translate(f"{zid}/ZN-T", csp, truth, ov, 10.0, 40.0, reverse=True, key=f"CLG|{zname}")
                if vid is not None and (vid in ov.comm_loss or vid in ov.frozen):
                    ep_c = self._last_sched.get(f"CLGHOLD|{zname}", ep_c)
                self._last_sched[f"CLGHOLD|{zname}"] = ep_c
                out[A("Zone Temperature Control", "Cooling Setpoint", zname)] = max(ep_c, ep_h + 0.5)
            # occupancy (truth) -> people actuator
            mult = ov.occ_mult.get(zname, 1.0) * ov.occ_mult.get("*", 1.0)
            add = ov.occ_add.get(zname, 0.0)
            for pname in z.people:
                ndes = self.engine.internal_values.get(f"NPEOPLE|{pname}".upper(), 0.0)
                sched = self.b.people_sched.get(pname)
                p = raw.get(f"SCHED|{sched}".upper(), 0.0) if sched else 0.0
                if self.occ_stochastic and not warm:
                    m = self.occ_models.get(pname)
                    if m is None:
                        orng = np.random.default_rng([self.seed, 2, zlib.crc32(pname.encode())])
                        m = self.occ_models[pname] = ZoneOccupancy(ndes, orng, self.occ_mobility, self.occ_att_min)
                    n = m.step(t, p, mult, add)
                    out[A("People", "Number of People", pname)] = n
                elif mult != 1.0 or add:
                    out[A("People", "Number of People", pname)] = ndes * min(1.0, p) * mult + add
                else:
                    out[A("People", "Number of People", pname)] = None
            # internal gains
            lm = ov.light_mult.get(zname, 1.0) * ov.light_mult.get("*", 1.0)
            for lname in z.lights:
                sched = self.b.light_sched.get(lname)
                if abs(lm - 1.0) > 1e-9:
                    des = self.engine.internal_values.get(f"LIGHTDES|{lname}".upper(), 0.0)
                    out[A("Lights", "Electricity Rate", lname)] = des * raw.get(f"SCHED|{sched}".upper(), 0.0) * lm
                else:
                    out[A("Lights", "Electricity Rate", lname)] = None
            pm = ov.plug_mult.get(zname, 1.0) * ov.plug_mult.get("*", 1.0)
            for ename in z.equipment:
                sched = self.b.equip_sched.get(ename)
                if abs(pm - 1.0) > 1e-9:
                    des = self.engine.internal_values.get(f"PLUGDES|{ename}".upper(), 0.0)
                    out[A("ElectricEquipment", "Electricity Rate", ename)] = des * raw.get(f"SCHED|{sched}".upper(), 0.0) * pm
                else:
                    out[A("ElectricEquipment", "Electricity Rate", ename)] = None
            ach = ov.infil_add_ach.get(zname, 0.0)
            if z.infiltration_window and not z.infiltration:
                # leakage-area infiltration keeps its own physics; the event adds air exchange on a zero-flow object
                vol = self.engine.internal_values.get(f"ZVOL|{zname}".upper(), 0.0)
                out[A("Zone Infiltration", "Air Exchange Flow Rate", z.infiltration_window)] = \
                    ach * vol / 3600.0 if ach > 0 else None
            if z.infiltration:
                if ach > 0:
                    base = self._infil_base.setdefault(zname, raw.get(f"INFIL|{zname}".upper(), 0.0))
                    vol = self.engine.internal_values.get(f"ZVOL|{zname}".upper(), 0.0)
                    per = (base + ach * vol / 3600.0) / len(z.infiltration)
                    for inf in z.infiltration:
                        out[A("Zone Infiltration", "Air Exchange Flow Rate", inf)] = per
                else:
                    self._infil_base.pop(zname, None)
                    for inf in z.infiltration:
                        out[A("Zone Infiltration", "Air Exchange Flow Rate", inf)] = None
        # ---------- VAV boxes: flow loop through the airflow sensor + damper faults
        for vid in self.vav:
            e = self.cat.equipment[vid]
            vmax = e.meta["vmax_m3s"]
            sp = cmd.get(f"{vid}/DA-F-SP", e.meta["vmin_frac"] * vmax)
            x_target = self._translate(f"{vid}/DA-F", sp, truth, ov, 0.0, vmax, reverse=False, key=f"FLOW|{vid}")
            frac = min(1.0, max(0.0, x_target / vmax)) if vmax > 0 else 0.0
            if vid in ov.damper_stuck:
                frac = ov.damper_stuck[vid]
            elif vid in ov.comm_loss or vid in ov.frozen:
                frac = self._last_frac.get(vid, frac)
            self._last_frac[vid] = frac
            sched = e.meta.get("flow_cmd_schedule")
            if sched:
                out[sa(sched)] = frac
            rh = e.meta.get("reheat_coil")
            if rh:
                out[A("Plant Component Coil:Heating:Water", "On/Off Supervisory", rh)] = 0.0 if vid in ov.reheat_closed else None
        # ---------- AHUs
        for a in self.cat.equipment_of_type("AHU"):
            aid = a.id
            fan_on = cmd.get(f"{aid}/SF-CMD", 1.0) > 0.5 and aid not in ov.fan_failed
            if a.meta.get("fan_schedule"):
                out[sa(a.meta["fan_schedule"])] = 1.0 if fan_on else 0.0
            sat_sp = cmd.get(f"{aid}/SA-T-SP", self.ccfg.sat_fixed)
            if a.meta.get("sat_schedule"):
                out[sa(a.meta["sat_schedule"])] = self._translate(f"{aid}/SA-T", sat_sp, truth, ov, 4.0, 35.0,
                                                                  reverse=True, key=f"SAT|{aid}")
            oac = a.meta.get("oa_controller")
            if oac:
                # supply flow of this step = sum of the terminal flows commanded this step
                sa_mass = sum(self._last_frac.get(v, 0.0) * self.cat.equipment[v].meta["vmax_m3s"]
                              for v in a.meta.get("vav", []) if v in self.cat.equipment) * RHO_AIR
                frac = cmd.get(f"{aid}/OAD-CMD", 0.0) / 100.0
                if aid in ov.oa_damper_stuck:
                    frac = ov.oa_damper_stuck[aid]
                out[A("Outdoor Air Controller", "Air Mass Flow Rate", oac)] = max(0.0, frac * sa_mass) if fan_on else 0.0
            fan = a.meta.get("fan")
            if fan:
                dp0 = self.engine.internal_values.get(f"FANDP|{fan}".upper())
                eff0 = self.engine.internal_values.get(f"FANEFF|{fan}".upper())
                dsp_sp = cmd.get(f"{aid}/DSP-SP", self.ccfg.dsp_design)
                extra = ov.filter_dp_add.get(aid, 0.0) - (self.ccfg.dsp_design - dsp_sp)
                if dp0 and abs(extra) > 1e-6:
                    out[A("Fan", "Fan Pressure Rise", fan)] = max(50.0, dp0 + extra)
                else:
                    out[A("Fan", "Fan Pressure Rise", fan)] = None
                m = ov.fan_eff_mult.get(aid, 1.0)
                if eff0 and abs(m - 1.0) > 1e-9:
                    out[A("Fan", "Fan Total Efficiency", fan)] = max(0.05, eff0 * m)
                else:
                    out[A("Fan", "Fan Total Efficiency", fan)] = None
            loop = topo.air_loops.get(a.eplus_name)
            if loop:
                for c in loop.cooling_coils:
                    out[A("Plant Component Coil:Cooling:Water", "On/Off Supervisory", c.name)] = 0.0 if f"{aid}:CC" in ov.coil_closed else None
                for c in loop.heating_coils:
                    if c.type == "Coil:Heating:Water":
                        out[A("Plant Component Coil:Heating:Water", "On/Off Supervisory", c.name)] = 0.0 if f"{aid}:HC" in ov.coil_closed else None
        # ---------- plant loops
        for e in self.cat.equipment_of_type("PlantLoop"):
            pre = e.id.split("-")[0]
            sched = e.meta.get("swt_schedule")
            if not sched:
                continue
            sp = cmd.get(f"{e.id}/{pre}-ST-SP")
            if sp is None:
                continue
            lo, hi, rev = {"CHW": (3.0, 15.0, True), "HW": (30.0, 95.0, False), "CW": (5.0, 40.0, True)}[pre]
            out[sa(sched)] = self._translate(f"{e.id}/{pre}-ST", sp, truth, ov, lo, hi, reverse=rev, key=f"SWT|{e.id}")
        for e in self.cat.equipment.values():
            if e.type in ("Chiller", "Boiler", "CoolingTower", "Pump"):
                ptype = e.meta.get("type") or {"Boiler": "Boiler:HotWater"}.get(e.type)
                if e.type == "CoolingTower":
                    ptype = next((tw.type for pl in topo.plant_loops.values() for tw in pl.towers if tw.name == e.eplus_name), None)
                if ptype:
                    out[A("Plant Component " + ptype, "On/Off Supervisory", e.eplus_name)] = 0.0 if e.id in ov.trips else None
                ff = e.meta.get("fouling_fault")
                if ff and ff in man.faults:
                    f = man.faults[ff]
                    r = ov.fouling.get(e.id, 1.0)
                    out[sa(f["active_schedule"])] = 1.0 if r < 0.999 else 0.0
                    # EnergyPlus 23.2 applies factor = fouling_factor / severity  (fouling_factor = 1)
                    out[sa(f["value_schedule"])] = 1.0 / max(r, 0.05)
        self._actuate_der(out, truth, raw, cmd, ov, dark)
        co2 = man.commands.get("OUTDOOR CO2")
        if co2:
            out[sa(co2["schedule"])] = ov.outdoor_co2 if ov.outdoor_co2 is not None else co2["default"]
        return out

    def _outage_state(self, truth: dict[str, float], ov: Overlays, warm: bool) -> bool:
        """True while the building is dark (grid outage without backup, or storage exhausted while islanded)."""
        if warm or not ov.grid_outage:
            self._dark = False
            return False
        if not ov.outage_backup or not self.batteries:
            self._dark = True
            return True
        socs = [(truth.get(f"{e.id}/SOC", math.nan), float(e.meta.get("min_soc") or 0.0)) for e in self.batteries]
        low = all(_ok(s_) and s_ <= lo + 0.01 for s_, lo in socs)
        high = any(_ok(s_) and s_ >= lo + 0.05 for s_, lo in socs)
        self._dark = (self._dark and not high) or low
        return self._dark

    def _actuate_der(self, out, truth, raw, cmd, ov: Overlays, dark: bool) -> None:
        A = self.cat.actuator
        sa = self.cat.schedule_actuator
        man = self.b.manifest
        topo = man.topo
        # ---------- zone equipment: enable / trips / blackout, heat-pump degradation, ERV faults
        for e in self.zone_units:
            sched = e.meta.get("enable_schedule")
            if sched:
                en = cmd.get(f"{e.id}/ENABLE", float(e.meta.get("enable_default", 1.0)))
                if e.id in ov.comm_loss:
                    en = self._last_enable.get(e.id, en)
                self._last_enable[e.id] = en
                on = en > 0.5 and e.id not in ov.trips and not dark
                out[sa(sched)] = 1.0 if on else 0.0
            ff = e.meta.get("degrade_fault")
            if ff and ff in man.faults:
                f = man.faults[ff]
                rq, rc = ov.hp_degrade.get(e.id, (1.0, 1.0))
                out[sa(f["active_schedule"])] = 1.0 if (rq < 0.999 or rc < 0.999) else 0.0
                out[sa(f["value_schedule"])] = max(0.05, rq)
                out[sa(f["cop_schedule"])] = max(0.05, rc)
            if e.type == "ERV":
                failed = ov.erv_fan_failed.get(e.id, "")
                for fan_key, which in (("supply_fan", "supply"), ("exhaust_fan", "exhaust")):
                    fan = e.meta.get(fan_key)
                    if fan:
                        out[A("Fan", "Fan Air Mass Flow Rate", fan)] = 0.0 if failed in (which, "both") else None
                hf = e.meta.get("hx_fault")
                if hf and hf in man.faults:
                    f = man.faults[hf]
                    r = ov.erv_hx.get(e.id, 1.0)
                    out[sa(f["active_schedule"])] = 1.0 if r < 0.999 else 0.0
                    out[sa(f["value_schedule"])] = max(0.0, r)
        # ---------- PV systems: soiling, inverter trip, anti-islanding and export curtailment
        for e in self.pv_systems:
            lc = topo.load_centers.get(e.eplus_name)
            f = man.faults.get(e.meta.get("loss_fault") or "")
            if lc is None or f is None:
                continue
            eta = float(e.meta.get("inverter_eff") or 1.0)
            dc = sum(raw.get(f"GENERATOR PRODUCED DC ELECTRICITY RATE|{g.name}".upper(), 0.0) for g in lc.generators)
            inv = lc.inverter.name if lc.inverter else None
            ac = raw.get(f"INVERTER AC OUTPUT ELECTRICITY RATE|{inv}".upper(), dc * eta) if inv else dc * eta
            dc, ac = (dc if _ok(dc) else 0.0), (ac if _ok(ac) else 0.0)
            # values of the previous step: extrapolate linearly to the step being simulated (PV ramps)
            dc_1, ac_1 = self._pv_last.get(e.id, (dc, ac))
            self._pv_last[e.id] = (dc, ac)
            dc, ac = max(0.0, 2.0 * dc - dc_1), max(0.0, 2.0 * ac - ac_1)
            tripped = e.id in ov.inverter_trip or (ov.grid_outage and not ov.outage_backup)
            if tripped:
                loss = ac           # no AC output at all (DC-coupled storage idles, see below)
            else:
                pv_ac = dc * eta    # PV share of the inverter output (the DC-coupled battery also flows through it)
                loss = ov.pv_loss.get(e.id, 0.0) * pv_ac
                if ov.grid_outage:
                    # islanded: the surplus cannot be exported -> curtail what neither the loads nor the battery absorb
                    load = 1000.0 * max(0.0, _g0(truth, "MTR/BLDG-ELEC-KW"))
                    room = sum(1000.0 * float(b.meta.get("max_charge_kw") or 0.0) for b in self.batteries
                               if b.meta.get("load_center") == lc.name and
                               _g0(truth, f"{b.id}/SOC") < float(b.meta.get("max_soc") or 1.0) - 0.005)
                    self._pv_curtail[e.id] = max(0.0, pv_ac - loss - load - room)
                    loss += self._pv_curtail[e.id]
                else:
                    self._pv_curtail.pop(e.id, None)
            out[A("ElectricEquipment", "Electricity Rate", f["loss_object"])] = max(0.0, loss) if loss > 0 else None
        # ---------- electrical storage: BAS dispatch (NaN = native EnergyPlus storage scheme)
        for e in self.batteries:
            lc_name = e.meta.get("load_center")
            chg, dis = cmd.get(f"{e.id}/CHG-CMD", math.nan), cmd.get(f"{e.id}/DCHG-CMD", math.nan)
            idle = any(p.id in ov.inverter_trip and p.eplus_name == lc_name for p in self.pv_systems) or (
                ov.grid_outage and not ov.outage_backup)
            if e.id in ov.comm_loss:
                chg = dis = math.nan
            if dark and not idle:
                # islanded and depleted: no discharge, PV recharges the battery with what the (dark) site does not use
                pv_ac = sum(self._pv_last.get(p.id, (0.0, 0.0))[0] * float(p.meta.get("inverter_eff") or 1.0)
                            for p in self.pv_systems if p.eplus_name == lc_name) / 1000.0
                surplus = pv_ac - max(0.0, _g0(truth, "MTR/BLDG-ELEC-KW"))
                chg, dis = min(float(e.meta.get("max_charge_kw") or 0.0), max(0.0, surplus)), 0.0
            out[A("Electrical Storage", "Power Charge Rate", lc_name)] = 0.0 if idle else (
                max(0.0, chg) * 1000.0 if _ok(chg) else None)
            out[A("Electrical Storage", "Power Draw Rate", lc_name)] = 0.0 if idle else (
                max(0.0, dis) * 1000.0 if _ok(dis) else None)
        # ---------- water heaters with a bound set point
        for e in self.cat.equipment_of_type("WaterHeater"):
            sched = e.meta.get("sp_schedule")
            if sched:
                sp = cmd.get(f"{e.id}/TANK-SP", 55.0)
                out[sa(sched)] = 5.0 if dark else sp

    # ------------------------------------------------------------------ KPI
    def _kpi(self, truth, cmd, dts, t, dow) -> None:
        h = dts / 3600.0
        k = self.kpi
        k["elec_kwh"] += max(0.0, truth.get("MTR/BLDG-ELEC-KW", 0.0) or 0.0) * h
        k["gas_kwh"] += max(0.0, truth.get("MTR/BLDG-GAS-KW", 0.0) or 0.0) * h
        k["hvac_elec_kwh"] += max(0.0, truth.get("MTR/HVAC-ELEC-KW", 0.0) or 0.0) * h
        k["steps"] += 1
        price, ci = truth.get("GRID/PRICE", 0.0), truth.get("GRID/CO2-INT", 0.0)
        e_kw = max(0.0, truth.get("MTR/BLDG-ELEC-KW", 0.0) or 0.0)
        if "grid_import_kwh" in k:
            # on-site generation / storage: the utility bills the grid import
            e_kw = max(0.0, _g0(truth, "GRID/IMPORT-PWR"))
            k["grid_import_kwh"] += e_kw * h
            k["grid_export_kwh"] += max(0.0, _g0(truth, "GRID/EXPORT-PWR")) * h
            k["pv_kwh"] += sum(max(0.0, _g0(truth, f"{p.id}/DC-PWR")) for p in self.pv_systems) * h
            k["unserved_kwh"] += max(0.0, _g0(truth, "GRID/UNSERVED-KW")) * h
        g_kw = max(0.0, truth.get("MTR/BLDG-GAS-KW", 0.0) or 0.0)
        if _ok(price) and _ok(ci):
            k["cost_usd"] += (e_kw * price + g_kw * self.env.cfg.gas_price_per_kwh) * h
            k["co2_kg"] += (e_kw * ci + g_kw * self.env.cfg.gas_carbon) * h
        unmet = 0
        for zid in self.cat.zone_of_equip:
            if cmd.get(f"{zid}/OCC-MODE", 0.0) < 0.5:
                continue
            T = truth.get(f"{zid}/ZN-T", math.nan)
            if not _ok(T):
                continue
            lo, hi = cmd.get(f"{zid}/HTG-SP", 21.0) - 0.5, cmd.get(f"{zid}/CLG-SP", 24.0) + 0.5
            dev = max(0.0, lo - T, T - hi)
            k["comfort_kh"] += dev * h
            if dev > 0:
                unmet += 1
            c = truth.get(f"{zid}/ZN-CO2", math.nan)
            if _ok(c) and c > 1000:
                k["co2_over_1000_h"] += h
            pm = truth.get(f"{zid}/ZN-PM25", math.nan)
            if _ok(pm) and pm > 15.0:
                k["pm25_over_15_h"] += h
            tv = truth.get(f"{zid}/ZN-TVOC", math.nan)
            if _ok(tv) and tv > 500.0:
                k["tvoc_over_500_h"] += h
        k["unmet_occ_hours"] += unmet * h


def faults_catalog() -> list[dict[str, Any]]:
    return fault_catalog()
