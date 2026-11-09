"""Experiment 6 - AI agents in the loop.

Part A  An autonomous "adversarial" AI agent injects faults through the public REST API (the
        same endpoints a human uses in the GUI). It observes the building every 6 simulated hours
        and chooses the fault that is expected to be most disruptive for the current conditions.
Part B  A supervisory AI controller (Gymnasium interface) is evaluated in three outer spaces:
        ideal sensors, realistic sensors, realistic sensors + outdoor-air sensor bias. This shows
        the "simulation-to-reality gap" that EmuBAS exposes before deployment.
"""
import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


# ----------------------------------------------------------------------------- Part A
def adversary_policy(client):
    """Heuristic adversary: read the BAS like an operator and pick a damaging fault."""
    snap = client.get("/api/snapshot").json()
    pts = snap["points"]

    def val(p):
        v = pts.get(p, [None])[0]
        return v if v is not None else math.nan
    oat = val("WX/OA-T")
    ahus = ["AHU-1", "AHU-2", "AHU-3", "AHU-4"]
    big = max(ahus, key=lambda a: val(f"{a}/SF-KW") if not math.isnan(val(f"{a}/SF-KW")) else -1)
    hour = int(snap["time"][11:13])
    active = {(i["type"], i["target"]) for i in snap["injections"] if i["severity"] > 0}
    zones = [k.split("/")[0] for k in pts if k.endswith("/ZN-T")]
    if oat > 26 and ("oa_damper_stuck", big) not in active:
        return {"type": "oa_damper_stuck", "target": big, "params": {"position": 100}, "duration": "12h",
                "note": f"hot outdoor air ({oat:.1f} C): force 100% OA on the largest AHU"}
    if hour >= 20 and ("schedule_error_always_on", big) not in active:
        return {"type": "schedule_error_always_on", "target": big, "duration": "10h", "note": "after-hours runtime"}
    z = zones[sum(map(ord, snap["time"])) % len(zones)]
    return {"type": "sensor_drift", "target": f"{z}/ZN-T", "params": {"rate_per_day": 0.8, "max_abs": 3}, "duration": "2d",
            "note": "slow stealthy drift of a zone thermostat"}


def part_a(out: Path):
    from fastapi.testclient import TestClient
    from virtualbas.server.app import create_app
    sc = {"start": "2023-07-10", "end": "2023-07-16", "seed": 5, "start_paused": True}
    app = create_app(str(ROOT / "buildings/large_office"), sc, speed="max", out_root=str(out / "partA"))
    c = TestClient(app)
    v = app.state.session.vbas
    while v.warmup:
        time.sleep(0.1)
    c.post("/api/control", json={"action": "pause"})
    log = []
    for k in range(4 * 6):           # 6 days, every 6 h
        dec = adversary_policy(c)
        r = c.post("/api/injections", json=dict(dec, source="ai"))
        log.append({"time": c.get("/api/status").json()["time"], "decision": dec, "status": r.status_code,
                    "id": r.json().get("id")})
        k0 = v.step_count               # read before releasing the steps (avoids a race at max speed)
        c.post("/api/control", json={"action": "step", "value": 72})
        while v.step_count < k0 + 72 and not v.engine.finished.is_set():
            time.sleep(0.01)
        if v.engine.finished.is_set():
            break
    c.post("/api/control", json={"action": "resume"})
    v.engine.finished.wait(120)
    res = v.finish()
    inj = c.get("/api/injections").json()
    (out / "partA_log.json").write_text(json.dumps({"log": log, "kpi": res["kpi"], "injections": inj}, indent=1, default=str))
    print("Part A: AI injected", len(inj), "faults; KPI", res["kpi"])
    return res


# ----------------------------------------------------------------------------- Part B
def sat_reset_policy(obs_names, obs):
    """Supervisory AI policy: outdoor-air based SAT and CHWST reset (acts on OBSERVED values)."""
    oat = obs[obs_names.index("WX/OA-T")]
    x = min(1.0, max(0.0, (oat - 15.0) / (24.0 - 15.0)))
    sat = 16.5 - x * (16.5 - 12.8)
    chw = 9.0 - x * (9.0 - 6.7)
    return np.array([sat] * 4 + [chw], dtype=np.float32)


def run_agent(case: str, use_agent: bool, season):
    from virtualbas.ai.gym_env import VirtualBASEnv
    start, end = season
    sc = {"start": start, "end": end, "seed": 21, "occupancy": {"stochastic": True}}
    if case == "ideal":
        sc["realism"] = 0.0
    else:
        sc["realism"] = 1.0
    if case == "oat_bias":
        sc["injections"] = [{"type": "sensor_bias", "target": "WX/OA-T", "start": start, "params": {"bias": 4.0}}]
    env = VirtualBASEnv(ROOT / "buildings/large_office", scenario=sc, decision_steps=3)
    obs, info = env.reset(seed=21)
    total = 0.0
    while True:
        if use_agent:
            a = sat_reset_policy(env.obs_points, obs)
        else:
            a = None
        if a is None:
            # no agent: write the baseline values (equivalent to the BAS program)
            a = np.array([12.8] * 4 + [6.7], dtype=np.float32)
        obs, r, term, trunc, info = env.step(a)
        if term:
            break
        total += r
    kpi = dict(env.vbas.kpi) if env.vbas else {}
    env.close()
    return {"case": case, "agent": use_agent, "return": total, "kpi": kpi}


def part_b(out: Path):
    from concurrent.futures import ProcessPoolExecutor
    seasons = {"shoulder": ("2023-05-15", "2023-05-28"), "summer": ("2023-07-10", "2023-07-23")}
    jobs = [(case, ag, s) for s in seasons for case in ["ideal", "realistic", "oat_bias"] for ag in [False, True]]
    with ProcessPoolExecutor(max_workers=4) as ex:
        futs = [(j, ex.submit(run_agent, j[0], j[1], seasons[j[2]])) for j in jobs]
        res = []
        for j, f in futs:
            r = f.result()
            r["season"] = j[2]
            res.append(r)
            print(r["season"], r["case"], "agent" if r["agent"] else "baseline", round(r["kpi"]["elec_kwh"]),
                  round(r["kpi"]["gas_kwh"]), round(r["kpi"]["comfort_kh"], 1))
    (out / "partB.json").write_text(json.dumps(res, indent=1))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "results/exp6_ai"))
    ap.add_argument("--part", default="AB")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if "A" in a.part:
        part_a(out)
    if "B" in a.part:
        part_b(out)


if __name__ == "__main__":
    main()
