"""Answer the author's review of version 1 inside the reviewed Word file, then build the tracked-changes comparison.

    python paper/revisions/2026-11-08_LZ_review/respond_review.py

Uses Microsoft Word through COM (Windows). Steps:
1. open 'manuscript_LZ comments and edits.docx' (archived in paper/archive/v1_2026-11-08_latex/);
2. resolve the author's tracked edits: accept all, except the deletion of the generative-AI declaration (rejected);
3. reply to each of the author's comments in its thread, and add one comment per edit decision;
4. save 'manuscript_v1_LZ comments_with responses.docx';
5. compare that file (edits resolved) with the clean version 2 and save 'manuscript_v2_tracked changes.docx'.
"""
import shutil
import sys
from pathlib import Path

import win32com.client as win32

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REVIEW = ROOT / "paper/archive/v1_2026-11-08_latex/manuscript_LZ comments and edits.docx"
RESPONSES = HERE / "manuscript_v1_LZ comments_with responses.docx"
CLEAN = HERE / "manuscript_v2_clean.docx"
TRACKED = HERE / "manuscript_v2_tracked changes.docx"
ME, ME_INI = "Claude (AI assistant)", "CL"

# reply to each author comment, keyed by the start of the comment text
REPLIES = {
    "The whole paper too long": (
        "Done, point by point. (1) Length: the main text was shortened from about 8,000 to 5,700 words (-29%, "
        "figure captions excluded) and ends on page 35 of the double-spaced template layout. Moved to appendices and "
        "cited from the main text: BAS-ization details with the "
        "transformation and point tables (Appendix A); the full sensor, occupancy, light, sound, comfort and forecast "
        "models (B); the control-program details (C); the labelled data products (D); five GUI views and the speed "
        "figure (E); and the table of 18 uses (F). Related work, method and discussion were condensed. (2) Title "
        "shortened from 29 to 17 words: 'EmuBAS: an open-source emulator of real-world building automation systems "
        "for testing building operation and artificial intelligence'. (3) Name: 'EmuBAS' (emulated BAS), a proper "
        "name rather than a type of tool; a web search found no existing tool with this name. It is used in the paper, "
        "README, docs and GUI; the Python package (virtualbas), the CLI (vbas) and the repository URL are unchanged, so "
        "existing installs keep working. (4) Reformatted with the manuscript-template skill: the manuscript is now built "
        "from paper/manuscript.md with md2docx (Times 12 pt, double spacing, Fig./Table captions, numbered equations, "
        "EndNote-linked citations); check_format reports 0 FAIL. Note: Energy and Buildings suggests about 20 "
        "double-spaced pages; the main text has 35 pages including 18 figures, so further cuts are possible if you "
        "want them (e.g. moving Experiments 7 and 8 or the GUI figure to the appendix)."),
    "I think you do not introduce the background": (
        "Agreed. The abstract now opens with building-operation technologies in general (control sequences, fault "
        "detection and diagnosis, analytics and, increasingly, AI agents) and the people who operate buildings, all of "
        "which must be tested under real-world conditions; AI is one of them. The first paragraph of the Introduction "
        "was reframed the same way."),
    "Indoor environment also belong": (
        "Agreed. The abstract now says that the point list extends the typical point list with particles, volatile "
        "organic compounds, light, sound, comfort indices, occupant feedback, forecasts and grid signals. Section 3.3 "
        "states that the standard tier includes the zone temperature, CO2 and occupancy sensors through which a "
        "typical BAS already observes the indoor environment, and Table A.2 lists them as standard points."),
    "This number is meaningless": (
        "Removed from the abstract. The verification result remains in Experiment 1 (Table 1, Fig. 10) and in the "
        "Conclusions."),
    "Reduce to 6 most important": (
        "Done: building automation system; building emulator; EnergyPlus co-simulation; fault injection; sensor "
        "errors; artificial intelligence."),
    "Some content here is repeated": (
        "Agreed. The Introduction now states the gap in one sentence and points to Section 2; BCVTB, BOPTEST, the "
        "Advanced Controls Test Bed, Energym, Sinergym and CityLearn are described once, in Section 2."),
    "Do not highlight RL, there and many others such as MCP": None,  # placeholder, replaced below
}
REPLY_RL = (
    "Agreed. RL is no longer singled out: the paper speaks of control sequences, model predictive and learning-based "
    "control throughout, the keyword 'Reinforcement learning' was removed, and Section 2 describes the Gym-style "
    "interfaces as serving learning-based control in general.")
