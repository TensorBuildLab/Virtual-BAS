"""Set the author of Claude's replies and decision comments to 'Claude (AI assistant)'.

Word stamps new comments with the signed-in Office account even when Application.UserName is set, so the author is
corrected in word/comments.xml afterwards. Only comments whose text starts with one of Claude's reply openings change;
the author's own comments are untouched.

    python paper/revisions/2026-11-08_LZ_review/fix_comment_authors.py
"""
import re
import shutil
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOCX = HERE / "manuscript_v1_LZ comments_with responses.docx"
ME, INI = "Claude (AI assistant)", "CL"
OPENINGS = ("Done, point by point", "Agreed.", "Agreed, the wording", "Removed from the abstract", "Done: building",
            "Edit accepted", "Edits accepted", "Deletion not accepted")


def main():
    tmp = DOCX.with_suffix(".tmp.docx")
    changed = 0
    with zipfile.ZipFile(DOCX) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/comments.xml":
                xml = data.decode("utf-8")

                def fix(m):
                    nonlocal changed
                    block = m.group(0)
                    text = "".join(re.findall(r"<w:t(?: [^>]*)?>([^<]*)</w:t>", block))
                    if text.startswith(OPENINGS):
                        changed += 1
                        block = re.sub(r'w:author="[^"]*"', f'w:author="{ME}"', block, count=1)
                        block = re.sub(r'w:initials="[^"]*"', f'w:initials="{INI}"', block, count=1)
                    return block
                xml = re.sub(r"<w:comment\b.*?</w:comment>", fix, xml, flags=re.S)
                data = xml.encode("utf-8")
            zout.writestr(item, data)
    shutil.move(tmp, DOCX)
    print(f"{changed} comments now by {ME}")


if __name__ == "__main__":
    main()
