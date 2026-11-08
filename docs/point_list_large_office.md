# BAS point list - DOE large office

518 points on 48 pieces of equipment (generated automatically from the EnergyPlus model).

## WX - WeatherStation

Rooftop weather station

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `WX/OA-T` | sensor | degC | Outdoor air dry-bulb temperature | Outside_Air_Temperature_Sensor |
| `WX/OA-RH` | sensor | %RH | Outdoor air relative humidity | Outside_Air_Humidity_Sensor |
| `WX/OA-WB` | sensor | degC | Outdoor air wet-bulb temperature (calculated by station) | Outside_Air_Wet_Bulb_Temperature_Sensor |
| `WX/WIND` | sensor | m/s | Wind speed | Wind_Speed_Sensor |
| `WX/SOLAR` | sensor | W/m2 | Global horizontal irradiance (pyranometer) | Solar_Radiance_Sensor |

## MTR - Meter

Utility and sub-meters

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `MTR/BLDG-ELEC-KW` | meter | kW | Whole-building electric demand | Electric_Power_Sensor |
| `MTR/BLDG-GAS-KW` | meter | kW | Whole-building natural gas rate | Electric_Power_Sensor |
| `MTR/HVAC-ELEC-KW` | meter | kW | HVAC electric demand | Electric_Power_Sensor |
| `MTR/LIGHT-KW` | meter | kW | Interior lighting demand | Electric_Power_Sensor |
| `MTR/PLUG-KW` | meter | kW | Plug and process load demand | Electric_Power_Sensor |
| `MTR/CLG-ELEC-KW` | meter | kW | Cooling (chiller) electric demand | Electric_Power_Sensor |
| `MTR/FAN-ELEC-KW` | meter | kW | Fan electric demand | Electric_Power_Sensor |
| `MTR/PUMP-ELEC-KW` | meter | kW | Pump electric demand | Electric_Power_Sensor |
| `MTR/HREJ-ELEC-KW` | meter | kW | Heat rejection electric demand | Electric_Power_Sensor |
| `MTR/HTG-GAS-KW` | meter | kW | Heating natural gas rate | Electric_Power_Sensor |

## ZN-Basement - Zone

Thermal zone Basement

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `ZN-Basement/ZN-T` | sensor | degC | Zone air temperature | Zone_Air_Temperature_Sensor |
| `ZN-Basement/ZN-RH` | sensor | %RH | Zone air relative humidity | Zone_Air_Humidity_Sensor |
| `ZN-Basement/ZN-CO2` | sensor | ppm | Zone CO2 concentration | CO2_Sensor |
| `ZN-Basement/ZN-OCC` | sensor | - | Zone occupancy sensor (PIR) | Occupancy_Sensor |
| `ZN-Basement/OCCUPANTS` | truth | people | True number of occupants (ground truth only) | Occupancy_Count_Sensor |
| `ZN-Basement/PMV` | truth | - | Fanger predicted mean vote (ground truth only) |  |
| `ZN-Basement/LIGHT-KW` | meter | kW | Zone lighting power | Electric_Power_Sensor |
| `ZN-Basement/PLUG-KW` | meter | kW | Zone plug load power | Electric_Power_Sensor |
| `ZN-Basement/HTG-SP` | setpoint | degC | Active heating set point | Zone_Air_Heating_Temperature_Setpoint |
| `ZN-Basement/CLG-SP` | setpoint | degC | Active cooling set point | Zone_Air_Cooling_Temperature_Setpoint |
| `ZN-Basement/OCC-HTG-SP` | setpoint | degC | Occupied heating set point | Occupied_Air_Temperature_Heating_Setpoint |
| `ZN-Basement/OCC-CLG-SP` | setpoint | degC | Occupied cooling set point | Occupied_Air_Temperature_Cooling_Setpoint |
| `ZN-Basement/OCC-MODE` | status | - | Zone occupancy mode (1 occupied / 0 unoccupied) | Occupancy_Status |

## VAV-Basement - VAV

VAV terminal with hot-water reheat serving Basement

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `VAV-Basement/DA-F` | sensor | m3/s | Discharge air flow | Discharge_Air_Flow_Sensor |
| `VAV-Basement/DA-T` | sensor | degC | Discharge air temperature | Discharge_Air_Temperature_Sensor |
| `VAV-Basement/DMPR-POS` | sensor | % | Damper position feedback | Damper_Position_Sensor |
| `VAV-Basement/RHV-POS` | sensor | % | Reheat valve position (feedback) | Valve_Position_Sensor |
| `VAV-Basement/RH-Q` | truth | kW | Reheat coil heat rate (ground truth) |  |
| `VAV-Basement/DA-F-SP` | setpoint | m3/s | Discharge air flow set point | Discharge_Air_Flow_Setpoint |
| `VAV-Basement/DMPR-CMD` | command | % | Damper command | Damper_Position_Command |
| `VAV-Basement/CLG-LOOP` | virtual | % | Cooling loop output |  |
| `VAV-Basement/HTG-LOOP` | virtual | % | Heating loop output |  |

## ZN-Core_bottom - Zone

Thermal zone Core_bottom

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `ZN-Core_bottom/ZN-T` | sensor | degC | Zone air temperature | Zone_Air_Temperature_Sensor |
| `ZN-Core_bottom/ZN-RH` | sensor | %RH | Zone air relative humidity | Zone_Air_Humidity_Sensor |
| `ZN-Core_bottom/ZN-CO2` | sensor | ppm | Zone CO2 concentration | CO2_Sensor |
| `ZN-Core_bottom/ZN-OCC` | sensor | - | Zone occupancy sensor (PIR) | Occupancy_Sensor |
| `ZN-Core_bottom/OCCUPANTS` | truth | people | True number of occupants (ground truth only) | Occupancy_Count_Sensor |
| `ZN-Core_bottom/PMV` | truth | - | Fanger predicted mean vote (ground truth only) |  |
| `ZN-Core_bottom/LIGHT-KW` | meter | kW | Zone lighting power | Electric_Power_Sensor |
| `ZN-Core_bottom/PLUG-KW` | meter | kW | Zone plug load power | Electric_Power_Sensor |
| `ZN-Core_bottom/HTG-SP` | setpoint | degC | Active heating set point | Zone_Air_Heating_Temperature_Setpoint |
| `ZN-Core_bottom/CLG-SP` | setpoint | degC | Active cooling set point | Zone_Air_Cooling_Temperature_Setpoint |
| `ZN-Core_bottom/OCC-HTG-SP` | setpoint | degC | Occupied heating set point | Occupied_Air_Temperature_Heating_Setpoint |
| `ZN-Core_bottom/OCC-CLG-SP` | setpoint | degC | Occupied cooling set point | Occupied_Air_Temperature_Cooling_Setpoint |
| `ZN-Core_bottom/OCC-MODE` | status | - | Zone occupancy mode (1 occupied / 0 unoccupied) | Occupancy_Status |

## VAV-Core_bottom - VAV

VAV terminal with hot-water reheat serving Core_bottom

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `VAV-Core_bottom/DA-F` | sensor | m3/s | Discharge air flow | Discharge_Air_Flow_Sensor |
| `VAV-Core_bottom/DA-T` | sensor | degC | Discharge air temperature | Discharge_Air_Temperature_Sensor |
| `VAV-Core_bottom/DMPR-POS` | sensor | % | Damper position feedback | Damper_Position_Sensor |
| `VAV-Core_bottom/RHV-POS` | sensor | % | Reheat valve position (feedback) | Valve_Position_Sensor |
| `VAV-Core_bottom/RH-Q` | truth | kW | Reheat coil heat rate (ground truth) |  |
| `VAV-Core_bottom/DA-F-SP` | setpoint | m3/s | Discharge air flow set point | Discharge_Air_Flow_Setpoint |
| `VAV-Core_bottom/DMPR-CMD` | command | % | Damper command | Damper_Position_Command |
| `VAV-Core_bottom/CLG-LOOP` | virtual | % | Cooling loop output |  |
| `VAV-Core_bottom/HTG-LOOP` | virtual | % | Heating loop output |  |

## ZN-Core_mid - Zone

Thermal zone Core_mid (x10 floors)

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `ZN-Core_mid/ZN-T` | sensor | degC | Zone air temperature | Zone_Air_Temperature_Sensor |
| `ZN-Core_mid/ZN-RH` | sensor | %RH | Zone air relative humidity | Zone_Air_Humidity_Sensor |
| `ZN-Core_mid/ZN-CO2` | sensor | ppm | Zone CO2 concentration | CO2_Sensor |
| `ZN-Core_mid/ZN-OCC` | sensor | - | Zone occupancy sensor (PIR) | Occupancy_Sensor |
| `ZN-Core_mid/OCCUPANTS` | truth | people | True number of occupants (ground truth only) | Occupancy_Count_Sensor |
| `ZN-Core_mid/PMV` | truth | - | Fanger predicted mean vote (ground truth only) |  |
| `ZN-Core_mid/LIGHT-KW` | meter | kW | Zone lighting power | Electric_Power_Sensor |
| `ZN-Core_mid/PLUG-KW` | meter | kW | Zone plug load power | Electric_Power_Sensor |
| `ZN-Core_mid/HTG-SP` | setpoint | degC | Active heating set point | Zone_Air_Heating_Temperature_Setpoint |
| `ZN-Core_mid/CLG-SP` | setpoint | degC | Active cooling set point | Zone_Air_Cooling_Temperature_Setpoint |
| `ZN-Core_mid/OCC-HTG-SP` | setpoint | degC | Occupied heating set point | Occupied_Air_Temperature_Heating_Setpoint |
| `ZN-Core_mid/OCC-CLG-SP` | setpoint | degC | Occupied cooling set point | Occupied_Air_Temperature_Cooling_Setpoint |
| `ZN-Core_mid/OCC-MODE` | status | - | Zone occupancy mode (1 occupied / 0 unoccupied) | Occupancy_Status |

