"""
================================================================================
Two-Stage Hierarchical Evaluation Pipeline for OpenLID-v2
================================================================================
Purpose:
  Stock OpenLID-v2 correctly routes global background languages (English, German,
  French, Tamil, etc.), but classifies ALL text written in Sinhala script as 'sin_Sinh'.
  
  Conversely, a fine-tuned OpenLID-v2 model trained only on Sinhala, Pali, and Sanskrit
  (in Sinhala script) accurately disambiguates those 3 target languages, but loses
  its ability to identify global background languages.

  Solution: Two-Stage Hierarchical Pipeline Architecture
    - Stage 1 (Stock OpenLID-v2 Router): Receives input text. If Stage 1 detects any
      global non-Sinhala-script language (e.g. English, Tamil, Devanagari Sanskrit),
      it immediately returns that global prediction.
    - Stage 2 (Fine-Tuned OpenLID-v2 Specialist): If Stage 1 detects 'sin_Sinh'
      (Sinhala script), the input text is routed to Stage 2 to make the fine-grained
      3-way distinction between 'sinhala', 'pali', and 'sanskrit'.

  This script benchmarks the Two-Stage OpenLID-v2 pipeline against hybrid FLORES+,
  CommonLID, and WiLI-2018 datasets containing both background and target languages.
================================================================================
"""

import sys
import os
import re
import json
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, f1_score
import fasttext
from huggingface_hub import hf_hub_download

# ------------------------------------------------------------------------------
# 1. Helper Utility: Windows Long Path Normalization
# ------------------------------------------------------------------------------
def fix_win_path(path):
    """
    Prepends standard Windows extended-length path prefix (\\\\?\\) to avoid
    Windows MAX_PATH (260 character limit) file access errors.
    """
    abs_path = os.path.abspath(path)
    if sys.platform == "win32" and not abs_path.startswith("\\\\?\\"):
        return "\\\\?\\" + abs_path
    return abs_path

# ------------------------------------------------------------------------------
# 2. Workspace & Environment Resolution
# ------------------------------------------------------------------------------
# Ensure working directory is set to the project root directory
proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
os.chdir(proj_root)

# Define dataset and output result directories
benchmark_dir = os.path.join(proj_root, "data_pipeline", "datasets", "preprocessed")
results_dir = os.path.join(proj_root, "data_pipeline", "datasets", "benchmark_results")
os.makedirs(results_dir, exist_ok=True)

# ------------------------------------------------------------------------------
# 3. Model Loading (Stage 1 Router & Stage 2 Specialist)
# ------------------------------------------------------------------------------
# Path to local Fine-Tuned OpenLID-v2 model weights (Stage 2)
finetuned_model_path = fix_win_path(os.path.join(proj_root, "data_pipeline", "models", "openlid_v2_finetuned.bin"))

# Download / locate Stock OpenLID-v2 base model from HuggingFace (Stage 1 Router)
print("Downloading stock OpenLID-v2 base model from Hugging Face repository ('laurievb/OpenLID-v2')...")
stock_model_path = hf_hub_download(repo_id="laurievb/OpenLID-v2", filename="model.bin")

print(f"Loading Stock OpenLID-v2 (Stage 1 Router) from {stock_model_path}...")
stock_model = fasttext.load_model(stock_model_path)

print(f"Loading Fine-Tuned OpenLID-v2 (Stage 2 Specialist) from {finetuned_model_path}...")
finetuned_model = fasttext.load_model(finetuned_model_path)

# ------------------------------------------------------------------------------
# 4. Taxonomy & Label Mapping Dictionaries
# ------------------------------------------------------------------------------
# Maps OpenLID-v2 (NLLB BCP-47) 3-letter + script labels to common benchmark names
STAGE1_TO_COMMON = {
    "eng_Latn": "english",
    "deu_Latn": "german",
    "fra_Latn": "french",
    "tam_Taml": "tamil",
    "hin_Deva": "hindi",
    "ben_Beng": "bengali",
    "arb_Arab": "arabic",
    "san_Deva": "sanskrit_deva",
}

# The complete list of 11 evaluation languages present across benchmark datasets
ALL_BENCHMARK_LANGUAGES = [
    "sinhala", "pali", "sanskrit", "sanskrit_deva", "english", "tamil",
    "hindi", "bengali", "arabic", "french", "german"
]

# Comprehensive label resolution dictionary mapping raw dataset labels to common names
LABEL_MAPPING_ALL = {
    "sin": "sinhala", "sin_Sinh": "sinhala", "sinhala": "sinhala", "si": "sinhala",
    "pli": "pali", "pli_Sinh": "pali", "pli_Latn": "pali", "pali": "pali", "pi": "pali",
    "sanskrit": "sanskrit", "san_Sinh": "sanskrit",
    "san_Deva": "sanskrit_deva", "sa": "sanskrit_deva",
    "eng": "english", "eng_Latn": "english", "english": "english", "en": "english",
    "tam": "tamil", "tam_Taml": "tamil", "tamil": "tamil", "ta": "tamil",
    "hin": "hindi", "hin_Deva": "hindi", "hindi": "hindi", "hi": "hindi",
    "ben": "bengali", "ben_Beng": "bengali", "bengali": "bengali", "bn": "bengali",
    "arb": "arabic", "arb_Arab": "arabic", "arabic": "arabic", "ar": "arabic",
    "fra": "french", "fra_Latn": "french", "french": "french", "fr": "french",
    "deu": "german", "deu_Latn": "german", "german": "german", "de": "german"
}

