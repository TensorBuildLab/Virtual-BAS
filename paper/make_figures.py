"""Generate all paper figures and result tables from the experiment outputs in results/.

    python paper/make_figures.py
"""
import datetime as dt
import json
import sys
from pathlib import Path

import matplotlib.dates as mdates  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments"))
sys.path.insert(0, str(ROOT / "paper"))
from figstyle import (AI, C, ENV, FAULT, FULL_W, INK, INK2, INNER, MUTED, OUTER, panel,  # noqa: E402,F401
                      plt, save)
from virtualbas.bas.historian import load_dataset  # noqa: E402

RES = ROOT / "results"
TAB = ROOT / "paper/tables"
TAB.mkdir(parents=True, exist_ok=True)
# The architecture and other conceptual diagrams are HTML/SVG files in paper/diagrams/ (tools/render_html.py);
# model and data figures beyond the experiments are in paper/make_figures_extra.py.


def legend_above(ax, ncol=3, **kw):
    """Frameless legend in the band between the panel title and the plot area (never on the data).
    The panel title (set before) is lifted above the legend rows."""
    n = len(ax.get_legend_handles_labels()[0])
    rows = -(-n // ncol)
    fs = kw.get("fontsize", plt.rcParams["legend.fontsize"])
    leg = ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=ncol, borderaxespad=0.15, handlelength=1.8,
                    columnspacing=1.4, labelspacing=0.3, **kw)
    title = ax.get_title(loc="left")
    if title:
        ax.set_title(title, loc="left", pad=3 + rows * (fs * 1.45))
    return leg


def day_ticks(ax, fmt="%a %d"):
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter(fmt))
    ax.tick_params(axis="x", labelrotation=0)


# ----------------------------------------------------------------------------- Fig: sensor model
def fig_sensor_model():
    from virtualbas.realworld.sensors import SENSOR_CLASSES, FaultOverlay, Sensor
    t = np.arange(0, 3 * 288) * 300 / 3600.0
    x = 22 + 2.0 * np.sin(2 * np.pi * (t - 9) / 24) + 0.3 * np.sin(2 * np.pi * t / 3.1)
    spec = SENSOR_CLASSES["zone_temperature"]
    cases = [("typical sensor", None),
             ("drift fault, +1 K/d", "drift"),
             ("spikes, missing data", "spk"),
             ("stuck sensor", "stuck")]
    fig, axs = plt.subplots(2, 2, figsize=(FULL_W, 3.5), sharex=True, sharey=True)
    for i, (ax, (title, kind)) in enumerate(zip(axs.flat, cases)):
        s = Sensor("demo", spec, np.random.default_rng(7), realism=1.0)
        s.bias = 0.25
        y = []
        for k, xv in enumerate(x):
            ov = FaultOverlay()
            if kind == "drift" and t[k] >= 24:
                ov.bias = (t[k] - 24) / 24.0
            if kind == "spk":
                ov.spike_prob, ov.spike_std, ov.p_gb = 0.03, 2.0, 0.02
            if kind == "stuck" and t[k] >= 36:
                ov.stuck = True
            y.append(s.measure(float(xv), 300, ov)[0])
        ax.plot(t / 24, x, color=INNER, lw=1.6, label="truth $x_k$ (EnergyPlus)")
        ax.plot(t / 24, y, color=OUTER, lw=0.8, label="observed $y_k$ (BAS)")
        if kind in ("drift", "stuck"):
            ax.axvline(1.0 if kind == "drift" else 1.5, color=FAULT, lw=0.8, ls=":")
            ax.text(1.0 if kind == "drift" else 1.5, 28.3, " fault onset", color=INK2, fontsize=7, va="top")
        panel(ax, "abcd"[i], title)
        ax.set_xlim(0, 3)
    for ax in axs[1]:
        ax.set_xlabel("time [d]")
    for ax in axs[:, 0]:
        ax.set_ylabel("zone temperature [°C]")
    h, lab = axs[0, 0].get_legend_handles_labels()
    fig.legend(h, lab, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.045))
    fig.tight_layout(h_pad=1.2)
    save(fig, "fig_sensor_model")


