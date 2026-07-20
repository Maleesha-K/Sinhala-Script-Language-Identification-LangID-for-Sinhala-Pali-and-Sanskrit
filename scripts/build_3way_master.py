import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path

SEED = 42
TRAIN, VAL, TEST = 0.80, 0.10, 0.10

INPUTS = [
    "pali_suttacentral_common.csv",
    "pali_only_dataset.csv",
    "Sinhala_sidiac_common.csv",
    "sanskrit_wiki_common.csv",
    "sanskrit_sansin_common.csv",
]

PROC = Path("data/processed")
OUT = PROC / "3way_master.csv"

def assign_grouped_split(df, seed=SEED):
    rng = np.random.default_rng(seed)
    group_label = df.groupby("group_id")["label"].agg(lambda s: s.value_counts().idxmax())
    split_of_group = {}

    for label in sorted(group_label.unique()):
        groups = group_label[group_label == label].index.to_numpy()
        groups = groups.copy()
        rng.shuffle(groups)

        n = len(groups)
        n_train = int(round(n * TRAIN))
        n_val = int(round(n * VAL))

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

def downsample_class(df, label, max_rows, seed=SEED):
    class_df = df[df["label"] == label]
    if len(class_df) <= max_rows:
        return class_df
    rng = np.random.default_rng(seed)
    groups = class_df["group_id"].unique()
    rng.shuffle(groups)
    
    group_sizes = class_df.groupby("group_id").size()
    sizes = group_sizes.loc[groups].values
    cum_sizes = np.cumsum(sizes)
    idx = np.searchsorted(cum_sizes, max_rows)
    keep_groups = groups[:idx+1]
    
    return class_df[class_df["group_id"].isin(keep_groups)]

def main():
    frames = []
    for name in INPUTS:
        path = PROC / name
        if not path.exists():
            print(f"Skipping {name} (not found)")
            continue
        
        df = pd.read_csv(path, encoding="utf-8-sig")
        # Standardize label names
        df['label'] = df['label'].str.lower().str.strip()
        print(f"Loaded {name}: {len(df)} rows")
        frames.append(df)

    if not frames:
        print("No input data found!")
        sys.exit(1)

    master = pd.concat(frames, ignore_index=True)
    master = master.dropna(subset=['text', 'label', 'group_id'])
    
    # Basic deduplication
    n_before = len(master)
    master = master.drop_duplicates(subset=["text", "label"], keep="first").copy()
    print(f"Removed {n_before - len(master)} duplicates.")

    # Check classes
    counts = master['label'].value_counts()
    print("\nInitial Class Distribution:")
    print(counts)

    # Balance the classes to the size of the smallest class (or slightly larger, e.g. 10000)
    min_class_size = counts.min()
    target_size = min(min_class_size, 10000)
    print(f"\nDownsampling to ~{target_size} per class for perfect balance.")

    balanced_frames = []
    for label in counts.index:
        ds = downsample_class(master, label, target_size)
        balanced_frames.append(ds)
        
    master_balanced = pd.concat(balanced_frames, ignore_index=True)

    print("\nAssigning splits (Train 80% / Val 10% / Test 10%)...")
    master_balanced["split"] = assign_grouped_split(master_balanced, seed=SEED)

    # Save
    master_balanced.to_csv(OUT, index=False, encoding="utf-8-sig")
    print(f"\nFinal dataset written to {OUT}")
    
    print("\nFinal Split Distribution:")
    tab = pd.crosstab(master_balanced["label"], master_balanced["split"])
    tab = tab.reindex(columns=["train", "val", "test"])
    print(tab)

if __name__ == "__main__":
    main()
