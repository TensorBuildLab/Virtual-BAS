"""Synthetic small all-electric building for the zone-equipment / DER tests.

Two identical, detached 4 m x 4 m x 3 m rooms (``ROOM_A`` and ``ROOM_B``) with a south window. Each room has a
packaged terminal heat pump (DX cooling / DX heating / electric supplemental heat); ``ROOM_A`` and ``ROOM_B`` also
have an energy-recovery ventilator. The site has a PVWatts array behind a PVWatts inverter with DC-coupled simple
storage, and a stand-alone electric water heater. Curves are the standard ones of the EnergyPlus example file
``PackagedTerminalHeatPump.idf``. Everything is hard-sized (no sizing objects needed).
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

W, D, H = 4.0, 4.0, 3.0


def _v(pts):
    return [{"vertex_x_coordinate": x, "vertex_y_coordinate": y, "vertex_z_coordinate": z} for x, y, z in pts]


def _box(m: dict, zone: str, x0: float) -> None:
    X = x0 + W
    walls = {
        "Floor": ("Floor", "Ground", [(x0, 0, 0), (x0, D, 0), (X, D, 0), (X, 0, 0)], "FLOOR"),
        "Roof": ("Roof", "Outdoors", [(x0, 0, H), (X, 0, H), (X, D, H), (x0, D, H)], "ROOF"),
        "South": ("Wall", "Outdoors", [(x0, 0, H), (x0, 0, 0), (X, 0, 0), (X, 0, H)], "WALL"),
        "East": ("Wall", "Outdoors", [(X, 0, H), (X, 0, 0), (X, D, 0), (X, D, H)], "WALL"),
        "North": ("Wall", "Outdoors", [(X, D, H), (X, D, 0), (x0, D, 0), (x0, D, H)], "WALL"),
        "West": ("Wall", "Outdoors", [(x0, D, H), (x0, D, 0), (x0, 0, 0), (x0, 0, H)], "WALL"),
    }
    for nm, (st, obc, pts, con) in walls.items():
        out = obc == "Outdoors"
        m["BuildingSurface:Detailed"][f"{zone}_{nm}"] = {
            "surface_type": st, "construction_name": con, "zone_name": zone, "outside_boundary_condition": obc,
            "sun_exposure": "SunExposed" if out else "NoSun", "wind_exposure": "WindExposed" if out else "NoWind",
            "number_of_vertices": 4, "vertices": _v(pts)}
    win = [(x0 + 1, 0, 2.2), (x0 + 1, 0, 0.9), (x0 + 3, 0, 0.9), (x0 + 3, 0, 2.2)]
    f = {"surface_type": "Window", "construction_name": "GLAZING", "building_surface_name": f"{zone}_South",
         "number_of_vertices": 4}
    for i, (x, y, z) in enumerate(win, start=1):
        f.update({f"vertex_{i}_x_coordinate": x, f"vertex_{i}_y_coordinate": y, f"vertex_{i}_z_coordinate": z})
    m["FenestrationSurface:Detailed"][f"{zone}_Window"] = f


def _pthp(m: dict, z: str) -> None:
    m["ZoneHVAC:PackagedTerminalHeatPump"][f"{z}_PTHP"] = {
        "availability_schedule_name": f"{z}_PTHP_Avail", "air_inlet_node_name": f"{z}_HP_In",
        "air_outlet_node_name": f"{z}_HP_Out", "cooling_supply_air_flow_rate": 0.15, "heating_supply_air_flow_rate": 0.15,
        "no_load_supply_air_flow_rate": 0.0, "cooling_outdoor_air_flow_rate": 0.0, "heating_outdoor_air_flow_rate": 0.0,
        "no_load_outdoor_air_flow_rate": 0.0, "supply_air_fan_object_type": "Fan:OnOff", "supply_air_fan_name": f"{z}_HP_Fan",
        "heating_coil_object_type": "Coil:Heating:DX:SingleSpeed", "heating_coil_name": f"{z}_HP_HtgCoil",
        "heating_convergence_tolerance": 0.001, "cooling_coil_object_type": "Coil:Cooling:DX:SingleSpeed",
        "cooling_coil_name": f"{z}_HP_ClgCoil", "cooling_convergence_tolerance": 0.001,
        "supplemental_heating_coil_object_type": "Coil:Heating:Electric", "supplemental_heating_coil_name": f"{z}_HP_SuppCoil",
        "maximum_supply_air_temperature_from_supplemental_heater": 50.0,
        "maximum_outdoor_dry_bulb_temperature_for_supplemental_heater_operation": 5.0,
        "fan_placement": "BlowThrough", "supply_air_fan_operating_mode_schedule_name": "Cycling"}
    m["Schedule:Constant"][f"{z}_PTHP_Avail"] = {"hourly_value": 1.0, "schedule_type_limits_name": "Fraction"}
    m["Fan:OnOff"][f"{z}_HP_Fan"] = {
        "availability_schedule_name": "AlwaysOn", "fan_total_efficiency": 0.5, "pressure_rise": 75.0,
        "maximum_flow_rate": 0.15, "motor_efficiency": 0.9, "motor_in_airstream_fraction": 1.0,
        "air_inlet_node_name": f"{z}_HP_In", "air_outlet_node_name": f"{z}_HP_FanOut"}
    m["Coil:Cooling:DX:SingleSpeed"][f"{z}_HP_ClgCoil"] = {
        "availability_schedule_name": "AlwaysOn", "gross_rated_total_cooling_capacity": 2500.0,
        "gross_rated_sensible_heat_ratio": 0.75, "gross_rated_cooling_cop": 3.5, "rated_air_flow_rate": 0.15,
        "air_inlet_node_name": f"{z}_HP_FanOut", "air_outlet_node_name": f"{z}_HP_ClgOut",
        "total_cooling_capacity_function_of_temperature_curve_name": "CoolCapFT",
        "total_cooling_capacity_function_of_flow_fraction_curve_name": "CoolCapFFF",
        "energy_input_ratio_function_of_temperature_curve_name": "CoolEIRFT",
        "energy_input_ratio_function_of_flow_fraction_curve_name": "CoolEIRFFF",
        "part_load_fraction_correlation_curve_name": "CoolPLF", "condenser_type": "AirCooled"}
    m["Coil:Heating:DX:SingleSpeed"][f"{z}_HP_HtgCoil"] = {
        "availability_schedule_name": "AlwaysOn", "gross_rated_heating_capacity": 2500.0, "gross_rated_heating_cop": 3.2,
        "rated_air_flow_rate": 0.15, "air_inlet_node_name": f"{z}_HP_ClgOut", "air_outlet_node_name": f"{z}_HP_HtgOut",
        "heating_capacity_function_of_temperature_curve_name": "HeatCapFT",
        "heating_capacity_function_of_flow_fraction_curve_name": "HeatCapFFF",
        "energy_input_ratio_function_of_temperature_curve_name": "HeatEIRFT",
        "energy_input_ratio_function_of_flow_fraction_curve_name": "HeatEIRFFF",
        "part_load_fraction_correlation_curve_name": "HeatPLF",
        "defrost_energy_input_ratio_function_of_temperature_curve_name": "DefrostEIRFT",
        "minimum_outdoor_dry_bulb_temperature_for_compressor_operation": -10.0,
        "maximum_outdoor_dry_bulb_temperature_for_defrost_operation": 5.0, "defrost_strategy": "ReverseCycle",
        "defrost_control": "Timed", "defrost_time_period_fraction": 0.058333}
    m["Coil:Heating:Electric"][f"{z}_HP_SuppCoil"] = {
        "availability_schedule_name": "AlwaysOn", "efficiency": 1.0, "nominal_capacity": 2000.0,
        "air_inlet_node_name": f"{z}_HP_HtgOut", "air_outlet_node_name": f"{z}_HP_Out"}


def _erv(m: dict, z: str) -> None:
    m["ZoneHVAC:EnergyRecoveryVentilator"][f"{z}_ERV"] = {
        "availability_schedule_name": "AlwaysOn", "heat_exchanger_name": f"{z}_ERV_HX", "supply_air_flow_rate": 0.025,
        "exhaust_air_flow_rate": 0.025, "supply_air_fan_name": f"{z}_ERV_SupFan", "exhaust_air_fan_name": f"{z}_ERV_ExhFan"}
    eps = {k: v for k, v in [("sensible_effectiveness_at_100_heating_air_flow", 0.75),
                             ("latent_effectiveness_at_100_heating_air_flow", 0.6),
                             ("sensible_effectiveness_at_75_heating_air_flow", 0.78),
                             ("latent_effectiveness_at_75_heating_air_flow", 0.63),
                             ("sensible_effectiveness_at_100_cooling_air_flow", 0.75),
                             ("latent_effectiveness_at_100_cooling_air_flow", 0.6),
                             ("sensible_effectiveness_at_75_cooling_air_flow", 0.78),
                             ("latent_effectiveness_at_75_cooling_air_flow", 0.63)]}
    m["HeatExchanger:AirToAir:SensibleAndLatent"][f"{z}_ERV_HX"] = {
        "availability_schedule_name": "AlwaysOn", "nominal_supply_air_flow_rate": 0.025, **eps,
        "supply_air_inlet_node_name": f"{z}_ERV_OA", "supply_air_outlet_node_name": f"{z}_ERV_HXSupOut",
        "exhaust_air_inlet_node_name": f"{z}_ERV_ExhIn", "exhaust_air_outlet_node_name": f"{z}_ERV_HXExhOut",
        "nominal_electric_power": 0.0, "supply_air_outlet_temperature_control": "No", "heat_exchanger_type": "Plate",
        "frost_control_type": "None", "economizer_lockout": "No"}
    for fan, i, o in [("SupFan", "HXSupOut", "SupOut"), ("ExhFan", "HXExhOut", "ExhOut")]:
        m["Fan:OnOff"][f"{z}_ERV_{fan}"] = {
            "availability_schedule_name": "AlwaysOn", "fan_total_efficiency": 0.35, "pressure_rise": 120.0,
            "maximum_flow_rate": 0.025, "motor_efficiency": 0.8, "motor_in_airstream_fraction": 1.0,
            "air_inlet_node_name": f"{z}_ERV_{i}", "air_outlet_node_name": f"{z}_ERV_{o}"}
    m["OutdoorAir:Node"][f"{z}_ERV_OA"] = {}


def build_model(with_erv_b: bool = True) -> dict[str, Any]:
    zones = ["ROOM_A", "ROOM_B"]
    m: dict[str, Any] = {k: {} for k in [
        "BuildingSurface:Detailed", "FenestrationSurface:Detailed", "Schedule:Constant", "Schedule:Compact",
        "ZoneHVAC:PackagedTerminalHeatPump", "Fan:OnOff", "Coil:Cooling:DX:SingleSpeed", "Coil:Heating:DX:SingleSpeed",
        "Coil:Heating:Electric", "ZoneHVAC:EnergyRecoveryVentilator", "HeatExchanger:AirToAir:SensibleAndLatent",
        "OutdoorAir:Node", "Zone", "People", "Lights", "ElectricEquipment", "ZoneInfiltration:DesignFlowRate",
        "ZoneControl:Thermostat", "ThermostatSetpoint:DualSetpoint", "ZoneHVAC:EquipmentConnections",
        "ZoneHVAC:EquipmentList", "NodeList"]}
    m["Version"] = {"Version 1": {"version_identifier": "23.2"}}
    m["SimulationControl"] = {"SimulationControl 1": {
        "do_zone_sizing_calculation": "No", "do_system_sizing_calculation": "No", "do_plant_sizing_calculation": "No",
        "run_simulation_for_sizing_periods": "No", "run_simulation_for_weather_file_run_periods": "Yes"}}
    m["Building"] = {"SmallTestBuilding": {"north_axis": 0.0, "terrain": "Suburbs", "solar_distribution": "FullExterior",
                                           "maximum_number_of_warmup_days": 25, "minimum_number_of_warmup_days": 6}}
    m["Timestep"] = {"Timestep 1": {"number_of_timesteps_per_hour": 12}}
    m["GlobalGeometryRules"] = {"GlobalGeometryRules 1": {"starting_vertex_position": "UpperLeftCorner",
                                                          "vertex_entry_direction": "Counterclockwise",
                                                          "coordinate_system": "Relative"}}
    m["RunPeriod"] = {"Annual": {"begin_month": 1, "begin_day_of_month": 1, "end_month": 12, "end_day_of_month": 31,
                                 "begin_year": 2023, "end_year": 2023}}
    m["Site:GroundTemperature:BuildingSurface"] = {"Site:GroundTemperature:BuildingSurface 1": {
        f"{mo}_ground_temperature": 18.0 for mo in ["january", "february", "march", "april", "may", "june", "july",
                                                    "august", "september", "october", "november", "december"]}}
    m["ScheduleTypeLimits"] = {"Fraction": {"lower_limit_value": 0.0, "upper_limit_value": 1.0, "numeric_type": "Continuous"},
                               "Any Number": {}, "Control Type": {"lower_limit_value": 0, "upper_limit_value": 4,
                                                                  "numeric_type": "Discrete"}}
    m["Schedule:Constant"].update({
        "AlwaysOn": {"hourly_value": 1.0, "schedule_type_limits_name": "Fraction"},
        "Cycling": {"hourly_value": 0.0, "schedule_type_limits_name": "Fraction"},
        "DualSP": {"hourly_value": 4, "schedule_type_limits_name": "Control Type"},
        "Activity": {"hourly_value": 120.0, "schedule_type_limits_name": "Any Number"},
        "DHW_SP": {"hourly_value": 50.0, "schedule_type_limits_name": "Any Number"},
        "ColdWater": {"hourly_value": 15.0, "schedule_type_limits_name": "Any Number"}})
    m["Schedule:Compact"].update({
        "Occ": {"schedule_type_limits_name": "Fraction", "data": [{"field": f} for f in [
            "Through: 12/31", "For: Weekdays", "Until: 08:00", 0.0, "Until: 18:00", 1.0, "Until: 24:00", 0.0,
            "For: AllOtherDays", "Until: 24:00", 0.0]]},
        "HtgSP": {"schedule_type_limits_name": "Any Number", "data": [{"field": f} for f in [
            "Through: 12/31", "For: AllDays", "Until: 07:00", 16.0, "Until: 19:00", 21.0, "Until: 24:00", 16.0]]},
        "ClgSP": {"schedule_type_limits_name": "Any Number", "data": [{"field": f} for f in [
            "Through: 12/31", "For: AllDays", "Until: 07:00", 29.0, "Until: 19:00", 24.0, "Until: 24:00", 29.0]]},
        "DHWUse": {"schedule_type_limits_name": "Fraction", "data": [{"field": f} for f in [
            "Through: 12/31", "For: AllDays", "Until: 08:00", 0.0, "Until: 09:00", 1.0, "Until: 12:00", 0.0,
            "Until: 13:00", 1.0, "Until: 24:00", 0.0]]}})
    m["Material"] = {
        "Wall Board": {"roughness": "Smooth", "thickness": 0.013, "conductivity": 0.16, "density": 800.0, "specific_heat": 1090.0},
        "Insulation": {"roughness": "MediumRough", "thickness": 0.1, "conductivity": 0.04, "density": 30.0, "specific_heat": 1200.0},
        "Concrete": {"roughness": "MediumRough", "thickness": 0.15, "conductivity": 1.4, "density": 2100.0, "specific_heat": 900.0}}
    m["WindowMaterial:SimpleGlazingSystem"] = {"Glass": {"u_factor": 1.8, "solar_heat_gain_coefficient": 0.35,
                                                        "visible_transmittance": 0.6}}
    m["Construction"] = {"WALL": {"outside_layer": "Wall Board", "layer_2": "Insulation", "layer_3": "Wall Board"},
                         "ROOF": {"outside_layer": "Insulation", "layer_2": "Wall Board"},
                         "FLOOR": {"outside_layer": "Concrete"}, "GLAZING": {"outside_layer": "Glass"}}
    for i, z in enumerate(zones):
        m["Zone"][z] = {"x_origin": 0.0, "y_origin": 0.0, "z_origin": 0.0, "multiplier": 1}
        _box(m, z, i * 10.0)
        m["People"][f"{z}_People"] = {"zone_or_zonelist_or_space_or_spacelist_name": z, "number_of_people_schedule_name": "Occ",
                                      "number_of_people_calculation_method": "People", "number_of_people": 2,
                                      "fraction_radiant": 0.3, "activity_level_schedule_name": "Activity"}
        m["Lights"][f"{z}_Lights"] = {"zone_or_zonelist_or_space_or_spacelist_name": z, "schedule_name": "Occ",
                                      "design_level_calculation_method": "LightingLevel", "lighting_level": 120.0}
        m["ElectricEquipment"][f"{z}_Plugs"] = {"zone_or_zonelist_or_space_or_spacelist_name": z, "schedule_name": "Occ",
                                               "design_level_calculation_method": "EquipmentLevel", "design_level": 300.0}
        m["ZoneInfiltration:DesignFlowRate"][f"{z}_Infil"] = {
            "zone_or_zonelist_or_space_or_spacelist_name": z, "schedule_name": "AlwaysOn",
            "design_flow_rate_calculation_method": "AirChanges/Hour", "air_changes_per_hour": 0.2}
        m["ThermostatSetpoint:DualSetpoint"][f"{z}_DualSP"] = {"heating_setpoint_temperature_schedule_name": "HtgSP",
                                                              "cooling_setpoint_temperature_schedule_name": "ClgSP"}
        m["ZoneControl:Thermostat"][f"{z}_Thermostat"] = {"zone_or_zonelist_name": z, "control_type_schedule_name": "DualSP",
                                                          "control_1_object_type": "ThermostatSetpoint:DualSetpoint",
                                                          "control_1_name": f"{z}_DualSP"}
        _pthp(m, z)
        erv = with_erv_b or z == "ROOM_A"
        eq = []
        if erv:
            _erv(m, z)
            eq.append({"zone_equipment_object_type": "ZoneHVAC:EnergyRecoveryVentilator", "zone_equipment_name": f"{z}_ERV",
                       "zone_equipment_cooling_sequence": 1, "zone_equipment_heating_or_no_load_sequence": 1})
        eq.append({"zone_equipment_object_type": "ZoneHVAC:PackagedTerminalHeatPump", "zone_equipment_name": f"{z}_PTHP",
                   "zone_equipment_cooling_sequence": len(eq) + 1, "zone_equipment_heating_or_no_load_sequence": len(eq) + 1})
        m["ZoneHVAC:EquipmentList"][f"{z}_EqList"] = {"load_distribution_scheme": "SequentialLoad", "equipment": eq}
        m["NodeList"][f"{z}_Inlets"] = {"nodes": [{"node_name": f"{z}_HP_Out"}] + ([{"node_name": f"{z}_ERV_SupOut"}] if erv else [])}
        m["NodeList"][f"{z}_Exhausts"] = {"nodes": [{"node_name": f"{z}_HP_In"}] + ([{"node_name": f"{z}_ERV_ExhIn"}] if erv else [])}
        m["ZoneHVAC:EquipmentConnections"][f"{z}_Conn"] = {
            "zone_name": z, "zone_conditioning_equipment_list_name": f"{z}_EqList", "zone_air_node_name": f"{z}_AirNode",
            "zone_return_air_node_or_nodelist_name": f"{z}_Return", "zone_air_inlet_node_or_nodelist_name": f"{z}_Inlets",
            "zone_air_exhaust_node_or_nodelist_name": f"{z}_Exhausts"}
    m["Curve:Biquadratic"] = {
        "CoolCapFT": {"coefficient1_constant": 0.942587793, "coefficient2_x": 0.009543347, "coefficient3_x_2": 0.000683770,
                      "coefficient4_y": -0.011042676, "coefficient5_y_2": 0.000005249, "coefficient6_x_y": -0.000009720,
                      "minimum_value_of_x": 12.77778, "maximum_value_of_x": 23.88889, "minimum_value_of_y": 18.0,
                      "maximum_value_of_y": 46.11111},
        "CoolEIRFT": {"coefficient1_constant": 0.342414409, "coefficient2_x": 0.034885008, "coefficient3_x_2": -0.000623700,
                      "coefficient4_y": 0.004977216, "coefficient5_y_2": 0.000437951, "coefficient6_x_y": -0.000728028,
                      "minimum_value_of_x": 12.77778, "maximum_value_of_x": 23.88889, "minimum_value_of_y": 18.0,
                      "maximum_value_of_y": 46.11111},
        "DefrostEIRFT": {"coefficient1_constant": 1.0, "coefficient2_x": 0.0, "coefficient3_x_2": 0.0, "coefficient4_y": 0.0,
                         "coefficient5_y_2": 0.0, "coefficient6_x_y": 0.0, "minimum_value_of_x": -100.0,
                         "maximum_value_of_x": 100.0, "minimum_value_of_y": -100.0, "maximum_value_of_y": 100.0}}
    m["Curve:Cubic"] = {
        "HeatCapFT": {"coefficient1_constant": 0.758746, "coefficient2_x": 0.027626, "coefficient3_x_2": 0.000148716,
                      "coefficient4_x_3": 0.0000034992, "minimum_value_of_x": -20.0, "maximum_value_of_x": 20.0},
        "HeatEIRFT": {"coefficient1_constant": 1.19248, "coefficient2_x": -0.0300438, "coefficient3_x_2": 0.00103745,
                      "coefficient4_x_3": -0.000023328, "minimum_value_of_x": -20.0, "maximum_value_of_x": 20.0},
        "HeatCapFFF": {"coefficient1_constant": 0.84, "coefficient2_x": 0.16, "coefficient3_x_2": 0.0, "coefficient4_x_3": 0.0,
                       "minimum_value_of_x": 0.5, "maximum_value_of_x": 1.5}}
    m["Curve:Quadratic"] = {
        "CoolCapFFF": {"coefficient1_constant": 0.8, "coefficient2_x": 0.2, "coefficient3_x_2": 0.0,
                       "minimum_value_of_x": 0.5, "maximum_value_of_x": 1.5},
        "CoolEIRFFF": {"coefficient1_constant": 1.1552, "coefficient2_x": -0.1808, "coefficient3_x_2": 0.0256,
                       "minimum_value_of_x": 0.5, "maximum_value_of_x": 1.5},
        "CoolPLF": {"coefficient1_constant": 0.85, "coefficient2_x": 0.15, "coefficient3_x_2": 0.0,
                    "minimum_value_of_x": 0.0, "maximum_value_of_x": 1.0},
        "HeatEIRFFF": {"coefficient1_constant": 1.3824, "coefficient2_x": -0.4336, "coefficient3_x_2": 0.0512,
                       "minimum_value_of_x": 0.0, "maximum_value_of_x": 1.0},
        "HeatPLF": {"coefficient1_constant": 0.75, "coefficient2_x": 0.25, "coefficient3_x_2": 0.0,
                    "minimum_value_of_x": 0.0, "maximum_value_of_x": 1.0}}
    # ---- PV + inverter + DC-coupled storage; a small battery so that outages can deplete it
    m["Generator:PVWatts"] = {"PV_Array": {"pvwatts_version": "5", "dc_system_capacity": 3000.0, "module_type": "Standard",
                                           "array_type": "FixedOpenRack", "system_losses": 0.14,
                                           "array_geometry_type": "TiltAzimuth", "tilt_angle": 25.0, "azimuth_angle": 180.0}}
    m["ElectricLoadCenter:Generators"] = {"PV_List": {"generator_outputs": [{
        "generator_name": "PV_Array", "generator_object_type": "Generator:PVWatts",
        "generator_rated_electric_power_output": 3000.0, "generator_availability_schedule_name": "AlwaysOn"}]}}
    m["ElectricLoadCenter:Inverter:PVWatts"] = {"PV_Inverter": {"dc_to_ac_size_ratio": 1.1, "inverter_efficiency": 0.96}}
    m["ElectricLoadCenter:Storage:Simple"] = {"Battery": {
        "availability_schedule_name": "AlwaysOn", "radiative_fraction_for_zone_heat_gains": 0.0,
        "nominal_energetic_efficiency_for_charging": 0.95, "nominal_discharging_energetic_efficiency": 0.95,
        "maximum_storage_capacity": 1.8e7, "maximum_power_for_discharging": 3000.0, "maximum_power_for_charging": 2000.0,
        "initial_state_of_charge": 9.0e6}}
    m["ElectricLoadCenter:Distribution"] = {"Site_Power": {
        "generator_list_name": "PV_List", "generator_operation_scheme_type": "Baseload", "inverter_name": "PV_Inverter",
        "electrical_buss_type": "DirectCurrentWithInverterDCStorage", "electrical_storage_object_name": "Battery",
        "minimum_storage_state_of_charge_fraction": 0.2, "maximum_storage_state_of_charge_fraction": 1.0,
        "storage_operation_scheme": "TrackFacilityElectricDemandStoreExcessOnSite"}}
    m["WaterHeater:Mixed"] = {"DHW_Heater": {
        "tank_volume": 0.15, "setpoint_temperature_schedule_name": "DHW_SP", "deadband_temperature_difference": 3.0,
        "maximum_temperature_limit": 80.0, "heater_control_type": "Cycle", "heater_maximum_capacity": 2000.0,
        "heater_fuel_type": "Electricity", "heater_thermal_efficiency": 1.0, "ambient_temperature_indicator": "Zone",
        "ambient_temperature_zone_name": "ROOM_B", "off_cycle_loss_coefficient_to_ambient_temperature": 1.0,
        "on_cycle_loss_coefficient_to_ambient_temperature": 1.0, "peak_use_flow_rate": 2e-6,
        "use_flow_rate_fraction_schedule_name": "DHWUse", "cold_water_supply_temperature_schedule_name": "ColdWater"}}
    return m


def write_model(path: str | Path, **kw) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build_model(**kw), indent=1))
    return path


def unknown_fields(model: dict[str, Any], schema: dict[str, Any], types: list[str] | None = None) -> list[str]:
    """Fields that are not in the EnergyPlus schema (EnergyPlus silently ignores them)."""
    bad = []
    for t, objs in model.items():
        if types is not None and t not in types:
            continue
        props = schema["properties"].get(t)
        if props is None:
            bad.append(f"type {t}")
            continue
        pat = next(iter(props.get("patternProperties", {}).values()), {"properties": {}})
        fields = pat.get("properties", {})
        for n, o in objs.items():
            for k, v in o.items():
                if k not in fields:
                    bad.append(f"{t}/{n}/{k}")
                elif isinstance(v, list) and fields[k].get("type") == "array":
                    item = fields[k].get("items", {}).get("properties", {})
                    for it in v:
                        bad += [f"{t}/{n}/{k}/{kk}" for kk in it if kk not in item]
    return bad


def copy_model(m):
    return copy.deepcopy(m)