# ----------------------------------------------------------------------------- Fig/table: validation
def fig_validation():
    from compare_native import compare, native_hourly
    exp = RES / "exp1_validation"
    r = compare(exp)
    r["energy"].round(2).to_csv(TAB / "validation_energy.csv", index=False)
    r["temps"].round(3).to_csv(TAB / "validation_temps.csv", index=False)
    nat = native_hourly(exp / "native" / "eplusout.csv", 2023)
    tr = load_dataset(exp / "vbas")["truth"]
    vb = tr.resample("1h", label="right", closed="right").mean()
    idx = nat.index.intersection(vb.index)
    fig, axs = plt.subplots(1, 3, figsize=(FULL_W, 2.25), gridspec_kw={"width_ratios": [1.2, 1.2, 1]})
    for i, (ax, (m, pid, lab)) in enumerate(zip(axs[:2], [("Electricity:Facility", "MTR/BLDG-ELEC-KW", "electricity"),
                                                         ("NaturalGas:Facility", "MTR/BLDG-GAS-KW", "natural gas")])):
        col = next(c for c in nat.columns if c.startswith(m))
        n = (nat.loc[idx, col] / 3.6e9).groupby(idx.month).sum()
        v = (vb.loc[idx, pid] / 1000).groupby(idx.month).sum()
        w = 0.4
        ax.bar(n.index - w / 2, n.values, w * 0.95, color=INNER, label="native EnergyPlus")
        ax.bar(v.index + w / 2, v.values, w * 0.95, color=OUTER, label="Virtual BAS, ideal sensors")
        ax.set_xticks(range(1, 13))
        ax.set_xticklabels("JFMAMJJASOND")
        ax.set_ylabel("MWh per month")
        ax.grid(axis="x", visible=False)
        panel(ax, "ab"[i], f"monthly {lab}")
    ax = axs[2]
    xs, ys = [], []
    for c in nat.columns:
        if "Zone Air Temperature" not in c:
            continue
        zone = c.split(":")[0]
        pid = next((p for p in tr.columns if p.endswith("/ZN-T") and p.split("/")[0][3:].upper() == zone.upper()), None)
        if pid:
            xs.append(nat.loc[idx, c].values)
            ys.append(vb.loc[idx, pid].values)
    xs, ys = np.concatenate(xs), np.concatenate(ys)
    ax.hexbin(xs, ys, gridsize=55, cmap="Blues", mincnt=1, bins="log", linewidths=0)
    ax.plot([12, 32], [12, 32], color=INK2, lw=0.7, ls="--")
    ax.set_xlim(12, 32)
    ax.set_ylim(12, 32)
    ax.set_aspect("equal")
    ax.set_xlabel("native [°C]")
    ax.set_ylabel("Virtual BAS [°C]")
    mae = np.nanmean(np.abs(xs - ys))
    ax.text(31.5, 13, f"MAE {mae:.2f} K", ha="right", va="bottom", fontsize=7.5, color=INK)
    panel(ax, "c", "hourly zone temperature")
    h, lab = axs[0].get_legend_handles_labels()
    fig.legend(h, lab, loc="upper center", ncol=2, bbox_to_anchor=(0.42, 1.08))
    fig.tight_layout(w_pad=1.0)
    save(fig, "fig_validation")
    return r


# ----------------------------------------------------------------------------- Fig: drift case study
def fig_drift():
    base = load_dataset(RES / "exp2_faults/summer/none")
    drift = load_dataset(RES / "exp2_faults/summer/ZN_T_drift__Core_mid___0_5_K_d_")
    z, v = "ZN-Core_mid", "VAV-Core_mid"
    fig, axs = plt.subplots(3, 1, figsize=(FULL_W, 4.9), sharex=True, gridspec_kw={"height_ratios": [1.35, 1, 1]})
    ax = axs[0]
    ax.plot(drift["commands"].index, drift["commands"][f"{z}/CLG-SP"], color=INK2, lw=0.8, ls="--", label="cooling set point")
    ax.plot(drift["observed"].index, drift["observed"][f"{z}/ZN-T"], color=OUTER, lw=0.8, label="observed by BAS (drifting sensor)")
    ax.plot(drift["truth"].index, drift["truth"][f"{z}/ZN-T"], color=INNER, lw=1.1, label="truth (EnergyPlus)")
    ax.set_ylabel("°C")
    panel(ax, "a", "zone Core_mid: the BAS holds the reading at set point while the true zone cools")
    legend_above(ax, ncol=3)
    ax = axs[1]
    ax.plot(base["truth"].index, base["truth"][f"{v}/DA-F"], color=MUTED, lw=0.8, label="fault-free twin")
    ax.plot(drift["truth"].index, drift["truth"][f"{v}/DA-F"], color=OUTER, lw=0.9, label="with sensor drift")
    ax.set_ylabel("m³/s")
    panel(ax, "b", "VAV-Core_mid discharge air flow: the wrong command reaches EnergyPlus")
    legend_above(ax, ncol=2)
    ax = axs[2]
    eb = base["truth"]["MTR/HVAC-ELEC-KW"].resample("1h").mean()
    ed = drift["truth"]["MTR/HVAC-ELEC-KW"].resample("1h").mean()
    ax.plot(eb.index, eb.values, color=MUTED, lw=0.8, label="fault-free twin")
    ax.plot(ed.index, ed.values, color=OUTER, lw=0.9, label="with sensor drift")
    ax.set_ylabel("kW")
    panel(ax, "c", "HVAC electric demand, hourly mean")
    legend_above(ax, ncol=2)
    for ax in axs:
        ax.margins(x=0)
    day_ticks(axs[-1], "%a %d Jul")
    fig.tight_layout(h_pad=0.6)
    save(fig, "fig_drift_case")


