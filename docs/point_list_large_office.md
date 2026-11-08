# BAS point list - DOE large office

1207 points on 54 pieces of equipment (generated automatically from the EnergyPlus model): 508 standard, 295 next_gen, 244 advanced, 160 truth.

Tier: **standard** = found in typical commercial BAS today, **advanced** = well-instrumented BAS, **next_gen** = rarely installed today but valuable for analytics/AI, **truth** = ground truth only. Source: energyplus (inner-space physics), model (outer-space physical model), surrogate (engineering correlation), bas (calculated by the BAS). See [point_taxonomy.md](point_taxonomy.md).

## WX - WeatherStation

Rooftop weather station, outdoor air-quality monitor and weather-forecast feed

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `WX/OA-T` | sensor | standard | energyplus | degC | outdoor_temperature | Outdoor air dry-bulb temperature | Outside_Air_Temperature_Sensor |
| `WX/OA-RH` | sensor | standard | energyplus | %RH | humidity | Outdoor air relative humidity | Outside_Air_Humidity_Sensor |
| `WX/OA-WB` | sensor | advanced | energyplus | degC | outdoor_temperature | Outdoor air wet-bulb temperature (calculated by station) | Outside_Air_Wet_Bulb_Temperature_Sensor |
| `WX/OA-DP` | sensor | advanced | energyplus | degC | outdoor_temperature | Outdoor air dew-point temperature | Outside_Air_Dewpoint_Sensor |
| `WX/OA-H` | sensor | advanced | energyplus | kJ/kg | enthalpy | Outdoor air specific enthalpy (calculated by station) | Outside_Air_Enthalpy_Sensor |
| `WX/OA-W` | sensor | advanced | energyplus | g/kg | humidity_ratio | Outdoor air humidity ratio | Humidity_Sensor |
| `WX/BARO` | sensor | advanced | energyplus | kPa | barometric | Barometric pressure | Air_Pressure_Sensor |
| `WX/WIND` | sensor | advanced | energyplus | m/s | speed | Wind speed | Wind_Speed_Sensor |
| `WX/WIND-DIR` | sensor | advanced | energyplus | deg | wind_direction | Wind direction (0 = north, clockwise) | Wind_Direction_Sensor |
| `WX/SOLAR` | sensor | advanced | energyplus | W/m2 | solar | Global horizontal irradiance (pyranometer) | Solar_Radiance_Sensor |
| `WX/DNI` | sensor | next_gen | energyplus | W/m2 | solar | Direct normal irradiance (pyrheliometer) | Solar_Radiance_Sensor |
| `WX/DHI` | sensor | next_gen | energyplus | W/m2 | solar | Diffuse horizontal irradiance (shaded pyranometer) | Solar_Radiance_Sensor |
| `WX/OA-LUX` | sensor | advanced | energyplus | lux | illuminance | Exterior horizontal illuminance (roof photocell) | Outside_Illuminance_Sensor |
| `WX/SKY-COVER` | sensor | next_gen | energyplus | tenths | ideal | Total sky cover (sky imager) |  |
| `WX/SKY-T` | sensor | next_gen | energyplus | degC | outdoor_temperature | Sky temperature (pyrgeometer) | Temperature_Sensor |
| `WX/RAIN` | sensor | advanced | energyplus | - | binary | Rain sensor | Rain_Sensor |
| `WX/PRECIP` | sensor | next_gen | energyplus | mm/h | ideal | Precipitation rate (tipping bucket) | Precipitation_Sensor |
| `WX/OA-PM25` | sensor | next_gen | model | ug/m3 | pm_sensor | Outdoor PM2.5 (air-quality monitor / public AQ feed) | PM2.5_Sensor |
| `WX/OA-PM10` | sensor | next_gen | model | ug/m3 | pm_sensor | Outdoor PM10 (air-quality monitor / public AQ feed) | PM10_Sensor |
| `WX/OA-T-FC1H` | sensor | next_gen | model | degC | ideal | Forecast outdoor dry-bulb temperature, 1 h ahead (weather service) |  |
| `WX/GHI-FC1H` | sensor | next_gen | model | W/m2 | ideal | Forecast global horizontal irradiance, 1 h ahead (weather service) |  |
| `WX/OA-T-FC6H` | sensor | next_gen | model | degC | ideal | Forecast outdoor dry-bulb temperature, 6 h ahead (weather service) |  |
| `WX/GHI-FC6H` | sensor | next_gen | model | W/m2 | ideal | Forecast global horizontal irradiance, 6 h ahead (weather service) |  |
| `WX/OA-T-FC24H` | sensor | next_gen | model | degC | ideal | Forecast outdoor dry-bulb temperature, 24 h ahead (weather service) |  |
| `WX/GHI-FC24H` | sensor | next_gen | model | W/m2 | ideal | Forecast global horizontal irradiance, 24 h ahead (weather service) |  |
| `WX/HDD-TODAY` | virtual | standard | bas | K.d |  | Heating degree-days today (base 18 C) |  |
| `WX/CDD-TODAY` | virtual | standard | bas | K.d |  | Cooling degree-days today (base 18 C) |  |

## MTR - Meter

Utility meters and end-use sub-meters

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `MTR/BLDG-ELEC-KW` | meter | standard | energyplus | kW | energy | Whole-building electric demand | Electric_Power_Sensor |
| `MTR/BLDG-GAS-KW` | meter | standard | energyplus | kW | energy | Whole-building natural gas rate | Natural_Gas_Usage_Sensor |
| `MTR/HVAC-ELEC-KW` | meter | advanced | energyplus | kW | energy | HVAC electric demand | Electric_Power_Sensor |
| `MTR/LIGHT-KW` | meter | advanced | energyplus | kW | energy | Interior lighting demand | Electric_Power_Sensor |
| `MTR/PLUG-KW` | meter | next_gen | energyplus | kW | energy | Plug and process load demand | Electric_Power_Sensor |
| `MTR/CLG-ELEC-KW` | meter | advanced | energyplus | kW | energy | Cooling (chiller) electric demand | Electric_Power_Sensor |
| `MTR/FAN-ELEC-KW` | meter | advanced | energyplus | kW | energy | Fan electric demand | Electric_Power_Sensor |
| `MTR/PUMP-ELEC-KW` | meter | advanced | energyplus | kW | energy | Pump electric demand | Electric_Power_Sensor |
| `MTR/HREJ-ELEC-KW` | meter | advanced | energyplus | kW | energy | Heat rejection electric demand | Electric_Power_Sensor |
| `MTR/HTG-GAS-KW` | meter | advanced | energyplus | kW | energy | Heating natural gas rate | Natural_Gas_Usage_Sensor |
| `MTR/EXT-LIGHT-KW` | meter | advanced | energyplus | kW | energy | Exterior (facade) lighting demand | Electric_Power_Sensor |
| `MTR/ELEV-KW` | meter | next_gen | energyplus | kW | energy | Elevators electric demand | Electric_Power_Sensor |
| `MTR/DHW-GAS-KW` | meter | advanced | energyplus | kW | energy | Domestic hot water heater gas rate | Natural_Gas_Usage_Sensor |
| `MTR/WATER-F` | meter | standard | energyplus | L/s | energy | Building water flow (domestic + cooling-tower make-up) | Water_Usage_Sensor |
| `MTR/TOWER-WATER-F` | meter | advanced | energyplus | L/s | energy | Cooling-tower make-up water sub-meter | Water_Usage_Sensor |
| `MTR/BLDG-ELEC-KWH` | meter | standard | model | kWh | energy | Electricity totaliser (since start of run) | Electric_Energy_Sensor |
| `MTR/BLDG-GAS-KWH` | meter | standard | model | kWh | energy | Natural-gas totaliser (since start of run) | Natural_Gas_Usage_Sensor |
| `MTR/WATER-M3` | meter | standard | model | m3 | energy | Water totaliser (since start of run) | Water_Usage_Sensor |
| `MTR/BLDG-DMD-15` | virtual | standard | bas | kW |  | Electric demand, 15-minute rolling average |  |
| `MTR/PEAK-DMD-DAY` | virtual | standard | bas | kW |  | Peak 15-minute demand today |  |
| `MTR/PEAK-DMD-MONTH` | virtual | standard | bas | kW |  | Peak 15-minute demand this month (billing demand) |  |

## GRID - Grid

Utility tariff, grid carbon intensity and demand-response signals (OpenADR-style feed)

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `GRID/PRICE` | sensor | next_gen | model | $/kWh | ideal | Electricity price (time-of-use tariff) |  |
| `GRID/TOU-PERIOD` | sensor | next_gen | model | - | ideal | Tariff period (0 off-peak, 1 mid-peak, 2 on-peak) |  |
| `GRID/CO2-INT` | sensor | next_gen | model | kgCO2/kWh | ideal | Marginal grid carbon intensity |  |
| `GRID/DR-EVENT` | sensor | next_gen | model | - | ideal | Demand-response event active |  |
| `GRID/DR-SHED-KW` | sensor | next_gen | model | kW | ideal | Requested demand-response load shed |  |
| `GRID/COST-TODAY` | sensor | next_gen | model | $ | ideal | Energy cost today (electricity + gas) |  |
| `GRID/CO2-TODAY` | sensor | next_gen | model | kgCO2 | ideal | Operational carbon emissions today |  |

## BLDG - Building

Building-level calculated values

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `BLDG/OCC-COUNT` | virtual | next_gen | bas | people |  | Building occupancy (sum of zone people counters) | Occupancy_Count_Sensor |

## ZN-Basement - Zone

Thermal zone Basement

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `ZN-Basement/ZN-T` | sensor | standard | energyplus | degC | zone_temperature | Zone air temperature | Zone_Air_Temperature_Sensor |
| `ZN-Basement/ZN-RH` | sensor | advanced | energyplus | %RH | humidity | Zone air relative humidity | Zone_Air_Humidity_Sensor |
| `ZN-Basement/ZN-DP` | sensor | advanced | energyplus | degC | air_temperature | Zone air dew-point temperature (calculated by T/RH transmitter) | Dewpoint_Sensor |
| `ZN-Basement/ZN-CO2` | sensor | standard | energyplus | ppm | co2 | Zone CO2 concentration (NDIR) | CO2_Sensor |
| `ZN-Basement/ZN-OCC` | sensor | standard | energyplus | - | occupancy | Zone occupancy sensor (PIR) | Occupancy_Sensor |
| `ZN-Basement/OCCUPANTS` | truth | truth | energyplus | people |  | True number of occupants (ground truth only) | Occupancy_Count_Sensor |
| `ZN-Basement/OCC-COUNT` | sensor | next_gen | model | people | people_count | People counter (camera / thermopile) | Occupancy_Count_Sensor |
| `ZN-Basement/WIN-STS` | sensor | advanced | model | - | binary | Window / door contact (1 = open) | Open_Close_Status |
| `ZN-Basement/ZN-MRT` | sensor | next_gen | energyplus | degC | radiant_temperature | Mean radiant temperature (globe thermometer) | Radiant_Temperature_Sensor |
| `ZN-Basement/ZN-OPT` | sensor | next_gen | energyplus | degC | zone_temperature | Operative temperature (comfort station) | Operative_Temperature |
| `ZN-Basement/PMV` | sensor | next_gen | energyplus | - | comfort_index | Predicted mean vote, ISO 7730 (comfort station) |  |
| `ZN-Basement/PPD` | sensor | next_gen | energyplus | % | comfort_ppd | Predicted percentage dissatisfied, ISO 7730 (comfort station) |  |
| `ZN-Basement/TS-VOTE` | sensor | next_gen | model | - | ideal | Mean thermal-sensation vote of occupants, last hour (feedback app, -3..+3) |  |
| `ZN-Basement/HOT-CALLS` | sensor | next_gen | model | count | ideal | Too-hot complaints today (work orders / app) |  |
| `ZN-Basement/COLD-CALLS` | sensor | next_gen | model | count | ideal | Too-cold complaints today (work orders / app) |  |
| `ZN-Basement/ZN-PM25` | sensor | next_gen | model | ug/m3 | pm_sensor | Zone PM2.5 (optical particle sensor) | PM2.5_Sensor |
| `ZN-Basement/ZN-PM10` | sensor | next_gen | model | ug/m3 | pm_sensor | Zone PM10 (optical particle sensor) | PM10_Sensor |
| `ZN-Basement/ZN-TVOC` | sensor | next_gen | model | ug/m3 | tvoc_sensor | Zone total VOC (metal-oxide sensor) | TVOC_Sensor |
| `ZN-Basement/ZN-LUX` | sensor | advanced | model | lux | illuminance | Work-plane illuminance (daylight-harvesting photosensor) | Illuminance_Sensor |
| `ZN-Basement/DAYLIGHT-LUX` | truth | truth | model | lux |  | Daylight share of the work-plane illuminance (ground truth only) |  |
| `ZN-Basement/LIGHT-LVL` | sensor | advanced | model | % | percent | Lighting level (networked lighting controls) |  |
| `ZN-Basement/ZN-DBA` | sensor | next_gen | model | dBA | sound | Background sound level (class-2 sound level meter) |  |
| `ZN-Basement/LIGHT-KW` | meter | advanced | energyplus | kW | power | Zone lighting power (lighting panel sub-meter) | Electric_Power_Sensor |
| `ZN-Basement/PLUG-KW` | meter | next_gen | energyplus | kW | power | Zone plug load power (circuit-level sub-meter) | Electric_Power_Sensor |
| `ZN-Basement/WIN-SOL-KW` | truth | truth | energyplus | kW |  | Transmitted solar gain (ground truth only) |  |
| `ZN-Basement/WIN-Q-KW` | truth | truth | energyplus | kW |  | Window heat gain (ground truth only) |  |
| `ZN-Basement/INT-GAIN-KW` | truth | truth | energyplus | kW |  | Total internal heat gain (ground truth only) |  |
| `ZN-Basement/SYS-CLG-KW` | truth | truth | energyplus | kW |  | Sensible cooling delivered to the zone (ground truth only) |  |
| `ZN-Basement/SYS-HTG-KW` | truth | truth | energyplus | kW |  | Sensible heating delivered to the zone (ground truth only) |  |
| `ZN-Basement/HTG-SP` | setpoint | standard | bas | degC |  | Active heating set point | Zone_Air_Heating_Temperature_Setpoint |
| `ZN-Basement/CLG-SP` | setpoint | standard | bas | degC |  | Active cooling set point | Zone_Air_Cooling_Temperature_Setpoint |
| `ZN-Basement/OCC-HTG-SP` | setpoint | standard | bas | degC |  | Occupied heating set point | Occupied_Air_Temperature_Heating_Setpoint |
| `ZN-Basement/OCC-CLG-SP` | setpoint | standard | bas | degC |  | Occupied cooling set point | Occupied_Air_Temperature_Cooling_Setpoint |
| `ZN-Basement/OCC-MODE` | status | standard | bas | - |  | Zone occupancy mode (1 occupied / 0 unoccupied) | Occupancy_Status |
| `ZN-Basement/ZN-T-ADJ` | setpoint | standard | bas | K |  | Occupant set-point adjustment (wall sensor slider, +/-) | Temperature_Adjust_Sensor |

## VAV-Basement - VAV

VAV terminal with hot-water reheat serving Basement

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `VAV-Basement/DA-F` | sensor | standard | energyplus | m3/s | air_flow | Discharge air flow | Discharge_Air_Flow_Sensor |
| `VAV-Basement/DA-T` | sensor | standard | energyplus | degC | air_temperature | Discharge air temperature | Discharge_Air_Temperature_Sensor |
| `VAV-Basement/DMPR-POS` | sensor | advanced | energyplus | % | position | Damper position feedback | Damper_Position_Sensor |
| `VAV-Basement/DA-VP` | sensor | advanced | surrogate | Pa | pressure | Flow-cross velocity pressure (airflow transducer) | Velocity_Pressure_Sensor |
| `VAV-Basement/RHV-POS` | sensor | advanced | energyplus | % | position | Reheat valve position (feedback) | Valve_Position_Sensor |
| `VAV-Basement/RH-Q` | truth | truth | energyplus | kW |  | Reheat coil heat rate (ground truth) |  |
| `VAV-Basement/RH-BTU` | sensor | next_gen | energyplus | kW | thermal_power | Reheat coil BTU meter (water-side heat rate) | Thermal_Power_Sensor |
| `VAV-Basement/RH-WF` | sensor | next_gen | energyplus | L/s | water_flow | Reheat coil water flow | Water_Flow_Sensor |
| `VAV-Basement/ZN-MODE` | status | standard | bas | - |  | Terminal control state (0 deadband, 1 cooling, 2 heating) | Mode_Status |
| `VAV-Basement/CLG-REQ` | virtual | standard | bas | count |  | Cooling SAT-reset requests (G36) |  |
| `VAV-Basement/PRS-REQ` | virtual | standard | bas | count |  | Static-pressure reset requests (G36) |  |
| `VAV-Basement/HW-REQ` | virtual | standard | bas | count |  | Hot-water reset requests (G36) |  |
| `VAV-Basement/LOW-FLOW-ALM` | status | standard | bas | - |  | Low airflow alarm (G36: flow < 70 % of set point for 5 min) | Low_Air_Flow_Alarm |
| `VAV-Basement/DA-F-SP` | setpoint | standard | bas | m3/s |  | Discharge air flow set point | Discharge_Air_Flow_Setpoint |
| `VAV-Basement/DMPR-CMD` | command | standard | bas | % |  | Damper command | Damper_Position_Command |
| `VAV-Basement/CLG-LOOP` | virtual | standard | bas | % |  | Cooling loop output |  |
| `VAV-Basement/HTG-LOOP` | virtual | standard | bas | % |  | Heating loop output |  |

## ZN-Core_bottom - Zone

Thermal zone Core_bottom

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `ZN-Core_bottom/ZN-T` | sensor | standard | energyplus | degC | zone_temperature | Zone air temperature | Zone_Air_Temperature_Sensor |
| `ZN-Core_bottom/ZN-RH` | sensor | advanced | energyplus | %RH | humidity | Zone air relative humidity | Zone_Air_Humidity_Sensor |
| `ZN-Core_bottom/ZN-DP` | sensor | advanced | energyplus | degC | air_temperature | Zone air dew-point temperature (calculated by T/RH transmitter) | Dewpoint_Sensor |
| `ZN-Core_bottom/ZN-CO2` | sensor | standard | energyplus | ppm | co2 | Zone CO2 concentration (NDIR) | CO2_Sensor |
| `ZN-Core_bottom/ZN-OCC` | sensor | standard | energyplus | - | occupancy | Zone occupancy sensor (PIR) | Occupancy_Sensor |
| `ZN-Core_bottom/OCCUPANTS` | truth | truth | energyplus | people |  | True number of occupants (ground truth only) | Occupancy_Count_Sensor |
| `ZN-Core_bottom/OCC-COUNT` | sensor | next_gen | model | people | people_count | People counter (camera / thermopile) | Occupancy_Count_Sensor |
| `ZN-Core_bottom/WIN-STS` | sensor | advanced | model | - | binary | Window / door contact (1 = open) | Open_Close_Status |
| `ZN-Core_bottom/ZN-MRT` | sensor | next_gen | energyplus | degC | radiant_temperature | Mean radiant temperature (globe thermometer) | Radiant_Temperature_Sensor |
| `ZN-Core_bottom/ZN-OPT` | sensor | next_gen | energyplus | degC | zone_temperature | Operative temperature (comfort station) | Operative_Temperature |
| `ZN-Core_bottom/PMV` | sensor | next_gen | energyplus | - | comfort_index | Predicted mean vote, ISO 7730 (comfort station) |  |
| `ZN-Core_bottom/PPD` | sensor | next_gen | energyplus | % | comfort_ppd | Predicted percentage dissatisfied, ISO 7730 (comfort station) |  |
| `ZN-Core_bottom/TS-VOTE` | sensor | next_gen | model | - | ideal | Mean thermal-sensation vote of occupants, last hour (feedback app, -3..+3) |  |
| `ZN-Core_bottom/HOT-CALLS` | sensor | next_gen | model | count | ideal | Too-hot complaints today (work orders / app) |  |
| `ZN-Core_bottom/COLD-CALLS` | sensor | next_gen | model | count | ideal | Too-cold complaints today (work orders / app) |  |
| `ZN-Core_bottom/ZN-PM25` | sensor | next_gen | model | ug/m3 | pm_sensor | Zone PM2.5 (optical particle sensor) | PM2.5_Sensor |
| `ZN-Core_bottom/ZN-PM10` | sensor | next_gen | model | ug/m3 | pm_sensor | Zone PM10 (optical particle sensor) | PM10_Sensor |
| `ZN-Core_bottom/ZN-TVOC` | sensor | next_gen | model | ug/m3 | tvoc_sensor | Zone total VOC (metal-oxide sensor) | TVOC_Sensor |
| `ZN-Core_bottom/ZN-LUX` | sensor | advanced | model | lux | illuminance | Work-plane illuminance (daylight-harvesting photosensor) | Illuminance_Sensor |
| `ZN-Core_bottom/DAYLIGHT-LUX` | truth | truth | model | lux |  | Daylight share of the work-plane illuminance (ground truth only) |  |
| `ZN-Core_bottom/LIGHT-LVL` | sensor | advanced | model | % | percent | Lighting level (networked lighting controls) |  |
| `ZN-Core_bottom/ZN-DBA` | sensor | next_gen | model | dBA | sound | Background sound level (class-2 sound level meter) |  |
| `ZN-Core_bottom/LIGHT-KW` | meter | advanced | energyplus | kW | power | Zone lighting power (lighting panel sub-meter) | Electric_Power_Sensor |
| `ZN-Core_bottom/PLUG-KW` | meter | next_gen | energyplus | kW | power | Zone plug load power (circuit-level sub-meter) | Electric_Power_Sensor |
| `ZN-Core_bottom/WIN-SOL-KW` | truth | truth | energyplus | kW |  | Transmitted solar gain (ground truth only) |  |
| `ZN-Core_bottom/WIN-Q-KW` | truth | truth | energyplus | kW |  | Window heat gain (ground truth only) |  |
| `ZN-Core_bottom/INT-GAIN-KW` | truth | truth | energyplus | kW |  | Total internal heat gain (ground truth only) |  |
| `ZN-Core_bottom/SYS-CLG-KW` | truth | truth | energyplus | kW |  | Sensible cooling delivered to the zone (ground truth only) |  |
| `ZN-Core_bottom/SYS-HTG-KW` | truth | truth | energyplus | kW |  | Sensible heating delivered to the zone (ground truth only) |  |
| `ZN-Core_bottom/HTG-SP` | setpoint | standard | bas | degC |  | Active heating set point | Zone_Air_Heating_Temperature_Setpoint |
| `ZN-Core_bottom/CLG-SP` | setpoint | standard | bas | degC |  | Active cooling set point | Zone_Air_Cooling_Temperature_Setpoint |
| `ZN-Core_bottom/OCC-HTG-SP` | setpoint | standard | bas | degC |  | Occupied heating set point | Occupied_Air_Temperature_Heating_Setpoint |
| `ZN-Core_bottom/OCC-CLG-SP` | setpoint | standard | bas | degC |  | Occupied cooling set point | Occupied_Air_Temperature_Cooling_Setpoint |
| `ZN-Core_bottom/OCC-MODE` | status | standard | bas | - |  | Zone occupancy mode (1 occupied / 0 unoccupied) | Occupancy_Status |
| `ZN-Core_bottom/ZN-T-ADJ` | setpoint | standard | bas | K |  | Occupant set-point adjustment (wall sensor slider, +/-) | Temperature_Adjust_Sensor |

## VAV-Core_bottom - VAV

VAV terminal with hot-water reheat serving Core_bottom

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `VAV-Core_bottom/DA-F` | sensor | standard | energyplus | m3/s | air_flow | Discharge air flow | Discharge_Air_Flow_Sensor |
| `VAV-Core_bottom/DA-T` | sensor | standard | energyplus | degC | air_temperature | Discharge air temperature | Discharge_Air_Temperature_Sensor |
| `VAV-Core_bottom/DMPR-POS` | sensor | advanced | energyplus | % | position | Damper position feedback | Damper_Position_Sensor |
| `VAV-Core_bottom/DA-VP` | sensor | advanced | surrogate | Pa | pressure | Flow-cross velocity pressure (airflow transducer) | Velocity_Pressure_Sensor |
| `VAV-Core_bottom/RHV-POS` | sensor | advanced | energyplus | % | position | Reheat valve position (feedback) | Valve_Position_Sensor |
| `VAV-Core_bottom/RH-Q` | truth | truth | energyplus | kW |  | Reheat coil heat rate (ground truth) |  |
| `VAV-Core_bottom/RH-BTU` | sensor | next_gen | energyplus | kW | thermal_power | Reheat coil BTU meter (water-side heat rate) | Thermal_Power_Sensor |
| `VAV-Core_bottom/RH-WF` | sensor | next_gen | energyplus | L/s | water_flow | Reheat coil water flow | Water_Flow_Sensor |
| `VAV-Core_bottom/ZN-MODE` | status | standard | bas | - |  | Terminal control state (0 deadband, 1 cooling, 2 heating) | Mode_Status |
| `VAV-Core_bottom/CLG-REQ` | virtual | standard | bas | count |  | Cooling SAT-reset requests (G36) |  |
| `VAV-Core_bottom/PRS-REQ` | virtual | standard | bas | count |  | Static-pressure reset requests (G36) |  |
| `VAV-Core_bottom/HW-REQ` | virtual | standard | bas | count |  | Hot-water reset requests (G36) |  |
| `VAV-Core_bottom/LOW-FLOW-ALM` | status | standard | bas | - |  | Low airflow alarm (G36: flow < 70 % of set point for 5 min) | Low_Air_Flow_Alarm |
| `VAV-Core_bottom/DA-F-SP` | setpoint | standard | bas | m3/s |  | Discharge air flow set point | Discharge_Air_Flow_Setpoint |
| `VAV-Core_bottom/DMPR-CMD` | command | standard | bas | % |  | Damper command | Damper_Position_Command |
| `VAV-Core_bottom/CLG-LOOP` | virtual | standard | bas | % |  | Cooling loop output |  |
| `VAV-Core_bottom/HTG-LOOP` | virtual | standard | bas | % |  | Heating loop output |  |

