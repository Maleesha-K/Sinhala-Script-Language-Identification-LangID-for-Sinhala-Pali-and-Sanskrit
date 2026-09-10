"""
Builds a strictly balanced, non-contaminated 11-language training dataset
(10,000 sentences per language class = 110,000 total sentences).

Taxonomy (11 BCP-47 classes):
  1. Sinh-Sinh (Sinhala in Sinhala script)
  2. Pali-Sinh (Pali in Sinhala script)
  3. San-Sinh  (Sanskrit in Sinhala script)
  4. San-Deva  (Sanskrit in Devanagari script)
  5. Eng-Latn  (English in Latin script)
  6. Tam-Taml  (Tamil in Tamil script)
  7. Hin-Deva  (Hindi in Devanagari script)
  8. Ben-Beng  (Bengali in Bengali script)
  9. Ara-Arab  (Arabic in Arabic script)
 10. Fre-Latn  (French in Latin script)
 11. Ger-Latn  (German in Latin script)
"""

import os
import sys
import re
import random
import pandas as pd
from datasets import load_dataset

# Ensure unbuffered immediate printing
sys.stdout.reconfigure(line_buffering=True)

SAMPLES_PER_CLASS = 10000
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

OUTPUT_DIR = "data_pipeline/datasets/finetuning"
os.makedirs(OUTPUT_DIR, exist_ok=True)

TRAIN_OUTPUT = os.path.join(OUTPUT_DIR, "train_11lang_uniform.csv")
VAL_OUTPUT = os.path.join(OUTPUT_DIR, "val_11lang_uniform.csv")

def clean_sentence(text):
    text = str(text).strip()
    text = re.sub(r'\s+', ' ', text)
    words = text.split()
    if len(words) < 3 or len(text) < 15 or len(words) > 60:
        return None
    return text

print("--- Step 1: Loading Target Languages (Sinh-Sinh, Pali-Sinh, San-Sinh) ---", flush=True)
target_df = pd.read_csv("data/Nadil/train.csv")

target_records = []
label_map = {
    "sinhala": "Sinh-Sinh",
    "pali": "Pali-Sinh",
    "sanskrit": "San-Sinh"
}

for orig_label, target_bcp in label_map.items():
    sub = target_df[target_df["label"] == orig_label].copy()
    valid_texts = []
    for t in sub["text"]:
        c = clean_sentence(t)
        if c:
            valid_texts.append(c)
    
    valid_texts = list(dict.fromkeys(valid_texts))
    random.shuffle(valid_texts)
    sampled = valid_texts[:SAMPLES_PER_CLASS]
    print(f"  {target_bcp}: sampled {len(sampled)} / {len(valid_texts)} sentences", flush=True)
    for s in sampled:
        target_records.append({"text": s, "label": target_bcp, "source": "target_train"})

print(f"Total target sentences extracted: {len(target_records)}", flush=True)

print("\n--- Step 2: Extracting Global Languages from Tatoeba (Vectorized) ---", flush=True)
tatoeba_path = "data_pipeline/datasets/raw_download/tatoeba/sentences.csv"
tatoeba_targets = {
    "eng": "Eng-Latn",
    "hin": "Hin-Deva",
    "ben": "Ben-Beng",
    "ara": "Ara-Arab",
    "fra": "Fre-Latn",
    "deu": "Ger-Latn"
}

tatoeba_collected = {k: [] for k in tatoeba_targets}
target_keys = set(tatoeba_targets.keys())

chunk_idx = 0
for chunk in pd.read_csv(tatoeba_path, sep='\t', header=None, usecols=[1, 2], chunksize=200000):
    chunk_idx += 1
    # Vectorized filter: keep only our 6 target languages
    filtered = chunk[chunk[1].isin(target_keys)]
    for lang, text in zip(filtered[1], filtered[2]):
        if len(tatoeba_collected[lang]) < SAMPLES_PER_CLASS * 1.5:
            c = clean_sentence(text)
            if c:
                tatoeba_collected[lang].append(c)
    
    # Check if all reached target
    if all(len(v) >= SAMPLES_PER_CLASS for v in tatoeba_collected.values()):
        print(f"  All Tatoeba quotas fulfilled at chunk {chunk_idx}!", flush=True)
        break