# ----------------------------------------------------------------------------- Fig/table: fault matrix
def fig_fault_matrix():
    res = json.loads((RES / "exp2_faults/results.json").read_text())
    df = pd.DataFrame([{"fault": r["fault"], "layer": r["layer"], "season": r["season"], **r["kpi"], "alarms": r["alarms"]} for r in res])
    rows = []
    for season in ["summer", "winter"]:
        b = df[(df.season == season) & (df.fault == "none")].iloc[0]
        for _, r in df[(df.season == season) & (df.fault != "none")].iterrows():
            rows.append({"fault": r.fault, "layer": r.layer, "season": season,
                         "d_elec_%": (r.elec_kwh - b.elec_kwh) / b.elec_kwh * 100,
                         "d_gas_%": (r.gas_kwh - b.gas_kwh) / b.gas_kwh * 100,
                         "d_comfort_Kh": r.comfort_kh - b.comfort_kh,
                         "alarms": r.alarms - b.alarms})
    d = pd.DataFrame(rows)
    d.round(2).to_csv(TAB / "fault_matrix.csv", index=False)
    piv = d.pivot_table(index=["layer", "fault"], columns="season", values=["d_elec_%", "d_gas_%", "d_comfort_Kh"], sort=False)
    order = ["sensor", "actuator", "equipment", "control", "network", "event"]
    piv = piv.reset_index()
    piv["lo"] = piv["layer"].map({k: i for i, k in enumerate(order)})
    piv = piv.sort_values(["lo"], kind="stable").reset_index(drop=True)
    labels = list(piv["fault"])
    cols = [("d_elec_%", "summer"), ("d_elec_%", "winter"), ("d_gas_%", "summer"), ("d_gas_%", "winter"),
            ("d_comfort_Kh", "summer"), ("d_comfort_Kh", "winter")]
    M = np.array([[piv[c].iloc[i] for c in cols] for i in range(len(piv))], dtype=float)
    S = np.sign(M) * np.log10(1 + np.abs(M))
    vmax = np.nanmax(np.abs(S))
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("div", [INNER, "#f2f1ee", FAULT])
    n = len(labels)
    fig, ax = plt.subplots(figsize=(FULL_W, 0.19 * n + 1.0))
    ax.imshow(S, cmap=cmap, vmin=-vmax, vmax=vmax, aspect="auto")
    for i in range(n):
        for j in range(M.shape[1]):
            val = M[i, j]
            if np.isnan(val):
                continue
            txt = "0.0" if abs(val) < 0.05 else (f"{val:+.1f}" if abs(val) < 100 else f"{val:+.0f}")
            ax.text(j, i, txt, ha="center", va="center", fontsize=6.6,
                    color=INK if abs(S[i, j]) < 0.6 * vmax else "white")
    ax.set_xticks(range(6))
    ax.set_xticklabels(["summer", "winter"] * 3, fontsize=7)
    ax.xaxis.tick_top()
    ax.tick_params(axis="both", length=0)
    for j, t in enumerate(["Δ electricity [%]", "Δ natural gas [%]", "Δ discomfort [K·h]"]):
        ax.text(2 * j + 0.5, -1.55, t, ha="center", va="bottom", fontsize=7.5, fontweight="bold", color=INK)
    ax.set_yticks(range(n))
    ax.set_yticklabels(labels, fontsize=7)
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    for j in (1.5, 3.5):
        ax.axvline(j, color="white", lw=3)
    prev = None
    for i, lay in enumerate(piv["layer"]):
        if lay != prev:
            if i:
                ax.axhline(i - 0.5, color="white", lw=3)
            ax.annotate(lay, xy=(1.0, i - 0.5), xycoords=("axes fraction", "data"), xytext=(4, -2),
                        textcoords="offset points", ha="left", va="top", fontsize=7, color=INK2, style="italic")
            prev = lay
    ax.text(0, n - 0.1, "colour: signed log scale; blue = decrease, red = increase vs. fault-free run",
            ha="left", va="top", fontsize=6.8, color=INK2, transform=ax.transData)
    fig.tight_layout()
    save(fig, "fig_fault_matrix")
    return d


