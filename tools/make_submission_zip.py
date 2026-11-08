"""Build paper/submission/latex_source.zip with every file the manuscript needs.

    python tools/make_submission_zip.py
"""
import re
import zipfile
from pathlib import Path

PAPER = Path(__file__).resolve().parents[1] / "paper"


def main():
    tex = (PAPER / "manuscript.tex").read_text(encoding="utf-8")
    figs = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", tex)
    tabs = re.findall(r"\\input\{(tables/[^}]+)\}", tex)
    files = ["manuscript.tex", "references.bib", "results_macros.tex", "manuscript.bbl"]
    files += [t if t.endswith(".tex") else t + ".tex" for t in tabs]
    for f in figs:
        p = Path("figures") / f
        files.append((p if p.suffix else p.with_suffix(".pdf")).as_posix())
    missing = [f for f in files if not (PAPER / f).exists()]
    if missing:
        raise SystemExit(f"missing files: {missing}")
    with zipfile.ZipFile(PAPER / "submission/latex_source.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(PAPER / f, f)
    print(f"latex_source.zip: {len(files)} files")


if __name__ == "__main__":
    main()