# ------------------------------------------------------------------------------
# 5. Preprocessing & Label Resolution Functions
# ------------------------------------------------------------------------------
def clean_for_openlid(text):
    """
    Cleans raw text for OpenLID-v2 inference by lowercasing, removing punctuation,
    digits, newlines, and extra whitespace.
    """
    text = str(text).strip().replace("\n", " ").lower()
    text = re.sub(r"[^\w\s]|\d", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def map_all_label(row):
    """
    Resolves ambiguous ground-truth labels.
    Specifically distinguishes between Sinhala-script Sanskrit ('sanskrit') and
    Devanagari-script Sanskrit ('sanskrit_deva') based on dataset source metadata.
    """
    lbl = str(row.get("label", "")).strip()
    src = str(row.get("source", "")).strip()
    if lbl == "san":
        # If source is from known Sinhala-script corpora, treat as Sinhala-script Sanskrit
        if src in ["DCS", "SansinNT", "SiDiaC-v2", "Nadil"]:
            return "sanskrit"
        else:
            return "sanskrit_deva"
    return LABEL_MAPPING_ALL.get(lbl)

def load_all_languages_dataset(file_path):
    """
    Loads JSON Lines (.jsonl) benchmark files and maps raw labels to normalized target names.
    """
    records = []
    with open(fix_win_path(file_path), encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            row = json.loads(line)
            mapped_label = map_all_label(row)
            if mapped_label:
                row["target_label"] = mapped_label
                records.append(row)
    return pd.DataFrame(records)

# ------------------------------------------------------------------------------
# 6. Core Two-Stage Prediction Routing Logic
# ------------------------------------------------------------------------------
def predict_two_stage(clean_text):
    """
    Executes Two-Stage Hierarchical Classification for OpenLID-v2:
    
    Stage 1: Stock OpenLID-v2 (Router)
      - Predicts top language label (k=1).
      - If predicted label IS NOT 'sin_Sinh' (non-Sinhala script language):
        - Return mapped global label (e.g. 'english', 'tamil', 'german', etc.).
        
    Stage 2: Fine-Tuned OpenLID-v2 (Specialist)
      - If Stage 1 predicted 'sin_Sinh' (Sinhala script text), pass text to Stage 2.
      - Stage 2 predicts fine-grained target label ('sinhala', 'pali', or 'sanskrit').
    """
    # Stage 1: Stock OpenLID-v2 Prediction
    p1, _ = stock_model.predict(clean_text, k=1)
    lbl1 = p1[0].replace("__label__", "")
    
    # If Stage 1 detects a global non-Sinhala script language, return global prediction
    if lbl1 != "sin_Sinh":
        return STAGE1_TO_COMMON.get(lbl1, lbl1)
    
    # Stage 2: Fine-Tuned OpenLID-v2 Specialist for Sinhala script
    p2, _ = finetuned_model.predict(clean_text, k=1)
    lbl2 = p2[0].replace("__label__", "")
    return lbl2

# ------------------------------------------------------------------------------
# 7. Benchmark Execution Loop Across All Datasets
# ------------------------------------------------------------------------------
benchmark_files = ['flores_plus_integrated.jsonl', 'commonlid_integrated.jsonl', 'wili-2018_integrated.jsonl']

for fname in benchmark_files:
    file_path = os.path.join(benchmark_dir, fname)
    if not os.path.exists(file_path):
        print(f"Warning: Benchmark file {file_path} not found.")
        continue
    
    dataset_name = os.path.splitext(fname)[0]
    df_all = load_all_languages_dataset(file_path)
    if df_all.empty:
        print(f"No matching languages found in {dataset_name}.")
        continue
    
    print(f"\nEvaluating Two-Stage OpenLID-v2 Pipeline on {len(df_all)} samples from {dataset_name}...")
    
    # Clean text and execute 2-stage inference
    clean_texts = df_all["text"].apply(clean_for_openlid).tolist()
    preds = [predict_two_stage(t) for t in clean_texts]
    
    # Store true vs predicted results
    results = df_all[["text", "label", "source"]].copy()
    results["true_label"] = df_all["target_label"]
    results["predicted_label"] = preds
    
    # Calculate overall Accuracy and Macro-F1 across all 11 benchmark languages
    acc_all = accuracy_score(results["true_label"], results["predicted_label"])
    macro_f1_all = f1_score(
        results["true_label"], results["predicted_label"],
        average="macro", labels=ALL_BENCHMARK_LANGUAGES, zero_division=0
    )
    
    # Print formatted summary and per-language precision, recall, and F1 table
    print("=" * 70)
    print(f"TWO-STAGE HIERARCHICAL BENCHMARK RESULTS (OpenLID-v2 - Evaluated on {dataset_name})")
    print("=" * 70)
    print(f"Accuracy:  {acc_all * 100:.2f}%")
    print(f"Macro F1:  {macro_f1_all * 100:.2f}%")
    print("=" * 70)
    print("\nPer-language breakdown:\n")
    print(classification_report(
        results["true_label"], results["predicted_label"],
        labels=ALL_BENCHMARK_LANGUAGES, digits=4, zero_division=0
    ))
    
    # Save predictions to CSV for downstream auditing
    out_csv = fix_win_path(os.path.join(results_dir, f"openlid_v2_twostage_all_langs_{dataset_name}.csv"))
    results.to_csv(out_csv, index=False)
    print(f"Saved two-stage benchmark predictions to {out_csv}")

print("\n" + "=" * 55)
print("TWO-STAGE OPENLID-V2 BENCHMARKING COMPLETE")
print("=" * 55)
