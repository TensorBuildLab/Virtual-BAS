"""Experiment 7 - Extended environment: wildfire smoke, filtration and the visibility of IEQ in today's BAS.

A five-day summer week with a 30-hour wildfire-smoke episode (+120 ug/m3 outdoor PM2.5) is simulated
for three AHU filter situations: MERV 8 (reference model), MERV 13, and MERV 8 with a filter-bypass fault
(60 % bypass on all AHUs, no pressure-drop symptom). The run also records a complete IEQ day profile of
a perimeter zone (illuminance, sound, TVOC, PMV, votes) and the point counts per tier, i.e. what a
standard BAS of today would see.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

ZONE = "ZN-Perimeter_mid_ZN_1"
SMOKE = {"type": "wildfire_smoke", "start": "2023-07-12T06:00:00", "duration": "30h", "params": {"pm25_add": 120.0}}
CASES = {
    "MERV 8": {"environment": {"filter_merv": 8}, "injections": [SMOKE]},
    "MERV 13": {"environment": {"filter_merv": 13}, "injections": [SMOKE]},
    "MERV 8 + bypass fault": {"environment": {"filter_merv": 8}, "injections": [SMOKE] + [
        {"type": "filter_bypass", "target": f"AHU-{i}", "start": "2023-07-10T00:00:00", "params": {"bypass": 0.6}}
        for i in range(1, 5)]},
    # an IEQ-aware sequence that sees the (next-generation) outdoor PM2.5 sensor locks the economizer out
    "MERV 8 + smoke economizer lock-out": {"environment": {"filter_merv": 8}, "injections": [SMOKE] + [
        {"type": "economizer_disabled", "target": f"AHU-{i}", "start": SMOKE["start"], "duration": SMOKE["duration"],
         "source": "ai", "note": "outdoor PM2.5 > 35 ug/m3"} for i in range(1, 5)]},
}
SERIES = ["WX/OA-PM25", f"{ZONE}/ZN-PM25", f"{ZONE}/ZN-PM10", f"{ZONE}/ZN-TVOC", f"{ZONE}/ZN-LUX", f"{ZONE}/DAYLIGHT-LUX",
          f"{ZONE}/ZN-DBA", f"{ZONE}/PMV", f"{ZONE}/PPD", f"{ZONE}/TS-VOTE", f"{ZONE}/OCCUPANTS", f"{ZONE}/ZN-CO2",
          f"{ZONE}/ZN-T", "GRID/PRICE", "GRID/CO2-INT", "AHU-3/OA-FRAC"]


def run_case(name, extra):
    from virtualbas.core import VirtualBAS
    sc = {"start": "2023-07-10", "end": "2023-07-14", "seed": 11, **extra}
    v = VirtualBAS(ROOT / "buildings/large_office", scenario=sc, record=False)
    rows = []
    zones = [e.id for e in v.cat.equipment_of_type("Zone")]

    def hook(b, t):
        if b.warmup:
            return
        tr, pv = b.truth, b.pv
        occ = [z for z in zones if (tr.get(f"{z}/OCCUPANTS") or 0) > 0]
        mean_in = sum(tr[f"{z}/ZN-PM25"] for z in zones) / len(zones)
        rows.append({"time": t.isoformat(), **{k: tr.get(k) for k in SERIES},
                     **{f"obs:{k}": pv.get(k) for k in SERIES if k in v.sensors},
                     "mean_in_pm25": mean_in,
                     "occ_zone_over_35": sum(1 for z in occ if tr[f"{z}/ZN-PM25"] > 35.0),
                     "occ_zone_over_15": sum(1 for z in occ if tr[f"{z}/ZN-PM25"] > 15.0)})
    v.step_hooks.append(hook)
    r = v.run()
    return {"kpi": r["kpi"], "rows": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "results/exp7_environment"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    res = {}
    for name, extra in CASES.items():
        r = run_case(name, extra)
        rows = r["rows"]
        h = 1.0 / 12.0
        res[name] = {"kpi": r["kpi"], "elec_kwh": r["kpi"]["elec_kwh"],
                     "peak_in_pm25": max(x["mean_in_pm25"] for x in rows),
                     "occ_zone_hours_over_35": sum(x["occ_zone_over_35"] for x in rows) * h,
                     "occ_zone_hours_over_15": sum(x["occ_zone_over_15"] for x in rows) * h,
                     "peak_out_pm25": max(x["WX/OA-PM25"] for x in rows)}
        (out / f"series_{name.replace(' ', '_').replace('+', 'plus')}.json").write_text(json.dumps(rows))
        print(name, json.dumps({k: v for k, v in res[name].items() if k != "kpi"}))
    from collections import Counter
    from virtualbas.core import Building
    cat = Building(ROOT / "buildings/large_office").catalog
    res["tiers"] = dict(Counter(p.tier for p in cat.points.values()))
    res["tiers_by_group"] = {}
    for p in cat.points.values():
        g = "IEQ" if p.equip_type == "Zone" else ("Weather/grid/meters" if p.equip_type in ("WeatherStation", "Grid", "Meter", "Building")
                                                  else "Equipment")
        d = res["tiers_by_group"].setdefault(g, {})
        d[p.tier] = d.get(p.tier, 0) + 1
    (out / "summary.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