## ZN-Core_mid - Zone

Thermal zone Core_mid (x10 floors)

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `ZN-Core_mid/ZN-T` | sensor | standard | energyplus | degC | zone_temperature | Zone air temperature | Zone_Air_Temperature_Sensor |
| `ZN-Core_mid/ZN-RH` | sensor | advanced | energyplus | %RH | humidity | Zone air relative humidity | Zone_Air_Humidity_Sensor |
| `ZN-Core_mid/ZN-DP` | sensor | advanced | energyplus | degC | air_temperature | Zone air dew-point temperature (calculated by T/RH transmitter) | Dewpoint_Sensor |
| `ZN-Core_mid/ZN-CO2` | sensor | standard | energyplus | ppm | co2 | Zone CO2 concentration (NDIR) | CO2_Sensor |
| `ZN-Core_mid/ZN-OCC` | sensor | standard | energyplus | - | occupancy | Zone occupancy sensor (PIR) | Occupancy_Sensor |
| `ZN-Core_mid/OCCUPANTS` | truth | truth | energyplus | people |  | True number of occupants (ground truth only) | Occupancy_Count_Sensor |
| `ZN-Core_mid/OCC-COUNT` | sensor | next_gen | model | people | people_count | People counter (camera / thermopile) | Occupancy_Count_Sensor |
| `ZN-Core_mid/WIN-STS` | sensor | advanced | model | - | binary | Window / door contact (1 = open) | Open_Close_Status |
| `ZN-Core_mid/ZN-MRT` | sensor | next_gen | energyplus | degC | radiant_temperature | Mean radiant temperature (globe thermometer) | Radiant_Temperature_Sensor |
| `ZN-Core_mid/ZN-OPT` | sensor | next_gen | energyplus | degC | zone_temperature | Operative temperature (comfort station) | Operative_Temperature |
| `ZN-Core_mid/PMV` | sensor | next_gen | energyplus | - | comfort_index | Predicted mean vote, ISO 7730 (comfort station) |  |
| `ZN-Core_mid/PPD` | sensor | next_gen | energyplus | % | comfort_ppd | Predicted percentage dissatisfied, ISO 7730 (comfort station) |  |
| `ZN-Core_mid/TS-VOTE` | sensor | next_gen | model | - | ideal | Mean thermal-sensation vote of occupants, last hour (feedback app, -3..+3) |  |
| `ZN-Core_mid/HOT-CALLS` | sensor | next_gen | model | count | ideal | Too-hot complaints today (work orders / app) |  |
| `ZN-Core_mid/COLD-CALLS` | sensor | next_gen | model | count | ideal | Too-cold complaints today (work orders / app) |  |
| `ZN-Core_mid/ZN-PM25` | sensor | next_gen | model | ug/m3 | pm_sensor | Zone PM2.5 (optical particle sensor) | PM2.5_Sensor |
| `ZN-Core_mid/ZN-PM10` | sensor | next_gen | model | ug/m3 | pm_sensor | Zone PM10 (optical particle sensor) | PM10_Sensor |
| `ZN-Core_mid/ZN-TVOC` | sensor | next_gen | model | ug/m3 | tvoc_sensor | Zone total VOC (metal-oxide sensor) | TVOC_Sensor |
| `ZN-Core_mid/ZN-LUX` | sensor | advanced | model | lux | illuminance | Work-plane illuminance (daylight-harvesting photosensor) | Illuminance_Sensor |
| `ZN-Core_mid/DAYLIGHT-LUX` | truth | truth | model | lux |  | Daylight share of the work-plane illuminance (ground truth only) |  |
| `ZN-Core_mid/LIGHT-LVL` | sensor | advanced | model | % | percent | Lighting level (networked lighting controls) |  |
| `ZN-Core_mid/ZN-DBA` | sensor | next_gen | model | dBA | sound | Background sound level (class-2 sound level meter) |  |
| `ZN-Core_mid/LIGHT-KW` | meter | advanced | energyplus | kW | power | Zone lighting power (lighting panel sub-meter) | Electric_Power_Sensor |
| `ZN-Core_mid/PLUG-KW` | meter | next_gen | energyplus | kW | power | Zone plug load power (circuit-level sub-meter) | Electric_Power_Sensor |
| `ZN-Core_mid/WIN-SOL-KW` | truth | truth | energyplus | kW |  | Transmitted solar gain (ground truth only) |  |
| `ZN-Core_mid/WIN-Q-KW` | truth | truth | energyplus | kW |  | Window heat gain (ground truth only) |  |
| `ZN-Core_mid/INT-GAIN-KW` | truth | truth | energyplus | kW |  | Total internal heat gain (ground truth only) |  |
| `ZN-Core_mid/SYS-CLG-KW` | truth | truth | energyplus | kW |  | Sensible cooling delivered to the zone (ground truth only) |  |
| `ZN-Core_mid/SYS-HTG-KW` | truth | truth | energyplus | kW |  | Sensible heating delivered to the zone (ground truth only) |  |
| `ZN-Core_mid/HTG-SP` | setpoint | standard | bas | degC |  | Active heating set point | Zone_Air_Heating_Temperature_Setpoint |
| `ZN-Core_mid/CLG-SP` | setpoint | standard | bas | degC |  | Active cooling set point | Zone_Air_Cooling_Temperature_Setpoint |
| `ZN-Core_mid/OCC-HTG-SP` | setpoint | standard | bas | degC |  | Occupied heating set point | Occupied_Air_Temperature_Heating_Setpoint |
| `ZN-Core_mid/OCC-CLG-SP` | setpoint | standard | bas | degC |  | Occupied cooling set point | Occupied_Air_Temperature_Cooling_Setpoint |
| `ZN-Core_mid/OCC-MODE` | status | standard | bas | - |  | Zone occupancy mode (1 occupied / 0 unoccupied) | Occupancy_Status |
| `ZN-Core_mid/ZN-T-ADJ` | setpoint | standard | bas | K |  | Occupant set-point adjustment (wall sensor slider, +/-) | Temperature_Adjust_Sensor |

## VAV-Core_mid - VAV

VAV terminal with hot-water reheat serving Core_mid

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `VAV-Core_mid/DA-F` | sensor | standard | energyplus | m3/s | air_flow | Discharge air flow | Discharge_Air_Flow_Sensor |
| `VAV-Core_mid/DA-T` | sensor | standard | energyplus | degC | air_temperature | Discharge air temperature | Discharge_Air_Temperature_Sensor |
| `VAV-Core_mid/DMPR-POS` | sensor | advanced | energyplus | % | position | Damper position feedback | Damper_Position_Sensor |
| `VAV-Core_mid/DA-VP` | sensor | advanced | surrogate | Pa | pressure | Flow-cross velocity pressure (airflow transducer) | Velocity_Pressure_Sensor |
| `VAV-Core_mid/RHV-POS` | sensor | advanced | energyplus | % | position | Reheat valve position (feedback) | Valve_Position_Sensor |
| `VAV-Core_mid/RH-Q` | truth | truth | energyplus | kW |  | Reheat coil heat rate (ground truth) |  |
| `VAV-Core_mid/RH-BTU` | sensor | next_gen | energyplus | kW | thermal_power | Reheat coil BTU meter (water-side heat rate) | Thermal_Power_Sensor |
| `VAV-Core_mid/RH-WF` | sensor | next_gen | energyplus | L/s | water_flow | Reheat coil water flow | Water_Flow_Sensor |
| `VAV-Core_mid/ZN-MODE` | status | standard | bas | - |  | Terminal control state (0 deadband, 1 cooling, 2 heating) | Mode_Status |
| `VAV-Core_mid/CLG-REQ` | virtual | standard | bas | count |  | Cooling SAT-reset requests (G36) |  |
| `VAV-Core_mid/PRS-REQ` | virtual | standard | bas | count |  | Static-pressure reset requests (G36) |  |
| `VAV-Core_mid/HW-REQ` | virtual | standard | bas | count |  | Hot-water reset requests (G36) |  |
| `VAV-Core_mid/LOW-FLOW-ALM` | status | standard | bas | - |  | Low airflow alarm (G36: flow < 70 % of set point for 5 min) | Low_Air_Flow_Alarm |
| `VAV-Core_mid/DA-F-SP` | setpoint | standard | bas | m3/s |  | Discharge air flow set point | Discharge_Air_Flow_Setpoint |
| `VAV-Core_mid/DMPR-CMD` | command | standard | bas | % |  | Damper command | Damper_Position_Command |
| `VAV-Core_mid/CLG-LOOP` | virtual | standard | bas | % |  | Cooling loop output |  |
| `VAV-Core_mid/HTG-LOOP` | virtual | standard | bas | % |  | Heating loop output |  |

## ZN-Core_top - Zone

Thermal zone Core_top

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `ZN-Core_top/ZN-T` | sensor | standard | energyplus | degC | zone_temperature | Zone air temperature | Zone_Air_Temperature_Sensor |
| `ZN-Core_top/ZN-RH` | sensor | advanced | energyplus | %RH | humidity | Zone air relative humidity | Zone_Air_Humidity_Sensor |
| `ZN-Core_top/ZN-DP` | sensor | advanced | energyplus | degC | air_temperature | Zone air dew-point temperature (calculated by T/RH transmitter) | Dewpoint_Sensor |
| `ZN-Core_top/ZN-CO2` | sensor | standard | energyplus | ppm | co2 | Zone CO2 concentration (NDIR) | CO2_Sensor |
| `ZN-Core_top/ZN-OCC` | sensor | standard | energyplus | - | occupancy | Zone occupancy sensor (PIR) | Occupancy_Sensor |
| `ZN-Core_top/OCCUPANTS` | truth | truth | energyplus | people |  | True number of occupants (ground truth only) | Occupancy_Count_Sensor |
| `ZN-Core_top/OCC-COUNT` | sensor | next_gen | model | people | people_count | People counter (camera / thermopile) | Occupancy_Count_Sensor |
| `ZN-Core_top/WIN-STS` | sensor | advanced | model | - | binary | Window / door contact (1 = open) | Open_Close_Status |
| `ZN-Core_top/ZN-MRT` | sensor | next_gen | energyplus | degC | radiant_temperature | Mean radiant temperature (globe thermometer) | Radiant_Temperature_Sensor |
| `ZN-Core_top/ZN-OPT` | sensor | next_gen | energyplus | degC | zone_temperature | Operative temperature (comfort station) | Operative_Temperature |
| `ZN-Core_top/PMV` | sensor | next_gen | energyplus | - | comfort_index | Predicted mean vote, ISO 7730 (comfort station) |  |
| `ZN-Core_top/PPD` | sensor | next_gen | energyplus | % | comfort_ppd | Predicted percentage dissatisfied, ISO 7730 (comfort station) |  |
| `ZN-Core_top/TS-VOTE` | sensor | next_gen | model | - | ideal | Mean thermal-sensation vote of occupants, last hour (feedback app, -3..+3) |  |
| `ZN-Core_top/HOT-CALLS` | sensor | next_gen | model | count | ideal | Too-hot complaints today (work orders / app) |  |
| `ZN-Core_top/COLD-CALLS` | sensor | next_gen | model | count | ideal | Too-cold complaints today (work orders / app) |  |
| `ZN-Core_top/ZN-PM25` | sensor | next_gen | model | ug/m3 | pm_sensor | Zone PM2.5 (optical particle sensor) | PM2.5_Sensor |
| `ZN-Core_top/ZN-PM10` | sensor | next_gen | model | ug/m3 | pm_sensor | Zone PM10 (optical particle sensor) | PM10_Sensor |
| `ZN-Core_top/ZN-TVOC` | sensor | next_gen | model | ug/m3 | tvoc_sensor | Zone total VOC (metal-oxide sensor) | TVOC_Sensor |
| `ZN-Core_top/ZN-LUX` | sensor | advanced | model | lux | illuminance | Work-plane illuminance (daylight-harvesting photosensor) | Illuminance_Sensor |
| `ZN-Core_top/DAYLIGHT-LUX` | truth | truth | model | lux |  | Daylight share of the work-plane illuminance (ground truth only) |  |
| `ZN-Core_top/LIGHT-LVL` | sensor | advanced | model | % | percent | Lighting level (networked lighting controls) |  |
| `ZN-Core_top/ZN-DBA` | sensor | next_gen | model | dBA | sound | Background sound level (class-2 sound level meter) |  |
| `ZN-Core_top/LIGHT-KW` | meter | advanced | energyplus | kW | power | Zone lighting power (lighting panel sub-meter) | Electric_Power_Sensor |
| `ZN-Core_top/PLUG-KW` | meter | next_gen | energyplus | kW | power | Zone plug load power (circuit-level sub-meter) | Electric_Power_Sensor |
| `ZN-Core_top/WIN-SOL-KW` | truth | truth | energyplus | kW |  | Transmitted solar gain (ground truth only) |  |
| `ZN-Core_top/WIN-Q-KW` | truth | truth | energyplus | kW |  | Window heat gain (ground truth only) |  |
| `ZN-Core_top/INT-GAIN-KW` | truth | truth | energyplus | kW |  | Total internal heat gain (ground truth only) |  |
| `ZN-Core_top/SYS-CLG-KW` | truth | truth | energyplus | kW |  | Sensible cooling delivered to the zone (ground truth only) |  |
| `ZN-Core_top/SYS-HTG-KW` | truth | truth | energyplus | kW |  | Sensible heating delivered to the zone (ground truth only) |  |
| `ZN-Core_top/HTG-SP` | setpoint | standard | bas | degC |  | Active heating set point | Zone_Air_Heating_Temperature_Setpoint |
| `ZN-Core_top/CLG-SP` | setpoint | standard | bas | degC |  | Active cooling set point | Zone_Air_Cooling_Temperature_Setpoint |
| `ZN-Core_top/OCC-HTG-SP` | setpoint | standard | bas | degC |  | Occupied heating set point | Occupied_Air_Temperature_Heating_Setpoint |
| `ZN-Core_top/OCC-CLG-SP` | setpoint | standard | bas | degC |  | Occupied cooling set point | Occupied_Air_Temperature_Cooling_Setpoint |
| `ZN-Core_top/OCC-MODE` | status | standard | bas | - |  | Zone occupancy mode (1 occupied / 0 unoccupied) | Occupancy_Status |
| `ZN-Core_top/ZN-T-ADJ` | setpoint | standard | bas | K |  | Occupant set-point adjustment (wall sensor slider, +/-) | Temperature_Adjust_Sensor |

## VAV-Core_top - VAV

VAV terminal with hot-water reheat serving Core_top

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `VAV-Core_top/DA-F` | sensor | standard | energyplus | m3/s | air_flow | Discharge air flow | Discharge_Air_Flow_Sensor |
| `VAV-Core_top/DA-T` | sensor | standard | energyplus | degC | air_temperature | Discharge air temperature | Discharge_Air_Temperature_Sensor |
| `VAV-Core_top/DMPR-POS` | sensor | advanced | energyplus | % | position | Damper position feedback | Damper_Position_Sensor |
| `VAV-Core_top/DA-VP` | sensor | advanced | surrogate | Pa | pressure | Flow-cross velocity pressure (airflow transducer) | Velocity_Pressure_Sensor |
| `VAV-Core_top/RHV-POS` | sensor | advanced | energyplus | % | position | Reheat valve position (feedback) | Valve_Position_Sensor |
| `VAV-Core_top/RH-Q` | truth | truth | energyplus | kW |  | Reheat coil heat rate (ground truth) |  |
| `VAV-Core_top/RH-BTU` | sensor | next_gen | energyplus | kW | thermal_power | Reheat coil BTU meter (water-side heat rate) | Thermal_Power_Sensor |
| `VAV-Core_top/RH-WF` | sensor | next_gen | energyplus | L/s | water_flow | Reheat coil water flow | Water_Flow_Sensor |
| `VAV-Core_top/ZN-MODE` | status | standard | bas | - |  | Terminal control state (0 deadband, 1 cooling, 2 heating) | Mode_Status |
| `VAV-Core_top/CLG-REQ` | virtual | standard | bas | count |  | Cooling SAT-reset requests (G36) |  |
| `VAV-Core_top/PRS-REQ` | virtual | standard | bas | count |  | Static-pressure reset requests (G36) |  |
| `VAV-Core_top/HW-REQ` | virtual | standard | bas | count |  | Hot-water reset requests (G36) |  |
| `VAV-Core_top/LOW-FLOW-ALM` | status | standard | bas | - |  | Low airflow alarm (G36: flow < 70 % of set point for 5 min) | Low_Air_Flow_Alarm |
| `VAV-Core_top/DA-F-SP` | setpoint | standard | bas | m3/s |  | Discharge air flow set point | Discharge_Air_Flow_Setpoint |
| `VAV-Core_top/DMPR-CMD` | command | standard | bas | % |  | Damper command | Damper_Position_Command |
| `VAV-Core_top/CLG-LOOP` | virtual | standard | bas | % |  | Cooling loop output |  |
| `VAV-Core_top/HTG-LOOP` | virtual | standard | bas | % |  | Heating loop output |  |

## ZN-Perimeter_bot_ZN_1 - Zone

Thermal zone Perimeter_bot_ZN_1

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `ZN-Perimeter_bot_ZN_1/ZN-T` | sensor | standard | energyplus | degC | zone_temperature | Zone air temperature | Zone_Air_Temperature_Sensor |
| `ZN-Perimeter_bot_ZN_1/ZN-RH` | sensor | advanced | energyplus | %RH | humidity | Zone air relative humidity | Zone_Air_Humidity_Sensor |
| `ZN-Perimeter_bot_ZN_1/ZN-DP` | sensor | advanced | energyplus | degC | air_temperature | Zone air dew-point temperature (calculated by T/RH transmitter) | Dewpoint_Sensor |
| `ZN-Perimeter_bot_ZN_1/ZN-CO2` | sensor | standard | energyplus | ppm | co2 | Zone CO2 concentration (NDIR) | CO2_Sensor |
| `ZN-Perimeter_bot_ZN_1/ZN-OCC` | sensor | standard | energyplus | - | occupancy | Zone occupancy sensor (PIR) | Occupancy_Sensor |
| `ZN-Perimeter_bot_ZN_1/OCCUPANTS` | truth | truth | energyplus | people |  | True number of occupants (ground truth only) | Occupancy_Count_Sensor |
| `ZN-Perimeter_bot_ZN_1/OCC-COUNT` | sensor | next_gen | model | people | people_count | People counter (camera / thermopile) | Occupancy_Count_Sensor |
| `ZN-Perimeter_bot_ZN_1/WIN-STS` | sensor | advanced | model | - | binary | Window / door contact (1 = open) | Open_Close_Status |
| `ZN-Perimeter_bot_ZN_1/ZN-MRT` | sensor | next_gen | energyplus | degC | radiant_temperature | Mean radiant temperature (globe thermometer) | Radiant_Temperature_Sensor |
| `ZN-Perimeter_bot_ZN_1/ZN-OPT` | sensor | next_gen | energyplus | degC | zone_temperature | Operative temperature (comfort station) | Operative_Temperature |
| `ZN-Perimeter_bot_ZN_1/PMV` | sensor | next_gen | energyplus | - | comfort_index | Predicted mean vote, ISO 7730 (comfort station) |  |
| `ZN-Perimeter_bot_ZN_1/PPD` | sensor | next_gen | energyplus | % | comfort_ppd | Predicted percentage dissatisfied, ISO 7730 (comfort station) |  |
| `ZN-Perimeter_bot_ZN_1/TS-VOTE` | sensor | next_gen | model | - | ideal | Mean thermal-sensation vote of occupants, last hour (feedback app, -3..+3) |  |
| `ZN-Perimeter_bot_ZN_1/HOT-CALLS` | sensor | next_gen | model | count | ideal | Too-hot complaints today (work orders / app) |  |
| `ZN-Perimeter_bot_ZN_1/COLD-CALLS` | sensor | next_gen | model | count | ideal | Too-cold complaints today (work orders / app) |  |
| `ZN-Perimeter_bot_ZN_1/ZN-PM25` | sensor | next_gen | model | ug/m3 | pm_sensor | Zone PM2.5 (optical particle sensor) | PM2.5_Sensor |
| `ZN-Perimeter_bot_ZN_1/ZN-PM10` | sensor | next_gen | model | ug/m3 | pm_sensor | Zone PM10 (optical particle sensor) | PM10_Sensor |
| `ZN-Perimeter_bot_ZN_1/ZN-TVOC` | sensor | next_gen | model | ug/m3 | tvoc_sensor | Zone total VOC (metal-oxide sensor) | TVOC_Sensor |
| `ZN-Perimeter_bot_ZN_1/ZN-LUX` | sensor | advanced | model | lux | illuminance | Work-plane illuminance (daylight-harvesting photosensor) | Illuminance_Sensor |
| `ZN-Perimeter_bot_ZN_1/DAYLIGHT-LUX` | truth | truth | model | lux |  | Daylight share of the work-plane illuminance (ground truth only) |  |
| `ZN-Perimeter_bot_ZN_1/LIGHT-LVL` | sensor | advanced | model | % | percent | Lighting level (networked lighting controls) |  |
| `ZN-Perimeter_bot_ZN_1/ZN-DBA` | sensor | next_gen | model | dBA | sound | Background sound level (class-2 sound level meter) |  |
| `ZN-Perimeter_bot_ZN_1/LIGHT-KW` | meter | advanced | energyplus | kW | power | Zone lighting power (lighting panel sub-meter) | Electric_Power_Sensor |
| `ZN-Perimeter_bot_ZN_1/PLUG-KW` | meter | next_gen | energyplus | kW | power | Zone plug load power (circuit-level sub-meter) | Electric_Power_Sensor |
| `ZN-Perimeter_bot_ZN_1/INFIL-ACH` | truth | truth | energyplus | 1/h |  | Infiltration air-change rate (ground truth only) |  |
| `ZN-Perimeter_bot_ZN_1/WIN-SOL-KW` | truth | truth | energyplus | kW |  | Transmitted solar gain (ground truth only) |  |
| `ZN-Perimeter_bot_ZN_1/WIN-Q-KW` | truth | truth | energyplus | kW |  | Window heat gain (ground truth only) |  |
| `ZN-Perimeter_bot_ZN_1/INT-GAIN-KW` | truth | truth | energyplus | kW |  | Total internal heat gain (ground truth only) |  |
| `ZN-Perimeter_bot_ZN_1/SYS-CLG-KW` | truth | truth | energyplus | kW |  | Sensible cooling delivered to the zone (ground truth only) |  |
| `ZN-Perimeter_bot_ZN_1/SYS-HTG-KW` | truth | truth | energyplus | kW |  | Sensible heating delivered to the zone (ground truth only) |  |
| `ZN-Perimeter_bot_ZN_1/HTG-SP` | setpoint | standard | bas | degC |  | Active heating set point | Zone_Air_Heating_Temperature_Setpoint |
| `ZN-Perimeter_bot_ZN_1/CLG-SP` | setpoint | standard | bas | degC |  | Active cooling set point | Zone_Air_Cooling_Temperature_Setpoint |
| `ZN-Perimeter_bot_ZN_1/OCC-HTG-SP` | setpoint | standard | bas | degC |  | Occupied heating set point | Occupied_Air_Temperature_Heating_Setpoint |
| `ZN-Perimeter_bot_ZN_1/OCC-CLG-SP` | setpoint | standard | bas | degC |  | Occupied cooling set point | Occupied_Air_Temperature_Cooling_Setpoint |
| `ZN-Perimeter_bot_ZN_1/OCC-MODE` | status | standard | bas | - |  | Zone occupancy mode (1 occupied / 0 unoccupied) | Occupancy_Status |
| `ZN-Perimeter_bot_ZN_1/ZN-T-ADJ` | setpoint | standard | bas | K |  | Occupant set-point adjustment (wall sensor slider, +/-) | Temperature_Adjust_Sensor |

## VAV-Perimeter_bot_ZN_1 - VAV

VAV terminal with hot-water reheat serving Perimeter_bot_ZN_1

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `VAV-Perimeter_bot_ZN_1/DA-F` | sensor | standard | energyplus | m3/s | air_flow | Discharge air flow | Discharge_Air_Flow_Sensor |
| `VAV-Perimeter_bot_ZN_1/DA-T` | sensor | standard | energyplus | degC | air_temperature | Discharge air temperature | Discharge_Air_Temperature_Sensor |
| `VAV-Perimeter_bot_ZN_1/DMPR-POS` | sensor | advanced | energyplus | % | position | Damper position feedback | Damper_Position_Sensor |
| `VAV-Perimeter_bot_ZN_1/DA-VP` | sensor | advanced | surrogate | Pa | pressure | Flow-cross velocity pressure (airflow transducer) | Velocity_Pressure_Sensor |
| `VAV-Perimeter_bot_ZN_1/RHV-POS` | sensor | advanced | energyplus | % | position | Reheat valve position (feedback) | Valve_Position_Sensor |
| `VAV-Perimeter_bot_ZN_1/RH-Q` | truth | truth | energyplus | kW |  | Reheat coil heat rate (ground truth) |  |
| `VAV-Perimeter_bot_ZN_1/RH-BTU` | sensor | next_gen | energyplus | kW | thermal_power | Reheat coil BTU meter (water-side heat rate) | Thermal_Power_Sensor |
| `VAV-Perimeter_bot_ZN_1/RH-WF` | sensor | next_gen | energyplus | L/s | water_flow | Reheat coil water flow | Water_Flow_Sensor |
| `VAV-Perimeter_bot_ZN_1/ZN-MODE` | status | standard | bas | - |  | Terminal control state (0 deadband, 1 cooling, 2 heating) | Mode_Status |
| `VAV-Perimeter_bot_ZN_1/CLG-REQ` | virtual | standard | bas | count |  | Cooling SAT-reset requests (G36) |  |
| `VAV-Perimeter_bot_ZN_1/PRS-REQ` | virtual | standard | bas | count |  | Static-pressure reset requests (G36) |  |
| `VAV-Perimeter_bot_ZN_1/HW-REQ` | virtual | standard | bas | count |  | Hot-water reset requests (G36) |  |
| `VAV-Perimeter_bot_ZN_1/LOW-FLOW-ALM` | status | standard | bas | - |  | Low airflow alarm (G36: flow < 70 % of set point for 5 min) | Low_Air_Flow_Alarm |
| `VAV-Perimeter_bot_ZN_1/DA-F-SP` | setpoint | standard | bas | m3/s |  | Discharge air flow set point | Discharge_Air_Flow_Setpoint |
| `VAV-Perimeter_bot_ZN_1/DMPR-CMD` | command | standard | bas | % |  | Damper command | Damper_Position_Command |
| `VAV-Perimeter_bot_ZN_1/CLG-LOOP` | virtual | standard | bas | % |  | Cooling loop output |  |
| `VAV-Perimeter_bot_ZN_1/HTG-LOOP` | virtual | standard | bas | % |  | Heating loop output |  |

