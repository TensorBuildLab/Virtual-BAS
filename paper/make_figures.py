"""Generate all paper figures and result tables from the experiment outputs in results/.

    python paper/make_figures.py
"""
import datetime as dt
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments"))
from virtualbas.bas.historian import load_dataset  # noqa: E402

RES = ROOT / "results"
FIG = ROOT / "paper/figures"
TAB = ROOT / "paper/tables"
FIG.mkdir(parents=True, exist_ok=True)
TAB.mkdir(parents=True, exist_ok=True)

# validated categorical palette (fixed order) + neutrals
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#d9d8d4"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.edgecolor": INK2, "axes.labelcolor": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.5,
                     "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 1.4, "legend.frameon": False,
                     "savefig.dpi": 300, "savefig.bbox": "tight", "figure.dpi": 150})


def save(fig, name):
    fig.savefig(FIG / f"{name}.pdf")
    fig.savefig(FIG / f"{name}.png")
    plt.close(fig)
    print("figure", name)


# ----------------------------------------------------------------------------- Fig: architecture
def fig_architecture():
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    ax.set_axis_off()
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 50)

    def box(x, y, w, h, text, fc, ec, fs=7, bold=False):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2", fc=fc, ec=ec, lw=0.8))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=INK,
                weight="bold" if bold else "normal", wrap=True)

    def arrow(x1, y1, x2, y2, text="", color=INK2, rad=0.0, dy=1.2):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=8, color=color, lw=0.9,
                                     connectionstyle=f"arc3,rad={rad}"))
        if text:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2 + dy, text, ha="center", va="bottom", fontsize=6.3, color=INK2, style="italic")

    # inner space
    ax.add_patch(FancyBboxPatch((1, 2), 26, 46, boxstyle="round,pad=0.3,rounding_size=2", fc="#eef4fc", ec=C[0], lw=1.0))
    ax.text(14, 45.5, "INNER SPACE", ha="center", fontsize=8, weight="bold", color=C[0])
    ax.text(14, 42.6, "EnergyPlus physics (ground truth)", ha="center", fontsize=6.5, color=INK2)
    box(3.5, 30, 21, 9, "Zones & envelope\noccupants, gains, CO$_2$", "white", C[0])
    box(3.5, 17.5, 21, 9.5, "Air side: AHU (OA damper, coils,\nfan), VAV boxes + reheat", "white", C[0])
    box(3.5, 5, 21, 9.5, "Water side: chillers, tower,\nboiler, pumps (fault models)", "white", C[0])
    # outer space
    ax.add_patch(FancyBboxPatch((33, 2), 66, 46, boxstyle="round,pad=0.3,rounding_size=2", fc="#fdf3ec", ec=C[1], lw=1.0))
    ax.text(66, 45.5, "OUTER SPACE", ha="center", fontsize=8, weight="bold", color=C[1])
    ax.text(66, 42.6, "real world: labelled imperfection and randomness", ha="center", fontsize=6.5, color=INK2)
    box(36, 29, 18, 10, "Sensor models\n$y=(1+g)\\tilde x+b+d(t)+n$\nstuck, missing, spikes", "white", C[1], fs=6.3)
    box(59, 29, 17, 10, "BAS controllers\n(observed values only)\nVAV, AHU, plant", "white", C[1], fs=6.3)
    box(81, 29, 16, 10, "Overrides\npriority array\n(operator / AI)", "white", C[1], fs=6.3)
    box(36, 15, 18, 9.5, "Actuator models &\nlocal-loop emulation\n$x^*=(r-b)/(1+g)$", "white", C[1], fs=6.3)
    box(59, 15, 17, 9.5, "Real-world randomness\noccupancy, weather,\ngains, infiltration", "white", C[1], fs=6.3)
    box(81, 15, 16, 9.5, "Fault & event\ninjection (39 types)\n5 layers", "white", C[1], fs=6.3)
    box(36, 4, 61, 7, "Historian: observed | truth | commands | labels  -  GUI, REST/WebSocket, MCP, Gymnasium  -  speed 1x ... max",
        "#ffffff", INK2, fs=6.3)
    arrow(24.5, 34.5, 36, 34.5, "truth $x_k$")
    arrow(54, 34.5, 59, 34.5, "$y_k$", dy=0.8)
    arrow(81, 34, 76, 34, "")
    arrow(67, 29, 47, 24.5, "commands $u_k$", rad=0.0, dy=0.3)
    arrow(36, 19.5, 24.5, 22, "actuators", dy=0.6)
    arrow(59, 19.5, 24.5, 34, "", rad=0.25)
    arrow(89, 24.5, 89, 29, "")
    arrow(81, 18, 76, 18, "")
    ax.text(70, 26.4, "faults modify sensors, controllers,\nactuators and EnergyPlus physics", fontsize=5.8, color=INK2, ha="left")
    save(fig, "fig_architecture")


