"""BAS point catalog generated automatically from the discovered HVAC topology.

Each BAS point has:
* a stable identifier ``<EQUIP>/<POINT>`` (e.g. ``AHU-1/SA-T``),
* semantic metadata (Project-Haystack style tags and a Brick class) so that AI agents can
  reason about the point list without building-specific knowledge,
* a binding to the *inner space* (EnergyPlus output variable, meter or derived quantity)
  from which the true physical value is obtained, and
* a sensor class that determines its real-world imperfections.

Equipment covered: zones, VAV terminal units, air handling units (economizer, coils, fan,
filter), chillers, boilers, cooling towers, pumps, plant loops, weather station and meters, and
for small all-electric buildings: zone heat pumps / PTACs, energy-recovery ventilators, electric
baseboards, PV systems (arrays + inverter), electrical storage, grid import/export and water heaters.
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
    # availability tier: "standard" (found in typical commercial BAS today), "advanced" (found in
    # well-instrumented / recently commissioned BAS), "next_gen" (rarely found today but valuable for
    # analytics and AI; see docs/point_taxonomy.md)
    tier: str = "standard"
    # where the true value comes from: "energyplus" (inner-space physics), "model" (outer-space
    # physical model driven by EnergyPlus, see realworld/environment.py), "surrogate" (simplified
    # engineering correlation), "bas" (calculated by the BAS from present values)
    source: str = "energyplus"

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


def dp_from_w(w: float, p: float = 101325.0) -> float:
    """Dew-point temperature [C] from humidity ratio [kg/kg] (inverse Magnus-Tetens)."""
    import math
    if not math.isfinite(w) or w <= 0:
        return float("nan")
    pw = w * p / (0.621945 + w)
    g = math.log(pw / 610.94)
    return 243.04 * g / (17.625 - g)


def _id_safe(name: str) -> str:
    return name.replace(" ", "_")


def build_catalog(man: Manifest) -> Catalog:
    topo = man.topo
    cat = Catalog()
    co2 = man.options.get("enable_co2", True)

    def sensor(equip, etype, name, desc, unit, sclass, truth, tags, brick, kind="sensor", tier="standard",
               source="energyplus", **meta):
        if truth is None and source == "energyplus":
            source = "model"
        return cat.add_point(Point(id=f"{equip}/{name}", equip=equip, equip_type=etype, name=name, description=desc,
                                   unit=unit, kind=kind, sensor_class=sclass, tags=tags, brick=brick, meta=meta,
                                   tier=tier, source=source), truth)

    def soft(equip, etype, name, desc, unit, kind, tags, brick, writable=True, tier="standard", source="bas", **meta):
        return cat.add_point(Point(id=f"{equip}/{name}", equip=equip, equip_type=etype, name=name, description=desc,
                                   unit=unit, kind=kind, sensor_class="ideal", tags=tags, brick=brick,
                                   writable=writable, meta=meta, tier=tier, source=source))

    def calc(equip, etype, name, desc, unit, tags, brick="", tier="standard"):
        """BAS-calculated virtual point (see bas/analytics.py)."""
        return soft(equip, etype, name, desc, unit, "virtual", tags, brick, writable=False, tier=tier, source="bas")

    def raw(alias, scale=1.0, offset=0.0):
        return lambda v, dt, a=alias, s=scale, o=offset: v.get(a, float("nan")) * s + o

    import math as _m

    # ---------------------------------------------------------------- weather
    wx = cat.add_equip(Equipment("WX", "WeatherStation", "Environment", "Rooftop weather station, outdoor air-quality "
                                 "monitor and weather-forecast feed"))
    W = "WeatherStation"
    env = "Environment"
    sensor(wx.id, W, "OA-T", "Outdoor air dry-bulb temperature", "degC", "outdoor_temperature",
           raw(cat.var("Site Outdoor Air Drybulb Temperature", env)), ["outside", "air", "temp", "sensor"],
           "Outside_Air_Temperature_Sensor")
    sensor(wx.id, W, "OA-RH", "Outdoor air relative humidity", "%RH", "humidity",
           raw(cat.var("Site Outdoor Air Relative Humidity", env)), ["outside", "air", "humidity", "sensor"],
           "Outside_Air_Humidity_Sensor")
    sensor(wx.id, W, "OA-WB", "Outdoor air wet-bulb temperature (calculated by station)", "degC",
           "outdoor_temperature", raw(cat.var("Site Outdoor Air Wetbulb Temperature", env)),
           ["outside", "air", "wetBulb", "temp", "sensor"], "Outside_Air_Wet_Bulb_Temperature_Sensor", tier="advanced")
    sensor(wx.id, W, "OA-DP", "Outdoor air dew-point temperature", "degC", "outdoor_temperature",
           raw(cat.var("Site Outdoor Air Dewpoint Temperature", env)), ["outside", "air", "dewPoint", "temp", "sensor"],
           "Outside_Air_Dewpoint_Sensor", tier="advanced")
    sensor(wx.id, W, "OA-H", "Outdoor air specific enthalpy (calculated by station)", "kJ/kg", "enthalpy",
           raw(cat.var("Site Outdoor Air Enthalpy", env), 0.001), ["outside", "air", "enthalpy", "sensor"],
           "Outside_Air_Enthalpy_Sensor", tier="advanced")
    sensor(wx.id, W, "OA-W", "Outdoor air humidity ratio", "g/kg", "humidity_ratio",
           raw(cat.var("Site Outdoor Air Humidity Ratio", env), 1000.0), ["outside", "air", "humidity", "ratio", "sensor"],
           "Humidity_Sensor", tier="advanced")
    sensor(wx.id, W, "BARO", "Barometric pressure", "kPa", "barometric",
           raw(cat.var("Site Outdoor Air Barometric Pressure", env), 0.001), ["outside", "air", "pressure", "sensor"],
           "Air_Pressure_Sensor", tier="advanced")
    sensor(wx.id, W, "WIND", "Wind speed", "m/s", "speed",
           raw(cat.var("Site Wind Speed", env)), ["outside", "wind", "speed", "sensor"], "Wind_Speed_Sensor", tier="advanced")
    sensor(wx.id, W, "WIND-DIR", "Wind direction (0 = north, clockwise)", "deg", "wind_direction",
           raw(cat.var("Site Wind Direction", env)), ["outside", "wind", "direction", "sensor"], "Wind_Direction_Sensor",
           tier="advanced")
    a1 = cat.var("Site Direct Solar Radiation Rate per Area", env)
    a2 = cat.var("Site Diffuse Solar Radiation Rate per Area", env)
    alt = cat.var("Site Solar Altitude Angle", env)
    # EnergyPlus reports beam *normal* irradiance; the horizontal pyranometer sees DNI sin(altitude) + DHI
    sensor(wx.id, W, "SOLAR", "Global horizontal irradiance (pyranometer)", "W/m2", "solar",
           lambda v, dt: max(0.0, v.get(a1, 0.0) * _m.sin(_m.radians(max(0.0, v.get(alt, 0.0))))) + v.get(a2, 0.0),
           ["outside", "solar", "irradiance", "sensor"], "Solar_Radiance_Sensor", tier="advanced")
    sensor(wx.id, W, "DNI", "Direct normal irradiance (pyrheliometer)", "W/m2", "solar", raw(a1),
           ["outside", "solar", "direct", "irradiance", "sensor"], "Solar_Radiance_Sensor", tier="next_gen")
    sensor(wx.id, W, "DHI", "Diffuse horizontal irradiance (shaded pyranometer)", "W/m2", "solar", raw(a2),
           ["outside", "solar", "diffuse", "irradiance", "sensor"], "Solar_Radiance_Sensor", tier="next_gen")
    b1 = cat.var("Site Exterior Horizontal Beam Illuminance", env)
    b2 = cat.var("Site Exterior Horizontal Sky Illuminance", env)
    sensor(wx.id, W, "OA-LUX", "Exterior horizontal illuminance (roof photocell)", "lux", "illuminance",
           lambda v, dt: v.get(b1, 0.0) + v.get(b2, 0.0), ["outside", "illuminance", "sensor"], "Outside_Illuminance_Sensor",
           tier="advanced")
    sensor(wx.id, W, "SKY-COVER", "Total sky cover (sky imager)", "tenths", "ideal",
           raw(cat.var("Site Total Sky Cover", env)), ["outside", "sky", "cover", "sensor"], "", tier="next_gen")
    sensor(wx.id, W, "SKY-T", "Sky temperature (pyrgeometer)", "degC", "outdoor_temperature",
           raw(cat.var("Site Sky Temperature", env)), ["outside", "sky", "temp", "sensor"], "Temperature_Sensor",
           tier="next_gen")
    sensor(wx.id, W, "RAIN", "Rain sensor", "-", "binary", raw(cat.var("Site Rain Status", env)),
           ["outside", "rain", "sensor"], "Rain_Sensor", tier="advanced")
    sensor(wx.id, W, "PRECIP", "Precipitation rate (tipping bucket)", "mm/h", "ideal",
           raw(cat.var("Site Precipitation Rate", env), 3.6e6), ["outside", "rain", "rate", "sensor"],
           "Precipitation_Sensor", tier="next_gen")
    sensor(wx.id, W, "OA-PM25", "Outdoor PM2.5 (air-quality monitor / public AQ feed)", "ug/m3", "pm_sensor", None,
           ["outside", "air", "pm25", "sensor"], "PM2.5_Sensor", tier="next_gen")
    sensor(wx.id, W, "OA-PM10", "Outdoor PM10 (air-quality monitor / public AQ feed)", "ug/m3", "pm_sensor", None,
           ["outside", "air", "pm10", "sensor"], "PM10_Sensor", tier="next_gen")
    for h in (1, 6, 24):
        sensor(wx.id, W, f"OA-T-FC{h}H", f"Forecast outdoor dry-bulb temperature, {h} h ahead (weather service)", "degC",
               "ideal", None, ["outside", "air", "temp", "forecast"], "", tier="next_gen", lead_h=h)
        sensor(wx.id, W, f"GHI-FC{h}H", f"Forecast global horizontal irradiance, {h} h ahead (weather service)", "W/m2",
               "ideal", None, ["outside", "solar", "forecast"], "", tier="next_gen", lead_h=h)
    calc(wx.id, W, "HDD-TODAY", "Heating degree-days today (base 18 C)", "K.d", ["hdd", "weather"], tier="standard")
    calc(wx.id, W, "CDD-TODAY", "Cooling degree-days today (base 18 C)", "K.d", ["cdd", "weather"], tier="standard")

    # ---------------------------------------------------------------- meters
    mtr = cat.add_equip(Equipment("MTR", "Meter", "Facility", "Utility meters and end-use sub-meters"))
    for name, mname, desc, tier in [("BLDG-ELEC-KW", "Electricity:Facility", "Whole-building electric demand", "standard"),
                                    ("BLDG-GAS-KW", "NaturalGas:Facility", "Whole-building natural gas rate", "standard"),
                                    ("HVAC-ELEC-KW", "Electricity:HVAC", "HVAC electric demand", "advanced"),
                                    ("LIGHT-KW", "InteriorLights:Electricity", "Interior lighting demand", "advanced"),
                                    ("PLUG-KW", "InteriorEquipment:Electricity", "Plug and process load demand", "next_gen"),
                                    ("CLG-ELEC-KW", "Cooling:Electricity", "Cooling (chiller) electric demand", "advanced"),
                                    ("FAN-ELEC-KW", "Fans:Electricity", "Fan electric demand", "advanced"),
                                    ("PUMP-ELEC-KW", "Pumps:Electricity", "Pump electric demand", "advanced"),
                                    ("HREJ-ELEC-KW", "HeatRejection:Electricity", "Heat rejection electric demand", "advanced"),
                                    ("HTG-GAS-KW", "Heating:NaturalGas", "Heating natural gas rate", "advanced"),
                                    ("EXT-LIGHT-KW", "ExteriorLights:Electricity", "Exterior (facade) lighting demand", "advanced"),
                                    ("ELEV-KW", "ExteriorEquipment:Electricity", "Elevators electric demand", "next_gen"),
                                    ("DHW-GAS-KW", "WaterSystems:NaturalGas", "Domestic hot water heater gas rate", "advanced")]:
        al = cat.meter(mname)
        sensor(mtr.id, "Meter", name, desc, "kW", "energy", lambda v, dt, a=al: v.get(a, 0.0) / dt / 1000.0,
               ["power", "sensor", "meter"], "Electric_Power_Sensor" if "ELEC" in mname.upper() or "Electricity" in mname
               else "Natural_Gas_Usage_Sensor", kind="meter", meter=mname, tier=tier)
    # EnergyPlus' Electricity:HVAC covers air-side components only; plant equipment is metered on Electricity:Plant
    a_h, a_p = cat.meter("Electricity:HVAC"), cat.meter("Electricity:Plant")
    cat.truth["MTR/HVAC-ELEC-KW"] = lambda v, dt, a=a_h, b=a_p: (v.get(a, 0.0) + v.get(b, 0.0)) / dt / 1000.0
    cat.points["MTR/HVAC-ELEC-KW"].description = "HVAC electric demand (air-side + plant)"
    cat.points["MTR/HVAC-ELEC-KW"].meta["meter"] = "Electricity:HVAC + Electricity:Plant"
    al = cat.meter("Water:Facility")
    sensor(mtr.id, "Meter", "WATER-F", "Building water flow (domestic + cooling-tower make-up)", "L/s", "energy",
           lambda v, dt, a=al: v.get(a, 0.0) / dt * 1000.0, ["water", "flow", "sensor", "meter"], "Water_Usage_Sensor",
           kind="meter", meter="Water:Facility", tier="standard")
    al = cat.meter("HeatRejection:Water")
    sensor(mtr.id, "Meter", "TOWER-WATER-F", "Cooling-tower make-up water sub-meter", "L/s", "energy",
           lambda v, dt, a=al: v.get(a, 0.0) / dt * 1000.0, ["water", "flow", "sensor", "meter"], "Water_Usage_Sensor",
           kind="meter", meter="HeatRejection:Water", tier="advanced")
    sensor(mtr.id, "Meter", "BLDG-ELEC-KWH", "Electricity totaliser (since start of run)", "kWh", "energy", None,
           ["elec", "energy", "sensor", "meter"], "Electric_Energy_Sensor", kind="meter", tier="standard")
    sensor(mtr.id, "Meter", "BLDG-GAS-KWH", "Natural-gas totaliser (since start of run)", "kWh", "energy", None,
           ["gas", "energy", "sensor", "meter"], "Natural_Gas_Usage_Sensor", kind="meter", tier="standard")
    sensor(mtr.id, "Meter", "WATER-M3", "Water totaliser (since start of run)", "m3", "energy", None,
           ["water", "volume", "sensor", "meter"], "Water_Usage_Sensor", kind="meter", tier="standard")
    calc(mtr.id, "Meter", "BLDG-DMD-15", "Electric demand, 15-minute rolling average", "kW", ["elec", "demand"])
    calc(mtr.id, "Meter", "PEAK-DMD-DAY", "Peak 15-minute demand today", "kW", ["elec", "demand", "peak"])
    calc(mtr.id, "Meter", "PEAK-DMD-MONTH", "Peak 15-minute demand this month (billing demand)", "kW", ["elec", "demand", "peak"])

    # ---------------------------------------------------------------- grid interaction
    grid = cat.add_equip(Equipment("GRID", "Grid", "Utility", "Utility tariff, grid carbon intensity and demand-response "
                                   "signals (OpenADR-style feed)"))
    G = "Grid"
    sensor(grid.id, G, "PRICE", "Electricity price (time-of-use tariff)", "$/kWh", "ideal", None,
           ["elec", "price"], "", tier="next_gen")
    sensor(grid.id, G, "TOU-PERIOD", "Tariff period (0 off-peak, 1 mid-peak, 2 on-peak)", "-", "ideal", None,
           ["elec", "tariff"], "", tier="next_gen")
    sensor(grid.id, G, "CO2-INT", "Marginal grid carbon intensity", "kgCO2/kWh", "ideal", None,
           ["elec", "co2", "emission"], "", tier="next_gen")
    sensor(grid.id, G, "DR-EVENT", "Demand-response event active", "-", "ideal", None, ["dr", "event"], "", tier="next_gen")
    sensor(grid.id, G, "DR-SHED-KW", "Requested demand-response load shed", "kW", "ideal", None, ["dr", "shed"], "",
           tier="next_gen")
    sensor(grid.id, G, "COST-TODAY", "Energy cost today (electricity + gas)", "$", "ideal", None, ["cost"], "",
           tier="next_gen")
    sensor(grid.id, G, "CO2-TODAY", "Operational carbon emissions today", "kgCO2", "ideal", None, ["co2", "emission"], "",
           tier="next_gen")

    # ---------------------------------------------------------------- building level
    bldg = cat.add_equip(Equipment("BLDG", "Building", "Building", "Building-level calculated values"))
    calc(bldg.id, "Building", "OCC-COUNT", "Building occupancy (sum of zone people counters)", "people",
         ["occupants", "count"], "Occupancy_Count_Sensor", tier="next_gen")

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
        Z = "Zone"
        zn = z.name
        sensor(zid, Z, "ZN-RH", "Zone air relative humidity", "%RH", "humidity",
               raw(cat.var("Zone Air Relative Humidity", zn)), ["zone", "air", "humidity", "sensor"], "Zone_Air_Humidity_Sensor",
               tier="advanced")
        sensor(zid, Z, "ZN-DP", "Zone air dew-point temperature (calculated by T/RH transmitter)", "degC", "air_temperature",
               raw(cat.var("Zone Mean Air Dewpoint Temperature", zn)), ["zone", "air", "dewPoint", "sensor"],
               "Dewpoint_Sensor", tier="advanced")
        if co2:
            sensor(zid, Z, "ZN-CO2", "Zone CO2 concentration (NDIR)", "ppm", "co2",
                   raw(cat.var("Zone Air CO2 Concentration", zn)), ["zone", "air", "co2", "sensor"], "CO2_Sensor")
        occ = cat.var("Zone People Occupant Count", zn)
        sensor(zid, Z, "ZN-OCC", "Zone occupancy sensor (PIR)", "-", "occupancy",
               lambda v, dt, a=occ: 1.0 if v.get(a, 0.0) > 0.01 else 0.0, ["zone", "occupied", "sensor"], "Occupancy_Sensor")
        sensor(zid, Z, "OCCUPANTS", "True number of occupants (ground truth only)", "people", "ideal",
               raw(occ), ["zone", "occupants"], "Occupancy_Count_Sensor", kind="truth")
        sensor(zid, Z, "OCC-COUNT", "People counter (camera / thermopile)", "people", "people_count", None,
               ["zone", "occupants", "count", "sensor"], "Occupancy_Count_Sensor", tier="next_gen")
        sensor(zid, Z, "WIN-STS", "Window / door contact (1 = open)", "-", "binary", None, ["zone", "window", "sensor"],
               "Open_Close_Status", tier="advanced")
        # thermal comfort station (globe thermometer + T/RH/air speed -> ISO 7730 indices)
        sensor(zid, Z, "ZN-MRT", "Mean radiant temperature (globe thermometer)", "degC", "radiant_temperature",
               raw(cat.var("Zone Mean Radiant Temperature", zn)), ["zone", "radiant", "temp", "sensor"], "Radiant_Temperature_Sensor",
               tier="next_gen")
        sensor(zid, Z, "ZN-OPT", "Operative temperature (comfort station)", "degC", "zone_temperature",
               raw(cat.var("Zone Operative Temperature", zn)), ["zone", "operative", "temp", "sensor"], "Operative_Temperature",
               tier="next_gen")
        if z.people:
            sensor(zid, Z, "PMV", "Predicted mean vote, ISO 7730 (comfort station)", "-", "comfort_index",
                   raw(cat.var("Zone Thermal Comfort Fanger Model PMV", z.people[0])), ["zone", "comfort", "pmv", "sensor"], "",
                   tier="next_gen")
            sensor(zid, Z, "PPD", "Predicted percentage dissatisfied, ISO 7730 (comfort station)", "%", "comfort_ppd",
                   raw(cat.var("Zone Thermal Comfort Fanger Model PPD", z.people[0])), ["zone", "comfort", "ppd", "sensor"], "",
                   tier="next_gen")
            sensor(zid, Z, "TS-VOTE", "Mean thermal-sensation vote of occupants, last hour (feedback app, -3..+3)", "-",
                   "ideal", None, ["zone", "comfort", "vote"], "", tier="next_gen")
            sensor(zid, Z, "HOT-CALLS", "Too-hot complaints today (work orders / app)", "count", "ideal", None,
                   ["zone", "complaint", "hot"], "", tier="next_gen")
            sensor(zid, Z, "COLD-CALLS", "Too-cold complaints today (work orders / app)", "count", "ideal", None,
                   ["zone", "complaint", "cold"], "", tier="next_gen")
        # indoor air quality monitor (RESET / WELL style)
        sensor(zid, Z, "ZN-PM25", "Zone PM2.5 (optical particle sensor)", "ug/m3", "pm_sensor", None,
               ["zone", "air", "pm25", "sensor"], "PM2.5_Sensor", tier="next_gen")
        sensor(zid, Z, "ZN-PM10", "Zone PM10 (optical particle sensor)", "ug/m3", "pm_sensor", None,
               ["zone", "air", "pm10", "sensor"], "PM10_Sensor", tier="next_gen")
        sensor(zid, Z, "ZN-TVOC", "Zone total VOC (metal-oxide sensor)", "ug/m3", "tvoc_sensor", None,
               ["zone", "air", "tvoc", "sensor"], "TVOC_Sensor", tier="next_gen")
        # light and sound
        sensor(zid, Z, "ZN-LUX", "Work-plane illuminance (daylight-harvesting photosensor)", "lux", "illuminance", None,
               ["zone", "illuminance", "sensor"], "Illuminance_Sensor", tier="advanced")
        sensor(zid, Z, "DAYLIGHT-LUX", "Daylight share of the work-plane illuminance (ground truth only)", "lux", "ideal",
               None, ["zone", "daylight", "illuminance"], "", kind="truth")
        sensor(zid, Z, "LIGHT-LVL", "Lighting level (networked lighting controls)", "%", "percent", None,
               ["zone", "lights", "level", "sensor"], "", tier="advanced")
        sensor(zid, Z, "ZN-DBA", "Background sound level (class-2 sound level meter)", "dBA", "sound", None,
               ["zone", "sound", "sensor"], "", tier="next_gen")
        sensor(zid, Z, "LIGHT-KW", "Zone lighting power (lighting panel sub-meter)", "kW", "power",
               raw(cat.var("Zone Lights Electricity Rate", zn), 0.001), ["zone", "lights", "power", "sensor"],
               "Electric_Power_Sensor", kind="meter", tier="advanced")
        sensor(zid, Z, "PLUG-KW", "Zone plug load power (circuit-level sub-meter)", "kW", "power",
               raw(cat.var("Zone Electric Equipment Electricity Rate", zn), 0.001), ["zone", "plug", "power", "sensor"],
               "Electric_Power_Sensor", kind="meter", tier="next_gen")
        # physics ground truth useful for research (not measurable by a BAS)
        for nm, var, sc, unit, desc in ([
                ("INFIL-ACH", "Zone Infiltration Air Change Rate", 1.0, "1/h", "Infiltration air-change rate")]
                if (z.infiltration or z.infiltration_other) else []) + [
                ("WIN-SOL-KW", "Zone Windows Total Transmitted Solar Radiation Rate", 0.001, "kW", "Transmitted solar gain"),
                ("WIN-Q-KW", "Zone Windows Total Heat Gain Rate", 0.001, "kW", "Window heat gain"),
                ("INT-GAIN-KW", "Zone Total Internal Total Heating Rate", 0.001, "kW", "Total internal heat gain"),
                ("SYS-CLG-KW", "Zone Air System Sensible Cooling Rate", 0.001, "kW", "Sensible cooling delivered to the zone"),
                ("SYS-HTG-KW", "Zone Air System Sensible Heating Rate", 0.001, "kW", "Sensible heating delivered to the zone")]:
            al = cat.var(var, zn)
            if nm == "WIN-SOL-KW":
                cat.variables[f"ZWINSOL|{zn}".upper()] = (var, zn)
            sensor(zid, Z, nm, f"{desc} (ground truth only)", unit, "ideal", raw(al, sc), ["zone", "truth"], "", kind="truth")
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
        soft(zid, "Zone", "ZN-T-ADJ", "Occupant set-point adjustment (wall sensor slider, +/-)", "K", "setpoint",
             ["zone", "temp", "sp", "adjust"], "Temperature_Adjust_Sensor")
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
        if z.infiltration_window:
            cat.actuator("Zone Infiltration", "Air Exchange Flow Rate", z.infiltration_window)
        if z.zone_equipment and not z.terminal:
            # outdoor air delivered by zone equipment (ERV, PTAC/PTHP outdoor-air mixer) for the IAQ model
            cat.variables[f"ZMECHVENT|{zn}".upper()] = ("Zone Mechanical Ventilation Current Density Volume Flow Rate", zn)

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
               "Damper_Position_Sensor", tier="advanced")
        # flow cross: velocity pressure ~ (V / Vmax)^2, ~250 Pa (1 in. w.c.) at maximum flow
        sensor(vid, "VAV", "DA-VP", "Flow-cross velocity pressure (airflow transducer)", "Pa", "pressure",
               lambda v, dt, a=fl, vm=vmax: 250.0 * (v.get(a, 0.0) / RHO_AIR / vm) ** 2, ["discharge", "air", "velocityPressure",
                                                                                        "sensor"], "Velocity_Pressure_Sensor",
               tier="advanced", source="surrogate")
        if t.reheat and t.reheat.water_inlet:
            wf = cat.var("System Node Mass Flow Rate", t.reheat.water_inlet)
            wmax = (rh_w or 1e-3) * RHO_WATER
            sensor(vid, "VAV", "RHV-POS", "Reheat valve position (feedback)", "%", "position",
                   lambda v, dt, a=wf, m=wmax: 100.0 * min(1.0, v.get(a, 0.0) / m), ["reheat", "valve", "position", "sensor"],
                   "Valve_Position_Sensor", tier="advanced")
            rq = cat.var("Heating Coil Heating Rate", t.reheat.name)
            sensor(vid, "VAV", "RH-Q", "Reheat coil heat rate (ground truth)", "kW", "ideal",
                   raw(rq, 0.001), ["reheat", "heat", "power"], "", kind="truth")
            sensor(vid, "VAV", "RH-BTU", "Reheat coil BTU meter (water-side heat rate)", "kW", "thermal_power",
                   raw(rq, 0.001), ["reheat", "heat", "power", "sensor"], "Thermal_Power_Sensor", tier="next_gen")
            sensor(vid, "VAV", "RH-WF", "Reheat coil water flow", "L/s", "water_flow", raw(wf, 1000.0 / RHO_WATER),
                   ["reheat", "water", "flow", "sensor"], "Water_Flow_Sensor", tier="next_gen")
            cat.actuator("Plant Component Coil:Heating:Water", "On/Off Supervisory", t.reheat.name)
        soft(vid, "VAV", "ZN-MODE", "Terminal control state (0 deadband, 1 cooling, 2 heating)", "-", "status",
             ["zone", "mode"], "Mode_Status", writable=False)
        for rq_name, rq_desc in [("CLG-REQ", "Cooling SAT-reset requests (G36)"), ("PRS-REQ", "Static-pressure reset requests (G36)"),
                                 ("HW-REQ", "Hot-water reset requests (G36)")]:
            soft(vid, "VAV", rq_name, rq_desc, "count", "virtual", ["request"], "", writable=False)
        soft(vid, "VAV", "LOW-FLOW-ALM", "Low airflow alarm (G36: flow < 70 % of set point for 5 min)", "-", "status",
             ["alarm", "flow"], "Low_Air_Flow_Alarm", writable=False)
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
        # ---- additional AHU instrumentation
        oat_al = cat.var("Site Outdoor Air Drybulb Temperature", "Environment")
        sensor(aid, "AHU", "OA-T", "Outdoor air temperature at the AHU intake (local sensor)", "degC", "outdoor_temperature",
               raw(oat_al), ["outside", "air", "temp", "sensor"], "Outside_Air_Temperature_Sensor")
        sensor(aid, "AHU", "OA-RH", "Outdoor air humidity at the AHU intake (enthalpy economizer)", "%RH", "outdoor_humidity",
               raw(cat.var("Site Outdoor Air Relative Humidity", "Environment")), ["outside", "air", "humidity", "sensor"],
               "Outside_Air_Humidity_Sensor", tier="advanced")
        _t2, _w2 = cat.var("System Node Temperature", loop.supply_outlet), cat.var("System Node Humidity Ratio", loop.supply_outlet)
        sensor(aid, "AHU", "SA-DP", "Supply air dew point (calculated by T/RH transmitter)", "degC", "air_temperature",
               lambda v, dt, b=_w2: dp_from_w(v.get(b, float("nan"))), ["discharge", "air", "dewPoint", "sensor"],
               "Dewpoint_Sensor", tier="advanced")
        if loop.return_node:
            sensor(aid, "AHU", "RA-CO2", "Return air CO2", "ppm", "co2",
                   raw(cat.var("System Node CO2 Concentration", loop.return_node)), ["return", "air", "co2", "sensor"],
                   "Return_Air_CO2_Sensor", tier="advanced")
            calc(aid, "AHU", "OA-FRAC-CALC", "Outdoor-air fraction from OA/RA/MA temperatures", "%", ["outside", "air", "fraction"],
                 tier="standard")
        calc(aid, "AHU", "OA-FRAC-AFMS", "Outdoor-air fraction from airflow stations (OA-F / SA-F)", "%",
             ["outside", "air", "fraction"], tier="advanced")
        sensor(aid, "AHU", "OA-FRAC", "True outdoor-air fraction (ground truth only)", "%", "ideal", None,
               ["outside", "air", "fraction"], "", kind="truth")
        sensor(aid, "AHU", "SA-PM25", "Supply air PM2.5 after filter (ground truth only)", "ug/m3", "ideal", None,
               ["discharge", "air", "pm25"], "", kind="truth")
        mfrz = loop.mixed_air_node
        hc_out = hc.outlet if hc and hc.outlet else None
        if hc_out:
            sensor(aid, "AHU", "HC-LAT", "Preheat coil leaving air temperature", "degC", "air_temperature",
                   raw(cat.var("System Node Temperature", hc_out)), ["heating", "coil", "leaving", "air", "temp", "sensor"],
                   "Air_Temperature_Sensor", tier="advanced")
        frz_node = hc_out or mfrz
        if frz_node:
            fa = cat.var("System Node Temperature", frz_node)
            sensor(aid, "AHU", "FRZ-STAT", "Freeze-stat low-limit (hard-wired, trips < 3.3 C)", "-", "binary",
                   lambda v, dt, a=fa, b=sa_m: 1.0 if v.get(b, 0.0) > 1e-3 and v.get(a, 20.0) < 3.3 else 0.0,
                   ["freezeStat", "alarm", "sensor"], "Low_Freeze_Protect_Temperature_Sensor")
        sensor(aid, "AHU", "SMK-DET", "Duct smoke detector (hard-wired fan shutdown)", "-", "binary", lambda v, dt: 0.0,
               ["smoke", "detector", "sensor"], "Smoke_Detection_Alarm")
        if cc and cc.water_inlet:
            cwf = cat.var("System Node Mass Flow Rate", cc.water_inlet)
            sensor(aid, "AHU", "CC-EWT", "Cooling coil entering water temperature", "degC", "water_temperature",
                   raw(cat.var("System Node Temperature", cc.water_inlet)), ["cooling", "coil", "entering", "water", "temp", "sensor"],
                   "Chilled_Water_Supply_Temperature_Sensor", tier="next_gen")
            if cc.water_outlet:
                sensor(aid, "AHU", "CC-LWT", "Cooling coil leaving water temperature", "degC", "water_temperature",
                       raw(cat.var("System Node Temperature", cc.water_outlet)),
                       ["cooling", "coil", "leaving", "water", "temp", "sensor"], "Chilled_Water_Return_Temperature_Sensor",
                       tier="next_gen")
            sensor(aid, "AHU", "CC-WF", "Cooling coil water flow", "L/s", "water_flow", raw(cwf, 1000.0 / RHO_WATER),
                   ["cooling", "coil", "water", "flow", "sensor"], "Water_Flow_Sensor", tier="next_gen")
            sensor(aid, "AHU", "CC-BTU", "Cooling coil BTU meter", "kW", "thermal_power",
                   raw(cat.var("Cooling Coil Total Cooling Rate", cc.name), 0.001), ["cooling", "coil", "power", "sensor"],
                   "Thermal_Power_Sensor", tier="next_gen")
            sensor(aid, "AHU", "CC-DP", "Cooling coil air-side pressure drop (surrogate)", "Pa", "pressure",
                   lambda v, dt, a=sa_m, d=vd: 125.0 * (v.get(a, 0.0) / RHO_AIR / d) ** 1.8, ["cooling", "coil", "pressure",
                                                                                          "sensor"],
                   "Differential_Pressure_Sensor", tier="next_gen", source="surrogate")
        if hc and hc.water_inlet:
            sensor(aid, "AHU", "HC-BTU", "Preheat coil BTU meter", "kW", "thermal_power",
                   raw(cat.var("Heating Coil Heating Rate", hc.name), 0.001), ["heating", "coil", "power", "sensor"],
                   "Thermal_Power_Sensor", tier="next_gen")
        if loop.fan:
            sensor(aid, "AHU", "SF-HZ", "Supply fan VFD output frequency", "Hz", "frequency",
                   lambda v, dt, a=sa_m, d=vd: 60.0 * min(1.0, v.get(a, 0.0) / RHO_AIR / d), ["discharge", "fan", "freq",
                                                                                         "sensor"],
                   "Frequency_Sensor")
            # motor current at 460 V, PF 0.88: I = P / (sqrt(3) V PF)
            sensor(aid, "AHU", "SF-AMPS", "Supply fan motor current (VFD)", "A", "current",
                   lambda v, dt, a=fp: v.get(a, 0.0) / (1.732 * 460.0 * 0.88), ["discharge", "fan", "current", "sensor"],
                   "Current_Sensor", tier="advanced")
            sensor(aid, "AHU", "SF-VIB", "Supply fan vibration velocity, ISO 10816 (surrogate)", "mm/s", "vibration", None,
                   ["discharge", "fan", "vibration", "sensor"], "Vibration_Sensor", tier="next_gen", source="surrogate")
            calc(aid, "AHU", "SF-W-PER-CMS", "Specific fan power (fan W per m3/s supply)", "W/(m3/s)", ["fan", "efficiency"],
                 tier="advanced")
        sensor(aid, "AHU", "DSP", "Duct static pressure (surrogate model)", "Pa", "pressure", None,
               ["discharge", "air", "pressure", "sensor"], "Static_Pressure_Sensor", surrogate=True, source="surrogate")
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
        sensor(sid, "PlantLoop", f"{pre}-DP", f"{desc} differential pressure (surrogate model)", "kPa", "water_dp", None,
               ["water", "pressure", "sensor"], "Differential_Pressure_Sensor", surrogate=True)
        soft(sid, "PlantLoop", f"{pre}-ST-SP", f"{desc} supply temperature set point", "degC", "setpoint",
             ["supply", "water", "temp", "sp"], "Supply_Water_Temperature_Setpoint", writable=False)
        calc(sid, "PlantLoop", f"{pre}-DT", f"{desc} delta-T (return - supply)", "K", ["water", "deltaT"])
        if pre == "CHW":
            calc(sid, "PlantLoop", "CHW-TONS", "Chilled-water load from loop flow and delta-T", "ton", ["chilled", "load"])
            calc(sid, "PlantLoop", "PLANT-KW-TON", "Chiller-plant efficiency (chillers + tower + CHW/CW pumps)", "kW/ton",
                 ["plant", "efficiency"], tier="advanced")
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
            sensor(pid, "Pump", "HZ", "Pump VFD output frequency", "Hz", "frequency",
                   lambda v, dt, a=pm, d=pdes: 60.0 * min(1.0, v.get(a, 0.0) / RHO_WATER / d), ["pump", "freq", "sensor"],
                   "Frequency_Sensor")
            sensor(pid, "Pump", "VIB", "Pump vibration velocity, ISO 10816 (surrogate)", "mm/s", "vibration", None,
                   ["pump", "vibration", "sensor"], "Vibration_Sensor", tier="next_gen", source="surrogate")
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
            # ---- chiller panel (vendor BACnet integration)
            cop_ref = float(man.options.get("chiller_reference_cop", 6.1))
            p_ref = (cap / cop_ref) if cap else 350e3
            kwa = cat.var("Chiller Electricity Rate", ch.name)
            lwt_a = cat.var("Chiller Evaporator Outlet Temperature", ch.name)
            cdl_a = cat.var("Chiller Condenser Outlet Temperature", ch.name)
            plr_a = cat.var("Chiller Part Load Ratio", ch.name)
            sensor(cid, "Chiller", "PCT-RLA", "Compressor current, percent of rated load amps", "%", "percent",
                   lambda v, dt, a=kwa, p=p_ref: 100.0 * v.get(a, 0.0) / p, ["chiller", "current", "sensor"], "Current_Sensor")
            sensor(cid, "Chiller", "CHW-F", "Evaporator water flow", "L/s", "water_flow",
                   raw(cat.var("Chiller Evaporator Mass Flow Rate", ch.name), 1000.0 / RHO_WATER),
                   ["chilled", "water", "flow", "sensor"], "Chilled_Water_Flow_Sensor", tier="advanced")
            sensor(cid, "Chiller", "CDW-F", "Condenser water flow", "L/s", "water_flow",
                   raw(cat.var("Chiller Condenser Mass Flow Rate", ch.name), 1000.0 / RHO_WATER),
                   ["condenser", "water", "flow", "sensor"], "Condenser_Water_Flow_Sensor", tier="advanced")
            # refrigerant side (R-134a): saturation temperatures from approach temperatures that grow with load and
            # fouling; pressures from a Clausius-Clapeyron fit of R-134a, ln p[kPa] = 15.422 - 2661 / T[K]
            for nm, desc_r, unit in [("EVAP-SAT-T", "Evaporator saturated refrigerant temperature", "degC"),
                                     ("COND-SAT-T", "Condenser saturated refrigerant temperature", "degC"),
                                     ("EVAP-P", "Evaporator refrigerant pressure (abs.)", "kPa"),
                                     ("COND-P", "Condenser refrigerant pressure (abs.)", "kPa")]:
                sensor(cid, "Chiller", nm, f"{desc_r} (surrogate)", unit,
                       "water_temperature" if unit == "degC" else "refrigerant_pressure", None,
                       ["chiller", "refrigerant", "sensor"], "Refrigerant_Pressure_Sensor" if unit == "kPa" else "Temperature_Sensor",
                       tier="advanced", source="surrogate", lwt=lwt_a, cdl=cdl_a, plr=plr_a)
            sensor(cid, "Chiller", "ALM", "Chiller common alarm / lock-out", "-", "binary", None, ["chiller", "alarm", "sensor"],
                   "Alarm")
            calc(cid, "Chiller", "KW-TON", "Chiller efficiency", "kW/ton", ["chiller", "efficiency"])
            calc(cid, "Chiller", "LOAD-TONS", "Chiller cooling load", "ton", ["chiller", "load"], tier="advanced")
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
            plr_b = cat.var("Boiler Part Load Ratio", b.name)
            sensor(bid, "Boiler", "FIRE-RATE", "Burner firing rate (modulation)", "%", "percent", raw(plr_b, 100.0),
                   ["boiler", "firing", "sensor"], "")
            sensor(bid, "Boiler", "HW-F", "Boiler water flow", "L/s", "water_flow",
                   raw(cat.var("Boiler Mass Flow Rate", b.name), 1000.0 / RHO_WATER), ["hot", "water", "flow", "sensor"],
                   "Hot_Water_Flow_Sensor", tier="advanced")
            sensor(bid, "Boiler", "FLUE-T", "Flue (stack) gas temperature (surrogate)", "degC", "air_temperature", None,
                   ["boiler", "flue", "temp", "sensor"], "Exhaust_Air_Temperature_Sensor", tier="advanced", source="surrogate",
                   lwt=cat.var("Boiler Outlet Temperature", b.name), plr=plr_b)
            sensor(bid, "Boiler", "EFF", "Boiler combustion efficiency (ground truth)", "-", "ideal",
                   raw(cat.var("Boiler Efficiency", b.name)), ["boiler", "efficiency"], "", kind="truth")
            sensor(bid, "Boiler", "ALM", "Boiler flame-failure / lock-out alarm", "-", "binary", None, ["boiler", "alarm", "sensor"],
                   "Alarm")
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
            sensor(tid, "CoolingTower", "FAN-SPD", "Tower fan speed / duty (fan cycling ratio)", "%", "percent",
                   raw(cat.var("Cooling Tower Fan Cycling Ratio", tw.name), 100.0), ["tower", "fan", "speed", "sensor"],
                   "Frequency_Sensor")
            sensor(tid, "CoolingTower", "MAKEUP-F", "Make-up water flow (water meter)", "L/s", "water_flow",
                   raw(cat.var("Cooling Tower Make Up Water Volume Flow Rate", tw.name), 1000.0), ["tower", "makeup", "water",
                                                                                                   "flow", "sensor"],
                   "Water_Flow_Sensor", tier="advanced")
            sensor(tid, "CoolingTower", "EVAP-F", "Evaporation loss (ground truth)", "L/s", "ideal",
                   raw(cat.var("Cooling Tower Water Evaporation Volume Flow Rate", tw.name), 1000.0), ["tower", "evaporation"],
                   "", kind="truth")
            sensor(tid, "CoolingTower", "Q-REJ", "Heat rejection rate (ground truth)", "kW", "ideal",
                   raw(cat.var("Cooling Tower Heat Transfer Rate", tw.name), 0.001), ["tower", "heat"], "", kind="truth")
            sensor(tid, "CoolingTower", "ALM", "Tower vibration cut-out / VFD fault", "-", "binary", None, ["tower", "alarm", "sensor"],
                   "Alarm")
            calc(tid, "CoolingTower", "APPROACH", "Tower approach (leaving water - outdoor wet bulb)", "K", ["tower", "approach"])
            calc(tid, "CoolingTower", "RANGE", "Tower range (entering - leaving water)", "K", ["tower", "range"])
            cat.actuator("Plant Component " + tw.type, "On/Off Supervisory", tw.name)
            f = man.faults.get(f"{tw.name} FOULING")
            if f:
                cat.schedule_actuator(f["active_schedule"])
                cat.schedule_actuator(f["value_schedule"])

    # ---------------------------------------------------------------- domestic hot water heaters
    whs = sorted({n for t_, objs in (man.design or {}).items() if t_.upper() == "WATERHEATER:MIXED" for n in objs})
    wh_topo = {k.upper(): v for k, v in topo.water_heaters.items() if v.type == "WaterHeater:Mixed"}
    whs += sorted(v.name for k, v in wh_topo.items() if k not in whs)
    for i, wname in enumerate(whs, start=1):
        did = f"DHW-{i}"
        wh = wh_topo.get(wname.upper())
        if wh is not None and wh.fuel.lower() == "electricity":
            cat.add_equip(Equipment(did, "WaterHeater", wh.name, "Domestic (service) hot-water heater, electric",
                                    meta={"fuel": wh.fuel, "capacity_kw": (wh.capacity_w or 0) / 1000.0 or None,
                                          "volume_m3": wh.volume_m3,
                                          "sp_schedule": man.commands.get(f"{wh.name} SP", {}).get("schedule")}))
            sensor(did, "WaterHeater", "TANK-T", "Tank water temperature", "degC", "water_temperature",
                   raw(cat.var("Water Heater Tank Temperature", wh.name)), ["domestic", "water", "temp", "sensor"],
                   "Hot_Water_Supply_Temperature_Sensor", tier="advanced")
            pa = cat.var("Water Heater Electricity Rate", wh.name)
            sensor(did, "WaterHeater", "STS", "Element status", "-", "binary", lambda v, dt, a=pa: 1.0 if v.get(a, 0.0) > 1.0 else 0.0,
                   ["domestic", "water", "run", "sensor"], "Run_Status", tier="advanced")
            sensor(did, "WaterHeater", "ELEC-PWR", "Water heater electric power", "kW", "power_small", raw(pa, 0.001),
                   ["domestic", "elec", "power", "sensor"], "Electric_Power_Sensor", tier="advanced")
            sensor(did, "WaterHeater", "USE-F", "Hot-water draw (flow meter)", "L/s", "water_flow",
                   raw(cat.var("Water Heater Use Side Mass Flow Rate", wh.name), 1000.0 / RHO_WATER),
                   ["domestic", "water", "flow", "sensor"], "Water_Flow_Sensor", tier="next_gen")
            sp = man.commands.get(f"{wh.name} SP", {}).get("schedule")
            if sp:
                soft(did, "WaterHeater", "TANK-SP", "Tank set point", "degC", "setpoint", ["domestic", "water", "temp", "sp"],
                     "Hot_Water_Supply_Temperature_Setpoint", tier="advanced")
                cat.schedule_actuator(sp)
            continue
        cat.add_equip(Equipment(did, "WaterHeater", wname, "Domestic (service) hot-water heater, gas fired"))
        sensor(did, "WaterHeater", "TANK-T", "Tank water temperature", "degC", "water_temperature",
               raw(cat.var("Water Heater Tank Temperature", wname)), ["domestic", "water", "temp", "sensor"],
               "Hot_Water_Supply_Temperature_Sensor", tier="advanced")
        hq = cat.var("Water Heater Heating Rate", wname)
        sensor(did, "WaterHeater", "STS", "Burner status", "-", "binary", lambda v, dt, a=hq: 1.0 if v.get(a, 0.0) > 1.0 else 0.0,
               ["domestic", "water", "run", "sensor"], "Run_Status", tier="advanced")
        sensor(did, "WaterHeater", "GAS-KW", "Gas input", "kW", "power", raw(cat.var("Water Heater NaturalGas Rate", wname), 0.001),
               ["domestic", "gas", "power", "sensor"], "Natural_Gas_Usage_Sensor", tier="advanced")
        sensor(did, "WaterHeater", "USE-F", "Hot-water draw (flow meter)", "L/s", "water_flow",
               raw(cat.var("Water Heater Use Side Mass Flow Rate", wname), 1000.0 / RHO_WATER),
               ["domestic", "water", "flow", "sensor"], "Water_Flow_Sensor", tier="next_gen")

    _zone_equipment_points(cat, man, sensor, soft, calc, raw)
    _der_points(cat, man, sensor, soft, calc, raw)

    # ---------------------------------------------------------------- return plenums
    for z in topo.zones.values():
        if z.thermostat or "PLENUM" not in z.name.upper():
            continue
        pid_ = f"PLN-{_id_safe(z.name)}"
        cat.add_equip(Equipment(pid_, "Plenum", z.name, f"Return-air plenum {z.name}", meta={"multiplier": z.multiplier}))
        sensor(pid_, "Plenum", "T", "Plenum air temperature", "degC", "air_temperature",
               raw(cat.var("Zone Air Temperature", z.name)), ["plenum", "air", "temp", "sensor"], "Air_Temperature_Sensor",
               tier="advanced")

    # ---------------------------------------------------------------- run-hours / starts of every status point
    for p in list(cat.points.values()):
        if p.kind == "sensor" and p.sensor_class == "binary" and p.name.endswith("STS") and \
                p.equip_type in ("AHU", "Pump", "Chiller", "Boiler", "CoolingTower", "HeatPump", "PTAC", "ERV"):
            pre = p.name[:-3]
            calc(p.equip, p.equip_type, f"{pre}RUNHRS", f"Run-hours ({p.description.lower()})", "h", ["runtime"],
                 "Run_Time_Sensor")
            calc(p.equip, p.equip_type, f"{pre}STARTS", f"Start count ({p.description.lower()})", "count", ["starts"])

    # ---------------------------------------------------------------- tiers / sources of pre-existing points
    overrides = {"OAD-POS": "advanced", "CCV-POS": "advanced", "HCV-POS": "advanced", "SA-RH": "advanced",
                 "RA-RH": "advanced", "CC-LAT": "advanced"}
    for p in cat.points.values():
        if p.equip_type == "AHU" and p.name in overrides:
            p.tier = overrides[p.name]
        if p.equip_type in ("Chiller", "Boiler") and p.name in ("LOAD", "GAS-KW"):
            p.tier = "advanced"
        if p.meta.get("surrogate"):
            p.source = "surrogate"
        if p.kind == "truth":
            p.tier = "truth"

    # building-level actuators
    s = man.commands.get("OUTDOOR CO2", {}).get("schedule")
    if s:
        cat.schedule_actuator(s)
    for c in ["Outdoor Dry Bulb", "Outdoor Relative Humidity", "Direct Solar", "Diffuse Solar", "Wind Speed", "Outdoor Dew Point"]:
        cat.actuator("Weather Data", c, "Environment")
    return cat


ZONE_EQUIP_PREFIX = {"heat_pump": ("HP", "HeatPump"), "ptac": ("PTAC", "PTAC"), "erv": ("ERV", "ERV"),
                     "baseboard": ("BB", "Baseboard"), "ideal_loads": ("IDL", "IdealLoads")}


def _zone_equipment_points(cat: Catalog, man: Manifest, sensor, soft, calc, raw) -> None:
    """Zone heat pumps / PTACs / ERVs / baseboards / ideal loads (ZoneHVAC:EquipmentList units)."""
    topo = man.topo
    for zid, zname in list(cat.zone_of_equip.items()):
        z = topo.zones[zname]
        ids = []
        for ze in topo.zone_equipment_of(zname):
            pre, etype = ZONE_EQUIP_PREFIX[ze.kind]
            eid, n = f"{pre}-{_id_safe(zname)}", 2
            while eid in cat.equipment:
                eid, n = f"{pre}-{_id_safe(zname)}-{n}", n + 1
            en = man.commands.get(f"{ze.name} ENABLE", {})
            deg = man.faults.get(f"{ze.name} DEGRADE")
            hx = man.faults.get(f"{ze.name} HX")
            x = ze.extra
            meta = {"zone": zname, "zone_equip": zid, "eplus_type": ze.type, "kind": ze.kind,
                    "enable_schedule": en.get("schedule"), "enable_default": en.get("default", 1.0),
                    "degrade_fault": f"{ze.name} DEGRADE" if deg else None, "hx_fault": f"{ze.name} HX" if hx else None}
            if ze.kind in ("heat_pump", "ptac"):
                meta.update({"fan": ze.fan.name if ze.fan else None,
                             "design_flow_m3s": x.get("cooling_flow_m3s") or x.get("heating_flow_m3s"),
                             "cooling_coil": ze.cooling_coil.name if ze.cooling_coil else None,
                             "heating_coil": ze.heating_coil.name if ze.heating_coil else None,
                             "supp_coil": ze.supp_coil.name if ze.supp_coil else None,
                             "cooling_capacity_w": man.design_value(ze.cooling_coil.type, ze.cooling_coil.name,
                                                                    "Gross Rated Total Cooling Capacity", None) if ze.cooling_coil else None})
            elif ze.kind == "erv":
                meta.update({"supply_fan": x.get("supply_fan"), "exhaust_fan": x.get("exhaust_fan"), "hx": x.get("hx"),
                             "design_flow_m3s": x.get("supply_flow_m3s"), "eps_sens": x.get("eps_sens_heating")})
            desc = {"heat_pump": f"Zone heat pump ({ze.type.split(':')[-1]}) serving {zname}",
                    "ptac": f"Packaged terminal air conditioner serving {zname}",
                    "erv": f"Energy-recovery ventilator serving {zname}",
                    "baseboard": f"Electric baseboard heater in {zname}",
                    "ideal_loads": f"Ideal loads air system serving {zname} (idealised HVAC)"}[ze.kind]
            cat.add_equip(Equipment(eid, etype, ze.name, desc, meta=meta))
            ids.append(eid)
            if en.get("schedule"):
                soft(eid, etype, "ENABLE", "Unit enable command (BAS start/stop)", "-", "command", ["enable", "cmd"],
                     "Enable_Command", writable=True)
                cat.schedule_actuator(en["schedule"])
            if ze.kind in ("heat_pump", "ptac"):
                _heat_pump_points(cat, eid, etype, ze, man, sensor, soft, calc, raw, deg)
            elif ze.kind == "erv":
                _erv_points(cat, eid, ze, sensor, soft, calc, raw, hx)
            elif ze.kind == "baseboard":
                sensor(eid, etype, "ELEC-PWR", "Baseboard electric power", "kW", "power_small",
                       raw(cat.var("Baseboard Electricity Rate", ze.name), 0.001), ["heating", "elec", "power", "sensor"],
                       "Electric_Power_Sensor", tier="advanced")
            else:
                sensor(eid, etype, "HTG-Q", "Ideal loads sensible heating rate", "kW", "ideal",
                       raw(cat.var("Zone Ideal Loads Supply Air Sensible Heating Rate", ze.name), 0.001), ["heating", "power"],
                       "", kind="truth")
                sensor(eid, etype, "CLG-Q", "Ideal loads sensible cooling rate", "kW", "ideal",
                       raw(cat.var("Zone Ideal Loads Supply Air Sensible Cooling Rate", ze.name), 0.001), ["cooling", "power"],
                       "", kind="truth")
        if ids:
            e = cat.equipment[zid]
            e.meta["zone_equipment"] = ids
            primary = next((i for i in ids if cat.equipment[i].type in ("HeatPump", "PTAC", "Baseboard", "IdealLoads")), None)
            if e.parent is None and primary:
                e.parent = primary      # the room thermostat is wired to the unit controller
            e.meta["hvac"] = primary


def _heat_pump_points(cat, eid, etype, ze, man, sensor, soft, calc, raw, deg) -> None:
    rep = ze.extra.get("report") or "Zone Packaged Terminal Heat Pump"
    fan = ze.fan.name if ze.fan else None
    if fan:
        fp = cat.var("Fan Electricity Rate", fan)
        sensor(eid, etype, "STS", "Unit run status (fan current switch)", "-", "binary",
               lambda v, dt, a=fp: 1.0 if v.get(a, 0.0) > 1.0 else 0.0, ["fan", "run", "sensor"], "Run_Status")
        sensor(eid, etype, "FAN-PWR", "Supply fan power", "kW", "power_small", raw(fp, 0.001), ["fan", "power", "sensor"],
               "Electric_Power_Sensor", tier="advanced")
    sensor(eid, etype, "ELEC-PWR", "Unit electric power (compressor + fan + supplemental heat)", "kW", "power_small",
           raw(cat.var(f"{rep} Electricity Rate", ze.name), 0.001), ["elec", "power", "sensor"], "Electric_Power_Sensor")
    qc, qh = cat.var(f"{rep} Total Cooling Rate", ze.name), cat.var(f"{rep} Total Heating Rate", ze.name)
    sensor(eid, etype, "CLG-Q", "Total cooling rate delivered (refrigerant-side BTU estimate)", "kW", "thermal_power_small",
           raw(qc, 0.001), ["cooling", "power", "sensor"], "Thermal_Power_Sensor", tier="next_gen")
    sensor(eid, etype, "HTG-Q", "Total heating rate delivered (refrigerant-side BTU estimate)", "kW", "thermal_power_small",
           raw(qh, 0.001), ["heating", "power", "sensor"], "Thermal_Power_Sensor", tier="next_gen")
    pa = cat.var(f"{rep} Electricity Rate", ze.name)
    sensor(eid, etype, "COP", "Unit coefficient of performance (ground truth)", "-", "ideal",
           lambda v, dt, a=qc, b=qh, c=pa: (v.get(a, 0.0) + v.get(b, 0.0)) / v.get(c, 0.0) if v.get(c, 0.0) > 50.0 else float("nan"),
           ["cop"], "", kind="truth")
    sensor(eid, etype, "COMP-PLR", "Compressor part-load ratio (ground truth)", "-", "ideal",
           raw(cat.var(f"{rep} Compressor Part Load Ratio", ze.name)), ["compressor", "plr"], "", kind="truth")
    if ze.outlet:
        sensor(eid, etype, "SA-T", "Supply (discharge) air temperature", "degC", "air_temperature",
               raw(cat.var("System Node Temperature", ze.outlet)), ["discharge", "air", "temp", "sensor"],
               "Discharge_Air_Temperature_Sensor")
        sensor(eid, etype, "SA-F", "Supply air flow", "m3/s", "air_flow",
               raw(cat.var("System Node Mass Flow Rate", ze.outlet), 1 / RHO_AIR), ["discharge", "air", "flow", "sensor"],
               "Discharge_Air_Flow_Sensor", tier="advanced")
    if ze.inlet:
        sensor(eid, etype, "RA-T", "Return (entering) air temperature", "degC", "air_temperature",
               raw(cat.var("System Node Temperature", ze.inlet)), ["return", "air", "temp", "sensor"],
               "Return_Air_Temperature_Sensor", tier="advanced")
    hc = ze.heating_coil
    if hc and hc.type.startswith("Coil:Heating:DX"):
        da = cat.var("Heating Coil Defrost Electricity Rate", hc.name)
        sensor(eid, etype, "DEFROST", "Defrost cycle active", "-", "binary", lambda v, dt, a=da: 1.0 if v.get(a, 0.0) > 1.0 else 0.0,
               ["defrost", "sensor"], "Defrost_Status", tier="advanced")
        sensor(eid, etype, "DEFROST-PWR", "Defrost electric power", "kW", "power_small", raw(da, 0.001), ["defrost", "power", "sensor"],
               "Electric_Power_Sensor", tier="next_gen")
    sc = ze.supp_coil
    if sc and sc.type == "Coil:Heating:Electric":
        sensor(eid, etype, "SUPP-PWR", "Supplemental (auxiliary) electric heat power", "kW", "power_small",
               raw(cat.var("Heating Coil Electricity Rate", sc.name), 0.001), ["heating", "aux", "power", "sensor"],
               "Electric_Power_Sensor", tier="advanced")
    if ze.cooling_coil:
        sensor(eid, etype, "CLG-COIL-PWR", "Cooling compressor power", "kW", "power_small",
               raw(cat.var("Cooling Coil Electricity Rate", ze.cooling_coil.name), 0.001), ["cooling", "compressor", "power",
                                                                                         "sensor"],
               "Electric_Power_Sensor", tier="next_gen")
    sensor(eid, etype, "ALM", "Unit lock-out / trip alarm", "-", "binary", None, ["alarm", "sensor"], "Alarm")
    soft(eid, etype, "MODE", "Unit operating mode (0 idle, 1 cooling, 2 heating, -1 disabled)", "-", "status",
         ["mode"], "Mode_Status", writable=False)
    if deg:
        for k in ("active_schedule", "value_schedule", "cop_schedule"):
            cat.schedule_actuator(deg[k])


def _erv_points(cat, eid, ze, sensor, soft, calc, raw, hx) -> None:
    x = ze.extra
    T = "ERV"
    vd = x.get("supply_flow_m3s") or 0.05
    if x.get("supply_fan"):
        sm = cat.var("Fan Air Mass Flow Rate", x["supply_fan"])
        sensor(eid, T, "SA-F", "Supply (outdoor) air flow", "m3/s", "air_flow", raw(sm, 1 / RHO_AIR),
               ["discharge", "air", "flow", "sensor"], "Supply_Air_Flow_Sensor", tier="advanced")
        sensor(eid, T, "STS", "Supply fan status (current switch)", "-", "binary",
               lambda v, dt, a=sm, d=vd: 1.0 if v.get(a, 0.0) / RHO_AIR > 0.1 * d else 0.0, ["fan", "run", "sensor"], "Fan_Status")
        sensor(eid, T, "SF-PWR", "Supply fan power", "kW", "power_small", raw(cat.var("Fan Electricity Rate", x["supply_fan"]), 0.001),
               ["discharge", "fan", "power", "sensor"], "Electric_Power_Sensor", tier="advanced")
        cat.actuator("Fan", "Fan Air Mass Flow Rate", x["supply_fan"])
    if x.get("exhaust_fan"):
        em = cat.var("Fan Air Mass Flow Rate", x["exhaust_fan"])
        sensor(eid, T, "EA-F", "Exhaust air flow", "m3/s", "air_flow", raw(em, 1 / RHO_AIR),
               ["exhaust", "air", "flow", "sensor"], "Exhaust_Air_Flow_Sensor", tier="advanced")
        sensor(eid, T, "EF-STS", "Exhaust fan status (current switch)", "-", "binary",
               lambda v, dt, a=em, d=vd: 1.0 if v.get(a, 0.0) / RHO_AIR > 0.1 * d else 0.0, ["exhaust", "fan", "run", "sensor"],
               "Fan_Status")
        sensor(eid, T, "EF-PWR", "Exhaust fan power", "kW", "power_small", raw(cat.var("Fan Electricity Rate", x["exhaust_fan"]), 0.001),
               ["exhaust", "fan", "power", "sensor"], "Electric_Power_Sensor", tier="advanced")
        cat.actuator("Fan", "Fan Air Mass Flow Rate", x["exhaust_fan"])
    if ze.outlet:
        sensor(eid, T, "SA-T", "Supply air temperature (to the room)", "degC", "air_temperature",
               raw(cat.var("System Node Temperature", ze.outlet)), ["discharge", "air", "temp", "sensor"],
               "Supply_Air_Temperature_Sensor")
    to = x.get("hx_supply_inlet")
    tl = x.get("hx_supply_outlet")
    te = x.get("hx_exhaust_inlet")
    if to:
        sensor(eid, T, "OA-T", "Outdoor air temperature at the ERV intake", "degC", "outdoor_temperature",
               raw(cat.var("System Node Temperature", to)), ["outside", "air", "temp", "sensor"], "Outside_Air_Temperature_Sensor",
               tier="advanced")
    if te:
        sensor(eid, T, "RA-T", "Return (room exhaust) air temperature entering the ERV", "degC", "air_temperature",
               raw(cat.var("System Node Temperature", te)), ["return", "air", "temp", "sensor"], "Return_Air_Temperature_Sensor",
               tier="advanced")
    if x.get("hx_exhaust_outlet"):
        sensor(eid, T, "EA-T", "Exhaust air temperature leaving the ERV core", "degC", "air_temperature",
               raw(cat.var("System Node Temperature", x["hx_exhaust_outlet"])), ["exhaust", "air", "temp", "sensor"],
               "Exhaust_Air_Temperature_Sensor", tier="next_gen")
    if to and tl and te:
        a_o, a_l, a_e = (cat.var("System Node Temperature", n) for n in (to, tl, te))
        a_f = cat.var("Fan Air Mass Flow Rate", x["supply_fan"]) if x.get("supply_fan") else None

        def eff(v, dt, a_o=a_o, a_l=a_l, a_e=a_e, a_f=a_f):
            d = v.get(a_e, 0.0) - v.get(a_o, 0.0)
            if abs(d) < 2.0 or (a_f and v.get(a_f, 0.0) < 1e-4):
                return float("nan")
            return max(0.0, min(1.2, (v.get(a_l, 0.0) - v.get(a_o, 0.0)) / d))
        sensor(eid, T, "HX-EFF", "Heat-recovery sensible effectiveness (from ERV controller temperatures)", "-", "ideal", eff,
               ["heatRecovery", "effectiveness", "sensor"], "", tier="next_gen")
        sensor(eid, T, "HX-LAT", "Supply air temperature leaving the heat-recovery core", "degC", "air_temperature",
               raw(a_l), ["heatRecovery", "leaving", "air", "temp", "sensor"], "Air_Temperature_Sensor", tier="next_gen")
    sensor(eid, T, "ALM", "ERV fan failure / filter alarm", "-", "binary", None, ["alarm", "sensor"], "Alarm")
    if hx:
        cat.schedule_actuator(hx["active_schedule"])
        cat.schedule_actuator(hx["value_schedule"])


def _der_points(cat: Catalog, man: Manifest, sensor, soft, calc, raw) -> None:
    """PV systems, electrical storage and grid import/export of ElectricLoadCenter:Distribution objects."""
    topo = man.topo
    lcs = [lc for lc in topo.load_centers.values() if lc.generators or lc.storage]
    if not lcs:
        return
    loss_vars = []
    n_pv = n_ess = 0
    for lc in lcs:
        pvs = [g for g in lc.generators if g.type.startswith("Generator:P")]
        loss = man.faults.get(f"{lc.name} PV LOSS")
        la = cat.var("Electric Equipment Electricity Rate", loss["loss_object"]) if loss else None
        if la:
            loss_vars.append((la, loss.get("host_zone")))
            cat.actuator("ElectricEquipment", "Electricity Rate", loss["loss_object"])
        eta = float((lc.inverter.extra.get("efficiency") if lc.inverter else None) or 1.0)
        if pvs:
            n_pv += 1
            pid = "PV" if n_pv == 1 else f"PV-{n_pv}"
            dc_cap = sum(float(g.extra.get("dc_capacity_w") or g.extra.get("rated_w") or 0.0) for g in pvs)
            cat.add_equip(Equipment(pid, "PVSystem", lc.name, f"Photovoltaic system ({len(pvs)} array(s), "
                                    f"{dc_cap / 1000.0:.1f} kWp DC) on load centre {lc.name}",
                                    meta={"load_center": lc.name, "dc_capacity_kw": dc_cap / 1000.0,
                                          "inverter": lc.inverter.name if lc.inverter else None, "inverter_eff": eta,
                                          "arrays": [g.name for g in pvs], "buss_type": lc.buss_type,
                                          "loss_fault": f"{lc.name} PV LOSS" if loss else None}))
            dcs = [cat.var("Generator Produced DC Electricity Rate", g.name) for g in pvs]

            def dc_total(v, dt, dcs=tuple(dcs), la=la, eta=eta):
                tot = sum(v.get(a, 0.0) for a in dcs)
                lost = v.get(la, 0.0) / max(eta, 1e-3) if la else 0.0
                return max(0.0, tot - lost) / 1000.0
            sensor(pid, "PVSystem", "DC-PWR", "PV DC power (all arrays)", "kW", "power_small", dc_total,
                   ["solar", "dc", "power", "sensor"], "PV_Generation_Sensor")
            if lc.inverter:
                ia = cat.var("Inverter AC Output Electricity Rate", lc.inverter.name)
                sensor(pid, "PVSystem", "AC-PWR", "Inverter AC output" + (" (PV + DC-coupled battery)"
                                                                          if "DCStorage" in lc.buss_type else ""),
                       "kW", "power_small", lambda v, dt, a=ia, la=la: max(0.0, v.get(a, 0.0) - (v.get(la, 0.0) if la else 0.0)) / 1000.0,
                       ["solar", "ac", "power", "sensor"], "Electric_Power_Sensor")
                sensor(pid, "PVSystem", "INV-STS", "Inverter status (1 = exporting AC)", "-", "binary",
                       lambda v, dt, a=ia, la=la: 1.0 if v.get(a, 0.0) - (v.get(la, 0.0) if la else 0.0) > 10.0 else 0.0,
                       ["inverter", "run", "sensor"], "Run_Status", tier="advanced")
                sensor(pid, "PVSystem", "INV-EFF", "Inverter DC-to-AC efficiency (ground truth)", "-", "ideal",
                       raw(cat.var("Inverter DC to AC Efficiency", lc.inverter.name)), ["inverter", "efficiency"], "", kind="truth")
            if la:
                sensor(pid, "PVSystem", "LOSS-KW", "Lost PV AC output due to soiling / trips / curtailment (ground truth)",
                       "kW", "ideal", raw(la, 0.001), ["solar", "loss"], "", kind="truth")
            sensor(pid, "PVSystem", "ALM", "Inverter fault / ground-fault alarm", "-", "binary", None, ["inverter", "alarm", "sensor"],
                   "Alarm", tier="advanced")
            for g in pvs:
                aid = f"PVA-{_id_safe(g.name)}"
                cap = float(g.extra.get("dc_capacity_w") or g.extra.get("rated_w") or 0.0)
                cat.add_equip(Equipment(aid, "PVArray", g.name, f"PV array {g.name} ({cap / 1000.0:.2f} kWp, {g.type})",
                                        parent=pid, meta={"dc_capacity_kw": cap / 1000.0, "type": g.type}))
                ga = cat.var("Generator Produced DC Electricity Rate", g.name)

                def dc_one(v, dt, ga=ga, dcs=tuple(dcs), la=la, eta=eta):
                    tot = sum(v.get(a, 0.0) for a in dcs)
                    lost = v.get(la, 0.0) / max(eta, 1e-3) if la else 0.0
                    f = max(0.0, 1.0 - lost / tot) if tot > 1.0 else 1.0
                    return v.get(ga, 0.0) * f / 1000.0
                sensor(aid, "PVArray", "DC-PWR", "Array DC power (string monitor)", "kW", "power_small", dc_one,
                       ["solar", "dc", "power", "sensor"], "PV_Generation_Sensor", tier="advanced")
                sensor(aid, "PVArray", "CELL-T", "PV module (back-of-module) temperature", "degC", "outdoor_temperature",
                       raw(cat.var("Generator PV Cell Temperature", g.name)), ["solar", "module", "temp", "sensor"],
                       "PV_Panel_Temperature_Sensor", tier="next_gen")
        st = lc.storage
        if st:
            n_ess += 1
            sid = "ESS" if n_ess == 1 else f"ESS-{n_ess}"
            cap_j = float(st.extra.get("capacity_j") or 0.0)
            pch = float(st.extra.get("max_charge_w") or 0.0)
            pdis = float(st.extra.get("max_discharge_w") or 0.0)
            cat.add_equip(Equipment(sid, "Battery", st.name, f"Electrical energy storage {st.name} ({st.type.split(':')[-1]}"
                                    + (f", {cap_j / 3.6e6:.1f} kWh" if cap_j else "") + ")",
                                    meta={"load_center": lc.name, "storage_type": st.type, "capacity_kwh": cap_j / 3.6e6 or None,
                                          "max_charge_kw": pch / 1000.0 or None, "max_discharge_kw": pdis / 1000.0 or None,
                                          "min_soc": lc.min_soc, "max_soc": lc.max_soc, "storage_scheme": lc.storage_scheme,
                                          "eff_charge": st.extra.get("eff_charge"), "eff_discharge": st.extra.get("eff_discharge")}))
            if st.type.endswith("Storage:Simple") and cap_j > 0:
                sa = cat.var("Electric Storage Simple Charge State", st.name)
                sensor(sid, "Battery", "SOC", "State of charge (BMS)", "-", "soc", raw(sa, 1.0 / cap_j),
                       ["battery", "soc", "sensor"], "Battery_State_Of_Charge_Sensor")
                sensor(sid, "Battery", "SOC-KWH", "Stored energy (BMS)", "kWh", "energy", raw(sa, 1.0 / 3.6e6),
                       ["battery", "energy", "sensor"], "Battery_Energy_Sensor", tier="advanced")
            else:
                sensor(sid, "Battery", "SOC", "State of charge (BMS)", "-", "soc",
                       raw(cat.var("Electric Storage Charge Fraction", st.name)), ["battery", "soc", "sensor"],
                       "Battery_State_Of_Charge_Sensor")
            ca = cat.var("Electric Storage Charge Power", st.name)
            da = cat.var("Electric Storage Discharge Power", st.name)
            sensor(sid, "Battery", "CHG-PWR", "Charge power", "kW", "power_small", raw(ca, 0.001), ["battery", "charge", "power", "sensor"],
                   "Electric_Power_Sensor")
            sensor(sid, "Battery", "DCHG-PWR", "Discharge power", "kW", "power_small", raw(da, 0.001),
                   ["battery", "discharge", "power", "sensor"], "Electric_Power_Sensor")
            sensor(sid, "Battery", "STS", "Battery state (1 charging, 0 idle, -1 discharging)", "-", "ideal",
                   lambda v, dt, a=ca, b=da: 1.0 if v.get(a, 0.0) > 10.0 else (-1.0 if v.get(b, 0.0) > 10.0 else 0.0),
                   ["battery", "mode", "sensor"], "Mode_Status", tier="advanced")
            sensor(sid, "Battery", "ALM", "BMS fault alarm", "-", "binary", None, ["battery", "alarm", "sensor"], "Alarm",
                   tier="advanced")
            soft(sid, "Battery", "CHG-CMD", "Charge power command (blank = native storage scheme)", "kW", "command",
                 ["battery", "charge", "power", "cmd"], "Power_Command", writable=True)
            soft(sid, "Battery", "DCHG-CMD", "Discharge power command (blank = native storage scheme)", "kW", "command",
                 ["battery", "discharge", "power", "cmd"], "Power_Command", writable=True)
            soft(sid, "Battery", "RESERVE-SP", "Backup reserve (minimum state of charge for dispatch)", "-", "setpoint",
                 ["battery", "soc", "sp"], "Battery_Energy_Setpoint", writable=True)
            soft(sid, "Battery", "MODE", "Dispatch mode (0 native storage scheme, 1 BAS dispatch)", "-", "status",
                 ["battery", "mode"], "Mode_Status", writable=False)
            cat.actuator("Electrical Storage", "Power Draw Rate", lc.name)
            cat.actuator("Electrical Storage", "Power Charge Rate", lc.name)
    # ---- grid connection (utility meter with net metering)
    if "GRID" in cat.equipment:
        G = "Grid"
        for nm, var, desc, brick in [("IMPORT-PWR", "Facility Total Purchased Electricity Rate", "Grid import power", "Electric_Power_Sensor"),
                                     ("EXPORT-PWR", "Facility Total Surplus Electricity Rate", "Grid export power", "Electric_Power_Sensor"),
                                     ("NET-PWR", "Facility Net Purchased Electricity Rate", "Net grid power (import - export)",
                                      "Electric_Power_Sensor")]:
            sensor("GRID", G, nm, desc + " (revenue meter)", "kW", "power_small", raw(cat.var(var, "Whole Building"), 0.001),
                   ["elec", "grid", "power", "sensor"], brick, kind="meter")
        sensor("GRID", G, "OUTAGE", "Utility grid outage (1 = grid down)", "-", "binary", None, ["grid", "outage", "sensor"], "",
               tier="advanced")
        sensor("GRID", G, "UNSERVED-KW", "Load not served by on-site sources during a grid outage (ground truth)", "kW",
               "ideal", None, ["grid", "unserved"], "", kind="truth")
    # ---- the lost-PV load is not a building load: remove it from the facility, plug-load and zone sub-meters
    if loss_vars:
        allv = tuple(a for a, _ in loss_vars)
        targets = {"MTR/BLDG-ELEC-KW": allv, "MTR/PLUG-KW": allv}
        for a, zone in loss_vars:
            if zone:
                targets.setdefault(f"ZN-{_id_safe(zone)}/PLUG-KW", ())
                targets[f"ZN-{_id_safe(zone)}/PLUG-KW"] += (a,)
        for pid, las in targets.items():
            fn = cat.truth.get(pid)
            if fn is not None and las:
                cat.truth[pid] = lambda v, dt, fn=fn, la=las: fn(v, dt) - sum(v.get(a, 0.0) for a in la) / 1000.0

