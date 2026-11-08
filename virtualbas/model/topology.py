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
    infiltration: list[str] = field(default_factory=list)


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
        return t

    # convenience -------------------------------------------------------------
    def conditioned_zones(self) -> list[Zone]:
        return [z for z in self.zones.values() if z.thermostat]

    def loops_of_kind(self, kind: str) -> list[PlantLoop]:
        return [p for p in self.plant_loops.values() if p.kind == kind]


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
                          ("ZoneInfiltration:DesignFlowRate", "infiltration")]:
        for oname, o in model.get(objtype, {}).items():
            zk = zkey(o.get("zone_or_zonelist_or_space_or_spacelist_name", ""))
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

    # ---- setpoint managers --------------------------------------------------------
    for t, objs in model.items():
        if not t.startswith("SetpointManager:"):
            continue
        for n, o in objs.items():
            node = o.get("setpoint_node_or_nodelist_name")
            topo.setpoint_managers.append({"type": t, "name": n, "nodes": node_list(model, node) if node else [],
                                           "schedule": o.get("schedule_name"), "control_variable": o.get("control_variable")})
    return topo