## ZN-Perimeter_bot_ZN_2 - Zone

Thermal zone Perimeter_bot_ZN_2

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `ZN-Perimeter_bot_ZN_2/ZN-T` | sensor | standard | energyplus | degC | zone_temperature | Zone air temperature | Zone_Air_Temperature_Sensor |
| `ZN-Perimeter_bot_ZN_2/ZN-RH` | sensor | advanced | energyplus | %RH | humidity | Zone air relative humidity | Zone_Air_Humidity_Sensor |
| `ZN-Perimeter_bot_ZN_2/ZN-DP` | sensor | advanced | energyplus | degC | air_temperature | Zone air dew-point temperature (calculated by T/RH transmitter) | Dewpoint_Sensor |
| `ZN-Perimeter_bot_ZN_2/ZN-CO2` | sensor | standard | energyplus | ppm | co2 | Zone CO2 concentration (NDIR) | CO2_Sensor |
| `ZN-Perimeter_bot_ZN_2/ZN-OCC` | sensor | standard | energyplus | - | occupancy | Zone occupancy sensor (PIR) | Occupancy_Sensor |
| `ZN-Perimeter_bot_ZN_2/OCCUPANTS` | truth | truth | energyplus | people |  | True number of occupants (ground truth only) | Occupancy_Count_Sensor |
| `ZN-Perimeter_bot_ZN_2/OCC-COUNT` | sensor | next_gen | model | people | people_count | People counter (camera / thermopile) | Occupancy_Count_Sensor |
| `ZN-Perimeter_bot_ZN_2/WIN-STS` | sensor | advanced | model | - | binary | Window / door contact (1 = open) | Open_Close_Status |
| `ZN-Perimeter_bot_ZN_2/ZN-MRT` | sensor | next_gen | energyplus | degC | radiant_temperature | Mean radiant temperature (globe thermometer) | Radiant_Temperature_Sensor |
| `ZN-Perimeter_bot_ZN_2/ZN-OPT` | sensor | next_gen | energyplus | degC | zone_temperature | Operative temperature (comfort station) | Operative_Temperature |
| `ZN-Perimeter_bot_ZN_2/PMV` | sensor | next_gen | energyplus | - | comfort_index | Predicted mean vote, ISO 7730 (comfort station) |  |
| `ZN-Perimeter_bot_ZN_2/PPD` | sensor | next_gen | energyplus | % | comfort_ppd | Predicted percentage dissatisfied, ISO 7730 (comfort station) |  |
| `ZN-Perimeter_bot_ZN_2/TS-VOTE` | sensor | next_gen | model | - | ideal | Mean thermal-sensation vote of occupants, last hour (feedback app, -3..+3) |  |
| `ZN-Perimeter_bot_ZN_2/HOT-CALLS` | sensor | next_gen | model | count | ideal | Too-hot complaints today (work orders / app) |  |
| `ZN-Perimeter_bot_ZN_2/COLD-CALLS` | sensor | next_gen | model | count | ideal | Too-cold complaints today (work orders / app) |  |
| `ZN-Perimeter_bot_ZN_2/ZN-PM25` | sensor | next_gen | model | ug/m3 | pm_sensor | Zone PM2.5 (optical particle sensor) | PM2.5_Sensor |
| `ZN-Perimeter_bot_ZN_2/ZN-PM10` | sensor | next_gen | model | ug/m3 | pm_sensor | Zone PM10 (optical particle sensor) | PM10_Sensor |
| `ZN-Perimeter_bot_ZN_2/ZN-TVOC` | sensor | next_gen | model | ug/m3 | tvoc_sensor | Zone total VOC (metal-oxide sensor) | TVOC_Sensor |
| `ZN-Perimeter_bot_ZN_2/ZN-LUX` | sensor | advanced | model | lux | illuminance | Work-plane illuminance (daylight-harvesting photosensor) | Illuminance_Sensor |
| `ZN-Perimeter_bot_ZN_2/DAYLIGHT-LUX` | truth | truth | model | lux |  | Daylight share of the work-plane illuminance (ground truth only) |  |
| `ZN-Perimeter_bot_ZN_2/LIGHT-LVL` | sensor | advanced | model | % | percent | Lighting level (networked lighting controls) |  |
| `ZN-Perimeter_bot_ZN_2/ZN-DBA` | sensor | next_gen | model | dBA | sound | Background sound level (class-2 sound level meter) |  |
| `ZN-Perimeter_bot_ZN_2/LIGHT-KW` | meter | advanced | energyplus | kW | power | Zone lighting power (lighting panel sub-meter) | Electric_Power_Sensor |
| `ZN-Perimeter_bot_ZN_2/PLUG-KW` | meter | next_gen | energyplus | kW | power | Zone plug load power (circuit-level sub-meter) | Electric_Power_Sensor |
| `ZN-Perimeter_bot_ZN_2/INFIL-ACH` | truth | truth | energyplus | 1/h |  | Infiltration air-change rate (ground truth only) |  |
| `ZN-Perimeter_bot_ZN_2/WIN-SOL-KW` | truth | truth | energyplus | kW |  | Transmitted solar gain (ground truth only) |  |
| `ZN-Perimeter_bot_ZN_2/WIN-Q-KW` | truth | truth | energyplus | kW |  | Window heat gain (ground truth only) |  |
| `ZN-Perimeter_bot_ZN_2/INT-GAIN-KW` | truth | truth | energyplus | kW |  | Total internal heat gain (ground truth only) |  |
| `ZN-Perimeter_bot_ZN_2/SYS-CLG-KW` | truth | truth | energyplus | kW |  | Sensible cooling delivered to the zone (ground truth only) |  |
| `ZN-Perimeter_bot_ZN_2/SYS-HTG-KW` | truth | truth | energyplus | kW |  | Sensible heating delivered to the zone (ground truth only) |  |
| `ZN-Perimeter_bot_ZN_2/HTG-SP` | setpoint | standard | bas | degC |  | Active heating set point | Zone_Air_Heating_Temperature_Setpoint |
| `ZN-Perimeter_bot_ZN_2/CLG-SP` | setpoint | standard | bas | degC |  | Active cooling set point | Zone_Air_Cooling_Temperature_Setpoint |
| `ZN-Perimeter_bot_ZN_2/OCC-HTG-SP` | setpoint | standard | bas | degC |  | Occupied heating set point | Occupied_Air_Temperature_Heating_Setpoint |
| `ZN-Perimeter_bot_ZN_2/OCC-CLG-SP` | setpoint | standard | bas | degC |  | Occupied cooling set point | Occupied_Air_Temperature_Cooling_Setpoint |
| `ZN-Perimeter_bot_ZN_2/OCC-MODE` | status | standard | bas | - |  | Zone occupancy mode (1 occupied / 0 unoccupied) | Occupancy_Status |
| `ZN-Perimeter_bot_ZN_2/ZN-T-ADJ` | setpoint | standard | bas | K |  | Occupant set-point adjustment (wall sensor slider, +/-) | Temperature_Adjust_Sensor |

## VAV-Perimeter_bot_ZN_2 - VAV

VAV terminal with hot-water reheat serving Perimeter_bot_ZN_2

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `VAV-Perimeter_bot_ZN_2/DA-F` | sensor | standard | energyplus | m3/s | air_flow | Discharge air flow | Discharge_Air_Flow_Sensor |
| `VAV-Perimeter_bot_ZN_2/DA-T` | sensor | standard | energyplus | degC | air_temperature | Discharge air temperature | Discharge_Air_Temperature_Sensor |
| `VAV-Perimeter_bot_ZN_2/DMPR-POS` | sensor | advanced | energyplus | % | position | Damper position feedback | Damper_Position_Sensor |
| `VAV-Perimeter_bot_ZN_2/DA-VP` | sensor | advanced | surrogate | Pa | pressure | Flow-cross velocity pressure (airflow transducer) | Velocity_Pressure_Sensor |
| `VAV-Perimeter_bot_ZN_2/RHV-POS` | sensor | advanced | energyplus | % | position | Reheat valve position (feedback) | Valve_Position_Sensor |
| `VAV-Perimeter_bot_ZN_2/RH-Q` | truth | truth | energyplus | kW |  | Reheat coil heat rate (ground truth) |  |
| `VAV-Perimeter_bot_ZN_2/RH-BTU` | sensor | next_gen | energyplus | kW | thermal_power | Reheat coil BTU meter (water-side heat rate) | Thermal_Power_Sensor |
| `VAV-Perimeter_bot_ZN_2/RH-WF` | sensor | next_gen | energyplus | L/s | water_flow | Reheat coil water flow | Water_Flow_Sensor |
| `VAV-Perimeter_bot_ZN_2/ZN-MODE` | status | standard | bas | - |  | Terminal control state (0 deadband, 1 cooling, 2 heating) | Mode_Status |
| `VAV-Perimeter_bot_ZN_2/CLG-REQ` | virtual | standard | bas | count |  | Cooling SAT-reset requests (G36) |  |
| `VAV-Perimeter_bot_ZN_2/PRS-REQ` | virtual | standard | bas | count |  | Static-pressure reset requests (G36) |  |
| `VAV-Perimeter_bot_ZN_2/HW-REQ` | virtual | standard | bas | count |  | Hot-water reset requests (G36) |  |
| `VAV-Perimeter_bot_ZN_2/LOW-FLOW-ALM` | status | standard | bas | - |  | Low airflow alarm (G36: flow < 70 % of set point for 5 min) | Low_Air_Flow_Alarm |
| `VAV-Perimeter_bot_ZN_2/DA-F-SP` | setpoint | standard | bas | m3/s |  | Discharge air flow set point | Discharge_Air_Flow_Setpoint |
| `VAV-Perimeter_bot_ZN_2/DMPR-CMD` | command | standard | bas | % |  | Damper command | Damper_Position_Command |
| `VAV-Perimeter_bot_ZN_2/CLG-LOOP` | virtual | standard | bas | % |  | Cooling loop output |  |
| `VAV-Perimeter_bot_ZN_2/HTG-LOOP` | virtual | standard | bas | % |  | Heating loop output |  |

## ZN-Perimeter_bot_ZN_3 - Zone

Thermal zone Perimeter_bot_ZN_3

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `ZN-Perimeter_bot_ZN_3/ZN-T` | sensor | standard | energyplus | degC | zone_temperature | Zone air temperature | Zone_Air_Temperature_Sensor |
| `ZN-Perimeter_bot_ZN_3/ZN-RH` | sensor | advanced | energyplus | %RH | humidity | Zone air relative humidity | Zone_Air_Humidity_Sensor |
| `ZN-Perimeter_bot_ZN_3/ZN-DP` | sensor | advanced | energyplus | degC | air_temperature | Zone air dew-point temperature (calculated by T/RH transmitter) | Dewpoint_Sensor |
| `ZN-Perimeter_bot_ZN_3/ZN-CO2` | sensor | standard | energyplus | ppm | co2 | Zone CO2 concentration (NDIR) | CO2_Sensor |
| `ZN-Perimeter_bot_ZN_3/ZN-OCC` | sensor | standard | energyplus | - | occupancy | Zone occupancy sensor (PIR) | Occupancy_Sensor |
| `ZN-Perimeter_bot_ZN_3/OCCUPANTS` | truth | truth | energyplus | people |  | True number of occupants (ground truth only) | Occupancy_Count_Sensor |
| `ZN-Perimeter_bot_ZN_3/OCC-COUNT` | sensor | next_gen | model | people | people_count | People counter (camera / thermopile) | Occupancy_Count_Sensor |
| `ZN-Perimeter_bot_ZN_3/WIN-STS` | sensor | advanced | model | - | binary | Window / door contact (1 = open) | Open_Close_Status |
| `ZN-Perimeter_bot_ZN_3/ZN-MRT` | sensor | next_gen | energyplus | degC | radiant_temperature | Mean radiant temperature (globe thermometer) | Radiant_Temperature_Sensor |
| `ZN-Perimeter_bot_ZN_3/ZN-OPT` | sensor | next_gen | energyplus | degC | zone_temperature | Operative temperature (comfort station) | Operative_Temperature |
| `ZN-Perimeter_bot_ZN_3/PMV` | sensor | next_gen | energyplus | - | comfort_index | Predicted mean vote, ISO 7730 (comfort station) |  |
| `ZN-Perimeter_bot_ZN_3/PPD` | sensor | next_gen | energyplus | % | comfort_ppd | Predicted percentage dissatisfied, ISO 7730 (comfort station) |  |
| `ZN-Perimeter_bot_ZN_3/TS-VOTE` | sensor | next_gen | model | - | ideal | Mean thermal-sensation vote of occupants, last hour (feedback app, -3..+3) |  |
| `ZN-Perimeter_bot_ZN_3/HOT-CALLS` | sensor | next_gen | model | count | ideal | Too-hot complaints today (work orders / app) |  |
| `ZN-Perimeter_bot_ZN_3/COLD-CALLS` | sensor | next_gen | model | count | ideal | Too-cold complaints today (work orders / app) |  |
| `ZN-Perimeter_bot_ZN_3/ZN-PM25` | sensor | next_gen | model | ug/m3 | pm_sensor | Zone PM2.5 (optical particle sensor) | PM2.5_Sensor |
| `ZN-Perimeter_bot_ZN_3/ZN-PM10` | sensor | next_gen | model | ug/m3 | pm_sensor | Zone PM10 (optical particle sensor) | PM10_Sensor |
| `ZN-Perimeter_bot_ZN_3/ZN-TVOC` | sensor | next_gen | model | ug/m3 | tvoc_sensor | Zone total VOC (metal-oxide sensor) | TVOC_Sensor |
| `ZN-Perimeter_bot_ZN_3/ZN-LUX` | sensor | advanced | model | lux | illuminance | Work-plane illuminance (daylight-harvesting photosensor) | Illuminance_Sensor |
| `ZN-Perimeter_bot_ZN_3/DAYLIGHT-LUX` | truth | truth | model | lux |  | Daylight share of the work-plane illuminance (ground truth only) |  |
| `ZN-Perimeter_bot_ZN_3/LIGHT-LVL` | sensor | advanced | model | % | percent | Lighting level (networked lighting controls) |  |
| `ZN-Perimeter_bot_ZN_3/ZN-DBA` | sensor | next_gen | model | dBA | sound | Background sound level (class-2 sound level meter) |  |
| `ZN-Perimeter_bot_ZN_3/LIGHT-KW` | meter | advanced | energyplus | kW | power | Zone lighting power (lighting panel sub-meter) | Electric_Power_Sensor |
| `ZN-Perimeter_bot_ZN_3/PLUG-KW` | meter | next_gen | energyplus | kW | power | Zone plug load power (circuit-level sub-meter) | Electric_Power_Sensor |
| `ZN-Perimeter_bot_ZN_3/INFIL-ACH` | truth | truth | energyplus | 1/h |  | Infiltration air-change rate (ground truth only) |  |
| `ZN-Perimeter_bot_ZN_3/WIN-SOL-KW` | truth | truth | energyplus | kW |  | Transmitted solar gain (ground truth only) |  |
| `ZN-Perimeter_bot_ZN_3/WIN-Q-KW` | truth | truth | energyplus | kW |  | Window heat gain (ground truth only) |  |
| `ZN-Perimeter_bot_ZN_3/INT-GAIN-KW` | truth | truth | energyplus | kW |  | Total internal heat gain (ground truth only) |  |
| `ZN-Perimeter_bot_ZN_3/SYS-CLG-KW` | truth | truth | energyplus | kW |  | Sensible cooling delivered to the zone (ground truth only) |  |
| `ZN-Perimeter_bot_ZN_3/SYS-HTG-KW` | truth | truth | energyplus | kW |  | Sensible heating delivered to the zone (ground truth only) |  |
| `ZN-Perimeter_bot_ZN_3/HTG-SP` | setpoint | standard | bas | degC |  | Active heating set point | Zone_Air_Heating_Temperature_Setpoint |
| `ZN-Perimeter_bot_ZN_3/CLG-SP` | setpoint | standard | bas | degC |  | Active cooling set point | Zone_Air_Cooling_Temperature_Setpoint |
| `ZN-Perimeter_bot_ZN_3/OCC-HTG-SP` | setpoint | standard | bas | degC |  | Occupied heating set point | Occupied_Air_Temperature_Heating_Setpoint |
| `ZN-Perimeter_bot_ZN_3/OCC-CLG-SP` | setpoint | standard | bas | degC |  | Occupied cooling set point | Occupied_Air_Temperature_Cooling_Setpoint |
| `ZN-Perimeter_bot_ZN_3/OCC-MODE` | status | standard | bas | - |  | Zone occupancy mode (1 occupied / 0 unoccupied) | Occupancy_Status |
| `ZN-Perimeter_bot_ZN_3/ZN-T-ADJ` | setpoint | standard | bas | K |  | Occupant set-point adjustment (wall sensor slider, +/-) | Temperature_Adjust_Sensor |

## VAV-Perimeter_bot_ZN_3 - VAV

VAV terminal with hot-water reheat serving Perimeter_bot_ZN_3

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `VAV-Perimeter_bot_ZN_3/DA-F` | sensor | standard | energyplus | m3/s | air_flow | Discharge air flow | Discharge_Air_Flow_Sensor |
| `VAV-Perimeter_bot_ZN_3/DA-T` | sensor | standard | energyplus | degC | air_temperature | Discharge air temperature | Discharge_Air_Temperature_Sensor |
| `VAV-Perimeter_bot_ZN_3/DMPR-POS` | sensor | advanced | energyplus | % | position | Damper position feedback | Damper_Position_Sensor |
| `VAV-Perimeter_bot_ZN_3/DA-VP` | sensor | advanced | surrogate | Pa | pressure | Flow-cross velocity pressure (airflow transducer) | Velocity_Pressure_Sensor |
| `VAV-Perimeter_bot_ZN_3/RHV-POS` | sensor | advanced | energyplus | % | position | Reheat valve position (feedback) | Valve_Position_Sensor |
| `VAV-Perimeter_bot_ZN_3/RH-Q` | truth | truth | energyplus | kW |  | Reheat coil heat rate (ground truth) |  |
| `VAV-Perimeter_bot_ZN_3/RH-BTU` | sensor | next_gen | energyplus | kW | thermal_power | Reheat coil BTU meter (water-side heat rate) | Thermal_Power_Sensor |
| `VAV-Perimeter_bot_ZN_3/RH-WF` | sensor | next_gen | energyplus | L/s | water_flow | Reheat coil water flow | Water_Flow_Sensor |
| `VAV-Perimeter_bot_ZN_3/ZN-MODE` | status | standard | bas | - |  | Terminal control state (0 deadband, 1 cooling, 2 heating) | Mode_Status |
| `VAV-Perimeter_bot_ZN_3/CLG-REQ` | virtual | standard | bas | count |  | Cooling SAT-reset requests (G36) |  |
| `VAV-Perimeter_bot_ZN_3/PRS-REQ` | virtual | standard | bas | count |  | Static-pressure reset requests (G36) |  |
| `VAV-Perimeter_bot_ZN_3/HW-REQ` | virtual | standard | bas | count |  | Hot-water reset requests (G36) |  |
| `VAV-Perimeter_bot_ZN_3/LOW-FLOW-ALM` | status | standard | bas | - |  | Low airflow alarm (G36: flow < 70 % of set point for 5 min) | Low_Air_Flow_Alarm |
| `VAV-Perimeter_bot_ZN_3/DA-F-SP` | setpoint | standard | bas | m3/s |  | Discharge air flow set point | Discharge_Air_Flow_Setpoint |
| `VAV-Perimeter_bot_ZN_3/DMPR-CMD` | command | standard | bas | % |  | Damper command | Damper_Position_Command |
| `VAV-Perimeter_bot_ZN_3/CLG-LOOP` | virtual | standard | bas | % |  | Cooling loop output |  |
| `VAV-Perimeter_bot_ZN_3/HTG-LOOP` | virtual | standard | bas | % |  | Heating loop output |  |

## ZN-Perimeter_bot_ZN_4 - Zone

Thermal zone Perimeter_bot_ZN_4

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `ZN-Perimeter_bot_ZN_4/ZN-T` | sensor | standard | energyplus | degC | zone_temperature | Zone air temperature | Zone_Air_Temperature_Sensor |
| `ZN-Perimeter_bot_ZN_4/ZN-RH` | sensor | advanced | energyplus | %RH | humidity | Zone air relative humidity | Zone_Air_Humidity_Sensor |
| `ZN-Perimeter_bot_ZN_4/ZN-DP` | sensor | advanced | energyplus | degC | air_temperature | Zone air dew-point temperature (calculated by T/RH transmitter) | Dewpoint_Sensor |
| `ZN-Perimeter_bot_ZN_4/ZN-CO2` | sensor | standard | energyplus | ppm | co2 | Zone CO2 concentration (NDIR) | CO2_Sensor |
| `ZN-Perimeter_bot_ZN_4/ZN-OCC` | sensor | standard | energyplus | - | occupancy | Zone occupancy sensor (PIR) | Occupancy_Sensor |
| `ZN-Perimeter_bot_ZN_4/OCCUPANTS` | truth | truth | energyplus | people |  | True number of occupants (ground truth only) | Occupancy_Count_Sensor |
| `ZN-Perimeter_bot_ZN_4/OCC-COUNT` | sensor | next_gen | model | people | people_count | People counter (camera / thermopile) | Occupancy_Count_Sensor |
| `ZN-Perimeter_bot_ZN_4/WIN-STS` | sensor | advanced | model | - | binary | Window / door contact (1 = open) | Open_Close_Status |
| `ZN-Perimeter_bot_ZN_4/ZN-MRT` | sensor | next_gen | energyplus | degC | radiant_temperature | Mean radiant temperature (globe thermometer) | Radiant_Temperature_Sensor |
| `ZN-Perimeter_bot_ZN_4/ZN-OPT` | sensor | next_gen | energyplus | degC | zone_temperature | Operative temperature (comfort station) | Operative_Temperature |
| `ZN-Perimeter_bot_ZN_4/PMV` | sensor | next_gen | energyplus | - | comfort_index | Predicted mean vote, ISO 7730 (comfort station) |  |
| `ZN-Perimeter_bot_ZN_4/PPD` | sensor | next_gen | energyplus | % | comfort_ppd | Predicted percentage dissatisfied, ISO 7730 (comfort station) |  |
| `ZN-Perimeter_bot_ZN_4/TS-VOTE` | sensor | next_gen | model | - | ideal | Mean thermal-sensation vote of occupants, last hour (feedback app, -3..+3) |  |
| `ZN-Perimeter_bot_ZN_4/HOT-CALLS` | sensor | next_gen | model | count | ideal | Too-hot complaints today (work orders / app) |  |
| `ZN-Perimeter_bot_ZN_4/COLD-CALLS` | sensor | next_gen | model | count | ideal | Too-cold complaints today (work orders / app) |  |
| `ZN-Perimeter_bot_ZN_4/ZN-PM25` | sensor | next_gen | model | ug/m3 | pm_sensor | Zone PM2.5 (optical particle sensor) | PM2.5_Sensor |
| `ZN-Perimeter_bot_ZN_4/ZN-PM10` | sensor | next_gen | model | ug/m3 | pm_sensor | Zone PM10 (optical particle sensor) | PM10_Sensor |
| `ZN-Perimeter_bot_ZN_4/ZN-TVOC` | sensor | next_gen | model | ug/m3 | tvoc_sensor | Zone total VOC (metal-oxide sensor) | TVOC_Sensor |
| `ZN-Perimeter_bot_ZN_4/ZN-LUX` | sensor | advanced | model | lux | illuminance | Work-plane illuminance (daylight-harvesting photosensor) | Illuminance_Sensor |
| `ZN-Perimeter_bot_ZN_4/DAYLIGHT-LUX` | truth | truth | model | lux |  | Daylight share of the work-plane illuminance (ground truth only) |  |
| `ZN-Perimeter_bot_ZN_4/LIGHT-LVL` | sensor | advanced | model | % | percent | Lighting level (networked lighting controls) |  |
| `ZN-Perimeter_bot_ZN_4/ZN-DBA` | sensor | next_gen | model | dBA | sound | Background sound level (class-2 sound level meter) |  |
| `ZN-Perimeter_bot_ZN_4/LIGHT-KW` | meter | advanced | energyplus | kW | power | Zone lighting power (lighting panel sub-meter) | Electric_Power_Sensor |
| `ZN-Perimeter_bot_ZN_4/PLUG-KW` | meter | next_gen | energyplus | kW | power | Zone plug load power (circuit-level sub-meter) | Electric_Power_Sensor |
| `ZN-Perimeter_bot_ZN_4/INFIL-ACH` | truth | truth | energyplus | 1/h |  | Infiltration air-change rate (ground truth only) |  |
| `ZN-Perimeter_bot_ZN_4/WIN-SOL-KW` | truth | truth | energyplus | kW |  | Transmitted solar gain (ground truth only) |  |
| `ZN-Perimeter_bot_ZN_4/WIN-Q-KW` | truth | truth | energyplus | kW |  | Window heat gain (ground truth only) |  |
| `ZN-Perimeter_bot_ZN_4/INT-GAIN-KW` | truth | truth | energyplus | kW |  | Total internal heat gain (ground truth only) |  |
| `ZN-Perimeter_bot_ZN_4/SYS-CLG-KW` | truth | truth | energyplus | kW |  | Sensible cooling delivered to the zone (ground truth only) |  |
| `ZN-Perimeter_bot_ZN_4/SYS-HTG-KW` | truth | truth | energyplus | kW |  | Sensible heating delivered to the zone (ground truth only) |  |
| `ZN-Perimeter_bot_ZN_4/HTG-SP` | setpoint | standard | bas | degC |  | Active heating set point | Zone_Air_Heating_Temperature_Setpoint |
| `ZN-Perimeter_bot_ZN_4/CLG-SP` | setpoint | standard | bas | degC |  | Active cooling set point | Zone_Air_Cooling_Temperature_Setpoint |
| `ZN-Perimeter_bot_ZN_4/OCC-HTG-SP` | setpoint | standard | bas | degC |  | Occupied heating set point | Occupied_Air_Temperature_Heating_Setpoint |
| `ZN-Perimeter_bot_ZN_4/OCC-CLG-SP` | setpoint | standard | bas | degC |  | Occupied cooling set point | Occupied_Air_Temperature_Cooling_Setpoint |
| `ZN-Perimeter_bot_ZN_4/OCC-MODE` | status | standard | bas | - |  | Zone occupancy mode (1 occupied / 0 unoccupied) | Occupancy_Status |
| `ZN-Perimeter_bot_ZN_4/ZN-T-ADJ` | setpoint | standard | bas | K |  | Occupant set-point adjustment (wall sensor slider, +/-) | Temperature_Adjust_Sensor |