# ----------------------------------------------------------------------------- Fig: sensor model
def fig_sensor_model():
    from virtualbas.realworld.sensors import SENSOR_CLASSES, FaultOverlay, Sensor
    rng = np.random.default_rng(3)
    t = np.arange(0, 3 * 288) * 300 / 3600.0
    x = 22 + 2.0 * np.sin(2 * np.pi * (t - 9) / 24) + 0.3 * np.sin(2 * np.pi * t / 3.1)
    spec = SENSOR_CLASSES["zone_temperature"]
    cases = [("Typical sensor (bias, noise, lag, quantisation)", None),
             ("Drift fault (+1 K/day from day 1)", "drift"),
             ("Spikes + bursty missing data", "spk"),
             ("Stuck at day 1.5", "stuck")]
    fig, axs = plt.subplots(2, 2, figsize=(7.2, 3.8), sharex=True, sharey=True)
    for ax, (title, kind) in zip(axs.flat, cases):
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
        ax.plot(t / 24, x, color=INK2, lw=1.0, ls="--", label="truth $x_k$ (EnergyPlus)")
        ax.plot(t / 24, y, color=C[1], lw=0.9, label="observed $y_k$ (BAS)")
        ax.set_title(title, fontsize=7.5, loc="left", color=INK)
    for ax in axs[1]:
        ax.set_xlabel("time [day]")
    for ax in axs[:, 0]:
        ax.set_ylabel("zone temperature [°C]")
    axs[0, 0].legend(loc="lower left", fontsize=6.5)
    fig.tight_layout()
    save(fig, "fig_sensor_model")


