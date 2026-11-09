# Review round 1 - Liang Zhang's comments and edits (8 Nov 2026)

| File | What it is |
|---|---|
| `manuscript_v1_LZ comments_with responses.docx` | the reviewed version 1: every comment answered in its thread, every tracked edit accepted or rejected, with a comment on each decision |
| `manuscript_v2_clean.docx` | version 2, clean (built from `paper/manuscript.md` with the manuscript template) |
| `manuscript_v2_tracked changes.docx` | version 2 compared with version 1 (edits resolved) in Word: all text changes as tracked changes, formatting changes not shown |
| `respond_review.py`, `fix_comment_authors.py` | the scripts that wrote the replies and the comparison (Microsoft Word through COM), and set the author of the replies to "Claude (AI assistant)" |

The original reviewed file is archived in `paper/archive/v1_2026-11-08_latex/`.

## Comments

| # | Comment (short) | Response | Where |
|---|---|---|---|
| 1 | Paper too long; move details to an appendix | Main text shortened from about 8,000 to 5,700 words (-29%, figure captions excluded); about 1,800 words of detail moved to Appendices A-F and cited from the text; 18 figures remain in the main text and 11 are in the appendices | whole paper |
| 1 | Title too long | 29 to 17 words: "EmuBAS: an open-source emulator of real-world building automation systems for testing building operation and artificial intelligence" | title |
| 1 | "Virtual BAS" sounds like a type of tool | Renamed EmuBAS (emulated BAS) in paper, README, docs and GUI; package, CLI and repo URL unchanged | everywhere |
| 1 | Use the manuscript-template skill | Manuscript rebuilt with the skill (md2docx); check_format 0 FAIL | whole paper |
| 2 | Abstract background is not only about AI | Abstract and Introduction now open with testing building-operation technologies and people in real conditions; AI is one part | abstract, §1 |
| 3 | Indoor environment is also typical BAS | "extends the typical point list with ..."; standard tier includes zone temperature, CO2, occupancy | abstract, §3.3, Table A.2 |
| 4 | Validation number meaningless in abstract | Removed from abstract; kept in Experiment 1 | abstract |
| 5 | Six keywords | building automation system; building emulator; EnergyPlus co-simulation; fault injection; sensor errors; artificial intelligence | keywords |
| 6 | Related work repeats the Introduction | Test beds described once, in §2; Introduction keeps one sentence | §1, §2 |
| 7 | Do not highlight RL | "model predictive and learning-based control" throughout; RL keyword removed | whole paper |
| 8 | "RL environments" inaccurate | Gap paragraph rewritten: closed-loop interaction at every time step, as in control test beds | §2 |

## Tracked edits

| Edit | Decision |
|---|---|
| Two affiliations (University of Arizona; National Laboratory of the Rockies) and corresponding-author line | Accepted |
| CRediT statement deleted | Accepted (entered in the submission system for a single author) |
| Competing-interest statement replaced by the NSF acknowledgement (Award No. 2623038) | Accepted; the declaration of interests remains a separate submission file, as Elsevier requires |
| Generative-AI declaration deleted | **Not accepted**: Elsevier requires authors to disclose AI use in the writing process at the end of the manuscript, before the references. Kept under Elsevier's heading; delete it in `manuscript.md` if you decide otherwise |
| Formatting of the title block (superscripts, spacing) | Accepted; the template now formats the title block |