## VAV-Perimeter_bot_ZN_4 - VAV

VAV terminal with hot-water reheat serving Perimeter_bot_ZN_4

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `VAV-Perimeter_bot_ZN_4/DA-F` | sensor | standard | energyplus | m3/s | air_flow | Discharge air flow | Discharge_Air_Flow_Sensor |
| `VAV-Perimeter_bot_ZN_4/DA-T` | sensor | standard | energyplus | degC | air_temperature | Discharge air temperature | Discharge_Air_Temperature_Sensor |
| `VAV-Perimeter_bot_ZN_4/DMPR-POS` | sensor | advanced | energyplus | % | position | Damper position feedback | Damper_Position_Sensor |
| `VAV-Perimeter_bot_ZN_4/DA-VP` | sensor | advanced | surrogate | Pa | pressure | Flow-cross velocity pressure (airflow transducer) | Velocity_Pressure_Sensor |
| `VAV-Perimeter_bot_ZN_4/RHV-POS` | sensor | advanced | energyplus | % | position | Reheat valve position (feedback) | Valve_Position_Sensor |
| `VAV-Perimeter_bot_ZN_4/RH-Q` | truth | truth | energyplus | kW |  | Reheat coil heat rate (ground truth) |  |
| `VAV-Perimeter_bot_ZN_4/RH-BTU` | sensor | next_gen | energyplus | kW | thermal_power | Reheat coil BTU meter (water-side heat rate) | Thermal_Power_Sensor |
| `VAV-Perimeter_bot_ZN_4/RH-WF` | sensor | next_gen | energyplus | L/s | water_flow | Reheat coil water flow | Water_Flow_Sensor |
| `VAV-Perimeter_bot_ZN_4/ZN-MODE` | status | standard | bas | - |  | Terminal control state (0 deadband, 1 cooling, 2 heating) | Mode_Status |
| `VAV-Perimeter_bot_ZN_4/CLG-REQ` | virtual | standard | bas | count |  | Cooling SAT-reset requests (G36) |  |
| `VAV-Perimeter_bot_ZN_4/PRS-REQ` | virtual | standard | bas | count |  | Static-pressure reset requests (G36) |  |
| `VAV-Perimeter_bot_ZN_4/HW-REQ` | virtual | standard | bas | count |  | Hot-water reset requests (G36) |  |
| `VAV-Perimeter_bot_ZN_4/LOW-FLOW-ALM` | status | standard | bas | - |  | Low airflow alarm (G36: flow < 70 % of set point for 5 min) | Low_Air_Flow_Alarm |
| `VAV-Perimeter_bot_ZN_4/DA-F-SP` | setpoint | standard | bas | m3/s |  | Discharge air flow set point | Discharge_Air_Flow_Setpoint |
| `VAV-Perimeter_bot_ZN_4/DMPR-CMD` | command | standard | bas | % |  | Damper command | Damper_Position_Command |
| `VAV-Perimeter_bot_ZN_4/CLG-LOOP` | virtual | standard | bas | % |  | Cooling loop output |  |
| `VAV-Perimeter_bot_ZN_4/HTG-LOOP` | virtual | standard | bas | % |  | Heating loop output |  |

## ZN-Perimeter_mid_ZN_1 - Zone

Thermal zone Perimeter_mid_ZN_1 (x10 floors)

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `ZN-Perimeter_mid_ZN_1/ZN-T` | sensor | standard | energyplus | degC | zone_temperature | Zone air temperature | Zone_Air_Temperature_Sensor |
| `ZN-Perimeter_mid_ZN_1/ZN-RH` | sensor | advanced | energyplus | %RH | humidity | Zone air relative humidity | Zone_Air_Humidity_Sensor |
| `ZN-Perimeter_mid_ZN_1/ZN-DP` | sensor | advanced | energyplus | degC | air_temperature | Zone air dew-point temperature (calculated by T/RH transmitter) | Dewpoint_Sensor |
| `ZN-Perimeter_mid_ZN_1/ZN-CO2` | sensor | standard | energyplus | ppm | co2 | Zone CO2 concentration (NDIR) | CO2_Sensor |
| `ZN-Perimeter_mid_ZN_1/ZN-OCC` | sensor | standard | energyplus | - | occupancy | Zone occupancy sensor (PIR) | Occupancy_Sensor |
| `ZN-Perimeter_mid_ZN_1/OCCUPANTS` | truth | truth | energyplus | people |  | True number of occupants (ground truth only) | Occupancy_Count_Sensor |
| `ZN-Perimeter_mid_ZN_1/OCC-COUNT` | sensor | next_gen | model | people | people_count | People counter (camera / thermopile) | Occupancy_Count_Sensor |
| `ZN-Perimeter_mid_ZN_1/WIN-STS` | sensor | advanced | model | - | binary | Window / door contact (1 = open) | Open_Close_Status |
| `ZN-Perimeter_mid_ZN_1/ZN-MRT` | sensor | next_gen | energyplus | degC | radiant_temperature | Mean radiant temperature (globe thermometer) | Radiant_Temperature_Sensor |
| `ZN-Perimeter_mid_ZN_1/ZN-OPT` | sensor | next_gen | energyplus | degC | zone_temperature | Operative temperature (comfort station) | Operative_Temperature |
| `ZN-Perimeter_mid_ZN_1/PMV` | sensor | next_gen | energyplus | - | comfort_index | Predicted mean vote, ISO 7730 (comfort station) |  |
| `ZN-Perimeter_mid_ZN_1/PPD` | sensor | next_gen | energyplus | % | comfort_ppd | Predicted percentage dissatisfied, ISO 7730 (comfort station) |  |
| `ZN-Perimeter_mid_ZN_1/TS-VOTE` | sensor | next_gen | model | - | ideal | Mean thermal-sensation vote of occupants, last hour (feedback app, -3..+3) |  |
| `ZN-Perimeter_mid_ZN_1/HOT-CALLS` | sensor | next_gen | model | count | ideal | Too-hot complaints today (work orders / app) |  |
| `ZN-Perimeter_mid_ZN_1/COLD-CALLS` | sensor | next_gen | model | count | ideal | Too-cold complaints today (work orders / app) |  |
| `ZN-Perimeter_mid_ZN_1/ZN-PM25` | sensor | next_gen | model | ug/m3 | pm_sensor | Zone PM2.5 (optical particle sensor) | PM2.5_Sensor |
| `ZN-Perimeter_mid_ZN_1/ZN-PM10` | sensor | next_gen | model | ug/m3 | pm_sensor | Zone PM10 (optical particle sensor) | PM10_Sensor |
| `ZN-Perimeter_mid_ZN_1/ZN-TVOC` | sensor | next_gen | model | ug/m3 | tvoc_sensor | Zone total VOC (metal-oxide sensor) | TVOC_Sensor |
| `ZN-Perimeter_mid_ZN_1/ZN-LUX` | sensor | advanced | model | lux | illuminance | Work-plane illuminance (daylight-harvesting photosensor) | Illuminance_Sensor |
| `ZN-Perimeter_mid_ZN_1/DAYLIGHT-LUX` | truth | truth | model | lux |  | Daylight share of the work-plane illuminance (ground truth only) |  |
| `ZN-Perimeter_mid_ZN_1/LIGHT-LVL` | sensor | advanced | model | % | percent | Lighting level (networked lighting controls) |  |
| `ZN-Perimeter_mid_ZN_1/ZN-DBA` | sensor | next_gen | model | dBA | sound | Background sound level (class-2 sound level meter) |  |
| `ZN-Perimeter_mid_ZN_1/LIGHT-KW` | meter | advanced | energyplus | kW | power | Zone lighting power (lighting panel sub-meter) | Electric_Power_Sensor |
| `ZN-Perimeter_mid_ZN_1/PLUG-KW` | meter | next_gen | energyplus | kW | power | Zone plug load power (circuit-level sub-meter) | Electric_Power_Sensor |
| `ZN-Perimeter_mid_ZN_1/INFIL-ACH` | truth | truth | energyplus | 1/h |  | Infiltration air-change rate (ground truth only) |  |
| `ZN-Perimeter_mid_ZN_1/WIN-SOL-KW` | truth | truth | energyplus | kW |  | Transmitted solar gain (ground truth only) |  |
| `ZN-Perimeter_mid_ZN_1/WIN-Q-KW` | truth | truth | energyplus | kW |  | Window heat gain (ground truth only) |  |
| `ZN-Perimeter_mid_ZN_1/INT-GAIN-KW` | truth | truth | energyplus | kW |  | Total internal heat gain (ground truth only) |  |
| `ZN-Perimeter_mid_ZN_1/SYS-CLG-KW` | truth | truth | energyplus | kW |  | Sensible cooling delivered to the zone (ground truth only) |  |
| `ZN-Perimeter_mid_ZN_1/SYS-HTG-KW` | truth | truth | energyplus | kW |  | Sensible heating delivered to the zone (ground truth only) |  |
| `ZN-Perimeter_mid_ZN_1/HTG-SP` | setpoint | standard | bas | degC |  | Active heating set point | Zone_Air_Heating_Temperature_Setpoint |
| `ZN-Perimeter_mid_ZN_1/CLG-SP` | setpoint | standard | bas | degC |  | Active cooling set point | Zone_Air_Cooling_Temperature_Setpoint |
| `ZN-Perimeter_mid_ZN_1/OCC-HTG-SP` | setpoint | standard | bas | degC |  | Occupied heating set point | Occupied_Air_Temperature_Heating_Setpoint |
| `ZN-Perimeter_mid_ZN_1/OCC-CLG-SP` | setpoint | standard | bas | degC |  | Occupied cooling set point | Occupied_Air_Temperature_Cooling_Setpoint |
| `ZN-Perimeter_mid_ZN_1/OCC-MODE` | status | standard | bas | - |  | Zone occupancy mode (1 occupied / 0 unoccupied) | Occupancy_Status |
| `ZN-Perimeter_mid_ZN_1/ZN-T-ADJ` | setpoint | standard | bas | K |  | Occupant set-point adjustment (wall sensor slider, +/-) | Temperature_Adjust_Sensor |

## VAV-Perimeter_mid_ZN_1 - VAV

VAV terminal with hot-water reheat serving Perimeter_mid_ZN_1

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `VAV-Perimeter_mid_ZN_1/DA-F` | sensor | standard | energyplus | m3/s | air_flow | Discharge air flow | Discharge_Air_Flow_Sensor |
| `VAV-Perimeter_mid_ZN_1/DA-T` | sensor | standard | energyplus | degC | air_temperature | Discharge air temperature | Discharge_Air_Temperature_Sensor |
| `VAV-Perimeter_mid_ZN_1/DMPR-POS` | sensor | advanced | energyplus | % | position | Damper position feedback | Damper_Position_Sensor |
| `VAV-Perimeter_mid_ZN_1/DA-VP` | sensor | advanced | surrogate | Pa | pressure | Flow-cross velocity pressure (airflow transducer) | Velocity_Pressure_Sensor |
| `VAV-Perimeter_mid_ZN_1/RHV-POS` | sensor | advanced | energyplus | % | position | Reheat valve position (feedback) | Valve_Position_Sensor |
| `VAV-Perimeter_mid_ZN_1/RH-Q` | truth | truth | energyplus | kW |  | Reheat coil heat rate (ground truth) |  |
| `VAV-Perimeter_mid_ZN_1/RH-BTU` | sensor | next_gen | energyplus | kW | thermal_power | Reheat coil BTU meter (water-side heat rate) | Thermal_Power_Sensor |
| `VAV-Perimeter_mid_ZN_1/RH-WF` | sensor | next_gen | energyplus | L/s | water_flow | Reheat coil water flow | Water_Flow_Sensor |
| `VAV-Perimeter_mid_ZN_1/ZN-MODE` | status | standard | bas | - |  | Terminal control state (0 deadband, 1 cooling, 2 heating) | Mode_Status |
| `VAV-Perimeter_mid_ZN_1/CLG-REQ` | virtual | standard | bas | count |  | Cooling SAT-reset requests (G36) |  |
| `VAV-Perimeter_mid_ZN_1/PRS-REQ` | virtual | standard | bas | count |  | Static-pressure reset requests (G36) |  |
| `VAV-Perimeter_mid_ZN_1/HW-REQ` | virtual | standard | bas | count |  | Hot-water reset requests (G36) |  |
| `VAV-Perimeter_mid_ZN_1/LOW-FLOW-ALM` | status | standard | bas | - |  | Low airflow alarm (G36: flow < 70 % of set point for 5 min) | Low_Air_Flow_Alarm |
| `VAV-Perimeter_mid_ZN_1/DA-F-SP` | setpoint | standard | bas | m3/s |  | Discharge air flow set point | Discharge_Air_Flow_Setpoint |
| `VAV-Perimeter_mid_ZN_1/DMPR-CMD` | command | standard | bas | % |  | Damper command | Damper_Position_Command |
| `VAV-Perimeter_mid_ZN_1/CLG-LOOP` | virtual | standard | bas | % |  | Cooling loop output |  |
| `VAV-Perimeter_mid_ZN_1/HTG-LOOP` | virtual | standard | bas | % |  | Heating loop output |  |

## ZN-Perimeter_mid_ZN_2 - Zone

Thermal zone Perimeter_mid_ZN_2 (x10 floors)

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `ZN-Perimeter_mid_ZN_2/ZN-T` | sensor | standard | energyplus | degC | zone_temperature | Zone air temperature | Zone_Air_Temperature_Sensor |
| `ZN-Perimeter_mid_ZN_2/ZN-RH` | sensor | advanced | energyplus | %RH | humidity | Zone air relative humidity | Zone_Air_Humidity_Sensor |
| `ZN-Perimeter_mid_ZN_2/ZN-DP` | sensor | advanced | energyplus | degC | air_temperature | Zone air dew-point temperature (calculated by T/RH transmitter) | Dewpoint_Sensor |
| `ZN-Perimeter_mid_ZN_2/ZN-CO2` | sensor | standard | energyplus | ppm | co2 | Zone CO2 concentration (NDIR) | CO2_Sensor |
| `ZN-Perimeter_mid_ZN_2/ZN-OCC` | sensor | standard | energyplus | - | occupancy | Zone occupancy sensor (PIR) | Occupancy_Sensor |
| `ZN-Perimeter_mid_ZN_2/OCCUPANTS` | truth | truth | energyplus | people |  | True number of occupants (ground truth only) | Occupancy_Count_Sensor |
| `ZN-Perimeter_mid_ZN_2/OCC-COUNT` | sensor | next_gen | model | people | people_count | People counter (camera / thermopile) | Occupancy_Count_Sensor |
| `ZN-Perimeter_mid_ZN_2/WIN-STS` | sensor | advanced | model | - | binary | Window / door contact (1 = open) | Open_Close_Status |
| `ZN-Perimeter_mid_ZN_2/ZN-MRT` | sensor | next_gen | energyplus | degC | radiant_temperature | Mean radiant temperature (globe thermometer) | Radiant_Temperature_Sensor |
| `ZN-Perimeter_mid_ZN_2/ZN-OPT` | sensor | next_gen | energyplus | degC | zone_temperature | Operative temperature (comfort station) | Operative_Temperature |
| `ZN-Perimeter_mid_ZN_2/PMV` | sensor | next_gen | energyplus | - | comfort_index | Predicted mean vote, ISO 7730 (comfort station) |  |
| `ZN-Perimeter_mid_ZN_2/PPD` | sensor | next_gen | energyplus | % | comfort_ppd | Predicted percentage dissatisfied, ISO 7730 (comfort station) |  |
| `ZN-Perimeter_mid_ZN_2/TS-VOTE` | sensor | next_gen | model | - | ideal | Mean thermal-sensation vote of occupants, last hour (feedback app, -3..+3) |  |
| `ZN-Perimeter_mid_ZN_2/HOT-CALLS` | sensor | next_gen | model | count | ideal | Too-hot complaints today (work orders / app) |  |
| `ZN-Perimeter_mid_ZN_2/COLD-CALLS` | sensor | next_gen | model | count | ideal | Too-cold complaints today (work orders / app) |  |
| `ZN-Perimeter_mid_ZN_2/ZN-PM25` | sensor | next_gen | model | ug/m3 | pm_sensor | Zone PM2.5 (optical particle sensor) | PM2.5_Sensor |
| `ZN-Perimeter_mid_ZN_2/ZN-PM10` | sensor | next_gen | model | ug/m3 | pm_sensor | Zone PM10 (optical particle sensor) | PM10_Sensor |
| `ZN-Perimeter_mid_ZN_2/ZN-TVOC` | sensor | next_gen | model | ug/m3 | tvoc_sensor | Zone total VOC (metal-oxide sensor) | TVOC_Sensor |
| `ZN-Perimeter_mid_ZN_2/ZN-LUX` | sensor | advanced | model | lux | illuminance | Work-plane illuminance (daylight-harvesting photosensor) | Illuminance_Sensor |
| `ZN-Perimeter_mid_ZN_2/DAYLIGHT-LUX` | truth | truth | model | lux |  | Daylight share of the work-plane illuminance (ground truth only) |  |
| `ZN-Perimeter_mid_ZN_2/LIGHT-LVL` | sensor | advanced | model | % | percent | Lighting level (networked lighting controls) |  |
| `ZN-Perimeter_mid_ZN_2/ZN-DBA` | sensor | next_gen | model | dBA | sound | Background sound level (class-2 sound level meter) |  |
| `ZN-Perimeter_mid_ZN_2/LIGHT-KW` | meter | advanced | energyplus | kW | power | Zone lighting power (lighting panel sub-meter) | Electric_Power_Sensor |
| `ZN-Perimeter_mid_ZN_2/PLUG-KW` | meter | next_gen | energyplus | kW | power | Zone plug load power (circuit-level sub-meter) | Electric_Power_Sensor |
| `ZN-Perimeter_mid_ZN_2/INFIL-ACH` | truth | truth | energyplus | 1/h |  | Infiltration air-change rate (ground truth only) |  |
| `ZN-Perimeter_mid_ZN_2/WIN-SOL-KW` | truth | truth | energyplus | kW |  | Transmitted solar gain (ground truth only) |  |
| `ZN-Perimeter_mid_ZN_2/WIN-Q-KW` | truth | truth | energyplus | kW |  | Window heat gain (ground truth only) |  |
| `ZN-Perimeter_mid_ZN_2/INT-GAIN-KW` | truth | truth | energyplus | kW |  | Total internal heat gain (ground truth only) |  |
| `ZN-Perimeter_mid_ZN_2/SYS-CLG-KW` | truth | truth | energyplus | kW |  | Sensible cooling delivered to the zone (ground truth only) |  |
| `ZN-Perimeter_mid_ZN_2/SYS-HTG-KW` | truth | truth | energyplus | kW |  | Sensible heating delivered to the zone (ground truth only) |  |
| `ZN-Perimeter_mid_ZN_2/HTG-SP` | setpoint | standard | bas | degC |  | Active heating set point | Zone_Air_Heating_Temperature_Setpoint |
| `ZN-Perimeter_mid_ZN_2/CLG-SP` | setpoint | standard | bas | degC |  | Active cooling set point | Zone_Air_Cooling_Temperature_Setpoint |
| `ZN-Perimeter_mid_ZN_2/OCC-HTG-SP` | setpoint | standard | bas | degC |  | Occupied heating set point | Occupied_Air_Temperature_Heating_Setpoint |
| `ZN-Perimeter_mid_ZN_2/OCC-CLG-SP` | setpoint | standard | bas | degC |  | Occupied cooling set point | Occupied_Air_Temperature_Cooling_Setpoint |
| `ZN-Perimeter_mid_ZN_2/OCC-MODE` | status | standard | bas | - |  | Zone occupancy mode (1 occupied / 0 unoccupied) | Occupancy_Status |
| `ZN-Perimeter_mid_ZN_2/ZN-T-ADJ` | setpoint | standard | bas | K |  | Occupant set-point adjustment (wall sensor slider, +/-) | Temperature_Adjust_Sensor |

## VAV-Perimeter_mid_ZN_2 - VAV

VAV terminal with hot-water reheat serving Perimeter_mid_ZN_2

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `VAV-Perimeter_mid_ZN_2/DA-F` | sensor | standard | energyplus | m3/s | air_flow | Discharge air flow | Discharge_Air_Flow_Sensor |
| `VAV-Perimeter_mid_ZN_2/DA-T` | sensor | standard | energyplus | degC | air_temperature | Discharge air temperature | Discharge_Air_Temperature_Sensor |
| `VAV-Perimeter_mid_ZN_2/DMPR-POS` | sensor | advanced | energyplus | % | position | Damper position feedback | Damper_Position_Sensor |
| `VAV-Perimeter_mid_ZN_2/DA-VP` | sensor | advanced | surrogate | Pa | pressure | Flow-cross velocity pressure (airflow transducer) | Velocity_Pressure_Sensor |
| `VAV-Perimeter_mid_ZN_2/RHV-POS` | sensor | advanced | energyplus | % | position | Reheat valve position (feedback) | Valve_Position_Sensor |
| `VAV-Perimeter_mid_ZN_2/RH-Q` | truth | truth | energyplus | kW |  | Reheat coil heat rate (ground truth) |  |
| `VAV-Perimeter_mid_ZN_2/RH-BTU` | sensor | next_gen | energyplus | kW | thermal_power | Reheat coil BTU meter (water-side heat rate) | Thermal_Power_Sensor |
| `VAV-Perimeter_mid_ZN_2/RH-WF` | sensor | next_gen | energyplus | L/s | water_flow | Reheat coil water flow | Water_Flow_Sensor |
| `VAV-Perimeter_mid_ZN_2/ZN-MODE` | status | standard | bas | - |  | Terminal control state (0 deadband, 1 cooling, 2 heating) | Mode_Status |
| `VAV-Perimeter_mid_ZN_2/CLG-REQ` | virtual | standard | bas | count |  | Cooling SAT-reset requests (G36) |  |
| `VAV-Perimeter_mid_ZN_2/PRS-REQ` | virtual | standard | bas | count |  | Static-pressure reset requests (G36) |  |
| `VAV-Perimeter_mid_ZN_2/HW-REQ` | virtual | standard | bas | count |  | Hot-water reset requests (G36) |  |
| `VAV-Perimeter_mid_ZN_2/LOW-FLOW-ALM` | status | standard | bas | - |  | Low airflow alarm (G36: flow < 70 % of set point for 5 min) | Low_Air_Flow_Alarm |
| `VAV-Perimeter_mid_ZN_2/DA-F-SP` | setpoint | standard | bas | m3/s |  | Discharge air flow set point | Discharge_Air_Flow_Setpoint |
| `VAV-Perimeter_mid_ZN_2/DMPR-CMD` | command | standard | bas | % |  | Damper command | Damper_Position_Command |
| `VAV-Perimeter_mid_ZN_2/CLG-LOOP` | virtual | standard | bas | % |  | Cooling loop output |  |
| `VAV-Perimeter_mid_ZN_2/HTG-LOOP` | virtual | standard | bas | % |  | Heating loop output |  |

## ZN-Perimeter_mid_ZN_3 - Zone