## VAV-Core_mid - VAV

VAV terminal with hot-water reheat serving Core_mid

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `VAV-Core_mid/DA-F` | sensor | m3/s | Discharge air flow | Discharge_Air_Flow_Sensor |
| `VAV-Core_mid/DA-T` | sensor | degC | Discharge air temperature | Discharge_Air_Temperature_Sensor |
| `VAV-Core_mid/DMPR-POS` | sensor | % | Damper position feedback | Damper_Position_Sensor |
| `VAV-Core_mid/RHV-POS` | sensor | % | Reheat valve position (feedback) | Valve_Position_Sensor |
| `VAV-Core_mid/RH-Q` | truth | kW | Reheat coil heat rate (ground truth) |  |
| `VAV-Core_mid/DA-F-SP` | setpoint | m3/s | Discharge air flow set point | Discharge_Air_Flow_Setpoint |
| `VAV-Core_mid/DMPR-CMD` | command | % | Damper command | Damper_Position_Command |
| `VAV-Core_mid/CLG-LOOP` | virtual | % | Cooling loop output |  |
| `VAV-Core_mid/HTG-LOOP` | virtual | % | Heating loop output |  |

## ZN-Core_top - Zone

Thermal zone Core_top

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `ZN-Core_top/ZN-T` | sensor | degC | Zone air temperature | Zone_Air_Temperature_Sensor |
| `ZN-Core_top/ZN-RH` | sensor | %RH | Zone air relative humidity | Zone_Air_Humidity_Sensor |
| `ZN-Core_top/ZN-CO2` | sensor | ppm | Zone CO2 concentration | CO2_Sensor |
| `ZN-Core_top/ZN-OCC` | sensor | - | Zone occupancy sensor (PIR) | Occupancy_Sensor |
| `ZN-Core_top/OCCUPANTS` | truth | people | True number of occupants (ground truth only) | Occupancy_Count_Sensor |
| `ZN-Core_top/PMV` | truth | - | Fanger predicted mean vote (ground truth only) |  |
| `ZN-Core_top/LIGHT-KW` | meter | kW | Zone lighting power | Electric_Power_Sensor |
| `ZN-Core_top/PLUG-KW` | meter | kW | Zone plug load power | Electric_Power_Sensor |
| `ZN-Core_top/HTG-SP` | setpoint | degC | Active heating set point | Zone_Air_Heating_Temperature_Setpoint |
| `ZN-Core_top/CLG-SP` | setpoint | degC | Active cooling set point | Zone_Air_Cooling_Temperature_Setpoint |
| `ZN-Core_top/OCC-HTG-SP` | setpoint | degC | Occupied heating set point | Occupied_Air_Temperature_Heating_Setpoint |
| `ZN-Core_top/OCC-CLG-SP` | setpoint | degC | Occupied cooling set point | Occupied_Air_Temperature_Cooling_Setpoint |
| `ZN-Core_top/OCC-MODE` | status | - | Zone occupancy mode (1 occupied / 0 unoccupied) | Occupancy_Status |

## VAV-Core_top - VAV

VAV terminal with hot-water reheat serving Core_top

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `VAV-Core_top/DA-F` | sensor | m3/s | Discharge air flow | Discharge_Air_Flow_Sensor |
| `VAV-Core_top/DA-T` | sensor | degC | Discharge air temperature | Discharge_Air_Temperature_Sensor |
| `VAV-Core_top/DMPR-POS` | sensor | % | Damper position feedback | Damper_Position_Sensor |
| `VAV-Core_top/RHV-POS` | sensor | % | Reheat valve position (feedback) | Valve_Position_Sensor |
| `VAV-Core_top/RH-Q` | truth | kW | Reheat coil heat rate (ground truth) |  |
| `VAV-Core_top/DA-F-SP` | setpoint | m3/s | Discharge air flow set point | Discharge_Air_Flow_Setpoint |
| `VAV-Core_top/DMPR-CMD` | command | % | Damper command | Damper_Position_Command |
| `VAV-Core_top/CLG-LOOP` | virtual | % | Cooling loop output |  |
| `VAV-Core_top/HTG-LOOP` | virtual | % | Heating loop output |  |

## ZN-Perimeter_bot_ZN_1 - Zone

Thermal zone Perimeter_bot_ZN_1

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `ZN-Perimeter_bot_ZN_1/ZN-T` | sensor | degC | Zone air temperature | Zone_Air_Temperature_Sensor |
| `ZN-Perimeter_bot_ZN_1/ZN-RH` | sensor | %RH | Zone air relative humidity | Zone_Air_Humidity_Sensor |
| `ZN-Perimeter_bot_ZN_1/ZN-CO2` | sensor | ppm | Zone CO2 concentration | CO2_Sensor |
| `ZN-Perimeter_bot_ZN_1/ZN-OCC` | sensor | - | Zone occupancy sensor (PIR) | Occupancy_Sensor |
| `ZN-Perimeter_bot_ZN_1/OCCUPANTS` | truth | people | True number of occupants (ground truth only) | Occupancy_Count_Sensor |
| `ZN-Perimeter_bot_ZN_1/PMV` | truth | - | Fanger predicted mean vote (ground truth only) |  |
| `ZN-Perimeter_bot_ZN_1/LIGHT-KW` | meter | kW | Zone lighting power | Electric_Power_Sensor |
| `ZN-Perimeter_bot_ZN_1/PLUG-KW` | meter | kW | Zone plug load power | Electric_Power_Sensor |
| `ZN-Perimeter_bot_ZN_1/HTG-SP` | setpoint | degC | Active heating set point | Zone_Air_Heating_Temperature_Setpoint |
| `ZN-Perimeter_bot_ZN_1/CLG-SP` | setpoint | degC | Active cooling set point | Zone_Air_Cooling_Temperature_Setpoint |
| `ZN-Perimeter_bot_ZN_1/OCC-HTG-SP` | setpoint | degC | Occupied heating set point | Occupied_Air_Temperature_Heating_Setpoint |
| `ZN-Perimeter_bot_ZN_1/OCC-CLG-SP` | setpoint | degC | Occupied cooling set point | Occupied_Air_Temperature_Cooling_Setpoint |
| `ZN-Perimeter_bot_ZN_1/OCC-MODE` | status | - | Zone occupancy mode (1 occupied / 0 unoccupied) | Occupancy_Status |

## VAV-Perimeter_bot_ZN_1 - VAV

VAV terminal with hot-water reheat serving Perimeter_bot_ZN_1

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `VAV-Perimeter_bot_ZN_1/DA-F` | sensor | m3/s | Discharge air flow | Discharge_Air_Flow_Sensor |
| `VAV-Perimeter_bot_ZN_1/DA-T` | sensor | degC | Discharge air temperature | Discharge_Air_Temperature_Sensor |
| `VAV-Perimeter_bot_ZN_1/DMPR-POS` | sensor | % | Damper position feedback | Damper_Position_Sensor |
| `VAV-Perimeter_bot_ZN_1/RHV-POS` | sensor | % | Reheat valve position (feedback) | Valve_Position_Sensor |
| `VAV-Perimeter_bot_ZN_1/RH-Q` | truth | kW | Reheat coil heat rate (ground truth) |  |
| `VAV-Perimeter_bot_ZN_1/DA-F-SP` | setpoint | m3/s | Discharge air flow set point | Discharge_Air_Flow_Setpoint |
| `VAV-Perimeter_bot_ZN_1/DMPR-CMD` | command | % | Damper command | Damper_Position_Command |
| `VAV-Perimeter_bot_ZN_1/CLG-LOOP` | virtual | % | Cooling loop output |  |
| `VAV-Perimeter_bot_ZN_1/HTG-LOOP` | virtual | % | Heating loop output |  |

## ZN-Perimeter_bot_ZN_2 - Zone

Thermal zone Perimeter_bot_ZN_2

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `ZN-Perimeter_bot_ZN_2/ZN-T` | sensor | degC | Zone air temperature | Zone_Air_Temperature_Sensor |
| `ZN-Perimeter_bot_ZN_2/ZN-RH` | sensor | %RH | Zone air relative humidity | Zone_Air_Humidity_Sensor |
| `ZN-Perimeter_bot_ZN_2/ZN-CO2` | sensor | ppm | Zone CO2 concentration | CO2_Sensor |
| `ZN-Perimeter_bot_ZN_2/ZN-OCC` | sensor | - | Zone occupancy sensor (PIR) | Occupancy_Sensor |
| `ZN-Perimeter_bot_ZN_2/OCCUPANTS` | truth | people | True number of occupants (ground truth only) | Occupancy_Count_Sensor |
| `ZN-Perimeter_bot_ZN_2/PMV` | truth | - | Fanger predicted mean vote (ground truth only) |  |
| `ZN-Perimeter_bot_ZN_2/LIGHT-KW` | meter | kW | Zone lighting power | Electric_Power_Sensor |
| `ZN-Perimeter_bot_ZN_2/PLUG-KW` | meter | kW | Zone plug load power | Electric_Power_Sensor |
| `ZN-Perimeter_bot_ZN_2/HTG-SP` | setpoint | degC | Active heating set point | Zone_Air_Heating_Temperature_Setpoint |
| `ZN-Perimeter_bot_ZN_2/CLG-SP` | setpoint | degC | Active cooling set point | Zone_Air_Cooling_Temperature_Setpoint |
| `ZN-Perimeter_bot_ZN_2/OCC-HTG-SP` | setpoint | degC | Occupied heating set point | Occupied_Air_Temperature_Heating_Setpoint |
| `ZN-Perimeter_bot_ZN_2/OCC-CLG-SP` | setpoint | degC | Occupied cooling set point | Occupied_Air_Temperature_Cooling_Setpoint |
| `ZN-Perimeter_bot_ZN_2/OCC-MODE` | status | - | Zone occupancy mode (1 occupied / 0 unoccupied) | Occupancy_Status |