# ----------------------------------------------------------------------------- Fig/table: validation
def fig_validation():
    from compare_native import METERS, compare, native_hourly
    exp = RES / "exp1_validation"
    r = compare(exp)
    r["energy"].round(2).to_csv(TAB / "validation_energy.csv", index=False)
    r["temps"].round(3).to_csv(TAB / "validation_temps.csv", index=False)
    nat = native_hourly(exp / "native" / "eplusout.csv", 2023)
    tr = load_dataset(exp / "vbas")["truth"]
    vb = tr.resample("1h", label="right", closed="right").mean()
    idx = nat.index.intersection(vb.index)
    fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.5), gridspec_kw={"width_ratios": [1.25, 1.25, 1]})
    for ax, (m, pid, lab) in zip(axs[:2], [("Electricity:Facility", "MTR/BLDG-ELEC-KW", "Electricity"),
                                          ("NaturalGas:Facility", "MTR/BLDG-GAS-KW", "Natural gas")]):
        col = next(c for c in nat.columns if c.startswith(m))
        n = (nat.loc[idx, col] / 3.6e9).groupby(idx.month).sum()
        v = (vb.loc[idx, pid] / 1000).groupby(idx.month).sum()
        w = 0.38
        ax.bar(n.index - w / 2, n.values, w, color=C[0], label="native EnergyPlus")
        ax.bar(v.index + w / 2, v.values, w, color=C[1], label="Virtual BAS (ideal sensors)")
        ax.set_xticks(range(1, 13))
        ax.set_xticklabels("JFMAMJJASOND")
        ax.set_ylabel(f"{lab} [MWh/month]")
        ax.set_title(lab, fontsize=8, loc="left")
    h, l = axs[0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper center", ncol=2, fontsize=7, bbox_to_anchor=(0.4, 1.06))
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
    ax.hexbin(xs, ys, gridsize=60, cmap="Blues", mincnt=1, bins="log", linewidths=0)
    ax.plot([12, 32], [12, 32], color=INK2, lw=0.8, ls="--")
    ax.set_xlim(12, 32)
    ax.set_ylim(12, 32)
    ax.set_xlabel("native zone temp. [°C]")
    ax.set_ylabel("Virtual BAS zone temp. [°C]")
    ax.set_title("16 zones, 8760 h", fontsize=8, loc="left")
    fig.tight_layout()
    save(fig, "fig_validation")
    return r


# ----------------------------------------------------------------------------- Fig: drift case study
def fig_drift():
    base = load_dataset(RES / "exp2_faults/summer/none")
    drift = load_dataset(RES / "exp2_faults/summer/ZN_T_drift__Core_mid___0_5_K_d_")
    z, v = "ZN-Core_mid", "VAV-Core_mid"
    fig, axs = plt.subplots(3, 1, figsize=(7.2, 4.6), sharex=True)
    ax = axs[0]
    ax.plot(drift["observed"].index, drift["observed"][f"{z}/ZN-T"], color=C[1], lw=0.8, label="observed by BAS (drifting sensor)")
    ax.plot(drift["truth"].index, drift["truth"][f"{z}/ZN-T"], color=C[0], lw=1.0, label="true zone temperature (EnergyPlus)")
    ax.plot(drift["commands"].index, drift["commands"][f"{z}/CLG-SP"], color=INK2, lw=0.8, ls="--", label="cooling set point")
    ax.set_ylabel("°C")
    ax.legend(fontsize=6.3, ncol=3, loc="lower left")
    ax.set_title("(a) Zone Core_mid: the BAS keeps the observed value at set point while the true temperature drops", fontsize=7.5, loc="left")
    ax = axs[1]
    ax.plot(base["truth"].index, base["truth"][f"{v}/DA-F"], color=INK2, lw=0.8, label="fault-free twin")
    ax.plot(drift["truth"].index, drift["truth"][f"{v}/DA-F"], color=C[1], lw=0.9, label="with drift")
    ax.set_ylabel("m³/s")
    ax.legend(fontsize=6.3, loc="upper left")
    ax.set_title("(b) VAV-Core_mid discharge air flow: wrong control signal sent to EnergyPlus", fontsize=7.5, loc="left")
    ax = axs[2]
    eb = base["truth"]["MTR/HVAC-ELEC-KW"].resample("1h").mean()
    ed = drift["truth"]["MTR/HVAC-ELEC-KW"].resample("1h").mean()
    ax.plot(eb.index, eb.values, color=INK2, lw=0.8, label="fault-free twin")
    ax.plot(ed.index, ed.values, color=C[1], lw=0.9, label="with drift")
    ax.set_ylabel("kW")
    ax.legend(fontsize=6.3, loc="upper left")
    ax.set_title("(c) HVAC electric demand (hourly mean)", fontsize=7.5, loc="left")
    for ax in axs:
        ax.margins(x=0)
    fig.autofmt_xdate()
    fig.tight_layout()
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
    piv = piv.sort_values(["lo"], kind="stable")
    labels = [f"{f}" for f in piv["fault"]]
    cols = [("d_elec_%", "summer"), ("d_elec_%", "winter"), ("d_gas_%", "summer"), ("d_gas_%", "winter"),
            ("d_comfort_Kh", "summer"), ("d_comfort_Kh", "winter")]
    titles = ["ΔElec.\nsummer [%]", "ΔElec.\nwinter [%]", "ΔGas\nsummer [%]", "ΔGas\nwinter [%]", "ΔDiscomfort\nsummer [K·h]", "ΔDiscomfort\nwinter [K·h]"]
    M = np.array([[piv[c].iloc[i] for c in cols] for i in range(len(piv))], dtype=float)
    fig, ax = plt.subplots(figsize=(7.2, 7.2))
    # diverging per-column scaling (signed log-like compression for readability)
    S = np.sign(M) * np.log10(1 + np.abs(M))
    vmax = np.nanmax(np.abs(S))
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("div", ["#2a78d6", "#f2f1ee", "#e34948"])
    ax.imshow(S, cmap=cmap, vmin=-vmax, vmax=vmax, aspect="auto")
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            val = M[i, j]
            ax.text(j, i, f"{val:+.1f}" if abs(val) < 100 else f"{val:+.0f}", ha="center", va="center", fontsize=6.2,
                    color=INK if abs(S[i, j]) < 0.6 * vmax else "white")
    ax.set_xticks(range(len(titles)))
    ax.set_xticklabels(titles, fontsize=6.5)
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=6.5)
    ax.grid(False)
    prev = None
    for i, lay in enumerate(piv["layer"]):
        if lay != prev:
            ax.axhline(i - 0.5, color="white", lw=2)
            ax.text(-0.6 - 0.02, i - 0.45, lay.upper(), transform=ax.transData, ha="right", va="top", fontsize=6, color=C[6],
                    weight="bold", clip_on=False) if False else None
            prev = lay
    fig.tight_layout()
    save(fig, "fig_fault_matrix")
    return d


# ----------------------------------------------------------------------------- Fig: occupancy
def fig_occupancy():
    d = load_dataset(RES / "exp2_faults/summer/none")
    occ = d["truth"]["ZN-Core_mid/OCCUPANTS"]
    fig, ax = plt.subplots(figsize=(7.2, 1.9))
    ax.plot(occ.index, occ.values, color=C[0], lw=0.8, label="stochastic occupants (Markov chain, truth)")
    o2 = d["observed"]["ZN-Core_mid/ZN-OCC"] * occ.max() * 1.05
    ax.fill_between(o2.index, 0, o2.values, color=C[2], alpha=0.15, lw=0, label="PIR occupancy sensor = 1")
    ax.set_ylabel("people (Core_mid)")
    ax.legend(fontsize=6.3, ncol=2, loc="upper right")
    ax.margins(x=0)
    fig.autofmt_xdate()
    fig.tight_layout()
    save(fig, "fig_occupancy")


