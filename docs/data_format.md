# Output data format

A recorded run (`vbas run ... --out DIR` or `VirtualBAS(..., out_dir=DIR)`) contains:

| File | Rows × columns | Content |
|---|---|---|
| `observed.parquet` | samples × sensor points | BAS trend log, what a real BAS would archive; `NaN` = missing sample |
| `truth.parquet` | samples × (sensor + ground-truth-only points) | EnergyPlus physical truth |
| `commands.parquet` | samples × software points | set points, commands, loop outputs, modes |
| `labels.parquet` | samples × sensor points | uint8 bit mask per sample (below) |
| `injections.parquet` | long table | `time, injection_id, severity` for every active injection |
| `injections_table.json` | list | full definition of every injection (type, layer, target, start, end, params, source, note) |
| `points.json` | list | point metadata (unit, kind, sensor class, Haystack tags, Brick class) |
| `sensors.json` | dict | installation bias / gain / drift rate drawn for each sensor |
| `alarms.json` | list | BAS alarm history |
| `metadata.json` | dict | scenario, seed, realism, control configuration, KPIs, EnergyPlus version |

Time stamps refer to the **end** of each 5-min interval (the moment the BAS samples).

## Label bits

| Bit | Value | Meaning |
|---|---|---|
| 0 | 1 | missing sample (sensor dropout / bursty data loss) |
| 1 | 2 | stuck (frozen) value |
| 2 | 4 | spike / outlier |
| 3 | 8 | sensor fault active (bias, drift, gain, noise, dropout, spikes) |
| 4 | 16 | communication loss of the controller |
| 5 | 32 | false binary reading (occupancy / status) |
| 6 | 64 | spoofed / overridden value |

## Loading

```python
from virtualbas.bas.historian import load_dataset
d = load_dataset("results/run")
err = d["observed"] - d["truth"][d["observed"].columns]      # exact sensor error of every sample
faulty = (d["labels"] & 8) > 0                               # samples affected by a sensor fault
```
