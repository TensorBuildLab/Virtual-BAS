# Tutorial 4 - Convert your own building

```bash
vbas prepare --model path/to/my_building.idf --weather path/to/site.epw --out buildings/my_building --timesteps 12
vbas points  --building buildings/my_building          # inspect the generated BAS point list
vbas serve   --building buildings/my_building
```

`prepare` performs topology discovery, command binding, physical fault hooks and a sizing run, and writes

| file | content |
|---|---|
| `model.epJSON` | the BAS-ready EnergyPlus model |
| `manifest.json` | topology, command & fault bindings, native schedules, autosized design values |
| `weather.epw` | weather file |
| `building.yaml` | editable configuration (name, control profile, set points) |

## Configuration (`building.yaml`)

```yaml
name: My Building
control:
  profile: baseline           # baseline | g36
  schedule_source: native     # native: use the model's own schedules | config: use the values below
  weekday_start: 6.0
  weekday_end: 22.0
  htg_occ: 21.0
  clg_occ: 24.0
  sat_min: 12.8
  chwst: 6.7
```

All fields of `virtualbas.control.sequences.ControlConfig` can be set here or per scenario.

## What is supported

| System element | Monitored | BAS-controlled |
|---|---|---|
| Zones with thermostats | yes | yes (set points through the thermostat local loop) |
| `AirTerminal:SingleDuct:VAV:Reheat` / `:NoReheat` | yes | yes (air-flow command, reheat local loop) |
| Multi-zone `AirLoopHVAC` with `Controller:OutdoorAir` | yes | yes (fan start/stop, SAT, economizer/min OA, static pressure) |
| Water coils, `Fan:VariableVolume` | yes | through local loops |
| Chillers (electric EIR/reformulated EIR), boilers, towers, pumps | yes | supply temperatures, enable/trip, fouling |
| Packaged single-zone systems, DX coils | partly | native local control (thermostat from BAS) |
| Zone equipment: `ZoneHVAC:PackagedTerminalHeatPump`, `...:PackagedTerminalAirConditioner`, `...:WaterToAirHeatPump`, electric baseboards, ideal loads | yes | enable (availability schedule), thermostat local loop; DX capacity/COP degradation and trips |
| `ZoneHVAC:EnergyRecoveryVentilator` (sensible/latent plate or rotary HX) | yes | enable; fan failures, heat-recovery degradation |
| `ElectricLoadCenter:Distribution` with PV generators, inverter and storage | yes | battery charge/discharge (EMS storage actuators), PV soiling / inverter trips, grid outages |
| Stand-alone `WaterHeater:Mixed` | yes | tank set point |

Unsupported objects are simply left under native EnergyPlus control, so any model runs. Contributions of adapters for
more system types (fan coils, VRF, radiant) are welcome: add the object types to
`virtualbas/model/topology.py`, points to `virtualbas/bas/catalog.py` and actuation to `virtualbas/core.py`.

### Small all-electric buildings (zone heat pumps, ERVs, PV, storage)

Zone equipment is discovered from `ZoneHVAC:EquipmentList`, distributed energy resources from
`ElectricLoadCenter:Distribution`. Equipment ids: `HP-<zone>` / `PTAC-<zone>` / `ERV-<zone>` / `BB-<zone>`,
`PV` (system, with `PVA-<array>` children), `ESS` (storage), `DHW-<n>`; grid exchange is on `GRID`
(`IMPORT-PWR`, `EXPORT-PWR`, `NET-PWR`, `OUTAGE`). Battery dispatch writes `ESS/CHG-CMD` / `ESS/DCHG-CMD`
(kW; blank = the native storage scheme) to the EnergyPlus `Electrical Storage` actuators, which are keyed on the
*distribution* name. How each physical fault is realised in EnergyPlus 23.2:

| Fault | EnergyPlus mechanism (added by `vbas prepare`, inactive by default) |
|---|---|
| `hp_capacity_degradation` | per-coil copies of the DX capacity / EIR f(T) curves; an EMS program overrides `Curve Result` with r_Q f_Q(T) and f_EIR(T)/r_COP (`@CurveValue` of the original curve at the coil inlet / outdoor conditions) |
| `hp_trip` | unit availability schedule forced to 0 |
| `erv_fan_failure` | EMS `Fan Air Mass Flow Rate` = 0 on the failed fan(s) |
| `erv_hx_degradation` | HX supply-outlet temperature control with an EMS set point: pass-through when healthy, bypass to T_oa + r eps (T_exh - T_oa) when faulted |
| `pv_soiling`, `inverter_trip` | `Generator:PVWatts` ignores availability schedules and EMS power requests, so the lost AC power is drawn by a non-thermal `ElectricEquipment` (fraction lost = 1) through its EMS actuator and removed again from the building-load meters |
| `battery_soc_sensor_drift` | measurement layer only (drift on `<ESS>/SOC`), the BAS dispatches on the wrong value |
| `grid_outage` | islanding is emulated: PV export curtailed, storage covers the load; when storage reaches its minimum (or without backup) the building goes dark (units, lights and plugs off); grid import during the outage is reported as `GRID/UNSERVED-KW` |

The `geb` control profile adds pre-cooling before the on-peak window, an on-peak set-point relaxation, battery
dispatch from the TOU / demand-response signals and load shedding on `demand_response` events
(`geb_*` and `ess_*` fields of `ControlConfig`). The `baseline` profile reproduces the native EnergyPlus run.

## Verification

Run your building once with ideal sensors and the baseline profile and compare it with the native model:

```bash
python experiments/exp1_validation.py --building buildings/my_building --start 2023-01-01 --end 2023-12-31 --out results/my_validation
python experiments/compare_native.py results/my_validation
```