## VAV-Perimeter_bot_ZN_2 - VAV

VAV terminal with hot-water reheat serving Perimeter_bot_ZN_2

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `VAV-Perimeter_bot_ZN_2/DA-F` | sensor | m3/s | Discharge air flow | Discharge_Air_Flow_Sensor |
| `VAV-Perimeter_bot_ZN_2/DA-T` | sensor | degC | Discharge air temperature | Discharge_Air_Temperature_Sensor |
| `VAV-Perimeter_bot_ZN_2/DMPR-POS` | sensor | % | Damper position feedback | Damper_Position_Sensor |
| `VAV-Perimeter_bot_ZN_2/RHV-POS` | sensor | % | Reheat valve position (feedback) | Valve_Position_Sensor |
| `VAV-Perimeter_bot_ZN_2/RH-Q` | truth | kW | Reheat coil heat rate (ground truth) |  |
| `VAV-Perimeter_bot_ZN_2/DA-F-SP` | setpoint | m3/s | Discharge air flow set point | Discharge_Air_Flow_Setpoint |
| `VAV-Perimeter_bot_ZN_2/DMPR-CMD` | command | % | Damper command | Damper_Position_Command |
| `VAV-Perimeter_bot_ZN_2/CLG-LOOP` | virtual | % | Cooling loop output |  |
| `VAV-Perimeter_bot_ZN_2/HTG-LOOP` | virtual | % | Heating loop output |  |

## ZN-Perimeter_bot_ZN_3 - Zone

Thermal zone Perimeter_bot_ZN_3

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `ZN-Perimeter_bot_ZN_3/ZN-T` | sensor | degC | Zone air temperature | Zone_Air_Temperature_Sensor |
| `ZN-Perimeter_bot_ZN_3/ZN-RH` | sensor | %RH | Zone air relative humidity | Zone_Air_Humidity_Sensor |
| `ZN-Perimeter_bot_ZN_3/ZN-CO2` | sensor | ppm | Zone CO2 concentration | CO2_Sensor |
| `ZN-Perimeter_bot_ZN_3/ZN-OCC` | sensor | - | Zone occupancy sensor (PIR) | Occupancy_Sensor |
| `ZN-Perimeter_bot_ZN_3/OCCUPANTS` | truth | people | True number of occupants (ground truth only) | Occupancy_Count_Sensor |
| `ZN-Perimeter_bot_ZN_3/PMV` | truth | - | Fanger predicted mean vote (ground truth only) |  |
| `ZN-Perimeter_bot_ZN_3/LIGHT-KW` | meter | kW | Zone lighting power | Electric_Power_Sensor |
| `ZN-Perimeter_bot_ZN_3/PLUG-KW` | meter | kW | Zone plug load power | Electric_Power_Sensor |
| `ZN-Perimeter_bot_ZN_3/HTG-SP` | setpoint | degC | Active heating set point | Zone_Air_Heating_Temperature_Setpoint |
| `ZN-Perimeter_bot_ZN_3/CLG-SP` | setpoint | degC | Active cooling set point | Zone_Air_Cooling_Temperature_Setpoint |
| `ZN-Perimeter_bot_ZN_3/OCC-HTG-SP` | setpoint | degC | Occupied heating set point | Occupied_Air_Temperature_Heating_Setpoint |
| `ZN-Perimeter_bot_ZN_3/OCC-CLG-SP` | setpoint | degC | Occupied cooling set point | Occupied_Air_Temperature_Cooling_Setpoint |
| `ZN-Perimeter_bot_ZN_3/OCC-MODE` | status | - | Zone occupancy mode (1 occupied / 0 unoccupied) | Occupancy_Status |

## VAV-Perimeter_bot_ZN_3 - VAV

VAV terminal with hot-water reheat serving Perimeter_bot_ZN_3

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `VAV-Perimeter_bot_ZN_3/DA-F` | sensor | m3/s | Discharge air flow | Discharge_Air_Flow_Sensor |
| `VAV-Perimeter_bot_ZN_3/DA-T` | sensor | degC | Discharge air temperature | Discharge_Air_Temperature_Sensor |
| `VAV-Perimeter_bot_ZN_3/DMPR-POS` | sensor | % | Damper position feedback | Damper_Position_Sensor |
| `VAV-Perimeter_bot_ZN_3/RHV-POS` | sensor | % | Reheat valve position (feedback) | Valve_Position_Sensor |
| `VAV-Perimeter_bot_ZN_3/RH-Q` | truth | kW | Reheat coil heat rate (ground truth) |  |
| `VAV-Perimeter_bot_ZN_3/DA-F-SP` | setpoint | m3/s | Discharge air flow set point | Discharge_Air_Flow_Setpoint |
| `VAV-Perimeter_bot_ZN_3/DMPR-CMD` | command | % | Damper command | Damper_Position_Command |
| `VAV-Perimeter_bot_ZN_3/CLG-LOOP` | virtual | % | Cooling loop output |  |
| `VAV-Perimeter_bot_ZN_3/HTG-LOOP` | virtual | % | Heating loop output |  |

## ZN-Perimeter_bot_ZN_4 - Zone

Thermal zone Perimeter_bot_ZN_4

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `ZN-Perimeter_bot_ZN_4/ZN-T` | sensor | degC | Zone air temperature | Zone_Air_Temperature_Sensor |
| `ZN-Perimeter_bot_ZN_4/ZN-RH` | sensor | %RH | Zone air relative humidity | Zone_Air_Humidity_Sensor |
| `ZN-Perimeter_bot_ZN_4/ZN-CO2` | sensor | ppm | Zone CO2 concentration | CO2_Sensor |
| `ZN-Perimeter_bot_ZN_4/ZN-OCC` | sensor | - | Zone occupancy sensor (PIR) | Occupancy_Sensor |
| `ZN-Perimeter_bot_ZN_4/OCCUPANTS` | truth | people | True number of occupants (ground truth only) | Occupancy_Count_Sensor |
| `ZN-Perimeter_bot_ZN_4/PMV` | truth | - | Fanger predicted mean vote (ground truth only) |  |
| `ZN-Perimeter_bot_ZN_4/LIGHT-KW` | meter | kW | Zone lighting power | Electric_Power_Sensor |
| `ZN-Perimeter_bot_ZN_4/PLUG-KW` | meter | kW | Zone plug load power | Electric_Power_Sensor |
| `ZN-Perimeter_bot_ZN_4/HTG-SP` | setpoint | degC | Active heating set point | Zone_Air_Heating_Temperature_Setpoint |
| `ZN-Perimeter_bot_ZN_4/CLG-SP` | setpoint | degC | Active cooling set point | Zone_Air_Cooling_Temperature_Setpoint |
| `ZN-Perimeter_bot_ZN_4/OCC-HTG-SP` | setpoint | degC | Occupied heating set point | Occupied_Air_Temperature_Heating_Setpoint |
| `ZN-Perimeter_bot_ZN_4/OCC-CLG-SP` | setpoint | degC | Occupied cooling set point | Occupied_Air_Temperature_Cooling_Setpoint |
| `ZN-Perimeter_bot_ZN_4/OCC-MODE` | status | - | Zone occupancy mode (1 occupied / 0 unoccupied) | Occupancy_Status |

## VAV-Perimeter_bot_ZN_4 - VAV

VAV terminal with hot-water reheat serving Perimeter_bot_ZN_4

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `VAV-Perimeter_bot_ZN_4/DA-F` | sensor | m3/s | Discharge air flow | Discharge_Air_Flow_Sensor |
| `VAV-Perimeter_bot_ZN_4/DA-T` | sensor | degC | Discharge air temperature | Discharge_Air_Temperature_Sensor |
| `VAV-Perimeter_bot_ZN_4/DMPR-POS` | sensor | % | Damper position feedback | Damper_Position_Sensor |
| `VAV-Perimeter_bot_ZN_4/RHV-POS` | sensor | % | Reheat valve position (feedback) | Valve_Position_Sensor |
| `VAV-Perimeter_bot_ZN_4/RH-Q` | truth | kW | Reheat coil heat rate (ground truth) |  |
| `VAV-Perimeter_bot_ZN_4/DA-F-SP` | setpoint | m3/s | Discharge air flow set point | Discharge_Air_Flow_Setpoint |
| `VAV-Perimeter_bot_ZN_4/DMPR-CMD` | command | % | Damper command | Damper_Position_Command |
| `VAV-Perimeter_bot_ZN_4/CLG-LOOP` | virtual | % | Cooling loop output |  |
| `VAV-Perimeter_bot_ZN_4/HTG-LOOP` | virtual | % | Heating loop output |  |

## ZN-Perimeter_mid_ZN_1 - Zone

