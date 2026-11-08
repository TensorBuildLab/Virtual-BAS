"""Convert an arbitrary EnergyPlus model into a *BAS-ready* model.

The preparation step is the generic part of the Virtual BAS methodology. It applies a small
set of well-defined, reversible transformations to the original model:

T1  Simulation control: run the weather-file run period only (sizing is still performed).
T2  Time resolution: set the zone time step (= BAS sampling interval).
T3  Run period: set the calendar window and year.
T4  Output pruning: remove file outputs (data are exchanged through the API instead).
T5  Command binding: every quantity a BAS writes is bound to a dedicated ``Schedule:Constant``
    ("command schedule") that the outer space overwrites through the EnergyPlus API:
      - air-loop supply-air temperature set points (SetpointManager:Scheduled)
      - plant / condenser loop supply temperature set points
      - air-loop supply-fan enable (fan availability schedule; native night-cycle disabled)
      - terminal-unit air-flow commands (VAV minimum-flow-fraction schedule, ``Scheduled`` method)
T6  Physical fault hooks: EnergyPlus ``FaultModel:*`` objects are attached to primary plant
    equipment with a severity schedule initialised to 0 (fault free). The outer space can then
    activate *physical* degradation at run time.
T7  Indoor air quality: zone CO2 mass balance is enabled with an actuatable outdoor CO2 schedule.

The output of the step is the prepared epJSON and a JSON *manifest* containing the discovered
topology, all command/fault schedule bindings and the design (autosized) parameters.
"""
from __future__ import annotations

import copy
import json
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .. import eplus
from .epjson import EpJSON, add_object, add_schedule_constant, find_object, load_model, save_model
from .topology import Topology, discover

OUTPUT_TYPES_TO_DROP = [
    "Output:Variable", "Output:Meter", "Output:Meter:MeterFileOnly", "Output:Meter:Cumulative",
    "Output:Table:Monthly", "Output:Table:TimeBins", "Output:SQLite", "Output:Surfaces:Drawing",
    "Output:Surfaces:List", "Output:Constructions", "Output:VariableDictionary", "Output:EnvironmentalImpactFactors",
]


@dataclass
class PrepareOptions:
    timesteps_per_hour: int = 12
    begin_month: int = 1
    begin_day: int = 1
    end_month: int = 12
    end_day: int = 31
    year: int = 2023
    enable_co2: bool = True
    outdoor_co2_ppm: float = 420.0
    keep_summary_reports: bool = True


@dataclass
class Manifest:
    source_model: str
    weather_file: str
    options: dict[str, Any]
    topology: dict[str, Any]
    commands: dict[str, dict[str, Any]] = field(default_factory=dict)
    faults: dict[str, dict[str, Any]] = field(default_factory=dict)
    design: dict[str, dict[str, dict[str, float]]] = field(default_factory=dict)
    energyplus_version: str = ""
    native: dict[str, Any] = field(default_factory=dict)   # native schedules -> default BAS program

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.__dict__, indent=1))

    @staticmethod
    def load(path: str | Path) -> "Manifest":
        return Manifest(**json.loads(Path(path).read_text()))

    @property
    def topo(self) -> Topology:
        return Topology.from_dict(self.topology)

    def design_value(self, obj_type: str, name: str, key_contains: str, default: float | None = None) -> float | None:
        recs = self.design.get(obj_type.upper(), {}).get(name.upper(), {})
        kc = _norm(key_contains)
        for k, v in recs.items():
            if kc in _norm(k):
                return v
        return default


def _first_numeric(model: EpJSON, sched_name: str | None, default: float) -> float:
    if not sched_name:
        return default
    for t in ["Schedule:Compact", "Schedule:Constant"]:
        o = find_object(model, t, sched_name)
        if o is None:
            continue
        if t == "Schedule:Constant":
            return float(o.get("hourly_value", default))
        for f in o.get("data", []):
            v = f.get("field")
            if isinstance(v, (int, float)):
                return float(v)
    return default


def _norm(s: str) -> str:
    """Normalise EnergyPlus sizing descriptions ('u-factor_times_area_value' == 'U-Factor Times Area Value')."""
    return re.sub(r"[\s_\-]+", " ", s.lower()).strip()


def _safe(name: str) -> str:
    return re.sub(r"\s+", " ", name).strip()


