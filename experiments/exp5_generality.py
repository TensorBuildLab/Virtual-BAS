"""Experiment 5 - Generality: automatic BAS-ization of different DOE reference buildings.

Each model is converted without building-specific code (topology discovery, command binding,
fault hooks, point catalog) and simulated for one week with realistic sensors.
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

MODELS = ["RefBldgLargeOfficeNew2004_Chicago", "RefBldgMediumOfficeNew2004_Chicago", "RefBldgSmallOfficeNew2004_Chicago",
          "RefBldgHospitalNew2004_Chicago", "RefBldgSecondarySchoolNew2004_Chicago"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "results/exp5_generality"))
    a = ap.parse_args()
    from virtualbas import eplus
    from virtualbas.bas.catalog import build_catalog
    from virtualbas.core import VirtualBAS
    from virtualbas.model.prepare import PrepareOptions, prepare_model
    out = Path(a.out)
    rows = []
    for m in MODELS:
        t = time.time()
        bdir = out / "buildings" / m
        _, man = prepare_model(eplus.example_file(m + ".idf"), eplus.weather_file("USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw"),
                               bdir, PrepareOptions(timesteps_per_hour=12))
        t_prep = time.time() - t
        cat = build_catalog(man)
        topo = man.topo
        eq = {}
        for e in cat.equipment.values():
            eq[e.type] = eq.get(e.type, 0) + 1
        t = time.time()
        v = VirtualBAS(bdir, out_dir=None, scenario={"start": "2023-07-10", "end": "2023-07-16", "seed": 1}, speed="max")
        r = v.run()
        t_run = time.time() - t
        row = {"model": m, "zones": len(topo.zones), "conditioned_zones": len(topo.conditioned_zones()),
               "vav_terminals": len(topo.terminals), "air_loops": len(topo.air_loops),
               "plant_loops": len([p for p in topo.plant_loops.values() if p.kind != "other"]),
               "equipment": eq, "points": cat.summary(), "n_points": len(cat.points),
               "commands": len(man.commands), "fault_hooks": len(man.faults), "prepare_s": t_prep,
               "week_run_s": t_run, "steps": r["steps"], "steps_per_s": r["steps"] / t_run,
               "exit_code": r["exit_code"], "missing_handles": len(r["missing"]),
               "unmet_occ_zone_hours": r["kpi"]["unmet_occ_hours"]}
        rows.append(row)
        print(json.dumps(row))
    out.mkdir(parents=True, exist_ok=True)
    (out / "generality.json").write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
