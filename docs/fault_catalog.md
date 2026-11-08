# Fault & event catalog

Generated from `virtualbas/realworld/faults.py` (`python tools/gen_docs.py`).

Every injection has a severity profile s(t) in [0, 1] (step, ramp or intermittent) and modifies one
model parameter as theta(t) = theta_0 + s(t) * delta_theta. All injections are recorded as ground-truth labels.

## Events - control layer

| Type | Target | Description | Equation | Parameters |
|---|---|---|---|---|
| `setpoint_override` | `equip:Zone` | Occupant/operator changes zone set points (e.g. space heater complaint, demand response). | $T_{sp}' = T_{sp} + s(t)\,\Delta T$ | `delta`=2.0 K - set point shift |

## Events - gains layer

| Type | Target | Description | Equation | Parameters |
|---|---|---|---|---|
| `window_open` | `zone` | Operable window/door left open - additional infiltration. | $\dot V_{inf}' = \dot V_{inf} + s(t)\,ACH\,V_z/3600$ | `ach`=2.0 1/h - additional air changes |
| `plug_load_change` | `zone / building` | Plug/process load change (server room, new equipment, after-hours use). | $P_{plug}' = (1 + s(m-1)) P_{plug}$ | `multiplier`=1.5 - - multiplier m |
| `lighting_change` | `zone / building` | Lighting left on / turned off. | $P_{light}' = (1 + s(m-1)) P_{light}$ | `multiplier`=1.5 - - multiplier m |

## Events - occupancy layer

| Type | Target | Description | Equation | Parameters |
|---|---|---|---|---|
| `occupancy_surge` | `zone / building` | Sudden change of occupancy (conference, evacuation drill, holiday). | $P'(t) = \min\big(1, m^{s(t)} P(t)\big),\ N' = \lceil m N \rceil$ | `multiplier`=1.8 - - occupancy multiplier m (0 = vacant) |
| `meeting` | `zone` | Additional people gathering in a zone. | $N'(t) = N(t) + s(t)\,n$ | `people`=25 people - extra occupants n |
| `holiday` | `building` | Unscheduled holiday: building unoccupied and BAS in unoccupied mode. | $P(t)=0,\ \text{mode}=\text{unocc}$ | - |

## Events - weather layer

| Type | Target | Description | Equation | Parameters |
|---|---|---|---|---|
| `weather_change` | `building` | Weather perturbation added to the weather file (heat wave, cold snap, cloud cover). | $T_{db}' = T_{db} + s\,\Delta T,\ \phi' = \phi + s\,\Delta\phi,\ I' = (1 - s(1-m_I)) I$ | `delta_t`=5.0 K - dry-bulb offset<br>`delta_rh`=0.0 % - RH offset<br>`solar_mult`=1.0 - - solar multiplier m_I |
| `outdoor_co2_change` | `building` | Change of ambient CO2 concentration (traffic, wildfire). | $C_{out}' = C_{out}+s\,\Delta C$ | `delta_ppm`=150.0 ppm - offset |

## Faults - actuator layer

| Type | Target | Description | Equation | Parameters |
|---|---|---|---|---|
| `vav_damper_stuck` | `equip:VAV` | VAV damper stuck at a fixed position regardless of the command. | $\phi^{real}_k = \phi_{stuck}$ | `position`=30.0 % - stuck damper position |
| `reheat_valve_stuck_closed` | `equip:VAV` | VAV reheat valve stuck closed (no reheat available). | $\dot m_{w,rh} = 0$ | - |
| `reheat_valve_stuck_open` | `equip:VAV` | VAV reheat valve stuck open / leaking: unbounded reheat until the zone reaches the forced temperature. | $T^{E+}_{htg} = T_{force}$ | `force_temp`=26.0 degC - temperature reached with full reheat |
| `oa_damper_stuck` | `equip:AHU` | Outdoor-air damper stuck (common economizer fault). | $f^{real}_{OA} = f_{stuck}$ | `position`=100.0 % - stuck OA fraction |
| `cooling_coil_valve_stuck_closed` | `equip:AHU` | AHU chilled-water valve stuck closed. | $\dot m_{w,cc}=0$ | - |
| `heating_coil_valve_stuck_closed` | `equip:AHU` | AHU preheat hot-water valve stuck closed. | $\dot m_{w,hc}=0$ | - |
| `supply_fan_failure` | `equip:AHU` | Supply fan trips (VFD fault / belt failure). | $\dot V_{SA}=0$ | - |

## Faults - control layer

| Type | Target | Description | Equation | Parameters |
|---|---|---|---|---|
| `schedule_error_always_on` | `equip:AHU` | Occupancy schedule overridden - AHU runs 24/7 (forgotten manual override). | $\text{mode}=\text{occupied}$ | - |
| `schedule_error_off` | `equip:AHU` | AHU never starts (schedule deleted / wrong calendar). | $\text{mode}=\text{unoccupied}$ | - |
| `pid_mistuning` | `equip:VAV / AHU` | Controller gains multiplied by a factor (aggressive tuning leading to oscillation). | $K_p' = m\,K_p,\ K_i' = m\,K_i$ | `multiplier`=6.0 - - gain multiplier m |
| `economizer_disabled` | `equip:AHU` | Economizer logic disabled (minimum OA only). | $f_{OA}=f_{OA,min}$ | - |
| `economizer_always_on` | `equip:AHU` | Economizer high-limit lock-out failure - economizer enabled in hot weather. | $\text{econ}=1$ | - |
| `sat_reset_disabled` | `equip:AHU` | Supply-air temperature reset disabled; fixed set point. | $T_{SA,sp}=T_{fixed}$ | `setpoint`=12.8 degC - fixed SAT set point |
| `controller_frozen` | `equip:VAV / AHU` | Controller software hang - outputs frozen at last values. | $u_k = u_{k_0}$ | - |

