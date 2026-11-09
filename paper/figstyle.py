"""Shared style for every paper figure (matplotlib charts and HTML/SVG diagrams).

Design widths match the preprint text block (390 pt = 5.4 in; text height 548 pt = 7.6 in) so text prints at 7-9 pt without scaling.
Every figure is saved twice: vector PDF (LaTeX) and 300-dpi PNG (Word, README).

Semantic colours are fixed across the paper:
    INNER  - EnergyPlus physics / ground truth          (blue)
    OUTER  - BAS / observed values / real-world layer   (orange)
    AI     - AI agents and machine interfaces           (purple)
    ENV    - weather, indoor environment                (green)
    FAULT  - injected faults and events                 (red)
    BASE   - fault-free twin, baselines, neutral        (grey)
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "paper/figures"
FIG.mkdir(parents=True, exist_ok=True)

# validated categorical palette, fixed order (see the dataviz validator); never cycled
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
INNER, OUTER, ENV, AI, FAULT = C[0], C[1], C[2], C[6], C[7]
INK, INK2, MUTED, GRID, SURFACE = "#1b1b1a", "#52514e", "#8a8984", "#e3e2de", "#ffffff"
INNER_BG, OUTER_BG, AI_BG, ENV_BG, FAULT_BG = "#eef4fc", "#fdf1ea", "#f1effc", "#e9f7f1", "#fdeeee"
# ordinal ramp for point tiers (standard -> advanced -> next-gen), truth in neutral grey
TIER = {"standard": "#1f5fae", "advanced": "#5b9be6", "next_gen": "#b5d3f5", "truth": "#bdbcb7"}
TIER_LABEL = {"standard": "Standard (typical BAS)", "advanced": "Advanced", "next_gen": "Next-generation",
              "truth": "Ground truth only"}

FONT = ["Arial", "Liberation Sans", "DejaVu Sans"]
FULL_W = 5.4      # inches, full text width (390 pt)
HALF_W = 2.6      # inches, half width

plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": FONT, "font.size": 8, "mathtext.fontset": "dejavusans",
    "axes.titlesize": 8.5, "axes.titleweight": "bold", "axes.titlelocation": "left", "axes.labelsize": 8,
    "axes.edgecolor": INK2, "axes.labelcolor": INK, "axes.linewidth": 0.6,
    "xtick.color": INK2, "ytick.color": INK2, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.5, "axes.axisbelow": True,
    "axes.spines.top": False, "axes.spines.right": False,
    "lines.linewidth": 1.3, "legend.frameon": False, "legend.fontsize": 7.5,
    "savefig.dpi": 300, "savefig.bbox": "tight", "savefig.pad_inches": 0.03, "figure.dpi": 150,
    "pdf.fonttype": 42, "ps.fonttype": 42,
})


def save(fig, name):
    """Save a matplotlib figure as paper/figures/<name>.pdf and .png (300 dpi)."""
    fig.savefig(FIG / f"{name}.pdf")
    fig.savefig(FIG / f"{name}.png", dpi=300)
    plt.close(fig)
    print("figure", name)


def panel(ax, letter, title=""):
    """Panel title '(a) title' at the top left of an axes."""
    ax.set_title(f"({letter}) {title}" if title else f"({letter})", loc="left", fontsize=8.5, fontweight="bold",
                 color=INK, pad=4)


def date_axis(ax, fmt="%a %d"):
    """Compact, horizontal date ticks (no rotated ISO dates)."""
    import matplotlib.dates as mdates
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter(fmt))
    for lab in ax.get_xticklabels():
        lab.set_rotation(0)
        lab.set_ha("center")
