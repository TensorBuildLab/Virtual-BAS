"""BAS point catalog generated automatically from the discovered HVAC topology.

Each BAS point has:
* a stable identifier ``<EQUIP>/<POINT>`` (e.g. ``AHU-1/SA-T``),
* semantic metadata (Project-Haystack style tags and a Brick class) so that AI agents can
  reason about the point list without building-specific knowledge,
* a binding to the *inner space* (EnergyPlus output variable, meter or derived quantity)
  from which the true physical value is obtained, and
* a sensor class that determines its real-world imperfections.

Equipment covered: zones, VAV terminal units, air handling units (economizer, coils, fan,
filter), chillers, boilers, cooling towers, pumps, plant loops, weather station and meters.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable

from ..model.prepare import Manifest

RHO_AIR = 1.204       # kg/m3 (standard air) for volumetric flow reporting
RHO_WATER = 998.0     # kg/m3


@dataclass
class Point:
    id: str
    equip: str
    equip_type: str
    name: str
    description: str
    unit: str
    kind: str                      # sensor | command | setpoint | status | virtual | meter | truth
    sensor_class: str = "ideal"
    tags: list[str] = field(default_factory=list)
    brick: str = ""
    writable: bool = False
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Equipment:
    id: str
    type: str
    eplus_name: str
    description: str
    parent: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)
    points: list[str] = field(default_factory=list)


@dataclass
class Catalog:
    points: dict[str, Point] = field(default_factory=dict)
    equipment: dict[str, Equipment] = field(default_factory=dict)
    variables: dict[str, tuple[str, str]] = field(default_factory=dict)   # raw alias -> (var, key)
    meters: dict[str, str] = field(default_factory=dict)
    actuators: dict[str, tuple[str, str, str]] = field(default_factory=dict)
    truth: dict[str, Callable[[dict[str, float], float], float]] = field(default_factory=dict)
    zone_of_equip: dict[str, str] = field(default_factory=dict)

    # ------------------------------------------------------------------ helpers
    def add_equip(self, e: Equipment) -> Equipment:
        self.equipment[e.id] = e
        return e

    def add_point(self, p: Point, truth: Callable[[dict[str, float], float], float] | None = None) -> Point:
        self.points[p.id] = p
        if p.equip in self.equipment:
            self.equipment[p.equip].points.append(p.id)
        if truth is not None:
            self.truth[p.id] = truth
        return p

    def var(self, name: str, key: str) -> str:
        alias = f"{name}|{key}".upper()
        self.variables[alias] = (name, key)
        return alias

    def meter(self, name: str) -> str:
        alias = f"METER|{name}".upper()
        self.meters[alias] = name
        return alias

    def actuator(self, ctype: str, control: str, key: str) -> str:
        alias = f"{ctype}|{control}|{key}".upper()
        self.actuators[alias] = (ctype, control, key.upper())
        return alias

    def schedule_actuator(self, sched_name: str) -> str:
        return self.actuator("Schedule:Constant", "Schedule Value", sched_name)

    def points_of(self, equip_id: str) -> list[Point]:
        return [self.points[p] for p in self.equipment[equip_id].points]

    def equipment_of_type(self, t: str) -> list[Equipment]:
        return [e for e in self.equipment.values() if e.type == t]

    def summary(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for p in self.points.values():
            out[p.kind] = out.get(p.kind, 0) + 1
        return out


def rh_from_tw(t: float, w: float, p: float = 101325.0) -> float:
    """Relative humidity [%] from dry-bulb temperature [C] and humidity ratio [kg/kg] (ASHRAE psychrometrics)."""
    import math
    if not (math.isfinite(t) and math.isfinite(w)):
        return float("nan")
    pws = 610.94 * math.exp(17.625 * t / (t + 243.04))    # Magnus-Tetens saturation pressure [Pa]
    pw = w * p / (0.621945 + w)
    return max(0.0, min(100.0, 100.0 * pw / pws))


def _id_safe(name: str) -> str:
    return name.replace(" ", "_")


def build_catalog(man: Manifest) -> Catalog:
    topo = man.topo
    cat = Catalog()
    co2 = man.options.get("enable_co2", True)

    def sensor(equip, etype, name, desc, unit, sclass, truth, tags, brick, kind="sensor", **meta):
        return cat.add_point(Point(id=f"{equip}/{name}", equip=equip, equip_type=etype, name=name, description=desc,
                                   unit=unit, kind=kind, sensor_class=sclass, tags=tags, brick=brick, meta=meta), truth)

    def soft(equip, etype, name, desc, unit, kind, tags, brick, writable=True, **meta):
        return cat.add_point(Point(id=f"{equip}/{name}", equip=equip, equip_type=etype, name=name, description=desc,
                                   unit=unit, kind=kind, sensor_class="ideal", tags=tags, brick=brick,
                                   writable=writable, meta=meta))

    def raw(alias, scale=1.0, offset=0.0):
        return lambda v, dt, a=alias, s=scale, o=offset: v.get(a, float("nan")) * s + o

    # ---------------------------------------------------------------- weather
    wx = cat.add_equip(Equipment("WX", "WeatherStation", "Environment", "Rooftop weather station"))
    sensor(wx.id, "WeatherStation", "OA-T", "Outdoor air dry-bulb temperature", "degC", "outdoor_temperature",
           raw(cat.var("Site Outdoor Air Drybulb Temperature", "Environment")), ["outside", "air", "temp", "sensor"],
           "Outside_Air_Temperature_Sensor")
    sensor(wx.id, "WeatherStation", "OA-RH", "Outdoor air relative humidity", "%RH", "humidity",
           raw(cat.var("Site Outdoor Air Relative Humidity", "Environment")), ["outside", "air", "humidity", "sensor"],
           "Outside_Air_Humidity_Sensor")
    sensor(wx.id, "WeatherStation", "OA-WB", "Outdoor air wet-bulb temperature (calculated by station)", "degC",
           "outdoor_temperature", raw(cat.var("Site Outdoor Air Wetbulb Temperature", "Environment")),
           ["outside", "air", "wetBulb", "temp", "sensor"], "Outside_Air_Wet_Bulb_Temperature_Sensor")
    sensor(wx.id, "WeatherStation", "WIND", "Wind speed", "m/s", "speed",
           raw(cat.var("Site Wind Speed", "Environment")), ["outside", "wind", "speed", "sensor"], "Wind_Speed_Sensor")
    a1 = cat.var("Site Direct Solar Radiation Rate per Area", "Environment")
    a2 = cat.var("Site Diffuse Solar Radiation Rate per Area", "Environment")
    sensor(wx.id, "WeatherStation", "SOLAR", "Global horizontal irradiance (pyranometer)", "W/m2", "solar",
           lambda v, dt: v.get(a1, 0.0) + v.get(a2, 0.0), ["outside", "solar", "irradiance", "sensor"],
           "Solar_Radiance_Sensor")

    # ---------------------------------------------------------------- meters
    mtr = cat.add_equip(Equipment("MTR", "Meter", "Facility", "Utility and sub-meters"))
    for name, mname, desc in [("BLDG-ELEC-KW", "Electricity:Facility", "Whole-building electric demand"),
                              ("BLDG-GAS-KW", "NaturalGas:Facility", "Whole-building natural gas rate"),
                              ("HVAC-ELEC-KW", "Electricity:HVAC", "HVAC electric demand"),
                              ("LIGHT-KW", "InteriorLights:Electricity", "Interior lighting demand"),
                              ("PLUG-KW", "InteriorEquipment:Electricity", "Plug and process load demand"),
                              ("CLG-ELEC-KW", "Cooling:Electricity", "Cooling (chiller) electric demand"),
                              ("FAN-ELEC-KW", "Fans:Electricity", "Fan electric demand"),
                              ("PUMP-ELEC-KW", "Pumps:Electricity", "Pump electric demand"),
                              ("HREJ-ELEC-KW", "HeatRejection:Electricity", "Heat rejection electric demand"),
                              ("HTG-GAS-KW", "Heating:NaturalGas", "Heating natural gas rate")]:
        al = cat.meter(mname)
        sensor(mtr.id, "Meter", name, desc, "kW", "energy", lambda v, dt, a=al: v.get(a, 0.0) / dt / 1000.0,
               ["power", "sensor", "meter"], "Electric_Power_Sensor", kind="meter", meter=mname)

    # ---------------------------------------------------------------- zones & terminals
    zones = [z for z in topo.zones.values() if z.thermostat]
    for z in zones:
        zid = f"ZN-{_id_safe(z.name)}"
        ahu_of_loop = {ln: f"AHU-{i}" for i, ln in enumerate(sorted(topo.air_loops), start=1)}
        cat.add_equip(Equipment(zid, "Zone", z.name, f"Thermal zone {z.name}" + (f" (x{z.multiplier} floors)" if z.multiplier > 1 else ""),
                                meta={"multiplier": z.multiplier, "air_loop": z.air_loop, "terminal": z.terminal,
                                      "ahu": ahu_of_loop.get(z.air_loop)}))
        cat.zone_of_equip[zid] = z.name
        sensor(zid, "Zone", "ZN-T", "Zone air temperature", "degC", "zone_temperature",
               raw(cat.var("Zone Air Temperature", z.name)), ["zone", "air", "temp", "sensor"], "Zone_Air_Temperature_Sensor")
        sensor(zid, "Zone", "ZN-RH", "Zone air relative humidity", "%RH", "humidity",
               raw(cat.var("Zone Air Relative Humidity", z.name)), ["zone", "air", "humidity", "sensor"], "Zone_Air_Humidity_Sensor")
        if co2:
            sensor(zid, "Zone", "ZN-CO2", "Zone CO2 concentration", "ppm", "co2",
                   raw(cat.var("Zone Air CO2 Concentration", z.name)), ["zone", "air", "co2", "sensor"], "CO2_Sensor")
        occ = cat.var("Zone People Occupant Count", z.name)
        sensor(zid, "Zone", "ZN-OCC", "Zone occupancy sensor (PIR)", "-", "occupancy",
               lambda v, dt, a=occ: 1.0 if v.get(a, 0.0) > 0.01 else 0.0, ["zone", "occupied", "sensor"], "Occupancy_Sensor")
        sensor(zid, "Zone", "OCCUPANTS", "True number of occupants (ground truth only)", "people", "ideal",
               raw(occ), ["zone", "occupants"], "Occupancy_Count_Sensor", kind="truth")
        pmv = cat.var("Zone Thermal Comfort Fanger Model PMV", z.people[0]) if z.people else None
        if pmv:
            sensor(zid, "Zone", "PMV", "Fanger predicted mean vote (ground truth only)", "-", "ideal", raw(pmv),
                   ["zone", "comfort"], "", kind="truth")
        sensor(zid, "Zone", "LIGHT-KW", "Zone lighting power", "kW", "power",
               raw(cat.var("Zone Lights Electricity Rate", z.name), 0.001), ["zone", "lights", "power", "sensor"],
               "Electric_Power_Sensor", kind="meter")
        sensor(zid, "Zone", "PLUG-KW", "Zone plug load power", "kW", "power",
               raw(cat.var("Zone Electric Equipment Electricity Rate", z.name), 0.001), ["zone", "plug", "power", "sensor"],
               "Electric_Power_Sensor", kind="meter")
        soft(zid, "Zone", "HTG-SP", "Active heating set point", "degC", "setpoint", ["zone", "air", "temp", "heating", "sp"],
             "Zone_Air_Heating_Temperature_Setpoint", writable=False)
        soft(zid, "Zone", "CLG-SP", "Active cooling set point", "degC", "setpoint", ["zone", "air", "temp", "cooling", "sp"],
             "Zone_Air_Cooling_Temperature_Setpoint", writable=False)
        soft(zid, "Zone", "OCC-HTG-SP", "Occupied heating set point", "degC", "setpoint", ["zone", "occ", "heating", "sp"],
             "Occupied_Air_Temperature_Heating_Setpoint")
        soft(zid, "Zone", "OCC-CLG-SP", "Occupied cooling set point", "degC", "setpoint", ["zone", "occ", "cooling", "sp"],
             "Occupied_Air_Temperature_Cooling_Setpoint")
        soft(zid, "Zone", "OCC-MODE", "Zone occupancy mode (1 occupied / 0 unoccupied)", "-", "status", ["zone", "occ", "mode"],
             "Occupancy_Status", writable=False)
        # inner actuators bound to this zone
        cat.actuator("Zone Temperature Control", "Heating Setpoint", z.name)
        cat.actuator("Zone Temperature Control", "Cooling Setpoint", z.name)
        for p in z.people:
            cat.actuator("People", "Number of People", p)
        for li in z.lights:
            cat.actuator("Lights", "Electricity Rate", li)
        for e in z.equipment:
            cat.actuator("ElectricEquipment", "Electricity Rate", e)
        for inf in z.infiltration:
            cat.actuator("Zone Infiltration", "Air Exchange Flow Rate", inf)

        # terminal unit
        if not z.terminal or z.terminal not in topo.terminals:
            continue
        t = topo.terminals[z.terminal]
        vid = f"VAV-{_id_safe(z.name)}"
        vmax = man.design_value(t.type, t.name, "Maximum Air Flow Rate [m3/s]", 1.0) or 1.0
        frac_min = man.commands.get(f"{t.name} FLOW", {}).get("default", 0.3)
        if man.commands.get(f"{t.name} FLOW", {}).get("autosized"):
            frac_min = man.design_value(t.type, t.name, "Constant Minimum Air Flow Fraction", frac_min) or frac_min
        rh_w = man.commands.get(f"{t.name} FLOW", {}).get("reheat_max_water_m3s")
        vmax = man.commands.get(f"{t.name} FLOW", {}).get("vmax_m3s") or vmax
        if t.reheat and not rh_w:
            rh_w = man.design_value(t.reheat.type, t.reheat.name, "Maximum Water Flow Rate", None) or \
                man.design_value(t.type, t.name, "Maximum Reheat Water Flow Rate", None)
        cat.add_equip(Equipment(vid, "VAV", t.name, f"VAV terminal with hot-water reheat serving {z.name}", parent=None,
                                meta={"zone": z.name, "zone_equip": zid, "air_loop": t.air_loop, "vmax_m3s": vmax,
                                      "vmin_frac": frac_min, "reheat_max_water_m3s": rh_w,
                                      "flow_cmd_schedule": man.commands.get(f"{t.name} FLOW", {}).get("schedule"),
                                      "reheat_coil": t.reheat.name if t.reheat else None}))
        cat.equipment[zid].parent = vid
        fl = cat.var("System Node Mass Flow Rate", t.outlet)
        sensor(vid, "VAV", "DA-F", "Discharge air flow", "m3/s", "air_flow", raw(fl, 1 / RHO_AIR),
               ["discharge", "air", "flow", "sensor"], "Discharge_Air_Flow_Sensor")
        sensor(vid, "VAV", "DA-T", "Discharge air temperature", "degC", "air_temperature",
               raw(cat.var("System Node Temperature", t.outlet)), ["discharge", "air", "temp", "sensor"],
               "Discharge_Air_Temperature_Sensor")
        sensor(vid, "VAV", "DMPR-POS", "Damper position feedback", "%", "position",
               lambda v, dt, a=fl, vm=vmax: 100.0 * min(1.0, v.get(a, 0.0) / RHO_AIR / vm), ["damper", "position", "sensor"],
               "Damper_Position_Sensor")
        if t.reheat and t.reheat.water_inlet:
            wf = cat.var("System Node Mass Flow Rate", t.reheat.water_inlet)
            wmax = (rh_w or 1e-3) * RHO_WATER
            sensor(vid, "VAV", "RHV-POS", "Reheat valve position (feedback)", "%", "position",
                   lambda v, dt, a=wf, m=wmax: 100.0 * min(1.0, v.get(a, 0.0) / m), ["reheat", "valve", "position", "sensor"],
                   "Valve_Position_Sensor")
            sensor(vid, "VAV", "RH-Q", "Reheat coil heat rate (ground truth)", "kW", "ideal",
                   raw(cat.var("Heating Coil Heating Rate", t.reheat.name), 0.001), ["reheat", "heat", "power"], "", kind="truth")
            cat.actuator("Plant Component Coil:Heating:Water", "On/Off Supervisory", t.reheat.name)
        soft(vid, "VAV", "DA-F-SP", "Discharge air flow set point", "m3/s", "setpoint", ["discharge", "air", "flow", "sp"],
             "Discharge_Air_Flow_Setpoint", writable=False)
        soft(vid, "VAV", "DMPR-CMD", "Damper command", "%", "command", ["damper", "cmd"], "Damper_Position_Command", writable=False)
        soft(vid, "VAV", "CLG-LOOP", "Cooling loop output", "%", "virtual", ["cooling", "loop"], "", writable=False)
        soft(vid, "VAV", "HTG-LOOP", "Heating loop output", "%", "virtual", ["heating", "loop"], "", writable=False)
        cs = man.commands.get(f"{t.name} FLOW", {}).get("schedule")
        if cs:
            cat.schedule_actuator(cs)

    # ---------------------------------------------------------------- air handling units
    for i, (lname, loop) in enumerate(sorted(topo.air_loops.items()), start=1):
        aid = f"AHU-{i}"
        vd = man.design_value("AirLoopHVAC", lname, "Supply Air Flow Rate", None) or \
            (man.design_value(loop.fan.type, loop.fan.name, "maximum_flow_rate", 1.0) if loop.fan else 1.0)
        oa_min = man.design_value("Controller:OutdoorAir", loop.oa_controller or "", "Minimum Outdoor Air Flow Rate", 0.0) or 0.0
        cc = loop.cooling_coils[0] if loop.cooling_coils else None
        hc = loop.heating_coils[0] if loop.heating_coils else None
        cc_w = man.design_value(cc.type, cc.name, "design_water_flow_rate", None) if cc else None
        hc_w = man.design_value(hc.type, hc.name, "Maximum Water Flow Rate", None) if hc else None
        fan_dp = None
        cat.add_equip(Equipment(aid, "AHU", lname, f"Air handling unit {lname} (VAV, economizer, CHW/HW coils)",
                                meta={"air_loop": lname, "design_flow_m3s": vd, "min_oa_m3s": oa_min,
                                      "zones": loop.zones, "terminals": loop.terminals,
                                      "vav": [f"VAV-{_id_safe(topo.terminals[t].zone)}" for t in loop.terminals],
                                      "zone_equips": [f"ZN-{_id_safe(z)}" for z in loop.zones],
                                      "fan": loop.fan.name if loop.fan else None, "fan_type": loop.fan.type if loop.fan else None,
                                      "oa_controller": loop.oa_controller,
                                      "cc_design_water_m3s": cc_w, "hc_design_water_m3s": hc_w,
                                      "sat_schedule": man.commands.get(f"{lname} SAT", {}).get("schedule"),
                                      "fan_schedule": man.commands.get(f"{lname} FAN", {}).get("schedule"),
                                      "fan_pressure_rise_pa": fan_dp}))
        for v in loop.zones:
            vid = f"VAV-{_id_safe(v)}"
            if vid in cat.equipment:
                cat.equipment[vid].parent = aid
        sa_m = cat.var("System Node Mass Flow Rate", loop.supply_outlet)
        sensor(aid, "AHU", "SA-T", "Supply air temperature", "degC", "air_temperature",
               raw(cat.var("System Node Temperature", loop.supply_outlet)), ["discharge", "air", "temp", "sensor"],
               "Supply_Air_Temperature_Sensor")
        _t, _w = cat.var("System Node Temperature", loop.supply_outlet), cat.var("System Node Humidity Ratio", loop.supply_outlet)
        sensor(aid, "AHU", "SA-RH", "Supply air relative humidity", "%RH", "humidity",
               lambda v, dt, a=_t, b=_w: rh_from_tw(v.get(a, float("nan")), v.get(b, float("nan"))),
               ["discharge", "air", "humidity", "sensor"], "Supply_Air_Humidity_Sensor")
        sensor(aid, "AHU", "SA-F", "Supply air flow", "m3/s", "air_flow", raw(sa_m, 1 / RHO_AIR),
               ["discharge", "air", "flow", "sensor"], "Supply_Air_Flow_Sensor")
        if loop.mixed_air_node:
            sensor(aid, "AHU", "MA-T", "Mixed air temperature", "degC", "air_temperature",
                   raw(cat.var("System Node Temperature", loop.mixed_air_node)), ["mixed", "air", "temp", "sensor"],
                   "Mixed_Air_Temperature_Sensor")
        if loop.return_node:
            sensor(aid, "AHU", "RA-T", "Return air temperature", "degC", "air_temperature",
                   raw(cat.var("System Node Temperature", loop.return_node)), ["return", "air", "temp", "sensor"],
                   "Return_Air_Temperature_Sensor")
            _t, _w = cat.var("System Node Temperature", loop.return_node), cat.var("System Node Humidity Ratio", loop.return_node)
            sensor(aid, "AHU", "RA-RH", "Return air relative humidity", "%RH", "humidity",
                   lambda v, dt, a=_t, b=_w: rh_from_tw(v.get(a, float("nan")), v.get(b, float("nan"))),
                   ["return", "air", "humidity", "sensor"], "Return_Air_Humidity_Sensor")
        if loop.oa_node:
            oa_m = cat.var("System Node Mass Flow Rate", loop.oa_node)
            sensor(aid, "AHU", "OA-F", "Outdoor air flow (airflow measuring station)", "m3/s", "air_flow",
                   raw(oa_m, 1 / RHO_AIR), ["outside", "air", "flow", "sensor"], "Outside_Air_Flow_Sensor")
            sensor(aid, "AHU", "OAD-POS", "Outdoor air damper position (feedback)", "%", "position",
                   lambda v, dt, a=oa_m, b=sa_m: 100.0 * min(1.0, v.get(a, 0.0) / v.get(b, 0.0)) if v.get(b, 0.0) > 1e-3 else 0.0,
                   ["outside", "damper", "position", "sensor"], "Damper_Position_Sensor")
            cat.actuator("Outdoor Air Controller", "Air Mass Flow Rate", loop.oa_controller or "")
        if cc and cc.water_inlet:
            cw = cat.var("System Node Mass Flow Rate", cc.water_inlet)
            m = (cc_w or 1e-2) * RHO_WATER
            sensor(aid, "AHU", "CCV-POS", "Cooling coil valve position (feedback)", "%", "position",
                   lambda v, dt, a=cw, mm=m: 100.0 * min(1.0, v.get(a, 0.0) / mm), ["cooling", "valve", "position", "sensor"],
                   "Valve_Position_Sensor")
            sensor(aid, "AHU", "CC-Q", "Cooling coil total load (ground truth)", "kW", "ideal",
                   raw(cat.var("Cooling Coil Total Cooling Rate", cc.name), 0.001), ["cooling", "coil", "power"], "", kind="truth")
            sensor(aid, "AHU", "CC-LAT", "Cooling coil leaving air temperature", "degC", "air_temperature",
                   raw(cat.var("System Node Temperature", cc.outlet)), ["cooling", "coil", "leaving", "air", "temp", "sensor"],
                   "Air_Temperature_Sensor")
            cat.actuator("Plant Component Coil:Cooling:Water", "On/Off Supervisory", cc.name)
        if hc and hc.water_inlet:
            hw = cat.var("System Node Mass Flow Rate", hc.water_inlet)
            m = (hc_w or 1e-2) * RHO_WATER
            sensor(aid, "AHU", "HCV-POS", "Heating (preheat) coil valve position (feedback)", "%", "position",
                   lambda v, dt, a=hw, mm=m: 100.0 * min(1.0, v.get(a, 0.0) / mm), ["heating", "valve", "position", "sensor"],
                   "Valve_Position_Sensor")
            cat.actuator("Plant Component Coil:Heating:Water", "On/Off Supervisory", hc.name)
        if loop.fan:
            fp = cat.var("Fan Electricity Rate", loop.fan.name)
            sensor(aid, "AHU", "SF-KW", "Supply fan power (VFD)", "kW", "power", raw(fp, 0.001),
                   ["discharge", "fan", "power", "sensor"], "Electric_Power_Sensor")
            sensor(aid, "AHU", "SF-SPD", "Supply fan speed (VFD output)", "%", "percent",
                   lambda v, dt, a=sa_m, d=vd: 100.0 * min(1.0, v.get(a, 0.0) / RHO_AIR / d), ["discharge", "fan", "speed", "sensor"],
                   "Frequency_Sensor")
            sensor(aid, "AHU", "SF-STS", "Supply fan status (current switch)", "-", "binary",
                   lambda v, dt, a=sa_m, d=vd: 1.0 if v.get(a, 0.0) / RHO_AIR > 0.05 * d else 0.0,
                   ["discharge", "fan", "run", "sensor"], "Fan_Status")
            cat.actuator("Fan", "Fan Pressure Rise", loop.fan.name)
            cat.actuator("Fan", "Fan Total Efficiency", loop.fan.name)
        sensor(aid, "AHU", "DSP", "Duct static pressure (surrogate model)", "Pa", "pressure", None,
               ["discharge", "air", "pressure", "sensor"], "Static_Pressure_Sensor", surrogate=True)
        sensor(aid, "AHU", "FLT-DP", "Filter differential pressure (surrogate model)", "Pa", "pressure", None,
               ["filter", "air", "pressure", "sensor"], "Filter_Differential_Pressure_Sensor", surrogate=True)
        soft(aid, "AHU", "SA-T-SP", "Supply air temperature set point", "degC", "setpoint", ["discharge", "air", "temp", "sp"],
             "Supply_Air_Temperature_Setpoint", writable=False)
        soft(aid, "AHU", "DSP-SP", "Duct static pressure set point", "Pa", "setpoint", ["discharge", "air", "pressure", "sp"],
             "Static_Pressure_Setpoint", writable=False)
        soft(aid, "AHU", "MA-T-SP", "Mixed air temperature set point (economizer)", "degC", "setpoint", ["mixed", "air", "temp", "sp"],
             "Mixed_Air_Temperature_Setpoint", writable=False)
        soft(aid, "AHU", "OAD-CMD", "Outdoor air damper command", "%", "command", ["outside", "damper", "cmd"],
             "Damper_Position_Command", writable=False)
        soft(aid, "AHU", "ECON-EN", "Economizer enable", "-", "status", ["economizer", "enable"], "Enable_Status", writable=False)
        soft(aid, "AHU", "SF-CMD", "Supply fan start/stop command", "-", "command", ["discharge", "fan", "cmd"],
             "Start_Stop_Command", writable=False)
        soft(aid, "AHU", "OCC-MODE", "AHU operating mode (2 occupied, 1 night cycle, 0 off)", "-", "status",
             ["occ", "mode"], "Operating_Mode_Status", writable=False)
        for key in ("SAT", "FAN"):
            s = man.commands.get(f"{lname} {key}", {}).get("schedule")
            if s:
                cat.schedule_actuator(s)

    # ---------------------------------------------------------------- plant
    kind_prefix = {"chilled_water": ("CHW", "Chilled water"), "hot_water": ("HW", "Hot water"),
                   "condenser": ("CW", "Condenser water")}
    counters = {"CH": 0, "BLR": 0, "CT": 0}
    for pname, pl in topo.plant_loops.items():
        if pl.kind not in kind_prefix:
            continue
        pre, desc = kind_prefix[pl.kind]
        sid = f"{pre}-SYS"
        pump_design = {p.name: man.design_value(p.type, p.name, "Design Flow Rate [m3/s]", None) for p in pl.pumps}
        loop_flow = sum(v for v in pump_design.values() if v) or 0.1
        cat.add_equip(Equipment(sid, "PlantLoop", pname, f"{desc} system", meta={"kind": pl.kind, "loop": pname,
                                "design_flow_m3s": loop_flow,
                                "swt_schedule": man.commands.get(f"{pname} SWT", {}).get("schedule")}))
        sf = cat.var("System Node Mass Flow Rate", pl.supply_outlet)
        sensor(sid, "PlantLoop", f"{pre}-ST", f"{desc} supply temperature", "degC", "water_temperature",
               raw(cat.var("System Node Temperature", pl.supply_outlet)), ["supply", "water", "temp", "sensor"],
               "Supply_Water_Temperature_Sensor")
        sensor(sid, "PlantLoop", f"{pre}-RT", f"{desc} return temperature", "degC", "water_temperature",
               raw(cat.var("System Node Temperature", pl.supply_inlet)), ["return", "water", "temp", "sensor"],
               "Return_Water_Temperature_Sensor")
        sensor(sid, "PlantLoop", f"{pre}-F", f"{desc} flow", "L/s", "water_flow", raw(sf, 1000.0 / RHO_WATER),
               ["water", "flow", "sensor"], "Water_Flow_Sensor")
        sensor(sid, "PlantLoop", f"{pre}-DP", f"{desc} differential pressure (surrogate model)", "kPa", "pressure", None,
               ["water", "pressure", "sensor"], "Differential_Pressure_Sensor", surrogate=True)
        soft(sid, "PlantLoop", f"{pre}-ST-SP", f"{desc} supply temperature set point", "degC", "setpoint",
             ["supply", "water", "temp", "sp"], "Supply_Water_Temperature_Setpoint", writable=False)
        s = man.commands.get(f"{pname} SWT", {}).get("schedule")
        if s:
            cat.schedule_actuator(s)
        for p in pl.pumps:
            pid = f"{pre}P-{len([e for e in cat.equipment if e.startswith(pre + 'P-')]) + 1}"
            pdes = pump_design.get(p.name) or loop_flow
            cat.add_equip(Equipment(pid, "Pump", p.name, f"{desc} pump ({p.type.split(':')[-1]})", parent=sid,
                                    meta={"design_flow_m3s": pdes, "type": p.type}))
            pm = cat.var("Pump Mass Flow Rate", p.name)
            sensor(pid, "Pump", "KW", "Pump power", "kW", "power", raw(cat.var("Pump Electricity Rate", p.name), 0.001),
                   ["pump", "power", "sensor"], "Electric_Power_Sensor")
            sensor(pid, "Pump", "SPD", "Pump speed (VFD output)", "%", "percent",
                   lambda v, dt, a=pm, d=pdes: 100.0 * min(1.2, v.get(a, 0.0) / RHO_WATER / d), ["pump", "speed", "sensor"],
                   "Frequency_Sensor")
            sensor(pid, "Pump", "STS", "Pump status", "-", "binary", lambda v, dt, a=pm: 1.0 if v.get(a, 0.0) > 1e-3 else 0.0,
                   ["pump", "run", "sensor"], "Pump_Status")
            cat.actuator("Pump", "Pump Mass Flow Rate", p.name)
            cat.actuator("Plant Component " + p.type, "On/Off Supervisory", p.name)
        for ch in pl.chillers:
            counters["CH"] += 1
            cid = f"CH-{counters['CH']}"
            cap = man.design_value(ch.type, ch.name, "Design Size Reference Capacity", None)
            cat.add_equip(Equipment(cid, "Chiller", ch.name, f"Water-cooled chiller ({ch.type.split(':')[-1]})", parent=sid,
                                    meta={"capacity_kw": cap / 1000 if cap else None, "type": ch.type,
                                          "fouling_fault": f"{ch.name} FOULING"}))
            sensor(cid, "Chiller", "KW", "Chiller power", "kW", "power", raw(cat.var("Chiller Electricity Rate", ch.name), 0.001),
                   ["chiller", "power", "sensor"], "Electric_Power_Sensor")
            q = cat.var("Chiller Evaporator Cooling Rate", ch.name)
            sensor(cid, "Chiller", "LOAD", "Chiller cooling load (BTU meter)", "kW", "power", raw(q, 0.001),
                   ["chiller", "cooling", "power", "sensor"], "Thermal_Power_Sensor")
            sensor(cid, "Chiller", "STS", "Chiller run status", "-", "binary", lambda v, dt, a=q: 1.0 if v.get(a, 0.0) > 1.0 else 0.0,
                   ["chiller", "run", "sensor"], "Run_Status")
            sensor(cid, "Chiller", "CHW-LWT", "Evaporator leaving water temperature", "degC", "water_temperature",
                   raw(cat.var("Chiller Evaporator Outlet Temperature", ch.name)), ["chilled", "leaving", "water", "temp", "sensor"],
                   "Chilled_Water_Supply_Temperature_Sensor")
            sensor(cid, "Chiller", "CHW-EWT", "Evaporator entering water temperature", "degC", "water_temperature",
                   raw(cat.var("Chiller Evaporator Inlet Temperature", ch.name)), ["chilled", "entering", "water", "temp", "sensor"],
                   "Chilled_Water_Return_Temperature_Sensor")
            sensor(cid, "Chiller", "CDW-EWT", "Condenser entering water temperature", "degC", "water_temperature",
                   raw(cat.var("Chiller Condenser Inlet Temperature", ch.name)), ["condenser", "entering", "water", "temp", "sensor"],
                   "Condenser_Water_Return_Temperature_Sensor")
            sensor(cid, "Chiller", "CDW-LWT", "Condenser leaving water temperature", "degC", "water_temperature",
                   raw(cat.var("Chiller Condenser Outlet Temperature", ch.name)), ["condenser", "leaving", "water", "temp", "sensor"],
                   "Condenser_Water_Supply_Temperature_Sensor")
            sensor(cid, "Chiller", "PLR", "Chiller part load ratio", "-", "ideal", raw(cat.var("Chiller Part Load Ratio", ch.name)),
                   ["chiller", "plr"], "", kind="truth")
            sensor(cid, "Chiller", "COP", "Chiller COP (ground truth)", "-", "ideal", raw(cat.var("Chiller COP", ch.name)),
                   ["chiller", "cop"], "", kind="truth")
            soft(cid, "Chiller", "EN-CMD", "Chiller enable command", "-", "command", ["chiller", "enable", "cmd"],
                 "Enable_Command", writable=False)
            cat.actuator("Plant Component " + ch.type, "On/Off Supervisory", ch.name)
            f = man.faults.get(f"{ch.name} FOULING")
            if f:
                cat.schedule_actuator(f["active_schedule"])
                cat.schedule_actuator(f["value_schedule"])
        for b in pl.boilers:
            counters["BLR"] += 1
            bid = f"BLR-{counters['BLR']}"
            cap = man.design_value(b.type, b.name, "Design Size Nominal Capacity", None)
            cat.add_equip(Equipment(bid, "Boiler", b.name, "Hot-water boiler (natural gas)", parent=sid,
                                    meta={"capacity_kw": cap / 1000 if cap else None, "fouling_fault": f"{b.name} FOULING"}))
            q = cat.var("Boiler Heating Rate", b.name)
            sensor(bid, "Boiler", "LOAD", "Boiler heating output", "kW", "power", raw(q, 0.001),
                   ["boiler", "heating", "power", "sensor"], "Thermal_Power_Sensor")
            sensor(bid, "Boiler", "GAS-KW", "Boiler gas input", "kW", "power", raw(cat.var("Boiler NaturalGas Rate", b.name), 0.001),
                   ["boiler", "gas", "power", "sensor"], "Natural_Gas_Usage_Sensor")
            sensor(bid, "Boiler", "STS", "Boiler firing status", "-", "binary", lambda v, dt, a=q: 1.0 if v.get(a, 0.0) > 1.0 else 0.0,
                   ["boiler", "run", "sensor"], "Run_Status")
            sensor(bid, "Boiler", "HW-LWT", "Boiler leaving water temperature", "degC", "water_temperature",
                   raw(cat.var("Boiler Outlet Temperature", b.name)), ["hot", "leaving", "water", "temp", "sensor"],
                   "Hot_Water_Supply_Temperature_Sensor")
            sensor(bid, "Boiler", "HW-EWT", "Boiler entering water temperature", "degC", "water_temperature",
                   raw(cat.var("Boiler Inlet Temperature", b.name)), ["hot", "entering", "water", "temp", "sensor"],
                   "Hot_Water_Return_Temperature_Sensor")
            sensor(bid, "Boiler", "PLR", "Boiler part load ratio", "-", "ideal", raw(cat.var("Boiler Part Load Ratio", b.name)),
                   ["boiler", "plr"], "", kind="truth")
            soft(bid, "Boiler", "EN-CMD", "Boiler enable command", "-", "command", ["boiler", "enable", "cmd"], "Enable_Command",
                 writable=False)
            cat.actuator("Plant Component " + b.type, "On/Off Supervisory", b.name)
            f = man.faults.get(f"{b.name} FOULING")
            if f:
                cat.schedule_actuator(f["active_schedule"])
                cat.schedule_actuator(f["value_schedule"])
        for tw in pl.towers:
            counters["CT"] += 1
            tid = f"CT-{counters['CT']}"
            cat.add_equip(Equipment(tid, "CoolingTower", tw.name, f"Cooling tower ({tw.type.split(':')[-1]})", parent=sid,
                                    meta={"fouling_fault": f"{tw.name} FOULING"}))
            fpw = cat.var("Cooling Tower Fan Electricity Rate", tw.name)
            sensor(tid, "CoolingTower", "FAN-KW", "Tower fan power", "kW", "power", raw(fpw, 0.001),
                   ["tower", "fan", "power", "sensor"], "Electric_Power_Sensor")
            sensor(tid, "CoolingTower", "FAN-STS", "Tower fan status", "-", "binary",
                   lambda v, dt, a=fpw: 1.0 if v.get(a, 0.0) > 1.0 else 0.0, ["tower", "fan", "run", "sensor"], "Fan_Status")
            sensor(tid, "CoolingTower", "LWT", "Tower leaving water temperature", "degC", "water_temperature",
                   raw(cat.var("Cooling Tower Outlet Temperature", tw.name)), ["tower", "leaving", "water", "temp", "sensor"],
                   "Water_Temperature_Sensor")
            sensor(tid, "CoolingTower", "EWT", "Tower entering water temperature", "degC", "water_temperature",
                   raw(cat.var("Cooling Tower Inlet Temperature", tw.name)), ["tower", "entering", "water", "temp", "sensor"],
                   "Water_Temperature_Sensor")
            cat.actuator("Plant Component " + tw.type, "On/Off Supervisory", tw.name)
            f = man.faults.get(f"{tw.name} FOULING")
            if f:
                cat.schedule_actuator(f["active_schedule"])
                cat.schedule_actuator(f["value_schedule"])

    # building-level actuators
    s = man.commands.get("OUTDOOR CO2", {}).get("schedule")
    if s:
        cat.schedule_actuator(s)
    for c in ["Outdoor Dry Bulb", "Outdoor Relative Humidity", "Direct Solar", "Diffuse Solar", "Wind Speed", "Outdoor Dew Point"]:
        cat.actuator("Weather Data", c, "Environment")
    return cat
