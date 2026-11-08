"""Example 3 - an autonomous AI fault injector (adversarial agent).

The agent looks at the building like an operator and decides which abnormality to inject,
e.g. to stress-test a fault detection system. Any LLM agent can do the same through the REST
API or the MCP server (virtualbas.ai.mcp_server).
"""
import math
import random
import time

from virtualbas.ai.client import VBASClient

bas = VBASClient("http://127.0.0.1:8000")
catalog = {f["name"]: f for f in bas.fault_catalog()}
equip = bas.equipment()
ahus = [e["id"] for e in equip if e["type"] == "AHU"]
vavs = [e["id"] for e in equip if e["type"] == "VAV"]
rng = random.Random(0)

for k in range(10):
    snap = bas.snapshot()
    pts = snap["points"]
    oat = pts["WX/OA-T"][0] or math.nan
    if oat > 26:
        target = max(ahus, key=lambda a: pts.get(f"{a}/SF-KW", [0])[0] or 0)
        choice = ("oa_damper_stuck", target, {"position": 100})
    elif rng.random() < 0.5:
        choice = ("vav_damper_stuck", rng.choice(vavs), {"position": rng.choice([0, 100])})
    else:
        choice = ("sensor_bias", f"{rng.choice(ahus)}/SA-T", {"bias": rng.choice([-2, 2])})
    t, target, params = choice
    print(snap["time"], "AI injects", t, "on", target, params, "-", catalog[t]["equation"])
    bas.inject(t, target, params=params, duration="4h", source="ai")
    time.sleep(10)
