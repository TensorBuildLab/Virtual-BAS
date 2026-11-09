# Tutorial 3 - Connecting AI agents (ambient AI, FDD, RL, LLM operators)

EmuBAS offers four interfaces. All of them see the building **through the outer space** (observed values,
missing data, faults) - exactly like an AI deployed in a real building would.

## 1. REST API (any language)

Interactive OpenAPI documentation: <http://127.0.0.1:8000/docs>. Main endpoints:

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/info`, `/api/status` | building, clock, KPIs, alarms, injections |
| GET | `/api/equipment`, `/api/points` | equipment hierarchy, point list with Haystack tags / Brick classes |
| GET | `/api/snapshot?truth=0` | present values of all points (`truth=1` adds the ground truth) |
| GET | `/api/read?points=a,b` | selected present values |
| GET | `/api/trend?points=a,b&n=288` | trend log (ring buffer, 2 weeks) |
| GET | `/api/alarms` | active alarms + history |
| POST | `/api/write` | priority-array override of set points / commands |
| POST | `/api/control` | pause / resume / step / speed / stop |
| GET | `/api/points?tier=next_gen` | point list filtered by tier (standard / advanced / next_gen / truth) |
| GET | `/api/forecast?hours=48` | hourly weather forecast as issued (add `truth=1` for the realised weather) |
| GET | `/api/faults/catalog` | injectable types with parameters and equations |
| GET/POST/DELETE | `/api/injections` | list / inject / clear faults & events |
| POST | `/api/random` | random fault generator rate |
| POST | `/api/session` | restart with a new scenario |
| WS | `/ws?truth=0` | snapshot push every second |

## 2. Python client

```python
from virtualbas.ai.client import VBASClient
bas = VBASClient("http://127.0.0.1:8000")
bas.read(["AHU-1/SA-T", "AHU-1/SA-T-SP"])
bas.write("AHU-1/SA-T-SP", 14.0, priority=10, duration_s=3600)        # supervisory control
bas.inject("sensor_bias", "AHU-1/SA-T", params={"bias": 2}, duration="1d", source="ai")   # adversarial agent
bas.pause(); bas.step(12); bas.resume()                                 # lock-step operation
bas.points(tier="next_gen")                                             # IEQ, people counts, BTU meters, grid signals
bas.forecast(24)                                                        # weather forecast for MPC-style agents
bas.read(["GRID/PRICE", "GRID/CO2-INT", "GRID/DR-EVENT", "MTR/BLDG-DMD-15"])
```

## 3. MCP server for LLM agents

```bash
pip install "mcp<2"
python -m virtualbas.ai.mcp_server --url http://127.0.0.1:8000
```

Register it in an MCP client (e.g. Claude Desktop / Claude Code):

```json
{"mcpServers": {"virtual-bas": {"command": "python",
  "args": ["-m", "virtualbas.ai.mcp_server", "--url", "http://127.0.0.1:8000"]}}}
```

Tools: `building_info`, `list_equipment`, `list_points` (with tier filter), `weather_forecast`, `read_points`, `get_trend`, `get_alarms`, `write_point`,
`release_point`, `fault_catalog`, `inject`, `clear_injection`, `list_injections`, `simulation_control`.
To emulate the instrumentation of a typical BAS of today, start the session with `point_tiers: [standard]` in the
scenario; the agent then sees only standard points while the full ground truth is still recorded. Comparing an agent
with `[standard]` and with all tiers quantifies the value of next-generation sensing for its task.

An LLM can now act as an ambient operator ("why is zone Core_mid cold?") or as a red team ("inject a realistic
fault that the FDD system will miss").

## 4. Gymnasium environment (in-process, fastest)

```python
from virtualbas.ai.gym_env import VirtualBASEnv
env = VirtualBASEnv("buildings/large_office", scenario={"start": "2023-07-01", "end": "2023-07-31",
                    "random_faults": {"rate_per_week": 2}}, decision_steps=3)
obs, info = env.reset(seed=0)
obs, reward, terminated, truncated, info = env.step(env.action_space.sample())
```

* Observations: BAS-observed values of AHUs, zones, plant and weather + time features.
* Actions: AHU supply-air set points and the chilled-water set point (configurable: any software point and bounds).
* Reward: −(electricity + w_gas·gas)/100 − w_comfort·(comfort violation K·h), computed from the *truth*.
* `decision_steps=3` → one decision every 15 min. The simulation runs at maximum speed.

## Recommended practice

Train/evaluate an AI agent in three outer spaces - `realism: 0` (ideal), `realism: 1` (realistic) and realistic +
injected faults - to quantify its robustness before deployment (see Experiment 6 in the paper).
