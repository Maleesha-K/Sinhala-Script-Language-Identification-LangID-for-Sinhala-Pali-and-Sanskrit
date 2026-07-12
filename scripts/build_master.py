"""
Merge the three processed CSVs into one master dataset, then assign splits.

Splitting strategy (this is the part that matters most for a trustworthy score):

  GROUPED  -- we split on group_id, never on individual rows. A group is a
              document: a SansinNT chapter, a SiDiaC book, or (for SiPaKosa) a
              single sentence. This guarantees no document has some sentences in
              train and others in test. Without this, neighbouring verses from
              the same chapter would sit on both sides of the split and the test
              score would be inflated by memorised vocabulary.

  STRATIFIED -- class proportions are held roughly constant across train/val/test.

  SEPARATE -- run once for is_core=True rows (the 3-way task) and once for the
              mixed rows (the code-mixing analysis), so each is independently
              well-proportioned.

  SEEDED   -- random_state=42 everywhere, so re-running gives identical splits.

We do NOT rebalance or downsample. The master file stays complete; any
rebalancing is a modelling decision to be made later, at training time.

Output: data/processed/master.csv
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent / "loaders"))
from common import SCHEMA, CORE_LABELS  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
PROC = REPO / "data" / "processed"
OUT = PROC / "master.csv"

SEED = 42
TRAIN, VAL, TEST = 0.80, 0.10, 0.10

INPUTS = [
    "sipakosa_common.csv",
    "sansin_common.csv",
    "sidiac_common.csv",
]


def assign_grouped_split(df, seed=SEED):
    """Assign train/val/test to `df` by group, keeping label proportions.

    Approach: each group_id gets exactly one split. We bucket the groups by
    their dominant label, shuffle the groups within each label, then hand out
    80/10/10 of the GROUPS per label. Because every group is assigned as a whole,
    no group can straddle two splits. Because we do it per-label, the label
    proportions are preserved.

    Returns a Series of "train"/"val"/"test" aligned to df.index.
    """
    rng = np.random.default_rng(seed)

    # One row per group: its label (the dominant one, if a group somehow spans
    # labels) and its size.
    group_label = df.groupby("group_id")["label"].agg(
        lambda s: s.value_counts().idxmax()
    )

    split_of_group = {}

    for label in sorted(group_label.unique()):
        groups = group_label[group_label == label].index.to_numpy()
        groups = groups.copy()
        rng.shuffle(groups)

        n = len(groups)
        n_train = int(round(n * TRAIN))
        n_val = int(round(n * VAL))

        # Guard the tiny-class case: if a label has very few groups, rounding
        # could leave val or test empty. Steal one group from train if so.
        if n >= 3:
            if n_val == 0:
                n_val = 1
                n_train = min(n_train, n - 2)
            if n - n_train - n_val == 0:
                n_train = max(0, n - n_val - 1)

        for i, g in enumerate(groups):
            if i < n_train:
                split_of_group[g] = "train"
            elif i < n_train + n_val:
                split_of_group[g] = "val"
            else:
                split_of_group[g] = "test"

    return df["group_id"].map(split_of_group)


def main():
    # ---------- load ----------
    frames = []
    for name in INPUTS:
        path = PROC / name
        df = pd.read_csv(path, encoding="utf-8")
        print(f"  loaded {name:<24} {len(df):>8,} rows")
        frames.append(df)

    master = pd.concat(frames, ignore_index=True)
    n_before = len(master)

    # ---------- dedupe ----------
    # Exact duplicates = same text AND same label. We keep the first occurrence.
    master = master.drop_duplicates(subset=["text", "label"], keep="first").copy()
    n_dupes = n_before - len(master)

    # ---------- is_core ----------
    # Recompute rather than trust the loaders, so the master file is
    # self-consistent even if a loader is ever changed.
    master["is_core"] = master["label"].isin(CORE_LABELS)

    # ---------- split ----------
    # Run the grouped split separately for core rows and mixed rows.
    core = master[master["is_core"]].copy()
    mixed = master[~master["is_core"]].copy()

    core["split"] = assign_grouped_split(core, seed=SEED)
    mixed["split"] = assign_grouped_split(mixed, seed=SEED)

    master = pd.concat([core, mixed], ignore_index=True)

    # ---------- write ----------
    master = master[SCHEMA]
    master.to_csv(OUT, index=False, encoding="utf-8")

    report(master, n_before, n_dupes)


def report(master, n_before, n_dupes):
    """Phase 4: print the report."""
    line = "=" * 66

    print(f"\n{line}\nMASTER DATASET\n{line}")
    print(f"  written to      : {OUT.relative_to(REPO)}")
    print(f"  rows before     : {n_before:,}")
    print(f"  exact dupes cut : {n_dupes:,}  (same text + same label)")
    print(f"  TOTAL ROWS      : {len(master):,}")

    print(f"\n{line}\nROWS PER SOURCE\n{line}")
    for src, n in master["source"].value_counts().items():
        print(f"  {src:<12} {n:>8,}")

    print(f"\n{line}\nLABEL x SPLIT\n{line}")
    tab = pd.crosstab(master["label"], master["split"])
    # Put the columns in a sensible order.
    tab = tab.reindex(columns=[c for c in ["train", "val", "test"] if c in tab])
    tab["TOTAL"] = tab.sum(axis=1)
    print(tab.to_string())

    # ---------- core class balance ----------
    print(f"\n{line}\nCORE 3-WAY CLASS BALANCE (is_core=True)\n{line}")
    core = master[master["is_core"]]
    counts = core["label"].value_counts()
    total = counts.sum()
    for label, n in counts.items():
        pct = 100 * n / total
        print(f"  {label:<10} {n:>8,}  ({pct:5.2f}%)")

    smallest = counts.idxmin()
    smallest_n = counts.min()
    largest_n = counts.max()
    ratio = largest_n / smallest_n

    print(f"\n  !! SMALLEST CORE CLASS: {smallest.upper()} "
          f"({smallest_n:,} rows, {100*smallest_n/total:.2f}% of core)")
    print(f"  !! IMBALANCE: the largest core class has {ratio:.1f}x more rows.")
    print(f"  !! {smallest} train/val/test counts:")
    sm = core[core["label"] == smallest]["split"].value_counts()
    for sp in ["train", "val", "test"]:
        print(f"       {sp:<6} {sm.get(sp, 0):>7,}")
    print(f"\n  Consider class weighting or resampling AT TRAINING TIME.")
    print(f"  The master file is deliberately left un-rebalanced.")

    # ---------- leakage check ----------
    print(f"\n{line}\nLEAKAGE CHECK\n{line}")
    per_group = master.groupby("group_id")["split"].nunique()
    straddling = (per_group > 1).sum()
    if straddling == 0:
        print(f"  PASS: all {len(per_group):,} group_ids appear in exactly one split.")
    else:
        print(f"  FAIL: {straddling:,} group_ids appear in more than one split!")

    # ---------- samples ----------
    print(f"\n{line}\n10 RANDOM SAMPLE ROWS\n{line}")
    for _, r in master.sample(10, random_state=SEED).iterrows():
        print(f"\n  id        : {r['id']}")
        print(f"  label     : {r['label']}   is_core={r['is_core']}   split={r['split']}")
        print(f"  source    : {r['source']}   subcorpus={r['subcorpus']}")
        print(f"  group_id  : {r['group_id']}")
        print(f"  text      : {r['text']}")


if __name__ == "__main__":
    main()
