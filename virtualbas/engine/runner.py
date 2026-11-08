"""Step-wise (co-simulation) EnergyPlus runner.

EnergyPlus runs in a worker thread. At the beginning of every zone time step the runner

1. reads all requested output variables, meters and internal variables (the *inner* state),
2. calls the user supplied ``on_step(sample) -> commands`` function, which may block
   (pause, real-time pacing, waiting for an external agent),
3. writes the returned actuator values back into EnergyPlus.

Because EnergyPlus is suspended while ``on_step`` runs, the simulation advances exactly one
time step per call - EnergyPlus is a stepped plant model, not a batch job.
"""
from __future__ import annotations

import datetime as dt
import threading
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .. import eplus

VarKey = tuple[str, str]           # (variable name, key)
ActKey = tuple[str, str, str]      # (component type, control type, key)
RUN_PERIOD_WEATHER = 3            # EnergyPlus KindOfSim::RunPeriodWeather


@dataclass
class Sample:
    time: dt.datetime                 # time stamp the values refer to (end of previous step)
    step: int                         # 0-based step counter (excluding warm-up)
    warmup: bool
    values: dict[str, float]          # alias -> value
    dt_seconds: float
    day_of_week: int = 1              # 1 = Sunday ... 7 = Saturday (EnergyPlus convention)
    holiday: int = 0


@dataclass
class EngineSpec:
    variables: dict[str, VarKey] = field(default_factory=dict)
    meters: dict[str, str] = field(default_factory=dict)
    internal: dict[str, tuple[str, str]] = field(default_factory=dict)
    actuators: dict[str, ActKey] = field(default_factory=dict)


