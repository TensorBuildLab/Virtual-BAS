"""Compose the annotated GUI figures of the paper from the raw screenshots.

    python tools/make_screenshots.py     # 1) raw 2x screenshots -> paper/figures/gui_*.png
    python tools/make_gui_figures.py     # 2) composites -> paper/figures/fig_gui_*.pdf / .png

Every panel is a crop of a raw screenshot (device scale factor 2, so 1 CSS px = 2 image px). Crops are chosen so
that the GUI text prints at >= ~5.5 pt at the paper's full text width (5.4 in), i.e. a full-width panel shows at most
~850 CSS px of the 1440 px wide window. Numbered callouts (white numbers in filled circles) are placed in the CSS
pixel coordinates of the source page; the figure captions explain each number.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "paper"))
from figstyle import FULL_W, INK, INK2, AI, FIG, save  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

DPI = 300
DSF = 2                  # device scale factor of the raw screenshots
TITLE_H = 0.17           # in, panel title band
GAP_X = 0.10             # in, between panels in a row
GAP_Y = 0.07             # in, between rows
NOTE_H = 0.10            # in, extra gap for a panel note
MARK = AI                # callout colour (AI purple stands out on the dark navy GUI)
_cache = {}


def box_data(name):
    """DOM boxes recorded at capture time (paper/figures/gui_boxes.json), used where table rows vary in height."""
    if "boxes" not in _cache:
        _cache["boxes"] = json.loads((FIG / "gui_boxes.json").read_text())
    return _cache["boxes"][name]


def row(name, text, within=None):
    """First recorded table row / card whose text contains `text` -> dict(x0, y0, x1, y1, cy, cells)."""
    for r in box_data(name)["rows"]:
        x, y, w, h = r["b"]
        if text in r["t"] and (within is None or within[1] <= y <= within[3]):
            cells = [(c[0], c[1], c[0] + c[2], c[1] + c[3]) for c in r["cells"]]
            return dict(x0=x, y0=y, x1=x + w, y1=y + h, cy=y + h / 2, cells=cells)
    raise KeyError(f"{name}: no row containing {text!r}")


def sel(name, selector):
    x, y, w, h = box_data(name)["sel"][selector]
    return x, y, x + w, y + h


def shot(name):
    if name not in _cache:
        _cache[name] = Image.open(FIG / f"{name}.png").convert("RGB")
    return _cache[name]


class P:
    """One panel: a crop (CSS px box) of a raw screenshot plus its callouts.

    marks: list of (number, x, y) or (number, x, y, tx, ty) in CSS px of the source page; (tx, ty) adds a leader line
    from the marker to that point. letter/title go into the band above the panel.
    """

    def __init__(self, src, box, letter=None, title="", marks=(), boxes=(), masks=(), note=""):
        self.src, self.box, self.letter, self.title = src, box, letter, title
        self.masks = list(masks)   # (x0, y0, x1, y1): cut-off fragments at a crop edge, filled with the adjacent colour
        self.note = note           # small italic line printed below the panel (e.g. rows omitted between two crops)
        self.marks, self.boxes = list(marks), list(boxes)
        self.w_css, self.h_css = box[2] - box[0], box[3] - box[1]


def compose(name, rows, width=FULL_W, show=False):
    """rows: list of rows; a row is a list of panels or of columns (lists of panels stacked vertically).

    All panels of a row share one scale (in per CSS px) chosen to fill the width. Returns scales (pt/CSS px).
    """
    layout, y, scales = [], 0.0, []
    for row in rows:
        cols = [c if isinstance(c, list) else [c] for c in row]
        col_w = [max(p.w_css for p in c) for c in cols]
        s = (width - GAP_X * (len(cols) - 1)) / sum(col_w)     # inches per CSS px
        scales.append(s * 72)
        x, row_h = 0.0, 0.0
        for c, cw in zip(cols, col_w):
            yy = y
            for p in c:
                th = TITLE_H if (p.letter or p.title) else 0.0
                layout.append((p, x, yy + th, p.w_css * s, p.h_css * s, s))
                yy += th + p.h_css * s + GAP_Y + (NOTE_H if p.note else 0.0)
            row_h = max(row_h, yy - y)
            x += cw * s + GAP_X
        y += row_h
    H = y - GAP_Y
    fig = plt.figure(figsize=(width, H))
    for p, x, yy, w, h, s in layout:
        ax = fig.add_axes([x / width, 1 - (yy + h) / H, w / width, h / H])
        x0, y0, x1, y1 = p.box
        im = shot(p.src).crop((x0 * DSF, y0 * DSF, x1 * DSF, y1 * DSF))
        for mx0, my0, mx1, my1 in p.masks:
            box = ((mx0 - x0) * DSF, (my0 - y0) * DSF, (mx1 - x0) * DSF, (my1 - y0) * DSF)
            im.paste(im.getpixel((max(0, box[0] - 3), box[1] + 2)), box)
        im = im.resize((max(1, round(w * DPI)), max(1, round(h * DPI))), Image.LANCZOS)
        ax.imshow(np.asarray(im), extent=(x0, x1, y1, y0), interpolation="none", aspect="auto")
        ax.set_xlim(x0, x1)
        ax.set_ylim(y1, y0)
        ax.set_axis_off()
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec="#9a9a96", lw=0.4, clip_on=False))
        if p.letter or p.title:
            lab = f"({p.letter})" if p.letter else ""
            fig.text(x / width, 1 - (yy - 0.035) / H, lab, fontsize=8.5, fontweight="bold", color=INK, va="bottom",
                     ha="left")
            if p.title:
                fig.text((x + (0.24 if p.letter else 0)) / width, 1 - (yy - 0.035) / H, p.title, fontsize=7.5,
                         color=INK2, va="bottom", ha="left")
        for b in p.boxes:                      # highlight rectangles (x0, y0, x1, y1) in CSS px
            ax.add_patch(Rectangle((b[0], b[1]), b[2] - b[0], b[3] - b[1], fill=False, ec=MARK, lw=1.0,
                                   ls=(0, (3, 1.5)), clip_on=False))
        if p.note:
            fig.text(x / width + 0.01, 1 - (yy + h + GAP_Y * 0.5 + NOTE_H * 0.5) / H, p.note, fontsize=6.5,
                     style="italic", color=INK2, va="center", ha="left")
        for m in p.marks:
            n, mx, my = m[:3]
            if len(m) == 5:
                ax.annotate("", xy=(m[3], m[4]), xytext=(mx, my),
                            arrowprops=dict(arrowstyle="-", color=MARK, lw=0.9, shrinkA=4.5, shrinkB=0))
                ax.plot([m[3]], [m[4]], "o", ms=2.2, color=MARK, mec="white", mew=0.4, clip_on=False)
            ax.text(mx, my, str(n), ha="center", va="center", fontsize=6.3, fontweight="bold", color="white",
                    clip_on=False, zorder=10,
                    bbox=dict(boxstyle="circle,pad=0.22", fc=MARK, ec="white", lw=0.6))
    save(fig, name)
    print(f"  {name}: {width:.2f} x {H:.2f} in; scales (pt per CSS px) " + ", ".join(f"{s:.2f}" for s in scales))
    return scales


# =============================================================================================== figures
def fig_overview():
    hdr = P("gui_overview", (0, 0, 905, 110), "a", "Header bar: simulation clock and time control, alarm banner",
            marks=[(1, 229, 12), (2, 412, 35), (3, 618, 12), (4, 836, 12), (5, 600, 95), (6, 763, 68, 742, 87)],
            masks=[(884, 78, 905, 110)])
    k = lambda x0, x1, **kw: P("gui_overview", (x0, 176, x1, 231), **kw)  # noqa: E731
    kpis = [k(205, 398, letter="c", title="KPI tiles"), k(397, 621, marks=[(7, 591, 191)]), k(620, 846), k(845, 1023),
            k(1022, 1195)]
    sec = P("gui_overview", (205, 238, 921, 625), "b", "Building section (zone tiles per floor)",
            marks=[(8, 879, 535), (9, 622, 262)])
    ahu = P("gui_ahu", (220, 188, 1135, 605), "d", "Air-handling unit graphic (AHU-1)",
            marks=[(10, 800, 300, 839, 327), (11, 744, 386), (12, 870, 568, 870, 549)])
    return compose("fig_gui_overview", [[hdr], [sec, kpis], [ahu]])


def fig_drift():
    tog = P("gui_vav", (1198, 4, 1330, 68), "a", "Truth switch",
            marks=[(1, 1220, 22)])
    zone = P("gui_vav", (660, 410, 1122, 620), "b", "VAV-Core_mid graphic: zone values",
             marks=[(2, 679, 484)])
    term = P("gui_vav", (1155, 187, 1424, 474), "c", "Terminal status",
             marks=[(3, 1288, 211), (4, 1290, 426)])
    tr = P("gui_trends", (526, 182, 1422, 702), "d", "Trends, 7-day window, truth overlay on",
           marks=[(5, 1200, 330, 1200, 362), (6, 1200, 462, 1200, 421), (7, 1360, 598, 1360, 636), (8, 1052, 206)])
    return compose("fig_gui_drift", [[[tog, zone], term], [tr]])


def fig_environment():
    heat = P("gui_zone", (184, 232, 1064, 568), "a", "Zones & IEQ: heat-map of all zones (PM2.5 metric)",
             marks=[(1, 612, 258), (2, 470, 320), (3, 466, 287)])
    therm = P("gui_zone", (184, 807, 618, 1197), "b", "Thermal comfort (ZN-Core_mid)",
              marks=[(4, 333, 850), (5, 604, 1007)])
    light = P("gui_zone", (184, 1209, 618, 1451), "d", "Light and sound", marks=[(6, 600, 1368)])
    iaq = P("gui_zone", (630, 807, 1064, 1139), "c", "Indoor air quality",
            marks=[(7, 958, 921), (8, 1046, 1080)])
    occ = P("gui_zone", (630, 1209, 1064, 1449), "e", "Occupancy and occupant feedback",
            marks=[(9, 728, 1300), (10, 1040, 1258), (11, 1030, 1373)])
    return compose("fig_gui_environment", [[heat], [[therm, light], [iaq, occ]]])


def fig_weather():
    ban = P("gui_weather", (184, 222, 1064, 360), "a", "Utility and air-quality event banners",
            marks=[(1, 1045, 255), (2, 1045, 328)])
    aq = P("gui_weather", (184, 641, 618, 928), "b", "Outdoor air quality",
           marks=[(3, 590, 697), (4, 575, 778)])
    grid = P("gui_weather", (184, 1326, 618, 1562), "c", "Grid and tariff signals",
             marks=[(5, 372, 1480), (6, 440, 1525)])
    fc = P("gui_weather", (184, 940, 1064, 1314), "d", "48-h weather forecast vs. realised weather",
           marks=[(7, 497, 1022), (8, 900, 1100, 900, 1062)])
    return compose("fig_gui_weather", [[ban], [aq, grid], [fc]])


def fig_faults():
    F = "gui_faults"
    r11, r6, r5, r1 = (row(F, k) for k in ("inj-0011", "inj-0006", "inj-0005", "inj-0001"))
    sev = r11["cells"][9]
    tab = P(F, (184, 346, 1064, r5["y1"] + 1), "a", "Injection log: every fault and event is a ground-truth label",
            note="(rows inj-0004 ... inj-0002 not shown: filter fouling, stuck VAV damper, chiller fouling)",
            marks=[(1, 645, 372), (2, r5["cells"][6][0] - 11, r5["cy"]), (3, sev[2] - 14, r11["y0"] - 21),
                   (4, r6["cells"][3][0] - 26, r6["cy"])])
    tab_b = P(F, (184, r1["y0"] - 1, 1064, r1["y1"] + 3), marks=[(5, r1["cells"][7][0] + 30, r1["cy"])])
    cat_top = sel(F, ".catalog")[1]
    stuck = row(F, "sensor_stuck")
    cat = P(F, (184, cat_top, 712, stuck["y1"] + 6), "b", "Fault and event catalogue (sensor layer)",
            marks=[(6, 585, cat_top + 12), (7, 600, cat_top + 37)])
    form = sel(F, "#inj-form")
    tgt = row(F, "Target", within=form)
    start = row(F, "Start", within=form)
    par = row(F, "rate_per_day", within=form)          # the parameters fieldset
    f_top = P(F, (724, form[1], 1064, tgt["y0"] - 4), "c", "Injection form for the selected type",
              marks=[(8, 1035, form[1] + 17)])
    f_bot = P(F, (724, start["y0"] - 8, 1064, par["y1"] + 8),
              marks=[(9, 1040, start["y0"] + 8), (10, 830, par["y0"] + 3)])
    return compose("fig_gui_faults", [[tab], [tab_b], [cat, [f_top, f_bot]]])


def fig_operations():
    A = "gui_alarms"
    act = sel(A, "#al-active")
    rows = [r for r in box_data(A)["rows"] if act[1] <= r["b"][1] <= act[3]]
    first3_bottom = rows[2]["b"][1] + rows[2]["b"][3]
    top4 = [row(A, k, within=act) for k in ("AHU-4:SAT-DEV", "AHU-4:FAN-FAIL", "WX:OA-PM25", "GRID:DR")]
    n_skip = len(rows) - 3 - 4
    r1, fan, wx = row(A, rows[0]["t"][:30], within=act), top4[1], top4[2]
    al_a = P(A, (176, 186, 1064, first3_bottom + 1), "a", "Alarm server (rules on observed values only)",
             note=f"({n_skip} further zone PM2.5 alarms raised by the smoke event not shown)",
             marks=[(1, 632, 204), (2, 1046, r1["cy"])])
    al_b = P(A, (176, top4[0]["y0"] - 1, 1064, top4[3]["y1"] + 6),
             marks=[(3, fan["cells"][1][0] - 12, fan["cy"]), (4, 1046, wx["cy"])])
    dlg = P("gui_point_dialog", (90, 168, 990, 490), "b", "Point dialog with BACnet-style priority array",
            marks=[(5, 230, 262), (6, 903, 257), (7, 780, 422)])
    return compose("fig_gui_operations", [[al_a], [al_b], [dlg]])


def fig_points():
    T = "gui_points"
    occ, cold = row(T, "ZN-Core_mid/OCC-COUNT"), row(T, "ZN-Core_mid/COLD-CALLS")
    st, tr = occ["cells"][5], occ["cells"][6]
    hy = occ["y0"] - 20
    tiers = P("gui_points_tiers", (184, 222, 1064, 358), "a", "Point availability tiers and filters",
              marks=[(1, 826, 240), (2, 1048, 240), (3, 910, 340)])
    tab = P(T, (212, hy - 12, 1120, cold["y1"] + 2), "b", "Point explorer: ZN-Core_mid, next-generation tier",
            marks=[(4, 285, hy + 1), (5, occ["cells"][4][0] - 20, hy + 1),
                   (6, (st[0] + st[2]) / 2, occ["cy"], tr[2] - 40, occ["cy"]),
                   (7, (st[0] + st[2]) / 2, cold["cy"])])
    return compose("fig_gui_points", [[tiers], [tab]])


FIGS = {"overview": fig_overview, "drift": fig_drift, "environment": fig_environment, "weather": fig_weather,
        "faults": fig_faults, "operations": fig_operations, "points": fig_points}

if __name__ == "__main__":
    which = sys.argv[1:] or list(FIGS)
    for k in which:
        FIGS[k]()