Thermal zone Perimeter_mid_ZN_3 (x10 floors)

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `ZN-Perimeter_mid_ZN_3/ZN-T` | sensor | standard | energyplus | degC | zone_temperature | Zone air temperature | Zone_Air_Temperature_Sensor |
| `ZN-Perimeter_mid_ZN_3/ZN-RH` | sensor | advanced | energyplus | %RH | humidity | Zone air relative humidity | Zone_Air_Humidity_Sensor |
| `ZN-Perimeter_mid_ZN_3/ZN-DP` | sensor | advanced | energyplus | degC | air_temperature | Zone air dew-point temperature (calculated by T/RH transmitter) | Dewpoint_Sensor |
| `ZN-Perimeter_mid_ZN_3/ZN-CO2` | sensor | standard | energyplus | ppm | co2 | Zone CO2 concentration (NDIR) | CO2_Sensor |
| `ZN-Perimeter_mid_ZN_3/ZN-OCC` | sensor | standard | energyplus | - | occupancy | Zone occupancy sensor (PIR) | Occupancy_Sensor |
| `ZN-Perimeter_mid_ZN_3/OCCUPANTS` | truth | truth | energyplus | people |  | True number of occupants (ground truth only) | Occupancy_Count_Sensor |
| `ZN-Perimeter_mid_ZN_3/OCC-COUNT` | sensor | next_gen | model | people | people_count | People counter (camera / thermopile) | Occupancy_Count_Sensor |
| `ZN-Perimeter_mid_ZN_3/WIN-STS` | sensor | advanced | model | - | binary | Window / door contact (1 = open) | Open_Close_Status |
| `ZN-Perimeter_mid_ZN_3/ZN-MRT` | sensor | next_gen | energyplus | degC | radiant_temperature | Mean radiant temperature (globe thermometer) | Radiant_Temperature_Sensor |
| `ZN-Perimeter_mid_ZN_3/ZN-OPT` | sensor | next_gen | energyplus | degC | zone_temperature | Operative temperature (comfort station) | Operative_Temperature |
| `ZN-Perimeter_mid_ZN_3/PMV` | sensor | next_gen | energyplus | - | comfort_index | Predicted mean vote, ISO 7730 (comfort station) |  |
| `ZN-Perimeter_mid_ZN_3/PPD` | sensor | next_gen | energyplus | % | comfort_ppd | Predicted percentage dissatisfied, ISO 7730 (comfort station) |  |
| `ZN-Perimeter_mid_ZN_3/TS-VOTE` | sensor | next_gen | model | - | ideal | Mean thermal-sensation vote of occupants, last hour (feedback app, -3..+3) |  |
| `ZN-Perimeter_mid_ZN_3/HOT-CALLS` | sensor | next_gen | model | count | ideal | Too-hot complaints today (work orders / app) |  |
| `ZN-Perimeter_mid_ZN_3/COLD-CALLS` | sensor | next_gen | model | count | ideal | Too-cold complaints today (work orders / app) |  |
| `ZN-Perimeter_mid_ZN_3/ZN-PM25` | sensor | next_gen | model | ug/m3 | pm_sensor | Zone PM2.5 (optical particle sensor) | PM2.5_Sensor |
| `ZN-Perimeter_mid_ZN_3/ZN-PM10` | sensor | next_gen | model | ug/m3 | pm_sensor | Zone PM10 (optical particle sensor) | PM10_Sensor |
| `ZN-Perimeter_mid_ZN_3/ZN-TVOC` | sensor | next_gen | model | ug/m3 | tvoc_sensor | Zone total VOC (metal-oxide sensor) | TVOC_Sensor |
| `ZN-Perimeter_mid_ZN_3/ZN-LUX` | sensor | advanced | model | lux | illuminance | Work-plane illuminance (daylight-harvesting photosensor) | Illuminance_Sensor |
| `ZN-Perimeter_mid_ZN_3/DAYLIGHT-LUX` | truth | truth | model | lux |  | Daylight share of the work-plane illuminance (ground truth only) |  |
| `ZN-Perimeter_mid_ZN_3/LIGHT-LVL` | sensor | advanced | model | % | percent | Lighting level (networked lighting controls) |  |
| `ZN-Perimeter_mid_ZN_3/ZN-DBA` | sensor | next_gen | model | dBA | sound | Background sound level (class-2 sound level meter) |  |
| `ZN-Perimeter_mid_ZN_3/LIGHT-KW` | meter | advanced | energyplus | kW | power | Zone lighting power (lighting panel sub-meter) | Electric_Power_Sensor |
| `ZN-Perimeter_mid_ZN_3/PLUG-KW` | meter | next_gen | energyplus | kW | power | Zone plug load power (circuit-level sub-meter) | Electric_Power_Sensor |
| `ZN-Perimeter_mid_ZN_3/INFIL-ACH` | truth | truth | energyplus | 1/h |  | Infiltration air-change rate (ground truth only) |  |
| `ZN-Perimeter_mid_ZN_3/WIN-SOL-KW` | truth | truth | energyplus | kW |  | Transmitted solar gain (ground truth only) |  |
| `ZN-Perimeter_mid_ZN_3/WIN-Q-KW` | truth | truth | energyplus | kW |  | Window heat gain (ground truth only) |  |
| `ZN-Perimeter_mid_ZN_3/INT-GAIN-KW` | truth | truth | energyplus | kW |  | Total internal heat gain (ground truth only) |  |
| `ZN-Perimeter_mid_ZN_3/SYS-CLG-KW` | truth | truth | energyplus | kW |  | Sensible cooling delivered to the zone (ground truth only) |  |
| `ZN-Perimeter_mid_ZN_3/SYS-HTG-KW` | truth | truth | energyplus | kW |  | Sensible heating delivered to the zone (ground truth only) |  |
| `ZN-Perimeter_mid_ZN_3/HTG-SP` | setpoint | standard | bas | degC |  | Active heating set point | Zone_Air_Heating_Temperature_Setpoint |
| `ZN-Perimeter_mid_ZN_3/CLG-SP` | setpoint | standard | bas | degC |  | Active cooling set point | Zone_Air_Cooling_Temperature_Setpoint |
| `ZN-Perimeter_mid_ZN_3/OCC-HTG-SP` | setpoint | standard | bas | degC |  | Occupied heating set point | Occupied_Air_Temperature_Heating_Setpoint |
| `ZN-Perimeter_mid_ZN_3/OCC-CLG-SP` | setpoint | standard | bas | degC |  | Occupied cooling set point | Occupied_Air_Temperature_Cooling_Setpoint |
| `ZN-Perimeter_mid_ZN_3/OCC-MODE` | status | standard | bas | - |  | Zone occupancy mode (1 occupied / 0 unoccupied) | Occupancy_Status |
| `ZN-Perimeter_mid_ZN_3/ZN-T-ADJ` | setpoint | standard | bas | K |  | Occupant set-point adjustment (wall sensor slider, +/-) | Temperature_Adjust_Sensor |

## VAV-Perimeter_mid_ZN_3 - VAV

VAV terminal with hot-water reheat serving Perimeter_mid_ZN_3

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `VAV-Perimeter_mid_ZN_3/DA-F` | sensor | standard | energyplus | m3/s | air_flow | Discharge air flow | Discharge_Air_Flow_Sensor |
| `VAV-Perimeter_mid_ZN_3/DA-T` | sensor | standard | energyplus | degC | air_temperature | Discharge air temperature | Discharge_Air_Temperature_Sensor |
| `VAV-Perimeter_mid_ZN_3/DMPR-POS` | sensor | advanced | energyplus | % | position | Damper position feedback | Damper_Position_Sensor |
| `VAV-Perimeter_mid_ZN_3/DA-VP` | sensor | advanced | surrogate | Pa | pressure | Flow-cross velocity pressure (airflow transducer) | Velocity_Pressure_Sensor |
| `VAV-Perimeter_mid_ZN_3/RHV-POS` | sensor | advanced | energyplus | % | position | Reheat valve position (feedback) | Valve_Position_Sensor |
| `VAV-Perimeter_mid_ZN_3/RH-Q` | truth | truth | energyplus | kW |  | Reheat coil heat rate (ground truth) |  |
| `VAV-Perimeter_mid_ZN_3/RH-BTU` | sensor | next_gen | energyplus | kW | thermal_power | Reheat coil BTU meter (water-side heat rate) | Thermal_Power_Sensor |
| `VAV-Perimeter_mid_ZN_3/RH-WF` | sensor | next_gen | energyplus | L/s | water_flow | Reheat coil water flow | Water_Flow_Sensor |
| `VAV-Perimeter_mid_ZN_3/ZN-MODE` | status | standard | bas | - |  | Terminal control state (0 deadband, 1 cooling, 2 heating) | Mode_Status |
| `VAV-Perimeter_mid_ZN_3/CLG-REQ` | virtual | standard | bas | count |  | Cooling SAT-reset requests (G36) |  |
| `VAV-Perimeter_mid_ZN_3/PRS-REQ` | virtual | standard | bas | count |  | Static-pressure reset requests (G36) |  |
| `VAV-Perimeter_mid_ZN_3/HW-REQ` | virtual | standard | bas | count |  | Hot-water reset requests (G36) |  |
| `VAV-Perimeter_mid_ZN_3/LOW-FLOW-ALM` | status | standard | bas | - |  | Low airflow alarm (G36: flow < 70 % of set point for 5 min) | Low_Air_Flow_Alarm |
| `VAV-Perimeter_mid_ZN_3/DA-F-SP` | setpoint | standard | bas | m3/s |  | Discharge air flow set point | Discharge_Air_Flow_Setpoint |
| `VAV-Perimeter_mid_ZN_3/DMPR-CMD` | command | standard | bas | % |  | Damper command | Damper_Position_Command |
| `VAV-Perimeter_mid_ZN_3/CLG-LOOP` | virtual | standard | bas | % |  | Cooling loop output |  |
| `VAV-Perimeter_mid_ZN_3/HTG-LOOP` | virtual | standard | bas | % |  | Heating loop output |  |

## ZN-Perimeter_mid_ZN_4 - Zone

Thermal zone Perimeter_mid_ZN_4 (x10 floors)

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `ZN-Perimeter_mid_ZN_4/ZN-T` | sensor | standard | energyplus | degC | zone_temperature | Zone air temperature | Zone_Air_Temperature_Sensor |
| `ZN-Perimeter_mid_ZN_4/ZN-RH` | sensor | advanced | energyplus | %RH | humidity | Zone air relative humidity | Zone_Air_Humidity_Sensor |
| `ZN-Perimeter_mid_ZN_4/ZN-DP` | sensor | advanced | energyplus | degC | air_temperature | Zone air dew-point temperature (calculated by T/RH transmitter) | Dewpoint_Sensor |
| `ZN-Perimeter_mid_ZN_4/ZN-CO2` | sensor | standard | energyplus | ppm | co2 | Zone CO2 concentration (NDIR) | CO2_Sensor |
| `ZN-Perimeter_mid_ZN_4/ZN-OCC` | sensor | standard | energyplus | - | occupancy | Zone occupancy sensor (PIR) | Occupancy_Sensor |
| `ZN-Perimeter_mid_ZN_4/OCCUPANTS` | truth | truth | energyplus | people |  | True number of occupants (ground truth only) | Occupancy_Count_Sensor |
| `ZN-Perimeter_mid_ZN_4/OCC-COUNT` | sensor | next_gen | model | people | people_count | People counter (camera / thermopile) | Occupancy_Count_Sensor |
| `ZN-Perimeter_mid_ZN_4/WIN-STS` | sensor | advanced | model | - | binary | Window / door contact (1 = open) | Open_Close_Status |
| `ZN-Perimeter_mid_ZN_4/ZN-MRT` | sensor | next_gen | energyplus | degC | radiant_temperature | Mean radiant temperature (globe thermometer) | Radiant_Temperature_Sensor |
| `ZN-Perimeter_mid_ZN_4/ZN-OPT` | sensor | next_gen | energyplus | degC | zone_temperature | Operative temperature (comfort station) | Operative_Temperature |
| `ZN-Perimeter_mid_ZN_4/PMV` | sensor | next_gen | energyplus | - | comfort_index | Predicted mean vote, ISO 7730 (comfort station) |  |
| `ZN-Perimeter_mid_ZN_4/PPD` | sensor | next_gen | energyplus | % | comfort_ppd | Predicted percentage dissatisfied, ISO 7730 (comfort station) |  |
| `ZN-Perimeter_mid_ZN_4/TS-VOTE` | sensor | next_gen | model | - | ideal | Mean thermal-sensation vote of occupants, last hour (feedback app, -3..+3) |  |
| `ZN-Perimeter_mid_ZN_4/HOT-CALLS` | sensor | next_gen | model | count | ideal | Too-hot complaints today (work orders / app) |  |
| `ZN-Perimeter_mid_ZN_4/COLD-CALLS` | sensor | next_gen | model | count | ideal | Too-cold complaints today (work orders / app) |  |
| `ZN-Perimeter_mid_ZN_4/ZN-PM25` | sensor | next_gen | model | ug/m3 | pm_sensor | Zone PM2.5 (optical particle sensor) | PM2.5_Sensor |
| `ZN-Perimeter_mid_ZN_4/ZN-PM10` | sensor | next_gen | model | ug/m3 | pm_sensor | Zone PM10 (optical particle sensor) | PM10_Sensor |
| `ZN-Perimeter_mid_ZN_4/ZN-TVOC` | sensor | next_gen | model | ug/m3 | tvoc_sensor | Zone total VOC (metal-oxide sensor) | TVOC_Sensor |
| `ZN-Perimeter_mid_ZN_4/ZN-LUX` | sensor | advanced | model | lux | illuminance | Work-plane illuminance (daylight-harvesting photosensor) | Illuminance_Sensor |
| `ZN-Perimeter_mid_ZN_4/DAYLIGHT-LUX` | truth | truth | model | lux |  | Daylight share of the work-plane illuminance (ground truth only) |  |
| `ZN-Perimeter_mid_ZN_4/LIGHT-LVL` | sensor | advanced | model | % | percent | Lighting level (networked lighting controls) |  |
| `ZN-Perimeter_mid_ZN_4/ZN-DBA` | sensor | next_gen | model | dBA | sound | Background sound level (class-2 sound level meter) |  |
| `ZN-Perimeter_mid_ZN_4/LIGHT-KW` | meter | advanced | energyplus | kW | power | Zone lighting power (lighting panel sub-meter) | Electric_Power_Sensor |
| `ZN-Perimeter_mid_ZN_4/PLUG-KW` | meter | next_gen | energyplus | kW | power | Zone plug load power (circuit-level sub-meter) | Electric_Power_Sensor |
| `ZN-Perimeter_mid_ZN_4/INFIL-ACH` | truth | truth | energyplus | 1/h |  | Infiltration air-change rate (ground truth only) |  |
| `ZN-Perimeter_mid_ZN_4/WIN-SOL-KW` | truth | truth | energyplus | kW |  | Transmitted solar gain (ground truth only) |  |
| `ZN-Perimeter_mid_ZN_4/WIN-Q-KW` | truth | truth | energyplus | kW |  | Window heat gain (ground truth only) |  |
| `ZN-Perimeter_mid_ZN_4/INT-GAIN-KW` | truth | truth | energyplus | kW |  | Total internal heat gain (ground truth only) |  |
| `ZN-Perimeter_mid_ZN_4/SYS-CLG-KW` | truth | truth | energyplus | kW |  | Sensible cooling delivered to the zone (ground truth only) |  |
| `ZN-Perimeter_mid_ZN_4/SYS-HTG-KW` | truth | truth | energyplus | kW |  | Sensible heating delivered to the zone (ground truth only) |  |
| `ZN-Perimeter_mid_ZN_4/HTG-SP` | setpoint | standard | bas | degC |  | Active heating set point | Zone_Air_Heating_Temperature_Setpoint |
| `ZN-Perimeter_mid_ZN_4/CLG-SP` | setpoint | standard | bas | degC |  | Active cooling set point | Zone_Air_Cooling_Temperature_Setpoint |
| `ZN-Perimeter_mid_ZN_4/OCC-HTG-SP` | setpoint | standard | bas | degC |  | Occupied heating set point | Occupied_Air_Temperature_Heating_Setpoint |
| `ZN-Perimeter_mid_ZN_4/OCC-CLG-SP` | setpoint | standard | bas | degC |  | Occupied cooling set point | Occupied_Air_Temperature_Cooling_Setpoint |
| `ZN-Perimeter_mid_ZN_4/OCC-MODE` | status | standard | bas | - |  | Zone occupancy mode (1 occupied / 0 unoccupied) | Occupancy_Status |
| `ZN-Perimeter_mid_ZN_4/ZN-T-ADJ` | setpoint | standard | bas | K |  | Occupant set-point adjustment (wall sensor slider, +/-) | Temperature_Adjust_Sensor |

## VAV-Perimeter_mid_ZN_4 - VAV

VAV terminal with hot-water reheat serving Perimeter_mid_ZN_4

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `VAV-Perimeter_mid_ZN_4/DA-F` | sensor | standard | energyplus | m3/s | air_flow | Discharge air flow | Discharge_Air_Flow_Sensor |
| `VAV-Perimeter_mid_ZN_4/DA-T` | sensor | standard | energyplus | degC | air_temperature | Discharge air temperature | Discharge_Air_Temperature_Sensor |
| `VAV-Perimeter_mid_ZN_4/DMPR-POS` | sensor | advanced | energyplus | % | position | Damper position feedback | Damper_Position_Sensor |
| `VAV-Perimeter_mid_ZN_4/DA-VP` | sensor | advanced | surrogate | Pa | pressure | Flow-cross velocity pressure (airflow transducer) | Velocity_Pressure_Sensor |
| `VAV-Perimeter_mid_ZN_4/RHV-POS` | sensor | advanced | energyplus | % | position | Reheat valve position (feedback) | Valve_Position_Sensor |
| `VAV-Perimeter_mid_ZN_4/RH-Q` | truth | truth | energyplus | kW |  | Reheat coil heat rate (ground truth) |  |
| `VAV-Perimeter_mid_ZN_4/RH-BTU` | sensor | next_gen | energyplus | kW | thermal_power | Reheat coil BTU meter (water-side heat rate) | Thermal_Power_Sensor |
| `VAV-Perimeter_mid_ZN_4/RH-WF` | sensor | next_gen | energyplus | L/s | water_flow | Reheat coil water flow | Water_Flow_Sensor |
| `VAV-Perimeter_mid_ZN_4/ZN-MODE` | status | standard | bas | - |  | Terminal control state (0 deadband, 1 cooling, 2 heating) | Mode_Status |
| `VAV-Perimeter_mid_ZN_4/CLG-REQ` | virtual | standard | bas | count |  | Cooling SAT-reset requests (G36) |  |
| `VAV-Perimeter_mid_ZN_4/PRS-REQ` | virtual | standard | bas | count |  | Static-pressure reset requests (G36) |  |
| `VAV-Perimeter_mid_ZN_4/HW-REQ` | virtual | standard | bas | count |  | Hot-water reset requests (G36) |  |
| `VAV-Perimeter_mid_ZN_4/LOW-FLOW-ALM` | status | standard | bas | - |  | Low airflow alarm (G36: flow < 70 % of set point for 5 min) | Low_Air_Flow_Alarm |
| `VAV-Perimeter_mid_ZN_4/DA-F-SP` | setpoint | standard | bas | m3/s |  | Discharge air flow set point | Discharge_Air_Flow_Setpoint |
| `VAV-Perimeter_mid_ZN_4/DMPR-CMD` | command | standard | bas | % |  | Damper command | Damper_Position_Command |
| `VAV-Perimeter_mid_ZN_4/CLG-LOOP` | virtual | standard | bas | % |  | Cooling loop output |  |
| `VAV-Perimeter_mid_ZN_4/HTG-LOOP` | virtual | standard | bas | % |  | Heating loop output |  |

## ZN-Perimeter_top_ZN_1 - Zone

Thermal zone Perimeter_top_ZN_1

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `ZN-Perimeter_top_ZN_1/ZN-T` | sensor | standard | energyplus | degC | zone_temperature | Zone air temperature | Zone_Air_Temperature_Sensor |
| `ZN-Perimeter_top_ZN_1/ZN-RH` | sensor | advanced | energyplus | %RH | humidity | Zone air relative humidity | Zone_Air_Humidity_Sensor |
| `ZN-Perimeter_top_ZN_1/ZN-DP` | sensor | advanced | energyplus | degC | air_temperature | Zone air dew-point temperature (calculated by T/RH transmitter) | Dewpoint_Sensor |
| `ZN-Perimeter_top_ZN_1/ZN-CO2` | sensor | standard | energyplus | ppm | co2 | Zone CO2 concentration (NDIR) | CO2_Sensor |
| `ZN-Perimeter_top_ZN_1/ZN-OCC` | sensor | standard | energyplus | - | occupancy | Zone occupancy sensor (PIR) | Occupancy_Sensor |
| `ZN-Perimeter_top_ZN_1/OCCUPANTS` | truth | truth | energyplus | people |  | True number of occupants (ground truth only) | Occupancy_Count_Sensor |
| `ZN-Perimeter_top_ZN_1/OCC-COUNT` | sensor | next_gen | model | people | people_count | People counter (camera / thermopile) | Occupancy_Count_Sensor |
| `ZN-Perimeter_top_ZN_1/WIN-STS` | sensor | advanced | model | - | binary | Window / door contact (1 = open) | Open_Close_Status |
| `ZN-Perimeter_top_ZN_1/ZN-MRT` | sensor | next_gen | energyplus | degC | radiant_temperature | Mean radiant temperature (globe thermometer) | Radiant_Temperature_Sensor |
| `ZN-Perimeter_top_ZN_1/ZN-OPT` | sensor | next_gen | energyplus | degC | zone_temperature | Operative temperature (comfort station) | Operative_Temperature |
| `ZN-Perimeter_top_ZN_1/PMV` | sensor | next_gen | energyplus | - | comfort_index | Predicted mean vote, ISO 7730 (comfort station) |  |
| `ZN-Perimeter_top_ZN_1/PPD` | sensor | next_gen | energyplus | % | comfort_ppd | Predicted percentage dissatisfied, ISO 7730 (comfort station) |  |
| `ZN-Perimeter_top_ZN_1/TS-VOTE` | sensor | next_gen | model | - | ideal | Mean thermal-sensation vote of occupants, last hour (feedback app, -3..+3) |  |
| `ZN-Perimeter_top_ZN_1/HOT-CALLS` | sensor | next_gen | model | count | ideal | Too-hot complaints today (work orders / app) |  |
| `ZN-Perimeter_top_ZN_1/COLD-CALLS` | sensor | next_gen | model | count | ideal | Too-cold complaints today (work orders / app) |  |
| `ZN-Perimeter_top_ZN_1/ZN-PM25` | sensor | next_gen | model | ug/m3 | pm_sensor | Zone PM2.5 (optical particle sensor) | PM2.5_Sensor |
| `ZN-Perimeter_top_ZN_1/ZN-PM10` | sensor | next_gen | model | ug/m3 | pm_sensor | Zone PM10 (optical particle sensor) | PM10_Sensor |
| `ZN-Perimeter_top_ZN_1/ZN-TVOC` | sensor | next_gen | model | ug/m3 | tvoc_sensor | Zone total VOC (metal-oxide sensor) | TVOC_Sensor |
| `ZN-Perimeter_top_ZN_1/ZN-LUX` | sensor | advanced | model | lux | illuminance | Work-plane illuminance (daylight-harvesting photosensor) | Illuminance_Sensor |
| `ZN-Perimeter_top_ZN_1/DAYLIGHT-LUX` | truth | truth | model | lux |  | Daylight share of the work-plane illuminance (ground truth only) |  |
| `ZN-Perimeter_top_ZN_1/LIGHT-LVL` | sensor | advanced | model | % | percent | Lighting level (networked lighting controls) |  |
| `ZN-Perimeter_top_ZN_1/ZN-DBA` | sensor | next_gen | model | dBA | sound | Background sound level (class-2 sound level meter) |  |
| `ZN-Perimeter_top_ZN_1/LIGHT-KW` | meter | advanced | energyplus | kW | power | Zone lighting power (lighting panel sub-meter) | Electric_Power_Sensor |
| `ZN-Perimeter_top_ZN_1/PLUG-KW` | meter | next_gen | energyplus | kW | power | Zone plug load power (circuit-level sub-meter) | Electric_Power_Sensor |
| `ZN-Perimeter_top_ZN_1/INFIL-ACH` | truth | truth | energyplus | 1/h |  | Infiltration air-change rate (ground truth only) |  |
| `ZN-Perimeter_top_ZN_1/WIN-SOL-KW` | truth | truth | energyplus | kW |  | Transmitted solar gain (ground truth only) |  |
| `ZN-Perimeter_top_ZN_1/WIN-Q-KW` | truth | truth | energyplus | kW |  | Window heat gain (ground truth only) |  |
| `ZN-Perimeter_top_ZN_1/INT-GAIN-KW` | truth | truth | energyplus | kW |  | Total internal heat gain (ground truth only) |  |
| `ZN-Perimeter_top_ZN_1/SYS-CLG-KW` | truth | truth | energyplus | kW |  | Sensible cooling delivered to the zone (ground truth only) |  |
| `ZN-Perimeter_top_ZN_1/SYS-HTG-KW` | truth | truth | energyplus | kW |  | Sensible heating delivered to the zone (ground truth only) |  |
| `ZN-Perimeter_top_ZN_1/HTG-SP` | setpoint | standard | bas | degC |  | Active heating set point | Zone_Air_Heating_Temperature_Setpoint |
| `ZN-Perimeter_top_ZN_1/CLG-SP` | setpoint | standard | bas | degC |  | Active cooling set point | Zone_Air_Cooling_Temperature_Setpoint |
| `ZN-Perimeter_top_ZN_1/OCC-HTG-SP` | setpoint | standard | bas | degC |  | Occupied heating set point | Occupied_Air_Temperature_Heating_Setpoint |
| `ZN-Perimeter_top_ZN_1/OCC-CLG-SP` | setpoint | standard | bas | degC |  | Occupied cooling set point | Occupied_Air_Temperature_Cooling_Setpoint |
| `ZN-Perimeter_top_ZN_1/OCC-MODE` | status | standard | bas | - |  | Zone occupancy mode (1 occupied / 0 unoccupied) | Occupancy_Status |
| `ZN-Perimeter_top_ZN_1/ZN-T-ADJ` | setpoint | standard | bas | K |  | Occupant set-point adjustment (wall sensor slider, +/-) | Temperature_Adjust_Sensor |

## VAV-Perimeter_top_ZN_1 - VAV

