"""Experiment 2 - Fault impact matrix (inner/outer space coupling at equipment level).

Each scenario injects ONE fault/event into a realistic run (sensor imperfections, stochastic
occupancy) and is compared with a fault-free twin run with identical random seed (common random
numbers), so that every difference is attributable to the injected fault. Two one-week periods
(summer, winter) are simulated.
"""
import argparse
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FAULTS = [
    # (id, layer, spec)
    ("none", "-", None),
    ("ZN-T drift (Core_mid, +0.5 K/d)", "sensor", {"type": "sensor_drift", "target": "ZN-Core_mid/ZN-T", "start": "+1d", "params": {"rate_per_day": 0.5, "max_abs": 4}}),
    ("SA-T bias (AHU-2, +2 K)", "sensor", {"type": "sensor_bias", "target": "AHU-2/SA-T", "start": "+1d", "params": {"bias": 2.0}}),
    ("OA-T bias (+4 K)", "sensor", {"type": "sensor_bias", "target": "WX/OA-T", "start": "+1d", "params": {"bias": 4.0}}),
    ("MA-T stuck (AHU-2)", "sensor", {"type": "sensor_stuck", "target": "AHU-2/MA-T", "start": "+1d", "params": {"value": 13.0}}),
    ("CHW-ST bias (-1.5 K)", "sensor", {"type": "sensor_bias", "target": "CHW-SYS/CHW-ST", "start": "+1d", "params": {"bias": -1.5}}),
    ("DA-F gain (VAV-Core_mid, +30%)", "sensor", {"type": "sensor_gain", "target": "VAV-Core_mid/DA-F", "start": "+1d", "params": {"gain": 0.3}}),
    ("ZN-T dropout (Core_mid)", "sensor", {"type": "sensor_dropout", "target": "ZN-Core_mid/ZN-T", "start": "+1d", "params": {"prob": 1.0}}),
    ("VAV damper stuck 20% (Core_mid)", "actuator", {"type": "vav_damper_stuck", "target": "VAV-Core_mid", "start": "+1d", "params": {"position": 20}}),
    ("Reheat valve stuck closed (Perim_mid_1)", "actuator", {"type": "reheat_valve_stuck_closed", "target": "VAV-Perimeter_mid_ZN_1", "start": "+1d"}),
    ("Reheat valve leaking (Perim_mid_1)", "actuator", {"type": "reheat_valve_stuck_open", "target": "VAV-Perimeter_mid_ZN_1", "start": "+1d"}),
    ("OA damper stuck 100% (AHU-2)", "actuator", {"type": "oa_damper_stuck", "target": "AHU-2", "start": "+1d", "params": {"position": 100}}),
    ("OA damper stuck closed (AHU-2)", "actuator", {"type": "oa_damper_stuck", "target": "AHU-2", "start": "+1d", "params": {"position": 0}}),
    ("CHW valve stuck closed (AHU-1)", "actuator", {"type": "cooling_coil_valve_stuck_closed", "target": "AHU-1", "start": "+1d"}),
    ("Supply fan failure (AHU-1, 8 h)", "actuator", {"type": "supply_fan_failure", "target": "AHU-1", "start": "+2d+9h", "duration": "8h"}),
    ("Chiller fouling (CH-1, r=0.6)", "equipment", {"type": "chiller_fouling", "target": "CH-1", "start": "+1d", "params": {"ratio": 0.6}}),
    ("Chiller trip (CH-1)", "equipment", {"type": "equipment_trip", "target": "CH-1", "start": "+1d"}),
    ("Boiler fouling (r=0.6)", "equipment", {"type": "boiler_fouling", "target": "BLR-1", "start": "+1d", "params": {"ratio": 0.6}}),
    ("Tower fouling (r=0.5)", "equipment", {"type": "tower_fouling", "target": "CT-1", "start": "+1d", "params": {"ratio": 0.5}}),
    ("Filter fouling (AHU-2, +300 Pa)", "equipment", {"type": "filter_fouling", "target": "AHU-2", "start": "+1d", "params": {"dp_add": 300}}),
    ("Fan degradation (AHU-2, -30%)", "equipment", {"type": "fan_degradation", "target": "AHU-2", "start": "+1d", "params": {"loss": 0.3}}),
    ("Schedule 24/7 (AHU-2)", "control", {"type": "schedule_error_always_on", "target": "AHU-2", "start": "+1d"}),
    ("Economizer disabled (AHU-2)", "control", {"type": "economizer_disabled", "target": "AHU-2", "start": "+1d"}),
    ("PI mistuning x6 (VAV-Core_mid)", "control", {"type": "pid_mistuning", "target": "VAV-Core_mid", "start": "+1d", "params": {"multiplier": 6}}),
    ("Comm. loss VAV-Core_mid (12 h)", "network", {"type": "comm_loss", "target": "VAV-Core_mid", "start": "+2d+8h", "duration": "12h"}),
    ("Occupancy surge x2 (Core_mid, 4 h)", "event", {"type": "occupancy_surge", "target": "Core_mid", "start": "+2d+10h", "duration": "4h", "params": {"multiplier": 2.0}}),
    ("Heat wave / cold snap (+-5 K, 3 d)", "event", None),  # filled per season
    ("Window open (Perim_bot_1, 6 h)", "event", {"type": "window_open", "target": "Perimeter_bot_ZN_1", "start": "+2d+9h", "duration": "6h", "params": {"ach": 3.0}}),
]

