# Tutorial 2 - Faults, events and scenarios

All abnormal or random conditions are *injections* of a registered type (see the full
[fault & event catalog](fault_catalog.md), or `vbas faults`). An injection has

| field | meaning |
|---|---|
| `type` | e.g. `sensor_drift`, `vav_damper_stuck`, `chiller_fouling`, `occupancy_surge`, `weather_change` |
| `target` | point id (`AHU-1/SA-T`), equipment id (`VAV-Core_mid`, `AHU-2`, `CH-1`), zone name (`Core_mid`) or `building` |
| `start` | `now`, ISO time `2023-07-11T08:00:00`, or relative `+2h`, `+3d` |
| `end` / `duration` | ISO time / `6h`, `2d` (omit = permanent) |
| `profile` | `step`, `ramp` (incipient fault, `ramp_s`), `intermittent` (`period_s`, `duty`) |
| `params` | type specific, e.g. `{"rate_per_day": 0.5}` |
| `source` | `human`, `ai`, `scenario`, `random` - kept in the labels |

## Five layers

* **sensor** - `sensor_bias`, `sensor_drift`, `sensor_gain`, `sensor_noise`, `sensor_stuck`, `sensor_spikes`,
  `sensor_dropout`, `sensor_override` (spoofing)
* **actuator** - `vav_damper_stuck`, `reheat_valve_stuck_closed/open`, `oa_damper_stuck`,
  `cooling_coil_valve_stuck_closed`, `heating_coil_valve_stuck_closed`, `supply_fan_failure`
* **equipment** (physics inside EnergyPlus) - `chiller_fouling`, `boiler_fouling`, `tower_fouling`,
  `filter_fouling`, `fan_degradation`, `equipment_trip`
* **control** - `schedule_error_always_on/off`, `pid_mistuning`, `economizer_disabled/always_on`,
  `sat_reset_disabled`, `controller_frozen`, `setpoint_override`
* **network** - `comm_loss` (controller off-line), `historian_outage`

and **events** (non-fault randomness): `occupancy_surge`, `meeting`, `holiday`, `weather_change`, `window_open`,
`plug_load_change`, `lighting_change`, `outdoor_co2_change`.

## Three ways to inject

1. **GUI** - *Faults & Events* page (forms are generated from the catalog).
2. **Scenario file** (reproducible experiments):

```yaml
start: 2023-07-10
end: 2023-07-23
seed: 42
realism: 1.0
occupancy: {stochastic: true}
random_faults: {rate_per_week: 2}
injections:
  - {type: chiller_fouling, target: CH-1, start: 2023-07-12T00:00:00, profile: ramp, ramp_s: 432000, params: {ratio: 0.6}}
  - {type: oa_damper_stuck, target: AHU-2, start: +3d, duration: 12h, params: {position: 100}}
```

3. **API** (humans, scripts, AI agents):

```bash
curl -X POST http://127.0.0.1:8000/api/injections -H "Content-Type: application/json" \
     -d '{"type":"vav_damper_stuck","target":"VAV-Core_mid","params":{"position":20},"duration":"6h","source":"ai"}'
```

## Background realism

`realism` scales all data-sheet imperfections (installation bias, gain error, drift rate, noise, spikes, data loss)
of all sensors; `0` gives ideal sensors, `1` typical commercial BAS hardware. Sensor classes and their parameters are
defined in `virtualbas/realworld/sensors.py` and can be overridden per class or per point in a scenario:

```yaml
sensors:
  zone_temperature: {noise_std: 0.1, bias_std: 0.5}
  AHU-1/SA-T: {tau_s: 120}
```

## Random fault generator

`random_faults: {rate_per_week: λ}` draws fault arrivals from a Poisson process; type, target, magnitude and duration
are sampled from `virtualbas/realworld/random_faults.py::DEFAULT_MENU` (customisable). Enable/disable at run time with
`POST /api/random {"rate_per_week": 2}`.

## Adding your own fault type

```python
from virtualbas.realworld.faults import register, Param

@register("duct_leak", "fault", "equipment", "equip:AHU", "Supply duct leakage", r"\dot V_{zone} = (1-s\,\ell)\dot V",
          {"leak": Param(0.1, "-", "leakage fraction")})
def _duct_leak(inj, s, ov, ctx):
    ov.fan_eff_mult[inj.target] = ov.fan_eff_mult.get(inj.target, 1.0) * (1 - s * inj.p("leak"))
```

The new type immediately appears in the GUI, the REST catalog and the MCP tools.
