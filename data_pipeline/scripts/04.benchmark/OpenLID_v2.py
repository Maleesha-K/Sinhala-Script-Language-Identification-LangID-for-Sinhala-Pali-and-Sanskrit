import sys
import os
import re
import json
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, f1_score
import fasttext
from huggingface_hub import hf_hub_download

def fix_win_path(path):
    abs_path = os.path.abspath(path)
    if sys.platform == "win32" and not abs_path.startswith("\\\\?\\"):
        return "\\\\?\\" + abs_path
    return abs_path

# Ensure working directory is project root
proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
os.chdir(proj_root)

input_dir = os.path.join(proj_root, "data_pipeline", "datasets", "preprocessed")
output_dir = os.path.join(proj_root, "data_pipeline", "datasets", "benchmark_results")
os.makedirs(output_dir, exist_ok=True)

print("Downloading OpenLID-v2 model from Hugging Face...")
model_path = hf_hub_download(repo_id="laurievb/OpenLID-v2", filename="model.bin")
print(f"Loading OpenLID-v2 model from {model_path}...")
model = fasttext.load_model(model_path)
model_name = "OpenLID-v2"

LABEL_MAP = {
    "sin": "sin_Sinh", "sin_Sinh": "sin_Sinh", "sinhala": "sin_Sinh",
    "pli": "pli_Sinh", "pli_Sinh": "pli_Sinh", "pali": "pli_Sinh",
    "san_Sinh": "san_Sinh", "sanskrit": "san_Sinh",
    "san_Deva": "san_Deva", "san": "san_Deva",
    "eng": "eng_Latn", "eng_Latn": "eng_Latn", "english": "eng_Latn",
    "tam": "tam_Taml", "tam_Taml": "tam_Taml", "tamil": "tam_Taml",
    "hin": "hin_Deva", "hin_Deva": "hin_Deva", "hindi": "hin_Deva",
    "ben": "ben_Beng", "ben_Beng": "ben_Beng", "bengali": "ben_Beng",
    "arb": "arb_Arab", "arb_Arab": "arb_Arab", "arabic": "arb_Arab",
    "fra": "fra_Latn", "fra_Latn": "fra_Latn", "french": "fra_Latn",
    "deu": "deu_Latn", "deu_Latn": "deu_Latn", "german": "deu_Latn",
}

target_labels = [
    "sin_Sinh", "pli_Sinh", "san_Sinh", "san_Deva",
    "eng_Latn", "tam_Taml", "hin_Deva", "ben_Beng",
    "arb_Arab", "fra_Latn", "deu_Latn"
]

def clean_for_openlid(text):
    text = str(text).strip().replace("\n", " ").lower()
    text = re.sub(r"[^\w\s]|\d", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def map_true_label(row):
    lbl = str(row.get("label", "")).strip()
    src = str(row.get("source", "")).strip()
    if lbl == "san":
        if src in ["DCS", "SansinNT", "SiDiaC-v2", "Nadil"]:
            return "san_Sinh"
        return "san_Deva"
    return LABEL_MAP.get(lbl)

def load_dataset(file_path):
    print(f"\nLoading {os.path.basename(file_path)}...")
    records = []
    with open(fix_win_path(file_path), encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            row = json.loads(line)
            mapped = map_true_label(row)
            if mapped:
                row["flores_label"] = mapped
                records.append(row)
    df = pd.DataFrame(records)
    if not df.empty:
        print(f"Loaded {len(df)} rows across {df['flores_label'].nunique()} language-script classes")
    return df

benchmark_files = ["flores_plus_integrated.jsonl", "commonlid_integrated.jsonl", "wili-2018_integrated.jsonl"]

for fname in benchmark_files:
    file_path = os.path.join(input_dir, fname)
    if not os.path.exists(file_path):
        print(f"Warning: {file_path} not found.")
        continue
        
    dataset_name = os.path.splitext(fname)[0]
    df = load_dataset(file_path)
    if df.empty: continue
    
    texts = df["text"].apply(clean_for_openlid).tolist()
    print(f"Evaluating {len(texts)} samples with {model_name} on {dataset_name}...")
    preds, _ = model.predict(texts, k=1)
    
    results = df[["text", "label", "source"]].copy()
    results["true_label"] = df["flores_label"]
    results["predicted_label"] = [p[0].replace("__label__", "") for p in preds]
    
    acc = accuracy_score(results["true_label"], results["predicted_label"])
    macro_f1 = f1_score(
        results["true_label"], results["predicted_label"],
        average="macro", labels=target_labels, zero_division=0
    )
    
    print("\n" + "=" * 52)
    print(f"ZERO-SHOT BENCHMARK RESULTS ({model_name} on {dataset_name})")
    print("=" * 52)
    print(f"Accuracy:  {acc * 100:.2f}%")
    print(f"Macro F1:  {macro_f1 * 100:.2f}%")
    print("=" * 52)
    print("\nPer-language breakdown:\n")
    print(classification_report(
        results["true_label"], results["predicted_label"],
        labels=target_labels, digits=4, zero_division=0
    ))
    
    out_file = fix_win_path(os.path.join(output_dir, f"openlid_v2_{dataset_name}.csv"))
    results.to_csv(out_file, index=False)
    print(f"Saved zero-shot predictions to {out_file}\n")
