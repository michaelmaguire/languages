#!/usr/bin/env python3
"""Step 1: turn every course document into plain text.

Reads  ../raw/*.docx, *.pdf
Writes cache/lesson_text/<file name>.txt   (only for new or changed files)
       etc/lesson_sources.csv                  (adds a row for every file it has not seen before)

Scanned PDFs and image-only Word files are OCR'd with tesseract (ita+deu, so
that ü and ö survive).  Standard library only.
"""
import csv, hashlib, json, re, subprocess, sys, tempfile, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from paths import RAW as SRC, ETC, CACHE as CACHE_DIR

CACHE = CACHE_DIR / "lesson_text"
INDEX = CACHE_DIR / "extract_index.json"
MANIFEST = ETC / "lesson_sources.csv"
MANIFEST_FIELDS = ["file", "variety", "canonical", "layout", "include", "notes"]
OCR_LANGS = "ita+deu"

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
MC = "{http://schemas.openxmlformats.org/markup-compatibility/2006}"
CELL_SEP = " ¦ "  # between paragraphs inside one table cell


def ocr_image(path):
    r = subprocess.run(["tesseract", str(path), "-", "-l", OCR_LANGS, "--psm", "3"],
                       capture_output=True, text=True)
    return r.stdout


def para_text(p, boxes):
    """Text of one paragraph. Text boxes anchored in it are collected separately."""
    out = []

    def walk(e):
        for c in e:
            if c.tag == MC + "Fallback":      # duplicate rendering of a text box
                continue
            if c.tag == W + "txbxContent":
                boxes.extend(para_text(q, boxes) for q in c.iter(W + "p"))
                continue
            if c.tag == W + "t":
                out.append(c.text or "")
            elif c.tag == W + "tab":
                out.append("\t")
            elif c.tag in (W + "br", W + "cr"):
                out.append("\n")
            else:
                walk(c)

    walk(p)
    return "".join(out)


def docx_text(path):
    z = zipfile.ZipFile(path)
    body = ET.fromstring(z.read("word/document.xml")).find(W + "body")
    lines = []

    def walk(e):
        for c in e:
            if c.tag == W + "p":
                boxes = []
                lines.append(para_text(c, boxes))
                lines.extend(boxes)
            elif c.tag == W + "tbl":
                for row in c.iter(W + "tr"):
                    cells = []
                    for tc in row.findall(W + "tc"):
                        boxes = []
                        paras = [para_text(p, boxes).strip() for p in tc.iter(W + "p")]
                        cells.append(CELL_SEP.join(x for x in paras + boxes if x))
                    lines.append("| " + " | ".join(cells))
            else:
                walk(c)

    walk(body)
    text = "\n".join(lines)
    if len(text.split()) < 20:               # image-only document: OCR the pictures
        with tempfile.TemporaryDirectory() as tmp:
            for name in sorted(n for n in z.namelist() if n.startswith("word/media/")):
                img = Path(tmp) / Path(name).name
                img.write_bytes(z.read(name))
                text += "\n" + ocr_image(img)
        return text, "ocr"
    return text, "text"


def looks_like_text(text):
    words = text.split()
    if len(words) < 20:
        return False
    letters = sum(ch.isalpha() for ch in text)
    return letters / max(1, len(text.replace(" ", "").replace("\n", ""))) > 0.6


def pdf_text(path):
    text = subprocess.run(["pdftotext", "-layout", str(path), "-"],
                          capture_output=True, text=True).stdout
    if looks_like_text(text):
        return text, "text"
    pages = []
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["pdftoppm", "-r", "300", "-gray", "-png", str(path), f"{tmp}/p"], check=True)
        for img in sorted(Path(tmp).glob("p-*.png")):
            pages.append(ocr_image(img))
    return "\n\f\n".join(pages), "ocr"


def main():
    from paths import raw_available
    if not raw_available():
        sys.exit("step 1: no source documents in raw/ (the submodule is not checked out); nothing to extract")
    CACHE.mkdir(parents=True, exist_ok=True)
    index = json.loads(INDEX.read_text()) if INDEX.exists() else {}
    files = sorted(p for p in SRC.iterdir() if p.suffix.lower() in (".docx", ".pdf"))
    for path in files:
        digest = hashlib.sha1(path.read_bytes()).hexdigest()
        out = CACHE / (path.name + ".txt")
        if index.get(path.name, {}).get("sha1") == digest and out.exists():
            continue
        print("extracting", path.name, flush=True)
        try:
            text, how = (docx_text if path.suffix.lower() == ".docx" else pdf_text)(path)
        except Exception as e:                # keep going; report at the end
            print("  FAILED:", e)
            continue
        text = re.sub(r"[ \t]+\n", "\n", text.replace(" ", " "))
        out.write_text(text)
        index[path.name] = {"sha1": digest, "how": how, "words": len(text.split()),
                            "text_sha1": hashlib.sha1(text.encode()).hexdigest()}
        INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=1))

    # manifest: keep the user's rows, add anything new
    rows = list(csv.DictReader(MANIFEST.open())) if MANIFEST.exists() else []
    known = {r["file"] for r in rows}
    seen_text = {}
    for r in rows:
        if r["file"] in index:
            seen_text.setdefault(index[r["file"]]["text_sha1"], r["file"])
    new = 0
    for path in files:
        if path.name in known or path.name not in index:
            continue
        info = index[path.name]
        dup = seen_text.get(info["text_sha1"])
        seen_text.setdefault(info["text_sha1"], path.name)
        rows.append({"file": path.name, "variety": "?", "canonical": "?",
                     "layout": "skip" if dup else "auto",
                     "include": "no" if dup else "yes",
                     "notes": f"duplicate of {dup}" if dup else "NEW - please check variety and layout"})
        new += 1
    with MANIFEST.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"{len(files)} source files, {new} new in etc/lesson_sources.csv")


if __name__ == "__main__":
    sys.exit(main())
