"""Additional data/model figures for EmuBAS paper (model, points, faults, labels, forecasts, maps, generality).

Usage:
    python paper/make_figures_extra.py              # all figures
    python paper/make_figures_extra.py points       # one figure (building_model, points, fault_library, labels,
                                                    #   forecast_grid, zone_maps, generality)
    python paper/make_figures_extra.py sim_zone_maps   # (re)run the two wildfire-smoke simulations for zone_maps

All figures are designed at their printed size (FULL_W = 5.4 in) and use paper/figstyle.py.
"""
import datetime as dt
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figstyle import *  # noqa: E402,F401,F403
from figstyle import C, INNER, OUTER, ENV, AI, FAULT, INK, INK2, MUTED, GRID, TIER, TIER_LABEL, FULL_W, ROOT, \
    save, panel, date_axis  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle, Polygon as MplPolygon  # noqa: E402

sys.path.insert(0, str(ROOT))

BLD = ROOT / "buildings/large_office"
OUT_MAPS = ROOT / "results/fig_zone_maps"


# ============================================================================= simulations (fig_zone_maps)
SMOKE = {"type": "wildfire_smoke", "start": "2023-07-12T06:00:00", "duration": "30h", "params": {"pm25_add": 120.0}}
MAP_CASES = {"MERV 8": {"environment": {"filter_merv": 8}, "injections": [SMOKE]},
             "MERV 13": {"environment": {"filter_merv": 13}, "injections": [SMOKE]}}


def sim_zone_maps():
    """Run the Experiment-6 smoke week (same scenario and seed as experiments/exp7_environment.py) for MERV 8 and
    MERV 13 and store the truth PM2.5 of every zone at every BAS sample in results/fig_zone_maps/."""
    from virtualbas.core import VirtualBAS
    OUT_MAPS.mkdir(parents=True, exist_ok=True)
    for name, extra in MAP_CASES.items():
        sc = {"start": "2023-07-11", "end": "2023-07-14", "seed": 11, **extra}
        v = VirtualBAS(BLD, scenario=sc, record=False)
        zones = [e.id for e in v.cat.equipment_of_type("Zone")]
        rows = []

        def hook(b, t):
            if b.warmup:
                return
            tr = b.truth
            rows.append({"time": t.isoformat(), "OA-PM25": tr.get("WX/OA-PM25"),
                         **{z: tr.get(f"{z}/ZN-PM25") for z in zones},
                         **{f"{z}|OCC": tr.get(f"{z}/OCCUPANTS") for z in zones},
                         **{f"AHU-{i}|OAF": tr.get(f"AHU-{i}/OA-FRAC") for i in range(1, 5)}})
        v.step_hooks.append(hook)
        t0 = dt.datetime.now()
        v.run()
        fn = OUT_MAPS / f"pm25_{name.replace(' ', '')}.json"
        fn.write_text(json.dumps({"scenario": sc, "zones": zones, "rows": rows}))
        print("sim", name, len(rows), "samples", (dt.datetime.now() - t0).total_seconds(), "s ->", fn)


# ============================================================================= helpers
def mix(c, w):
    """Blend a colour with white (w = 0 -> colour, 1 -> white)."""
    from matplotlib.colors import to_rgb
    r = np.array(to_rgb(c))
    return tuple(r + (1 - r) * w)


def shade(c, f):
    from matplotlib.colors import to_rgb
    return tuple(np.clip(np.array(to_rgb(c)) * f, 0, 1))


# AHU identity (categorical, fixed order; avoids OUTER orange / FAULT red / AI purple which carry paper semantics)
AHU_COL = {"AHU-1": C[0], "AHU-2": C[3], "AHU-3": C[4], "AHU-4": C[2]}
AHU_OF_LOOP = {"VAV_1": "AHU-1", "VAV_2": "AHU-2", "VAV_3": "AHU-3", "VAV_5": "AHU-4"}
GLASS = "#dfeaf3"
PLENUM = "#cfcdc6"
LAYER_COL = {"sensor": C[0], "actuator": C[3], "equipment": FAULT, "control": AI, "network": MUTED,
             "occupancy": C[4], "weather": ENV, "gains": C[5], "iaq": "#7a6f5a", "grid": INK2}


def _newell(V):
    n = np.zeros(3)
    for i in range(len(V)):
        a, b = V[i], V[(i + 1) % len(V)]
        n += [(a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])]
    L = np.linalg.norm(n)
    return n / L if L > 0 else n


def load_geometry(path):
    """Surfaces and windows of an epJSON model in absolute coordinates (zone origins added; GlobalGeometryRules
    'Relative' coordinates, all reference models have zero relative-north rotation)."""
    m = json.loads(Path(path).read_text())
    zones = m.get("Zone", {})
    rel = list(m.get("GlobalGeometryRules", {"x": {"coordinate_system": "Relative"}}).values())[0] \
        .get("coordinate_system", "Relative").lower() == "relative"

    def org(z):
        v = zones.get(z, {})
        if not rel:
            return np.zeros(3)
        assert float(v.get("direction_of_relative_north", 0) or 0) == 0.0
        return np.array([float(v.get(k, 0) or 0) for k in ("x_origin", "y_origin", "z_origin")])

    surfs = []
    for name, s in m.get("BuildingSurface:Detailed", {}).items():
        V = np.array([[p["vertex_x_coordinate"], p["vertex_y_coordinate"], p["vertex_z_coordinate"]]
                      for p in s["vertices"]], float) + org(s["zone_name"])
        surfs.append({"name": name, "zone": s["zone_name"], "type": s["surface_type"],
                      "bc": s["outside_boundary_condition"], "V": V, "n": _newell(V),
                      "selfref": s["outside_boundary_condition"] in ("Surface", "Adiabatic")
                      and s.get("outside_boundary_condition_object", name) == name})
    base = {s["name"]: s for s in surfs}
    wins = []
    for name, f in m.get("FenestrationSurface:Detailed", {}).items():
        V = []
        for i in range(1, 5):
            k = f"vertex_{i}_x_coordinate"
            if k in f:
                V.append([f[k], f[f"vertex_{i}_y_coordinate"], f[f"vertex_{i}_z_coordinate"]])
        b = base.get(f["building_surface_name"])
        if b is None or len(V) < 3:
            continue
        V = np.array(V, float) + org(b["zone"])
        wins.append({"zone": b["zone"], "V": V, "n": b["n"], "type": f.get("surface_type", "Window")})
    shades = []
    for name, s in m.get("Shading:Building:Detailed", {}).items():
        V = np.array([[p["vertex_x_coordinate"], p["vertex_y_coordinate"], p["vertex_z_coordinate"]]
                      for p in s["vertices"]], float)
        shades.append({"V": V, "n": _newell(V)})
    mult = {z: int(v.get("multiplier", 1) or 1) for z, v in zones.items()}
    return {"surfs": surfs, "wins": wins, "shades": shades, "mult": mult, "zones": list(zones)}


LIGHT = np.array([-0.45, -0.75, 0.5]) / np.linalg.norm([-0.45, -0.75, 0.5])


