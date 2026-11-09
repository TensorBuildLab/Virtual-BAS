"""Compare native EnergyPlus results with a EmuBAS run (energy by end use and zone temperatures)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from virtualbas.bas.historian import load_dataset  # noqa: E402

METERS = {"Electricity:Facility": "MTR/BLDG-ELEC-KW", "NaturalGas:Facility": "MTR/BLDG-GAS-KW",
          "Cooling:Electricity": "MTR/CLG-ELEC-KW", "Fans:Electricity": "MTR/FAN-ELEC-KW", "Pumps:Electricity": "MTR/PUMP-ELEC-KW",
          "HeatRejection:Electricity": "MTR/HREJ-ELEC-KW", "Heating:NaturalGas": "MTR/HTG-GAS-KW",
          "InteriorLights:Electricity": "MTR/LIGHT-KW", "InteriorEquipment:Electricity": "MTR/PLUG-KW"}


def native_hourly(csv: Path, year: int) -> pd.DataFrame:
    df = pd.read_csv(csv)
    ts = df["Date/Time"].str.strip()
    md = ts.str.slice(0, 5)
    hh = ts.str.slice(7, 9).astype(int)
    idx = pd.to_datetime(f"{year}/" + md, format="%Y/%m/%d") + pd.to_timedelta(hh, unit="h")
    df.index = idx
    df = df.drop(columns=["Date/Time"])
    return df[~df.index.duplicated(keep="last")]  # drop HVAC-sizing design-day rows


def compare(exp_dir: Path, year: int = 2023) -> dict:
    nat = native_hourly(exp_dir / "native" / "eplusout.csv", year)
    d = load_dataset(exp_dir / "vbas")
    tr = d["truth"]
    # VBAS samples are time-stamped at the END of each step interval -> hourly sums end at the hour
    vb_h = tr.resample("1h", label="right", closed="right").mean()
    rows = []
    for m, pid in METERS.items():
        col = next((c for c in nat.columns if c.startswith(m)), None)
        if col is None or pid not in vb_h:
            continue
        n_kwh = nat[col] / 3.6e6
        v_kwh = vb_h[pid].reindex(n_kwh.index)  # kW mean over the hour = kWh
        ok = v_kwh.notna()
        N, V = n_kwh[ok], v_kwh[ok]
        tot_n, tot_v = N.sum(), V.sum()
        cv = np.sqrt(((V - N) ** 2).mean()) / N.mean() * 100 if N.mean() > 0 else np.nan
        nmbe = (V - N).sum() / (len(N) * N.mean()) * 100 if N.mean() > 0 else np.nan
        rows.append({"meter": m, "native_MWh": tot_n / 1000, "vbas_MWh": tot_v / 1000,
                     "diff_%": (tot_v - tot_n) / tot_n * 100 if tot_n else np.nan, "NMBE_%": nmbe, "CVRMSE_%": cv})
    energy = pd.DataFrame(rows)
    zt = []
    for c in nat.columns:
        if "Zone Air Temperature" not in c:
            continue
        zone = c.split(":")[0]
        pid = next((p for p in tr.columns if p.endswith("/ZN-T") and p.split("/")[0][3:].upper() == zone.upper()), None)
        if pid is None:
            continue
        v = tr[pid].resample("1h", label="right", closed="right").mean().reindex(nat.index)
        ok = v.notna()
        diff = v[ok] - nat[c][ok]
        zt.append({"zone": zone, "MAE_K": diff.abs().mean(), "RMSE_K": np.sqrt((diff ** 2).mean()), "bias_K": diff.mean()})
    temps = pd.DataFrame(zt)
    return {"energy": energy, "temps": temps}


if __name__ == "__main__":
    r = compare(Path(sys.argv[1]))
    pd.set_option("display.width", 200)
    print(r["energy"].round(2).to_string())
    print(r["temps"].round(3).to_string())
    print("mean zone MAE", r["temps"]["MAE_K"].mean().round(3))