class EnergyPlusEngine:
    def __init__(self, model: str | Path, weather: str | Path, out_dir: str | Path, spec: EngineSpec,
                 on_step: Callable[[Sample], dict[str, float | None]], year: int = 2023,
                 console: bool = False):
        self.model = Path(model)
        self.weather = Path(weather)
        self.out_dir = Path(out_dir)
        self.spec = spec
        self.on_step = on_step
        self.year = year
        self.console = console
        self.api = eplus.api()
        self.state = None
        self._handles_ready = False
        self._vh: dict[str, int] = {}
        self._mh: dict[str, int] = {}
        self._ih: dict[str, int] = {}
        self._ah: dict[str, int] = {}
        self.internal_values: dict[str, float] = {}
        self.missing: list[str] = []
        self.step = 0
        self.thread: threading.Thread | None = None
        self.exit_code: int | None = None
        self.error: BaseException | None = None
        self.finished = threading.Event()
        self._stop_requested = False
        # weather perturbation applied when EnergyPlus sets the current weather
        self.weather_offsets: dict[str, float] = {"tdb": 0.0, "rh": 0.0, "solar_mult": 1.0}
        self._wx_actuated = False
        self._wx_handles: dict[str, int] = {}
        self._iter_cmds: dict[str, tuple[int, float]] = {}

    # ------------------------------------------------------------------ handles
    def _init_handles(self, state) -> None:
        ex = self.api.exchange
        for alias, (name, key) in self.spec.variables.items():
            h = ex.get_variable_handle(state, name, key)
            if h < 0:
                self.missing.append(f"variable:{name}:{key}")
            else:
                self._vh[alias] = h
        for alias, name in self.spec.meters.items():
            h = ex.get_meter_handle(state, name)
            if h < 0:
                self.missing.append(f"meter:{name}")
            else:
                self._mh[alias] = h
        for alias, (name, key) in self.spec.internal.items():
            h = ex.get_internal_variable_handle(state, name, key)
            if h < 0:
                self.missing.append(f"internal:{name}:{key}")
            else:
                self._ih[alias] = h
        for alias, (ctype, control, key) in self.spec.actuators.items():
            h = ex.get_actuator_handle(state, ctype, control, key)
            if h < 0:
                self.missing.append(f"actuator:{ctype}:{control}:{key}")
            else:
                self._ah[alias] = h
        for alias, h in self._ih.items():
            self.internal_values[alias] = ex.get_internal_variable_value(state, h)
        self._handles_ready = True

    def _timestamp(self, state) -> dt.datetime:
        ex = self.api.exchange
        month, day, hour, minute = ex.month(state), ex.day_of_month(state), ex.hour(state), ex.minutes(state)
        end = dt.datetime(self.year, month, day) + dt.timedelta(hours=hour, minutes=minute)
        # values available at the beginning of a step belong to the end of the previous step
        return end - dt.timedelta(seconds=self.dt_seconds)

    # ------------------------------------------------------------------ callbacks
    def _cb_begin(self, state) -> None:
        try:
            ex = self.api.exchange
            if not ex.api_data_fully_ready(state):
                return
            if ex.kind_of_sim(state) != RUN_PERIOD_WEATHER:
                return  # sizing / HVAC-sizing environments are not part of the BAS time line
            if not self._handles_ready:
                self._init_handles(state)
            self._dt = 3600.0 / max(1, ex.num_time_steps_in_hour(state))
            if self._stop_requested:
                self.api.runtime.stop_simulation(state)
                return
            warm = bool(ex.warmup_flag(state))
            values = {a: ex.get_variable_value(state, h) for a, h in self._vh.items()}
            for a, h in self._mh.items():
                values[a] = ex.get_meter_value(state, h)
            sample = Sample(time=self._timestamp(state), step=self.step, warmup=warm, values=values,
                            dt_seconds=self.dt_seconds, day_of_week=ex.day_of_week(state),
                            holiday=ex.holiday_index(state))
            cmds = self.on_step(sample)
            if not warm:
                self.step += 1
            for alias, val in (cmds or {}).items():
                h = self._ah.get(alias)
                if h is None:
                    continue
                if val is None:
                    ex.reset_actuator(state, h)
                    self._iter_cmds.pop(alias, None)
                else:
                    ex.set_actuator_value(state, h, float(val))
                    # plant supervisory overrides are cleared by EnergyPlus during the HVAC iterations and
                    # must be re-applied inside the system iteration loop
                    if self.spec.actuators[alias][1] == "On/Off Supervisory":
                        self._iter_cmds[alias] = (h, float(val))
            if self._stop_requested:
                self.api.runtime.stop_simulation(state)
        except BaseException as e:  # noqa: BLE001 - must not propagate into C
            self.error = e
            traceback.print_exc()
            self.api.runtime.stop_simulation(state)

    def _cb_iteration(self, state) -> None:
        if not self._iter_cmds:
            return
        ex = self.api.exchange
        for h, v in self._iter_cmds.values():
            ex.set_actuator_value(state, h, v)

    def _cb_weather(self, state) -> None:
        try:
            ex = self.api.exchange
            if not ex.api_data_fully_ready(state) or ex.kind_of_sim(state) != RUN_PERIOD_WEATHER:
                return
            if not self._wx_handles:
                for k, c in [("tdb", "Outdoor Dry Bulb"), ("rh", "Outdoor Relative Humidity"),
                             ("dir", "Direct Solar"), ("dif", "Diffuse Solar")]:
                    self._wx_handles[k] = ex.get_actuator_handle(state, "Weather Data", c, "Environment")
            off = self.weather_offsets
            active = abs(off.get("tdb", 0.0)) > 1e-9 or abs(off.get("rh", 0.0)) > 1e-9 or abs(off.get("solar_mult", 1.0) - 1) > 1e-9
            if not active:
                if self._wx_actuated:
                    for h in self._wx_handles.values():
                        if h >= 0:
                            ex.reset_actuator(state, h)
                    self._wx_actuated = False
                return
            hr = ex.hour(state)
            ts = ex.zone_time_step_number(state)
            tdb = ex.today_weather_outdoor_dry_bulb_at_time(state, hr, ts) + off.get("tdb", 0.0)
            rh = min(100.0, max(1.0, ex.today_weather_outdoor_relative_humidity_at_time(state, hr, ts) + off.get("rh", 0.0)))
            m = max(0.0, off.get("solar_mult", 1.0))
            vals = {"tdb": tdb, "rh": rh,
                    "dir": ex.today_weather_beam_solar_at_time(state, hr, ts) * m,
                    "dif": ex.today_weather_diffuse_solar_at_time(state, hr, ts) * m}
            for k, v in vals.items():
                h = self._wx_handles.get(k, -1)
                if h >= 0:
                    ex.set_actuator_value(state, h, float(v))
            self._wx_actuated = True
        except BaseException as e:  # noqa: BLE001
            self.error = e
            traceback.print_exc()
            self.api.runtime.stop_simulation(state)

    # ------------------------------------------------------------------ run
    @property
    def dt_seconds(self) -> float:
        return getattr(self, "_dt", 300.0)

    def _run(self) -> None:
        rt, ex = self.api.runtime, self.api.exchange
        self.state = self.api.state_manager.new_state()
        st = self.state
        for alias, (name, key) in self.spec.variables.items():
            ex.request_variable(st, name, key)
        rt.set_console_output_status(st, self.console)

        def begin_env(s):
            self._dt = ex.zone_time_step(s) * 3600.0
        rt.callback_after_new_environment_warmup_complete(st, begin_env)
        rt.callback_begin_new_environment(st, begin_env)
        rt.callback_begin_system_timestep_before_predictor(st, self._cb_begin)
        rt.callback_begin_zone_timestep_before_set_current_weather(st, self._cb_weather)
        rt.callback_inside_system_iteration_loop(st, self._cb_iteration)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        try:
            self.exit_code = rt.run_energyplus(st, ["-w", str(self.weather), "-d", str(self.out_dir), str(self.model)])
        except BaseException as e:  # noqa: BLE001
            self.error = e
        finally:
            self.finished.set()

    def start(self) -> None:
        self.thread = threading.Thread(target=self._run, name="energyplus", daemon=True)
        self.thread.start()

    def run_blocking(self) -> int | None:
        self._run()
        return self.exit_code

    def stop(self) -> None:
        self._stop_requested = True

    def close(self) -> None:
        if self.state is not None:
            try:
                self.api.state_manager.delete_state(self.state)
            except Exception:  # noqa: BLE001
                pass
            self.state = None