def render_building(ax, g, wall_col, ceil_col=None, cutaway=False, ghost=None, elev=24, azim=-58, zoom=1.0,
                    lw=0.25, edge="#ffffff"):
    """Draw an EnergyPlus geometry with mplot3d.

    wall_col(zone) -> colour of exterior walls (None = plenum / unconditioned grey);
    ceil_col(zone) -> colour of zone ceilings (cut-away view: plenum roofs removed);
    ghost: list of (x0, x1, y0, y1, z0, z1) boxes drawn as wire frames (floors represented by a multiplier)."""
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    polys, fcs, ecs, lws = [], [], [], []

    def add(V, fc, ec=edge, w=lw):
        polys.append(V)
        fcs.append(fc)
        ecs.append(ec)
        lws.append(w)

    def lit(c, n):
        return shade(c, 0.80 + 0.22 * max(0.0, float(np.dot(n, LIGHT))))

    for s in g["surfs"]:
        t, bc = s["type"].lower(), s["bc"].lower()
        if t == "wall" and bc in ("outdoors", "ground", "groundfcfactormethod", "groundslabpreprocessoraverage"):
            c = wall_col(s["zone"])
            c = PLENUM if c is None else c
            if bc != "outdoors":
                c = mix(c, 0.45)
            add(s["V"], lit(c, s["n"]))
        elif t == "wall" and s["selfref"]:            # adiabatic walls (e.g. towards zones not modelled)
            c = wall_col(s["zone"])
            add(s["V"], lit(mix(PLENUM if c is None else c, 0.3), s["n"]))
        elif t == "roof" or (t == "ceiling" and s["selfref"] and s["n"][2] > 0.9):
            if cutaway:
                continue
            add(s["V"], lit("#e4e3df", s["n"]))
        elif t == "ceiling" and cutaway and ceil_col is not None:
            c = ceil_col(s["zone"])
            if c is not None:
                add(s["V"], c, "#ffffff", 0.5)
        elif t == "floor" and bc == "outdoors":      # overhangs / exposed floors
            add(s["V"], lit("#e4e3df", s["n"]))
    span = max(np.ptp(np.vstack([s["V"] for s in g["surfs"]]), axis=0)[:2])
    off = 0.004 * span
    for w in g["wins"]:
        if w["type"].lower() in ("window", "glassdoor"):
            add(w["V"] + off * w["n"], lit(GLASS, w["n"]), mix(INK2, 0.6), 0.15)
    for s in g["shades"]:
        add(s["V"], lit("#d9d8d3", s["n"]))
    pc = Poly3DCollection(polys, facecolors=fcs, edgecolors=ecs, linewidths=lws, zorder=1)
    ax.computed_zorder = False
    ax.add_collection3d(pc)
    allv = np.vstack(polys)
    lo, hi = allv.min(0), allv.max(0)
    if ghost:
        # floors represented by a multiplier: dashed envelope edges on the silhouette only (never cross the model)
        e, a = np.radians(elev), np.radians(azim)
        vd = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), 0.0])
        for (x0, x1, y0, y1, z0, z1) in ghost:
            corners = [((x0, y0), (0, -1), (-1, 0)), ((x1, y0), (0, -1), (1, 0)),
                       ((x1, y1), (0, 1), (1, 0)), ((x0, y1), (0, 1), (-1, 0))]
            for (xc, yc), n1, n2 in corners:
                v1, v2 = np.dot(n1, vd[:2]) > 0, np.dot(n2, vd[:2]) > 0
                if v1 != v2:
                    ax.plot([xc, xc], [yc, yc], [z0, z1], color=MUTED, lw=0.6, ls=(0, (2.5, 2)), zorder=3)
    ax.set_xlim(lo[0], hi[0])
    ax.set_ylim(lo[1], hi[1])
    ax.set_zlim(lo[2], hi[2])
    ax.set_box_aspect(hi - lo, zoom=zoom)
    ax.view_init(elev=elev, azim=azim)
    ax.set_proj_type("ortho")
    ax.set_axis_off()
    return lo, hi


def proj2d(ax, x, y, z):
    from mpl_toolkits.mplot3d import proj3d
    x2, y2, _ = proj3d.proj_transform(x, y, z, ax.get_proj())
    return x2, y2


