"""Experiment 3 - Labelled dataset generation and an AHU fault detection & diagnosis benchmark.

Two independent multi-week runs (train / test: different seeds and periods) are generated with
the random fault generator restricted to AHU-level faults. Hourly features are computed from
*observed* BAS trend data only and a random-forest detector is trained on the ground-truth labels.
This demonstrates that Virtual BAS produces ML-ready, correctly labelled data.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

AHUS = ["AHU-1", "AHU-2", "AHU-3", "AHU-4"]
AHU_MENU = {
    "sensor_bias": {"targets": "sensor:AHU:degC", "params": {"bias": ("choice", [-2.5, -1.5, 1.5, 2.5])}, "hours": (24, 96)},
    "sensor_drift": {"targets": "sensor:AHU:degC", "params": {"rate_per_day": ("choice", [-0.8, -0.5, 0.5, 0.8])}, "hours": (48, 120)},
    "sensor_stuck": {"targets": "sensor:AHU:degC", "params": {}, "hours": (24, 72)},
    "oa_damper_stuck": {"targets": "equip:AHU", "params": {"position": ("choice", [0, 100])}, "hours": (24, 96)},
    "cooling_coil_valve_stuck_closed": {"targets": "equip:AHU", "params": {}, "hours": (12, 48)},
    "filter_fouling": {"targets": "equip:AHU", "params": {"dp_add": ("uniform", 150, 350)}, "hours": (48, 120)},
    "fan_degradation": {"targets": "equip:AHU", "params": {"loss": ("uniform", 0.2, 0.4)}, "hours": (48, 120)},
    "economizer_disabled": {"targets": "equip:AHU", "params": {}, "hours": (48, 120)},
    "schedule_error_always_on": {"targets": "equip:AHU", "params": {}, "hours": (24, 72)},
}
RUNS = {"train": ("2023-04-03", "2023-06-25", 101), "test": ("2023-07-03", "2023-08-27", 202)}


def generate(name, out_root, rate):
    from virtualbas.core import VirtualBAS
    from virtualbas.realworld.random_faults import RandomInjector
    start, end, seed = RUNS[name]
    sc = {"start": start, "end": end, "seed": seed, "realism": 1.0, "occupancy": {"stochastic": True}}
    v = VirtualBAS(ROOT / "buildings/large_office", out_dir=Path(out_root) / name, scenario=sc, speed="max")
    v.random = RandomInjector(rate_per_week=rate, menu=AHU_MENU, seed=seed)
    return v.run()


def features(d) -> pd.DataFrame:
    o, c = d["observed"], d["commands"]
    rows = []
    for a in AHUS:
        def g(k):
            return o[f"{a}/{k}"]

        def h(k):
            return c[f"{a}/{k}"]
        f = pd.DataFrame(index=o.index)
        oat = o["WX/OA-T"]
        frac = (g("OAD-POS") / 100.0).clip(0, 1)
        f["sat_err"] = g("SA-T") - h("SA-T-SP")
        f["mat"] = g("MA-T")
        f["rat"] = g("RA-T")
        f["oat"] = oat
        f["mat_minus_oat"] = g("MA-T") - oat
        f["rat_minus_mat"] = g("RA-T") - g("MA-T")
        f["oad_cmd"] = h("OAD-CMD")
        f["oad_pos"] = g("OAD-POS")
        f["oad_dev"] = g("OAD-POS") - h("OAD-CMD")
        f["mix_resid"] = g("MA-T") - (frac * oat + (1 - frac) * g("RA-T"))
        f["ccv"] = g("CCV-POS")
        f["hcv"] = g("HCV-POS")
        f["fan_kw_per_flow"] = g("SF-KW") / g("SA-F").clip(lower=0.5)
        f["flt_dp"] = g("FLT-DP")
        f["fan_spd"] = g("SF-SPD")
        f["fan_on"] = (h("SF-CMD") > 0.5).astype(float)
        f["fan_sts"] = g("SF-STS")
        f["occ_mode"] = h("OCC-MODE")
        f["econ_en"] = h("ECON-EN")
        f["sat_minus_cclat"] = g("SA-T") - g("CC-LAT")
        f["oa_flow"] = g("OA-F")
        f["sa_flow"] = g("SA-F")
        f["hour"] = o.index.hour
        f["weekday"] = (o.index.weekday < 5).astype(float)
        hourly = f.resample("1h").agg(["mean", "std"])
        hourly.columns = [f"{x}_{y}" for x, y in hourly.columns]
        hourly["ahu"] = a
        rows.append(hourly)
    return pd.concat(rows)


def labels(d, idx) -> dict[str, pd.Series]:
    inj = pd.DataFrame(d.get("injections_table", []))
    sev = d.get("injections")
    lab = {}
    for a in AHUS:
        y = pd.Series("normal", index=idx, dtype=object)
        if sev is not None and len(inj):
            for _, r in inj[inj["target"].astype(str).str.startswith(a)].iterrows():
                s = sev[(sev["injection_id"] == r["id"]) & (sev["severity"] > 0)]
                if len(s):
                    hrs = s["time"].dt.floor("1h").value_counts()
                    hrs = hrs[hrs >= 6].index   # active at least half of the hour
                    y.loc[y.index.intersection(hrs)] = r["type"]
        lab[a] = y
    return lab


def build_xy(d) -> pd.DataFrame:
    X = features(d)
    lab = labels(d, X.index.unique())
    parts = []
    for a in AHUS:
        xa = X[X["ahu"] == a].copy()
        xa["label"] = lab[a].reindex(xa.index).values
        parts.append(xa)
    return pd.concat(parts).dropna(subset=["fan_on_mean"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "results/exp3_fdd"))
    ap.add_argument("--rate", type=float, default=3.0)
    ap.add_argument("--skip-generate", action="store_true")
    a = ap.parse_args()
    if not a.skip_generate:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=2) as ex:
            futs = {n: ex.submit(generate, n, a.out, a.rate) for n in RUNS}
            for n, f in futs.items():
                print(n, json.dumps(f.result()["kpi"]))
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import classification_report, confusion_matrix, f1_score
    from virtualbas.bas.historian import load_dataset
    tr = build_xy(load_dataset(Path(a.out) / "train"))
    te = build_xy(load_dataset(Path(a.out) / "test"))
    feats = [c for c in tr.columns if c not in ("ahu", "label")]
    med = tr[feats].median()
    tr[feats] = tr[feats].fillna(med)
    te[feats] = te[feats].fillna(med)
    out = {}
    for task in ["detection", "diagnosis"]:
        ytr = tr["label"] if task == "diagnosis" else (tr["label"] != "normal").astype(int)
        yte = te["label"] if task == "diagnosis" else (te["label"] != "normal").astype(int)
        clf = RandomForestClassifier(n_estimators=400, min_samples_leaf=2, class_weight="balanced", random_state=0, n_jobs=-1)
        clf.fit(tr[feats], ytr)
        p = clf.predict(te[feats])
        rep = classification_report(yte, p, output_dict=True, zero_division=0)
        out[task] = {"macro_f1": float(f1_score(yte, p, average="macro")), "report": rep,
                     "labels": sorted(set(yte) | set(p), key=str),
                     "confusion": confusion_matrix(yte, p, labels=sorted(set(yte) | set(p), key=str)).tolist()}
        if task == "detection":
            out["top_features"] = sorted(zip(feats, map(float, clf.feature_importances_)), key=lambda x: -x[1])[:12]
        print(task, "macro-F1", round(out[task]["macro_f1"], 3))
    out["label_counts_train"] = tr["label"].value_counts().to_dict()
    out["label_counts_test"] = te["label"].value_counts().to_dict()
    Path(a.out).mkdir(parents=True, exist_ok=True)
    (Path(a.out) / "fdd_results.json").write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps({k: out[k] for k in ("label_counts_train", "label_counts_test")}, indent=1))


if __name__ == "__main__":
    main()