## Faults - equipment layer

| Type | Target | Description | Equation | Parameters |
|---|---|---|---|---|
| `chiller_fouling` | `equip:Chiller` | Condenser/evaporator fouling reducing nominal capacity and COP (EnergyPlus FaultModel:Fouling:Chiller). | $Q_{ref}^{f} = \big(1 - s(t)(1-r)\big) Q_{ref},\ COP^{f}_{ref} = \big(1 - s(t)(1-r)\big) COP_{ref}$ | `ratio`=0.7 - - capacity ratio r at full severity |
| `boiler_fouling` | `equip:Boiler` | Boiler heat-exchanger fouling reducing nominal capacity (EnergyPlus FaultModel:Fouling:Boiler). | $Q^{f}_{nom} = \big(1 - s(t)(1-r)\big) Q_{nom}$ | `ratio`=0.7 - - capacity ratio r |
| `tower_fouling` | `equip:CoolingTower` | Cooling tower fill fouling reducing UA (EnergyPlus FaultModel:Fouling:CoolingTower). | $UA^{f} = \big(1 - s(t)(1-r)\big) UA$ | `ratio`=0.6 - - UA ratio r |
| `filter_fouling` | `equip:AHU` | Air filter loading: additional pressure drop raises fan pressure rise and power. | $\Delta p_{fan} = \Delta p_{fan,0} + s(t)\,\Delta p_{add};\ \Delta p_{flt} = (\Delta p_{clean}+s\Delta p_{add})(\dot V/\dot V_d)^2$ | `dp_add`=250.0 Pa - additional filter pressure drop at design flow |
| `fan_degradation` | `equip:AHU` | Fan/motor efficiency degradation (bearing wear, belt slip). | $\eta_{fan} = \eta_{fan,0}\,(1 - s(t)\,\ell)$ | `loss`=0.25 - - relative efficiency loss l |
| `equipment_trip` | `equip:Chiller / Boiler / CoolingTower / Pump` | Primary plant equipment trip (safety lock-out). | $\text{available}=0$ | - |

## Faults - network layer

| Type | Target | Description | Equation | Parameters |
|---|---|---|---|---|
| `comm_loss` | `equip:*` | Controller off-line: all points of the equipment are missing; the BAS holds last values. | $y_k=\text{NaN}\ \forall\ \text{points of equipment}$ | - |
| `historian_outage` | `building` | Trend-log server outage: data are not archived (control unaffected). | $\text{log}_k=\emptyset$ | - |

## Faults - sensor layer

| Type | Target | Description | Equation | Parameters |
|---|---|---|---|---|
| `sensor_bias` | `point:sensor` | Constant calibration offset (e.g. mis-calibrated thermistor). | $y_k = y_k^{0} + s(t)\,b$ | `bias`=1.5 point unit - offset b |
| `sensor_drift` | `point:sensor` | Linear drift accumulating from the onset time, saturating at a maximum magnitude. | $y_k = y_k^{0} + \mathrm{sat}_{\pm d_{max}}\big(r\,(t-t_0)\big)$ | `rate_per_day`=0.25 unit/day - drift rate r<br>`max_abs`=5.0 point unit - d_max |
| `sensor_gain` | `point:sensor` | Multiplicative scaling error (e.g. wrong flow-pickup K-factor). | $y_k = (1 + s(t)\,g)\,x_k + \dots$ | `gain`=0.2 - - relative gain error g |
| `sensor_noise` | `point:sensor` | Excessive measurement noise (loose wiring, EMI). | $y_k = y_k^{0} + s(t)\,\sigma\,\varepsilon_k,\ \varepsilon_k\sim\mathcal N(0,1)$ | `std`=1.0 point unit - noise standard deviation sigma |
| `sensor_stuck` | `point:sensor` | Sensor output frozen at its last value (or a given value). | $y_k = y_{k_0}\ \ \forall k \ge k_0$ | `value`=None point unit - frozen value (None = last value) |
| `sensor_spikes` | `point:sensor` | Random outlier spikes. | $y_k = y_k^{0} + B_k\,\sigma_s\,\eta_k,\ B_k\sim\mathrm{Bern}(p)$ | `prob`=0.05 - - spike probability p per sample<br>`std`=5.0 point unit - sigma_s |
| `sensor_dropout` | `point:sensor` | Intermittent or complete loss of samples (failing transmitter). | $P(\text{missing}_k)=s(t)\,p$ | `prob`=1.0 - - loss probability p (1 = offline) |
| `sensor_override` | `point:sensor` | Spoofed / overwritten value (cyber-physical attack or wiring swap). | $y_k = v$ | `value`=20.0 point unit - reported value v |