Thermal zone Perimeter_mid_ZN_1 (x10 floors)

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `ZN-Perimeter_mid_ZN_1/ZN-T` | sensor | degC | Zone air temperature | Zone_Air_Temperature_Sensor |
| `ZN-Perimeter_mid_ZN_1/ZN-RH` | sensor | %RH | Zone air relative humidity | Zone_Air_Humidity_Sensor |
| `ZN-Perimeter_mid_ZN_1/ZN-CO2` | sensor | ppm | Zone CO2 concentration | CO2_Sensor |
| `ZN-Perimeter_mid_ZN_1/ZN-OCC` | sensor | - | Zone occupancy sensor (PIR) | Occupancy_Sensor |
| `ZN-Perimeter_mid_ZN_1/OCCUPANTS` | truth | people | True number of occupants (ground truth only) | Occupancy_Count_Sensor |
| `ZN-Perimeter_mid_ZN_1/PMV` | truth | - | Fanger predicted mean vote (ground truth only) |  |
| `ZN-Perimeter_mid_ZN_1/LIGHT-KW` | meter | kW | Zone lighting power | Electric_Power_Sensor |
| `ZN-Perimeter_mid_ZN_1/PLUG-KW` | meter | kW | Zone plug load power | Electric_Power_Sensor |
| `ZN-Perimeter_mid_ZN_1/HTG-SP` | setpoint | degC | Active heating set point | Zone_Air_Heating_Temperature_Setpoint |
| `ZN-Perimeter_mid_ZN_1/CLG-SP` | setpoint | degC | Active cooling set point | Zone_Air_Cooling_Temperature_Setpoint |
| `ZN-Perimeter_mid_ZN_1/OCC-HTG-SP` | setpoint | degC | Occupied heating set point | Occupied_Air_Temperature_Heating_Setpoint |
| `ZN-Perimeter_mid_ZN_1/OCC-CLG-SP` | setpoint | degC | Occupied cooling set point | Occupied_Air_Temperature_Cooling_Setpoint |
| `ZN-Perimeter_mid_ZN_1/OCC-MODE` | status | - | Zone occupancy mode (1 occupied / 0 unoccupied) | Occupancy_Status |

## VAV-Perimeter_mid_ZN_1 - VAV

VAV terminal with hot-water reheat serving Perimeter_mid_ZN_1

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `VAV-Perimeter_mid_ZN_1/DA-F` | sensor | m3/s | Discharge air flow | Discharge_Air_Flow_Sensor |
| `VAV-Perimeter_mid_ZN_1/DA-T` | sensor | degC | Discharge air temperature | Discharge_Air_Temperature_Sensor |
| `VAV-Perimeter_mid_ZN_1/DMPR-POS` | sensor | % | Damper position feedback | Damper_Position_Sensor |
| `VAV-Perimeter_mid_ZN_1/RHV-POS` | sensor | % | Reheat valve position (feedback) | Valve_Position_Sensor |
| `VAV-Perimeter_mid_ZN_1/RH-Q` | truth | kW | Reheat coil heat rate (ground truth) |  |
| `VAV-Perimeter_mid_ZN_1/DA-F-SP` | setpoint | m3/s | Discharge air flow set point | Discharge_Air_Flow_Setpoint |
| `VAV-Perimeter_mid_ZN_1/DMPR-CMD` | command | % | Damper command | Damper_Position_Command |
| `VAV-Perimeter_mid_ZN_1/CLG-LOOP` | virtual | % | Cooling loop output |  |
| `VAV-Perimeter_mid_ZN_1/HTG-LOOP` | virtual | % | Heating loop output |  |

## ZN-Perimeter_mid_ZN_2 - Zone

Thermal zone Perimeter_mid_ZN_2 (x10 floors)

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `ZN-Perimeter_mid_ZN_2/ZN-T` | sensor | degC | Zone air temperature | Zone_Air_Temperature_Sensor |
| `ZN-Perimeter_mid_ZN_2/ZN-RH` | sensor | %RH | Zone air relative humidity | Zone_Air_Humidity_Sensor |
| `ZN-Perimeter_mid_ZN_2/ZN-CO2` | sensor | ppm | Zone CO2 concentration | CO2_Sensor |
| `ZN-Perimeter_mid_ZN_2/ZN-OCC` | sensor | - | Zone occupancy sensor (PIR) | Occupancy_Sensor |
| `ZN-Perimeter_mid_ZN_2/OCCUPANTS` | truth | people | True number of occupants (ground truth only) | Occupancy_Count_Sensor |
| `ZN-Perimeter_mid_ZN_2/PMV` | truth | - | Fanger predicted mean vote (ground truth only) |  |
| `ZN-Perimeter_mid_ZN_2/LIGHT-KW` | meter | kW | Zone lighting power | Electric_Power_Sensor |
| `ZN-Perimeter_mid_ZN_2/PLUG-KW` | meter | kW | Zone plug load power | Electric_Power_Sensor |
| `ZN-Perimeter_mid_ZN_2/HTG-SP` | setpoint | degC | Active heating set point | Zone_Air_Heating_Temperature_Setpoint |
| `ZN-Perimeter_mid_ZN_2/CLG-SP` | setpoint | degC | Active cooling set point | Zone_Air_Cooling_Temperature_Setpoint |
| `ZN-Perimeter_mid_ZN_2/OCC-HTG-SP` | setpoint | degC | Occupied heating set point | Occupied_Air_Temperature_Heating_Setpoint |
| `ZN-Perimeter_mid_ZN_2/OCC-CLG-SP` | setpoint | degC | Occupied cooling set point | Occupied_Air_Temperature_Cooling_Setpoint |
| `ZN-Perimeter_mid_ZN_2/OCC-MODE` | status | - | Zone occupancy mode (1 occupied / 0 unoccupied) | Occupancy_Status |

## VAV-Perimeter_mid_ZN_2 - VAV

VAV terminal with hot-water reheat serving Perimeter_mid_ZN_2

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `VAV-Perimeter_mid_ZN_2/DA-F` | sensor | m3/s | Discharge air flow | Discharge_Air_Flow_Sensor |
| `VAV-Perimeter_mid_ZN_2/DA-T` | sensor | degC | Discharge air temperature | Discharge_Air_Temperature_Sensor |
| `VAV-Perimeter_mid_ZN_2/DMPR-POS` | sensor | % | Damper position feedback | Damper_Position_Sensor |
| `VAV-Perimeter_mid_ZN_2/RHV-POS` | sensor | % | Reheat valve position (feedback) | Valve_Position_Sensor |
| `VAV-Perimeter_mid_ZN_2/RH-Q` | truth | kW | Reheat coil heat rate (ground truth) |  |
| `VAV-Perimeter_mid_ZN_2/DA-F-SP` | setpoint | m3/s | Discharge air flow set point | Discharge_Air_Flow_Setpoint |
| `VAV-Perimeter_mid_ZN_2/DMPR-CMD` | command | % | Damper command | Damper_Position_Command |
| `VAV-Perimeter_mid_ZN_2/CLG-LOOP` | virtual | % | Cooling loop output |  |
| `VAV-Perimeter_mid_ZN_2/HTG-LOOP` | virtual | % | Heating loop output |  |

## ZN-Perimeter_mid_ZN_3 - Zone

Thermal zone Perimeter_mid_ZN_3 (x10 floors)

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `ZN-Perimeter_mid_ZN_3/ZN-T` | sensor | degC | Zone air temperature | Zone_Air_Temperature_Sensor |
| `ZN-Perimeter_mid_ZN_3/ZN-RH` | sensor | %RH | Zone air relative humidity | Zone_Air_Humidity_Sensor |
| `ZN-Perimeter_mid_ZN_3/ZN-CO2` | sensor | ppm | Zone CO2 concentration | CO2_Sensor |
| `ZN-Perimeter_mid_ZN_3/ZN-OCC` | sensor | - | Zone occupancy sensor (PIR) | Occupancy_Sensor |
| `ZN-Perimeter_mid_ZN_3/OCCUPANTS` | truth | people | True number of occupants (ground truth only) | Occupancy_Count_Sensor |
| `ZN-Perimeter_mid_ZN_3/PMV` | truth | - | Fanger predicted mean vote (ground truth only) |  |
| `ZN-Perimeter_mid_ZN_3/LIGHT-KW` | meter | kW | Zone lighting power | Electric_Power_Sensor |
| `ZN-Perimeter_mid_ZN_3/PLUG-KW` | meter | kW | Zone plug load power | Electric_Power_Sensor |
| `ZN-Perimeter_mid_ZN_3/HTG-SP` | setpoint | degC | Active heating set point | Zone_Air_Heating_Temperature_Setpoint |
| `ZN-Perimeter_mid_ZN_3/CLG-SP` | setpoint | degC | Active cooling set point | Zone_Air_Cooling_Temperature_Setpoint |
| `ZN-Perimeter_mid_ZN_3/OCC-HTG-SP` | setpoint | degC | Occupied heating set point | Occupied_Air_Temperature_Heating_Setpoint |
| `ZN-Perimeter_mid_ZN_3/OCC-CLG-SP` | setpoint | degC | Occupied cooling set point | Occupied_Air_Temperature_Cooling_Setpoint |
| `ZN-Perimeter_mid_ZN_3/OCC-MODE` | status | - | Zone occupancy mode (1 occupied / 0 unoccupied) | Occupancy_Status |

## VAV-Perimeter_mid_ZN_3 - VAV

