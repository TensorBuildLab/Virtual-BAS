"""Convert paper/references.bib to paper/references.ris for the manuscript template (EndNote-linked citations).

    python tools/bib2ris.py

The RIS `ID` of each record is the BibTeX key, so the manuscript cites [@key] exactly as before.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCENTS = {r"\'e": "é", r"\'a": "á", r"\'o": "ó", r"\'i": "í", r"\"o": "ö", r"\"u": "ü", r"\"a": "ä", r"\~a": "ã",
           r"\~n": "ñ", r"\`e": "è", r"\c{c}": "ç"}
TYPES = {"article": "JOUR", "inproceedings": "CPAPER", "techreport": "RPRT", "book": "BOOK", "misc": "GEN",
         "phdthesis": "THES", "incollection": "CHAP"}


def clean(v):
    v = re.sub(r"\$_?\{?(\d)\}?\$", r"\1", v)            # CO$_2$ -> CO2
    v = re.sub(r"\\url\{([^}]*)\}", r"\1", v)
    for k, a in ACCENTS.items():
        v = v.replace("{" + k + "}", a).replace(k, a)
    v = v.replace("--", "–").replace(r"\&", "&").replace("~", " ")
    v = re.sub(r"[{}]", "", v)
    return re.sub(r"\s+", " ", v).strip()


def entries(text):
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", text):
        kind, key, i = m.group(1).lower(), m.group(2), m.end()
        depth, j = 1, i
        while depth:
            depth += {"{": 1, "}": -1}.get(text[j], 0)
            j += 1
        body = text[i:j - 1]
        fields, k = {}, 0
        for fm in re.finditer(r"(\w+)\s*=\s*", body):
            if fm.start() < k:
                continue
            name, s = fm.group(1).lower(), fm.end()
            if body[s] == "{":
                d, e = 0, s
                while True:
                    d += {"{": 1, "}": -1}.get(body[e], 0)
                    e += 1
                    if d == 0:
                        break
                fields[name], k = body[s + 1:e - 1], e
            else:
                e = re.search(r"[,\n]|$", body[s:]).start() + s
                fields[name], k = body[s:e].strip(), e
        yield kind, key, fields


def to_ris(kind, key, f):
    lines = [f"TY  - {TYPES.get(kind, 'GEN')}", f"ID  - {key}"]
    for a in re.split(r"\s+and\s+", f.get("author", "")):
        a = a.strip()
        if a and a != "others":
            lines.append(f"AU  - {clean(a)}")
    lines.append(f"TI  - {clean(f.get('title', ''))}")
    if "journal" in f:
        lines.append(f"T2  - {clean(f['journal'])}")
    if "booktitle" in f:
        lines.append(f"T2  - {clean(f['booktitle'])}")
    lines.append(f"PY  - {clean(f.get('year', ''))}")
    for tag, name in (("VL", "volume"), ("IS", "number" if kind == "article" else "_"), ("DO", "doi"),
                      ("PB", "publisher"), ("PB", "institution"), ("CY", "address"), ("UR", "url")):
        if name in f:
            lines.append(f"{tag}  - {clean(f[name])}")
    if kind == "techreport" and "number" in f:
        lines.append(f"M1  - {clean(f['number'])}")
    if "pages" in f:
        p = clean(f["pages"]).split("–")
        lines.append(f"SP  - {p[0]}")
        if len(p) > 1:
            lines.append(f"EP  - {p[1]}")
    if "howpublished" in f:
        hp = clean(f["howpublished"])
        lines.append(f"UR  - {hp}" if hp.startswith("http") else f"PB  - {hp}")
    if "note" in f:
        lines.append(f"N1  - {clean(f['note'])}")
    return "\n".join(lines + ["ER  - ", ""])


def main():
    text = (ROOT / "paper/references.bib").read_text(encoding="utf-8")
    recs = [to_ris(*e) for e in entries(text)]
    (ROOT / "paper/references.ris").write_text("\n".join(recs), encoding="utf-8")
    print(f"references.ris: {len(recs)} records")


if __name__ == "__main__":
    main()
