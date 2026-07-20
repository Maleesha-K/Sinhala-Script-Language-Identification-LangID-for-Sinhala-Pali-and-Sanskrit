"""
Comprehensive audit of data/processed/master.csv
Run with: conda run -n langid python scripts/audit_master.py
"""
import sys
import json
from pathlib import Path
from collections import Counter

import pandas as pd
import numpy as np

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

REPO = Path(__file__).resolve().parents[1]
target_file = sys.argv[1] if len(sys.argv) > 1 else "master.csv"
MASTER = REPO / "data" / "processed" / target_file
REPORT = REPO / "data" / "processed" / f"audit_report_{target_file.split('.')[0]}.json"

SEP = "=" * 70

def main():
    print(f"\n{SEP}\n  MASTER DATASET AUDIT\n{SEP}\n")

    # ---- 1. Load ----
    df = pd.read_csv(MASTER, encoding="utf-8")
    print(f"File: {MASTER}")
    print(f"Total rows: {len(df):,}")
    print(f"Columns: {list(df.columns)}")
    print(f"Dtypes:\n{df.dtypes}\n")

    # ---- 2. Missing values ----
    print(f"{SEP}\n  MISSING / NULL VALUES\n{SEP}")
    for col in df.columns:
        n_null = df[col].isna().sum()
        n_empty = (df[col].astype(str).str.strip() == "").sum() if col == "text" else 0
        print(f"  {col:<12}  null={n_null:>6}  empty_string={n_empty:>6}")

    # ---- 3. Label distribution ----
    print(f"\n{SEP}\n  LABEL DISTRIBUTION (ALL ROWS)\n{SEP}")
    for label, n in df["label"].value_counts().items():
        pct = 100 * n / len(df)
        print(f"  {label:<10} {n:>8,}  ({pct:5.2f}%)")

    # ---- 4. Core vs Mixed ----
    print(f"\n{SEP}\n  CORE (is_core=True) vs MIXED (is_core=False)\n{SEP}")
    core = df[df["is_core"] == True]
    mixed = df[df["is_core"] == False]
    print(f"  Core rows:  {len(core):>8,}")
    print(f"  Mixed rows: {len(mixed):>8,}")

    # ---- 5. Core 3-way balance ----
    print(f"\n{SEP}\n  CORE 3-WAY CLASS BALANCE\n{SEP}")
    core_counts = core["label"].value_counts()
    core_total = core_counts.sum()
    for label, n in core_counts.items():
        pct = 100 * n / core_total
        print(f"  {label:<10} {n:>8,}  ({pct:5.2f}%)")
    imbalance = core_counts.max() / core_counts.min()
    print(f"\n  Largest / Smallest ratio: {imbalance:.2f}x")

    # ---- 6. Source breakdown ----
    print(f"\n{SEP}\n  SOURCE BREAKDOWN\n{SEP}")
    for src, n in df["source"].value_counts().items():
        pct = 100 * n / len(df)
        print(f"  {src:<12} {n:>8,}  ({pct:5.2f}%)")

    # ---- 7. Source x Label crosstab ----
    print(f"\n{SEP}\n  SOURCE x LABEL CROSSTAB\n{SEP}")
    ct = pd.crosstab(df["source"], df["label"])
    print(ct.to_string())

    # ---- 8. Split distribution ----
    print(f"\n{SEP}\n  SPLIT DISTRIBUTION\n{SEP}")
    for split, n in df["split"].value_counts().items():
        pct = 100 * n / len(df)
        print(f"  {split:<8} {n:>8,}  ({pct:5.2f}%)")

    # ---- 9. Label x Split crosstab ----
    print(f"\n{SEP}\n  LABEL x SPLIT CROSSTAB\n{SEP}")
    ct2 = pd.crosstab(df["label"], df["split"])
    ct2 = ct2.reindex(columns=["train", "val", "test"], fill_value=0)
    ct2["TOTAL"] = ct2.sum(axis=1)
    print(ct2.to_string())

    # ---- 10. Leakage check ----
    print(f"\n{SEP}\n  LEAKAGE CHECK (group_id across splits)\n{SEP}")
    per_group = df.groupby("group_id")["split"].nunique()
    straddling = (per_group > 1).sum()
    if straddling == 0:
        print(f"  PASS: all {len(per_group):,} group_ids appear in exactly one split.")
    else:
        print(f"  FAIL: {straddling:,} group_ids appear in more than one split!")
        bad = per_group[per_group > 1].index[:10].tolist()
        print(f"  Examples: {bad}")

    # ---- 11. Duplicate text check ----
    print(f"\n{SEP}\n  DUPLICATE TEXT ANALYSIS\n{SEP}")
    # Same text + same label (should be 0 after dedup)
    dup_same_label = df.duplicated(subset=["text", "label"], keep=False).sum()
    print(f"  Rows with same text AND same label (exact dupes): {dup_same_label:,}")

    # Same text but different labels (contradictory signal)
    text_labels = df.groupby("text")["label"].nunique()
    contradictory = (text_labels > 1).sum()
    print(f"  Unique texts appearing under >1 label (contradictory): {contradictory:,}")
    if contradictory > 0:
        examples = text_labels[text_labels > 1].head(5).index.tolist()
        for t in examples:
            labels = df[df["text"] == t]["label"].unique().tolist()
            print(f"    \"{t[:80]}...\" -> labels: {labels}")

    # ---- 12. Text length statistics ----
    print(f"\n{SEP}\n  TEXT LENGTH STATISTICS (chars)\n{SEP}")
    df["_len"] = df["text"].astype(str).str.len()
    for label in sorted(df["label"].unique()):
        subset = df[df["label"] == label]["_len"]
        print(f"  {label:<10}  min={subset.min():>5}  median={subset.median():>7.0f}  "
              f"mean={subset.mean():>7.1f}  max={subset.max():>6}  std={subset.std():>7.1f}")

    # Very short texts (< 10 chars) — possibly noise
    short = df[df["_len"] < 10]
    print(f"\n  Rows with < 10 chars: {len(short):,}")
    if len(short) > 0:
        print(f"    Label breakdown: {dict(short['label'].value_counts())}")

    # Very long texts (> 2000 chars)
    long_texts = df[df["_len"] > 2000]
    print(f"  Rows with > 2000 chars: {len(long_texts):,}")
    if len(long_texts) > 0:
        print(f"    Label breakdown: {dict(long_texts['label'].value_counts())}")

    # ---- 13. Text length statistics (words) ----
    print(f"\n{SEP}\n  TEXT LENGTH STATISTICS (words)\n{SEP}")
    df["_wlen"] = df["text"].astype(str).str.split().str.len()
    for label in sorted(df["label"].unique()):
        subset = df[df["label"] == label]["_wlen"]
        print(f"  {label:<10}  min={subset.min():>3}  median={subset.median():>6.0f}  "
              f"mean={subset.mean():>6.1f}  max={subset.max():>5}")

    # ---- 14. Subcorpus distribution ----
    print(f"\n{SEP}\n  SUBCORPUS DISTRIBUTION\n{SEP}")
    for sub, n in df["subcorpus"].value_counts().head(15).items():
        pct = 100 * n / len(df)
        print(f"  {str(sub):<35} {n:>8,}  ({pct:5.2f}%)")
    remaining = df["subcorpus"].nunique() - 15
    if remaining > 0:
        print(f"  ... and {remaining} more subcorpora")

    # ---- 15. Group ID statistics ----
    print(f"\n{SEP}\n  GROUP_ID STATISTICS\n{SEP}")
    group_sizes = df.groupby("group_id").size()
    print(f"  Total unique group_ids: {len(group_sizes):,}")
    print(f"  Rows per group:  min={group_sizes.min()}  median={group_sizes.median():.0f}  "
          f"mean={group_sizes.mean():.1f}  max={group_sizes.max()}")
    large_groups = (group_sizes > 100).sum()
    print(f"  Groups with > 100 rows: {large_groups:,}")

    # ---- 16. Script / encoding check ----
    print(f"\n{SEP}\n  SCRIPT / ENCODING SPOT-CHECK\n{SEP}")
    # Check if text contains Sinhala Unicode characters (range: U+0D80 - U+0DFF)
    def has_sinhala(text):
        return any('\u0D80' <= c <= '\u0DFF' for c in str(text))
    
    for label in sorted(df["label"].unique()):
        subset = df[df["label"] == label]
        sample = subset.sample(min(500, len(subset)), random_state=42)
        sinhala_pct = 100 * sample["text"].apply(has_sinhala).mean()
        print(f"  {label:<10}  {sinhala_pct:5.1f}% of sampled rows contain Sinhala script chars")

    # Check for rows with NO Sinhala characters at all
    no_sinhala = df[~df["text"].apply(has_sinhala)]
    print(f"\n  Rows with ZERO Sinhala script characters: {len(no_sinhala):,}")
    if len(no_sinhala) > 0:
        print(f"    Label breakdown: {dict(no_sinhala['label'].value_counts())}")
        print(f"    Source breakdown: {dict(no_sinhala['source'].value_counts())}")
        # Show a few examples
        for _, r in no_sinhala.head(3).iterrows():
            print(f"    Example ({r['label']}/{r['source']}): \"{str(r['text'])[:100]}\"")

    # ---- 17. ID uniqueness ----
    print(f"\n{SEP}\n  ID UNIQUENESS\n{SEP}")
    n_unique_ids = df["id"].nunique()
    n_dup_ids = len(df) - n_unique_ids
    print(f"  Unique IDs: {n_unique_ids:,}")
    print(f"  Duplicate IDs: {n_dup_ids:,}")

    # ---- 18. Random samples per label ----
    print(f"\n{SEP}\n  RANDOM SAMPLES (3 per core label)\n{SEP}")
    for label in ["sinhala", "pali", "sanskrit"]:
        subset = df[(df["label"] == label) & (df["is_core"] == True)]
        if len(subset) == 0:
            continue
        print(f"\n  --- {label.upper()} ---")
        for _, r in subset.sample(3, random_state=42).iterrows():
            print(f"    [{r['source']}/{r['subcorpus']}] {str(r['text'])[:120]}")

    # ---- Summary ----
    print(f"\n{SEP}\n  AUDIT SUMMARY\n{SEP}")
    issues = []
    if straddling > 0:
        issues.append(f"CRITICAL: {straddling} group_ids straddle splits (data leakage)")
    if dup_same_label > 0:
        issues.append(f"WARNING: {dup_same_label} exact duplicate rows remain")
    if contradictory > 0:
        issues.append(f"INFO: {contradictory} texts appear under multiple labels (known issue)")
    if len(no_sinhala) > 0:
        issues.append(f"WARNING: {len(no_sinhala)} rows have zero Sinhala script characters")
    if n_dup_ids > 0:
        issues.append(f"WARNING: {n_dup_ids} duplicate IDs found")
    if len(short) > 0:
        issues.append(f"INFO: {len(short)} rows have < 10 characters")
    
    if not issues:
        print("  No issues found. Dataset looks clean!")
    else:
        for issue in issues:
            print(f"  - {issue}")

    # Save a machine-readable summary
    summary = {
        "total_rows": len(df),
        "core_rows": len(core),
        "mixed_rows": len(mixed),
        "core_balance": {l: int(n) for l, n in core_counts.items()},
        "imbalance_ratio": round(imbalance, 2),
        "sources": {s: int(n) for s, n in df["source"].value_counts().items()},
        "leakage_check": "PASS" if straddling == 0 else "FAIL",
        "exact_duplicates": int(dup_same_label),
        "contradictory_texts": int(contradictory),
        "no_sinhala_script_rows": len(no_sinhala),
        "duplicate_ids": int(n_dup_ids),
        "issues": issues,
    }
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\n  Machine-readable report saved to: {REPORT.relative_to(REPO)}")

    df.drop(columns=["_len", "_wlen"], inplace=True)
    print(f"\n{SEP}\n  AUDIT COMPLETE\n{SEP}\n")


if __name__ == "__main__":
    main()
