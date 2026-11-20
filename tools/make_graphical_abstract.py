"""Build the graphical abstract from paper/diagrams/graphical_abstract.html (based on Fig. 1).

    python tools/make_graphical_abstract.py

Renders the diagram with tools/render_html.py (vector PDF + 300-dpi PNG) and copies both to paper/submission/.
Elsevier asks for at least 1328 x 531 px, readable at 13 x 5 cm; the design keeps text at >= 6 pt at that size.
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))


def main():
    from render_html import render
    render([ROOT / "paper/diagrams/graphical_abstract.html"])
    for ext in ("png", "pdf"):
        shutil.copy(ROOT / f"paper/figures/graphical_abstract.{ext}", ROOT / f"paper/submission/graphical_abstract.{ext}")
    print("written paper/submission/graphical_abstract.{png,pdf}")


if __name__ == "__main__":
    main()