VAV terminal with hot-water reheat serving Perimeter_mid_ZN_3

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `VAV-Perimeter_mid_ZN_3/DA-F` | sensor | m3/s | Discharge air flow | Discharge_Air_Flow_Sensor |
| `VAV-Perimeter_mid_ZN_3/DA-T` | sensor | degC | Discharge air temperature | Discharge_Air_Temperature_Sensor |
| `VAV-Perimeter_mid_ZN_3/DMPR-POS` | sensor | % | Damper position feedback | Damper_Position_Sensor |
| `VAV-Perimeter_mid_ZN_3/RHV-POS` | sensor | % | Reheat valve position (feedback) | Valve_Position_Sensor |
| `VAV-Perimeter_mid_ZN_3/RH-Q` | truth | kW | Reheat coil heat rate (ground truth) |  |
| `VAV-Perimeter_mid_ZN_3/DA-F-SP` | setpoint | m3/s | Discharge air flow set point | Discharge_Air_Flow_Setpoint |
| `VAV-Perimeter_mid_ZN_3/DMPR-CMD` | command | % | Damper command | Damper_Position_Command |
| `VAV-Perimeter_mid_ZN_3/CLG-LOOP` | virtual | % | Cooling loop output |  |
| `VAV-Perimeter_mid_ZN_3/HTG-LOOP` | virtual | % | Heating loop output |  |

## ZN-Perimeter_mid_ZN_4 - Zone

Thermal zone Perimeter_mid_ZN_4 (x10 floors)

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `ZN-Perimeter_mid_ZN_4/ZN-T` | sensor | degC | Zone air temperature | Zone_Air_Temperature_Sensor |
| `ZN-Perimeter_mid_ZN_4/ZN-RH` | sensor | %RH | Zone air relative humidity | Zone_Air_Humidity_Sensor |
| `ZN-Perimeter_mid_ZN_4/ZN-CO2` | sensor | ppm | Zone CO2 concentration | CO2_Sensor |
| `ZN-Perimeter_mid_ZN_4/ZN-OCC` | sensor | - | Zone occupancy sensor (PIR) | Occupancy_Sensor |
| `ZN-Perimeter_mid_ZN_4/OCCUPANTS` | truth | people | True number of occupants (ground truth only) | Occupancy_Count_Sensor |
| `ZN-Perimeter_mid_ZN_4/PMV` | truth | - | Fanger predicted mean vote (ground truth only) |  |
| `ZN-Perimeter_mid_ZN_4/LIGHT-KW` | meter | kW | Zone lighting power | Electric_Power_Sensor |
| `ZN-Perimeter_mid_ZN_4/PLUG-KW` | meter | kW | Zone plug load power | Electric_Power_Sensor |
| `ZN-Perimeter_mid_ZN_4/HTG-SP` | setpoint | degC | Active heating set point | Zone_Air_Heating_Temperature_Setpoint |
| `ZN-Perimeter_mid_ZN_4/CLG-SP` | setpoint | degC | Active cooling set point | Zone_Air_Cooling_Temperature_Setpoint |
| `ZN-Perimeter_mid_ZN_4/OCC-HTG-SP` | setpoint | degC | Occupied heating set point | Occupied_Air_Temperature_Heating_Setpoint |
| `ZN-Perimeter_mid_ZN_4/OCC-CLG-SP` | setpoint | degC | Occupied cooling set point | Occupied_Air_Temperature_Cooling_Setpoint |
| `ZN-Perimeter_mid_ZN_4/OCC-MODE` | status | - | Zone occupancy mode (1 occupied / 0 unoccupied) | Occupancy_Status |

## VAV-Perimeter_mid_ZN_4 - VAV

VAV terminal with hot-water reheat serving Perimeter_mid_ZN_4

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `VAV-Perimeter_mid_ZN_4/DA-F` | sensor | m3/s | Discharge air flow | Discharge_Air_Flow_Sensor |
| `VAV-Perimeter_mid_ZN_4/DA-T` | sensor | degC | Discharge air temperature | Discharge_Air_Temperature_Sensor |
| `VAV-Perimeter_mid_ZN_4/DMPR-POS` | sensor | % | Damper position feedback | Damper_Position_Sensor |
| `VAV-Perimeter_mid_ZN_4/RHV-POS` | sensor | % | Reheat valve position (feedback) | Valve_Position_Sensor |
| `VAV-Perimeter_mid_ZN_4/RH-Q` | truth | kW | Reheat coil heat rate (ground truth) |  |
| `VAV-Perimeter_mid_ZN_4/DA-F-SP` | setpoint | m3/s | Discharge air flow set point | Discharge_Air_Flow_Setpoint |
| `VAV-Perimeter_mid_ZN_4/DMPR-CMD` | command | % | Damper command | Damper_Position_Command |
| `VAV-Perimeter_mid_ZN_4/CLG-LOOP` | virtual | % | Cooling loop output |  |
| `VAV-Perimeter_mid_ZN_4/HTG-LOOP` | virtual | % | Heating loop output |  |

## ZN-Perimeter_top_ZN_1 - Zone

Thermal zone Perimeter_top_ZN_1

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `ZN-Perimeter_top_ZN_1/ZN-T` | sensor | degC | Zone air temperature | Zone_Air_Temperature_Sensor |
| `ZN-Perimeter_top_ZN_1/ZN-RH` | sensor | %RH | Zone air relative humidity | Zone_Air_Humidity_Sensor |
| `ZN-Perimeter_top_ZN_1/ZN-CO2` | sensor | ppm | Zone CO2 concentration | CO2_Sensor |
| `ZN-Perimeter_top_ZN_1/ZN-OCC` | sensor | - | Zone occupancy sensor (PIR) | Occupancy_Sensor |
| `ZN-Perimeter_top_ZN_1/OCCUPANTS` | truth | people | True number of occupants (ground truth only) | Occupancy_Count_Sensor |
| `ZN-Perimeter_top_ZN_1/PMV` | truth | - | Fanger predicted mean vote (ground truth only) |  |
| `ZN-Perimeter_top_ZN_1/LIGHT-KW` | meter | kW | Zone lighting power | Electric_Power_Sensor |
| `ZN-Perimeter_top_ZN_1/PLUG-KW` | meter | kW | Zone plug load power | Electric_Power_Sensor |
| `ZN-Perimeter_top_ZN_1/HTG-SP` | setpoint | degC | Active heating set point | Zone_Air_Heating_Temperature_Setpoint |
| `ZN-Perimeter_top_ZN_1/CLG-SP` | setpoint | degC | Active cooling set point | Zone_Air_Cooling_Temperature_Setpoint |
| `ZN-Perimeter_top_ZN_1/OCC-HTG-SP` | setpoint | degC | Occupied heating set point | Occupied_Air_Temperature_Heating_Setpoint |
| `ZN-Perimeter_top_ZN_1/OCC-CLG-SP` | setpoint | degC | Occupied cooling set point | Occupied_Air_Temperature_Cooling_Setpoint |
| `ZN-Perimeter_top_ZN_1/OCC-MODE` | status | - | Zone occupancy mode (1 occupied / 0 unoccupied) | Occupancy_Status |

## VAV-Perimeter_top_ZN_1 - VAV

VAV terminal with hot-water reheat serving Perimeter_top_ZN_1

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `VAV-Perimeter_top_ZN_1/DA-F` | sensor | m3/s | Discharge air flow | Discharge_Air_Flow_Sensor |
| `VAV-Perimeter_top_ZN_1/DA-T` | sensor | degC | Discharge air temperature | Discharge_Air_Temperature_Sensor |
| `VAV-Perimeter_top_ZN_1/DMPR-POS` | sensor | % | Damper position feedback | Damper_Position_Sensor |
| `VAV-Perimeter_top_ZN_1/RHV-POS` | sensor | % | Reheat valve position (feedback) | Valve_Position_Sensor |
| `VAV-Perimeter_top_ZN_1/RH-Q` | truth | kW | Reheat coil heat rate (ground truth) |  |
| `VAV-Perimeter_top_ZN_1/DA-F-SP` | setpoint | m3/s | Discharge air flow set point | Discharge_Air_Flow_Setpoint |
| `VAV-Perimeter_top_ZN_1/DMPR-CMD` | command | % | Damper command | Damper_Position_Command |
| `VAV-Perimeter_top_ZN_1/CLG-LOOP` | virtual | % | Cooling loop output |  |
| `VAV-Perimeter_top_ZN_1/HTG-LOOP` | virtual | % | Heating loop output |  |

## ZN-Perimeter_top_ZN_2 - Zone

Thermal zone Perimeter_top_ZN_2

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `ZN-Perimeter_top_ZN_2/ZN-T` | sensor | degC | Zone air temperature | Zone_Air_Temperature_Sensor |
| `ZN-Perimeter_top_ZN_2/ZN-RH` | sensor | %RH | Zone air relative humidity | Zone_Air_Humidity_Sensor |
| `ZN-Perimeter_top_ZN_2/ZN-CO2` | sensor | ppm | Zone CO2 concentration | CO2_Sensor |
| `ZN-Perimeter_top_ZN_2/ZN-OCC` | sensor | - | Zone occupancy sensor (PIR) | Occupancy_Sensor |
| `ZN-Perimeter_top_ZN_2/OCCUPANTS` | truth | people | True number of occupants (ground truth only) | Occupancy_Count_Sensor |
| `ZN-Perimeter_top_ZN_2/PMV` | truth | - | Fanger predicted mean vote (ground truth only) |  |
| `ZN-Perimeter_top_ZN_2/LIGHT-KW` | meter | kW | Zone lighting power | Electric_Power_Sensor |
| `ZN-Perimeter_top_ZN_2/PLUG-KW` | meter | kW | Zone plug load power | Electric_Power_Sensor |
| `ZN-Perimeter_top_ZN_2/HTG-SP` | setpoint | degC | Active heating set point | Zone_Air_Heating_Temperature_Setpoint |
| `ZN-Perimeter_top_ZN_2/CLG-SP` | setpoint | degC | Active cooling set point | Zone_Air_Cooling_Temperature_Setpoint |
| `ZN-Perimeter_top_ZN_2/OCC-HTG-SP` | setpoint | degC | Occupied heating set point | Occupied_Air_Temperature_Heating_Setpoint |
| `ZN-Perimeter_top_ZN_2/OCC-CLG-SP` | setpoint | degC | Occupied cooling set point | Occupied_Air_Temperature_Cooling_Setpoint |
| `ZN-Perimeter_top_ZN_2/OCC-MODE` | status | - | Zone occupancy mode (1 occupied / 0 unoccupied) | Occupancy_Status |