# ============================================================================= fig 1: building model + hierarchy
def fig_building_model():
    from virtualbas.core import Building
    man = json.loads((BLD / "manifest.json").read_text())
    zinfo = man["topology"]["zones"]
    g = load_geometry(BLD / "model.epJSON")
    ahu_of = {z: AHU_OF_LOOP.get(v["air_loop"]) for z, v in zinfo.items()}

    def wall_col(z):
        a = ahu_of.get(z)
        return None if a is None else mix(AHU_COL[a], 0.15)

    def ceil_col(z):
        a = ahu_of.get(z)
        if a is None:
            return None
        return mix(AHU_COL[a], 0.62 if z.startswith("Core") else 0.30)

    fig = plt.figure(figsize=(FULL_W, 6.4))
    # ---------------- (a) 3D model
    ya0, yah = 0.515, 0.455
    ax = fig.add_axes([0.0, ya0 + 0.005, 0.58, yah - 0.02], projection="3d")
    h = 47.5584 / 12            # floor-to-floor height of the reference model (12 storeys)
    ghost = [(0, 73.1072, 0, 48.7381, h, 5 * h), (0, 73.1072, 0, 48.7381, 6 * h, 11 * h)]
    render_building(ax, g, wall_col, ceil_col, cutaway=True, ghost=ghost, elev=20, azim=-57, zoom=1.08)
    axa = fig.add_axes([0.0, ya0, 1.0, yah])
    axa.set_axis_off()
    axa.set_xlim(0, 1)
    axa.set_ylim(0, 1)
    panel(axa, "a", "EnergyPlus model of the large office, zones coloured by serving AHU")
    fig.canvas.draw()

    def to_fig(x, y, z):
        x2, y2 = proj2d(ax, x, y, z)
        p = ax.transData.transform((x2, y2))
        return axa.transAxes.inverted().transform(p)

    labels = [((73.1, 48.7, 45.3), "Top floor (12th): 5 zones, AHU-3", "AHU-3"),
              ((73.1, 48.7, 33.0), "Floors 2-5 and 7-11 (dashed): represented\nby the multiplier of the middle floor", None),
              ((73.1, 48.7, 21.6), "Middle floor (6th), zone multiplier 10\n(floors 2-11): 5 zones, AHU-2", "AHU-2"),
              ((73.1, 48.7, 1.6), "Ground floor: 5 zones, AHU-1", "AHU-1"),
              ((73.1, 48.7, -1.5), "Basement: 1 zone, AHU-4", "AHU-4")]
    xl = 0.6
    for (xyz, txt, a), (_, _, z) in zip(labels, [l[0] for l in labels]):
        p = to_fig(*xyz)
        ty = p[1] + {45.3: 0.0, 33.0: 0.0, 21.6: 0.0, 1.6: 0.035, -1.5: -0.045}[z]
        axa.plot([p[0] + 0.006, xl - 0.008], [p[1], ty], color=MUTED, lw=0.5)
        if a:
            axa.add_patch(Rectangle((xl, ty - 0.022), 0.016, 0.044, color=AHU_COL[a], lw=0))
        axa.text(xl + (0.024 if a else 0.0), ty, txt, va="center", ha="left", fontsize=7, color=INK,
                 linespacing=1.15)
    axa.text(xl, 0.0, "Cut-away view: plenum roofs removed to show\nthe zone ceilings (perimeter darker, core "
             "lighter);\ngrey bands = return plenums, light = windows.", fontsize=6.5, color=INK2, va="bottom",
             linespacing=1.15)

    # ---------------- (b) HVAC hierarchy
    b = Building(BLD)
    cat = b.catalog
    axb = fig.add_axes([0.0, 0.0, 1.0, 0.47])
    axb.set_axis_off()
    W, H = 100.0, 47.0
    axb.set_xlim(0, W)
    axb.set_ylim(0, H)
    panel(axb, "b", "HVAC hierarchy discovered by BAS-ization (54 equipment objects, 1,207 points)")

    def box(x, y, w, hh, txt, fc="#ffffff", ec=INK2, fs=7, tc=INK, stripe=None, bold=False, lw=0.6):
        axb.add_patch(FancyBboxPatch((x, y), w, hh, boxstyle="round,pad=0,rounding_size=0.8", fc=fc, ec=ec, lw=lw))
        if stripe:
            axb.add_patch(Rectangle((x, y), 1.0, hh, fc=stripe, ec="none"))
        axb.text(x + w / 2 + (0.5 if stripe else 0), y + hh / 2, txt, ha="center", va="center", fontsize=fs, color=tc,
                 fontweight="bold" if bold else "normal", linespacing=1.1)

    def npts(eid):
        return len(cat.equipment[eid].points)

    # plant row
    yP = 37.5
    loops = [("CW-SYS", "Condenser water", ["CT-1", "CWP-1"]), ("CHW-SYS", "Chilled water", ["CH-1", "CH-2", "CHWP-1"]),
             ("HW-SYS", "Hot water", ["BLR-1", "HWP-1"]), ("DHW-1", "Service hot water", ["DHW-1"])]
    xs = [0.3, 27.3, 57.6, 81.6]
    ws = [25.5, 28.8, 22.5, 18.1]
    centers = {}
    for (lid, lname, eq), x, w in zip(loops, xs, ws):
        axb.add_patch(FancyBboxPatch((x, yP), w, 7.6, boxstyle="round,pad=0,rounding_size=1.0", fc="#f4f3f0",
                                     ec=MUTED, lw=0.5))
        head = f"{lname} ({lid})" if lid != "DHW-1" else "Service hot water"
        axb.text(x + 1.0, yP + 6.2, head, fontsize=6.8, color=INK, va="center", fontweight="bold")
        ew = (w - 2 - 1.2 * (len(eq) - 1)) / len(eq)
        for i, e in enumerate(eq):
            ex = x + 1 + i * (ew + 1.2)
            label = {"CT-1": "Tower", "CWP-1": "Pump", "CH-1": "Chiller 1", "CH-2": "Chiller 2", "CHWP-1": "Pump",
                     "BLR-1": "Boiler", "HWP-1": "Pump", "DHW-1": "Water heater"}[e]
            box(ex, yP + 0.8, ew, 3.8, f"{label}\n{e}", fs=6.5)
        centers[lid] = x + w / 2
    # AHU row
    groups = [("AHU-1", "Ground floor", ["Core_bottom"] + [f"Perimeter_bot_ZN_{i}" for i in range(1, 5)]),
              ("AHU-2", "Middle floor (×10)", ["Core_mid"] + [f"Perimeter_mid_ZN_{i}" for i in range(1, 5)]),
              ("AHU-3", "Top floor", ["Core_top"] + [f"Perimeter_top_ZN_{i}" for i in range(1, 5)]),
              ("AHU-4", "Basement", ["Basement"])]
    slot, gap = 4.75, 3.0
    x = 14.0
    yA, yV, yZ = 20.0, 9.6, 1.0
    bus_c, bus_h = 33.6, 31.0
    ahu_x = []
    for a, fl, zs in groups:
        gw = len(zs) * slot
        aw = max(gw - 0.5, 8.6)
        ax0 = x + (gw - aw) / 2 - 0.25 if len(zs) > 1 else 99.7 - aw
        ahu_x.append((ax0, aw))
        txt = f"{a} ({npts(a)} points)\n{fl}" if len(zs) > 1 else f"{a}\n{fl}"
        box(ax0, yA, aw, 5.8, txt, fc=mix(AHU_COL[a], 0.80), ec=AHU_COL[a], fs=6.6)
        ac = ax0 + aw / 2
        for i, z in enumerate(zs):
            cx = x + i * slot + slot / 2 - 0.25
            short = "B" if z == "Basement" else ("C" if z.startswith("Core") else "P" + z[-1])
            box(cx - 2.05, yV, 4.1, 4.8, f"VAV\n{short}", fs=6.5, ec=mix(INK2, 0.2))
            zc = mix(AHU_COL[a], 0.62 if short == "C" else 0.30)
            box(cx - 2.05, yZ, 4.1, 4.8, short, fc=zc, ec="none", fs=6.8)
            axb.plot([cx, cx], [yZ + 4.8, yV], color=INK2, lw=0.6)
            axb.plot([ac, ac, cx, cx], [yA, yA - 2.4, yA - 2.4, yV + 4.8], color=INK2, lw=0.6)
        x += gw + gap
    # water distribution buses (solid = chilled water, dashed = hot water)
    dash = (0, (3, 1.6))
    for yb, src, off in [(bus_c, "CHW-SYS", -1.4), (bus_h, "HW-SYS", 1.4)]:
        ls = dash if src == "HW-SYS" else "-"
        x0 = min(ahu_x[0][0] + ahu_x[0][1] / 2 + off, centers[src])
        x1 = ahu_x[-1][0] + ahu_x[-1][1] / 2 + off
        axb.plot([x0, x1], [yb, yb], color=INK2, lw=0.6, ls=ls)
        axb.plot([centers[src], centers[src]], [yP, yb], color=INK2, lw=0.6, ls=ls)
        for ax0, aw in ahu_x:
            xo = ax0 + aw / 2 + off
            axb.plot([xo, xo], [yb, yA + 5.8], color=INK2, lw=0.6, ls=ls)
    # row labels (left margin)
    for yy, t1, t2 in [(yA + 2.9, "Air handlers", "economizer,\nCHW + HW coils,\nVSD supply fan"),
                       (yV + 2.4, "Terminals", "16 VAV boxes\nwith HW reheat"),
                       (yZ + 2.4, "Zones", "16 conditioned\n(+3 plenums)"),
                       (bus_c - 1.3, "Water", "CHW solid, HW dashed")]:
        axb.text(0.3, yy + 0.9, t1, fontsize=6.8, color=INK, fontweight="bold", va="bottom")
        axb.text(0.3, yy + 0.6, t2, fontsize=6.5, color=INK2, va="top", linespacing=1.1)
    save(fig, "fig_building_model")


# ============================================================================= fig 2: point list and tiers
TIERS = ["standard", "advanced", "next_gen", "truth"]
EQ_LABEL = {"Zone": "Zone", "VAV": "VAV terminal", "AHU": "Air handling unit", "Chiller": "Chiller",
            "WeatherStation": "Weather station", "Meter": "Utility meters", "Pump": "Pump", "PlantLoop": "Plant loop",
            "Boiler": "Boiler", "CoolingTower": "Cooling tower", "Grid": "Grid interface", "WaterHeater": "DHW heater",
            "Plenum": "Return plenum", "Building": "Building"}


def _tier_bars(ax, rows, counts, height=0.66, total_fmt="{:,}", fs=7):
    """Horizontal bars stacked by tier (fixed order) with a 0.6-pt white gap between segments and the total at the
    bar end. rows: list of keys (top to bottom); counts[key][tier]."""
    y = np.arange(len(rows))[::-1]
    tmax = max(sum(counts[r].values()) for r in rows)
    for yi, r in zip(y, rows):
        left = 0
        for t in TIERS:
            v = counts[r].get(t, 0)
            if v:
                big = v > 0.015 * tmax
                ax.barh(yi, v, left=left, height=height, color=TIER[t], edgecolor="white" if big else TIER[t],
                        linewidth=0.6 if big else 0.3)
                left += v
        ax.text(left + tmax * 0.012, yi, total_fmt.format(left), va="center", ha="left", fontsize=fs, color=INK)
    ax.set_yticks(y)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    return y


