# Review round 2 - Liang Zhang's comments of 19 Nov 2026

| File | What it is |
|---|---|
| `manuscript_v3_clean.docx` / `.pdf` | version 3, clean (built from `paper/manuscript.md` with the manuscript template; 0 format FAIL, 0 WARN) |
| `manuscript_v3_tracked changes.docx` | version 3 compared with version 2 in Word: all text changes tracked (author "Claude (AI assistant)"), formatting changes not shown |
| `factcheck/` | fact-check reports: references, citation support (claim checker), numbers |

Version 2 is archived in `paper/archive/v2_2026-11-08_emubas/`. The tracked version was made with
`python tools/compare_docx.py paper/archive/v2_2026-11-08_emubas/manuscript.docx manuscript_v3_clean.docx "manuscript_v3_tracked changes.docx"`.

## Comments and responses

| # | Comment | Response | Where |
|---|---|---|---|
| 1 | "for testing building operation and artificial intelligence" is not accurate | New title states what the tool is and what makes it different: **"EmuBAS: an open-source emulator of building automation systems with labelled real-world faults and sensor errors"** (15 words). Its uses (testing, training, benchmarking) are left to the abstract | title, cover letter, declaration |
| 2 | Add benchmarking as an important future use | New subsection 5.2 "Towards benchmarks for building operation": what can be benchmarked (FDD, control, ambient-AI/LLM operators, commercial analytics, sensing and digital twins, people), how a benchmark is defined (building, seeded scenario, point tiers, KPIs from truth, paired comparisons), contrast with control test beds; also in the contributions, Section 5.1, future work, conclusions and cover letter | §5.2 and others |
| 3 | "up to 92,000 times real time" is confusing | Highlight: "Runs in real time for live operators and AI, or 92,000 times faster for data" (76 characters). Abstract: "The clock runs in real time, so that operators and ambient AI agents can work with the building live, or up to 92,000 times faster to generate long synthetic datasets." Same wording in the conclusions and cover letter | highlights, abstract, §6 |
| 4 | Merge Section 2 into Section 1 following its logic; down-select citations; check numbering | Related work removed as a section and woven into the Introduction (problem → control test beds and FDD data → requirements → semantics and agents → people and training → EmuBAS). Six loosely related references dropped (two RL application papers, BCVTB, Modelica Buildings library, OpenAI Gym preprint, a general real-world-RL paper); an MPC review added so that learning-based control is not favoured. Sections renumber automatically (1 Introduction ... 6 Conclusions); citations are EndNote fields numbered 1-52 in order of first citation, and the reference list is contiguous 1-52 (checked in the rendered PDF) | §1 |
| 5 | Future work: more fault-model libraries, e.g. OpenStudio-fault-measure-gem | Added to §5.3, citing the repository and Kim et al. (2019), the paper that describes the fault models | §5.3 |
| 6 | Conclusions in a standard structure; move the GitHub link to the first mention of EmuBAS | Conclusions now: background → what was done → five numbered findings → implications → limitations and future work. GitHub link moved to the first mention of EmuBAS in the Introduction (not in the abstract, where Elsevier discourages links) | §6, §1 |
| 7 | No fake citations | Full fact-check with the fact-check skill: **all 52 references exist** (Crossref/OpenAlex records or publishers' pages, every DOI-bearing entry rebuilt from its Crossref record, no detail typed from memory); 64 citing sentences judged, 0 unsupported; 18 summary numbers traced to the results. Corrections made: RP-1312, Gymnasium, Mortar and report author lists and DOIs; 8 partly supported citations reworded (Mills, Fernandez, BuildingsBench, WELL v2, LLM papers, training-simulator sentence, Guideline 36 reset, FDD-review statements) and one source added (14 CFR Part 60 for aviation simulators); one inconsistency fixed (Experiment 5 / conclusion on ideal vs. biased sensors) | whole paper |

## Fact-check status (final)

- References: 52/52 exist. Automated flags left on RP-1312, CARLA, Johra 2020, Gymnasium and scikit-learn are false matches of the search (no DOI or a Crossref record with swapped names); each was verified by hand on the publisher's page (see `factcheck/factcheck_report_claims.md`).
- Citation support: 0 not supported; the partly supported items were reworded as listed above.
- Numbers: 18/18 in the title, highlights, abstract and conclusions traced to the results.
- Notes kept for your judgement: ASHRAE Guideline 36 now has a 2024 edition and Guideline 14 a 2023 edition (the paper cites the editions it used); the MCP and EnergyPlus API references cite web documentation with an access date.
