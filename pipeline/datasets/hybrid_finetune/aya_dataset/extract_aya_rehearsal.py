"""
Extract Background Rehearsal Languages from CohereLabs/aya_dataset
-----------------------------------------------------------------
Downloads and filters the 7 non-Sanskrit rehearsal languages:
eng, tam, hin, ben, arb, fra, deu.
"""

import os
import json
from datasets import load_dataset

LANG_MAP = {
    "eng": "en",
    "tam": "ta",
    "hin": "hi",
    "ben": "bn",
    "arb": "ar",
    "fra": "fr",
    "deu": "de"
}

TRAIN_QUOTA = 5000
VAL_QUOTA = 500
TOTAL_QUOTA = TRAIN_QUOTA + VAL_QUOTA

def main():
    print("Loading CohereLabs/aya_dataset (streaming)...")
    ds = load_dataset("CohereLabs/aya_dataset", split="train", streaming=True)
    
    train_records = []
    val_records = []
    counts = {lang: 0 for lang in LANG_MAP}
    
    for row in ds:
        lang_code = row.get("language_code")
        if lang_code in LANG_MAP and counts[lang_code] < TOTAL_QUOTA:
            rec = {
                "text": row["inputs"],
                "label": lang_code,
                "source": "aya_dataset"
            }
            if counts[lang_code] < TRAIN_QUOTA:
                train_records.append(rec)
            else:
                val_records.append(rec)
            counts[lang_code] += 1
            
        if all(counts[l] == TOTAL_QUOTA for l in LANG_MAP):
            break
            
    print(f"Successfully sampled {sum(counts.values())} records across 7 languages:")
    for l, c in counts.items():
        print(f"  {l}: {c} records")

    with open("aya_rehearsal_sample.jsonl", "w", encoding="utf-8") as f:
        for r in train_records[:100]:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("Saved sample to aya_rehearsal_sample.jsonl")

if __name__ == "__main__":
    main()