def fig_points():
    from virtualbas.core import Building
    cat = Building(BLD).catalog
    P = list(cat.points.values())
    n = len(P)
    neq = Counter(e.type for e in cat.equipment.values())
    by_eq = defaultdict(Counter)
    by_kind = defaultdict(Counter)
    by_src = defaultdict(Counter)
    for p in P:
        by_eq[p.equip_type][p.tier] += 1
        by_kind[p.kind][p.tier] += 1
        by_src[p.source][p.tier] += 1
    tiers = Counter(p.tier for p in P)

    fig = plt.figure(figsize=(FULL_W, 3.55))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.22, 1], height_ratios=[7.6, 4.4], wspace=0.62, hspace=0.62,
                          left=0.205, right=0.975, top=0.80, bottom=0.10)
    # (a) equipment classes
    ax = fig.add_subplot(gs[:, 0])
    rows = sorted(by_eq, key=lambda k: -sum(by_eq[k].values()))
    _tier_bars(ax, rows, by_eq)
    ax.set_yticklabels([f"{EQ_LABEL.get(r, r)} ({neq[r]})" if neq[r] > 1 else EQ_LABEL.get(r, r) for r in rows],
                       fontsize=7)
    ax.set_xlabel("points", fontsize=7.5)
    ax.set_xlim(0, 660)
    panel(ax, "a", "points per equipment class (count)")
    # (b) kinds
    axk = fig.add_subplot(gs[0, 1])
    KL = {"sensor": "sensor", "truth": "ground truth only", "virtual": "BAS-calculated", "setpoint": "set point",
          "status": "status", "meter": "meter", "command": "command"}
    rows_k = sorted(by_kind, key=lambda k: -sum(by_kind[k].values()))
    _tier_bars(axk, rows_k, by_kind)
    axk.set_yticklabels([KL.get(r, r) for r in rows_k], fontsize=7)
    axk.set_xlim(0, 820)
    panel(axk, "b", "by kind")
    # (c) source of the true value
    axs = fig.add_subplot(gs[1, 1])
    SL = {"energyplus": "EnergyPlus", "bas": "BAS (calculated)", "model": "outer-space model",
          "surrogate": "surrogate model"}
    rows_s = sorted(by_src, key=lambda k: -sum(by_src[k].values()))
    _tier_bars(axs, rows_s, by_src)
    axs.set_yticklabels([SL.get(r, r) for r in rows_s], fontsize=7)
    axs.set_xlim(0, 820)
    axs.set_xlabel("points", fontsize=7.5)
    panel(axs, "c", "by source of the truth")
    # legend + headline
    from matplotlib.patches import Patch
    hs = [Patch(fc=TIER[t], ec="none", label=f"{TIER_LABEL[t]}: {tiers[t]:,}") for t in TIERS]
    fig.legend(handles=hs, loc="upper left", bbox_to_anchor=(0.01, 0.995), ncol=4, fontsize=7, handlelength=1.1,
               handletextpad=0.5, columnspacing=1.3, frameon=False)
    fig.text(0.01, 0.905, f"A typical BAS of today exposes only the standard tier: {tiers['standard']:,} of {n:,} "
             f"points ({tiers['standard'] / n:.0%}).", fontsize=7.5, color=INK, va="center")
    save(fig, "fig_points")
    return {"n": n, "tiers": dict(tiers), "by_eq": {k: dict(v) for k, v in by_eq.items()}}


# ============================================================================= fig 3: fault and event library
SHORT = {
    "sensor_bias": "Bias", "sensor_drift": "Drift", "sensor_gain": "Gain error", "sensor_noise": "Excess noise",
    "sensor_stuck": "Stuck value", "sensor_spikes": "Spikes", "sensor_dropout": "Dropout",
    "sensor_override": "Override / spoofing",
    "vav_damper_stuck": "VAV damper stuck", "reheat_valve_stuck_closed": "Reheat stuck closed",
    "reheat_valve_stuck_open": "Reheat stuck open", "oa_damper_stuck": "OA damper stuck",
    "cooling_coil_valve_stuck_closed": "CC valve stuck closed", "heating_coil_valve_stuck_closed": "HC valve stuck closed",
    "supply_fan_failure": "Supply fan failure",
    "chiller_fouling": "Chiller fouling", "boiler_fouling": "Boiler fouling", "tower_fouling": "Tower fouling",
    "filter_fouling": "Filter loading", "fan_degradation": "Fan degradation", "equipment_trip": "Equipment trip",
    "filter_bypass": "Filter bypass",
    "schedule_error_always_on": "Schedule always on", "schedule_error_off": "Schedule never on",
    "pid_mistuning": "PI mistuning", "economizer_disabled": "Economizer disabled",
    "economizer_always_on": "Economizer always on", "sat_reset_disabled": "SAT reset disabled",
    "controller_frozen": "Controller frozen", "setpoint_override": "Set-point override",
    "comm_loss": "Communication loss", "historian_outage": "Historian outage",
    "occupancy_surge": "Occupancy surge", "meeting": "Meeting", "holiday": "Unscheduled holiday",
    "weather_change": "Weather change", "outdoor_co2_change": "Outdoor CO$_2$ change",
    "wildfire_smoke": "Wildfire smoke", "window_open": "Window open", "plug_load_change": "Plug-load change",
    "lighting_change": "Lighting change", "indoor_pollutant_source": "Pollutant source",
    "demand_response": "Demand response", "price_spike": "Price / carbon spike"}
TARGET = {"point:sensor": "any sensor point", "equip:VAV": "VAV", "equip:AHU": "AHU", "equip:Chiller": "chiller",
          "equip:Boiler": "boiler", "equip:CoolingTower": "cooling tower",
          "equip:Chiller|Boiler|CoolingTower|Pump": "plant equipment", "equip:VAV|AHU": "VAV, AHU",
          "equip:Zone": "zone", "equip:*": "any equipment", "building": "building", "zone": "zone",
          "zone|building": "zone or building"}
CAT_COL = {"fault": FAULT, "event": ENV}