REPLY_RL_ENV = (
    "Agreed, the wording was inaccurate. The Gap paragraph now says that EmuBAS, like the control test beds, lets "
    "external programs interact with the building in closed loop at every time step; the Gymnasium interface is "
    "described as one of five interfaces, for learning-based and other programmatic controllers.")

# one comment per edit decision: (text to anchor on, after the edits are resolved; comment)
DECISIONS = [
    ("Liang Zhang", "Edit accepted: two affiliations (1 University of Arizona; 2 National Laboratory of the Rockies, "
     "Golden, CO) and the corresponding-author line, in the template's title-block format."),
    ("Acknowledgement", "Edits accepted: the CRediT statement was deleted (it is entered in the submission system "
     "for a single-author paper), and the NSF acknowledgement (Award No. 2623038) replaces the competing-interest "
     "statement, verbatim, under the template heading 'Acknowledgements'. The declaration of competing interests "
     "remains a separate submission file (paper/submission/declaration_of_competing_interests.txt), as Elsevier "
     "requires it at submission."),
    ("Declaration of generative AI", "Deletion not accepted (kept): Elsevier's policy on generative AI requires "
     "authors who used AI tools in the writing process to disclose it in a statement at the end of the manuscript, "
     "before the references; AI assisted with drafting this manuscript. Version 2 keeps the statement under "
     "Elsevier's heading 'Declaration of generative AI and AI-assisted technologies in the writing process'. If you "
     "decide otherwise, please delete it in manuscript.md."),
]


def find(doc, text):
    rng = doc.Content
    f = rng.Find
    f.ClearFormatting()
    if f.Execute(FindText=text[:250], MatchCase=True, Forward=True, Wrap=0):
        return rng
    return None


def main():
    if not CLEAN.exists():
        sys.exit("build version 2 first (python tools/build_manuscript.py) and copy it to " + str(CLEAN))
    work = HERE / "_work.docx"
    shutil.copy(REVIEW, work)
    word = win32.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    old_user, old_ini = word.UserName, word.UserInitials
    try:
        word.UserName, word.UserInitials = ME, ME_INI
        doc = word.Documents.Open(str(work))
        doc.TrackRevisions = False
        # 2. resolve tracked edits
        keep_ai = ("During the preparation of this work", "Declaration of generative AI")
        acc = rej = 0
        for i in range(doc.Revisions.Count, 0, -1):
            rev = doc.Revisions(i)
            text = rev.Range.Text
            if rev.Type == 2 and any(k in text for k in keep_ai):      # wdRevisionDelete of the AI declaration
                rev.Reject()
                rej += 1
            else:
                rev.Accept()
                acc += 1
        print(f"tracked edits: {acc} accepted, {rej} rejected")
        # 3a. replies in the author's comment threads
        n = 0
        originals = [doc.Comments(i) for i in range(1, doc.Comments.Count + 1)]   # replies shift the indices
        for c in originals:
            if c.Author == ME or c.Ancestor is not None:
                continue
            text = c.Range.Text.strip()
            scope = c.Scope.Text.strip()
            if text.startswith("Do not highlight RL"):
                reply = REPLY_RL_ENV if "RL environments" in scope or "not a right wording" in text else REPLY_RL
            else:
                reply = next((v for k, v in REPLIES.items() if v and text.startswith(k)), None)
            if reply is None:
                print("NO REPLY FOR:", text[:80])
                continue
            c.Replies.Add(c.Range, reply)
            n += 1
        print(f"replies added: {n}")
        # 3b. decision comments on the resolved edits
        for anchor, note in DECISIONS:
            rng = find(doc, anchor)
            if rng is None:
                print("anchor not found:", anchor)
                continue
            doc.Comments.Add(rng, note)
        doc.SaveAs2(str(RESPONSES), FileFormat=16)
        doc.Close(False)
        # 5. tracked comparison: version 1 (edits resolved) -> version 2
        d1 = word.Documents.Open(str(RESPONSES), ReadOnly=True)
        d2 = word.Documents.Open(str(CLEAN), ReadOnly=True)
        res = word.CompareDocuments(d1, d2, 2, 1, False, True, False, True, True, True, True, False, False, True, ME, True)
        res.SaveAs2(str(TRACKED), FileFormat=16)
        print("revisions in comparison:", res.Revisions.Count)
        for d in (res, d1, d2):
            d.Close(False)
    finally:
        word.UserName, word.UserInitials = old_user, old_ini
        word.Quit()
        work.unlink(missing_ok=True)
    print("written:", RESPONSES.name, "and", TRACKED.name)


if __name__ == "__main__":
    main()