def _bind_terminals(model: EpJSON, topo: Topology, cmd, design: dict[str, dict[str, dict[str, float]]] | None) -> None:
    """T5 for terminal units: hard-size from the native sizing run, then bind the flow command schedule.

    Switching the minimum-flow input method to ``Scheduled`` changes EnergyPlus' autosizing of
    reheat coils, so terminals (and their reheat coils) are first hard-sized with the values of a
    sizing run of the *native* terminal configuration.
    """
    def dv(t, n, key):
        recs = (design or {}).get(t.upper(), {}).get(n.upper(), {})
        for k, v in recs.items():
            if _norm(key) in _norm(k) and k.lower().startswith("design size"):
                return v
        return None

    for tname, term in topo.terminals.items():
        to = find_object(model, term.type, tname)
        if to is None:
            continue
        if design:
            for field, key in [("maximum_air_flow_rate", "Maximum Air Flow Rate [m3/s]"),
                               ("maximum_hot_water_or_steam_flow_rate", "Maximum Reheat Water Flow Rate"),
                               ("constant_minimum_air_flow_fraction", "Constant Minimum Air Flow Fraction"),
                               ("maximum_flow_fraction_during_reheat", "Maximum Flow Fraction during Reheat"),
                               ("maximum_flow_per_zone_floor_area_during_reheat", "Maximum Flow per Zone Floor Area during Reheat")]:
                if isinstance(to.get(field), str) and to.get(field, "").lower().startswith("auto"):
                    v = dv(term.type, tname, key)
                    if v is not None:
                        to[field] = v
            if term.reheat and term.reheat.type == "Coil:Heating:Water":
                co = find_object(model, term.reheat.type, term.reheat.name)
                if co is not None:
                    for field, key in [("maximum_water_flow_rate", "Maximum Water Flow Rate"),
                                       ("u_factor_times_area_value", "U-Factor Times Area Value"),
                                       ("rated_capacity", "Rated Capacity")]:
                        if isinstance(co.get(field), str) and co.get(field, "").lower().startswith("auto"):
                            v = dv(term.reheat.type, term.reheat.name, key)
                            if v is not None and v > 0:
                                co[field] = v
    for tname, term in topo.terminals.items():
        to = find_object(model, term.type, tname)
        if to is None:
            continue
        raw_frac = to.get("constant_minimum_air_flow_fraction", 0.3)
        frac = float(raw_frac) if isinstance(raw_frac, (int, float)) else 0.3  # 'Autosize' -> updated after sizing
        num = lambda v: float(v) if isinstance(v, (int, float)) else None  # noqa: E731
        s = cmd(f"{tname} FLOW", frac, kind="terminal_flow_fraction", terminal=tname, zone=term.zone, unit="-",
                autosized=not isinstance(raw_frac, (int, float)),
                vmax_m3s=num(to.get("maximum_air_flow_rate")),
                reheat_max_water_m3s=num(to.get("maximum_hot_water_or_steam_flow_rate")))
        to["zone_minimum_air_flow_input_method"] = "Scheduled"
        to["minimum_air_flow_fraction_schedule_name"] = s
        to["constant_minimum_air_flow_fraction"] = raw_frac  # used for sizing only
        to["damper_heating_action"] = "Normal"