def fig_fault_library():
    from virtualbas.realworld.faults import REGISTRY, Injection
    by_layer = defaultdict(list)
    for name, t in REGISTRY.items():
        by_layer[t.layer].append(t)
    fault_layers = ["sensor", "actuator", "equipment", "control", "network"]
    event_layers = ["occupancy", "weather", "gains", "iaq", "grid"]
    assert set(by_layer) == set(fault_layers + event_layers), set(by_layer)
    ncat = Counter(t.category for t in REGISTRY.values())
    LAYER_NAME = {"sensor": "Sensor", "actuator": "Actuator", "equipment": "Equipment", "control": "Control",
                  "network": "Network", "occupancy": "Occupancy", "weather": "Weather", "gains": "Gains / envelope",
                  "iaq": "Indoor air quality", "grid": "Grid"}

    W = FULL_W
    ch, vs, gap = 0.235, 0.04, 0.07
    cw = (W - 4 * gap) / 5
    n_f = max(len(by_layer[l]) for l in fault_layers)
    n_e = max(len(by_layer[l]) for l in event_layers)
    sec_h, head_h = 0.2, 0.19          # section label row, layer header row
    top_h = 2 * (sec_h + head_h) + (n_f + n_e) * (ch + vs) + 0.1
    prof_h = 1.45
    H = top_h + prof_h
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0, prof_h / H, 1, top_h / H])
    ax.set_xlim(0, W)
    ax.set_ylim(0, top_h)
    ax.set_axis_off()
    panel(ax, "a", f"fault and event library: {len(REGISTRY)} registered types ({ncat['fault']} faults, "
                   f"{ncat['event']} events)")

    def block(layers, label, ytop, nrows):
        ax.text(0, ytop - sec_h / 2, label, fontsize=7.5, color=INK2, va="center", style="italic")
        yh = ytop - sec_h - head_h / 2
        for j, layer in enumerate(layers):
            x = j * (cw + gap)
            items = by_layer[layer]
            ax.text(x, yh, f"{LAYER_NAME[layer]} ({len(items)})", fontsize=7, fontweight="bold", color=INK,
                    va="center", ha="left")
            for i, t in enumerate(items):
                y = ytop - sec_h - head_h - (i + 1) * (ch + vs) + vs
                ax.add_patch(FancyBboxPatch((x, y), cw, ch, boxstyle="round,pad=0,rounding_size=0.035",
                                            fc="#ffffff", ec=mix(INK2, 0.55), lw=0.5))
                ax.add_patch(FancyBboxPatch((x + 0.014, y + 0.025), 0.03, ch - 0.05,
                                            boxstyle="round,pad=0,rounding_size=0.012", fc=CAT_COL[t.category],
                                            ec="none"))
                ax.text(x + 0.07, y + ch * 0.68, SHORT.get(t.name, t.name), fontsize=6.6, color=INK, va="center",
                        ha="left")
                ax.text(x + 0.07, y + ch * 0.28, TARGET.get(t.target, t.target), fontsize=6.5, color=MUTED,
                        va="center", ha="left")
        return ytop - sec_h - head_h - nrows * (ch + vs)

    y = block(fault_layers, f"Faults ({ncat['fault']})", top_h, n_f)
    block(event_layers, f"Events ({ncat['event']})", y - 0.1, n_e)
    # category key
    for k, (cat, lab) in enumerate([("fault", "fault (abnormal condition)"), ("event", "event (real-world randomness)")]):
        xk = W - 3.0 + k * 1.5
        ax.add_patch(FancyBboxPatch((xk, top_h - sec_h / 2 - 0.055), 0.03, 0.11,
                                    boxstyle="round,pad=0,rounding_size=0.012", fc=CAT_COL[cat], ec="none"))
        ax.text(xk + 0.06, top_h - sec_h / 2, lab, fontsize=6.8, color=INK2, va="center")

    # (b) severity profiles, computed with Injection.severity()
    t0 = dt.datetime(2023, 7, 10, 2)
    t1 = t0 + dt.timedelta(hours=8)
    tt = [t0 + dt.timedelta(minutes=5 * k) for k in range(-24, 12 * 12 + 1)]
    xh = np.array([(t - t0).total_seconds() / 3600 for t in tt])
    profs = [("step", "Step", {}, "$s=1$ between $t_0$ and $t_1$"),
             ("ramp", "Ramp (incipient fault)", {"ramp_s": 5 * 3600}, "linear rise over $T_r$ (here 5 h)"),
             ("intermittent", "Intermittent", {"period_s": 2 * 3600, "duty": 0.4},
              "period $P$ = 2 h, duty cycle $D$ = 0.4")]
    lm, sp = 0.42, 0.32
    bw = (W - lm - 0.05 - 2 * sp) / 3
    for k, (pf, title, kw, note) in enumerate(profs):
        axp = fig.add_axes([(lm + k * (bw + sp)) / W, 0.36 / H, bw / W, 0.62 / H])
        inj = Injection("sensor_bias", "AHU-1/SA-T", t0, t1, profile=pf, **kw)
        s = np.array([inj.severity(t) for t in tt])
        axp.fill_between(xh, 0, s, step="post", color=mix(FAULT, 0.85), lw=0)
        axp.step(xh, s, where="post", color=FAULT, lw=1.1)
        axp.set_ylim(-0.08, 1.15)
        axp.set_xlim(xh[0], xh[-1])
        axp.set_yticks([0, 1])
        axp.set_xticks([0, 8])
        axp.set_xticklabels(["$t_0$", "$t_1$"])
        axp.grid(False)
        axp.text(0.0, 1.07, title, transform=axp.transAxes, fontsize=7.2, color=INK, va="bottom")
        axp.set_xlabel(note, fontsize=6.8, color=INK2, labelpad=1.5)
        if k == 0:
            axp.set_ylabel("$s(t)$", fontsize=7.5, labelpad=1)
    fig.text(0.0, (prof_h - 0.06) / H, "(b) severity profiles $s(t)$ of an injection; each type modulates one "
             r"parameter, $\theta(t)=\theta_0+s(t)\,\Delta\theta$", fontsize=8.5, fontweight="bold", color=INK,
             va="top")
    save(fig, "fig_fault_library")
    return {"n": len(REGISTRY), "cat": dict(ncat), "layers": {k: len(v) for k, v in by_layer.items()}}




# ============================================================================= fig 4: labelled data products
LABEL_RUN = ROOT / "results/exp3_fdd/train"
BIT_ORDER = [(8, "sensor fault active", FAULT), (2, "stuck value", C[3]), (4, "spike", AI),
             (32, "false binary reading", C[4]), (1, "missing sample", INK2)]


