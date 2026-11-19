"""Make a tracked-changes Word file by comparing two versions of the manuscript with Microsoft Word (Windows).

    python tools/compare_docx.py OLD.docx NEW.docx OUT.docx [--author "Claude (AI assistant)"]

Text changes become tracked insertions and deletions by --author; formatting-only changes are not marked. Word is run
hidden and always quit without saving, so it can never wait on an invisible dialog.
"""
import argparse
import shutil
import tempfile
from pathlib import Path

import win32com.client as win32


def compare(old, new, out, author="Claude (AI assistant)"):
    tmp = Path(tempfile.mkdtemp())
    a, b = tmp / "old.docx", tmp / "new.docx"          # private copies: Word never locks the originals
    shutil.copy(old, a)
    shutil.copy(new, b)
    word = win32.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    try:
        d1 = word.Documents.Open(str(a))
        d2 = word.Documents.Open(str(b))
        # CompareDocuments(Original, Revised, Destination=new doc, Granularity=word, CompareFormatting=False,
        #   CaseChanges, Whitespace=False, Tables, Headers, Footnotes, Textboxes, Fields=False, Comments=False,
        #   Moves=True, RevisedAuthor, IgnoreAllComparisonWarnings)
        res = word.CompareDocuments(d1, d2, 2, 1, False, True, False, True, True, True, True, False, False, True,
                                    author, True)
        n = res.Revisions.Count
        res.SaveAs2(str(Path(out).resolve()), FileFormat=16)
        for d in (res, d1, d2):
            d.Close(0)
    finally:
        word.Quit(0)
        shutil.rmtree(tmp, ignore_errors=True)
    return n


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("out")
    ap.add_argument("--author", default="Claude (AI assistant)")
    a = ap.parse_args()
    print("revisions:", compare(a.old, a.new, a.out, a.author), "->", a.out)
