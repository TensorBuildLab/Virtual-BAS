"""Build the Word manuscript from paper/manuscript.md with the manuscript-template skill.

    python tools/build_manuscript.py            -> paper/manuscript.docx (+ format report)
    python tools/build_manuscript.py --pdf      -> also paper/manuscript.pdf and page PNGs (Microsoft Word engine)

paper/manuscript.md is the master text. Numbers that come from the experiments are written {{Name}} and filled in
from paper/results_macros.tex (written by paper/make_figures.py), so the text always matches the results.
References come from paper/references.ris (python tools/bib2ris.py converts references.bib).
The template skill is looked up in $MANUSCRIPT_TEMPLATE_DIR, then in the author's Box skills folder.
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
BUILD = PAPER / "build"
SKILL_DIRS = [os.environ.get("MANUSCRIPT_TEMPLATE_DIR", ""),
              str(Path.home() / "Box/X2GO_SharedFolder/.Claude/skills/manuscript-template"),
              str(Path.home() / ".claude/skills/manuscript-template")]


def skill_dir():
    for d in SKILL_DIRS:
        if d and (Path(d) / "scripts/md2docx.py").exists():
            return Path(d)
    sys.exit("manuscript-template skill not found; set MANUSCRIPT_TEMPLATE_DIR")


def macros():
    out = {}
    for line in (PAPER / "results_macros.tex").read_text(encoding="utf-8").splitlines():
        m = re.match(r"\\newcommand\{\\(\w+)\}\{(.*)\}\s*$", line)
        if m:
            out[m.group(1)] = m.group(2).replace("{,}", ",")
    return out


def expand(text, mac):
    missing = sorted({k for k in re.findall(r"\{\{(\w+)\}\}", text) if k not in mac})
    if missing:
        sys.exit(f"undefined result macros: {missing}")
    return re.sub(r"\{\{(\w+)\}\}", lambda m: mac[m.group(1)], text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", action="store_true", help="render PDF and page PNGs with Word")
    ap.add_argument("--md", default=str(PAPER / "manuscript.md"))
    ap.add_argument("--out", default=str(PAPER / "manuscript.docx"))
    a = ap.parse_args()
    sk = skill_dir()
    BUILD.mkdir(exist_ok=True)
    src = Path(a.md)
    text = expand(src.read_text(encoding="utf-8"), macros())
    expanded = PAPER / f"_{src.stem}_expanded.md"          # next to figures/ and references.ris
    expanded.write_text(text, encoding="utf-8")
    py = sys.executable
    r = subprocess.run([py, str(sk / "scripts/md2docx.py"), str(expanded), "-o", a.out], capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode:
        sys.exit(r.stderr)
    if r.stderr.strip():
        print(r.stderr.strip())
    rep = BUILD / f"{Path(a.out).stem}_format_report.md"
    c = subprocess.run([py, str(sk / "scripts/check_format.py"), a.out, "--out", str(rep)], capture_output=True, text=True)
    print("\n".join(line for line in c.stdout.splitlines() if "FAIL" in line or "summary" in line.lower())[:3000])
    print("format report:", rep)
    if a.pdf:
        subprocess.run([py, str(sk / "scripts/render_docx.py"), a.out, "--out-dir", str(BUILD), "--png", "--update-fields"],
                       check=False)
    expanded.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