def fig_labels():
    import pandas as pd
    import matplotlib.dates as mdates
    from matplotlib.colors import ListedColormap, BoundaryNorm
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D
    from virtualbas.bas.historian import load_dataset
    d = load_dataset(LABEL_RUN)
    obs, tru, lab = d["observed"], d["truth"], d["labels"]
    inj = d["injections_table"]
    t_start, t_end = obs.index[0], obs.index[-1] + pd.Timedelta(minutes=5)
    X0, X1 = mdates.date2num(t_start), mdates.date2num(t_end)

    def weeks(axis):
        axis.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO, interval=2))
        axis.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))

    fig = plt.figure(figsize=(FULL_W, 6.6))
    gs = fig.add_gridspec(3, 2, height_ratios=[1.45, 1.75, 1.2], hspace=0.62, wspace=0.27,
                          left=0.2, right=0.985, top=0.96, bottom=0.095)
    # ---------------- (a) Gantt of injections: one row per type, colour = target AHU
    ax = fig.add_subplot(gs[0, :])
    layer_order = ["sensor", "actuator", "equipment", "control", "network"]
    lay_of = {i["type"]: i["layer"] for i in inj}
    types = sorted(lay_of, key=lambda t: (layer_order.index(lay_of[t]), t))
    lanes, rows = {}, []
    for ty in types:
        lane_end = []
        for it in sorted([i for i in inj if i["type"] == ty], key=lambda i: i["start"]):
            s, e = pd.Timestamp(it["start"]), pd.Timestamp(it["end"])
            for k, le in enumerate(lane_end):
                if s > le + pd.Timedelta(hours=6):
                    lane_end[k] = e
                    lanes[it["id"]] = (ty, k)
                    break
            else:
                lane_end.append(e)
                lanes[it["id"]] = (ty, len(lane_end) - 1)
        rows.append((ty, len(lane_end)))
    ypos, y = {}, 0.0
    sep = []
    prev = None
    for ty, nl in rows[::-1]:
        if prev is not None and lay_of[ty] != lay_of[prev]:
            sep.append(y - 0.5)
            y += 0.25
        for k in range(nl):
            ypos[(ty, k)] = y + (nl - 1 - k) * 0.55
        y += (nl - 1) * 0.55 + 1.0
        prev = ty
    for it in inj:
        s, e = pd.Timestamp(it["start"]), pd.Timestamp(it["end"])
        a = it["target"].split("/")[0]
        ax.barh(ypos[lanes[it["id"]]], (e - s).total_seconds() / 86400, left=mdates.date2num(s), height=0.48,
                color=AHU_COL[a], lw=0)
    ty_y = {ty: np.mean([ypos[(ty, k)] for k in range(nl)]) for ty, nl in rows}
    ax.set_yticks([ty_y[t] for t, _ in rows])
    ax.set_yticklabels([("Sensor " + SHORT[t].lower()) if lay_of[t] == "sensor" else SHORT[t] for t, _ in rows],
                       fontsize=6.8)
    for ys in sep:
        ax.axhline(ys, color=GRID, lw=0.6)
    ax.set_ylim(-0.6, y - 0.4)
    ax.set_xlim(X0, X1)
    weeks(ax)
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    nsrc = Counter(i["source"] for i in inj)
    panel(ax, "a", f"{len(inj)} random fault injections of {len(types)} types in 12 weeks, by target AHU")
    hs = [Patch(fc=AHU_COL[a], ec="none", label=a) for a in ("AHU-1", "AHU-2", "AHU-3", "AHU-4")]
    ax.legend(handles=hs, loc="upper right", bbox_to_anchor=(1.0, -0.16), ncol=4, fontsize=6.6, handlelength=1.0,
              handletextpad=0.4, columnspacing=1.0, frameon=False)

    # ---------------- (b) label raster
    axr = fig.add_subplot(gs[1, :])
    pts = []
    for k in range(1, 5):
        pts += [f"AHU-{k}/{n}" for n in ("SA-T", "MA-T", "CC-LAT", "SA-F")]
    pts += [f"ZN-{z}/ZN-OCC" for z in ("Core_mid", "Basement")]
    L = lab[pts]
    code = np.zeros(L.shape, int)
    for ci, (bit, _, _) in reversed(list(enumerate(BIT_ORDER))):
        code[(L.values & bit) > 0] = ci + 1
    cd = pd.DataFrame(code, index=L.index, columns=pts)
    # 2-h bins: the highest-priority label of the bin (sensor fault > stuck > spike > false binary > missing)
    pri = cd.replace(0, 99).resample("2h").min().replace(99, 0)
    cmap = ListedColormap(["#f3f2ef"] + [c for _, _, c in BIT_ORDER])
    norm = BoundaryNorm(np.arange(-0.5, len(BIT_ORDER) + 1), cmap.N)
    x1 = mdates.date2num(pri.index[-1] + pd.Timedelta(hours=2))
    axr.imshow(pri.values.T, aspect="auto", cmap=cmap, norm=norm, interpolation="nearest",
               extent=[mdates.date2num(pri.index[0]), x1, len(pts) - 0.5, -0.5])
    axr.set_yticks(range(len(pts)))
    axr.set_yticklabels([p.replace("ZN-", "").replace("/", " ").replace("_", " ") for p in pts], fontsize=6.5)
    for yy in [3.5, 7.5, 11.5, 15.5]:
        axr.axhline(yy, color="white", lw=1.6)
    axr.grid(False)
    axr.tick_params(axis="y", length=0)
    axr.set_xlim(X0, X1)
    weeks(axr)
    for s in axr.spines.values():
        s.set_visible(False)
    nlab = int((lab.values > 0).sum())
    panel(axr, "b", f"per-sample label bit masks, 18 of the {lab.shape[1]} recorded sensor points (2-h bins)")
    hs = [Patch(fc=c, ec="none", label=f"{name} (bit {int(np.log2(bit))})") for bit, name, c in BIT_ORDER]
    axr.legend(handles=hs, loc="upper left", bbox_to_anchor=(-0.235, -0.1), ncol=5, fontsize=6.6, handlelength=1.0,
               handletextpad=0.4, columnspacing=0.9, frameon=False)

    # ---------------- (c, d) zooms: observed vs truth with the label shading
    zooms = [("c", "AHU-2/MA-T", "inj-0024", "2023-06-06 12:00", "2023-06-11 12:00", 8, "drift",
              "label: sensor fault (bit 3)", 0.97),
             ("d", "AHU-4/SA-T", "inj-0012", "2023-05-07 06:00", "2023-05-10 12:00", 2, "stuck",
              "label: stuck (bit 1)", 0.55)]
    for j, (letter, pid, iid, a, b, bit, word, ltxt, ly) in enumerate(zooms):
        axz = fig.add_subplot(gs[2, j])
        o, t, l = obs[pid][a:b], tru[pid][a:b], lab[pid][a:b]
        on = ((l & bit) > 0).values.astype(int)
        edges = np.diff(np.r_[0, on, 0])
        for s_, e_ in zip(np.where(edges == 1)[0], np.where(edges == -1)[0]):
            axz.axvspan(l.index[s_], l.index[min(e_, len(l) - 1)], color=FAULT_BG, lw=0, zorder=0)
        axz.plot(t.index, t.values, color=INNER, lw=1.0)
        axz.plot(o.index, o.values, color=OUTER, lw=0.8)
        axz.set_xlim(o.index[0], o.index[-1])
        axz.xaxis.set_major_locator(mdates.DayLocator())
        axz.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
        axz.set_ylabel(f"{pid.split('/')[1]} [°C]", fontsize=7.5)
        panel(axz, letter, f"{pid.replace('/', ' ')}: {word} ({iid})")
        axz.text(0.5 if j else 0.98, ly, ltxt, transform=axz.transAxes, ha="center" if j else "right", va="top",
                 fontsize=6.6, color=INK2)
    hl = [Line2D([], [], color=INNER, lw=1.2, label="truth (EnergyPlus, inner space)"),
          Line2D([], [], color=OUTER, lw=1.2, label="observed (BAS trend log)"),
          Patch(fc=FAULT_BG, ec="none", label="labelled samples")]
    fig.legend(handles=hl, loc="lower center", bbox_to_anchor=(0.55, 0.0), ncol=3, fontsize=6.8, handlelength=1.5,
               columnspacing=1.5, frameon=False)
    save(fig, "fig_labels")
    return {"n_inj": len(inj), "types": len(types), "sources": dict(nsrc), "n_points": lab.shape[1],
            "n_samples": lab.shape[0], "labelled_samples": nlab}




