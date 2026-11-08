# Tutorial 1 - Run your first virtual BAS

This tutorial starts the DOE reference large office (Chicago) as a live BAS with a web front end.

## 1. Start the server

```bash
vbas serve --building buildings/large_office --scenario scenarios/demo_summer.yaml --speed 60x
```

Open <http://127.0.0.1:8000>. The first ~10-20 s are EnergyPlus warm-up days (shown in the header); then the
clock starts. `--speed` sets simulated seconds per wall-clock second:

| Speed | Meaning |
|---|---|
| `1x` | real time - one 5-min sample every 5 min (deploy-like testing of an AI agent) |
| `2x`, `10x`, `60x`, `360x` | accelerated, paced |
| `max` | as fast as possible (dataset generation, RL training) |

The speed can be changed at any time with the buttons in the header (or `POST /api/control`).

## 2. Explore the BAS

* **Overview** - building section with zone tiles (temperature vs. set points, CO2, occupancy, VAV flow),
  AHU and plant summaries, KPIs and active injections.
* **AHU** - schematic of each air handler: outdoor-air damper, mixing box, filter, chilled-water coil, preheat coil,
  supply fan, duct static pressure, economizer state, served VAV boxes.
* **VAV** - box schematic (damper, reheat coil, discharge) and its zone.
* **Plant** - chillers, chilled-water pump, cooling tower, condenser pump, boiler, hot-water pump.
* **Trends** - pick any points; plot observed values and (with the *ground truth* toggle) the EnergyPlus truth.
* **Alarms** - BAS alarms raised from *observed* values (so sensor faults can create false alarms).
* **Points** - full point list with Haystack tags and Brick classes; click a set point/command to override it
  with a priority (1 = highest, 8 = operator, 10 = default for AI agents, 16 = BAS program).

## 3. Turn on "ground truth"

The *Show ground truth (inner space)* toggle shows the EnergyPlus truth next to every observed value. Differences
are what a real BAS would never see - and exactly what Virtual BAS labels.

## 4. Inject a fault

Open **Faults & Events**, choose e.g. `sensor_drift`, target `ZN-Core_mid/ZN-T`, `rate_per_day = 1`,
duration `2d`, and press *Inject*. Watch the VAV page of `VAV-Core_mid`: the observed zone temperature stays at the
set point while the true temperature drops and the air flow increases.

## 5. Headless one-shot run

```bash
vbas run --building buildings/large_office --scenario scenarios/drift_example.yaml --out results/drift
```

produces `results/drift/{observed,truth,commands,labels,injections}.parquet` plus metadata. Load it with

```python
from virtualbas.bas.historian import load_dataset
d = load_dataset("results/drift")
d["observed"]["ZN-Core_mid/ZN-T"].plot(); d["truth"]["ZN-Core_mid/ZN-T"].plot()
```