## VAV-Perimeter_top_ZN_2 - VAV

VAV terminal with hot-water reheat serving Perimeter_top_ZN_2

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `VAV-Perimeter_top_ZN_2/DA-F` | sensor | m3/s | Discharge air flow | Discharge_Air_Flow_Sensor |
| `VAV-Perimeter_top_ZN_2/DA-T` | sensor | degC | Discharge air temperature | Discharge_Air_Temperature_Sensor |
| `VAV-Perimeter_top_ZN_2/DMPR-POS` | sensor | % | Damper position feedback | Damper_Position_Sensor |
| `VAV-Perimeter_top_ZN_2/RHV-POS` | sensor | % | Reheat valve position (feedback) | Valve_Position_Sensor |
| `VAV-Perimeter_top_ZN_2/RH-Q` | truth | kW | Reheat coil heat rate (ground truth) |  |
| `VAV-Perimeter_top_ZN_2/DA-F-SP` | setpoint | m3/s | Discharge air flow set point | Discharge_Air_Flow_Setpoint |
| `VAV-Perimeter_top_ZN_2/DMPR-CMD` | command | % | Damper command | Damper_Position_Command |
| `VAV-Perimeter_top_ZN_2/CLG-LOOP` | virtual | % | Cooling loop output |  |
| `VAV-Perimeter_top_ZN_2/HTG-LOOP` | virtual | % | Heating loop output |  |

## ZN-Perimeter_top_ZN_3 - Zone

Thermal zone Perimeter_top_ZN_3

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `ZN-Perimeter_top_ZN_3/ZN-T` | sensor | degC | Zone air temperature | Zone_Air_Temperature_Sensor |
| `ZN-Perimeter_top_ZN_3/ZN-RH` | sensor | %RH | Zone air relative humidity | Zone_Air_Humidity_Sensor |
| `ZN-Perimeter_top_ZN_3/ZN-CO2` | sensor | ppm | Zone CO2 concentration | CO2_Sensor |
| `ZN-Perimeter_top_ZN_3/ZN-OCC` | sensor | - | Zone occupancy sensor (PIR) | Occupancy_Sensor |
| `ZN-Perimeter_top_ZN_3/OCCUPANTS` | truth | people | True number of occupants (ground truth only) | Occupancy_Count_Sensor |
| `ZN-Perimeter_top_ZN_3/PMV` | truth | - | Fanger predicted mean vote (ground truth only) |  |
| `ZN-Perimeter_top_ZN_3/LIGHT-KW` | meter | kW | Zone lighting power | Electric_Power_Sensor |
| `ZN-Perimeter_top_ZN_3/PLUG-KW` | meter | kW | Zone plug load power | Electric_Power_Sensor |
| `ZN-Perimeter_top_ZN_3/HTG-SP` | setpoint | degC | Active heating set point | Zone_Air_Heating_Temperature_Setpoint |
| `ZN-Perimeter_top_ZN_3/CLG-SP` | setpoint | degC | Active cooling set point | Zone_Air_Cooling_Temperature_Setpoint |
| `ZN-Perimeter_top_ZN_3/OCC-HTG-SP` | setpoint | degC | Occupied heating set point | Occupied_Air_Temperature_Heating_Setpoint |
| `ZN-Perimeter_top_ZN_3/OCC-CLG-SP` | setpoint | degC | Occupied cooling set point | Occupied_Air_Temperature_Cooling_Setpoint |
| `ZN-Perimeter_top_ZN_3/OCC-MODE` | status | - | Zone occupancy mode (1 occupied / 0 unoccupied) | Occupancy_Status |

## VAV-Perimeter_top_ZN_3 - VAV

VAV terminal with hot-water reheat serving Perimeter_top_ZN_3

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `VAV-Perimeter_top_ZN_3/DA-F` | sensor | m3/s | Discharge air flow | Discharge_Air_Flow_Sensor |
| `VAV-Perimeter_top_ZN_3/DA-T` | sensor | degC | Discharge air temperature | Discharge_Air_Temperature_Sensor |
| `VAV-Perimeter_top_ZN_3/DMPR-POS` | sensor | % | Damper position feedback | Damper_Position_Sensor |
| `VAV-Perimeter_top_ZN_3/RHV-POS` | sensor | % | Reheat valve position (feedback) | Valve_Position_Sensor |
| `VAV-Perimeter_top_ZN_3/RH-Q` | truth | kW | Reheat coil heat rate (ground truth) |  |
| `VAV-Perimeter_top_ZN_3/DA-F-SP` | setpoint | m3/s | Discharge air flow set point | Discharge_Air_Flow_Setpoint |
| `VAV-Perimeter_top_ZN_3/DMPR-CMD` | command | % | Damper command | Damper_Position_Command |
| `VAV-Perimeter_top_ZN_3/CLG-LOOP` | virtual | % | Cooling loop output |  |
| `VAV-Perimeter_top_ZN_3/HTG-LOOP` | virtual | % | Heating loop output |  |

## ZN-Perimeter_top_ZN_4 - Zone

Thermal zone Perimeter_top_ZN_4

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `ZN-Perimeter_top_ZN_4/ZN-T` | sensor | degC | Zone air temperature | Zone_Air_Temperature_Sensor |
| `ZN-Perimeter_top_ZN_4/ZN-RH` | sensor | %RH | Zone air relative humidity | Zone_Air_Humidity_Sensor |
| `ZN-Perimeter_top_ZN_4/ZN-CO2` | sensor | ppm | Zone CO2 concentration | CO2_Sensor |
| `ZN-Perimeter_top_ZN_4/ZN-OCC` | sensor | - | Zone occupancy sensor (PIR) | Occupancy_Sensor |
| `ZN-Perimeter_top_ZN_4/OCCUPANTS` | truth | people | True number of occupants (ground truth only) | Occupancy_Count_Sensor |
| `ZN-Perimeter_top_ZN_4/PMV` | truth | - | Fanger predicted mean vote (ground truth only) |  |
| `ZN-Perimeter_top_ZN_4/LIGHT-KW` | meter | kW | Zone lighting power | Electric_Power_Sensor |
| `ZN-Perimeter_top_ZN_4/PLUG-KW` | meter | kW | Zone plug load power | Electric_Power_Sensor |
| `ZN-Perimeter_top_ZN_4/HTG-SP` | setpoint | degC | Active heating set point | Zone_Air_Heating_Temperature_Setpoint |
| `ZN-Perimeter_top_ZN_4/CLG-SP` | setpoint | degC | Active cooling set point | Zone_Air_Cooling_Temperature_Setpoint |
| `ZN-Perimeter_top_ZN_4/OCC-HTG-SP` | setpoint | degC | Occupied heating set point | Occupied_Air_Temperature_Heating_Setpoint |
| `ZN-Perimeter_top_ZN_4/OCC-CLG-SP` | setpoint | degC | Occupied cooling set point | Occupied_Air_Temperature_Cooling_Setpoint |
| `ZN-Perimeter_top_ZN_4/OCC-MODE` | status | - | Zone occupancy mode (1 occupied / 0 unoccupied) | Occupancy_Status |

## VAV-Perimeter_top_ZN_4 - VAV

VAV terminal with hot-water reheat serving Perimeter_top_ZN_4

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `VAV-Perimeter_top_ZN_4/DA-F` | sensor | m3/s | Discharge air flow | Discharge_Air_Flow_Sensor |
| `VAV-Perimeter_top_ZN_4/DA-T` | sensor | degC | Discharge air temperature | Discharge_Air_Temperature_Sensor |
| `VAV-Perimeter_top_ZN_4/DMPR-POS` | sensor | % | Damper position feedback | Damper_Position_Sensor |
| `VAV-Perimeter_top_ZN_4/RHV-POS` | sensor | % | Reheat valve position (feedback) | Valve_Position_Sensor |
| `VAV-Perimeter_top_ZN_4/RH-Q` | truth | kW | Reheat coil heat rate (ground truth) |  |
| `VAV-Perimeter_top_ZN_4/DA-F-SP` | setpoint | m3/s | Discharge air flow set point | Discharge_Air_Flow_Setpoint |
| `VAV-Perimeter_top_ZN_4/DMPR-CMD` | command | % | Damper command | Damper_Position_Command |
| `VAV-Perimeter_top_ZN_4/CLG-LOOP` | virtual | % | Cooling loop output |  |
| `VAV-Perimeter_top_ZN_4/HTG-LOOP` | virtual | % | Heating loop output |  |

## AHU-1 - AHU

