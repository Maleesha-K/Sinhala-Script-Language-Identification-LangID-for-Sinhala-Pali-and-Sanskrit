# [COLAB SETUP]
import sys
import os

if "google.colab" in sys.modules:
    print("Running in Google Colab. Setting up environment...")
    
    from google.colab import drive
    drive.mount('/content/drive')
    
    repo_path = '/content/drive/MyDrive/Sinhala-Script-Language-Identification-LangID-for-Sinhala-Pali-and-Sanskrit'
    
    if not os.path.exists(repo_path):
        print(f"Cloning repository into {repo_path}...")
        os.makedirs('/content/drive/MyDrive', exist_ok=True)
        os.system(f'git clone https://github.com/Maleesha-K/Sinhala-Script-Language-Identification-LangID-for-Sinhala-Pali-and-Sanskrit.git {repo_path}')
        
    os.chdir(repo_path + '/data_pipeline')
    print("Installing dependencies...")
    os.system('pip install -q pandas datasets')
    print("Setup complete!")


import os
import json
import pandas as pd
from datasets import load_dataset
import random

# Auto-resolve the project root if running manually
if not os.path.exists("Makefile") and os.path.exists("../../Makefile"):
    os.chdir("../../")

output_dir = 'datasets/finetuning'
train_jsonl_path = os.path.join(output_dir, "train.jsonl")
val_jsonl_path = os.path.join(output_dir, "val.jsonl")
output_train_mixed_path = os.path.join(output_dir, "train_mixed.jsonl")
output_val_mixed_path = os.path.join(output_dir, "val_mixed.jsonl")

# Target languages to preserve (excluding Sinhala, Pali, Sanskrit)
TARGET_LANGUAGES = {
    "eng": "en", "hin": "hi", "arb": "ar", "fra": "fr", "deu": "de", "ben": "bn", "tam": "ta",
    "jpn": "ja", "nld": "nl", "pol": "pl", "ita": "it", "por": "pt", "tur": "tr", "spa": "es",
    "ell": "el", "urd": "ur", "zho": "zh", "rus": "ru", "tha": "th", "swh": "sw", "vie": "vi"
}

TRAIN_SAMPLES_PER_LANG = 5000
VAL_SAMPLES_PER_LANG = 500
TOTAL_SAMPLES = TRAIN_SAMPLES_PER_LANG + VAL_SAMPLES_PER_LANG


print("Loading Aya Dataset from HuggingFace...")
aya_dataset = load_dataset("CohereLabs/aya_dataset", split="train")

print("Filtering for target rehearsal languages...")
rehearsal_train_records = []
rehearsal_val_records = []
lang_counts = {lang: 0 for lang in TARGET_LANGUAGES.keys()}

for row in aya_dataset:
    lang = row['language_code']
    if lang in TARGET_LANGUAGES and lang_counts[lang] < TOTAL_SAMPLES:
        record = {
            "text": row["inputs"],
            "label": lang,
            "source": "aya_dataset"
        }
        if lang_counts[lang] < TRAIN_SAMPLES_PER_LANG:
            rehearsal_train_records.append(record)
        else:
            rehearsal_val_records.append(record)
        lang_counts[lang] += 1

    # Stop early if all quotas are met
    if all(count == TOTAL_SAMPLES for count in lang_counts.values()):
        break

print(f"Sampled rehearsal distributions from Aya Dataset:")
for lang, count in lang_counts.items():
    print(f"  {lang}: {count} total ({min(count, TRAIN_SAMPLES_PER_LANG)} train, {max(0, count - TRAIN_SAMPLES_PER_LANG)} val)")


def load_base_data(jsonl_path):
    records = []
    if os.path.exists(jsonl_path):
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                records.append(json.loads(line))
        print(f"Loaded {len(records)} base records from {jsonl_path}.")
    else:
        print(f"WARNING: {jsonl_path} not found.")
    return records

base_train = load_base_data(train_jsonl_path)
base_val = load_base_data(val_jsonl_path)

print("\nCombining and shuffling datasets...")
train_mixed = base_train + rehearsal_train_records
val_mixed = base_val + rehearsal_val_records

random.shuffle(train_mixed)
random.shuffle(val_mixed)

with open(output_train_mixed_path, 'w', encoding='utf-8') as f:
    for record in train_mixed:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')

with open(output_val_mixed_path, 'w', encoding='utf-8') as f:
    for record in val_mixed:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')

print(f"Created {output_train_mixed_path} with {len(train_mixed)} total mixed records.")
print(f"Created {output_val_mixed_path} with {len(val_mixed)} total mixed records.")


