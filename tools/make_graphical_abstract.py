"""Build paper/submission/graphical_abstract.png from the GUI screenshot and the drift figure.

    python tools/make_graphical_abstract.py          (run paper/make_figures.py and tools/make_screenshots.py first)
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.image as mpimg  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    from virtualbas.core import Building
    from virtualbas.realworld.faults import REGISTRY
    cat = Building(ROOT / "buildings/large_office").catalog
    macros = {}
    for line in (ROOT / "paper/results_macros.tex").read_text().splitlines():
        if line.startswith("\\newcommand"):
            k = line.split("{")[1].strip("\\}")
            macros[k] = line.split("}{", 1)[1].rstrip("}").replace("{,}", ",")
    fig = plt.figure(figsize=(26.56, 10.62), dpi=100)
    fig.text(0.015, 0.94, "Virtual BAS: EnergyPlus physics (inner space) + labelled real world (outer space)",
             fontsize=34, weight="bold", family="DejaVu Sans")
    fig.text(0.015, 0.835, f"{len(cat.points):,} BAS points from equipment to indoor environment, weather and grid "
             f"(standard / advanced / next-gen)\nsensor errors and {len(REGISTRY)} fault & event types - controllers act "
             f"on what they see - humans & AI inject at run time, 1x ... {macros.get('SpeedMaxK', '90,000')}x real time",
             fontsize=19.5, linespacing=1.4, color="#52514e", family="DejaVu Sans")
    ax1 = fig.add_axes([0.015, 0.0, 0.47, 0.80])
    ax1.imshow(mpimg.imread(ROOT / "paper/figures/fig_architecture.png"))
    ax1.axis("off")
    ax2 = fig.add_axes([0.505, 0.0, 0.485, 0.80])
    ax2.imshow(mpimg.imread(ROOT / "paper/figures/fig_drift_case.png"))
    ax2.axis("off")
    out = ROOT / "paper/submission/graphical_abstract.png"
    fig.savefig(out, dpi=100, facecolor="white")
    print("written", out)


if __name__ == "__main__":
    main()
