"""The graphical abstract is Fig. 1 (architecture): copy its vector PDF and 300-dpi PNG to paper/submission/.

    python tools/make_graphical_abstract.py      (render Fig. 1 first: python tools/render_html.py)

Fig. 1 is 1625 x 1172 px, above Elsevier's minimum of 1328 x 531 px.
"""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    for ext in ("png", "pdf"):
        shutil.copy(ROOT / f"paper/figures/fig_architecture.{ext}", ROOT / f"paper/submission/graphical_abstract.{ext}")
    print("written paper/submission/graphical_abstract.{png,pdf} (= Fig. 1)")
