# Who is Virtual BAS for? - 18 uses

A real BAS is a poor place to learn, experiment or certify. Faults cannot be staged on demand, and the true state is
unknown. Every mistake affects occupants and equipment, a year of operation takes a year, and access is restricted by
owners, vendors and IT security. Virtual BAS removes these barriers:

* **safe to break** - stuck dampers, tripped chillers and drifting sensors harm nobody
* **labelled** - every fault and imperfection has a defining equation and a ground-truth record
* **repeatable** - seeded scenarios give everyone the same building, weather, occupants and faults
* **fast** - 1x to about 90,000x real time, changeable while running
* **open and generic** - free, MIT-licensed, and any EnergyPlus model can be converted

The table below lists the uses grouped into four areas. **Evidence** tells you how far each use is supported today:
*Exp. n* means it is demonstrated in Experiment n of the paper; *interfaces* means all needed functions exist but
there is no published evaluation yet; *partial* means some functions are still missing.

| # | Use | Who | What you use | Evidence |
|---|---|---|---|---|
| | **Research and development of building AI** | | | |
| 1 | FDD development and benchmarking | FDD researchers, analytics developers | `vbas run` with `random_faults` / `injections`; `labels.parquet` | Exp. 3, 4 |
| 2 | Supervisory, MPC and RL control under realistic conditions | control and RL researchers | Gymnasium env, `realism`, faults; compare `realism: 0` vs `1` | Exp. 5 |
| 3 | Ambient-AI and LLM operators (and adversaries) | AI researchers, BAS vendors | MCP server, REST API, priority overrides, alarms | Exp. 5 |
| 4 | Foundation models and synthetic pre-training data | ML researchers | batch `vbas run` over buildings, seasons, seeds | Exp. 4, 8 |
| 5 | Virtual sensing, state estimation, sensor recalibration | researchers, analytics developers | `observed.parquet` vs `truth.parquet`, `sensors.json` | Exp. 2 |
| 6 | Metadata inference and portable (Brick/Haystack) apps | researchers, integrators | `points.json` of automatically converted buildings | Exp. 8 |
| 7 | Value of information and sensor design | sensor makers, designers, standard writers | `point_tiers: [standard]` vs. all tiers | Exp. 6 |
| | **Education and workforce development** | | | |
| 8 | University courses: HVAC, controls, building energy, building data science | instructors, students | web GUI, scenario files, truth switch, time acceleration | interfaces |
| 9 | Operator, facility-manager and technician training | owners, utilities, training programmes | `scenarios/training_drill.yaml`, random faults, alarms, trends | interfaces |
| 10 | Commissioning and retro-commissioning practice | commissioning agents | staged faults, overrides for functional tests, trends | interfaces |
| 11 | Emergency and resilience drills | facility managers | `wildfire_smoke`, `weather_change`, `equipment_trip`, `demand_response` | Exp. 6 |
| 12 | Alarm management and operator-interface (HMI) research | human-factors researchers, vendors | reproducible alarm floods for user studies | interfaces |
| | **Industry practice** | | | |
| 13 | Neutral evaluation of commercial FDD / analytics products | owners, utilities, efficiency programmes | blind recorded runs; score against `injections_table.json` | Exp. 4 |
| 14 | Control-sequence verification and virtual commissioning | designers, control contractors | G36-style sequences in closed loop, sensor faults | Exp. 2, 3 |
| 15 | BAS and analytics software development | vendors, start-ups | a "mock building" behind REST / WebSocket / MCP for CI and demos | interfaces |
| 16 | Cyber-physical security | security researchers | `sensor_override` (spoofing), overrides, `comm_loss`, `historian_outage` | partial |
| 17 | Grid-interactive buildings and demand response | utilities, aggregators | tariff, carbon intensity, `GRID/DR-EVENT`, demand meters | interfaces |
| | **Research community** | | | |
| 18 | Shared benchmarks, competitions, reproducible studies | everyone | seeded scenarios, open models, common KPIs | Exp. 1-8 |

## Recipes

### Teaching a course

Start one server per student group (each on its own port), or give every student the same seeded scenario on their
own laptop. A typical lab session:

1. Explore the AHU, VAV, plant and zone graphics with the **truth** switch off. Map each point to the equipment.
2. Change set points from the point explorer, for example the AHU supply-air temperature or a zone set point, and
   watch the loops respond in the trends. Run the clock at 60x-360x.
3. Inject a fault from *Faults & Events* (a stuck VAV damper, a drifting zone sensor, economizer disabled). Predict
   the symptoms first, then check them.
4. Switch the truth on: what did the BAS show, and what really happened?
5. For data-science courses, record a run (`vbas run ... --out results/lab1`) and give students the parquet files.

### A troubleshooting drill for operators

```bash
vbas serve --building buildings/large_office --scenario scenarios/training_drill.yaml --speed 360x
```

The trainee works only with graphics, trends, alarms and overrides, with the truth switch off and without opening the
*Faults & Events* page, and writes down equipment, fault and onset time. The instructor then opens
`GET /api/injections` (or the *Faults & Events* page) as the answer key. Change `seed` for a new drill, raise
`random_faults.rate_per_week` for a harder one, or set `point_tiers` to all tiers to show trainees what extra sensors
would reveal. For now hiding the labels relies on the trainee not opening that page; a proper instructor/trainee mode
is planned.

### Testing an analytics product

Record a blind run with random faults, give the product only `observed.parquet` and `points.json` (or the live REST
API), and score its findings against `injections_table.json` and `labels.parquet`
(see `experiments/exp3_fdd_benchmark.py` for a scoring example).

### Value of an extra sensor

Run the same scenario (same `seed`) twice, once with `point_tiers: [standard]` and once with all tiers, and compare
what an algorithm or a person can detect. `scenarios/standard_bas.yaml` and `scenarios/wildfire_smoke.yaml` are
examples.

## Status and contributions

Uses marked *interfaces* or *partial* have not yet been evaluated with users (for example, with students in a course).
If you use Virtual BAS for teaching, training, product testing or a competition, please open an issue or a pull request
with your course module, drill or benchmark, so others can build on it.
