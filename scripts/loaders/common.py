"""
Shared helpers for the three per-source loaders.

Every loader produces a CSV with exactly these columns, in this order.
`split` is left blank here; build_master.py fills it in at the end.
"""

import re

# The common schema. Keep this list as the single source of truth for column
# order -- all three loaders and build_master.py import it from here.
SCHEMA = [
    "id",
    "text",
    "label",
    "source",
    "subcorpus",
    "group_id",
    "is_core",
    "split",
]

# The three "real" languages. Anything else (i.e. "mixed") is not part of the
# 3-way classification task, so it gets is_core=False.
CORE_LABELS = {"sinhala", "pali", "sanskrit"}

# Matches any run of whitespace, including the newlines that come from the
# hard line-wraps in the OCR'd SiDiaC page scans.
_WHITESPACE_RUN = re.compile(r"\s+")


def clean_text(raw):
    """Normalise one piece of text.

    Collapses every run of whitespace (spaces, tabs, newlines) down to a single
    space and trims the ends. This is what joins the OCR line-wraps back into
    one continuous sentence.

    Returns "" for anything empty/missing, so callers can drop those rows.
    """
    if raw is None:
        return ""
    # Guard against pandas giving us a float NaN for an empty CSV cell.
    if not isinstance(raw, str):
        # NaN is the only non-str we expect; str() it and let the check below
        # catch the "nan" case via the caller's emptiness test.
        if raw != raw:  # NaN is the only value that isn't equal to itself
            return ""
        raw = str(raw)
    return _WHITESPACE_RUN.sub(" ", raw).strip()


def is_core_label(label):
    """True for the three target languages, False for 'mixed'."""
    return label in CORE_LABELS


def finalise(df):
    """Apply the cleaning rules every loader shares, and enforce the schema.

    - drop rows whose text is empty or whitespace-only
    - set is_core from the label
    - leave split blank
    - put the columns in schema order

    Returns (dataframe, n_dropped_empty).
    """
    before = len(df)

    df["text"] = df["text"].map(clean_text)
    # Drop empties. We deliberately do NOT drop *short* texts -- the benchmark
    # wants short fragments, so a 2-character row is legitimate data.
    df = df[df["text"] != ""].copy()

    n_dropped_empty = before - len(df)

    df["is_core"] = df["label"].map(is_core_label)
    df["split"] = ""

    return df[SCHEMA], n_dropped_empty