# ----------------------------------------------------------------------------- Fig: FDD
def fig_fdd():
    r = json.loads((RES / "exp3_fdd/fdd_results.json").read_text())
    rep = r["diagnosis"]["report"]
    classes = [k for k in rep if k not in ("accuracy", "macro avg", "weighted avg")]
    f1 = [rep[k]["f1-score"] for k in classes]
    sup = [rep[k]["support"] for k in classes]
    o = np.argsort(f1)
    fig, ax = plt.subplots(figsize=(3.5, 2.6))
    ax.barh(range(len(classes)), np.array(f1)[o], color=C[0], height=0.6)
    ax.set_yticks(range(len(classes)))
    ax.set_yticklabels([f"{classes[i]} (n={int(sup[i])})" for i in o], fontsize=6.2)
    ax.set_xlabel("F1 score (test period)")
    ax.set_xlim(0, 1)
    ax.set_title(f"AHU diagnosis, macro-F1 = {r['diagnosis']['macro_f1']:.2f}\n(detection macro-F1 = {r['detection']['macro_f1']:.2f})",
                 fontsize=7.5, loc="left")
    fig.tight_layout()
    save(fig, "fig_fdd")
    return r


# ----------------------------------------------------------------------------- Fig: speed
def fig_speed():
    s = json.loads((RES / "exp4_speed/speed.json").read_text())
    pts = [x for x in s if x["target"] != "max"]
    fig, ax = plt.subplots(figsize=(3.5, 2.4))
    tg = [float(x["target"]) for x in pts]
    ac = [x["achieved_factor"] for x in pts]
    ax.loglog(tg, tg, color=INK2, ls="--", lw=0.8, label="target")
    ax.loglog(tg, ac, "o", color=C[0], ms=5, label="achieved")
    mx = [x for x in s if x["target"] == "max"][0]
    ax.axhline(mx["achieved_factor"], color=C[1], lw=1.0)
    ax.text(tg[0], mx["achieved_factor"] * 0.55, f"max speed: {mx['achieved_factor']:,.0f}× real time ({mx['ms_per_step']:.1f} ms/step)",
            fontsize=6.3, color=INK)
    ax.set_xlabel("target speed factor [-]")
    ax.set_ylabel("achieved speed factor [-]")
    ax.legend(fontsize=6.3, loc="upper left")
    fig.tight_layout()
    save(fig, "fig_speed")
    return s


# ----------------------------------------------------------------------------- Fig: AI agents
def fig_ai():
    b = json.loads((RES / "exp6_ai/partB.json").read_text())
    df = pd.DataFrame([{"season": r["season"], "case": r["case"], "agent": r["agent"], "elec": r["kpi"]["elec_kwh"] / 1000,
                        "gas": r["kpi"]["gas_kwh"] / 1000, "comfort": r["kpi"]["comfort_kh"]} for r in b])
    df.to_csv(TAB / "ai_partB.csv", index=False)
    cases = ["ideal", "realistic", "oat_bias"]
    names = ["ideal sensors", "realistic sensors", "realistic +\nOA-T bias"]
    names = [n.replace(" sensors", "\nsensors") for n in names]
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.5))
    for ax, (metric, lab) in zip(axs, [("elec", "electricity saving of AI agent [%]"), ("gas", "gas increase of AI agent [MWh]")]):
        w = 0.36
        for j, season in enumerate(["shoulder", "summer"]):
            d = df[df.season == season]
            vals = []
            for c in cases:
                a_ = float(d[(d.case == c) & (d.agent)][metric].iloc[0])
                n_ = float(d[(d.case == c) & (~d.agent)][metric].iloc[0])
                vals.append((n_ - a_) / n_ * 100 if metric == "elec" else a_ - n_)
            x = np.arange(3) + (j - 0.5) * w
            ax.bar(x, vals, w * 0.92, color=C[j], label=f"{season} (2 weeks)")
            for xi, v in zip(x, vals):
                ax.text(xi, v, f"{v:.1f}", ha="center", va="bottom" if v >= 0 else "top", fontsize=6.3, color=INK)
        ax.axhline(0, color=INK2, lw=0.6)
        ax.set_xticks(range(3))
        ax.set_xticklabels(names, fontsize=6.8)
        ax.set_ylabel(lab)
    axs[0].legend(fontsize=6.5, loc="upper right")
    fig.tight_layout()
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
    M["SpeedErr"] = f"{max(abs(x['error_%']) for x in s if x['target'] != 'max'):.2f}"
    # ---- generality
    g = json.loads((RES / "exp5_generality/generality.json").read_text())
    hosp = [x for x in g if "Hospital" in x["model"]][0]
    M["NumHospitalPts"] = hosp["n_points"]
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
              fig_speed, fig_ai, tables_misc, latex_outputs]:
        try:
            f()
        except Exception as e:  # noqa: BLE001
            print("FAILED", f.__name__, repr(e))
