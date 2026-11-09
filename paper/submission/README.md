# Submission package - Energy and Buildings

| File | Purpose |
|---|---|
| `manuscript.docx` | manuscript in the author's manuscript template (Word; EndNote-linked citations, numbered captions and equations) |
| `manuscript.pdf` | the same manuscript exported by Microsoft Word |
| `highlights.txt` | 5 highlights (each <= 85 characters) |
| `graphical_abstract.png` | graphical abstract (2656 x 1062 px) |
| `cover_letter.pdf` / `.tex` | cover letter |
| `declaration_of_competing_interests.txt` | declaration of interests (also generate the official .docx with Elsevier's declaration tool) |

## Sources and build

The master text is `paper/manuscript.md`. Numbers from the experiments are written `{{Name}}` and filled in from
`paper/results_macros.tex`; references come from `paper/references.bib` (converted to `references.ris`).

| Step | Command | Output |
|---|---|---|
| experiment and result figures, numbers | `python paper/make_figures.py` | `paper/figures/fig_*.{pdf,png}`, `results_macros.tex`, tables |
| model and data figures | `python paper/make_figures_extra.py` | `paper/figures/fig_*.{pdf,png}` |
| diagrams | `python tools/render_html.py` | renders `paper/diagrams/*.html` to vector PDF + 300-dpi PNG |
| GUI screenshots and composites | `python tools/make_screenshots.py`, `python tools/make_gui_figures.py` | `paper/figures/gui_*.png`, `fig_gui_*` |
| references | `python tools/bib2ris.py` | `paper/references.ris` |
| manuscript | `python tools/build_manuscript.py --pdf` | `paper/manuscript.docx`, `paper/build/manuscript.pdf`, format report |
| graphical abstract | `python tools/make_graphical_abstract.py` | `graphical_abstract.png` |

`build_manuscript.py` runs the author's `manuscript-template` skill (`md2docx.py`, `check_format.py`,
`render_docx.py`); set `MANUSCRIPT_TEMPLATE_DIR` if the skill is not in the default Box folder. In Word, run EndNote >
Update Citations and Bibliography after choosing the journal's output style.

If you edit the Word file directly, it becomes the master copy of the text; rebuilding from `manuscript.md` would
overwrite those edits.

Version history: `paper/archive/` holds earlier versions; `paper/revisions/` holds each review round (reviewed file
with replies, clean and tracked-changes versions).