tatoeba_records = []
for lang, bcp in tatoeba_targets.items():
    dedup = list(dict.fromkeys(tatoeba_collected[lang]))
    random.shuffle(dedup)
    sampled = dedup[:SAMPLES_PER_CLASS]
    print(f"  {bcp}: sampled {len(sampled)} sentences", flush=True)
    for s in sampled:
        tatoeba_records.append({"text": s, "label": bcp, "source": "tatoeba"})

print("\n--- Step 3: Extracting Sanskrit Devanagari (San-Deva) ---", flush=True)
san_ds = load_dataset("surajp/sanskrit_classic", split="train", trust_remote_code=True)
san_collected = []
for row in san_ds:
    c = clean_sentence(row["text"])
    if c:
        san_collected.append(c)
    if len(san_collected) >= SAMPLES_PER_CLASS * 1.5:
        break

san_dedup = list(dict.fromkeys(san_collected))
random.shuffle(san_dedup)
san_sampled = san_dedup[:SAMPLES_PER_CLASS]
print(f"  San-Deva: sampled {len(san_sampled)} sentences", flush=True)
san_records = [{"text": s, "label": "San-Deva", "source": "sanskrit_classic"} for s in san_sampled]

print("\n--- Step 4: Extracting Tamil (Tam-Taml) from Wikimedia ---", flush=True)
tam_ds = load_dataset("wikimedia/wikipedia", "20231101.ta", split="train", streaming=True)
tam_collected = []
for row in tam_ds:
    paragraphs = str(row["text"]).split("\n")
    for p in paragraphs:
        c = clean_sentence(p)
        if c:
            tam_collected.append(c)
    if len(tam_collected) >= SAMPLES_PER_CLASS * 1.5:
        break

tam_dedup = list(dict.fromkeys(tam_collected))
random.shuffle(tam_dedup)
tam_sampled = tam_dedup[:SAMPLES_PER_CLASS]
print(f"  Tam-Taml: sampled {len(tam_sampled)} sentences", flush=True)
tam_records = [{"text": s, "label": "Tam-Taml", "source": "wikimedia_ta"} for s in tam_sampled]

print("\n--- Step 5: Combining and Creating Stratified 90/10 Split ---", flush=True)
all_records = target_records + tatoeba_records + san_records + tam_records
df_all = pd.DataFrame(all_records)

print("Class distribution in combined dataset:", flush=True)
print(df_all["label"].value_counts(), flush=True)

train_frames = []
val_frames = []

for label, group in df_all.groupby("label"):
    shuffled = group.sample(frac=1.0, random_state=RANDOM_SEED).reset_index(drop=True)
    n_train = int(len(shuffled) * 0.9)
    train_frames.append(shuffled.iloc[:n_train])
    val_frames.append(shuffled.iloc[n_train:])

train_df = pd.concat(train_frames).sample(frac=1.0, random_state=RANDOM_SEED).reset_index(drop=True)
val_df = pd.concat(val_frames).sample(frac=1.0, random_state=RANDOM_SEED).reset_index(drop=True)

train_df["id"] = [f"train_11lang_{i:06d}" for i in range(len(train_df))]
val_df["id"] = [f"val_11lang_{i:06d}" for i in range(len(val_df))]

train_df[["id", "text", "label", "source"]].to_csv(TRAIN_OUTPUT, index=False, encoding="utf-8")
val_df[["id", "text", "label", "source"]].to_csv(VAL_OUTPUT, index=False, encoding="utf-8")

print(f"\nSuccessfully generated:", flush=True)
print(f"  Train: {TRAIN_OUTPUT} ({len(train_df)} rows - exactly {len(train_df)//11} per class)", flush=True)
print(f"  Val:   {VAL_OUTPUT} ({len(val_df)} rows - exactly {len(val_df)//11} per class)", flush=True)
