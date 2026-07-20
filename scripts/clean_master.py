import pandas as pd
import numpy as np
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MASTER = REPO / "data" / "processed" / "master.csv"
MASTER_CLEAN = REPO / "data" / "processed" / "master_clean.csv"

# Split config
TRAIN = 0.8
VAL = 0.1
TEST = 0.1

def assign_grouped_split(df: pd.DataFrame, seed: int = 42) -> pd.Series:
    """
    Randomly assigns each group_id to a split (train/val/test).
    Stratifies roughly by the group's dominant label.
    """
    rng = np.random.default_rng(seed)

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

def has_sinhala_chars(text: str) -> bool:
    # U+0D80 to U+0DFF is the Sinhala block
    return bool(re.search(r"[\u0D80-\u0DFF]", str(text)))

def main():
    print("Loading master dataset...")
    df = pd.read_csv(MASTER, encoding="utf-8")
    
    orig_len = len(df)
    print(f"Original length: {orig_len}")

    # 1. Contradictory labels
    print("\nIdentifying contradictory labels...")
    # Find texts that have >1 unique labels
    text_labels = df.groupby("text")["label"].unique()
    contradictory_texts = text_labels[text_labels.apply(len) > 1]
    
    print(f"Found {len(contradictory_texts)} texts with multiple labels.")
    
    texts_to_drop_completely = set()
    texts_to_drop_mixed = set()
    
    core_labels = {"sinhala", "pali", "sanskrit"}
    
    for text, labels in contradictory_texts.items():
        labels_set = set(labels)
        core_in_labels = labels_set.intersection(core_labels)
        
        if len(core_in_labels) > 1:
            texts_to_drop_completely.add(text)
        elif len(core_in_labels) == 1 and "mixed" in labels_set:
            texts_to_drop_mixed.add(text)
        else:
            texts_to_drop_completely.add(text)
            
    print(f" - {len(texts_to_drop_completely)} texts had multiple core labels (dropped entirely).")
    print(f" - {len(texts_to_drop_mixed)} texts had core + mixed (kept core, dropped mixed).")
    
    # Now use boolean masking to find drop indices
    mask_drop_completely = df["text"].isin(texts_to_drop_completely)
    mask_drop_mixed = (df["text"].isin(texts_to_drop_mixed)) & (df["label"] == "mixed")
    
    drop_indices = set(df[mask_drop_completely | mask_drop_mixed].index)
    
    # 2. Non-Sinhala script rows
    print("\nIdentifying rows with no Sinhala script characters...")
    has_sinhala = df["text"].apply(has_sinhala_chars)
    no_sinhala_idx = df[~has_sinhala].index
    print(f"Found {len(no_sinhala_idx)} rows with no Sinhala characters.")
    drop_indices.update(no_sinhala_idx)

    # 3. Ultra-short rows
    print("\nIdentifying ultra-short rows (< 10 chars)...")
    short_idx = df[df["text"].str.len() < 10].index
    print(f"Found {len(short_idx)} short rows.")
    drop_indices.update(short_idx)
    
    # Do drop
    print(f"\nDropping total {len(drop_indices)} rows...")
    df_clean = df.drop(index=list(drop_indices)).copy()
    
    new_len = len(df_clean)
    print(f"Cleaned dataset length: {new_len} (removed {orig_len - new_len} rows)")
    
    # Re-run split
    print("\nRe-assigning splits (seed=42) to maintain group integrity...")
    df_clean["split"] = assign_grouped_split(df_clean, seed=42)
    
    # Re-sort and reset index to be safe
    df_clean = df_clean.sort_values(by=["source", "id"]).reset_index(drop=True)
    
    # Save
    print(f"\nSaving to {MASTER_CLEAN}...")
    df_clean.to_csv(MASTER_CLEAN, index=False, encoding="utf-8")
    print("Done!")

if __name__ == "__main__":
    main()