def prepare_model(model_path: str | Path, weather_path: str | Path, out_dir: str | Path,
                  options: PrepareOptions | None = None, run_sizing: bool = True) -> tuple[Path, Manifest]:
    """Prepare ``model_path`` and write ``<out_dir>/model.epJSON`` and ``manifest.json``."""
    opts = options or PrepareOptions()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    original = load_model(model_path)
    model = copy.deepcopy(original)
    topo = discover(model)
    commands: dict[str, dict[str, Any]] = {}
    faults: dict[str, dict[str, Any]] = {}

    add_object(model, "ScheduleTypeLimits", "VBAS Any Number", {})
    add_schedule_constant(model, "VBAS Always Off", 0.0, "VBAS Any Number")
    add_schedule_constant(model, "VBAS Always On", 1.0, "VBAS Any Number")

    def cmd(key: str, value: float, **meta) -> str:
        sname = _safe(f"VBAS CMD {key}")
        add_schedule_constant(model, sname, value, "VBAS Any Number")
        commands[key] = {"schedule": sname, "default": value, **meta}
        return sname

    # ---- T1 simulation control -------------------------------------------------------
    for sc in model.get("SimulationControl", {}).values():
        sc.update({"do_zone_sizing_calculation": "Yes", "do_system_sizing_calculation": "Yes",
                   "do_plant_sizing_calculation": "Yes", "run_simulation_for_sizing_periods": "No",
                   "run_simulation_for_weather_file_run_periods": "Yes"})
    # ---- T2 time step ------------------------------------------------------------
    model["Timestep"] = {"Timestep 1": {"number_of_timesteps_per_hour": opts.timesteps_per_hour}}
    # ---- T3 run period -------------------------------------------------------------
    rp_old = next(iter(model.get("RunPeriod", {}).values()), {})
    rp = {k: v for k, v in rp_old.items() if k.startswith("use_") or k.startswith("apply_")}
    rp.update({"begin_month": opts.begin_month, "begin_day_of_month": opts.begin_day, "begin_year": opts.year,
               "end_month": opts.end_month, "end_day_of_month": opts.end_day, "end_year": opts.year})
    model["RunPeriod"] = {"VBAS Run Period": rp}
    # ---- T4 outputs ------------------------------------------------------------------
    for t in OUTPUT_TYPES_TO_DROP:
        model.pop(t, None)
    if opts.keep_summary_reports:
        model["Output:Table:SummaryReports"] = {"Output:Table:SummaryReports 1": {"reports": [{"report_name": "AllSummary"}]}}
        model["OutputControl:Table:Style"] = {"OutputControl:Table:Style 1": {"column_separator": "HTML"}}
    add_object(model, "EnergyManagementSystem:GlobalVariable", "EnergyManagementSystem:GlobalVariable VBAS",
               {"variables": [{"erl_variable_name": "vbas_enable"}]})

    # ---- native control program (schedules) - becomes the default BAS program -----------------
    native: dict[str, Any] = {"air_loops": {}, "zones": {}}
    for zname, z in topo.zones.items():
        if not z.thermostat:
            continue
        th = find_object(original, "ZoneControl:Thermostat", z.thermostat) or {}
        for i in range(1, 5):
            ctype, cname = th.get(f"control_{i}_object_type"), th.get(f"control_{i}_name")
            if ctype == "ThermostatSetpoint:DualSetpoint":
                o = find_object(original, ctype, cname) or {}
                native["zones"][zname] = {"htg_schedule": o.get("heating_setpoint_temperature_schedule_name"),
                                          "clg_schedule": o.get("cooling_setpoint_temperature_schedule_name")}
                break
            if ctype == "ThermostatSetpoint:SingleHeating":
                o = find_object(original, ctype, cname) or {}
                native["zones"].setdefault(zname, {})["htg_schedule"] = o.get("setpoint_temperature_schedule_name")
            if ctype == "ThermostatSetpoint:SingleCooling":
                o = find_object(original, ctype, cname) or {}
                native["zones"].setdefault(zname, {})["clg_schedule"] = o.get("setpoint_temperature_schedule_name")

    # ---- T5 command binding ------------------------------------------------------------
    spm_sched = model.get("SetpointManager:Scheduled", {})

    def bind_node_setpoint(node: str, sched: str, extra_nodes: list[str] = ()):  # type: ignore[assignment]
        targets = {node.upper(), *[n.upper() for n in extra_nodes]}
        # remove every temperature SPM acting on target nodes, then add one scheduled SPM
        for t in [k for k in model if k.startswith("SetpointManager:") and k != "SetpointManager:MixedAir"]:
            for n in list(model[t].keys()):
                o = model[t][n]
                if o.get("control_variable", "Temperature") not in ("Temperature",):
                    continue
                nodes = o.get("setpoint_node_or_nodelist_name", "")
                if nodes.upper() in targets:
                    del model[t][n]
            if not model[t]:
                del model[t]
        for i, n in enumerate([node, *extra_nodes]):
            add_object(model, "SetpointManager:Scheduled", _safe(f"VBAS SPM {n}"),
                       {"control_variable": "Temperature", "schedule_name": sched, "setpoint_node_or_nodelist_name": n})

    for lname, loop in topo.air_loops.items():
        old = next((o for o in spm_sched.values()
                    if o.get("setpoint_node_or_nodelist_name", "").upper() == loop.supply_outlet.upper()), None)
        sat_spm = [sm for sm in topo.setpoint_managers
                   if loop.supply_outlet.upper() in [n.upper() for n in sm["nodes"]]]
        single_zone = any(sm["type"].startswith("SetpointManager:SingleZone") for sm in sat_spm)
        # multi-zone VAV systems: the BAS owns the SAT set point; single-zone units keep their native logic
        if loop.terminals and not single_zone:
            default_sat = _first_numeric(original, old.get("schedule_name") if old else None, 12.8)
            s = cmd(f"{lname} SAT", default_sat, kind="sat_setpoint", air_loop=lname, unit="C")
            bind_node_setpoint(loop.supply_outlet, s)
        s_fan = cmd(f"{lname} FAN", 1.0, kind="fan_enable", air_loop=lname, unit="-")
        if loop.fan:
            fo = find_object(model, loop.fan.type, loop.fan.name)
            if fo is not None:
                native["air_loops"].setdefault(lname, {})["fan_schedule"] = fo.get("availability_schedule_name")
                fo["availability_schedule_name"] = s_fan
        if loop.oa_controller:
            oac = find_object(original, "Controller:OutdoorAir", loop.oa_controller) or {}
            native["air_loops"].setdefault(lname, {})["min_oa_schedule"] = oac.get("minimum_outdoor_air_schedule_name")
        if loop.availability_manager_list:
            aml = find_object(model, "AvailabilityManagerAssignmentList", loop.availability_manager_list) or {}
            for am in aml.get("managers", []):
                amo = find_object(model, am.get("availability_manager_object_type", ""), am.get("availability_manager_name", ""))
                if amo is not None:
                    amo["applicability_schedule_name"] = "VBAS Always Off"
                    if "fan_schedule_name" in amo:
                        amo["fan_schedule_name"] = s_fan

    for pname, pl in topo.plant_loops.items():
        if pl.kind not in ("chilled_water", "hot_water", "condenser") or not pl.setpoint_node:
            continue
        old = next((sm for sm in topo.setpoint_managers if pl.setpoint_node.upper() in [n.upper() for n in sm["nodes"]]), None)
        default = {"chilled_water": 6.7, "hot_water": 60.0, "condenser": 29.4}[pl.kind]
        if old and old.get("schedule"):
            default = _first_numeric(original, old["schedule"], default)
        s = cmd(f"{pname} SWT", default, kind="plant_supply_temperature", plant_loop=pl.kind, loop=pname, unit="C")
        extra = [c.outlet for c in (pl.chillers + pl.boilers + pl.towers) if c.outlet]
        # Only re-bind equipment outlet nodes that had their own set point manager in the original model
        sp_nodes = {n.upper() for sm in topo.setpoint_managers for n in sm["nodes"]}
        extra = [n for n in extra if n.upper() in sp_nodes]
        bind_node_setpoint(pl.setpoint_node, s, extra)

    # ---- T6 physical fault hooks ----------------------------------------------------------
    def fault_hook(key: str, obj_type: str, obj_name: str, fields: dict[str, Any], value_default: float, **meta) -> None:
        """Attach a FaultModel object with two command schedules: ACTIVE (0/1) and VALUE."""
        s_act = _safe(f"VBAS FAULT {key} ACTIVE")
        s_val = _safe(f"VBAS FAULT {key} VALUE")
        add_schedule_constant(model, s_act, 0.0, "VBAS Any Number")
        add_schedule_constant(model, s_val, value_default, "VBAS Any Number")
        add_object(model, obj_type, _safe(f"VBAS {obj_name}"),
                   {"availability_schedule_name": s_act, "severity_schedule_name": s_val, **fields})
        faults[key] = {"active_schedule": s_act, "value_schedule": s_val, "value_default": value_default,
                       "object_type": obj_type, **meta}

    for pl in topo.plant_loops.values():
        for ch in pl.chillers:
            # effective factor = reference (1.0) x VALUE  -> VALUE is the capacity/COP ratio
            fault_hook(f"{ch.name} FOULING", "FaultModel:Fouling:Chiller", f"{ch.name} Fouling",
                       {"chiller_object_type": ch.type, "chiller_object_name": ch.name, "fouling_factor": 1.0},
                       1.0, kind="chiller_fouling", equipment=ch.name)
        for b in pl.boilers:
            fault_hook(f"{b.name} FOULING", "FaultModel:Fouling:Boiler", f"{b.name} Fouling",
                       {"boiler_object_type": b.type, "boiler_object_name": b.name, "fouling_factor": 1.0},
                       1.0, kind="boiler_fouling", equipment=b.name)
        for tw in pl.towers:
            if tw.type in ("CoolingTower:SingleSpeed", "CoolingTower:TwoSpeed", "CoolingTower:VariableSpeed:Merkel"):
                fault_hook(f"{tw.name} FOULING", "FaultModel:Fouling:CoolingTower", f"{tw.name} Fouling",
                           {"cooling_tower_object_type": tw.type, "cooling_tower_object_name": tw.name,
                            "reference_ua_reduction_factor": 1.0},
                           1.0, kind="tower_fouling", equipment=tw.name)

    # ---- T7 CO2 ---------------------------------------------------------------------------
    if opts.enable_co2:
        s = cmd("OUTDOOR CO2", opts.outdoor_co2_ppm, kind="outdoor_co2", unit="ppm")
        model["ZoneAirContaminantBalance"] = {"ZoneAirContaminantBalance 1": {
            "carbon_dioxide_concentration": "Yes", "outdoor_carbon_dioxide_schedule_name": s}}

    shutil.copy(weather_path, out_dir / "weather.epw")
    native_design = run_sizing_only(model, out_dir / "weather.epw", out_dir / "sizing_native") if run_sizing else None
    _bind_terminals(model, topo, cmd, native_design)
    model_path_out = save_model(model, out_dir / "model.epJSON")
    manifest = Manifest(source_model=str(model_path), weather_file="weather.epw", options=opts.__dict__,
                        topology=topo.to_dict(), commands=commands, faults=faults,
                        energyplus_version=eplus.version_string(), native=native)
    if run_sizing:
        manifest.design = run_sizing_only(model, out_dir / "weather.epw", out_dir / "sizing")
        # autosized minimum flow fractions -> initial command values
        changed = False
        for key, c in commands.items():
            if c.get("kind") == "terminal_flow_fraction" and c.get("autosized"):
                t = topo.terminals[c["terminal"]]
                v = manifest.design_value(t.type, t.name, "Constant Minimum Air Flow Fraction", None)
                if v:
                    c["default"] = v
                    model["Schedule:Constant"][c["schedule"]]["hourly_value"] = v
                    changed = True
        if changed:
            save_model(model, out_dir / "model.epJSON")
    manifest.save(out_dir / "manifest.json")
    return model_path_out, manifest


