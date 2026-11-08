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

Unsupported objects are simply left under native EnergyPlus control, so any model runs. Contributions of adapters for
more system types (fan coils, VRF, radiant, heat pumps) are welcome: add the object types to
`virtualbas/model/topology.py`, points to `virtualbas/bas/catalog.py` and actuation to `virtualbas/core.py`.

## Verification

Run your building once with ideal sensors and the baseline profile and compare it with the native model:

```bash
python experiments/exp1_validation.py --building buildings/my_building --start 2023-01-01 --end 2023-12-31 --out results/my_validation
python experiments/compare_native.py results/my_validation
```