SEASONS = {"summer": ("2023-07-10", "2023-07-16"), "winter": ("2023-01-09", "2023-01-15")}


def _fix_start(spec, start):
    import datetime as dt
    s = dict(spec)
    st = s.get("start", "+0d")
    base = dt.datetime.fromisoformat(start)
    if isinstance(st, str) and st.startswith("+"):
        total = 0.0
        for part in st[1:].split("+"):
            num, unit = float(part[:-1]), part[-1]
            total += num * {"m": 60, "h": 3600, "d": 86400}[unit]
        s["start"] = (base + dt.timedelta(seconds=total)).isoformat()
    return s


def run_one(args):
    name, layer, spec, season, out_root = args
    from virtualbas.core import VirtualBAS
    start, end = SEASONS[season]
    sc = {"start": start, "end": end, "seed": 11, "realism": 1.0, "occupancy": {"stochastic": True}}
    if name.startswith("Heat wave"):
        spec = {"type": "weather_change", "target": "building", "start": "+2d", "duration": "3d",
                "params": {"delta_t": 5.0 if season == "summer" else -5.0}}
    if spec:
        sc["injections"] = [_fix_start(spec, start)]
    safe = "".join(c if c.isalnum() else "_" for c in name)[:40]
    out = Path(out_root) / season / safe
    record = name in ("none", "ZN-T drift (Core_mid, +0.5 K/d)", "OA damper stuck 100% (AHU-2)", "Chiller fouling (CH-1, r=0.6)",
                      "Reheat valve stuck closed (Perim_mid_1)", "Filter fouling (AHU-2, +300 Pa)")
    t = time.time()
    v = VirtualBAS(ROOT / "buildings/large_office", out_dir=out if record else None, scenario=sc, speed="max")
    res = v.run()
    return {"fault": name, "layer": layer, "season": season, "kpi": res["kpi"], "wall_s": time.time() - t,
            "alarms": len([a for a in v.alarms.history if a["state"] == "ALARM"]), "error": res["error"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "results/exp2_faults"))
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    jobs = [(n, l, s, season, a.out) for season in SEASONS for (n, l, s) in FAULTS]
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        results = list(ex.map(run_one, jobs))
    Path(a.out).mkdir(parents=True, exist_ok=True)
    (Path(a.out) / "results.json").write_text(json.dumps(results, indent=1))
    for r in results:
        print(r["season"], r["fault"], round(r["kpi"]["elec_kwh"]), round(r["kpi"]["gas_kwh"]), round(r["kpi"]["comfort_kh"], 1), r["error"])


if __name__ == "__main__":
    main()
