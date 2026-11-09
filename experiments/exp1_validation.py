"""Experiment 1 - Verification of the BAS-ization methodology.

Compares (a) the *native* EnergyPlus DOE large office (original controls, run as a batch
simulation) with (b) EmuBAS driving the same model step by step with ideal sensors,
deterministic occupancy and the 'baseline' control profile (BAS sequences re-implementing
the native controls). Agreement demonstrates that the inner/outer coupling does not distort
the physics.
"""
import argparse
import copy
import json
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from virtualbas import eplus  # noqa: E402
from virtualbas.core import VirtualBAS  # noqa: E402
from virtualbas.model.epjson import load_model, save_model  # noqa: E402


def run_native(building: Path, out: Path, start: str, end: str) -> pd.DataFrame:
    man = json.loads((building / "manifest.json").read_text())
    model = load_model(man["source_model"])
    ts = man["options"]["timesteps_per_hour"]
    y = man["options"]["year"]
    model["Timestep"] = {"Timestep 1": {"number_of_timesteps_per_hour": ts}}
    for sc in model["SimulationControl"].values():
        sc.update({"run_simulation_for_sizing_periods": "No", "run_simulation_for_weather_file_run_periods": "Yes"})
    rp_old = next(iter(model["RunPeriod"].values()))
    rp = {k: v for k, v in rp_old.items() if k.startswith("use_") or k.startswith("apply_")}
    s, e = pd.Timestamp(start), pd.Timestamp(end)
    rp.update({"begin_month": s.month, "begin_day_of_month": s.day, "begin_year": y, "end_month": e.month,
               "end_day_of_month": e.day, "end_year": y})
    model["RunPeriod"] = {"RP": rp}
    for t in ["Output:Variable", "Output:Meter", "Output:Meter:MeterFileOnly", "Output:Table:Monthly", "Output:SQLite"]:
        model.pop(t, None)
    meters = ["Electricity:Facility", "NaturalGas:Facility", "Electricity:HVAC", "Cooling:Electricity", "Fans:Electricity",
              "Pumps:Electricity", "HeatRejection:Electricity", "Heating:NaturalGas", "InteriorLights:Electricity",
              "InteriorEquipment:Electricity"]
    model["Output:Meter"] = {f"m{i}": {"key_name": m, "reporting_frequency": "Hourly"} for i, m in enumerate(meters)}
    model["Output:Variable"] = {"v1": {"key_value": "*", "variable_name": "Zone Air Temperature", "reporting_frequency": "Hourly"},
                                "v2": {"key_value": "*", "variable_name": "Heating Coil Heating Rate", "reporting_frequency": "Hourly"},
                                "v3": {"key_value": "*", "variable_name": "Cooling Coil Total Cooling Rate", "reporting_frequency": "Hourly"},
                                "v4": {"key_value": "*", "variable_name": "Air System Outdoor Air Mass Flow Rate", "reporting_frequency": "Hourly"},
                                "v5": {"key_value": "*", "variable_name": "Fan Air Mass Flow Rate", "reporting_frequency": "Hourly"},
                                "v6": {"key_value": "*", "variable_name": "Boiler Heating Rate", "reporting_frequency": "Hourly"}}
    out.mkdir(parents=True, exist_ok=True)
    p = save_model(model, out / "native.epJSON")
    subprocess.run([str(eplus.energyplus_exe()), "-w", str(building / "weather.epw"), "-d", str(out), "-r", str(p)],
                   check=True, capture_output=True)
    df = pd.read_csv(out / "eplusout.csv")
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--building", default=str(ROOT / "buildings/large_office"))
    ap.add_argument("--start", default="2023-01-01")
    ap.add_argument("--end", default="2023-12-31")
    ap.add_argument("--out", default=str(ROOT / "results/exp1_validation"))
    a = ap.parse_args()
    out = Path(a.out)
    t0 = time.time()
    native = run_native(Path(a.building), out / "native", a.start, a.end)
    t_native = time.time() - t0
    sc = {"start": a.start, "end": a.end, "seed": 0, "realism": 0.0, "occupancy": {"stochastic": False},
          "control": {"profile": "baseline"}}
    v = VirtualBAS(a.building, out_dir=out / "vbas", scenario=sc, speed="max")
    t1 = time.time()
    res = v.run()
    t_vbas = time.time() - t1
    res["wall_native_s"] = t_native
    res["wall_vbas_s"] = t_vbas
    (out / "summary.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main()
