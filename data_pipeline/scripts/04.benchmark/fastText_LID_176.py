import sys
import os
import json
import glob
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, f1_score
import urllib.request
import fasttext

def fix_win_path(path):
    abs_path = os.path.abspath(path)
    if sys.platform == "win32" and not abs_path.startswith("\\\\?\\"):
        return "\\\\?\\" + abs_path
    return abs_path

# Auto-resolve project root or data_pipeline root
if not os.path.exists("Makefile") and os.path.exists("../../Makefile"):
    os.chdir("../../")

input_dir = fix_win_path('datasets/preprocessed')
output_dir = fix_win_path('datasets/benchmark_results')
os.makedirs(output_dir, exist_ok=True)

TARGET_LANGUAGES = {
    "eng": "eng_Latn",
    "eng_Latn": "eng_Latn",
    "english": "eng_Latn",
    "sin": "sin_Sinh",
    "sin_Sinh": "sin_Sinh",
    "sinhala": "sin_Sinh",
    "tam": "tam_Taml",
    "tam_Taml": "tam_Taml",
    "tamil": "tam_Taml",
    "hin": "hin_Deva",
    "hin_Deva": "hin_Deva",
    "hindi": "hin_Deva",
    "ben": "ben_Beng",
    "ben_Beng": "ben_Beng",
    "bengali": "ben_Beng",
    "arb": "arb_Arab",
    "arb_Arab": "arb_Arab",
    "arabic": "arb_Arab",
    "fra": "fra_Latn",
    "fra_Latn": "fra_Latn",
    "french": "fra_Latn",
    "deu": "deu_Latn",
    "deu_Latn": "deu_Latn",
    "german": "deu_Latn",
    "pli": "pli_Sinh",
    "pli_Sinh": "pli_Sinh",
    "pali": "pli_Sinh",
    "sanskrit": "san_Sinh",
    "san_Sinh": "san_Sinh",
    "san_Deva": "san_Deva",
}

FASTTEXT_LANG_MAP = {
    "eng_Latn": "en",
    "sin_Sinh": "si",
    "san_Deva": "sa",
    "san_Sinh": "san_Sinh", # fastText LID-176 does not support Sinhala-script Sanskrit -> F1 = 0
    "pli_Sinh": "pli_Sinh", # fastText LID-176 does not support Pali -> F1 = 0
    "tam_Taml": "ta",
    "hin_Deva": "hi",
    "ben_Beng": "bn",
    "arb_Arab": "ar",
    "fra_Latn": "fr",
    "deu_Latn": "de",
}

def map_true_label(row):
    label = str(row.get("label", "")).strip()
    source = str(row.get("source", "")).strip()
    
    if label == "san":
        if source in ["DCS", "SansinNT", "SiDiaC-v2", "Nadil"]:
            return "san_Sinh"
        return "san_Deva"
    
    return TARGET_LANGUAGES.get(label)

def load_dataset(file_path):
    print(f"\nLoading {os.path.basename(file_path)}...")
    records = []
    with open(file_path, encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            row = json.loads(line)
            mapped_lbl = map_true_label(row)
            if mapped_lbl:
                row["flores_label"] = mapped_lbl
                records.append(row)
                
    df = pd.DataFrame(records)
    if not df.empty:
        print(f"Loaded {len(df)} rows across {df['flores_label'].nunique()} language-script classes")
        print("True-label counts:")
        print(df["flores_label"].value_counts().sort_index())
    else:
        print("No matching target languages found in this dataset.")
    return df

def evaluate_and_save(results, model_name, dataset_name, target_labels):
    acc = accuracy_score(results["true_label"], results["predicted_label"])
    macro_f1 = f1_score(
        results["true_label"],
        results["predicted_label"],
        average="macro",
        labels=target_labels,
        zero_division=0,
    )

    print("\n" + "=" * 60)
    print(f"ZERO-SHOT BENCHMARK RESULTS ({model_name} on {dataset_name})")
    print("=" * 60)
    print(f"Accuracy:  {acc * 100:.2f}%")
    print(f"Macro F1:  {macro_f1 * 100:.2f}%")
    print("=" * 60)
    print("\nPer-language breakdown:\n")
    print(classification_report(
        results["true_label"],
        results["predicted_label"],
        labels=target_labels,
        digits=4,
        zero_division=0,
    ))

    os.makedirs(output_dir, exist_ok=True)
    clean_name = model_name.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '').lower()
    out_file = fix_win_path(os.path.join(output_dir, f"{clean_name}_{dataset_name}.csv"))
    results.to_csv(out_file, index=False)
    print(f"\nSaved predictions to {out_file}\n")
    return results

MODEL_URL = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin"
MODEL_PATH = fix_win_path("models/benchmark/fastText/lid.176.bin")

if not os.path.exists(MODEL_PATH):
    print("Downloading fastText LID-176 model (~126MB)...")
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)

print("Loading fastText LID-176 model...")
model = fasttext.load_model(MODEL_PATH)
model_name = "fastText LID-176 Zero-Shot"
target_labels = sorted(set(FASTTEXT_LANG_MAP.values()))

benchmark_target_files = [
    'flores_plus_integrated.jsonl',
    'commonlid_integrated.jsonl',
    'wili-2018_integrated.jsonl'
]

for fname in benchmark_target_files:
    file_path = fix_win_path(os.path.join('datasets/preprocessed', fname))
    if not os.path.exists(file_path):
        print(f"Warning: {file_path} not found.")
        continue
    dataset_name = os.path.splitext(fname)[0]
    df = load_dataset(file_path)
    if df.empty: continue
    
    texts = df["text"].astype(str).str.replace("\n", " ").tolist()
    print(f"Evaluating {len(texts)} samples with {model_name} on {dataset_name}...")
    preds, _ = model.predict(texts, k=1)

    results = df[["text", "label", "source"]].copy()
    results["true_label"] = df["flores_label"].map(FASTTEXT_LANG_MAP)
    results["predicted_label"] = [p[0].replace("__label__", "") for p in preds]

    evaluate_and_save(results, model_name, dataset_name, target_labels)

print("Zero-shot fastText evaluation complete!")