# ----------------------------------------------------------------------------- Fig: occupancy
def fig_occupancy():
    d = load_dataset(RES / "exp2_faults/summer/none")
    occ = d["truth"]["ZN-Core_mid/OCCUPANTS"]
    fig, ax = plt.subplots(figsize=(FULL_W, 1.75))
    o2 = d["observed"]["ZN-Core_mid/ZN-OCC"].fillna(0) * occ.max() * 1.05
    ax.fill_between(o2.index, 0, o2.values, color=ENV, alpha=0.18, lw=0, step="post", label="PIR occupancy sensor on")
    ax.plot(occ.index, occ.values, color=INNER, lw=0.8, label="occupants, Markov chain (truth)")
    ax.set_ylabel("people")
    ax.margins(x=0)
    ax.set_ylim(0, None)
    panel(ax, "", "")
    ax.set_title("")
    legend_above(ax, ncol=2)
    day_ticks(ax, "%a %d Jul")
    fig.tight_layout()
    save(fig, "fig_occupancy")


# ----------------------------------------------------------------------------- Fig: FDD
def fig_fdd():
    r = json.loads((RES / "exp3_fdd/fdd_results.json").read_text())
    rep = r["diagnosis"]["report"]
    classes = [k for k in rep if k not in ("accuracy", "macro avg", "weighted avg")]
    f1 = np.array([rep[k]["f1-score"] for k in classes])
    sup = [rep[k]["support"] for k in classes]
    o = np.argsort(f1)
    fig, ax = plt.subplots(figsize=(3.9, 0.22 * len(classes) + 0.7))
    ax.barh(range(len(classes)), f1[o], color=INNER, height=0.62)
    for i, k in enumerate(o):
        ax.text(f1[k] + 0.015, i, f"{f1[k]:.2f}", va="center", fontsize=7, color=INK)
    ax.set_yticks(range(len(classes)))
    ax.set_yticklabels([f"{classes[i]} (n={int(sup[i])})" for i in o], fontsize=7)
    ax.set_xlabel("F1 score, test period")
    ax.set_xlim(0, 1.08)
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", length=0)
    ax.set_title(f"AHU diagnosis: macro-F1 {r['diagnosis']['macro_f1']:.2f}; detection: macro-F1 {r['detection']['macro_f1']:.2f}",
                 fontsize=8, loc="left")
    fig.tight_layout()
    save(fig, "fig_fdd")
    return r


# ----------------------------------------------------------------------------- Fig: speed
def fig_speed():
    s = json.loads((RES / "exp4_speed/speed.json").read_text())
    pts = [x for x in s if x["target"] != "max"]
    fig, ax = plt.subplots(figsize=(3.6, 2.4))
    tg = [float(x["target"]) for x in pts]
    ac = [x["achieved_factor"] for x in pts]
    mx = [x for x in s if x["target"] == "max"][0]
    ax.axhline(mx["achieved_factor"], color=OUTER, lw=1.0)
    ax.text(tg[0], mx["achieved_factor"] * 1.25, f"as fast as possible: {mx['achieved_factor']:,.0f}× ({mx['ms_per_step']:.1f} ms/step)",
            fontsize=7, color=INK)
    ax.loglog(tg, tg, color=INK2, ls="--", lw=0.8, label="target")
    ax.loglog(tg, ac, "o", color=INNER, ms=5, mec="white", mew=0.8, label="achieved")
    ax.set_xlabel("target speed factor")
    ax.set_ylabel("achieved speed factor")
    ax.set_ylim(0.5, mx["achieved_factor"] * 4)
    ax.legend(loc="center right")
    fig.tight_layout()
    save(fig, "fig_speed")
    return s


# ----------------------------------------------------------------------------- Fig: extended environment
EXP7_CASES = ["MERV 8", "MERV 13", "MERV 8 + bypass fault", "MERV 8 + smoke economizer lock-out"]


def _exp7_series(name):
    f = RES / "exp7_environment" / f"series_{name.replace(' ', '_').replace('+', 'plus')}.json"
    d = pd.DataFrame(json.loads(f.read_text()))
    d["time"] = pd.to_datetime(d["time"])
    return d.set_index("time")


