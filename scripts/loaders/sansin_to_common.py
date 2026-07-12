"""
SansinNT (Sanskrit New Testament, Sinhala script) -> common schema.

The file is USFX XML. The important thing to understand is that chapters and
verses are *milestones*, not containers:

    <c id="1" />                          <- chapter marker, self-closing
    <p style="p">
      <v id="1" bcv="MAT.1.1" />THE VERSE TEXT LIVES HERE
      <ve />
    </p>

So the verse text is NOT `v.text` -- it is `v.tail`, the text that follows the
self-closing <v/> tag. A naive `.//v` + `.text` extraction returns nothing at all.

We handle this by walking the document in order and treating <v/> as "open a new
verse" and <ve/> as "close it", accumulating any text we pass along the way. That
also correctly handles a verse whose text spans more than one <p> block.

Tag inventory of this file (counted over the whole document):
    p 7986, v 7959, ve 7959, c 260, toc 81, book/id/h 27 each, usfx/languageCode 1
There are NO footnote (<f>), cross-reference (<x>) or note tags, so nothing needs
stripping from the verse text. We only skip the book header tags: id, h, toc.

Output: data/processed/sansin_common.csv
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from common import clean_text, finalise  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
XML_PATH = REPO / "data" / "raw" / "SansinNT" / "sansin_usfx.xml"
OUT = REPO / "data" / "processed" / "sansin_common.csv"

# Book-header tags. Their text is titles/table-of-contents, not scripture, so we
# must not let it leak into a verse.
HEADER_TAGS = {"id", "h", "toc"}


def parse_verses(xml_path):
    """Walk the USFX tree and yield one dict per verse.

    Returns a list of dicts with keys: book, chapter, verse, text.
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    verses = []

    current_book = None
    current_chapter = None

    # The verse we are currently inside, or None if we are between verses.
    open_verse = None      # verse number, as a string
    open_chunks = []       # pieces of text collected for the open verse

    def close_open_verse():
        """Finish the verse we're inside (if any) and record it."""
        nonlocal open_verse, open_chunks
        if open_verse is not None:
            text = clean_text(" ".join(open_chunks))
            verses.append(
                {
                    "book": current_book,
                    "chapter": current_chapter,
                    "verse": open_verse,
                    "text": text,
                }
            )
        open_verse = None
        open_chunks = []

    # root.iter() yields every element in document order, which is exactly the
    # order the milestones appear in -- that's what makes this walk work.
    for el in root.iter():
        tag = el.tag

        if tag == "book":
            # A new book starts. Any verse still open belongs to the old book.
            close_open_verse()
            current_book = el.get("id")
            current_chapter = None

        elif tag == "c":
            close_open_verse()
            current_chapter = el.get("id")

        elif tag == "v":
            # A new verse opens. Close the previous one first (defensive: the
            # file always has <ve/>, but this keeps us correct if one is missing).
            close_open_verse()
            open_verse = el.get("id")

            # Prefer the bcv attribute ("MAT.1.1") when present -- it is the
            # authoritative book/chapter/verse triple.
            bcv = el.get("bcv")
            if bcv and bcv.count(".") == 2:
                b, c, v = bcv.split(".")
                current_book, current_chapter, open_verse = b, c, v

            # THE VERSE TEXT: it is the tail of this self-closing tag.
            if el.tail:
                open_chunks.append(el.tail)

        elif tag == "ve":
            # Verse end. Text may also trail the <ve/> tag, but that belongs
            # *after* the verse, so we ignore el.tail here and just close.
            close_open_verse()

        elif tag in HEADER_TAGS:
            # Book titles / table of contents. Skip their text entirely, but
            # their tail could still be verse text if we're mid-verse.
            if open_verse is not None and el.tail:
                open_chunks.append(el.tail)

        else:
            # Any other element (e.g. <p>). If we are inside a verse, its text
            # and tail are part of that verse -- this is what lets a verse span
            # multiple <p> blocks.
            if open_verse is not None:
                if el.text:
                    open_chunks.append(el.text)
                if el.tail:
                    open_chunks.append(el.tail)

    # End of document: close anything still open.
    close_open_verse()

    return verses


def main():
    verses = parse_verses(XML_PATH)
    print(f"  parsed {len(verses):,} verses from {XML_PATH.name}")

    raw = pd.DataFrame(verses)

    # Zero-pad chapter and verse so ids sort correctly as strings
    # (sansin_MAT_001_001 rather than sansin_MAT_1_1).
    chap = raw["chapter"].astype(str).str.zfill(3)
    vers = raw["verse"].astype(str).str.zfill(3)

    out = pd.DataFrame()
    out["id"] = "sansin_" + raw["book"] + "_" + chap + "_" + vers
    out["text"] = raw["text"]
    out["label"] = "sanskrit"
    out["source"] = "SansinNT"
    out["subcorpus"] = raw["book"]          # book code, e.g. MRK
    # Group by chapter, so a whole chapter lands in one split and near-identical
    # neighbouring verses can't straddle train/test.
    out["group_id"] = "sansin_" + raw["book"] + "_" + chap

    out, n_empty = finalise(out)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False, encoding="utf-8")

    print(f"\nSansinNT -> {OUT.relative_to(REPO)}")
    print(f"  rows written : {len(out):,}")
    print(f"  dropped empty: {n_empty:,}")
    print(f"  books        : {out['subcorpus'].nunique()}")
    print(f"  chapters     : {out['group_id'].nunique()}")


if __name__ == "__main__":
    main()