def run_sizing_only(model: EpJSON, weather: Path, out_dir: Path) -> dict[str, dict[str, dict[str, float]]]:
    """Run the sizing calculation only and parse 'Component Sizing Information' from the .eio."""
    m = copy.deepcopy(model)
    for sc in m.get("SimulationControl", {}).values():
        sc["run_simulation_for_weather_file_run_periods"] = "No"
        sc["run_simulation_for_sizing_periods"] = "No"
    out_dir.mkdir(parents=True, exist_ok=True)
    p = save_model(m, out_dir / "sizing.epJSON")
    proc = subprocess.run([str(eplus.energyplus_exe()), "-w", str(weather), "-d", str(out_dir), str(p)],
                          capture_output=True, text=True)
    eio = out_dir / "eplusout.eio"
    if not eio.exists():
        raise RuntimeError(f"Sizing run failed:\n{proc.stdout[-3000:]}\n{proc.stderr[-3000:]}")
    return parse_eio_sizing(eio)


def parse_eio_sizing(eio: Path) -> dict[str, dict[str, dict[str, float]]]:
    design: dict[str, dict[str, dict[str, float]]] = {}
    for line in eio.read_text(errors="ignore").splitlines():
        if not line.startswith(" Component Sizing Information,"):
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 5:
            continue
        _, ctype, cname, desc, val = parts[:5]
        try:
            v = float(val)
        except ValueError:
            continue
        design.setdefault(ctype.upper(), {}).setdefault(cname.upper(), {})[desc] = v
    return design