def fig_environment():
    zone = "ZN-Perimeter_mid_ZN_1"
    fig = plt.figure(figsize=(FULL_W, 5.6))
    gs = fig.add_gridspec(3, 2, height_ratios=[1.3, 1, 1], hspace=0.75, wspace=0.32)
    ax = fig.add_subplot(gs[0, :])
    base = _exp7_series(EXP7_CASES[0])
    ax.plot(base.index, base["WX/OA-PM25"], color=INK2, lw=1.0, label="outdoor")
    for i, n in enumerate(EXP7_CASES):
        d = _exp7_series(n)
        lab = n.replace("smoke economizer lock-out", "economizer lock-out").replace("bypass fault", "filter bypass fault")
        ax.plot(d.index, d["mean_in_pm25"], color=C[i], lw=1.2, label=f"indoor, {lab}")
    ax.axhline(35, color=FAULT, lw=0.7, ls=":")
    ax.text(base.index[-1], 36, "35 µg/m³ (24-h guideline)", fontsize=7, color=INK2, ha="right", va="bottom")
    ax.set_ylabel("PM2.5 [µg/m³]")
    ax.set_ylim(0, 175)
    ax.margins(x=0)
    day_ticks(ax, "%a %d Jul")
    panel(ax, "a", "wildfire-smoke episode: outdoor and mean indoor PM2.5")
    legend_above(ax, ncol=3)
    day = base.loc["2023-07-10 05:00":"2023-07-10 21:00"]
    hrs = day.index.hour + day.index.minute / 60
    ax = fig.add_subplot(gs[1, 0])
    ax.plot(hrs, day[f"{zone}/ZN-LUX"], color=C[3], label="work plane (truth)")
    ax.plot(hrs, day[f"{zone}/DAYLIGHT-LUX"], color=C[3], ls="--", lw=1.0, label="daylight share")
    ax.plot(hrs, day[f"obs:{zone}/ZN-LUX"], color=INK2, lw=0.6, label="photosensor")
    ax.set_ylabel("illuminance [lx]")
    panel(ax, "b", "light")
    legend_above(ax, ncol=2, fontsize=6.8)
    ax = fig.add_subplot(gs[1, 1])
    ax.axhspan(-0.5, 0.5, color=ENV, alpha=0.10, lw=0)
    ax.plot(hrs, day[f"{zone}/PMV"], color=INNER, label="PMV (truth)")
    v = day[f"{zone}/TS-VOTE"].astype(float)
    v = v[v.diff().fillna(1) != 0].dropna()          # one marker per new hourly vote
    ax.plot(v.index.hour + v.index.minute / 60, v.values, "o", color=OUTER, ms=3.5, mec="white", mew=0.6,
            label="mean occupant vote, hourly")
    ax.set_ylim(-2.2, 2.2)
    ax.set_ylabel("thermal sensation [-]")
    panel(ax, "c", "comfort and occupant feedback")
    legend_above(ax, ncol=2, fontsize=6.8)
    ax = fig.add_subplot(gs[2, 0])
    ax.plot(hrs, day[f"{zone}/ZN-TVOC"], color=AI, label="TVOC (truth)")
    ax.plot(hrs, day[f"obs:{zone}/ZN-TVOC"], color=INK2, lw=0.6, label="MOx sensor")
    ax.set_ylabel("TVOC [µg/m³]")
    ax.set_ylim(0, 260)
    ax.set_xlabel("hour of day, Monday")
    panel(ax, "d", "volatile organic compounds")
    legend_above(ax, ncol=2, fontsize=6.8)
    ax = fig.add_subplot(gs[2, 1])
    ax.plot(hrs, day[f"{zone}/ZN-DBA"], color=C[4], label="sound level (truth)")
    ax.plot(hrs, day[f"obs:{zone}/ZN-DBA"], color=INK2, lw=0.6, label="sound meter")
    ax.set_ylabel("sound [dBA]")
    ax.set_ylim(20, 55)
    ax.set_xlabel("hour of day, Monday")
    panel(ax, "e", "sound")
    legend_above(ax, ncol=2, fontsize=6.8)
    for a in fig.axes[1:]:
        a.set_xlim(5, 21)
        a.set_xticks([6, 9, 12, 15, 18, 21])
    save(fig, "fig_environment")


