"""
SiPaKosa -> common schema.

Reads the two raw metadata CSVs and maps them into the common schema.

Key rule: the label comes from the file's own language column, used AS-IS.
We never guess the label from the filename. In practice:
  - sipakosa_sinhala_metadata.csv -> all "sinhala"
  - sipakosa_mixed_metadata.csv   -> a mix of "pali" and "mixed"

NOTE: the raw CSVs call this column `language` (not `lang`), and they also have
their own `source` column, which we overwrite with "SiPaKosa" to match the
common schema. The original raw file is left untouched on disk.

Output: data/processed/sipakosa_common.csv
"""

import sys
from pathlib import Path

import pandas as pd

# Make `common.py` importable when this script is run directly.
sys.path.insert(0, str(Path(__file__).parent))
from common import finalise  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "data" / "raw" / "SiPaKosa"
OUT = REPO / "data" / "processed" / "sipakosa_common.csv"

# Both files have identical columns, so we can treat them the same way.
SOURCE_FILES = [
    "sipakosa_sinhala_metadata.csv",
    "sipakosa_mixed_metadata.csv",
]


def load_one(path):
    """Read one raw SiPaKosa CSV and map it into the common schema."""
    raw = pd.read_csv(path, encoding="utf-8")

    out = pd.DataFrame()
    out["id"] = "sipakosa_" + raw["sentence_id"].astype(str)
    out["text"] = raw["text"]
    # The label is taken straight from the file. No re-classification.
    out["label"] = raw["language"]
    out["source"] = "SiPaKosa"
    out["subcorpus"] = raw["book_category"]

    # group_id is unique per row, so SiPaKosa effectively gets a random split.
    # Its books are too few and too large to group on without starving a split.
    out["group_id"] = "sipakosa_" + raw["sentence_id"].astype(str)

    return out


def main():
    frames = []
    for name in SOURCE_FILES:
        path = RAW / name
        df = load_one(path)
        print(f"  read {name}: {len(df):,} rows")
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    combined, n_empty = finalise(combined)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(OUT, index=False, encoding="utf-8")

    print(f"\nSiPaKosa -> {OUT.relative_to(REPO)}")
    print(f"  rows written : {len(combined):,}")
    print(f"  dropped empty: {n_empty:,}")
    print("  label counts :")
    for label, n in combined["label"].value_counts().items():
        print(f"    {label:<10} {n:,}")


if __name__ == "__main__":
    main()
