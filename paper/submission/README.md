# Submission package - Energy and Buildings

| File | Purpose |
|---|---|
| `manuscript.pdf` | compiled manuscript (elsarticle, preprint, line numbers) |
| `manuscript.docx` | the same manuscript as an editable Word document (native Word equations, numbered captions, references) |
| `latex_source.zip` | LaTeX source: `manuscript.tex`, `references.bib`, `manuscript.bbl`, `results_macros.tex`, tables, figures |
| `highlights.txt` | 5 highlights (each <= 85 characters) |
| `graphical_abstract.png` | graphical abstract (2656 x 1062 px) |
| `cover_letter.pdf` / `.tex` | cover letter |
| `declaration_of_competing_interests.txt` | declaration of interests (also generate the official .docx with Elsevier's declaration tool) |

## How the figures and documents are built

| Step | Command | Output |
|---|---|---|
| experiment and result figures, numbers | `python paper/make_figures.py` | `paper/figures/fig_*.{pdf,png}`, `results_macros.tex`, tables |
| model and data figures (building, points, faults, labels, forecasts, maps) | `python paper/make_figures_extra.py` | `paper/figures/fig_*.{pdf,png}` |
| diagrams (architecture, step sequence, BAS-ization, interfaces, ...) | `python tools/render_html.py` | renders `paper/diagrams/*.html` to vector PDF + 300-dpi PNG |
| GUI screenshots | `python tools/make_screenshots.py` | `paper/figures/gui_*.png`, `fig_gui_*` |
| PDF | in `paper/`: `pdflatex manuscript && bibtex manuscript && pdflatex manuscript && pdflatex manuscript` | `manuscript.pdf` |
| Word | `python tools/make_docx.py` (after the PDF, it reads `manuscript.aux` for numbering) | `paper/manuscript.docx` |
| package | `python tools/make_graphical_abstract.py`, `python tools/make_submission_zip.py` | this folder |

All figures share one style (`paper/figstyle.py`): fonts, sizes and semantic colours (blue = EnergyPlus truth,
orange = BAS / observed, purple = AI, green = environment, red = faults). Word-only tools: `pip install pypandoc_binary
python-docx playwright`; `tools/docx_to_pdf.ps1` exports the Word file to PDF through Microsoft Word for checking.

If you edit the Word file directly, it becomes the master copy of the text; regenerating it from LaTeX would overwrite
those edits.
