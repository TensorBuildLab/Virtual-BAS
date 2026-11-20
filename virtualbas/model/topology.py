"""Generic HVAC topology discovery from an epJSON model.

The discovery walks EnergyPlus' own connection objects (AirLoopHVAC, Branch, BranchList,
SupplyPath, ZoneSplitter, ZoneHVAC:EquipmentConnections, PlantLoop, CondenserLoop ...)
and returns a building-agnostic description of the equipment that a Building
Automation System would expose as points: zones, terminal units, air handling units and
plant loops with their primary equipment. Nothing in this module is specific to the DOE
large office; any model with the supported object types can be converted.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .epjson import EpJSON, find_object, node_list

TERMINAL_TYPES = [
    "AirTerminal:SingleDuct:VAV:Reheat",
    "AirTerminal:SingleDuct:VAV:NoReheat",
]
CHILLER_TYPES = [
    "Chiller:Electric:ReformulatedEIR",
    "Chiller:Electric:EIR",
    "Chiller:Electric",
    "Chiller:ConstantCOP",
]
BOILER_TYPES = ["Boiler:HotWater"]
TOWER_TYPES = ["CoolingTower:SingleSpeed", "CoolingTower:TwoSpeed", "CoolingTower:VariableSpeed:Merkel", "CoolingTower:VariableSpeed"]
PUMP_TYPES = ["Pump:VariableSpeed", "Pump:ConstantSpeed", "HeaderedPumps:VariableSpeed", "HeaderedPumps:ConstantSpeed"]
FAN_TYPES = ["Fan:VariableVolume", "Fan:ConstantVolume", "Fan:SystemModel", "Fan:OnOff"]
CCOIL_TYPES = ["Coil:Cooling:Water", "Coil:Cooling:Water:DetailedGeometry"]
HCOIL_TYPES = ["Coil:Heating:Water", "Coil:Heating:Electric", "Coil:Heating:Fuel"]
# zone (forced-air or radiant) equipment listed in ZoneHVAC:EquipmentList -> kind
ZONE_EQUIP_KINDS = {
    "ZoneHVAC:PackagedTerminalHeatPump": "heat_pump",
    "ZoneHVAC:PackagedTerminalAirConditioner": "ptac",
    "ZoneHVAC:WaterToAirHeatPump": "heat_pump",
    "ZoneHVAC:EnergyRecoveryVentilator": "erv",
    "ZoneHVAC:Baseboard:Convective:Electric": "baseboard",
    "ZoneHVAC:Baseboard:RadiantConvective:Electric": "baseboard",
    "ZoneHVAC:IdealLoadsAirSystem": "ideal_loads",
}
# E+ output-variable prefix of the unit-level reports ("<prefix> Electricity Rate", "... Total Heating Rate")
ZONE_EQUIP_REPORT = {
    "ZoneHVAC:PackagedTerminalHeatPump": "Zone Packaged Terminal Heat Pump",
    "ZoneHVAC:PackagedTerminalAirConditioner": "Zone Packaged Terminal Air Conditioner",
    "ZoneHVAC:WaterToAirHeatPump": "Zone Water to Air Heat Pump",
}
PV_TYPES = ["Generator:PVWatts", "Generator:Photovoltaic"]
STORAGE_TYPES = ["ElectricLoadCenter:Storage:Simple", "ElectricLoadCenter:Storage:Battery",
                 "ElectricLoadCenter:Storage:LiIonNMCBattery"]
INVERTER_TYPES = ["ElectricLoadCenter:Inverter:PVWatts", "ElectricLoadCenter:Inverter:Simple",
                  "ElectricLoadCenter:Inverter:FunctionOfPower", "ElectricLoadCenter:Inverter:LookUpTable"]
WATER_HEATER_TYPES = ["WaterHeater:Mixed", "WaterHeater:Stratified"]


@dataclass
class Component:
    type: str
    name: str
    inlet: str | None = None
    outlet: str | None = None
    water_inlet: str | None = None
    water_outlet: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class Zone:
    name: str
    multiplier: int = 1
    thermostat: str | None = None
    air_node: str | None = None
    return_node: str | None = None
    terminal: str | None = None
    air_loop: str | None = None
    people: list[str] = field(default_factory=list)
    lights: list[str] = field(default_factory=list)
    equipment: list[str] = field(default_factory=list)
    infiltration: list[str] = field(default_factory=list)        # actuatable ZoneInfiltration:DesignFlowRate objects
    zone_equipment: list[str] = field(default_factory=list)      # ZoneHVAC:* units (see Topology.zone_equipment)
    infiltration_other: list[str] = field(default_factory=list)  # leakage-area / flow-coefficient infiltration
    infiltration_window: str | None = None                       # zero-flow DesignFlowRate added by prepare (events)


@dataclass
class ZoneEquipment:
    """A zone-level HVAC unit from ZoneHVAC:EquipmentList (heat pump, PTAC, ERV, baseboard, ideal loads)."""
    name: str
    type: str
    kind: str                      # heat_pump | ptac | erv | baseboard | ideal_loads
    zone: str
    inlet: str | None = None
    outlet: str | None = None
    availability_schedule: str | None = None
    fan: Component | None = None
    cooling_coil: Component | None = None
    heating_coil: Component | None = None
    supp_coil: Component | None = None
    sequence: int = 1
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class LoadCenter:
    """ElectricLoadCenter:Distribution with its generators, inverter and electrical storage."""
    name: str
    buss_type: str = ""
    generator_scheme: str = ""
    storage_scheme: str = ""
    generators: list[Component] = field(default_factory=list)
    inverter: Component | None = None
    storage: Component | None = None
    min_soc: float = 0.0
    max_soc: float = 1.0


@dataclass
class WaterHeater:
    name: str
    type: str
    fuel: str = "NaturalGas"
    setpoint_schedule: str | None = None
    capacity_w: float | None = None
    volume_m3: float | None = None
    standalone: bool = True        # True if not connected to a plant loop (no use-side nodes)


@dataclass
class Terminal:
    name: str
    type: str
    zone: str
    inlet: str
    outlet: str
    damper_node: str | None = None
    reheat: Component | None = None
    air_loop: str | None = None


@dataclass
class AirLoop:
    name: str
    supply_inlet: str
    supply_outlet: str
    demand_inlet: str
    oa_controller: str | None = None
    mixed_air_node: str | None = None
    oa_node: str | None = None
    return_node: str | None = None
    relief_node: str | None = None
    fan: Component | None = None
    cooling_coils: list[Component] = field(default_factory=list)
    heating_coils: list[Component] = field(default_factory=list)
    terminals: list[str] = field(default_factory=list)
    zones: list[str] = field(default_factory=list)
    availability_manager_list: str | None = None


@dataclass
class PlantLoop:
    name: str
    kind: str  # chilled_water | hot_water | condenser | service_hot_water | other
    supply_inlet: str
    supply_outlet: str
    demand_inlet: str
    demand_outlet: str
    setpoint_node: str | None = None
    chillers: list[Component] = field(default_factory=list)
    boilers: list[Component] = field(default_factory=list)
    towers: list[Component] = field(default_factory=list)
    pumps: list[Component] = field(default_factory=list)
    other_supply: list[Component] = field(default_factory=list)
    demand_components: list[Component] = field(default_factory=list)


@dataclass
class Topology:
    zones: dict[str, Zone] = field(default_factory=dict)
    terminals: dict[str, Terminal] = field(default_factory=dict)
    air_loops: dict[str, AirLoop] = field(default_factory=dict)
    plant_loops: dict[str, PlantLoop] = field(default_factory=dict)
    setpoint_managers: list[dict[str, Any]] = field(default_factory=list)
    zone_equipment: dict[str, ZoneEquipment] = field(default_factory=dict)
    load_centers: dict[str, LoadCenter] = field(default_factory=dict)
    water_heaters: dict[str, WaterHeater] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "Topology":
        def comp(c):
            return Component(**c) if c else None

        t = Topology()
        for k, z in d.get("zones", {}).items():
            t.zones[k] = Zone(**z)
        for k, v in d.get("terminals", {}).items():
            v = dict(v)
            v["reheat"] = comp(v.get("reheat"))
            t.terminals[k] = Terminal(**v)
        for k, v in d.get("air_loops", {}).items():
            v = dict(v)
            v["fan"] = comp(v.get("fan"))
            v["cooling_coils"] = [comp(c) for c in v.get("cooling_coils", [])]
            v["heating_coils"] = [comp(c) for c in v.get("heating_coils", [])]
            t.air_loops[k] = AirLoop(**v)
        for k, v in d.get("plant_loops", {}).items():
            v = dict(v)
            for key in ["chillers", "boilers", "towers", "pumps", "other_supply", "demand_components"]:
                v[key] = [comp(c) for c in v.get(key, [])]
            t.plant_loops[k] = PlantLoop(**v)
        t.setpoint_managers = d.get("setpoint_managers", [])
        for k, v in d.get("zone_equipment", {}).items():
            v = dict(v)
            for key in ("fan", "cooling_coil", "heating_coil", "supp_coil"):
                v[key] = comp(v.get(key))
            t.zone_equipment[k] = ZoneEquipment(**v)
        for k, v in d.get("load_centers", {}).items():
            v = dict(v)
            v["generators"] = [comp(c) for c in v.get("generators", [])]
            v["inverter"], v["storage"] = comp(v.get("inverter")), comp(v.get("storage"))
            t.load_centers[k] = LoadCenter(**v)
        for k, v in d.get("water_heaters", {}).items():
            t.water_heaters[k] = WaterHeater(**v)
        return t

    # convenience -------------------------------------------------------------
    def conditioned_zones(self) -> list[Zone]:
        return [z for z in self.zones.values() if z.thermostat]

    def loops_of_kind(self, kind: str) -> list[PlantLoop]:
        return [p for p in self.plant_loops.values() if p.kind == kind]

    def zone_equipment_of(self, zone: str, kinds: tuple[str, ...] | None = None) -> list[ZoneEquipment]:
        out = [self.zone_equipment[n] for n in self.zones[zone].zone_equipment if n in self.zone_equipment]
        return [e for e in out if kinds is None or e.kind in kinds]


def _u(s: str | None) -> str:
    return (s or "").upper()


def _water_nodes(model: EpJSON, ctype: str, cname: str) -> tuple[str | None, str | None]:
    o = find_object(model, ctype, cname) or {}
    wi = o.get("water_inlet_node_name") or o.get("chilled_water_inlet_node_name")
    wo = o.get("water_outlet_node_name") or o.get("chilled_water_outlet_node_name")
    return wi, wo


def _branch_components(model: EpJSON, branch_list: str) -> list[Component]:
    comps: list[Component] = []
    bl = find_object(model, "BranchList", branch_list) or {}
    for b in bl.get("branches", []):
        br = find_object(model, "Branch", b["branch_name"]) or {}
        for c in br.get("components", []):
            comps.append(
                Component(
                    type=c["component_object_type"],
                    name=c["component_name"],
                    inlet=c.get("component_inlet_node_name"),
                    outlet=c.get("component_outlet_node_name"),
                )
            )
    return comps


def discover(model: EpJSON) -> Topology:
    topo = Topology()

    # ---- zones --------------------------------------------------------------
    for zname, z in model.get("Zone", {}).items():
        mult = z.get("multiplier", 1) or 1
        topo.zones[zname] = Zone(name=zname, multiplier=int(mult))
    zone_by_upper = {k.upper(): k for k in topo.zones}

    def zkey(name: str) -> str | None:
        return zone_by_upper.get(_u(name))

    for tname, t in model.get("ZoneControl:Thermostat", {}).items():
        zk = zkey(t.get("zone_or_zonelist_name", ""))
        if zk:
            topo.zones[zk].thermostat = tname

    for objtype, attr in [("People", "people"), ("Lights", "lights"), ("ElectricEquipment", "equipment"),
                          ("ZoneInfiltration:DesignFlowRate", "infiltration"),
                          ("ZoneInfiltration:EffectiveLeakageArea", "infiltration_other"),
                          ("ZoneInfiltration:FlowCoefficient", "infiltration_other")]:
        for oname, o in model.get(objtype, {}).items():
            zk = zkey(o.get("zone_or_zonelist_or_space_or_spacelist_name", "") or o.get("zone_or_space_name", ""))
            if zk:
                getattr(topo.zones[zk], attr).append(oname)

    # zone equipment connections -> terminals
    adu_to_zone: dict[str, str] = {}
    for _, ec in model.get("ZoneHVAC:EquipmentConnections", {}).items():
        zk = zkey(ec.get("zone_name", ""))
        if not zk:
            continue
        topo.zones[zk].air_node = ec.get("zone_air_node_name")
        rn = ec.get("zone_return_air_node_or_nodelist_name")
        if rn:
            topo.zones[zk].return_node = node_list(model, rn)[0]
        el = find_object(model, "ZoneHVAC:EquipmentList", ec.get("zone_conditioning_equipment_list_name", "")) or {}
        for eq in el.get("equipment", []):
            if eq.get("zone_equipment_object_type") == "ZoneHVAC:AirDistributionUnit":
                adu_to_zone[_u(eq["zone_equipment_name"])] = zk
            elif eq.get("zone_equipment_object_type") in ZONE_EQUIP_KINDS:
                ze = _zone_equipment(model, eq["zone_equipment_object_type"], eq["zone_equipment_name"], zk,
                                     int(eq.get("zone_equipment_cooling_sequence", 1) or 1))
                if ze is not None:
                    topo.zone_equipment[ze.name] = ze
                    topo.zones[zk].zone_equipment.append(ze.name)

    inlet_to_zone: dict[str, str] = {}   # inlet node of ANY air terminal -> zone (for AHU zone lists)
    for aname, adu in model.get("ZoneHVAC:AirDistributionUnit", {}).items():
        zk = adu_to_zone.get(_u(aname))
        ttype = adu.get("air_terminal_object_type")
        tname = adu.get("air_terminal_name")
        if zk:
            to_any = find_object(model, ttype, tname) or {}
            inl = to_any.get("air_inlet_node_name")
            if inl:
                inlet_to_zone[_u(inl)] = zk
        if not zk or ttype not in TERMINAL_TYPES:
            continue
        t = find_object(model, ttype, tname) or {}
        reheat = None
        if t.get("reheat_coil_name"):
            wi, wo = _water_nodes(model, t["reheat_coil_object_type"], t["reheat_coil_name"])
            reheat = Component(type=t["reheat_coil_object_type"], name=t["reheat_coil_name"],
                               inlet=t.get("damper_air_outlet_node_name"), outlet=t.get("air_outlet_node_name"),
                               water_inlet=wi, water_outlet=wo)
        term = Terminal(name=tname, type=ttype, zone=zk, inlet=t.get("air_inlet_node_name"),
                        outlet=t.get("air_outlet_node_name"), damper_node=t.get("damper_air_outlet_node_name"),
                        reheat=reheat)
        topo.terminals[tname] = term
        topo.zones[zk].terminal = tname

    term_by_inlet = {_u(t.inlet): t for t in topo.terminals.values()}

    # ---- air loops -------------------------------------------------------------
    supply_paths = {
        _u(sp.get("supply_air_path_inlet_node_name")): sp for sp in model.get("AirLoopHVAC:SupplyPath", {}).values()
    }
    oa_sys_to_controller: dict[str, str] = {}
    for osn, osys in model.get("AirLoopHVAC:OutdoorAirSystem", {}).items():
        cl = find_object(model, "AirLoopHVAC:ControllerList", osys.get("controller_list_name", "")) or {}
        for i in range(1, 9):
            if cl.get(f"controller_{i}_object_type") == "Controller:OutdoorAir":
                oa_sys_to_controller[_u(osn)] = cl[f"controller_{i}_name"]

    for lname, al in model.get("AirLoopHVAC", {}).items():
        sup_out = node_list(model, al.get("supply_side_outlet_node_names"))[0]
        dem_in = node_list(model, al.get("demand_side_inlet_node_names"))[0]
        loop = AirLoop(name=lname, supply_inlet=al.get("supply_side_inlet_node_name"), supply_outlet=sup_out,
                       demand_inlet=dem_in, availability_manager_list=al.get("availability_manager_list_name"))
        for c in _branch_components(model, al.get("branch_list_name", "")):
            if c.type in FAN_TYPES:
                loop.fan = c
            elif c.type in CCOIL_TYPES:
                c.water_inlet, c.water_outlet = _water_nodes(model, c.type, c.name)
                loop.cooling_coils.append(c)
            elif c.type in HCOIL_TYPES:
                c.water_inlet, c.water_outlet = _water_nodes(model, c.type, c.name)
                loop.heating_coils.append(c)
            elif c.type == "AirLoopHVAC:OutdoorAirSystem":
                ctrl = oa_sys_to_controller.get(_u(c.name))
                if ctrl:
                    oac = find_object(model, "Controller:OutdoorAir", ctrl) or {}
                    loop.oa_controller = ctrl
                    loop.mixed_air_node = oac.get("mixed_air_node_name")
                    loop.oa_node = oac.get("actuator_node_name")
                    loop.return_node = oac.get("return_air_node_name")
                    loop.relief_node = oac.get("relief_air_outlet_node_name")
        # zones served via supply path splitter outlets
        sp = supply_paths.get(_u(dem_in))
        if sp:
            for comp in sp.get("components", []):
                if comp.get("component_object_type") == "AirLoopHVAC:ZoneSplitter":
                    spl = find_object(model, "AirLoopHVAC:ZoneSplitter", comp["component_name"]) or {}
                    for n in spl.get("nodes", []):
                        node = _u(n.get("outlet_node_name"))
                        t = term_by_inlet.get(node)
                        if t:
                            t.air_loop = lname
                            loop.terminals.append(t.name)
                        zk = t.zone if t else inlet_to_zone.get(node)
                        if not zk:
                            # direct-to-zone supply (AirTerminal:SingleDuct:Uncontrolled style): node is a zone inlet
                            for _, ec in model.get("ZoneHVAC:EquipmentConnections", {}).items():
                                inl = ec.get("zone_air_inlet_node_or_nodelist_name")
                                if inl and node in [_u(x) for x in node_list(model, inl)]:
                                    zk = zkey(ec.get("zone_name", ""))
                        if zk:
                            loop.zones.append(zk)
                            topo.zones[zk].air_loop = lname
        topo.air_loops[lname] = loop

    # ---- plant & condenser loops -----------------------------------------------
    def build_plant(name: str, o: dict[str, Any], condenser: bool) -> PlantLoop:
        if condenser:
            sup_bl = o.get("condenser_side_branch_list_name")
            dem_bl = o.get("condenser_demand_side_branch_list_name")
            sp_node = o.get("condenser_loop_temperature_setpoint_node_name")
            sin, sout = o.get("condenser_side_inlet_node_name"), o.get("condenser_side_outlet_node_name")
        else:
            sup_bl = o.get("plant_side_branch_list_name")
            dem_bl = o.get("demand_side_branch_list_name")
            sp_node = o.get("loop_temperature_setpoint_node_name")
            sin, sout = o.get("plant_side_inlet_node_name"), o.get("plant_side_outlet_node_name")
        pl = PlantLoop(name=name, kind="other", supply_inlet=sin, supply_outlet=sout,
                       demand_inlet=o.get("demand_side_inlet_node_name"),
                       demand_outlet=o.get("demand_side_outlet_node_name"), setpoint_node=sp_node)
        for c in _branch_components(model, sup_bl or ""):
            if c.type in CHILLER_TYPES:
                ch = find_object(model, c.type, c.name) or {}
                c.extra = {"condenser_inlet": ch.get("condenser_inlet_node_name"),
                           "condenser_outlet": ch.get("condenser_outlet_node_name")}
                pl.chillers.append(c)
            elif c.type in BOILER_TYPES:
                pl.boilers.append(c)
            elif c.type in TOWER_TYPES:
                pl.towers.append(c)
            elif c.type in PUMP_TYPES:
                pl.pumps.append(c)
            elif not c.type.startswith("Pipe:"):
                pl.other_supply.append(c)
        for c in _branch_components(model, dem_bl or ""):
            if not c.type.startswith("Pipe:"):
                pl.demand_components.append(c)
        if condenser:
            pl.kind = "condenser"
        elif pl.chillers:
            pl.kind = "chilled_water"
        elif pl.boilers:
            pl.kind = "hot_water"
        elif any(c.type.startswith("WaterHeater") for c in pl.other_supply):
            pl.kind = "service_hot_water"
        return pl

    for n, o in model.get("PlantLoop", {}).items():
        topo.plant_loops[n] = build_plant(n, o, condenser=False)
    for n, o in model.get("CondenserLoop", {}).items():
        topo.plant_loops[n] = build_plant(n, o, condenser=True)

    # ---- electric load centres (PV, inverter, storage) and water heaters ---------------------------
    for dname, d in model.get("ElectricLoadCenter:Distribution", {}).items():
        lc = LoadCenter(name=dname, buss_type=d.get("electrical_buss_type", "AlternatingCurrent"),
                        generator_scheme=d.get("generator_operation_scheme_type", "Baseload"),
                        storage_scheme=d.get("storage_operation_scheme", "TrackFacilityElectricDemandStoreExcessOnSite"),
                        min_soc=float(d.get("minimum_storage_state_of_charge_fraction", 0.0) or 0.0),
                        max_soc=float(d.get("maximum_storage_state_of_charge_fraction", 1.0) or 1.0))
        gl = find_object(model, "ElectricLoadCenter:Generators", d.get("generator_list_name", "") or "") or {}
        for g in gl.get("generator_outputs", []):
            gtype, gname = g.get("generator_object_type", ""), g.get("generator_name", "")
            go = find_object(model, gtype, gname) or {}
            lc.generators.append(Component(type=gtype, name=gname, extra={
                "rated_w": g.get("generator_rated_electric_power_output"),
                "dc_capacity_w": go.get("dc_system_capacity"),
                "availability_schedule": g.get("generator_availability_schedule_name")}))
        inv = d.get("inverter_name")
        if inv:
            itype = next((t for t in INVERTER_TYPES if find_object(model, t, inv) is not None), None)
            if itype:
                io = find_object(model, itype, inv) or {}
                eff = io.get("inverter_efficiency")
                lc.inverter = Component(type=itype, name=inv, extra={
                    "efficiency": eff if isinstance(eff, (int, float)) else 0.96,
                    "dc_to_ac_ratio": io.get("dc_to_ac_size_ratio")})
        sto = d.get("electrical_storage_object_name")
        if sto:
            stype = next((t for t in STORAGE_TYPES if find_object(model, t, sto) is not None), None)
            if stype:
                so = find_object(model, stype, sto) or {}
                lc.storage = Component(type=stype, name=sto, extra={
                    "capacity_j": so.get("maximum_storage_capacity"),
                    "max_charge_w": so.get("maximum_power_for_charging") or d.get("design_storage_control_charge_power"),
                    "max_discharge_w": so.get("maximum_power_for_discharging") or d.get("design_storage_control_discharge_power"),
                    "eff_charge": so.get("nominal_energetic_efficiency_for_charging"),
                    "eff_discharge": so.get("nominal_discharging_energetic_efficiency"),
                    "zone": so.get("zone_name")})
        topo.load_centers[dname] = lc

    for wtype in WATER_HEATER_TYPES:
        for wname, w in model.get(wtype, {}).items():
            sp = w.get("setpoint_temperature_schedule_name") or w.get("heater_1_setpoint_temperature_schedule_name")
            cap = w.get("heater_maximum_capacity", w.get("heater_1_capacity"))
            vol = w.get("tank_volume")
            topo.water_heaters[wname] = WaterHeater(
                name=wname, type=wtype, fuel=w.get("heater_fuel_type", "NaturalGas"), setpoint_schedule=sp,
                capacity_w=float(cap) if isinstance(cap, (int, float)) else None,
                volume_m3=float(vol) if isinstance(vol, (int, float)) else None,
                standalone=not w.get("use_side_inlet_node_name"))

    # ---- setpoint managers --------------------------------------------------------
    for t, objs in model.items():
        if not t.startswith("SetpointManager:"):
            continue
        for n, o in objs.items():
            node = o.get("setpoint_node_or_nodelist_name")
            topo.setpoint_managers.append({"type": t, "name": n, "nodes": node_list(model, node) if node else [],
                                           "schedule": o.get("schedule_name"), "control_variable": o.get("control_variable")})
    return topo


def _num(v: Any) -> float | None:
    return float(v) if isinstance(v, (int, float)) else None


def _zone_equipment(model: EpJSON, etype: str, ename: str, zone: str, seq: int) -> ZoneEquipment | None:
    """Describe one ZoneHVAC unit; returns None if the object is missing."""
    o = find_object(model, etype, ename)
    if o is None:
        return None
    kind = ZONE_EQUIP_KINDS[etype]
    ze = ZoneEquipment(name=ename, type=etype, kind=kind, zone=zone, sequence=seq,
                       availability_schedule=o.get("availability_schedule_name"),
                       inlet=o.get("air_inlet_node_name"), outlet=o.get("air_outlet_node_name"))

    def comp(t_key: str, n_key: str) -> Component | None:
        t, n = o.get(t_key), o.get(n_key)
        if not t or not n:
            return None
        co = find_object(model, t, n) or {}
        return Component(type=t, name=n, inlet=co.get("air_inlet_node_name") or co.get("inlet_node_name"),
                         outlet=co.get("air_outlet_node_name") or co.get("outlet_node_name"))

    if kind in ("heat_pump", "ptac"):
        ze.fan = comp("supply_air_fan_object_type", "supply_air_fan_name")
        ze.cooling_coil = comp("cooling_coil_object_type", "cooling_coil_name")
        ze.heating_coil = comp("heating_coil_object_type", "heating_coil_name")
        ze.supp_coil = comp("supplemental_heating_coil_object_type", "supplemental_heating_coil_name")
        oa = [v for v in (_num(o.get("cooling_outdoor_air_flow_rate")), _num(o.get("heating_outdoor_air_flow_rate")))
              if v is not None]
        ze.extra = {"cooling_flow_m3s": _num(o.get("cooling_supply_air_flow_rate")),
                    "heating_flow_m3s": _num(o.get("heating_supply_air_flow_rate")),
                    "oa_flow_m3s": max(oa or [0.0]),
                    "oa_mixer": o.get("outdoor_air_mixer_name"),
                    "fan_mode_schedule": o.get("supply_air_fan_operating_mode_schedule_name"),
                    "report": ZONE_EQUIP_REPORT.get(etype)}
    elif kind == "erv":
        hx_name = o.get("heat_exchanger_name") or ""
        hx_type = next((t for t in ("HeatExchanger:AirToAir:SensibleAndLatent", "HeatExchanger:AirToAir:FlatPlate",
                                    "HeatExchanger:Desiccant:BalancedFlow") if find_object(model, t, hx_name)), None)
        hx = (find_object(model, hx_type, hx_name) if hx_type else None) or {}
        sup_fan, exh_fan = o.get("supply_air_fan_name"), o.get("exhaust_air_fan_name")

        def fan_type(n):
            return next((t for t in FAN_TYPES if find_object(model, t, n or "")), "Fan:OnOff")
        sfo = find_object(model, fan_type(sup_fan), sup_fan or "") or {}
        efo = find_object(model, fan_type(exh_fan), exh_fan or "") or {}
        ze.fan = Component(type=fan_type(sup_fan), name=sup_fan, inlet=sfo.get("air_inlet_node_name"),
                           outlet=sfo.get("air_outlet_node_name")) if sup_fan else None
        ze.inlet = hx.get("supply_air_inlet_node_name")
        ze.outlet = sfo.get("air_outlet_node_name") or hx.get("supply_air_outlet_node_name")
        ze.extra = {"hx": hx_name or None, "hx_type": hx_type,
                    "hx_supply_inlet": hx.get("supply_air_inlet_node_name"),
                    "hx_supply_outlet": hx.get("supply_air_outlet_node_name"),
                    "hx_exhaust_inlet": hx.get("exhaust_air_inlet_node_name"),
                    "hx_exhaust_outlet": hx.get("exhaust_air_outlet_node_name"),
                    "hx_kind": hx.get("heat_exchanger_type", "Plate"),
                    "hx_temp_control": hx.get("supply_air_outlet_temperature_control", "No"),
                    "hx_availability_schedule": hx.get("availability_schedule_name"),
                    "eps_sens_heating": _num(hx.get("sensible_effectiveness_at_100_heating_air_flow")),
                    "eps_sens_cooling": _num(hx.get("sensible_effectiveness_at_100_cooling_air_flow")),
                    "supply_fan": sup_fan, "supply_fan_type": fan_type(sup_fan) if sup_fan else None,
                    "exhaust_fan": exh_fan, "exhaust_fan_type": fan_type(exh_fan) if exh_fan else None,
                    "exhaust_fan_outlet": efo.get("air_outlet_node_name"),
                    "supply_flow_m3s": _num(o.get("supply_air_flow_rate")),
                    "exhaust_flow_m3s": _num(o.get("exhaust_air_flow_rate")),
                    "controller": o.get("controller_name")}
    else:
        ze.extra = {"capacity_w": o.get("heating_design_capacity")}
    return ze