# ----------------------------------------------------------------------------- Fig: AI agents
def fig_ai():
    b = json.loads((RES / "exp6_ai/partB.json").read_text())
    df = pd.DataFrame([{"season": r["season"], "case": r["case"], "agent": r["agent"], "elec": r["kpi"]["elec_kwh"] / 1000,
                        "gas": r["kpi"]["gas_kwh"] / 1000, "comfort": r["kpi"]["comfort_kh"]} for r in b])
    df.to_csv(TAB / "ai_partB.csv", index=False)
    cases = ["ideal", "realistic", "oat_bias"]
    names = ["ideal\nsensors", "realistic\nsensors", "realistic +\nOA-T bias"]
    fig, axs = plt.subplots(1, 2, figsize=(FULL_W, 2.3))
    for k, (ax, (metric, lab)) in enumerate(zip(axs, [("elec", "electricity saving [%]"), ("gas", "gas increase [MWh]")])):
        w = 0.36
        for j, season in enumerate(["shoulder", "summer"]):
            d = df[df.season == season]
            vals = []
            for c in cases:
                a_ = float(d[(d.case == c) & (d.agent)][metric].iloc[0])
                n_ = float(d[(d.case == c) & (~d.agent)][metric].iloc[0])
                vals.append((n_ - a_) / n_ * 100 if metric == "elec" else a_ - n_)
            x = np.arange(3) + (j - 0.5) * w
            ax.bar(x, vals, w * 0.92, color=[INNER, C[3]][j], label=f"{season} season, 2 weeks")
            for xi, v in zip(x, vals):
                ax.text(xi, v, f"{v:.1f}", ha="center", va="bottom" if v >= 0 else "top", fontsize=7, color=INK)
        ax.axhline(0, color=INK2, lw=0.6)
        ax.set_xticks(range(3))
        ax.set_xticklabels(names, fontsize=7.5)
        ax.set_ylabel(lab)
        ax.grid(axis="x", visible=False)
        ax.margins(y=0.15)
        panel(ax, "ab"[k], "AI agent vs. baseline: " + ("electricity" if metric == "elec" else "natural gas"))
    h, lab = axs[0].get_legend_handles_labels()
    fig.legend(h, lab, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.08))
    fig.tight_layout(w_pad=2)
    save(fig, "fig_ai_agent")
    return df


def tables_misc():
    g = json.loads((RES / "exp5_generality/generality.json").read_text())
    pd.DataFrame([{"model": x["model"].replace("RefBldg", "").replace("New2004_Chicago", ""), "zones": x["conditioned_zones"],
                   "VAV": x["vav_terminals"], "air loops": x["air_loops"], "points": x["n_points"],
                   "equipment": sum(x["equipment"].values()), "commands": x["commands"], "fault hooks": x["fault_hooks"],
                   "prepare [s]": round(x["prepare_s"], 1), "steps/s": round(x["steps_per_s"]), "exit": x["exit_code"]} for x in g]
                 ).to_csv(TAB / "generality.csv", index=False)


