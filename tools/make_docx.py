"""Build the Word version of the manuscript (paper/manuscript.docx) from paper/manuscript.tex.

    python tools/make_docx.py            (compile the LaTeX first so manuscript.aux is current)

Pandoc (pip install pypandoc_binary) converts the LaTeX body; equations become native Word equations, citations are
formatted by paper/word/elsevier-numeric.csl from paper/references.bib, figures use the 300-dpi PNG versions, and
figure, table, section and equation numbers are taken from LaTeX's manuscript.aux so they match the PDF exactly.
Styles come from paper/word/reference.docx (created on first run; edit it in Word to restyle).
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
WORD = PAPER / "word"
OUT = PAPER / "manuscript.docx"


# ---------------------------------------------------------------------------------------------- LaTeX helpers
def braced(s, i):
    """Return (content, end) of the {...} group starting at s[i] == '{'."""
    assert s[i] == "{", s[i:i + 20]
    depth = 0
    for j in range(i, len(s)):
        if s[j] == "\\":
            continue
        if s[j] == "{" and s[j - 1] != "\\":
            depth += 1
        elif s[j] == "}" and s[j - 1] != "\\":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
    raise ValueError("unbalanced braces")


def env(s, name):
    m = re.search(r"\\begin\{%s\}(.*?)\\end\{%s\}" % (re.escape(name), re.escape(name)), s, re.S)
    return m.group(1).strip() if m else ""


def labels_from_aux(aux):
    lab = {}
    for m in re.finditer(r"\\newlabel\{([^}]+)\}\{\{([^}]*)\}", aux.read_text(encoding="utf-8", errors="ignore")):
        lab[m.group(1)] = m.group(2)
    return lab


def expand_macros(s, macros):
    for k in sorted(macros, key=len, reverse=True):
        s = re.sub(r"\\%s(\{\})?(?![A-Za-z])" % k, lambda _m, v=macros[k]: v, s)
    return s


# ---------------------------------------------------------------------------------------------- preprocessing
def preprocess():
    tex = (PAPER / "manuscript.tex").read_text(encoding="utf-8")
    aux = max([PAPER / "manuscript.aux", PAPER / "ms_build.aux"], key=lambda f: f.stat().st_mtime if f.exists() else 0)
    labels = labels_from_aux(aux)          # newest LaTeX run (ms_build = build while manuscript.pdf is open)
    macros = {}
    for line in (PAPER / "results_macros.tex").read_text(encoding="utf-8").splitlines():
        m = re.match(r"\\newcommand\{\\(\w+)\}\{(.*)\}\s*$", line)
        if m:
            macros[m.group(1)] = m.group(2).replace("{,}", ",")

    title = braced(tex, tex.index("\\title{") + 6)[0]
    abstract = env(tex, "abstract")
    keywords = [k.strip() for k in env(tex, "keyword").split("\\sep")]
    body = tex[tex.index("\\end{frontmatter}") + len("\\end{frontmatter}"):tex.index("\\bibliographystyle")]
    body = body.replace("\\linenumbers", "")

    # inline \input{tables/...}
    body = re.sub(r"\\input\{(tables/[^}]+)\}",
                  lambda m: (PAPER / (m.group(1) if m.group(1).endswith(".tex") else m.group(1) + ".tex")).read_text(encoding="utf-8"),
                  body)
    body = expand_macros(body, macros)
    abstract = expand_macros(abstract, macros)

    # TikZ figure (if any is left) -> its rendered PNG
    body = re.sub(r"\\resizebox\{[^}]*\}\{!\}\{%?\s*\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}\}",
                  r"\\includegraphics[width=\\linewidth]{fig_architecture.png}", body, flags=re.S)
    # figures: always the PNG; figure* -> figure; widths relative to text
    body = re.sub(r"\\includegraphics(\[[^\]]*\])?\{([^}]+?)(\.pdf|\.png)?\}",
                  lambda m: "\\includegraphics[width=\\linewidth]{figures/%s.png}" % m.group(2), body)
    body = body.replace("\\allowbreak", "")
    body = body.replace("\\textwidth", "\\linewidth").replace("figure*", "figure").replace("table*", "table")

    # equations: number them like the PDF (Word has no \label); strip labels everywhere else
    def number_eqs(m):
        envname, content = m.group(1), m.group(2)
        rows = re.split(r"\\\\", content)
        out = []
        for r in rows:
            lm = re.search(r"\\label\{([^}]+)\}", r)
            r = re.sub(r"\\label\{[^}]+\}", "", r)
            if lm and lm.group(1) in labels:
                r = r.rstrip() + r" \qquad (%s)" % labels[lm.group(1)]
            out.append(r)
        return "\\begin{%s}%s\\end{%s}" % (envname, "\\\\".join(out), envname)
    body = re.sub(r"\\begin\{(align\*?|equation\*?)\}(.*?)\\end\{\1\}", number_eqs, body, flags=re.S)

    # cross references -> numbers from the aux file
    body = re.sub(r"\\eqref\{([^}]+)\}", lambda m: "(%s)" % labels.get(m.group(1), "??"), body)
    body = re.sub(r"\\ref\{([^}]+)\}", lambda m: labels.get(m.group(1), "??"), body)
    body = re.sub(r"\\label\{[^}]+\}", "", body)

    # run-in paragraph headings -> bold lead-in (keeps Word section numbering clean)
    body = re.sub(r"\\paragraph\{([^}]*)\}\s*", r"\\textbf{\1.} ", body)
    # tabularx -> tabular with plain column types (Word decides widths)
    def tabx(m):
        spec = re.sub(r"[<>@]\{(?:[^{}]|\{[^{}]*\})*\}", "", m.group(1))   # drop >{..}, @{..}
        spec = re.sub(r"\{[^{}]*\}", "", spec)                               # drop p{..} widths
        return "\\begin{tabular}{%s}" % ("l" * len(re.findall(r"[lcrXp]", spec)))
    body = re.sub(r"\\begin\{tabularx\}\{[^}]*\}\{((?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*)\}", tabx, body)
    body = body.replace("\\end{tabularx}", "\\end{tabular}")
    body = re.sub(r"\\multicolumn\{(\d+)\}\{(?:[^{}]|\{[^{}]*\})*\}", r"\\multicolumn{\1}{l}", body)
    while "\\resizebox{" in body:                       # unwrap \resizebox{w}{h}{content}
        i = body.index("\\resizebox{")
        _, j = braced(body, i + len("\\resizebox"))
        _, j = braced(body, j)
        content, k = braced(body, j)
        body = body[:i] + content + body[k:]
    for cmd in ("\\footnotesize", "\\scriptsize", "\\small", "\\centering", "\\FloatBarrier", "\\clearpage"):
        body = body.replace(cmd, "")
    body = re.sub(r"\\renewcommand\{\\arraystretch\}\{[^}]*\}", "", body)
    body = re.sub(r"\\(begin|end)\{(figure|table)\}(\[[^\]]*\])?", lambda m: "\\%s{%s}" % (m.group(1), m.group(2)), body)
    body += "\n\\section*{References}\n"

    head = "\n".join([
        r"\documentclass{article}", r"\usepackage{amsmath,amssymb,graphicx,booktabs}",
        r"\title{" + title + "}",
        r"\author{Liang Zhang, University of Arizona, Tucson, AZ, USA (liangzhang1@arizona.edu)}",
        r"\date{}",
        r"\begin{document}", r"\maketitle", r"\begin{abstract}", abstract, r"\end{abstract}",
        body, r"\end{document}"])
    WORD.mkdir(exist_ok=True)
    (WORD / "manuscript_word.tex").write_text(head, encoding="utf-8")
    return keywords


# ---------------------------------------------------------------------------------------------- reference docx
def reference_docx(pandoc):
    ref = WORD / "reference.docx"
    if ref.exists():
        return ref
    subprocess.run([pandoc, "-o", str(ref), "--print-default-data-file", "reference.docx"], check=True)
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Inches, Pt, RGBColor
    d = Document(ref)
    for sec in d.sections:
        sec.left_margin = sec.right_margin = sec.top_margin = sec.bottom_margin = Inches(1)
    st = d.styles
    def font(name, size=None, bold=None, color=None, italic=None):
        s = st[name]
        s.font.name = "Times New Roman"
        rpr = s.element.get_or_add_rPr()
        rf = rpr.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rFonts")
        if rf is not None:
            for a in ("ascii", "hAnsi", "cs", "eastAsia"):
                rf.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}" + a, "Times New Roman")
            for a in ("asciiTheme", "hAnsiTheme", "cstheme", "eastAsiaTheme"):
                rf.attrib.pop("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}" + a, None)
        if size:
            s.font.size = Pt(size)
        if bold is not None:
            s.font.bold = bold
        if italic is not None:
            s.font.italic = italic
        s.font.color.rgb = RGBColor(0, 0, 0) if color is None else color
        return s
    for name in ("Normal", "Body Text", "First Paragraph", "Compact", "Abstract", "Bibliography", "Author", "Date"):
        if name in [x.name for x in st]:
            font(name, 12 if name != "Compact" else 11)
    for name in ("Body Text", "First Paragraph"):
        pf = st[name].paragraph_format
        pf.line_spacing = 1.5
        pf.space_after = Pt(6)
        pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    font("Title", 16, bold=True)
    for lvl, size in ((1, 14), (2, 12), (3, 12)):
        s = font(f"Heading {lvl}", size, bold=True, italic=(lvl == 3))
        s.paragraph_format.space_before = Pt(12)
        s.paragraph_format.space_after = Pt(6)
    for name in ("Caption", "Image Caption", "Table Caption"):
        if name in [x.name for x in st]:
            s = font(name, 10, italic=False)
            s.paragraph_format.space_after = Pt(10)
    if "Bibliography" in [x.name for x in st]:
        st["Bibliography"].font.size = Pt(10)
    d.save(ref)
    return ref


# ---------------------------------------------------------------------------------------------- post-processing
def postprocess(path, keywords):
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.shared import Pt
    d = Document(path)
    # keywords after the abstract
    abstract_paras = [p for p in d.paragraphs if p.style.name == "Abstract"]
    if abstract_paras:
        last = abstract_paras[-1]
        new = last._p.addnext(last._p.__class__()) if False else None  # noqa: F841
        from copy import deepcopy
        kp = deepcopy(last._p)
        last._p.addnext(kp)
        from docx.text.paragraph import Paragraph
        para = Paragraph(kp, last._parent)
        for r in list(para.runs):
            r._r.getparent().remove(r._r)
        run = para.add_run("Keywords: ")
        run.bold = True
        para.add_run("; ".join(keywords))
    # centre figures and captions; tables: booktabs-like rules, compact text
    for p in d.paragraphs:
        if p._p.xpath(".//w:drawing") or p.style.name in ("Captioned Figure", "Figure"):
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.keep_with_next = True
    for t in d.tables:
        tbl = t._tbl
        tblPr = tbl.tblPr
        borders = tblPr.find(qn("w:tblBorders"))
        if borders is None:
            borders = tblPr.makeelement(qn("w:tblBorders"), {})
            tblPr.append(borders)
        for edge in ("top", "bottom"):
            el = borders.find(qn(f"w:{edge}"))
            if el is None:
                el = borders.makeelement(qn(f"w:{edge}"), {})
                borders.append(el)
            el.set(qn("w:val"), "single")
            el.set(qn("w:sz"), "8")
            el.set(qn("w:color"), "000000")
        for row in t.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.space_after = Pt(0)
                    p.paragraph_format.line_spacing = 1.0
                    for r in p.runs:
                        r.font.size = Pt(9)
    d.save(path)


def main():
    import pypandoc
    pandoc = pypandoc.get_pandoc_path()
    keywords = preprocess()
    ref = reference_docx(pandoc)
    cmd = [pandoc, str(WORD / "manuscript_word.tex"), "-f", "latex", "-t", "docx+native_numbering",
           "--citeproc", f"--bibliography={PAPER / 'references.bib'}", f"--csl={WORD / 'elsevier-numeric.csl'}",
           f"--reference-doc={ref}", "--number-sections", f"--resource-path={PAPER}", "-o", str(OUT)]
    r = subprocess.run(cmd, cwd=PAPER, capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr)
    for line in r.stderr.splitlines():
        if "WARNING" in line.upper() and "Could not convert TeX math" not in line:
            print(line)
    postprocess(OUT, keywords)
    print("written", OUT)


if __name__ == "__main__":
    main()