Air handling unit VAV_1 (VAV, economizer, CHW/HW coils)

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `AHU-1/SA-T` | sensor | degC | Supply air temperature | Supply_Air_Temperature_Sensor |
| `AHU-1/SA-RH` | sensor | %RH | Supply air relative humidity | Supply_Air_Humidity_Sensor |
| `AHU-1/SA-F` | sensor | m3/s | Supply air flow | Supply_Air_Flow_Sensor |
| `AHU-1/MA-T` | sensor | degC | Mixed air temperature | Mixed_Air_Temperature_Sensor |
| `AHU-1/RA-T` | sensor | degC | Return air temperature | Return_Air_Temperature_Sensor |
| `AHU-1/RA-RH` | sensor | %RH | Return air relative humidity | Return_Air_Humidity_Sensor |
| `AHU-1/OA-F` | sensor | m3/s | Outdoor air flow (airflow measuring station) | Outside_Air_Flow_Sensor |
| `AHU-1/OAD-POS` | sensor | % | Outdoor air damper position (feedback) | Damper_Position_Sensor |
| `AHU-1/CCV-POS` | sensor | % | Cooling coil valve position (feedback) | Valve_Position_Sensor |
| `AHU-1/CC-Q` | truth | kW | Cooling coil total load (ground truth) |  |
| `AHU-1/CC-LAT` | sensor | degC | Cooling coil leaving air temperature | Air_Temperature_Sensor |
| `AHU-1/HCV-POS` | sensor | % | Heating (preheat) coil valve position (feedback) | Valve_Position_Sensor |
| `AHU-1/SF-KW` | sensor | kW | Supply fan power (VFD) | Electric_Power_Sensor |
| `AHU-1/SF-SPD` | sensor | % | Supply fan speed (VFD output) | Frequency_Sensor |
| `AHU-1/SF-STS` | sensor | - | Supply fan status (current switch) | Fan_Status |
| `AHU-1/DSP` | sensor | Pa | Duct static pressure (surrogate model) | Static_Pressure_Sensor |
| `AHU-1/FLT-DP` | sensor | Pa | Filter differential pressure (surrogate model) | Filter_Differential_Pressure_Sensor |
| `AHU-1/SA-T-SP` | setpoint | degC | Supply air temperature set point | Supply_Air_Temperature_Setpoint |
| `AHU-1/DSP-SP` | setpoint | Pa | Duct static pressure set point | Static_Pressure_Setpoint |
| `AHU-1/MA-T-SP` | setpoint | degC | Mixed air temperature set point (economizer) | Mixed_Air_Temperature_Setpoint |
| `AHU-1/OAD-CMD` | command | % | Outdoor air damper command | Damper_Position_Command |
| `AHU-1/ECON-EN` | status | - | Economizer enable | Enable_Status |
| `AHU-1/SF-CMD` | command | - | Supply fan start/stop command | Start_Stop_Command |
| `AHU-1/OCC-MODE` | status | - | AHU operating mode (2 occupied, 1 night cycle, 0 off) | Operating_Mode_Status |

## AHU-2 - AHU

Air handling unit VAV_2 (VAV, economizer, CHW/HW coils)

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `AHU-2/SA-T` | sensor | degC | Supply air temperature | Supply_Air_Temperature_Sensor |
| `AHU-2/SA-RH` | sensor | %RH | Supply air relative humidity | Supply_Air_Humidity_Sensor |
| `AHU-2/SA-F` | sensor | m3/s | Supply air flow | Supply_Air_Flow_Sensor |
| `AHU-2/MA-T` | sensor | degC | Mixed air temperature | Mixed_Air_Temperature_Sensor |
| `AHU-2/RA-T` | sensor | degC | Return air temperature | Return_Air_Temperature_Sensor |
| `AHU-2/RA-RH` | sensor | %RH | Return air relative humidity | Return_Air_Humidity_Sensor |
| `AHU-2/OA-F` | sensor | m3/s | Outdoor air flow (airflow measuring station) | Outside_Air_Flow_Sensor |
| `AHU-2/OAD-POS` | sensor | % | Outdoor air damper position (feedback) | Damper_Position_Sensor |
| `AHU-2/CCV-POS` | sensor | % | Cooling coil valve position (feedback) | Valve_Position_Sensor |
| `AHU-2/CC-Q` | truth | kW | Cooling coil total load (ground truth) |  |
| `AHU-2/CC-LAT` | sensor | degC | Cooling coil leaving air temperature | Air_Temperature_Sensor |
| `AHU-2/HCV-POS` | sensor | % | Heating (preheat) coil valve position (feedback) | Valve_Position_Sensor |
| `AHU-2/SF-KW` | sensor | kW | Supply fan power (VFD) | Electric_Power_Sensor |
| `AHU-2/SF-SPD` | sensor | % | Supply fan speed (VFD output) | Frequency_Sensor |
| `AHU-2/SF-STS` | sensor | - | Supply fan status (current switch) | Fan_Status |
| `AHU-2/DSP` | sensor | Pa | Duct static pressure (surrogate model) | Static_Pressure_Sensor |
| `AHU-2/FLT-DP` | sensor | Pa | Filter differential pressure (surrogate model) | Filter_Differential_Pressure_Sensor |
| `AHU-2/SA-T-SP` | setpoint | degC | Supply air temperature set point | Supply_Air_Temperature_Setpoint |
| `AHU-2/DSP-SP` | setpoint | Pa | Duct static pressure set point | Static_Pressure_Setpoint |
| `AHU-2/MA-T-SP` | setpoint | degC | Mixed air temperature set point (economizer) | Mixed_Air_Temperature_Setpoint |
| `AHU-2/OAD-CMD` | command | % | Outdoor air damper command | Damper_Position_Command |
| `AHU-2/ECON-EN` | status | - | Economizer enable | Enable_Status |
| `AHU-2/SF-CMD` | command | - | Supply fan start/stop command | Start_Stop_Command |
| `AHU-2/OCC-MODE` | status | - | AHU operating mode (2 occupied, 1 night cycle, 0 off) | Operating_Mode_Status |

## AHU-3 - AHU

Air handling unit VAV_3 (VAV, economizer, CHW/HW coils)

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `AHU-3/SA-T` | sensor | degC | Supply air temperature | Supply_Air_Temperature_Sensor |
| `AHU-3/SA-RH` | sensor | %RH | Supply air relative humidity | Supply_Air_Humidity_Sensor |
| `AHU-3/SA-F` | sensor | m3/s | Supply air flow | Supply_Air_Flow_Sensor |
| `AHU-3/MA-T` | sensor | degC | Mixed air temperature | Mixed_Air_Temperature_Sensor |
| `AHU-3/RA-T` | sensor | degC | Return air temperature | Return_Air_Temperature_Sensor |
| `AHU-3/RA-RH` | sensor | %RH | Return air relative humidity | Return_Air_Humidity_Sensor |
| `AHU-3/OA-F` | sensor | m3/s | Outdoor air flow (airflow measuring station) | Outside_Air_Flow_Sensor |
| `AHU-3/OAD-POS` | sensor | % | Outdoor air damper position (feedback) | Damper_Position_Sensor |
| `AHU-3/CCV-POS` | sensor | % | Cooling coil valve position (feedback) | Valve_Position_Sensor |
| `AHU-3/CC-Q` | truth | kW | Cooling coil total load (ground truth) |  |
| `AHU-3/CC-LAT` | sensor | degC | Cooling coil leaving air temperature | Air_Temperature_Sensor |
| `AHU-3/HCV-POS` | sensor | % | Heating (preheat) coil valve position (feedback) | Valve_Position_Sensor |
| `AHU-3/SF-KW` | sensor | kW | Supply fan power (VFD) | Electric_Power_Sensor |
| `AHU-3/SF-SPD` | sensor | % | Supply fan speed (VFD output) | Frequency_Sensor |
| `AHU-3/SF-STS` | sensor | - | Supply fan status (current switch) | Fan_Status |
| `AHU-3/DSP` | sensor | Pa | Duct static pressure (surrogate model) | Static_Pressure_Sensor |
| `AHU-3/FLT-DP` | sensor | Pa | Filter differential pressure (surrogate model) | Filter_Differential_Pressure_Sensor |
| `AHU-3/SA-T-SP` | setpoint | degC | Supply air temperature set point | Supply_Air_Temperature_Setpoint |
| `AHU-3/DSP-SP` | setpoint | Pa | Duct static pressure set point | Static_Pressure_Setpoint |
| `AHU-3/MA-T-SP` | setpoint | degC | Mixed air temperature set point (economizer) | Mixed_Air_Temperature_Setpoint |
| `AHU-3/OAD-CMD` | command | % | Outdoor air damper command | Damper_Position_Command |
| `AHU-3/ECON-EN` | status | - | Economizer enable | Enable_Status |
| `AHU-3/SF-CMD` | command | - | Supply fan start/stop command | Start_Stop_Command |
| `AHU-3/OCC-MODE` | status | - | AHU operating mode (2 occupied, 1 night cycle, 0 off) | Operating_Mode_Status |

## AHU-4 - AHU

