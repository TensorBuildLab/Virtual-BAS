"""Experiment 4 - Time-acceleration accuracy and throughput.

The simulation is paced to a target speed factor s (simulated seconds per wall-clock second).
For each target the achieved factor is measured over a number of BAS steps.
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "results/exp4_speed"))
    ap.add_argument("--realtime", action="store_true", help="also measure 1x (takes 10 minutes)")
    a = ap.parse_args()
    from virtualbas.core import VirtualBAS
    v = VirtualBAS(ROOT / "buildings/large_office", scenario={"start": "2023-07-10", "end": "2023-07-24", "seed": 3}, speed="max")
    v.start()
    while v.warmup or v.step_count < 5:
        time.sleep(0.05)
    targets = ([(1, 2)] if a.realtime else []) + [(10, 4), (60, 12), (360, 40), (3600, 200), ("max", 3000)]
    res = []
    for s, n in targets:
        v.set_speed(s)
        k = v.step_count
        while v.step_count < k + 2:      # let the pacing settle on the new target
            time.sleep(0.001)
        k0, t0 = v.step_count, time.perf_counter()
        while v.step_count < k0 + n:
            time.sleep(0.001)
        wall = time.perf_counter() - t0
        sim = n * 300.0
        achieved = sim / wall
        res.append({"target": s, "steps": n, "wall_s": wall, "achieved_factor": achieved,
                    "error_%": None if s == "max" else (achieved - float(s)) / float(s) * 100,
                    "ms_per_step": wall / n * 1000})
        print(res[-1])
    v.stop()
    v.engine.finished.wait(60)
    Path(a.out).mkdir(parents=True, exist_ok=True)
    (Path(a.out) / "speed.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
