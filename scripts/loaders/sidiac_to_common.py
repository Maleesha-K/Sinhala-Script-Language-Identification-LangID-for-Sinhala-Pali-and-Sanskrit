"""
SiDiaC (historical/diachronic Sinhala, OCR'd from PDFs) -> common schema.

Layout on disk: OCR_Final/ is NOT flat files. It is one directory per book:

    OCR_Final/<Book Name>/<Book Name>.txt
    OCR_Final/<Book Name>/metadata.json

metadata.json looks like:
    {"title": ..., "title_en": ..., "author": ..., "genre": "Non-Fiction",
     "issued_date": "1924", "written_date": "", "ocr_confidence": 0.9529}

The .txt has two OCR markup artifacts we must handle:

  <eos>  End-of-sentence marker. This is a gift -- it gives us exact sentence
         boundaries, so we split on it rather than guessing with punctuation.
         (We still punctuation-split any trailing text after the final <eos>,
         in case a book doesn't end with one.)

  <psi>  Appears INSIDE a word, e.g. "විසි<psi>නේ" -- a typesetting/line-break
         split artifact from the printed page. We delete it with no space, so
         the word is rejoined: "විසිනේ". It must not survive into the text: it
         appears only in SiDiaC, so leaving it in would let a model identify the
         source (and therefore the label) from the marker instead of the language.

The .txt also carries hard line-wraps from the original page scan, so lines must
be joined within a sentence -- clean_text() in common.py does that by collapsing
all whitespace runs.

Every row is label="sinhala": the SiDiaC curators already removed the Pali and
Sanskrit source verses from the sanna (gloss) texts, so what remains is Sinhala.

Output: data/processed/sidiac_common.csv
"""

import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from common import clean_text, finalise  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
OCR_DIR = REPO / "data" / "raw" / "SiDiaC" / "OCR_Final"
OUT = REPO / "data" / "processed" / "sidiac_common.csv"

# Mid-word split artifact -> delete entirely (no replacement space).
# The corpus contains at least one OCR typo of this marker ("<psij>"), so we
# match <psi> plus any trailing letters rather than the exact string. Leaving
# even one of these in would be a SiDiaC-only tell that leaks the source label.
PSI = re.compile(r"<psi[a-z]*>", re.IGNORECASE)

# Sentence-ending punctuation, used only as a fallback for text that trails the
# last <eos>. Includes the Sinhala/Devanagari danda (।, ॥) and Latin . ! ?
FALLBACK_SENTENCE_SPLIT = re.compile(r"(?<=[.!?।॥])\s+")


def long_path(path):
    """Work around the Windows 260-character MAX_PATH limit.

    A few SiDiaC books have very long Sinhala titles, and the title is repeated
    in both the directory name and the filename, so the full path can exceed 260
    chars. Windows then refuses to open the file even though glob can see it.
    Prefixing with \\\\?\\ switches to the extended-length API, which allows ~32k.
    On non-Windows this is a no-op.
    """
    path = path.resolve()
    if sys.platform == "win32" and not str(path).startswith("\\\\?\\"):
        return Path("\\\\?\\" + str(path))
    return path


def read_text_safely(path):
    """Read a UTF-8 text file, tolerating long paths and stray bad bytes.

    errors="replace" keeps one corrupt byte from killing an entire book; OCR
    output occasionally contains them.
    """
    return long_path(path).read_text(encoding="utf-8", errors="replace")


def book_stub(name):
    """Make a filesystem/id-safe stub from a Sinhala book directory name.

    We keep the Sinhala characters (they are valid UTF-8 and we must not mangle
    them) and only replace whitespace with underscores, so ids stay readable.
    """
    return re.sub(r"\s+", "_", name.strip())


def split_sentences(raw_text):
    """Split one book's raw OCR text into sentences.

    Primary split is on the explicit <eos> marker. Anything after the last
    <eos> (a book that doesn't end with one) is punctuation-split as a fallback
    so we don't silently lose the tail.
    """
    # Remove the mid-word split marker BEFORE splitting, so the word rejoins.
    text = PSI.sub("", raw_text)

    parts = text.split("<eos>")

    sentences = []
    for i, part in enumerate(parts):
        is_last = i == len(parts) - 1
        if is_last:
            # The trailing chunk had no <eos>; fall back to punctuation.
            for frag in FALLBACK_SENTENCE_SPLIT.split(part):
                sentences.append(frag)
        else:
            sentences.append(part)

    # clean_text collapses the OCR line-wraps; drop what's left empty.
    # We keep SHORT fragments on purpose -- the benchmark needs them.
    return [s for s in (clean_text(s) for s in sentences) if s]


def load_book(book_dir):
    """Read one book directory. Returns (rows, meta) or (None, None) if unusable."""
    name = book_dir.name

    # The .txt is normally named after the directory, but glob rather than
    # assume, so a mismatched filename doesn't silently skip the book.
    txt_files = list(book_dir.glob("*.txt"))
    if not txt_files:
        return None, None
    txt_path = txt_files[0]

    raw_text = read_text_safely(txt_path)

    # Metadata is optional; fall back to the book name if genre is missing.
    meta = {}
    meta_path = book_dir / "metadata.json"
    if meta_path.exists():
        try:
            meta = json.loads(read_text_safely(meta_path))
        except json.JSONDecodeError:
            meta = {}

    genre = (meta.get("genre") or "").strip()
    subcorpus = genre if genre else name

    stub = book_stub(name)
    sentences = split_sentences(raw_text)

    rows = []
    for i, sentence in enumerate(sentences):
        rows.append(
            {
                "id": f"sidiac_{stub}_{i:05d}",
                "text": sentence,
                "label": "sinhala",
                "source": "SiDiaC",
                "subcorpus": subcorpus,
                # Group by BOOK: no book may straddle train/val/test.
                "group_id": f"sidiac_{stub}",
            }
        )

    return rows, meta


def main():
    book_dirs = sorted(d for d in OCR_DIR.iterdir() if d.is_dir())
    print(f"  found {len(book_dirs)} book directories")

    all_rows = []
    n_no_text = 0
    n_no_meta = 0

    for book_dir in book_dirs:
        rows, meta = load_book(book_dir)
        if rows is None:
            n_no_text += 1
            continue
        if not meta:
            n_no_meta += 1
        all_rows.extend(rows)

    df = pd.DataFrame(all_rows)
    df, n_empty = finalise(df)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False, encoding="utf-8")

    print(f"\nSiDiaC -> {OUT.relative_to(REPO)}")
    print(f"  rows written       : {len(df):,}")
    print(f"  dropped empty      : {n_empty:,}")
    print(f"  books with no .txt : {n_no_text}")
    print(f"  books with no meta : {n_no_meta}")
    print(f"  books (group_id)   : {df['group_id'].nunique()}")
    print(f"  subcorpora (genre) : {df['subcorpus'].nunique()}")
    print("  top subcorpora:")
    for sub, n in df["subcorpus"].value_counts().head(8).items():
        print(f"    {sub:<28} {n:,}")


if __name__ == "__main__":
    main()
