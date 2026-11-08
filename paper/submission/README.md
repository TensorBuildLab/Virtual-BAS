# Submission package - Energy and Buildings

| File | Purpose |
|---|---|
| `manuscript.pdf` | compiled manuscript (elsarticle, preprint, line numbers) |
| `latex_source.zip` | LaTeX source: `manuscript.tex`, `references.bib`, `manuscript.bbl`, `results_macros.tex`, tables, figures |
| `highlights.txt` | 5 highlights (each <= 85 characters) |
| `graphical_abstract.png` | graphical abstract (2656 x 1062 px) |
| `cover_letter.pdf` / `.tex` | cover letter |
| `declaration_of_competing_interests.txt` | declaration of interests (also generate the official .docx with Elsevier's declaration tool) |

All numbers in the manuscript are produced by `python paper/make_figures.py` from the outputs of `experiments/*.py`
(`results_macros.tex`). Rebuild: `pdflatex manuscript && bibtex manuscript && pdflatex manuscript && pdflatex manuscript`.
