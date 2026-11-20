"""Convert an arbitrary EnergyPlus model into a *BAS-ready* model.

The preparation step is the generic part of EmuBAS methodology. It applies a small
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
      - zone-equipment enable (heat pumps, PTACs, ERVs, baseboards, ideal loads: availability schedule)
      - stand-alone water-heater set point
T6  Physical fault hooks: EnergyPlus ``FaultModel:*`` objects are attached to primary plant
    equipment with a severity schedule initialised to 0 (fault free). Where EnergyPlus has no
    FaultModel, an equivalent hook is built from EMS objects driven by the same ACTIVE/VALUE
    schedule pair (all inactive by default, i.e. native behaviour):
      - DX heat-pump / PTAC coils: per-coil copies of the capacity and EIR f(T) curves whose
        ``Curve Result`` is overridden by ``r_Q f(T)`` and ``f_EIR(T) / r_COP`` (capacity / COP derate)
      - ERV plate/rotary heat exchangers: supply-outlet temperature control with an EMS set point
        (pass-through when healthy, partial bypass = effectiveness loss when faulted)
      - PV systems: a non-thermal electric load (``ElectricEquipment`` with fraction lost = 1, driven by
        its EMS ``Electricity Rate`` actuator) equal to the lost PV output (Generator:PVWatts ignores
        availability schedules and EMS power requests)
T7  Indoor air quality: zone CO2 mass balance is enabled with an actuatable outdoor CO2 schedule.
T8  Events: zones whose infiltration is not a DesignFlowRate object get a zero-flow DesignFlowRate
    object so that window/door events can add air exchange through the EMS infiltration actuator.

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
    ems: dict[str, Any] = field(default_factory=dict)      # EMS objects added by prepare (documentation)

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


def _erl(name: str) -> str:
    """EnergyPlus Runtime Language variable name (alphanumeric + underscore)."""
    return re.sub(r"[^A-Za-z0-9_]", "_", name)


CURVE_DIMS = {"Curve:Linear": 1, "Curve:Quadratic": 1, "Curve:Cubic": 1, "Curve:Quartic": 1, "Curve:Exponent": 1,
              "Curve:Biquadratic": 2, "Curve:Bicubic": 2, "Curve:QuadraticLinear": 2, "Curve:CubicLinear": 2}
DX_CURVE_FIELDS = {
    "Coil:Cooling:DX:SingleSpeed": ("total_cooling_capacity_function_of_temperature_curve_name",
                                    "energy_input_ratio_function_of_temperature_curve_name"),
    "Coil:Heating:DX:SingleSpeed": ("heating_capacity_function_of_temperature_curve_name",
                                    "energy_input_ratio_function_of_temperature_curve_name"),
}


def _find_curve(model: EpJSON, name: str) -> tuple[str, dict[str, Any]] | tuple[None, None]:
    for t in CURVE_DIMS:
        o = find_object(model, t, name)
        if o is not None:
            return t, o
    return None, None


class _EMS:
    """Small builder for the EMS objects of the physical fault hooks."""

    def __init__(self, model: EpJSON):
        self.m = model
        self.programs: list[str] = []
        self.sensors: set[str] = set()

    def sensor(self, erl: str, var: str, key: str) -> str:
        if erl not in self.sensors:
            add_object(self.m, "EnergyManagementSystem:Sensor", erl,
                       {"output_variable_or_output_meter_index_key_name": key,
                        "output_variable_or_output_meter_name": var})
            self.sensors.add(erl)
        return erl

    def actuator(self, erl: str, ctype: str, control: str, key: str) -> str:
        add_object(self.m, "EnergyManagementSystem:Actuator", erl,
                   {"actuated_component_unique_name": key, "actuated_component_type": ctype,
                    "actuated_component_control_type": control})
        return erl

    def curve_index(self, erl: str, curve: str) -> str:
        add_object(self.m, "EnergyManagementSystem:CurveOrTableIndexVariable", erl, {"curve_or_table_object_name": curve})
        return erl

    def program(self, name: str, lines: list[str]) -> None:
        add_object(self.m, "EnergyManagementSystem:Program", name, {"lines": [{"program_line": ln} for ln in lines]})
        self.programs.append(name)

    def finish(self) -> None:
        if self.programs:
            add_object(self.m, "EnergyManagementSystem:ProgramCallingManager", "VBAS Fault Hooks",
                       {"energyplus_model_calling_point": "InsideHVACSystemIterationLoop",
                        "programs": [{"program_name": n} for n in self.programs]})
            add_object(self.m, "EnergyManagementSystem:GlobalVariable", "EnergyManagementSystem:GlobalVariable VBAS Zero",
                       {"variables": [{"erl_variable_name": "vbas_zero"}]})


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

    # ---- T5 zone equipment: enable through the availability schedule ------------------------------
    native["zone_equipment"] = {}
    for ename, ze in topo.zone_equipment.items():
        o = find_object(model, ze.type, ename)
        if o is None:
            continue
        orig = o.get("availability_schedule_name")
        default = 1.0 if _first_numeric(original, orig, 1.0) > 0 else 0.0
        s_en = cmd(f"{ename} ENABLE", default, kind="zone_equipment_enable", equipment=ename, equipment_type=ze.type,
                   equipment_kind=ze.kind, zone=ze.zone, unit="-")
        native["zone_equipment"][ename] = {"avail_schedule": orig}
        o["availability_schedule_name"] = s_en
    # ---- T5 stand-alone water heaters: tank set point -------------------------------------------
    native["water_heaters"] = {}
    for wname, wh in topo.water_heaters.items():
        o = find_object(model, wh.type, wname)
        if o is None or not wh.standalone or wh.type != "WaterHeater:Mixed":
            continue
        orig = o.get("setpoint_temperature_schedule_name")
        s_sp = cmd(f"{wname} SP", _first_numeric(original, orig, 55.0), kind="water_heater_setpoint", equipment=wname,
                   unit="C")
        native["water_heaters"][wname] = {"sp_schedule": orig}
        o["setpoint_temperature_schedule_name"] = s_sp

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

    def sched_pair(key: str, value_default: float, extra: dict[str, float] | None = None) -> dict[str, str]:
        out = {"active_schedule": _safe(f"VBAS FAULT {key} ACTIVE"), "value_schedule": _safe(f"VBAS FAULT {key} VALUE")}
        add_schedule_constant(model, out["active_schedule"], 0.0, "VBAS Any Number")
        add_schedule_constant(model, out["value_schedule"], value_default, "VBAS Any Number")
        for k, v in (extra or {}).items():
            out[k] = _safe(f"VBAS FAULT {key} {k.split('_')[0].upper()}")
            add_schedule_constant(model, out[k], v, "VBAS Any Number")
        return out

    ems = _EMS(model)
    ems_doc: dict[str, Any] = {}
    # (a) DX heat pumps / PTACs: capacity and COP derate through curve overrides
    n_hp = 0
    for ename, ze in topo.zone_equipment.items():
        if ze.kind not in ("heat_pump", "ptac"):
            continue
        coils = [c for c in (ze.cooling_coil, ze.heating_coil) if c and c.type in DX_CURVE_FIELDS]
        if not coils:
            continue
        n_hp += 1
        tag = f"vbas_hp{n_hp}"
        key = f"{ename} DEGRADE"
        sch = sched_pair(key, 1.0, {"cop_schedule": 1.0})
        act = ems.sensor(f"{tag}_act", "Schedule Value", sch["active_schedule"])
        rq = ems.sensor(f"{tag}_rq", "Schedule Value", sch["value_schedule"])
        rc = ems.sensor(f"{tag}_rc", "Schedule Value", sch["cop_schedule"])
        toa = ems.sensor("vbas_toa", "Site Outdoor Air Drybulb Temperature", "Environment")
        pb = ems.sensor("vbas_pb", "Site Outdoor Air Barometric Pressure", "Environment")
        on, off, hooked = [], [], []
        for j, c in enumerate(coils):
            co = find_object(model, c.type, c.name)
            if co is None or not c.inlet:
                continue
            ctag = f"{tag}_c{j}"
            tin = ems.sensor(f"{ctag}_tin", "System Node Temperature", c.inlet)
            win = ems.sensor(f"{ctag}_win", "System Node Humidity Ratio", c.inlet)
            cooling = c.type.startswith("Coil:Cooling")
            if cooling:
                on.append(f"SET {ctag}_x = @TwbFnTdbWPb {tin} {win} {pb}")
            for fld, ratio, op, short in [(DX_CURVE_FIELDS[c.type][0], rq, "*", "cap"),
                                          (DX_CURVE_FIELDS[c.type][1], rc, "/", "eir")]:
                ctype, cobj = _find_curve(model, co.get(fld, ""))
                if ctype is None:
                    continue
                dims = CURVE_DIMS[ctype]
                clone = _safe(f"VBAS {c.name} {short.upper()}FT")
                add_object(model, ctype, clone, copy.deepcopy(cobj))
                idx = ems.curve_index(f"{ctag}_{short}_idx", co[fld])
                co[fld] = clone
                av = ems.actuator(f"{ctag}_{short}", "Curve", "Curve Result", clone)
                if cooling:            # f(entering wet bulb, outdoor dry bulb)
                    x, y = f"{ctag}_x", toa
                elif dims == 2:        # heating: f(entering dry bulb, outdoor dry bulb)
                    x, y = tin, toa
                else:                  # heating: f(outdoor dry bulb)
                    x, y = toa, "vbas_zero"
                if dims == 1 and cooling:
                    x, y = toa, "vbas_zero"
                on += [f"SET {ctag}_{short}0 = @CurveValue {idx} {x} {y} vbas_zero vbas_zero vbas_zero",
                       f"SET {av} = {ctag}_{short}0 {op} {ratio}"]
                off.append(f"SET {av} = Null")
                hooked.append(f"{c.name}:{short}")
        if not hooked:
            continue
        ems.program(f"{tag}_degrade", ["SET vbas_zero = 0.0", f"IF {act} > 0.5", *on, "ELSE", *off, "ENDIF"])
        faults[key] = {**sch, "value_default": 1.0, "object_type": "EnergyManagementSystem:Program",
                       "kind": "hp_degradation", "equipment": ename, "zone": ze.zone, "hooked": hooked,
                       "mechanism": "EMS Curve Result override: Q = r_Q f_Q(T), EIR = f_EIR(T) / r_COP"}
        ems_doc[key] = {"program": f"{tag}_degrade", "curves": hooked}
    # (b) ERV heat exchangers: effectiveness loss as partial supply bypass to an EMS set point
    n_erv = 0
    for ename, ze in topo.zone_equipment.items():
        x = ze.extra
        if ze.kind != "erv" or x.get("hx_type") != "HeatExchanger:AirToAir:SensibleAndLatent":
            continue
        hxo = find_object(model, x["hx_type"], x["hx"])
        if hxo is None or str(x.get("hx_temp_control", "No")).lower() != "no" or not x.get("hx_supply_outlet"):
            continue
        n_erv += 1
        tag = f"vbas_erv{n_erv}"
        key = f"{ename} HX"
        sch = sched_pair(key, 1.0)
        hxo["supply_air_outlet_temperature_control"] = "Yes"
        act = ems.sensor(f"{tag}_act", "Schedule Value", sch["active_schedule"])
        r = ems.sensor(f"{tag}_r", "Schedule Value", sch["value_schedule"])
        t_o = ems.sensor(f"{tag}_to", "System Node Temperature", x["hx_supply_inlet"])
        t_e = ems.sensor(f"{tag}_te", "System Node Temperature", x["hx_exhaust_inlet"])
        sp = ems.actuator(f"{tag}_sp", "System Node Setpoint", "Temperature Setpoint", x["hx_supply_outlet"])
        eh = x.get("eps_sens_heating") or 0.75
        ec = x.get("eps_sens_cooling") or eh
        ems.program(f"{tag}_hx", [
            f"IF {act} > 0.5",
            f"IF {t_o} < {t_e}",
            f"SET {sp} = {t_o} + {r} * {eh} * ({t_e} - {t_o})",
            "ELSE",
            f"SET {sp} = {t_o} + {r} * {ec} * ({t_e} - {t_o})",
            "ENDIF",
            f"ELSEIF {t_o} < {t_e}",
            f"SET {sp} = 99.0",
            "ELSE",
            f"SET {sp} = -99.0",
            "ENDIF"])
        faults[key] = {**sch, "value_default": 1.0, "object_type": "EnergyManagementSystem:Program", "kind": "erv_hx",
                       "equipment": ename, "hx": x["hx"], "setpoint_node": x["hx_supply_outlet"],
                       "mechanism": "HX supply-outlet temperature control: set point = T_oa + r eps (T_exh - T_oa) when "
                                    "faulted, pass-through (+/-99 C) when healthy"}
        ems_doc[key] = {"program": f"{tag}_hx"}
    ems.finish()
    # (c) PV systems: lost generation as an equivalent non-thermal electric load. A zone ElectricEquipment with
    #     fraction lost = 1 adds no heat to the zone; its EMS "Electricity Rate" actuator is applied in the same time
    #     step (internal gains are re-evaluated after the BeginTimestepBeforePredictor calling point, whereas exterior
    #     equipment is evaluated before it, i.e. one step late).
    host = next((z for z, zo in topo.zones.items() if zo.thermostat), next(iter(topo.zones), None))
    for dname, lc in topo.load_centers.items():
        if host is None or not any(g.type.startswith("Generator:P") for g in lc.generators):
            continue
        key = f"{dname} PV LOSS"
        obj = _safe(f"VBAS PV LOSS {dname}")
        add_object(model, "ElectricEquipment", obj, {
            "zone_or_zonelist_or_space_or_spacelist_name": host, "schedule_name": "VBAS Always Off",
            "design_level_calculation_method": "EquipmentLevel", "design_level": 0.0, "fraction_latent": 0.0,
            "fraction_radiant": 0.0, "fraction_lost": 1.0, "end_use_subcategory": "VBAS PV Loss"})
        faults[key] = {"object_type": "ElectricEquipment", "kind": "pv_loss", "load_center": dname, "loss_object": obj,
                       "host_zone": host, "value_default": 0.0,
                       "mechanism": "Generator:PVWatts output cannot be curtailed in EnergyPlus 23.2 (availability and "
                                    "EMS requested power are ignored); the lost AC power is drawn by a non-thermal "
                                    "ElectricEquipment (fraction lost = 1) through its EMS Electricity Rate actuator, so "
                                    "that grid import/export and storage respond physically"}

    # ---- T8 window / door events need an actuatable infiltration object -------------------------
    for zname, z in topo.zones.items():
        if z.thermostat and not z.infiltration and z.infiltration_other:
            iname = _safe(f"VBAS INFIL {zname}")
            add_object(model, "ZoneInfiltration:DesignFlowRate", iname, {
                "zone_or_zonelist_or_space_or_spacelist_name": zname, "schedule_name": "VBAS Always On",
                "design_flow_rate_calculation_method": "Flow/Zone", "design_flow_rate": 0.0,
                "constant_term_coefficient": 1.0, "temperature_term_coefficient": 0.0,
                "velocity_term_coefficient": 0.0, "velocity_squared_term_coefficient": 0.0})
            z.infiltration_window = iname

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
                        energyplus_version=eplus.version_string(), native=native, ems=ems_doc)
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