def latex_outputs():
    """Write paper/results_macros.tex and LaTeX tables from the experiment results."""
    from virtualbas.core import Building
    from virtualbas.realworld.faults import REGISTRY
    M = {}
    cat = Building(ROOT / "buildings/large_office").catalog
    M["NumFaultTypes"] = len(REGISTRY)
    M["NumPoints"] = len(cat.points)
    M["NumEquip"] = len(cat.equipment)
    M["NumSensorPts"] = sum(p.kind in ("sensor", "meter") for p in cat.points.values())
    M["NumSoftPts"] = sum(p.kind in ("setpoint", "command", "virtual", "status") for p in cat.points.values())
    M["NumTruthPts"] = sum(p.kind == "truth" for p in cat.points.values())
    for key, tier in (("NumStdPts", "standard"), ("NumAdvPts", "advanced"), ("NumNextPts", "next_gen")):
        M[key] = sum(p.tier == tier for p in cat.points.values())
    M["NumModelPts"] = sum(p.source in ("model", "surrogate") for p in cat.points.values())
    M["NumStdPct"] = f"{100 * M['NumStdPts'] / M['NumPoints']:.0f}"
    M["NumBasSrcPts"] = sum(p.source == "bas" for p in cat.points.values())
    M["NumCalcPts"] = sum(p.source == "bas" and p.kind == "virtual" for p in cat.points.values())
    M["NumZonePts"] = len(cat.points_of(next(e.id for e in cat.equipment.values() if e.id == "ZN-Perimeter_mid_ZN_1")))
    M["NumWxPts"] = len(cat.points_of("WX"))
    # ---- validation
    e = pd.read_csv(TAB / "validation_energy.csv").set_index("meter")
    t = pd.read_csv(TAB / "validation_temps.csv")
    M["ValElecDiff"] = f"{e.loc['Electricity:Facility', 'diff_%']:+.1f}"
    M["ValElecDiffAbs"] = f"{abs(e.loc['Electricity:Facility', 'diff_%']):.1f}"
    M["ValElecCV"] = f"{e.loc['Electricity:Facility', 'CVRMSE_%']:.1f}"
    M["ValGasDiff"] = f"{e.loc['NaturalGas:Facility', 'diff_%']:.1f}"
    M["ValGasDiffAbs"] = f"{abs(e.loc['NaturalGas:Facility', 'diff_%']):.1f}"
    M["ValClgDiffAbs"] = f"{abs(e.loc['Cooling:Electricity', 'diff_%']):.1f}"
    M["ValFanDiffAbs"] = f"{abs(e.loc['Fans:Electricity', 'diff_%']):.1f}"
    M["ValZoneMAE"] = f"{t['MAE_K'].mean():.2f}"
    s1 = json.loads((RES / "exp1_validation/summary.json").read_text())
    M["ValWallVBAS"] = f"{s1['wall_vbas_s']:.0f}"
    M["ValWallVBASmin"] = f"{s1['wall_vbas_s'] / 60:.1f}"
    M["ValWallNative"] = f"{s1['wall_native_s']:.0f}"
    M["ValStepsPerSec"] = f"{105120 / s1['wall_vbas_s']:.0f}"
    names = {"Electricity:Facility": "Electricity, total", "NaturalGas:Facility": "Natural gas, total",
             "Cooling:Electricity": "Cooling (chillers)", "Fans:Electricity": "Fans", "Pumps:Electricity": "Pumps",
             "HeatRejection:Electricity": "Heat rejection", "Heating:NaturalGas": "Heating (boiler)",
             "InteriorLights:Electricity": "Interior lighting", "InteriorEquipment:Electricity": "Interior equipment"}
    rows = [r"\begin{tabular}{lrrrr}", r"\toprule",
            r"End use & Native [MWh] & Virtual BAS [MWh] & Diff. [\%] & CV(RMSE)$_h$ [\%] \\", r"\midrule"]
    for m, r in e.iterrows():
        rows.append(f"{names.get(m, m)} & {r['native_MWh']:,.0f} & {r['vbas_MWh']:,.0f} & {r['diff_%']:+.1f} & {r['CVRMSE_%']:.1f} " + r"\\")
    rows += [r"\midrule",
             f"Zone temp. MAE / RMSE [K] & \\multicolumn{{4}}{{l}}{{{t['MAE_K'].mean():.3f} / {t['RMSE_K'].mean():.3f} (mean of 16 zones)}} " + r"\\",
             r"\bottomrule", r"\end{tabular}"]
    (TAB / "validation_energy.tex").write_text("\n".join(rows))
    # ---- drift case
    base = load_dataset(RES / "exp2_faults/summer/none")
    drift = load_dataset(RES / "exp2_faults/summer/ZN_T_drift__Core_mid___0_5_K_d_")
    err = drift["observed"]["ZN-Core_mid/ZN-T"] - drift["truth"]["ZN-Core_mid/ZN-T"]
    M["DriftErr"] = f"{err.iloc[-288:].mean():.1f}"
    occ_b = base["commands"]["ZN-Core_mid/OCC-MODE"] > 0.5
    occ_d = drift["commands"]["ZN-Core_mid/OCC-MODE"] > 0.5
    fb = base["truth"]["VAV-Core_mid/DA-F"][occ_b].mean()
    fd = drift["truth"]["VAV-Core_mid/DA-F"][occ_d].mean()
    M["DriftFlow"] = f"{(fd / fb - 1) * 100:.0f}"
    hb, hd = base["truth"]["MTR/HVAC-ELEC-KW"].mean(), drift["truth"]["MTR/HVAC-ELEC-KW"].mean()
    M["DriftHVAC"] = f"{(hd / hb - 1) * 100:.1f}"
    # ---- fault matrix
    d = pd.read_csv(TAB / "fault_matrix.csv")

    def fm(name, season, col):
        r = d[(d.fault == name) & (d.season == season)]
        return float(r[col].iloc[0]) if len(r) else float("nan")
    res = json.loads((RES / "exp2_faults/results.json").read_text())
    gas_none_s = [r for r in res if r["fault"] == "none" and r["season"] == "summer"][0]["kpi"]["gas_kwh"]
    gas_leak_s = [r for r in res if r["fault"].startswith("Reheat valve leaking") and r["season"] == "summer"][0]["kpi"]["gas_kwh"]
    M["FMoaGasW"] = f"{fm('OA damper stuck 100% (AHU-2)', 'winter', 'd_gas_%'):.0f}"
    M["FMleakGasS"] = f"{gas_leak_s / gas_none_s:.0f}"
    M["FMleakComfS"] = f"{fm('Reheat valve leaking (Perim_mid_1)', 'summer', 'd_comfort_Kh'):.0f}"
    M["FMchwComfS"] = f"{fm('CHW valve stuck closed (AHU-1)', 'summer', 'd_comfort_Kh'):.0f}"
    M["FMrhComfW"] = f"{fm('Reheat valve stuck closed (Perim_mid_1)', 'winter', 'd_comfort_Kh'):.0f}"
    M["FMchFoulS"] = f"{fm('Chiller fouling (CH-1, r=0.6)', 'summer', 'd_elec_%'):.1f}"
    M["FMtwFoulS"] = f"{fm('Tower fouling (r=0.5)', 'summer', 'd_elec_%'):.1f}"
    M["FMblFoulW"] = f"{fm('Boiler fouling (r=0.6)', 'winter', 'd_gas_%'):.0f}"
    M["FMschedS"] = f"{fm('Schedule 24/7 (AHU-2)', 'summer', 'd_elec_%'):.1f}"
    # ---- FDD
    r = json.loads((RES / "exp3_fdd/fdd_results.json").read_text())
    M["FddDetF"] = f"{r['detection']['macro_f1']:.2f}"
    M["FddDiagF"] = f"{r['diagnosis']['macro_f1']:.2f}"
    M["FddTrainN"] = f"{sum(r['label_counts_train'].values()):,}".replace(",", "{,}")
    M["FddTestN"] = f"{sum(r['label_counts_test'].values()):,}".replace(",", "{,}")
    # ---- AI agents
    a = json.loads((RES / "exp6_ai/partA_log.json").read_text())
    M["AiInj"] = len(a["injections"])
    bb = pd.read_csv(TAB / "ai_partB.csv")

    def pick(season, case):
        x = bb[(bb.season == season) & (bb.case == case)]
        return x[~x.agent].iloc[0], x[x.agent].iloc[0]
    for key, case in [("Ideal", "ideal"), ("Real", "realistic"), ("Bias", "oat_bias")]:
        n, g = pick("shoulder", case)
        M[f"AiSh{key}"] = f"{(n.elec - g.elec) / n.elec * 100:.1f}"
        M[f"AiShGas{key}"] = f"{g.gas - n.gas:.0f}"
        M[f"AiShSite{key}"] = f"{((g.elec + g.gas) - (n.elec + n.gas)) / (n.elec + n.gas) * 100:+.1f}"
        n, g = pick("summer", case)
        M[f"AiSu{key}"] = f"{(n.elec - g.elec) / n.elec * 100:.1f}"
    # ---- speed
    s = json.loads((RES / "exp4_speed/speed.json").read_text())
    mx = [x for x in s if x["target"] == "max"][0]
    M["SpeedMs"] = f"{mx['ms_per_step']:.1f}"
    M["SpeedMaxK"] = f"{int(round(mx['achieved_factor'], -3)):,}".replace(",", "{,}")
    err = max(abs(x['error_%']) for x in s if x['target'] != 'max')
    M["SpeedErr"] = f"{max(err, 0.01):.2f}"           # an upper bound; never print 0.00
    # ---- generality
    g = json.loads((RES / "exp5_generality/generality.json").read_text())
    hosp = [x for x in g if "Hospital" in x["model"]][0]
    M["NumHospitalPts"] = hosp["n_points"]
    # ---- extended environment (exp7)
    e7 = json.loads((RES / "exp7_environment/summary.json").read_text())
    M["EnvPeakOut"] = f"{e7['MERV 8']['peak_out_pm25']:.0f}"
    for key, case in (("Eight", "MERV 8"), ("Thirteen", "MERV 13"), ("Bypass", "MERV 8 + bypass fault"),
                      ("Lock", "MERV 8 + smoke economizer lock-out")):
        M[f"EnvPeak{key}"] = f"{e7[case]['peak_in_pm25']:.0f}"
        M[f"EnvHrs{key}"] = f"{e7[case]['occ_zone_hours_over_35']:.0f}"
    from virtualbas.realworld.sensors import SENSOR_CLASSES
    M["NumSensorClasses"] = len(SENSOR_CLASSES) - 1
    M["HospitalSps"] = f"{hosp['steps_per_s']:.0f}"
    rows = [r"\begin{tabular}{lrrrrrrr}", r"\toprule",
            r"Building & Zones & VAV & AHUs & Plant loops & Equipment & Points & Samples/s \\", r"\midrule"]
    pretty = {"LargeOffice": "Large office", "MediumOffice": "Medium office", "SmallOffice": "Small office",
              "Hospital": "Hospital", "SecondarySchool": "Secondary school"}
    for x in g:
        nm = x["model"].replace("RefBldg", "").replace("New2004_Chicago", "")
        rows.append(f"{pretty.get(nm, nm)} & {x['conditioned_zones']} & {x['vav_terminals']} & {x['air_loops']} & "
                    f"{x['plant_loops']} & {sum(x['equipment'].values())} & {x['n_points']} & {x['steps_per_s']:.0f} " + r"\\")
    rows += [r"\bottomrule", r"\end{tabular}"]
    (TAB / "generality.tex").write_text("\n".join(rows))
    (ROOT / "paper/results_macros.tex").write_text("\n".join(f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in M.items()) + "\n")
    print("macros", M)


if __name__ == "__main__":
    for f in [fig_sensor_model, fig_validation, fig_drift, fig_fault_matrix, fig_occupancy, fig_fdd,
              fig_speed, fig_ai, fig_environment, tables_misc, latex_outputs]:
        try:
            f()
        except Exception as e:  # noqa: BLE001
            print("FAILED", f.__name__, repr(e))