VAV terminal with hot-water reheat serving Perimeter_top_ZN_1

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `VAV-Perimeter_top_ZN_1/DA-F` | sensor | standard | energyplus | m3/s | air_flow | Discharge air flow | Discharge_Air_Flow_Sensor |
| `VAV-Perimeter_top_ZN_1/DA-T` | sensor | standard | energyplus | degC | air_temperature | Discharge air temperature | Discharge_Air_Temperature_Sensor |
| `VAV-Perimeter_top_ZN_1/DMPR-POS` | sensor | advanced | energyplus | % | position | Damper position feedback | Damper_Position_Sensor |
| `VAV-Perimeter_top_ZN_1/DA-VP` | sensor | advanced | surrogate | Pa | pressure | Flow-cross velocity pressure (airflow transducer) | Velocity_Pressure_Sensor |
| `VAV-Perimeter_top_ZN_1/RHV-POS` | sensor | advanced | energyplus | % | position | Reheat valve position (feedback) | Valve_Position_Sensor |
| `VAV-Perimeter_top_ZN_1/RH-Q` | truth | truth | energyplus | kW |  | Reheat coil heat rate (ground truth) |  |
| `VAV-Perimeter_top_ZN_1/RH-BTU` | sensor | next_gen | energyplus | kW | thermal_power | Reheat coil BTU meter (water-side heat rate) | Thermal_Power_Sensor |
| `VAV-Perimeter_top_ZN_1/RH-WF` | sensor | next_gen | energyplus | L/s | water_flow | Reheat coil water flow | Water_Flow_Sensor |
| `VAV-Perimeter_top_ZN_1/ZN-MODE` | status | standard | bas | - |  | Terminal control state (0 deadband, 1 cooling, 2 heating) | Mode_Status |
| `VAV-Perimeter_top_ZN_1/CLG-REQ` | virtual | standard | bas | count |  | Cooling SAT-reset requests (G36) |  |
| `VAV-Perimeter_top_ZN_1/PRS-REQ` | virtual | standard | bas | count |  | Static-pressure reset requests (G36) |  |
| `VAV-Perimeter_top_ZN_1/HW-REQ` | virtual | standard | bas | count |  | Hot-water reset requests (G36) |  |
| `VAV-Perimeter_top_ZN_1/LOW-FLOW-ALM` | status | standard | bas | - |  | Low airflow alarm (G36: flow < 70 % of set point for 5 min) | Low_Air_Flow_Alarm |
| `VAV-Perimeter_top_ZN_1/DA-F-SP` | setpoint | standard | bas | m3/s |  | Discharge air flow set point | Discharge_Air_Flow_Setpoint |
| `VAV-Perimeter_top_ZN_1/DMPR-CMD` | command | standard | bas | % |  | Damper command | Damper_Position_Command |
| `VAV-Perimeter_top_ZN_1/CLG-LOOP` | virtual | standard | bas | % |  | Cooling loop output |  |
| `VAV-Perimeter_top_ZN_1/HTG-LOOP` | virtual | standard | bas | % |  | Heating loop output |  |

## ZN-Perimeter_top_ZN_2 - Zone

Thermal zone Perimeter_top_ZN_2

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `ZN-Perimeter_top_ZN_2/ZN-T` | sensor | standard | energyplus | degC | zone_temperature | Zone air temperature | Zone_Air_Temperature_Sensor |
| `ZN-Perimeter_top_ZN_2/ZN-RH` | sensor | advanced | energyplus | %RH | humidity | Zone air relative humidity | Zone_Air_Humidity_Sensor |
| `ZN-Perimeter_top_ZN_2/ZN-DP` | sensor | advanced | energyplus | degC | air_temperature | Zone air dew-point temperature (calculated by T/RH transmitter) | Dewpoint_Sensor |
| `ZN-Perimeter_top_ZN_2/ZN-CO2` | sensor | standard | energyplus | ppm | co2 | Zone CO2 concentration (NDIR) | CO2_Sensor |
| `ZN-Perimeter_top_ZN_2/ZN-OCC` | sensor | standard | energyplus | - | occupancy | Zone occupancy sensor (PIR) | Occupancy_Sensor |
| `ZN-Perimeter_top_ZN_2/OCCUPANTS` | truth | truth | energyplus | people |  | True number of occupants (ground truth only) | Occupancy_Count_Sensor |
| `ZN-Perimeter_top_ZN_2/OCC-COUNT` | sensor | next_gen | model | people | people_count | People counter (camera / thermopile) | Occupancy_Count_Sensor |
| `ZN-Perimeter_top_ZN_2/WIN-STS` | sensor | advanced | model | - | binary | Window / door contact (1 = open) | Open_Close_Status |
| `ZN-Perimeter_top_ZN_2/ZN-MRT` | sensor | next_gen | energyplus | degC | radiant_temperature | Mean radiant temperature (globe thermometer) | Radiant_Temperature_Sensor |
| `ZN-Perimeter_top_ZN_2/ZN-OPT` | sensor | next_gen | energyplus | degC | zone_temperature | Operative temperature (comfort station) | Operative_Temperature |
| `ZN-Perimeter_top_ZN_2/PMV` | sensor | next_gen | energyplus | - | comfort_index | Predicted mean vote, ISO 7730 (comfort station) |  |
| `ZN-Perimeter_top_ZN_2/PPD` | sensor | next_gen | energyplus | % | comfort_ppd | Predicted percentage dissatisfied, ISO 7730 (comfort station) |  |
| `ZN-Perimeter_top_ZN_2/TS-VOTE` | sensor | next_gen | model | - | ideal | Mean thermal-sensation vote of occupants, last hour (feedback app, -3..+3) |  |
| `ZN-Perimeter_top_ZN_2/HOT-CALLS` | sensor | next_gen | model | count | ideal | Too-hot complaints today (work orders / app) |  |
| `ZN-Perimeter_top_ZN_2/COLD-CALLS` | sensor | next_gen | model | count | ideal | Too-cold complaints today (work orders / app) |  |
| `ZN-Perimeter_top_ZN_2/ZN-PM25` | sensor | next_gen | model | ug/m3 | pm_sensor | Zone PM2.5 (optical particle sensor) | PM2.5_Sensor |
| `ZN-Perimeter_top_ZN_2/ZN-PM10` | sensor | next_gen | model | ug/m3 | pm_sensor | Zone PM10 (optical particle sensor) | PM10_Sensor |
| `ZN-Perimeter_top_ZN_2/ZN-TVOC` | sensor | next_gen | model | ug/m3 | tvoc_sensor | Zone total VOC (metal-oxide sensor) | TVOC_Sensor |
| `ZN-Perimeter_top_ZN_2/ZN-LUX` | sensor | advanced | model | lux | illuminance | Work-plane illuminance (daylight-harvesting photosensor) | Illuminance_Sensor |
| `ZN-Perimeter_top_ZN_2/DAYLIGHT-LUX` | truth | truth | model | lux |  | Daylight share of the work-plane illuminance (ground truth only) |  |
| `ZN-Perimeter_top_ZN_2/LIGHT-LVL` | sensor | advanced | model | % | percent | Lighting level (networked lighting controls) |  |
| `ZN-Perimeter_top_ZN_2/ZN-DBA` | sensor | next_gen | model | dBA | sound | Background sound level (class-2 sound level meter) |  |
| `ZN-Perimeter_top_ZN_2/LIGHT-KW` | meter | advanced | energyplus | kW | power | Zone lighting power (lighting panel sub-meter) | Electric_Power_Sensor |
| `ZN-Perimeter_top_ZN_2/PLUG-KW` | meter | next_gen | energyplus | kW | power | Zone plug load power (circuit-level sub-meter) | Electric_Power_Sensor |
| `ZN-Perimeter_top_ZN_2/INFIL-ACH` | truth | truth | energyplus | 1/h |  | Infiltration air-change rate (ground truth only) |  |
| `ZN-Perimeter_top_ZN_2/WIN-SOL-KW` | truth | truth | energyplus | kW |  | Transmitted solar gain (ground truth only) |  |
| `ZN-Perimeter_top_ZN_2/WIN-Q-KW` | truth | truth | energyplus | kW |  | Window heat gain (ground truth only) |  |
| `ZN-Perimeter_top_ZN_2/INT-GAIN-KW` | truth | truth | energyplus | kW |  | Total internal heat gain (ground truth only) |  |
| `ZN-Perimeter_top_ZN_2/SYS-CLG-KW` | truth | truth | energyplus | kW |  | Sensible cooling delivered to the zone (ground truth only) |  |
| `ZN-Perimeter_top_ZN_2/SYS-HTG-KW` | truth | truth | energyplus | kW |  | Sensible heating delivered to the zone (ground truth only) |  |
| `ZN-Perimeter_top_ZN_2/HTG-SP` | setpoint | standard | bas | degC |  | Active heating set point | Zone_Air_Heating_Temperature_Setpoint |
| `ZN-Perimeter_top_ZN_2/CLG-SP` | setpoint | standard | bas | degC |  | Active cooling set point | Zone_Air_Cooling_Temperature_Setpoint |
| `ZN-Perimeter_top_ZN_2/OCC-HTG-SP` | setpoint | standard | bas | degC |  | Occupied heating set point | Occupied_Air_Temperature_Heating_Setpoint |
| `ZN-Perimeter_top_ZN_2/OCC-CLG-SP` | setpoint | standard | bas | degC |  | Occupied cooling set point | Occupied_Air_Temperature_Cooling_Setpoint |
| `ZN-Perimeter_top_ZN_2/OCC-MODE` | status | standard | bas | - |  | Zone occupancy mode (1 occupied / 0 unoccupied) | Occupancy_Status |
| `ZN-Perimeter_top_ZN_2/ZN-T-ADJ` | setpoint | standard | bas | K |  | Occupant set-point adjustment (wall sensor slider, +/-) | Temperature_Adjust_Sensor |

## VAV-Perimeter_top_ZN_2 - VAV

VAV terminal with hot-water reheat serving Perimeter_top_ZN_2

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `VAV-Perimeter_top_ZN_2/DA-F` | sensor | standard | energyplus | m3/s | air_flow | Discharge air flow | Discharge_Air_Flow_Sensor |
| `VAV-Perimeter_top_ZN_2/DA-T` | sensor | standard | energyplus | degC | air_temperature | Discharge air temperature | Discharge_Air_Temperature_Sensor |
| `VAV-Perimeter_top_ZN_2/DMPR-POS` | sensor | advanced | energyplus | % | position | Damper position feedback | Damper_Position_Sensor |
| `VAV-Perimeter_top_ZN_2/DA-VP` | sensor | advanced | surrogate | Pa | pressure | Flow-cross velocity pressure (airflow transducer) | Velocity_Pressure_Sensor |
| `VAV-Perimeter_top_ZN_2/RHV-POS` | sensor | advanced | energyplus | % | position | Reheat valve position (feedback) | Valve_Position_Sensor |
| `VAV-Perimeter_top_ZN_2/RH-Q` | truth | truth | energyplus | kW |  | Reheat coil heat rate (ground truth) |  |
| `VAV-Perimeter_top_ZN_2/RH-BTU` | sensor | next_gen | energyplus | kW | thermal_power | Reheat coil BTU meter (water-side heat rate) | Thermal_Power_Sensor |
| `VAV-Perimeter_top_ZN_2/RH-WF` | sensor | next_gen | energyplus | L/s | water_flow | Reheat coil water flow | Water_Flow_Sensor |
| `VAV-Perimeter_top_ZN_2/ZN-MODE` | status | standard | bas | - |  | Terminal control state (0 deadband, 1 cooling, 2 heating) | Mode_Status |
| `VAV-Perimeter_top_ZN_2/CLG-REQ` | virtual | standard | bas | count |  | Cooling SAT-reset requests (G36) |  |
| `VAV-Perimeter_top_ZN_2/PRS-REQ` | virtual | standard | bas | count |  | Static-pressure reset requests (G36) |  |
| `VAV-Perimeter_top_ZN_2/HW-REQ` | virtual | standard | bas | count |  | Hot-water reset requests (G36) |  |
| `VAV-Perimeter_top_ZN_2/LOW-FLOW-ALM` | status | standard | bas | - |  | Low airflow alarm (G36: flow < 70 % of set point for 5 min) | Low_Air_Flow_Alarm |
| `VAV-Perimeter_top_ZN_2/DA-F-SP` | setpoint | standard | bas | m3/s |  | Discharge air flow set point | Discharge_Air_Flow_Setpoint |
| `VAV-Perimeter_top_ZN_2/DMPR-CMD` | command | standard | bas | % |  | Damper command | Damper_Position_Command |
| `VAV-Perimeter_top_ZN_2/CLG-LOOP` | virtual | standard | bas | % |  | Cooling loop output |  |
| `VAV-Perimeter_top_ZN_2/HTG-LOOP` | virtual | standard | bas | % |  | Heating loop output |  |

## ZN-Perimeter_top_ZN_3 - Zone

Thermal zone Perimeter_top_ZN_3

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `ZN-Perimeter_top_ZN_3/ZN-T` | sensor | standard | energyplus | degC | zone_temperature | Zone air temperature | Zone_Air_Temperature_Sensor |
| `ZN-Perimeter_top_ZN_3/ZN-RH` | sensor | advanced | energyplus | %RH | humidity | Zone air relative humidity | Zone_Air_Humidity_Sensor |
| `ZN-Perimeter_top_ZN_3/ZN-DP` | sensor | advanced | energyplus | degC | air_temperature | Zone air dew-point temperature (calculated by T/RH transmitter) | Dewpoint_Sensor |
| `ZN-Perimeter_top_ZN_3/ZN-CO2` | sensor | standard | energyplus | ppm | co2 | Zone CO2 concentration (NDIR) | CO2_Sensor |
| `ZN-Perimeter_top_ZN_3/ZN-OCC` | sensor | standard | energyplus | - | occupancy | Zone occupancy sensor (PIR) | Occupancy_Sensor |
| `ZN-Perimeter_top_ZN_3/OCCUPANTS` | truth | truth | energyplus | people |  | True number of occupants (ground truth only) | Occupancy_Count_Sensor |
| `ZN-Perimeter_top_ZN_3/OCC-COUNT` | sensor | next_gen | model | people | people_count | People counter (camera / thermopile) | Occupancy_Count_Sensor |
| `ZN-Perimeter_top_ZN_3/WIN-STS` | sensor | advanced | model | - | binary | Window / door contact (1 = open) | Open_Close_Status |
| `ZN-Perimeter_top_ZN_3/ZN-MRT` | sensor | next_gen | energyplus | degC | radiant_temperature | Mean radiant temperature (globe thermometer) | Radiant_Temperature_Sensor |
| `ZN-Perimeter_top_ZN_3/ZN-OPT` | sensor | next_gen | energyplus | degC | zone_temperature | Operative temperature (comfort station) | Operative_Temperature |
| `ZN-Perimeter_top_ZN_3/PMV` | sensor | next_gen | energyplus | - | comfort_index | Predicted mean vote, ISO 7730 (comfort station) |  |
| `ZN-Perimeter_top_ZN_3/PPD` | sensor | next_gen | energyplus | % | comfort_ppd | Predicted percentage dissatisfied, ISO 7730 (comfort station) |  |
| `ZN-Perimeter_top_ZN_3/TS-VOTE` | sensor | next_gen | model | - | ideal | Mean thermal-sensation vote of occupants, last hour (feedback app, -3..+3) |  |
| `ZN-Perimeter_top_ZN_3/HOT-CALLS` | sensor | next_gen | model | count | ideal | Too-hot complaints today (work orders / app) |  |
| `ZN-Perimeter_top_ZN_3/COLD-CALLS` | sensor | next_gen | model | count | ideal | Too-cold complaints today (work orders / app) |  |
| `ZN-Perimeter_top_ZN_3/ZN-PM25` | sensor | next_gen | model | ug/m3 | pm_sensor | Zone PM2.5 (optical particle sensor) | PM2.5_Sensor |
| `ZN-Perimeter_top_ZN_3/ZN-PM10` | sensor | next_gen | model | ug/m3 | pm_sensor | Zone PM10 (optical particle sensor) | PM10_Sensor |
| `ZN-Perimeter_top_ZN_3/ZN-TVOC` | sensor | next_gen | model | ug/m3 | tvoc_sensor | Zone total VOC (metal-oxide sensor) | TVOC_Sensor |
| `ZN-Perimeter_top_ZN_3/ZN-LUX` | sensor | advanced | model | lux | illuminance | Work-plane illuminance (daylight-harvesting photosensor) | Illuminance_Sensor |
| `ZN-Perimeter_top_ZN_3/DAYLIGHT-LUX` | truth | truth | model | lux |  | Daylight share of the work-plane illuminance (ground truth only) |  |
| `ZN-Perimeter_top_ZN_3/LIGHT-LVL` | sensor | advanced | model | % | percent | Lighting level (networked lighting controls) |  |
| `ZN-Perimeter_top_ZN_3/ZN-DBA` | sensor | next_gen | model | dBA | sound | Background sound level (class-2 sound level meter) |  |
| `ZN-Perimeter_top_ZN_3/LIGHT-KW` | meter | advanced | energyplus | kW | power | Zone lighting power (lighting panel sub-meter) | Electric_Power_Sensor |
| `ZN-Perimeter_top_ZN_3/PLUG-KW` | meter | next_gen | energyplus | kW | power | Zone plug load power (circuit-level sub-meter) | Electric_Power_Sensor |
| `ZN-Perimeter_top_ZN_3/INFIL-ACH` | truth | truth | energyplus | 1/h |  | Infiltration air-change rate (ground truth only) |  |
| `ZN-Perimeter_top_ZN_3/WIN-SOL-KW` | truth | truth | energyplus | kW |  | Transmitted solar gain (ground truth only) |  |
| `ZN-Perimeter_top_ZN_3/WIN-Q-KW` | truth | truth | energyplus | kW |  | Window heat gain (ground truth only) |  |
| `ZN-Perimeter_top_ZN_3/INT-GAIN-KW` | truth | truth | energyplus | kW |  | Total internal heat gain (ground truth only) |  |
| `ZN-Perimeter_top_ZN_3/SYS-CLG-KW` | truth | truth | energyplus | kW |  | Sensible cooling delivered to the zone (ground truth only) |  |
| `ZN-Perimeter_top_ZN_3/SYS-HTG-KW` | truth | truth | energyplus | kW |  | Sensible heating delivered to the zone (ground truth only) |  |
| `ZN-Perimeter_top_ZN_3/HTG-SP` | setpoint | standard | bas | degC |  | Active heating set point | Zone_Air_Heating_Temperature_Setpoint |
| `ZN-Perimeter_top_ZN_3/CLG-SP` | setpoint | standard | bas | degC |  | Active cooling set point | Zone_Air_Cooling_Temperature_Setpoint |
| `ZN-Perimeter_top_ZN_3/OCC-HTG-SP` | setpoint | standard | bas | degC |  | Occupied heating set point | Occupied_Air_Temperature_Heating_Setpoint |
| `ZN-Perimeter_top_ZN_3/OCC-CLG-SP` | setpoint | standard | bas | degC |  | Occupied cooling set point | Occupied_Air_Temperature_Cooling_Setpoint |
| `ZN-Perimeter_top_ZN_3/OCC-MODE` | status | standard | bas | - |  | Zone occupancy mode (1 occupied / 0 unoccupied) | Occupancy_Status |
| `ZN-Perimeter_top_ZN_3/ZN-T-ADJ` | setpoint | standard | bas | K |  | Occupant set-point adjustment (wall sensor slider, +/-) | Temperature_Adjust_Sensor |

## VAV-Perimeter_top_ZN_3 - VAV

VAV terminal with hot-water reheat serving Perimeter_top_ZN_3

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `VAV-Perimeter_top_ZN_3/DA-F` | sensor | standard | energyplus | m3/s | air_flow | Discharge air flow | Discharge_Air_Flow_Sensor |
| `VAV-Perimeter_top_ZN_3/DA-T` | sensor | standard | energyplus | degC | air_temperature | Discharge air temperature | Discharge_Air_Temperature_Sensor |
| `VAV-Perimeter_top_ZN_3/DMPR-POS` | sensor | advanced | energyplus | % | position | Damper position feedback | Damper_Position_Sensor |
| `VAV-Perimeter_top_ZN_3/DA-VP` | sensor | advanced | surrogate | Pa | pressure | Flow-cross velocity pressure (airflow transducer) | Velocity_Pressure_Sensor |
| `VAV-Perimeter_top_ZN_3/RHV-POS` | sensor | advanced | energyplus | % | position | Reheat valve position (feedback) | Valve_Position_Sensor |
| `VAV-Perimeter_top_ZN_3/RH-Q` | truth | truth | energyplus | kW |  | Reheat coil heat rate (ground truth) |  |
| `VAV-Perimeter_top_ZN_3/RH-BTU` | sensor | next_gen | energyplus | kW | thermal_power | Reheat coil BTU meter (water-side heat rate) | Thermal_Power_Sensor |
| `VAV-Perimeter_top_ZN_3/RH-WF` | sensor | next_gen | energyplus | L/s | water_flow | Reheat coil water flow | Water_Flow_Sensor |
| `VAV-Perimeter_top_ZN_3/ZN-MODE` | status | standard | bas | - |  | Terminal control state (0 deadband, 1 cooling, 2 heating) | Mode_Status |
| `VAV-Perimeter_top_ZN_3/CLG-REQ` | virtual | standard | bas | count |  | Cooling SAT-reset requests (G36) |  |
| `VAV-Perimeter_top_ZN_3/PRS-REQ` | virtual | standard | bas | count |  | Static-pressure reset requests (G36) |  |
| `VAV-Perimeter_top_ZN_3/HW-REQ` | virtual | standard | bas | count |  | Hot-water reset requests (G36) |  |
| `VAV-Perimeter_top_ZN_3/LOW-FLOW-ALM` | status | standard | bas | - |  | Low airflow alarm (G36: flow < 70 % of set point for 5 min) | Low_Air_Flow_Alarm |
| `VAV-Perimeter_top_ZN_3/DA-F-SP` | setpoint | standard | bas | m3/s |  | Discharge air flow set point | Discharge_Air_Flow_Setpoint |
| `VAV-Perimeter_top_ZN_3/DMPR-CMD` | command | standard | bas | % |  | Damper command | Damper_Position_Command |
| `VAV-Perimeter_top_ZN_3/CLG-LOOP` | virtual | standard | bas | % |  | Cooling loop output |  |
| `VAV-Perimeter_top_ZN_3/HTG-LOOP` | virtual | standard | bas | % |  | Heating loop output |  |

## ZN-Perimeter_top_ZN_4 - Zone

Thermal zone Perimeter_top_ZN_4

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `ZN-Perimeter_top_ZN_4/ZN-T` | sensor | standard | energyplus | degC | zone_temperature | Zone air temperature | Zone_Air_Temperature_Sensor |
| `ZN-Perimeter_top_ZN_4/ZN-RH` | sensor | advanced | energyplus | %RH | humidity | Zone air relative humidity | Zone_Air_Humidity_Sensor |
| `ZN-Perimeter_top_ZN_4/ZN-DP` | sensor | advanced | energyplus | degC | air_temperature | Zone air dew-point temperature (calculated by T/RH transmitter) | Dewpoint_Sensor |
| `ZN-Perimeter_top_ZN_4/ZN-CO2` | sensor | standard | energyplus | ppm | co2 | Zone CO2 concentration (NDIR) | CO2_Sensor |
| `ZN-Perimeter_top_ZN_4/ZN-OCC` | sensor | standard | energyplus | - | occupancy | Zone occupancy sensor (PIR) | Occupancy_Sensor |
| `ZN-Perimeter_top_ZN_4/OCCUPANTS` | truth | truth | energyplus | people |  | True number of occupants (ground truth only) | Occupancy_Count_Sensor |
| `ZN-Perimeter_top_ZN_4/OCC-COUNT` | sensor | next_gen | model | people | people_count | People counter (camera / thermopile) | Occupancy_Count_Sensor |
| `ZN-Perimeter_top_ZN_4/WIN-STS` | sensor | advanced | model | - | binary | Window / door contact (1 = open) | Open_Close_Status |
| `ZN-Perimeter_top_ZN_4/ZN-MRT` | sensor | next_gen | energyplus | degC | radiant_temperature | Mean radiant temperature (globe thermometer) | Radiant_Temperature_Sensor |
| `ZN-Perimeter_top_ZN_4/ZN-OPT` | sensor | next_gen | energyplus | degC | zone_temperature | Operative temperature (comfort station) | Operative_Temperature |
| `ZN-Perimeter_top_ZN_4/PMV` | sensor | next_gen | energyplus | - | comfort_index | Predicted mean vote, ISO 7730 (comfort station) |  |
| `ZN-Perimeter_top_ZN_4/PPD` | sensor | next_gen | energyplus | % | comfort_ppd | Predicted percentage dissatisfied, ISO 7730 (comfort station) |  |
| `ZN-Perimeter_top_ZN_4/TS-VOTE` | sensor | next_gen | model | - | ideal | Mean thermal-sensation vote of occupants, last hour (feedback app, -3..+3) |  |
| `ZN-Perimeter_top_ZN_4/HOT-CALLS` | sensor | next_gen | model | count | ideal | Too-hot complaints today (work orders / app) |  |
| `ZN-Perimeter_top_ZN_4/COLD-CALLS` | sensor | next_gen | model | count | ideal | Too-cold complaints today (work orders / app) |  |
| `ZN-Perimeter_top_ZN_4/ZN-PM25` | sensor | next_gen | model | ug/m3 | pm_sensor | Zone PM2.5 (optical particle sensor) | PM2.5_Sensor |
| `ZN-Perimeter_top_ZN_4/ZN-PM10` | sensor | next_gen | model | ug/m3 | pm_sensor | Zone PM10 (optical particle sensor) | PM10_Sensor |
| `ZN-Perimeter_top_ZN_4/ZN-TVOC` | sensor | next_gen | model | ug/m3 | tvoc_sensor | Zone total VOC (metal-oxide sensor) | TVOC_Sensor |
| `ZN-Perimeter_top_ZN_4/ZN-LUX` | sensor | advanced | model | lux | illuminance | Work-plane illuminance (daylight-harvesting photosensor) | Illuminance_Sensor |
| `ZN-Perimeter_top_ZN_4/DAYLIGHT-LUX` | truth | truth | model | lux |  | Daylight share of the work-plane illuminance (ground truth only) |  |
| `ZN-Perimeter_top_ZN_4/LIGHT-LVL` | sensor | advanced | model | % | percent | Lighting level (networked lighting controls) |  |
| `ZN-Perimeter_top_ZN_4/ZN-DBA` | sensor | next_gen | model | dBA | sound | Background sound level (class-2 sound level meter) |  |
| `ZN-Perimeter_top_ZN_4/LIGHT-KW` | meter | advanced | energyplus | kW | power | Zone lighting power (lighting panel sub-meter) | Electric_Power_Sensor |
| `ZN-Perimeter_top_ZN_4/PLUG-KW` | meter | next_gen | energyplus | kW | power | Zone plug load power (circuit-level sub-meter) | Electric_Power_Sensor |
| `ZN-Perimeter_top_ZN_4/INFIL-ACH` | truth | truth | energyplus | 1/h |  | Infiltration air-change rate (ground truth only) |  |
| `ZN-Perimeter_top_ZN_4/WIN-SOL-KW` | truth | truth | energyplus | kW |  | Transmitted solar gain (ground truth only) |  |
| `ZN-Perimeter_top_ZN_4/WIN-Q-KW` | truth | truth | energyplus | kW |  | Window heat gain (ground truth only) |  |
| `ZN-Perimeter_top_ZN_4/INT-GAIN-KW` | truth | truth | energyplus | kW |  | Total internal heat gain (ground truth only) |  |
| `ZN-Perimeter_top_ZN_4/SYS-CLG-KW` | truth | truth | energyplus | kW |  | Sensible cooling delivered to the zone (ground truth only) |  |
| `ZN-Perimeter_top_ZN_4/SYS-HTG-KW` | truth | truth | energyplus | kW |  | Sensible heating delivered to the zone (ground truth only) |  |
| `ZN-Perimeter_top_ZN_4/HTG-SP` | setpoint | standard | bas | degC |  | Active heating set point | Zone_Air_Heating_Temperature_Setpoint |
| `ZN-Perimeter_top_ZN_4/CLG-SP` | setpoint | standard | bas | degC |  | Active cooling set point | Zone_Air_Cooling_Temperature_Setpoint |
| `ZN-Perimeter_top_ZN_4/OCC-HTG-SP` | setpoint | standard | bas | degC |  | Occupied heating set point | Occupied_Air_Temperature_Heating_Setpoint |
| `ZN-Perimeter_top_ZN_4/OCC-CLG-SP` | setpoint | standard | bas | degC |  | Occupied cooling set point | Occupied_Air_Temperature_Cooling_Setpoint |
| `ZN-Perimeter_top_ZN_4/OCC-MODE` | status | standard | bas | - |  | Zone occupancy mode (1 occupied / 0 unoccupied) | Occupancy_Status |
| `ZN-Perimeter_top_ZN_4/ZN-T-ADJ` | setpoint | standard | bas | K |  | Occupant set-point adjustment (wall sensor slider, +/-) | Temperature_Adjust_Sensor |