# ============================================================================= fig 5: forecasts and grid signals
def fig_forecast_grid():
    import yaml
    import matplotlib.dates as mdates
    from virtualbas.realworld.environment import EnvConfig, WeatherFile, WeatherForecast, tou_price
    bcfg = yaml.safe_load((BLD / "building.yaml").read_text())
    cfg = EnvConfig.from_dict(bcfg.get("environment"))
    seed = 11                                   # seed of scenarios/wildfire_smoke.yaml (same week)
    wf = WeatherFile(BLD / "weather.epw", 2023)
    fc = WeatherForecast(wf, cfg, np.random.default_rng([seed, 3, 4]))
    d0, d1 = dt.datetime(2023, 7, 10), dt.datetime(2023, 7, 17)
    # hourly issues (spin-up of the AR(1) issue correlation from 8 July)
    issues = {}
    t = dt.datetime(2023, 7, 8)
    while t < d1:
        fc.update(t)
        if t >= d0:
            issues[t] = (np.array(fc.times), fc.values["tdb"].copy(), fc.truth["tdb"].copy())
        t += dt.timedelta(hours=1)
    err = np.array([v[1] - v[2] for v in issues.values()])          # issues x leads
    rmse = np.sqrt((err ** 2).mean(axis=0))
    leads = WeatherForecast.LEADS
    sig = cfg.fc_t_sigma0 + cfg.fc_t_sigma_inf * (1 - np.exp(-leads / cfg.fc_t_tau_h))
    # 5-min truth, price, carbon (same equations and random-stream layout as OuterEnvironment.step)
    ts = [d0 + dt.timedelta(minutes=5 * k) for k in range(int((d1 - d0).total_seconds() // 300) + 1)]
    tdb = np.array([wf.at(x, "tdb") for x in ts])
    rng = np.random.default_rng([seed, 3, 3])
    phi = math.exp(-(300 / 3600) / 3.0)
    x_ci, price, ci = 0.0, [], []
    for x in ts:
        dow = (x.weekday() + 1) % 7 + 1
        price.append(tou_price(cfg, x, dow)[0])
        x_ci = phi * x_ci + cfg.carbon_sigma * math.sqrt(1 - phi * phi) * rng.normal()
        hod = x.hour + x.minute / 60
        ghi = wf.at(x, "ghi")
        ci.append(max(0.02, cfg.carbon_base * (1 + cfg.carbon_diurnal * math.cos(2 * math.pi * (hod - 19) / 24)
                                                - cfg.carbon_solar_dip * min(1.0, ghi / 1000)) + x_ci))
    price, ci = np.array(price), np.array(ci)
    dr0, dr1 = dt.datetime(2023, 7, 13, 14), dt.datetime(2023, 7, 13, 17)     # DR event of wildfire_smoke.yaml

    fig = plt.figure(figsize=(FULL_W, 4.75))
    gs = fig.add_gridspec(3, 2, width_ratios=[2.35, 1], height_ratios=[1.6, 0.9, 0.9], hspace=0.55, wspace=0.3,
                          left=0.09, right=0.985, top=0.9, bottom=0.07)
    ax = fig.add_subplot(gs[0, 0])
    ax.plot(ts, tdb, color=INNER, lw=1.3, zorder=3)
    shown = [d0 + dt.timedelta(days=k) for k in (0, 2, 4, 6)]
    for k, iss in enumerate(shown):
        tt, v, _ = issues[iss]
        tt = [iss] + list(tt)
        v = np.r_[wf.at(iss, "tdb"), v]
        sg = np.r_[0.0, sig]
        ax.fill_between(tt, v - sg, v + sg, color=mix(OUTER, 0.78), lw=0, zorder=1)
        ax.plot(tt, v, color=OUTER, lw=0.9, zorder=2)
        ax.plot([iss], [v[0]], "o", ms=3.2, color=OUTER, mec="white", mew=0.5, zorder=4)
    ax.set_xlim(d0, d1)
    date_axis(ax)
    ax.set_ylabel("outdoor air temperature [°C]", fontsize=7.5)
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    ax.legend(handles=[Line2D([], [], color=INNER, lw=1.3, label="weather file (truth)"),
                       Line2D([], [], color=OUTER, lw=0.9, marker="o", ms=3, mec="white", mew=0.5,
                              label="48-h forecast (issue time marked)"),
                       Patch(fc=mix(OUTER, 0.78), ec="none", label=r"$\pm\sigma(h)$")],
              loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=3, fontsize=6.8, handlelength=1.6,
              borderaxespad=0.15, columnspacing=1.2)
    panel(ax, "a", "")
    ax.set_title("(a) outdoor temperature: truth and forecasts", loc="left", fontsize=8.5, fontweight="bold", color=INK, pad=16)
    # (b) error growth with lead time
    axb = fig.add_subplot(gs[0, 1])
    axb.plot(leads, sig, color=INK2, lw=1.0, ls=(0, (3, 1.5)), label=r"model $\sigma(h)$")
    axb.plot(leads, rmse, "o", ms=2.6, color=OUTER, mec="none", label="RMSE, 168 issues")
    axb.set_xlim(0, 49)
    axb.set_ylim(0, 3.0)
    axb.set_xticks([0, 12, 24, 36, 48])
    axb.set_xlabel("lead time $h$ [h]", fontsize=7.5)
    axb.set_ylabel("forecast error [K]", fontsize=7.5)
    axb.legend(loc="lower right", fontsize=6.8, handlelength=1.5, borderaxespad=0.2)
    axb.set_title("(b) error vs. lead time", loc="left", fontsize=8.5, fontweight="bold", color=INK, pad=16)
    # (c) price, (d) carbon
    axc = fig.add_subplot(gs[1, :])
    axd = fig.add_subplot(gs[2, :], sharex=axc)
    for a_ in (axc, axd):
        a_.axvspan(dr0, dr1, color=FAULT_BG, lw=0, zorder=0)
    axc.step(ts, price, where="post", color=C[3], lw=1.1)
    axc.set_ylim(0, 0.33)
    axc.set_yticks([0, 0.1, 0.2, 0.3])
    axc.set_ylabel("$/kWh", fontsize=7.5)
    axc.text(1.0, 1.02, "weekend: off-peak", transform=axc.transAxes, ha="right", va="bottom", fontsize=6.6,
             color=INK2)
    axc.set_title("(c) time-of-use electricity price", loc="left", fontsize=8.5, fontweight="bold", color=INK, pad=4)
    plt.setp(axc.get_xticklabels(), visible=False)
    axd.plot(ts, ci, color=INK2, lw=0.9)
    axd.set_ylim(0, 0.6)
    axd.set_ylabel("kgCO$_2$/kWh", fontsize=7.5)
    axd.set_xlim(d0, d1)
    date_axis(axd)
    axd.set_title("(d) marginal grid carbon intensity", loc="left", fontsize=8.5, fontweight="bold", color=INK,
                  pad=4)
    axc.text(dt.datetime(2023, 7, 13, 18), 0.29, "\u2190 demand-response event (300 kW shed request)", fontsize=6.6,
             color=INK2, va="center", ha="left")
    save(fig, "fig_forecast_grid")
    k6, k24, k48 = (np.where(leads == h)[0][0] for h in (6, 24, 48))
    return {"rmse_6h": float(rmse[k6]), "rmse_24h": float(rmse[k24]), "rmse_48h": float(rmse[k48]),
            "sigma_1h": float(sig[0]), "sigma_48h": float(sig[-1]), "price": sorted(set(np.round(price, 3))),
            "ci_min": float(ci.min()), "ci_max": float(ci.max()), "ci_mean": float(ci.mean())}


# ============================================================================= fig 6: zone maps (wildfire smoke)
def zone_plans(g):
    """Plan polygons (x, y) of the floor surfaces of every zone."""
    out = defaultdict(list)
    for s in g["surfs"]:
        if s["type"].lower() == "floor":
            out[s["zone"]].append(s["V"][:, :2])
    return out


def fig_zone_maps():
    import pandas as pd
    import matplotlib.dates as mdates
    from matplotlib.colors import LinearSegmentedColormap, Normalize
    from matplotlib.collections import PolyCollection
    files = {c: OUT_MAPS / f"pm25_{c.replace(' ', '')}.json" for c in MAP_CASES}
    if not all(f.exists() for f in files.values()):
        sim_zone_maps()
    D = {c: json.loads(f.read_text()) for c, f in files.items()}
    zones = D["MERV 8"]["zones"]
    S = {}
    for c, d in D.items():
        df = pd.DataFrame(d["rows"])
        df.index = pd.to_datetime(df["time"])
        S[c] = df
    plans = zone_plans(load_geometry(BLD / "model.epJSON"))
    floors = [("Basement", ["Basement"]),
              ("Ground floor", ["Core_bottom"] + [f"Perimeter_bot_ZN_{i}" for i in range(1, 5)]),
              ("Middle floor (×10)", ["Core_mid"] + [f"Perimeter_mid_ZN_{i}" for i in range(1, 5)]),
              ("Top floor", ["Core_top"] + [f"Perimeter_top_ZN_{i}" for i in range(1, 5)])]
    mean8 = S["MERV 8"][zones].mean(axis=1)
    tA = mean8.idxmax()                                     # peak of the zone-mean PM2.5 with MERV 8
    tB = pd.Timestamp("2023-07-13 03:00")                   # night, AHUs off
    snaps = [("A", tA), ("B", tB)]
    cmap = LinearSegmentedColormap.from_list("smoke", ["#fbf8f4", "#e8c7a5", "#c27d45", "#7a4320", "#3e1f0b"])
    norm = Normalize(0, 100)

    fig = plt.figure(figsize=(FULL_W, 5.45))
    # ---------------- (a) time series
    ax = fig.add_axes([0.095, 0.765, 0.875, 0.165])
    w0, w1 = pd.Timestamp("2023-07-11 12:00"), pd.Timestamp("2023-07-14 12:00")
    oa = S["MERV 8"]["OA-PM25"][w0:w1]
    ax.plot(oa.index, oa.values, color=INK2, lw=1.0, label="outdoor")
    ser_col = {"MERV 8": C[0], "MERV 13": C[1]}
    for c in MAP_CASES:
        m = S[c][zones].mean(axis=1)[w0:w1]
        ax.plot(m.index, m.values, color=ser_col[c], lw=1.2, label=f"zone mean, {c}")
    for lab_, t_ in snaps:
        ax.axvline(t_, color=MUTED, lw=0.6, ls=(0, (2, 2)))
        ax.text(t_, 152, lab_, ha="center", va="bottom", fontsize=7, color=INK, fontweight="bold")
    ax.set_ylim(0, 150)
    ax.set_yticks([0, 50, 100, 150])
    ax.set_xlim(w0, w1)
    date_axis(ax)
    ax.set_ylabel("PM2.5 [µg/m³]", fontsize=7.5)
    ax.legend(loc="upper right", fontsize=6.8, ncol=1, handlelength=1.5, borderaxespad=0.1, labelspacing=0.3)
    fig.text(0.0, 0.99, "(a) wildfire-smoke episode (+120 µg/m³ outdoors for 30 h): outdoor and zone-mean PM2.5",
             fontsize=8.5, fontweight="bold", color=INK, va="top")

    # ---------------- (b) maps
    fig.text(0.0, 0.672, "(b) zone PM2.5 (truth) at instants A and B, floor plans of the EnergyPlus model",
             fontsize=8.5, fontweight="bold", color=INK, va="bottom")
    rows = [(c, s) for s in snaps for c in MAP_CASES]
    left, right, top, bot = 0.135, 0.875, 0.635, 0.012
    cw = (right - left) / 4
    rh = (top - bot) / len(rows)
    allxy = np.vstack([p for z in plans for p in plans[z]])
    xmin, ymin = allxy.min(0)
    xmax, ymax = allxy.max(0)
    out = {}
    for i, (c, (lab_, t_)) in enumerate(rows):
        r = S[c].loc[t_]
        oaf = np.mean([r[f"AHU-{k}|OAF"] for k in range(1, 5)])
        state = f"OA fraction {oaf:.0f}%" if oaf > 0.5 else "AHUs off"
        fig.text(0.0, top - (i + 0.5) * rh + 0.012, f"{c}", fontsize=7.5, fontweight="bold", color=INK, va="center")
        fig.text(0.0, top - (i + 0.5) * rh - 0.016, f"{lab_}: {t_:%d %b %H:%M}\n{state}", fontsize=6.6, color=INK2,
                 va="center", linespacing=1.15)
        for j, (fname, zs) in enumerate(floors):
            axm = fig.add_axes([left + j * cw + 0.006, top - (i + 1) * rh + 0.03, cw - 0.012, rh - 0.042])
            polys, vals = [], []
            for z in zs:
                for P in plans[z]:
                    polys.append(P)
                    vals.append(r[f"ZN-{z}"])
            pc = PolyCollection(polys, array=np.array(vals), cmap=cmap, norm=norm, edgecolors="white",
                                linewidths=0.5)
            axm.add_collection(pc)
            axm.set_xlim(xmin - 0.5, xmax + 0.5)
            axm.set_ylim(ymin - 0.5, ymax + 0.5)
            axm.set_aspect("equal")
            axm.set_axis_off()
            if i == 0:
                axm.set_title(fname, fontsize=7.2, color=INK, pad=3, loc="center", fontweight="normal")
            core = [r[f"ZN-{z}"] for z in zs if not z.startswith("Perimeter")]
            per = [r[f"ZN-{z}"] for z in zs if z.startswith("Perimeter")]
            v = core[0]
            axm.text((xmin + xmax) / 2, (ymin + ymax) / 2, f"{v:.0f}", ha="center", va="center", fontsize=6.8,
                     color="white" if norm(v) > 0.55 else INK)
            if per:
                axm.text((xmin + xmax) / 2, ymin - 1.5, (f"perimeter {min(per):.0f}–{max(per):.0f}" if round(min(per)) != round(max(per))
                                                       else f"perimeter {min(per):.0f}"), ha="center",
                         va="top", fontsize=6.5, color=INK2)
            out[(c, lab_, fname)] = {"core": float(v), "per": [float(min(per)), float(max(per))] if per else None}
    cax = fig.add_axes([0.905, bot + 0.04, 0.016, top - bot - 0.08])
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax)
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=7, length=2)
    cb.set_label("zone PM2.5 [µg/m³]", fontsize=7.5)
    save(fig, "fig_zone_maps")
    res = {"tA": str(tA), "tB": str(tB),
           "peak_mean": {c: float(S[c][zones].mean(axis=1).max()) for c in MAP_CASES},
           "mean_at_A": {c: float(S[c].loc[tA, zones].mean()) for c in MAP_CASES},
           "mean_at_B": {c: float(S[c].loc[tB, zones].mean()) for c in MAP_CASES},
           "oa_at_A": float(S["MERV 8"].loc[tA, "OA-PM25"]), "oa_peak": float(S["MERV 8"]["OA-PM25"].max()),
           "maps": {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in out.items()}}
    return res


# ============================================================================= fig 7: generality
GEN = [("RefBldgSmallOfficeNew2004_Chicago", "Small office"), ("RefBldgMediumOfficeNew2004_Chicago", "Medium office"),
       ("RefBldgLargeOfficeNew2004_Chicago", "Large office"), ("RefBldgSecondarySchoolNew2004_Chicago",
                                                                 "Secondary school"),
       ("RefBldgHospitalNew2004_Chicago", "Hospital")]


def fig_generality():
    gen = {r["model"]: r for r in json.loads((ROOT / "results/exp5_generality/generality.json").read_text())}
    W = FULL_W
    lab_w = 0.78
    cw = (W - lab_w) / 5
    img_h, tab_h = 1.0, 1.1
    H = 0.14 + img_h + tab_h
    fig = plt.figure(figsize=(W, H))
    rows = [("Zones (conditioned)", lambda r: f"{r['conditioned_zones']}"),
            ("Air loops", lambda r: f"{r['air_loops']}"),
            ("VAV terminals", lambda r: f"{r['vav_terminals']}"),
            ("Equipment", lambda r: f"{sum(r['equipment'].values())}"),
            ("BAS points", lambda r: f"{r['n_points']:,}"),
            ("1-week run [s]", lambda r: f"{r['week_run_s']:.1f}"),
            ("Speed [samples/s]", lambda r: f"{r['steps_per_s']:.0f}")]
    out = {}
    for k, (model, name) in enumerate(GEN):
        bdir = ROOT / "results/exp5_generality/buildings" / model
        man = json.loads((bdir / "manifest.json").read_text())
        cond = {z for z, v in man["topology"]["zones"].items() if v.get("air_loop")}
        g = load_geometry(bdir / "model.epJSON")
        ax = fig.add_axes([(lab_w + (k + 0.06) * cw) / W, (tab_h - 0.02) / H, 0.88 * cw / W, img_h / H],
                          projection="3d")
        ghost = None
        if "LargeOffice" in model:
            h = 47.5584 / 12
            ghost = [(0, 73.1072, 0, 48.7381, h, 5 * h), (0, 73.1072, 0, 48.7381, 6 * h, 11 * h)]
        render_building(ax, g, lambda z: mix(INNER, 0.45) if z in cond else None, ghost=ghost, elev=24, azim=-57,
                        zoom=1.1, lw=0.15)
        fig.text((lab_w + (k + 0.5) * cw) / W, (H - 0.04) / H, name, ha="center", va="top", fontsize=7.5,
                 fontweight="bold", color=INK)
        r = gen[model]
        for i, (lab, f) in enumerate(rows):
            yy = (tab_h - 0.09 - i * 0.145) / H
            fig.text((lab_w + (k + 0.5) * cw) / W, yy, f(r), ha="center", va="center", fontsize=7.2, color=INK)
            if k == 0:
                fig.text(0.0, yy, lab, ha="left", va="center", fontsize=7, color=INK2)
        out[name] = {lab: f(r) for lab, f in rows}
    for i in range(len(rows)):
        if i % 2 == 0:
            yy = (tab_h - 0.09 - i * 0.145) / H
            fig.patches.append(Rectangle((0, yy - 0.0725 / H), 1, 0.145 / H, transform=fig.transFigure,
                                         fc="#f4f3f0", ec="none", zorder=-1))
    save(fig, "fig_generality")
    return out


FIGS = {"building_model": fig_building_model, "points": fig_points, "fault_library": fig_fault_library, "labels": fig_labels, "forecast_grid": fig_forecast_grid, "zone_maps": fig_zone_maps, "generality": fig_generality}


def main():
    args = sys.argv[1:]
    if args and args[0] == "sim_zone_maps":
        sim_zone_maps()
        return
    names = args or list(FIGS)
    for n in names:
        FIGS[n]()


if __name__ == "__main__":
    main()
