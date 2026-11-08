"""Example 1 - generate a labelled data set in one shot (no GUI).

    python examples/01_headless_dataset.py
"""
from virtualbas.bas.historian import load_dataset
from virtualbas.core import VirtualBAS

scenario = {
    "start": "2023-07-10", "end": "2023-07-16", "seed": 1, "realism": 1.0,
    "occupancy": {"stochastic": True},
    "random_faults": {"rate_per_week": 3},
    "injections": [{"type": "sensor_drift", "target": "ZN-Core_mid/ZN-T", "start": "2023-07-11T00:00:00",
                    "params": {"rate_per_day": 0.5}}],
}
bas = VirtualBAS("buildings/large_office", out_dir="results/example1", scenario=scenario, speed="max")
print(bas.run()["kpi"])

data = load_dataset("results/example1")
obs, truth, labels = data["observed"], data["truth"], data["labels"]
err = obs["ZN-Core_mid/ZN-T"] - truth["ZN-Core_mid/ZN-T"]
print("sensor error (observed - truth) of the drifting thermostat, daily mean:")
print(err.resample("1D").mean().round(2))
print("injections (ground truth):")
for inj in data["injections_table"]:
    print(f"  {inj['id']} {inj['type']:<28} {inj['target']:<28} {inj['source']:<8} {inj['start']} -> {inj['end']}")