## VAV-Perimeter_top_ZN_4 - VAV

VAV terminal with hot-water reheat serving Perimeter_top_ZN_4

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `VAV-Perimeter_top_ZN_4/DA-F` | sensor | standard | energyplus | m3/s | air_flow | Discharge air flow | Discharge_Air_Flow_Sensor |
| `VAV-Perimeter_top_ZN_4/DA-T` | sensor | standard | energyplus | degC | air_temperature | Discharge air temperature | Discharge_Air_Temperature_Sensor |
| `VAV-Perimeter_top_ZN_4/DMPR-POS` | sensor | advanced | energyplus | % | position | Damper position feedback | Damper_Position_Sensor |
| `VAV-Perimeter_top_ZN_4/DA-VP` | sensor | advanced | surrogate | Pa | pressure | Flow-cross velocity pressure (airflow transducer) | Velocity_Pressure_Sensor |
| `VAV-Perimeter_top_ZN_4/RHV-POS` | sensor | advanced | energyplus | % | position | Reheat valve position (feedback) | Valve_Position_Sensor |
| `VAV-Perimeter_top_ZN_4/RH-Q` | truth | truth | energyplus | kW |  | Reheat coil heat rate (ground truth) |  |
| `VAV-Perimeter_top_ZN_4/RH-BTU` | sensor | next_gen | energyplus | kW | thermal_power | Reheat coil BTU meter (water-side heat rate) | Thermal_Power_Sensor |
| `VAV-Perimeter_top_ZN_4/RH-WF` | sensor | next_gen | energyplus | L/s | water_flow | Reheat coil water flow | Water_Flow_Sensor |
| `VAV-Perimeter_top_ZN_4/ZN-MODE` | status | standard | bas | - |  | Terminal control state (0 deadband, 1 cooling, 2 heating) | Mode_Status |
| `VAV-Perimeter_top_ZN_4/CLG-REQ` | virtual | standard | bas | count |  | Cooling SAT-reset requests (G36) |  |
| `VAV-Perimeter_top_ZN_4/PRS-REQ` | virtual | standard | bas | count |  | Static-pressure reset requests (G36) |  |
| `VAV-Perimeter_top_ZN_4/HW-REQ` | virtual | standard | bas | count |  | Hot-water reset requests (G36) |  |
| `VAV-Perimeter_top_ZN_4/LOW-FLOW-ALM` | status | standard | bas | - |  | Low airflow alarm (G36: flow < 70 % of set point for 5 min) | Low_Air_Flow_Alarm |
| `VAV-Perimeter_top_ZN_4/DA-F-SP` | setpoint | standard | bas | m3/s |  | Discharge air flow set point | Discharge_Air_Flow_Setpoint |
| `VAV-Perimeter_top_ZN_4/DMPR-CMD` | command | standard | bas | % |  | Damper command | Damper_Position_Command |
| `VAV-Perimeter_top_ZN_4/CLG-LOOP` | virtual | standard | bas | % |  | Cooling loop output |  |
| `VAV-Perimeter_top_ZN_4/HTG-LOOP` | virtual | standard | bas | % |  | Heating loop output |  |

## AHU-1 - AHU

Air handling unit VAV_1 (VAV, economizer, CHW/HW coils)

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `AHU-1/SA-T` | sensor | standard | energyplus | degC | air_temperature | Supply air temperature | Supply_Air_Temperature_Sensor |
| `AHU-1/SA-RH` | sensor | advanced | energyplus | %RH | humidity | Supply air relative humidity | Supply_Air_Humidity_Sensor |
| `AHU-1/SA-F` | sensor | standard | energyplus | m3/s | air_flow | Supply air flow | Supply_Air_Flow_Sensor |
| `AHU-1/MA-T` | sensor | standard | energyplus | degC | air_temperature | Mixed air temperature | Mixed_Air_Temperature_Sensor |
| `AHU-1/RA-T` | sensor | standard | energyplus | degC | air_temperature | Return air temperature | Return_Air_Temperature_Sensor |
| `AHU-1/RA-RH` | sensor | advanced | energyplus | %RH | humidity | Return air relative humidity | Return_Air_Humidity_Sensor |
| `AHU-1/OA-F` | sensor | standard | energyplus | m3/s | air_flow | Outdoor air flow (airflow measuring station) | Outside_Air_Flow_Sensor |
| `AHU-1/OAD-POS` | sensor | advanced | energyplus | % | position | Outdoor air damper position (feedback) | Damper_Position_Sensor |
| `AHU-1/CCV-POS` | sensor | advanced | energyplus | % | position | Cooling coil valve position (feedback) | Valve_Position_Sensor |
| `AHU-1/CC-Q` | truth | truth | energyplus | kW |  | Cooling coil total load (ground truth) |  |
| `AHU-1/CC-LAT` | sensor | advanced | energyplus | degC | air_temperature | Cooling coil leaving air temperature | Air_Temperature_Sensor |
| `AHU-1/HCV-POS` | sensor | advanced | energyplus | % | position | Heating (preheat) coil valve position (feedback) | Valve_Position_Sensor |
| `AHU-1/SF-KW` | sensor | standard | energyplus | kW | power | Supply fan power (VFD) | Electric_Power_Sensor |
| `AHU-1/SF-SPD` | sensor | standard | energyplus | % | percent | Supply fan speed (VFD output) | Frequency_Sensor |
| `AHU-1/SF-STS` | sensor | standard | energyplus | - | binary | Supply fan status (current switch) | Fan_Status |
| `AHU-1/OA-T` | sensor | standard | energyplus | degC | outdoor_temperature | Outdoor air temperature at the AHU intake (local sensor) | Outside_Air_Temperature_Sensor |
| `AHU-1/OA-RH` | sensor | advanced | energyplus | %RH | outdoor_humidity | Outdoor air humidity at the AHU intake (enthalpy economizer) | Outside_Air_Humidity_Sensor |
| `AHU-1/SA-DP` | sensor | advanced | energyplus | degC | air_temperature | Supply air dew point (calculated by T/RH transmitter) | Dewpoint_Sensor |
| `AHU-1/RA-CO2` | sensor | advanced | energyplus | ppm | co2 | Return air CO2 | Return_Air_CO2_Sensor |
| `AHU-1/OA-FRAC-CALC` | virtual | standard | bas | % |  | Outdoor-air fraction from OA/RA/MA temperatures |  |
| `AHU-1/OA-FRAC-AFMS` | virtual | advanced | bas | % |  | Outdoor-air fraction from airflow stations (OA-F / SA-F) |  |
| `AHU-1/OA-FRAC` | truth | truth | model | % |  | True outdoor-air fraction (ground truth only) |  |
| `AHU-1/SA-PM25` | truth | truth | model | ug/m3 |  | Supply air PM2.5 after filter (ground truth only) |  |
| `AHU-1/HC-LAT` | sensor | advanced | energyplus | degC | air_temperature | Preheat coil leaving air temperature | Air_Temperature_Sensor |
| `AHU-1/FRZ-STAT` | sensor | standard | energyplus | - | binary | Freeze-stat low-limit (hard-wired, trips < 3.3 C) | Low_Freeze_Protect_Temperature_Sensor |
| `AHU-1/SMK-DET` | sensor | standard | energyplus | - | binary | Duct smoke detector (hard-wired fan shutdown) | Smoke_Detection_Alarm |
| `AHU-1/CC-EWT` | sensor | next_gen | energyplus | degC | water_temperature | Cooling coil entering water temperature | Chilled_Water_Supply_Temperature_Sensor |
| `AHU-1/CC-LWT` | sensor | next_gen | energyplus | degC | water_temperature | Cooling coil leaving water temperature | Chilled_Water_Return_Temperature_Sensor |
| `AHU-1/CC-WF` | sensor | next_gen | energyplus | L/s | water_flow | Cooling coil water flow | Water_Flow_Sensor |
| `AHU-1/CC-BTU` | sensor | next_gen | energyplus | kW | thermal_power | Cooling coil BTU meter | Thermal_Power_Sensor |
| `AHU-1/CC-DP` | sensor | next_gen | surrogate | Pa | pressure | Cooling coil air-side pressure drop (surrogate) | Differential_Pressure_Sensor |
| `AHU-1/HC-BTU` | sensor | next_gen | energyplus | kW | thermal_power | Preheat coil BTU meter | Thermal_Power_Sensor |
| `AHU-1/SF-HZ` | sensor | standard | energyplus | Hz | frequency | Supply fan VFD output frequency | Frequency_Sensor |
| `AHU-1/SF-AMPS` | sensor | advanced | energyplus | A | current | Supply fan motor current (VFD) | Current_Sensor |
| `AHU-1/SF-VIB` | sensor | next_gen | surrogate | mm/s | vibration | Supply fan vibration velocity, ISO 10816 (surrogate) | Vibration_Sensor |
| `AHU-1/SF-W-PER-CMS` | virtual | advanced | bas | W/(m3/s) |  | Specific fan power (fan W per m3/s supply) |  |
| `AHU-1/DSP` | sensor | standard | surrogate | Pa | pressure | Duct static pressure (surrogate model) | Static_Pressure_Sensor |
| `AHU-1/FLT-DP` | sensor | standard | surrogate | Pa | pressure | Filter differential pressure (surrogate model) | Filter_Differential_Pressure_Sensor |
| `AHU-1/SA-T-SP` | setpoint | standard | bas | degC |  | Supply air temperature set point | Supply_Air_Temperature_Setpoint |
| `AHU-1/DSP-SP` | setpoint | standard | bas | Pa |  | Duct static pressure set point | Static_Pressure_Setpoint |
| `AHU-1/MA-T-SP` | setpoint | standard | bas | degC |  | Mixed air temperature set point (economizer) | Mixed_Air_Temperature_Setpoint |
| `AHU-1/OAD-CMD` | command | standard | bas | % |  | Outdoor air damper command | Damper_Position_Command |
| `AHU-1/ECON-EN` | status | standard | bas | - |  | Economizer enable | Enable_Status |
| `AHU-1/SF-CMD` | command | standard | bas | - |  | Supply fan start/stop command | Start_Stop_Command |
| `AHU-1/OCC-MODE` | status | standard | bas | - |  | AHU operating mode (2 occupied, 1 night cycle, 0 off) | Operating_Mode_Status |
| `AHU-1/SF-RUNHRS` | virtual | standard | bas | h |  | Run-hours (supply fan status (current switch)) | Run_Time_Sensor |
| `AHU-1/SF-STARTS` | virtual | standard | bas | count |  | Start count (supply fan status (current switch)) |  |

## AHU-2 - AHU

Air handling unit VAV_2 (VAV, economizer, CHW/HW coils)

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `AHU-2/SA-T` | sensor | standard | energyplus | degC | air_temperature | Supply air temperature | Supply_Air_Temperature_Sensor |
| `AHU-2/SA-RH` | sensor | advanced | energyplus | %RH | humidity | Supply air relative humidity | Supply_Air_Humidity_Sensor |
| `AHU-2/SA-F` | sensor | standard | energyplus | m3/s | air_flow | Supply air flow | Supply_Air_Flow_Sensor |
| `AHU-2/MA-T` | sensor | standard | energyplus | degC | air_temperature | Mixed air temperature | Mixed_Air_Temperature_Sensor |
| `AHU-2/RA-T` | sensor | standard | energyplus | degC | air_temperature | Return air temperature | Return_Air_Temperature_Sensor |
| `AHU-2/RA-RH` | sensor | advanced | energyplus | %RH | humidity | Return air relative humidity | Return_Air_Humidity_Sensor |
| `AHU-2/OA-F` | sensor | standard | energyplus | m3/s | air_flow | Outdoor air flow (airflow measuring station) | Outside_Air_Flow_Sensor |
| `AHU-2/OAD-POS` | sensor | advanced | energyplus | % | position | Outdoor air damper position (feedback) | Damper_Position_Sensor |
| `AHU-2/CCV-POS` | sensor | advanced | energyplus | % | position | Cooling coil valve position (feedback) | Valve_Position_Sensor |
| `AHU-2/CC-Q` | truth | truth | energyplus | kW |  | Cooling coil total load (ground truth) |  |
| `AHU-2/CC-LAT` | sensor | advanced | energyplus | degC | air_temperature | Cooling coil leaving air temperature | Air_Temperature_Sensor |
| `AHU-2/HCV-POS` | sensor | advanced | energyplus | % | position | Heating (preheat) coil valve position (feedback) | Valve_Position_Sensor |
| `AHU-2/SF-KW` | sensor | standard | energyplus | kW | power | Supply fan power (VFD) | Electric_Power_Sensor |
| `AHU-2/SF-SPD` | sensor | standard | energyplus | % | percent | Supply fan speed (VFD output) | Frequency_Sensor |
| `AHU-2/SF-STS` | sensor | standard | energyplus | - | binary | Supply fan status (current switch) | Fan_Status |
| `AHU-2/OA-T` | sensor | standard | energyplus | degC | outdoor_temperature | Outdoor air temperature at the AHU intake (local sensor) | Outside_Air_Temperature_Sensor |
| `AHU-2/OA-RH` | sensor | advanced | energyplus | %RH | outdoor_humidity | Outdoor air humidity at the AHU intake (enthalpy economizer) | Outside_Air_Humidity_Sensor |
| `AHU-2/SA-DP` | sensor | advanced | energyplus | degC | air_temperature | Supply air dew point (calculated by T/RH transmitter) | Dewpoint_Sensor |
| `AHU-2/RA-CO2` | sensor | advanced | energyplus | ppm | co2 | Return air CO2 | Return_Air_CO2_Sensor |
| `AHU-2/OA-FRAC-CALC` | virtual | standard | bas | % |  | Outdoor-air fraction from OA/RA/MA temperatures |  |
| `AHU-2/OA-FRAC-AFMS` | virtual | advanced | bas | % |  | Outdoor-air fraction from airflow stations (OA-F / SA-F) |  |
| `AHU-2/OA-FRAC` | truth | truth | model | % |  | True outdoor-air fraction (ground truth only) |  |
| `AHU-2/SA-PM25` | truth | truth | model | ug/m3 |  | Supply air PM2.5 after filter (ground truth only) |  |
| `AHU-2/HC-LAT` | sensor | advanced | energyplus | degC | air_temperature | Preheat coil leaving air temperature | Air_Temperature_Sensor |
| `AHU-2/FRZ-STAT` | sensor | standard | energyplus | - | binary | Freeze-stat low-limit (hard-wired, trips < 3.3 C) | Low_Freeze_Protect_Temperature_Sensor |
| `AHU-2/SMK-DET` | sensor | standard | energyplus | - | binary | Duct smoke detector (hard-wired fan shutdown) | Smoke_Detection_Alarm |
| `AHU-2/CC-EWT` | sensor | next_gen | energyplus | degC | water_temperature | Cooling coil entering water temperature | Chilled_Water_Supply_Temperature_Sensor |
| `AHU-2/CC-LWT` | sensor | next_gen | energyplus | degC | water_temperature | Cooling coil leaving water temperature | Chilled_Water_Return_Temperature_Sensor |
| `AHU-2/CC-WF` | sensor | next_gen | energyplus | L/s | water_flow | Cooling coil water flow | Water_Flow_Sensor |
| `AHU-2/CC-BTU` | sensor | next_gen | energyplus | kW | thermal_power | Cooling coil BTU meter | Thermal_Power_Sensor |
| `AHU-2/CC-DP` | sensor | next_gen | surrogate | Pa | pressure | Cooling coil air-side pressure drop (surrogate) | Differential_Pressure_Sensor |
| `AHU-2/HC-BTU` | sensor | next_gen | energyplus | kW | thermal_power | Preheat coil BTU meter | Thermal_Power_Sensor |
| `AHU-2/SF-HZ` | sensor | standard | energyplus | Hz | frequency | Supply fan VFD output frequency | Frequency_Sensor |
| `AHU-2/SF-AMPS` | sensor | advanced | energyplus | A | current | Supply fan motor current (VFD) | Current_Sensor |
| `AHU-2/SF-VIB` | sensor | next_gen | surrogate | mm/s | vibration | Supply fan vibration velocity, ISO 10816 (surrogate) | Vibration_Sensor |
| `AHU-2/SF-W-PER-CMS` | virtual | advanced | bas | W/(m3/s) |  | Specific fan power (fan W per m3/s supply) |  |
| `AHU-2/DSP` | sensor | standard | surrogate | Pa | pressure | Duct static pressure (surrogate model) | Static_Pressure_Sensor |
| `AHU-2/FLT-DP` | sensor | standard | surrogate | Pa | pressure | Filter differential pressure (surrogate model) | Filter_Differential_Pressure_Sensor |
| `AHU-2/SA-T-SP` | setpoint | standard | bas | degC |  | Supply air temperature set point | Supply_Air_Temperature_Setpoint |
| `AHU-2/DSP-SP` | setpoint | standard | bas | Pa |  | Duct static pressure set point | Static_Pressure_Setpoint |
| `AHU-2/MA-T-SP` | setpoint | standard | bas | degC |  | Mixed air temperature set point (economizer) | Mixed_Air_Temperature_Setpoint |
| `AHU-2/OAD-CMD` | command | standard | bas | % |  | Outdoor air damper command | Damper_Position_Command |
| `AHU-2/ECON-EN` | status | standard | bas | - |  | Economizer enable | Enable_Status |
| `AHU-2/SF-CMD` | command | standard | bas | - |  | Supply fan start/stop command | Start_Stop_Command |
| `AHU-2/OCC-MODE` | status | standard | bas | - |  | AHU operating mode (2 occupied, 1 night cycle, 0 off) | Operating_Mode_Status |
| `AHU-2/SF-RUNHRS` | virtual | standard | bas | h |  | Run-hours (supply fan status (current switch)) | Run_Time_Sensor |
| `AHU-2/SF-STARTS` | virtual | standard | bas | count |  | Start count (supply fan status (current switch)) |  |

## AHU-3 - AHU

Air handling unit VAV_3 (VAV, economizer, CHW/HW coils)

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `AHU-3/SA-T` | sensor | standard | energyplus | degC | air_temperature | Supply air temperature | Supply_Air_Temperature_Sensor |
| `AHU-3/SA-RH` | sensor | advanced | energyplus | %RH | humidity | Supply air relative humidity | Supply_Air_Humidity_Sensor |
| `AHU-3/SA-F` | sensor | standard | energyplus | m3/s | air_flow | Supply air flow | Supply_Air_Flow_Sensor |
| `AHU-3/MA-T` | sensor | standard | energyplus | degC | air_temperature | Mixed air temperature | Mixed_Air_Temperature_Sensor |
| `AHU-3/RA-T` | sensor | standard | energyplus | degC | air_temperature | Return air temperature | Return_Air_Temperature_Sensor |
| `AHU-3/RA-RH` | sensor | advanced | energyplus | %RH | humidity | Return air relative humidity | Return_Air_Humidity_Sensor |
| `AHU-3/OA-F` | sensor | standard | energyplus | m3/s | air_flow | Outdoor air flow (airflow measuring station) | Outside_Air_Flow_Sensor |
| `AHU-3/OAD-POS` | sensor | advanced | energyplus | % | position | Outdoor air damper position (feedback) | Damper_Position_Sensor |
| `AHU-3/CCV-POS` | sensor | advanced | energyplus | % | position | Cooling coil valve position (feedback) | Valve_Position_Sensor |
| `AHU-3/CC-Q` | truth | truth | energyplus | kW |  | Cooling coil total load (ground truth) |  |
| `AHU-3/CC-LAT` | sensor | advanced | energyplus | degC | air_temperature | Cooling coil leaving air temperature | Air_Temperature_Sensor |
| `AHU-3/HCV-POS` | sensor | advanced | energyplus | % | position | Heating (preheat) coil valve position (feedback) | Valve_Position_Sensor |
| `AHU-3/SF-KW` | sensor | standard | energyplus | kW | power | Supply fan power (VFD) | Electric_Power_Sensor |
| `AHU-3/SF-SPD` | sensor | standard | energyplus | % | percent | Supply fan speed (VFD output) | Frequency_Sensor |
| `AHU-3/SF-STS` | sensor | standard | energyplus | - | binary | Supply fan status (current switch) | Fan_Status |
| `AHU-3/OA-T` | sensor | standard | energyplus | degC | outdoor_temperature | Outdoor air temperature at the AHU intake (local sensor) | Outside_Air_Temperature_Sensor |
| `AHU-3/OA-RH` | sensor | advanced | energyplus | %RH | outdoor_humidity | Outdoor air humidity at the AHU intake (enthalpy economizer) | Outside_Air_Humidity_Sensor |
| `AHU-3/SA-DP` | sensor | advanced | energyplus | degC | air_temperature | Supply air dew point (calculated by T/RH transmitter) | Dewpoint_Sensor |
| `AHU-3/RA-CO2` | sensor | advanced | energyplus | ppm | co2 | Return air CO2 | Return_Air_CO2_Sensor |
| `AHU-3/OA-FRAC-CALC` | virtual | standard | bas | % |  | Outdoor-air fraction from OA/RA/MA temperatures |  |
| `AHU-3/OA-FRAC-AFMS` | virtual | advanced | bas | % |  | Outdoor-air fraction from airflow stations (OA-F / SA-F) |  |
| `AHU-3/OA-FRAC` | truth | truth | model | % |  | True outdoor-air fraction (ground truth only) |  |
| `AHU-3/SA-PM25` | truth | truth | model | ug/m3 |  | Supply air PM2.5 after filter (ground truth only) |  |
| `AHU-3/HC-LAT` | sensor | advanced | energyplus | degC | air_temperature | Preheat coil leaving air temperature | Air_Temperature_Sensor |
| `AHU-3/FRZ-STAT` | sensor | standard | energyplus | - | binary | Freeze-stat low-limit (hard-wired, trips < 3.3 C) | Low_Freeze_Protect_Temperature_Sensor |
| `AHU-3/SMK-DET` | sensor | standard | energyplus | - | binary | Duct smoke detector (hard-wired fan shutdown) | Smoke_Detection_Alarm |
| `AHU-3/CC-EWT` | sensor | next_gen | energyplus | degC | water_temperature | Cooling coil entering water temperature | Chilled_Water_Supply_Temperature_Sensor |
| `AHU-3/CC-LWT` | sensor | next_gen | energyplus | degC | water_temperature | Cooling coil leaving water temperature | Chilled_Water_Return_Temperature_Sensor |
| `AHU-3/CC-WF` | sensor | next_gen | energyplus | L/s | water_flow | Cooling coil water flow | Water_Flow_Sensor |
| `AHU-3/CC-BTU` | sensor | next_gen | energyplus | kW | thermal_power | Cooling coil BTU meter | Thermal_Power_Sensor |
| `AHU-3/CC-DP` | sensor | next_gen | surrogate | Pa | pressure | Cooling coil air-side pressure drop (surrogate) | Differential_Pressure_Sensor |
| `AHU-3/HC-BTU` | sensor | next_gen | energyplus | kW | thermal_power | Preheat coil BTU meter | Thermal_Power_Sensor |
| `AHU-3/SF-HZ` | sensor | standard | energyplus | Hz | frequency | Supply fan VFD output frequency | Frequency_Sensor |
| `AHU-3/SF-AMPS` | sensor | advanced | energyplus | A | current | Supply fan motor current (VFD) | Current_Sensor |
| `AHU-3/SF-VIB` | sensor | next_gen | surrogate | mm/s | vibration | Supply fan vibration velocity, ISO 10816 (surrogate) | Vibration_Sensor |
| `AHU-3/SF-W-PER-CMS` | virtual | advanced | bas | W/(m3/s) |  | Specific fan power (fan W per m3/s supply) |  |
| `AHU-3/DSP` | sensor | standard | surrogate | Pa | pressure | Duct static pressure (surrogate model) | Static_Pressure_Sensor |
| `AHU-3/FLT-DP` | sensor | standard | surrogate | Pa | pressure | Filter differential pressure (surrogate model) | Filter_Differential_Pressure_Sensor |
| `AHU-3/SA-T-SP` | setpoint | standard | bas | degC |  | Supply air temperature set point | Supply_Air_Temperature_Setpoint |
| `AHU-3/DSP-SP` | setpoint | standard | bas | Pa |  | Duct static pressure set point | Static_Pressure_Setpoint |
| `AHU-3/MA-T-SP` | setpoint | standard | bas | degC |  | Mixed air temperature set point (economizer) | Mixed_Air_Temperature_Setpoint |
| `AHU-3/OAD-CMD` | command | standard | bas | % |  | Outdoor air damper command | Damper_Position_Command |
| `AHU-3/ECON-EN` | status | standard | bas | - |  | Economizer enable | Enable_Status |
| `AHU-3/SF-CMD` | command | standard | bas | - |  | Supply fan start/stop command | Start_Stop_Command |
| `AHU-3/OCC-MODE` | status | standard | bas | - |  | AHU operating mode (2 occupied, 1 night cycle, 0 off) | Operating_Mode_Status |
| `AHU-3/SF-RUNHRS` | virtual | standard | bas | h |  | Run-hours (supply fan status (current switch)) | Run_Time_Sensor |
| `AHU-3/SF-STARTS` | virtual | standard | bas | count |  | Start count (supply fan status (current switch)) |  |