Air handling unit VAV_5 (VAV, economizer, CHW/HW coils)

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `AHU-4/SA-T` | sensor | degC | Supply air temperature | Supply_Air_Temperature_Sensor |
| `AHU-4/SA-RH` | sensor | %RH | Supply air relative humidity | Supply_Air_Humidity_Sensor |
| `AHU-4/SA-F` | sensor | m3/s | Supply air flow | Supply_Air_Flow_Sensor |
| `AHU-4/MA-T` | sensor | degC | Mixed air temperature | Mixed_Air_Temperature_Sensor |
| `AHU-4/RA-T` | sensor | degC | Return air temperature | Return_Air_Temperature_Sensor |
| `AHU-4/RA-RH` | sensor | %RH | Return air relative humidity | Return_Air_Humidity_Sensor |
| `AHU-4/OA-F` | sensor | m3/s | Outdoor air flow (airflow measuring station) | Outside_Air_Flow_Sensor |
| `AHU-4/OAD-POS` | sensor | % | Outdoor air damper position (feedback) | Damper_Position_Sensor |
| `AHU-4/CCV-POS` | sensor | % | Cooling coil valve position (feedback) | Valve_Position_Sensor |
| `AHU-4/CC-Q` | truth | kW | Cooling coil total load (ground truth) |  |
| `AHU-4/CC-LAT` | sensor | degC | Cooling coil leaving air temperature | Air_Temperature_Sensor |
| `AHU-4/HCV-POS` | sensor | % | Heating (preheat) coil valve position (feedback) | Valve_Position_Sensor |
| `AHU-4/SF-KW` | sensor | kW | Supply fan power (VFD) | Electric_Power_Sensor |
| `AHU-4/SF-SPD` | sensor | % | Supply fan speed (VFD output) | Frequency_Sensor |
| `AHU-4/SF-STS` | sensor | - | Supply fan status (current switch) | Fan_Status |
| `AHU-4/DSP` | sensor | Pa | Duct static pressure (surrogate model) | Static_Pressure_Sensor |
| `AHU-4/FLT-DP` | sensor | Pa | Filter differential pressure (surrogate model) | Filter_Differential_Pressure_Sensor |
| `AHU-4/SA-T-SP` | setpoint | degC | Supply air temperature set point | Supply_Air_Temperature_Setpoint |
| `AHU-4/DSP-SP` | setpoint | Pa | Duct static pressure set point | Static_Pressure_Setpoint |
| `AHU-4/MA-T-SP` | setpoint | degC | Mixed air temperature set point (economizer) | Mixed_Air_Temperature_Setpoint |
| `AHU-4/OAD-CMD` | command | % | Outdoor air damper command | Damper_Position_Command |
| `AHU-4/ECON-EN` | status | - | Economizer enable | Enable_Status |
| `AHU-4/SF-CMD` | command | - | Supply fan start/stop command | Start_Stop_Command |
| `AHU-4/OCC-MODE` | status | - | AHU operating mode (2 occupied, 1 night cycle, 0 off) | Operating_Mode_Status |

## CHW-SYS - PlantLoop

Chilled water system

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `CHW-SYS/CHW-ST` | sensor | degC | Chilled water supply temperature | Supply_Water_Temperature_Sensor |
| `CHW-SYS/CHW-RT` | sensor | degC | Chilled water return temperature | Return_Water_Temperature_Sensor |
| `CHW-SYS/CHW-F` | sensor | L/s | Chilled water flow | Water_Flow_Sensor |
| `CHW-SYS/CHW-DP` | sensor | kPa | Chilled water differential pressure (surrogate model) | Differential_Pressure_Sensor |
| `CHW-SYS/CHW-ST-SP` | setpoint | degC | Chilled water supply temperature set point | Supply_Water_Temperature_Setpoint |

## CHWP-1 - Pump

Chilled water pump (VariableSpeed)

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `CHWP-1/KW` | sensor | kW | Pump power | Electric_Power_Sensor |
| `CHWP-1/SPD` | sensor | % | Pump speed (VFD output) | Frequency_Sensor |
| `CHWP-1/STS` | sensor | - | Pump status | Pump_Status |

## CH-1 - Chiller

Water-cooled chiller (ReformulatedEIR)

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `CH-1/KW` | sensor | kW | Chiller power | Electric_Power_Sensor |
| `CH-1/LOAD` | sensor | kW | Chiller cooling load (BTU meter) | Thermal_Power_Sensor |
| `CH-1/STS` | sensor | - | Chiller run status | Run_Status |
| `CH-1/CHW-LWT` | sensor | degC | Evaporator leaving water temperature | Chilled_Water_Supply_Temperature_Sensor |
| `CH-1/CHW-EWT` | sensor | degC | Evaporator entering water temperature | Chilled_Water_Return_Temperature_Sensor |
| `CH-1/CDW-EWT` | sensor | degC | Condenser entering water temperature | Condenser_Water_Return_Temperature_Sensor |
| `CH-1/CDW-LWT` | sensor | degC | Condenser leaving water temperature | Condenser_Water_Supply_Temperature_Sensor |
| `CH-1/PLR` | truth | - | Chiller part load ratio |  |
| `CH-1/COP` | truth | - | Chiller COP (ground truth) |  |
| `CH-1/EN-CMD` | command | - | Chiller enable command | Enable_Command |

## CH-2 - Chiller

Water-cooled chiller (ReformulatedEIR)

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `CH-2/KW` | sensor | kW | Chiller power | Electric_Power_Sensor |
| `CH-2/LOAD` | sensor | kW | Chiller cooling load (BTU meter) | Thermal_Power_Sensor |
| `CH-2/STS` | sensor | - | Chiller run status | Run_Status |
| `CH-2/CHW-LWT` | sensor | degC | Evaporator leaving water temperature | Chilled_Water_Supply_Temperature_Sensor |
| `CH-2/CHW-EWT` | sensor | degC | Evaporator entering water temperature | Chilled_Water_Return_Temperature_Sensor |
| `CH-2/CDW-EWT` | sensor | degC | Condenser entering water temperature | Condenser_Water_Return_Temperature_Sensor |
| `CH-2/CDW-LWT` | sensor | degC | Condenser leaving water temperature | Condenser_Water_Supply_Temperature_Sensor |
| `CH-2/PLR` | truth | - | Chiller part load ratio |  |
| `CH-2/COP` | truth | - | Chiller COP (ground truth) |  |
| `CH-2/EN-CMD` | command | - | Chiller enable command | Enable_Command |

## HW-SYS - PlantLoop

Hot water system

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `HW-SYS/HW-ST` | sensor | degC | Hot water supply temperature | Supply_Water_Temperature_Sensor |
| `HW-SYS/HW-RT` | sensor | degC | Hot water return temperature | Return_Water_Temperature_Sensor |
| `HW-SYS/HW-F` | sensor | L/s | Hot water flow | Water_Flow_Sensor |
| `HW-SYS/HW-DP` | sensor | kPa | Hot water differential pressure (surrogate model) | Differential_Pressure_Sensor |
| `HW-SYS/HW-ST-SP` | setpoint | degC | Hot water supply temperature set point | Supply_Water_Temperature_Setpoint |

## HWP-1 - Pump

Hot water pump (VariableSpeed)

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `HWP-1/KW` | sensor | kW | Pump power | Electric_Power_Sensor |
| `HWP-1/SPD` | sensor | % | Pump speed (VFD output) | Frequency_Sensor |
| `HWP-1/STS` | sensor | - | Pump status | Pump_Status |

## BLR-1 - Boiler

Hot-water boiler (natural gas)

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `BLR-1/LOAD` | sensor | kW | Boiler heating output | Thermal_Power_Sensor |
| `BLR-1/GAS-KW` | sensor | kW | Boiler gas input | Natural_Gas_Usage_Sensor |
| `BLR-1/STS` | sensor | - | Boiler firing status | Run_Status |
| `BLR-1/HW-LWT` | sensor | degC | Boiler leaving water temperature | Hot_Water_Supply_Temperature_Sensor |
| `BLR-1/HW-EWT` | sensor | degC | Boiler entering water temperature | Hot_Water_Return_Temperature_Sensor |
| `BLR-1/PLR` | truth | - | Boiler part load ratio |  |
| `BLR-1/EN-CMD` | command | - | Boiler enable command | Enable_Command |

## CW-SYS - PlantLoop

Condenser water system

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `CW-SYS/CW-ST` | sensor | degC | Condenser water supply temperature | Supply_Water_Temperature_Sensor |
| `CW-SYS/CW-RT` | sensor | degC | Condenser water return temperature | Return_Water_Temperature_Sensor |
| `CW-SYS/CW-F` | sensor | L/s | Condenser water flow | Water_Flow_Sensor |
| `CW-SYS/CW-DP` | sensor | kPa | Condenser water differential pressure (surrogate model) | Differential_Pressure_Sensor |
| `CW-SYS/CW-ST-SP` | setpoint | degC | Condenser water supply temperature set point | Supply_Water_Temperature_Setpoint |

## CWP-1 - Pump

Condenser water pump (ConstantSpeed)

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `CWP-1/KW` | sensor | kW | Pump power | Electric_Power_Sensor |
| `CWP-1/SPD` | sensor | % | Pump speed (VFD output) | Frequency_Sensor |
| `CWP-1/STS` | sensor | - | Pump status | Pump_Status |

## CT-1 - CoolingTower

Cooling tower (SingleSpeed)

| Point | Kind | Unit | Description | Brick class |
|---|---|---|---|---|
| `CT-1/FAN-KW` | sensor | kW | Tower fan power | Electric_Power_Sensor |
| `CT-1/FAN-STS` | sensor | - | Tower fan status | Fan_Status |
| `CT-1/LWT` | sensor | degC | Tower leaving water temperature | Water_Temperature_Sensor |
| `CT-1/EWT` | sensor | degC | Tower entering water temperature | Water_Temperature_Sensor |