## AHU-4 - AHU

Air handling unit VAV_5 (VAV, economizer, CHW/HW coils)

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `AHU-4/SA-T` | sensor | standard | energyplus | degC | air_temperature | Supply air temperature | Supply_Air_Temperature_Sensor |
| `AHU-4/SA-RH` | sensor | advanced | energyplus | %RH | humidity | Supply air relative humidity | Supply_Air_Humidity_Sensor |
| `AHU-4/SA-F` | sensor | standard | energyplus | m3/s | air_flow | Supply air flow | Supply_Air_Flow_Sensor |
| `AHU-4/MA-T` | sensor | standard | energyplus | degC | air_temperature | Mixed air temperature | Mixed_Air_Temperature_Sensor |
| `AHU-4/RA-T` | sensor | standard | energyplus | degC | air_temperature | Return air temperature | Return_Air_Temperature_Sensor |
| `AHU-4/RA-RH` | sensor | advanced | energyplus | %RH | humidity | Return air relative humidity | Return_Air_Humidity_Sensor |
| `AHU-4/OA-F` | sensor | standard | energyplus | m3/s | air_flow | Outdoor air flow (airflow measuring station) | Outside_Air_Flow_Sensor |
| `AHU-4/OAD-POS` | sensor | advanced | energyplus | % | position | Outdoor air damper position (feedback) | Damper_Position_Sensor |
| `AHU-4/CCV-POS` | sensor | advanced | energyplus | % | position | Cooling coil valve position (feedback) | Valve_Position_Sensor |
| `AHU-4/CC-Q` | truth | truth | energyplus | kW |  | Cooling coil total load (ground truth) |  |
| `AHU-4/CC-LAT` | sensor | advanced | energyplus | degC | air_temperature | Cooling coil leaving air temperature | Air_Temperature_Sensor |
| `AHU-4/HCV-POS` | sensor | advanced | energyplus | % | position | Heating (preheat) coil valve position (feedback) | Valve_Position_Sensor |
| `AHU-4/SF-KW` | sensor | standard | energyplus | kW | power | Supply fan power (VFD) | Electric_Power_Sensor |
| `AHU-4/SF-SPD` | sensor | standard | energyplus | % | percent | Supply fan speed (VFD output) | Frequency_Sensor |
| `AHU-4/SF-STS` | sensor | standard | energyplus | - | binary | Supply fan status (current switch) | Fan_Status |
| `AHU-4/OA-T` | sensor | standard | energyplus | degC | outdoor_temperature | Outdoor air temperature at the AHU intake (local sensor) | Outside_Air_Temperature_Sensor |
| `AHU-4/OA-RH` | sensor | advanced | energyplus | %RH | outdoor_humidity | Outdoor air humidity at the AHU intake (enthalpy economizer) | Outside_Air_Humidity_Sensor |
| `AHU-4/SA-DP` | sensor | advanced | energyplus | degC | air_temperature | Supply air dew point (calculated by T/RH transmitter) | Dewpoint_Sensor |
| `AHU-4/RA-CO2` | sensor | advanced | energyplus | ppm | co2 | Return air CO2 | Return_Air_CO2_Sensor |
| `AHU-4/OA-FRAC-CALC` | virtual | standard | bas | % |  | Outdoor-air fraction from OA/RA/MA temperatures |  |
| `AHU-4/OA-FRAC-AFMS` | virtual | advanced | bas | % |  | Outdoor-air fraction from airflow stations (OA-F / SA-F) |  |
| `AHU-4/OA-FRAC` | truth | truth | model | % |  | True outdoor-air fraction (ground truth only) |  |
| `AHU-4/SA-PM25` | truth | truth | model | ug/m3 |  | Supply air PM2.5 after filter (ground truth only) |  |
| `AHU-4/HC-LAT` | sensor | advanced | energyplus | degC | air_temperature | Preheat coil leaving air temperature | Air_Temperature_Sensor |
| `AHU-4/FRZ-STAT` | sensor | standard | energyplus | - | binary | Freeze-stat low-limit (hard-wired, trips < 3.3 C) | Low_Freeze_Protect_Temperature_Sensor |
| `AHU-4/SMK-DET` | sensor | standard | energyplus | - | binary | Duct smoke detector (hard-wired fan shutdown) | Smoke_Detection_Alarm |
| `AHU-4/CC-EWT` | sensor | next_gen | energyplus | degC | water_temperature | Cooling coil entering water temperature | Chilled_Water_Supply_Temperature_Sensor |
| `AHU-4/CC-LWT` | sensor | next_gen | energyplus | degC | water_temperature | Cooling coil leaving water temperature | Chilled_Water_Return_Temperature_Sensor |
| `AHU-4/CC-WF` | sensor | next_gen | energyplus | L/s | water_flow | Cooling coil water flow | Water_Flow_Sensor |
| `AHU-4/CC-BTU` | sensor | next_gen | energyplus | kW | thermal_power | Cooling coil BTU meter | Thermal_Power_Sensor |
| `AHU-4/CC-DP` | sensor | next_gen | surrogate | Pa | pressure | Cooling coil air-side pressure drop (surrogate) | Differential_Pressure_Sensor |
| `AHU-4/HC-BTU` | sensor | next_gen | energyplus | kW | thermal_power | Preheat coil BTU meter | Thermal_Power_Sensor |
| `AHU-4/SF-HZ` | sensor | standard | energyplus | Hz | frequency | Supply fan VFD output frequency | Frequency_Sensor |
| `AHU-4/SF-AMPS` | sensor | advanced | energyplus | A | current | Supply fan motor current (VFD) | Current_Sensor |
| `AHU-4/SF-VIB` | sensor | next_gen | surrogate | mm/s | vibration | Supply fan vibration velocity, ISO 10816 (surrogate) | Vibration_Sensor |
| `AHU-4/SF-W-PER-CMS` | virtual | advanced | bas | W/(m3/s) |  | Specific fan power (fan W per m3/s supply) |  |
| `AHU-4/DSP` | sensor | standard | surrogate | Pa | pressure | Duct static pressure (surrogate model) | Static_Pressure_Sensor |
| `AHU-4/FLT-DP` | sensor | standard | surrogate | Pa | pressure | Filter differential pressure (surrogate model) | Filter_Differential_Pressure_Sensor |
| `AHU-4/SA-T-SP` | setpoint | standard | bas | degC |  | Supply air temperature set point | Supply_Air_Temperature_Setpoint |
| `AHU-4/DSP-SP` | setpoint | standard | bas | Pa |  | Duct static pressure set point | Static_Pressure_Setpoint |
| `AHU-4/MA-T-SP` | setpoint | standard | bas | degC |  | Mixed air temperature set point (economizer) | Mixed_Air_Temperature_Setpoint |
| `AHU-4/OAD-CMD` | command | standard | bas | % |  | Outdoor air damper command | Damper_Position_Command |
| `AHU-4/ECON-EN` | status | standard | bas | - |  | Economizer enable | Enable_Status |
| `AHU-4/SF-CMD` | command | standard | bas | - |  | Supply fan start/stop command | Start_Stop_Command |
| `AHU-4/OCC-MODE` | status | standard | bas | - |  | AHU operating mode (2 occupied, 1 night cycle, 0 off) | Operating_Mode_Status |
| `AHU-4/SF-RUNHRS` | virtual | standard | bas | h |  | Run-hours (supply fan status (current switch)) | Run_Time_Sensor |
| `AHU-4/SF-STARTS` | virtual | standard | bas | count |  | Start count (supply fan status (current switch)) |  |

## CHW-SYS - PlantLoop

Chilled water system

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `CHW-SYS/CHW-ST` | sensor | standard | energyplus | degC | water_temperature | Chilled water supply temperature | Supply_Water_Temperature_Sensor |
| `CHW-SYS/CHW-RT` | sensor | standard | energyplus | degC | water_temperature | Chilled water return temperature | Return_Water_Temperature_Sensor |
| `CHW-SYS/CHW-F` | sensor | standard | energyplus | L/s | water_flow | Chilled water flow | Water_Flow_Sensor |
| `CHW-SYS/CHW-DP` | sensor | standard | surrogate | kPa | pressure | Chilled water differential pressure (surrogate model) | Differential_Pressure_Sensor |
| `CHW-SYS/CHW-ST-SP` | setpoint | standard | bas | degC |  | Chilled water supply temperature set point | Supply_Water_Temperature_Setpoint |
| `CHW-SYS/CHW-DT` | virtual | standard | bas | K |  | Chilled water delta-T (return - supply) |  |
| `CHW-SYS/CHW-TONS` | virtual | standard | bas | ton |  | Chilled-water load from loop flow and delta-T |  |
| `CHW-SYS/PLANT-KW-TON` | virtual | advanced | bas | kW/ton |  | Chiller-plant efficiency (chillers + tower + CHW/CW pumps) |  |

## CHWP-1 - Pump

Chilled water pump (VariableSpeed)

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `CHWP-1/KW` | sensor | standard | energyplus | kW | power | Pump power | Electric_Power_Sensor |
| `CHWP-1/SPD` | sensor | standard | energyplus | % | percent | Pump speed (VFD output) | Frequency_Sensor |
| `CHWP-1/STS` | sensor | standard | energyplus | - | binary | Pump status | Pump_Status |
| `CHWP-1/HZ` | sensor | standard | energyplus | Hz | frequency | Pump VFD output frequency | Frequency_Sensor |
| `CHWP-1/VIB` | sensor | next_gen | surrogate | mm/s | vibration | Pump vibration velocity, ISO 10816 (surrogate) | Vibration_Sensor |
| `CHWP-1/RUNHRS` | virtual | standard | bas | h |  | Run-hours (pump status) | Run_Time_Sensor |
| `CHWP-1/STARTS` | virtual | standard | bas | count |  | Start count (pump status) |  |

## CH-1 - Chiller

Water-cooled chiller (ReformulatedEIR)

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `CH-1/KW` | sensor | standard | energyplus | kW | power | Chiller power | Electric_Power_Sensor |
| `CH-1/LOAD` | sensor | advanced | energyplus | kW | power | Chiller cooling load (BTU meter) | Thermal_Power_Sensor |
| `CH-1/STS` | sensor | standard | energyplus | - | binary | Chiller run status | Run_Status |
| `CH-1/CHW-LWT` | sensor | standard | energyplus | degC | water_temperature | Evaporator leaving water temperature | Chilled_Water_Supply_Temperature_Sensor |
| `CH-1/CHW-EWT` | sensor | standard | energyplus | degC | water_temperature | Evaporator entering water temperature | Chilled_Water_Return_Temperature_Sensor |
| `CH-1/CDW-EWT` | sensor | standard | energyplus | degC | water_temperature | Condenser entering water temperature | Condenser_Water_Return_Temperature_Sensor |
| `CH-1/CDW-LWT` | sensor | standard | energyplus | degC | water_temperature | Condenser leaving water temperature | Condenser_Water_Supply_Temperature_Sensor |
| `CH-1/PLR` | truth | truth | energyplus | - |  | Chiller part load ratio |  |
| `CH-1/COP` | truth | truth | energyplus | - |  | Chiller COP (ground truth) |  |
| `CH-1/EN-CMD` | command | standard | bas | - |  | Chiller enable command | Enable_Command |
| `CH-1/PCT-RLA` | sensor | standard | energyplus | % | percent | Compressor current, percent of rated load amps | Current_Sensor |
| `CH-1/CHW-F` | sensor | advanced | energyplus | L/s | water_flow | Evaporator water flow | Chilled_Water_Flow_Sensor |
| `CH-1/CDW-F` | sensor | advanced | energyplus | L/s | water_flow | Condenser water flow | Condenser_Water_Flow_Sensor |
| `CH-1/EVAP-SAT-T` | sensor | advanced | surrogate | degC | water_temperature | Evaporator saturated refrigerant temperature (surrogate) | Temperature_Sensor |
| `CH-1/COND-SAT-T` | sensor | advanced | surrogate | degC | water_temperature | Condenser saturated refrigerant temperature (surrogate) | Temperature_Sensor |
| `CH-1/EVAP-P` | sensor | advanced | surrogate | kPa | refrigerant_pressure | Evaporator refrigerant pressure (abs.) (surrogate) | Refrigerant_Pressure_Sensor |
| `CH-1/COND-P` | sensor | advanced | surrogate | kPa | refrigerant_pressure | Condenser refrigerant pressure (abs.) (surrogate) | Refrigerant_Pressure_Sensor |
| `CH-1/ALM` | sensor | standard | model | - | binary | Chiller common alarm / lock-out | Alarm |
| `CH-1/KW-TON` | virtual | standard | bas | kW/ton |  | Chiller efficiency |  |
| `CH-1/LOAD-TONS` | virtual | advanced | bas | ton |  | Chiller cooling load |  |
| `CH-1/RUNHRS` | virtual | standard | bas | h |  | Run-hours (chiller run status) | Run_Time_Sensor |
| `CH-1/STARTS` | virtual | standard | bas | count |  | Start count (chiller run status) |  |

## CH-2 - Chiller

Water-cooled chiller (ReformulatedEIR)

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `CH-2/KW` | sensor | standard | energyplus | kW | power | Chiller power | Electric_Power_Sensor |
| `CH-2/LOAD` | sensor | advanced | energyplus | kW | power | Chiller cooling load (BTU meter) | Thermal_Power_Sensor |
| `CH-2/STS` | sensor | standard | energyplus | - | binary | Chiller run status | Run_Status |
| `CH-2/CHW-LWT` | sensor | standard | energyplus | degC | water_temperature | Evaporator leaving water temperature | Chilled_Water_Supply_Temperature_Sensor |
| `CH-2/CHW-EWT` | sensor | standard | energyplus | degC | water_temperature | Evaporator entering water temperature | Chilled_Water_Return_Temperature_Sensor |
| `CH-2/CDW-EWT` | sensor | standard | energyplus | degC | water_temperature | Condenser entering water temperature | Condenser_Water_Return_Temperature_Sensor |
| `CH-2/CDW-LWT` | sensor | standard | energyplus | degC | water_temperature | Condenser leaving water temperature | Condenser_Water_Supply_Temperature_Sensor |
| `CH-2/PLR` | truth | truth | energyplus | - |  | Chiller part load ratio |  |
| `CH-2/COP` | truth | truth | energyplus | - |  | Chiller COP (ground truth) |  |
| `CH-2/EN-CMD` | command | standard | bas | - |  | Chiller enable command | Enable_Command |
| `CH-2/PCT-RLA` | sensor | standard | energyplus | % | percent | Compressor current, percent of rated load amps | Current_Sensor |
| `CH-2/CHW-F` | sensor | advanced | energyplus | L/s | water_flow | Evaporator water flow | Chilled_Water_Flow_Sensor |
| `CH-2/CDW-F` | sensor | advanced | energyplus | L/s | water_flow | Condenser water flow | Condenser_Water_Flow_Sensor |
| `CH-2/EVAP-SAT-T` | sensor | advanced | surrogate | degC | water_temperature | Evaporator saturated refrigerant temperature (surrogate) | Temperature_Sensor |
| `CH-2/COND-SAT-T` | sensor | advanced | surrogate | degC | water_temperature | Condenser saturated refrigerant temperature (surrogate) | Temperature_Sensor |
| `CH-2/EVAP-P` | sensor | advanced | surrogate | kPa | refrigerant_pressure | Evaporator refrigerant pressure (abs.) (surrogate) | Refrigerant_Pressure_Sensor |
| `CH-2/COND-P` | sensor | advanced | surrogate | kPa | refrigerant_pressure | Condenser refrigerant pressure (abs.) (surrogate) | Refrigerant_Pressure_Sensor |
| `CH-2/ALM` | sensor | standard | model | - | binary | Chiller common alarm / lock-out | Alarm |
| `CH-2/KW-TON` | virtual | standard | bas | kW/ton |  | Chiller efficiency |  |
| `CH-2/LOAD-TONS` | virtual | advanced | bas | ton |  | Chiller cooling load |  |
| `CH-2/RUNHRS` | virtual | standard | bas | h |  | Run-hours (chiller run status) | Run_Time_Sensor |
| `CH-2/STARTS` | virtual | standard | bas | count |  | Start count (chiller run status) |  |

## HW-SYS - PlantLoop

Hot water system

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `HW-SYS/HW-ST` | sensor | standard | energyplus | degC | water_temperature | Hot water supply temperature | Supply_Water_Temperature_Sensor |
| `HW-SYS/HW-RT` | sensor | standard | energyplus | degC | water_temperature | Hot water return temperature | Return_Water_Temperature_Sensor |
| `HW-SYS/HW-F` | sensor | standard | energyplus | L/s | water_flow | Hot water flow | Water_Flow_Sensor |
| `HW-SYS/HW-DP` | sensor | standard | surrogate | kPa | pressure | Hot water differential pressure (surrogate model) | Differential_Pressure_Sensor |
| `HW-SYS/HW-ST-SP` | setpoint | standard | bas | degC |  | Hot water supply temperature set point | Supply_Water_Temperature_Setpoint |
| `HW-SYS/HW-DT` | virtual | standard | bas | K |  | Hot water delta-T (return - supply) |  |

## HWP-1 - Pump

Hot water pump (VariableSpeed)

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `HWP-1/KW` | sensor | standard | energyplus | kW | power | Pump power | Electric_Power_Sensor |
| `HWP-1/SPD` | sensor | standard | energyplus | % | percent | Pump speed (VFD output) | Frequency_Sensor |
| `HWP-1/STS` | sensor | standard | energyplus | - | binary | Pump status | Pump_Status |
| `HWP-1/HZ` | sensor | standard | energyplus | Hz | frequency | Pump VFD output frequency | Frequency_Sensor |
| `HWP-1/VIB` | sensor | next_gen | surrogate | mm/s | vibration | Pump vibration velocity, ISO 10816 (surrogate) | Vibration_Sensor |
| `HWP-1/RUNHRS` | virtual | standard | bas | h |  | Run-hours (pump status) | Run_Time_Sensor |
| `HWP-1/STARTS` | virtual | standard | bas | count |  | Start count (pump status) |  |

## BLR-1 - Boiler

Hot-water boiler (natural gas)

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `BLR-1/LOAD` | sensor | advanced | energyplus | kW | power | Boiler heating output | Thermal_Power_Sensor |
| `BLR-1/GAS-KW` | sensor | advanced | energyplus | kW | power | Boiler gas input | Natural_Gas_Usage_Sensor |
| `BLR-1/STS` | sensor | standard | energyplus | - | binary | Boiler firing status | Run_Status |
| `BLR-1/HW-LWT` | sensor | standard | energyplus | degC | water_temperature | Boiler leaving water temperature | Hot_Water_Supply_Temperature_Sensor |
| `BLR-1/HW-EWT` | sensor | standard | energyplus | degC | water_temperature | Boiler entering water temperature | Hot_Water_Return_Temperature_Sensor |
| `BLR-1/PLR` | truth | truth | energyplus | - |  | Boiler part load ratio |  |
| `BLR-1/EN-CMD` | command | standard | bas | - |  | Boiler enable command | Enable_Command |
| `BLR-1/FIRE-RATE` | sensor | standard | energyplus | % | percent | Burner firing rate (modulation) |  |
| `BLR-1/HW-F` | sensor | advanced | energyplus | L/s | water_flow | Boiler water flow | Hot_Water_Flow_Sensor |
| `BLR-1/FLUE-T` | sensor | advanced | surrogate | degC | air_temperature | Flue (stack) gas temperature (surrogate) | Exhaust_Air_Temperature_Sensor |
| `BLR-1/EFF` | truth | truth | energyplus | - |  | Boiler combustion efficiency (ground truth) |  |
| `BLR-1/ALM` | sensor | standard | model | - | binary | Boiler flame-failure / lock-out alarm | Alarm |
| `BLR-1/RUNHRS` | virtual | standard | bas | h |  | Run-hours (boiler firing status) | Run_Time_Sensor |
| `BLR-1/STARTS` | virtual | standard | bas | count |  | Start count (boiler firing status) |  |

## CW-SYS - PlantLoop

Condenser water system

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `CW-SYS/CW-ST` | sensor | standard | energyplus | degC | water_temperature | Condenser water supply temperature | Supply_Water_Temperature_Sensor |
| `CW-SYS/CW-RT` | sensor | standard | energyplus | degC | water_temperature | Condenser water return temperature | Return_Water_Temperature_Sensor |
| `CW-SYS/CW-F` | sensor | standard | energyplus | L/s | water_flow | Condenser water flow | Water_Flow_Sensor |
| `CW-SYS/CW-DP` | sensor | standard | surrogate | kPa | pressure | Condenser water differential pressure (surrogate model) | Differential_Pressure_Sensor |
| `CW-SYS/CW-ST-SP` | setpoint | standard | bas | degC |  | Condenser water supply temperature set point | Supply_Water_Temperature_Setpoint |
| `CW-SYS/CW-DT` | virtual | standard | bas | K |  | Condenser water delta-T (return - supply) |  |

## CWP-1 - Pump

Condenser water pump (ConstantSpeed)

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `CWP-1/KW` | sensor | standard | energyplus | kW | power | Pump power | Electric_Power_Sensor |
| `CWP-1/SPD` | sensor | standard | energyplus | % | percent | Pump speed (VFD output) | Frequency_Sensor |
| `CWP-1/STS` | sensor | standard | energyplus | - | binary | Pump status | Pump_Status |
| `CWP-1/HZ` | sensor | standard | energyplus | Hz | frequency | Pump VFD output frequency | Frequency_Sensor |
| `CWP-1/VIB` | sensor | next_gen | surrogate | mm/s | vibration | Pump vibration velocity, ISO 10816 (surrogate) | Vibration_Sensor |
| `CWP-1/RUNHRS` | virtual | standard | bas | h |  | Run-hours (pump status) | Run_Time_Sensor |
| `CWP-1/STARTS` | virtual | standard | bas | count |  | Start count (pump status) |  |

## CT-1 - CoolingTower

Cooling tower (SingleSpeed)

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `CT-1/FAN-KW` | sensor | standard | energyplus | kW | power | Tower fan power | Electric_Power_Sensor |
| `CT-1/FAN-STS` | sensor | standard | energyplus | - | binary | Tower fan status | Fan_Status |
| `CT-1/LWT` | sensor | standard | energyplus | degC | water_temperature | Tower leaving water temperature | Water_Temperature_Sensor |
| `CT-1/EWT` | sensor | standard | energyplus | degC | water_temperature | Tower entering water temperature | Water_Temperature_Sensor |
| `CT-1/FAN-SPD` | sensor | standard | energyplus | % | percent | Tower fan speed / duty (fan cycling ratio) | Frequency_Sensor |
| `CT-1/MAKEUP-F` | sensor | advanced | energyplus | L/s | water_flow | Make-up water flow (water meter) | Water_Flow_Sensor |
| `CT-1/EVAP-F` | truth | truth | energyplus | L/s |  | Evaporation loss (ground truth) |  |
| `CT-1/Q-REJ` | truth | truth | energyplus | kW |  | Heat rejection rate (ground truth) |  |
| `CT-1/ALM` | sensor | standard | model | - | binary | Tower vibration cut-out / VFD fault | Alarm |
| `CT-1/APPROACH` | virtual | standard | bas | K |  | Tower approach (leaving water - outdoor wet bulb) |  |
| `CT-1/RANGE` | virtual | standard | bas | K |  | Tower range (entering - leaving water) |  |
| `CT-1/FAN-RUNHRS` | virtual | standard | bas | h |  | Run-hours (tower fan status) | Run_Time_Sensor |
| `CT-1/FAN-STARTS` | virtual | standard | bas | count |  | Start count (tower fan status) |  |

## DHW-1 - WaterHeater

Domestic (service) hot-water heater, gas fired

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `DHW-1/TANK-T` | sensor | advanced | energyplus | degC | water_temperature | Tank water temperature | Hot_Water_Supply_Temperature_Sensor |
| `DHW-1/STS` | sensor | advanced | energyplus | - | binary | Burner status | Run_Status |
| `DHW-1/GAS-KW` | sensor | advanced | energyplus | kW | power | Gas input | Natural_Gas_Usage_Sensor |
| `DHW-1/USE-F` | sensor | next_gen | energyplus | L/s | water_flow | Hot-water draw (flow meter) | Water_Flow_Sensor |

## PLN-GroundFloor_Plenum - Plenum

Return-air plenum GroundFloor_Plenum

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `PLN-GroundFloor_Plenum/T` | sensor | advanced | energyplus | degC | air_temperature | Plenum air temperature | Air_Temperature_Sensor |

## PLN-MidFloor_Plenum - Plenum

Return-air plenum MidFloor_Plenum

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `PLN-MidFloor_Plenum/T` | sensor | advanced | energyplus | degC | air_temperature | Plenum air temperature | Air_Temperature_Sensor |

## PLN-TopFloor_Plenum - Plenum

Return-air plenum TopFloor_Plenum

| Point | Kind | Tier | Source | Unit | Sensor class | Description | Brick class |
|---|---|---|---|---|---|---|---|
| `PLN-TopFloor_Plenum/T` | sensor | advanced | energyplus | degC | air_temperature | Plenum air temperature | Air_Temperature_Sensor |
