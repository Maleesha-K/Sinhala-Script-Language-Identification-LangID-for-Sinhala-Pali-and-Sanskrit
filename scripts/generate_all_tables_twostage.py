"""
================================================================================
Generate Tables 4, 5, and 6: Unified Two-Stage Benchmark for 6 SOTA Models
================================================================================
Evaluates:
  1. XLM-R Base
  2. ConLID
  3. fastText LID-176
  4. GlotLID v3
  5. NLLB LID-218
  6. OpenLID-v2

Across the 3 Hybrid Benchmark Datasets:
  - Table 4: FLORES+ (flores_plus.jsonl)
  - Table 5: CommonLID (commonlid.jsonl)
  - Table 6: WiLI-2018 (wili-2018.jsonl)

Generates 3 CSV files matching the exact columns of Tables 4, 5, 6:
  Model, Sinh-Sinh, Pali-Sinh, San-Sinh, San-Deva, Eng-Latn, Tam-Taml, Hin-Deva, Ben-Beng, Ara-Arab, Fre-Latn, Ger-Latn, Macro F1
================================================================================
"""

import os
import sys
import json
import argparse
import time
import pandas as pd
import numpy as np
from sklearn.metrics import f1_score, classification_report

# Ensure project root is in sys.path
PROJ_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJ_ROOT not in sys.path:
    sys.path.insert(0, PROJ_ROOT)

from scripts.two_stage_routers import get_two_stage_router

def fix_win_path(path: str) -> str:
    abs_path = os.path.abspath(path)
    if sys.platform == "win32" and not abs_path.startswith("\\\\?\\"):
        return "\\\\?\\" + abs_path
    return abs_path

# Target column order matching Tables 4, 5, 6 in paper
COLUMN_LANGUAGES = [
    ("Sinh-Sinh", "sinhala"),
    ("Pali-Sinh", "pali"),
    ("San-Sinh", "sanskrit"),
    ("San-Deva", "sanskrit_deva"),
    ("Eng-Latn", "english"),
    ("Tam-Taml", "tamil"),
    ("Hin-Deva", "hindi"),
    ("Ben-Beng", "bengali"),
    ("Ara-Arab", "arabic"),
    ("Fre-Latn", "french"),
    ("Ger-Latn", "german"),
]

LANG_KEYS = [k for _, k in COLUMN_LANGUAGES]
LANG_HEADERS = [h for h, _ in COLUMN_LANGUAGES]

# Mapping dictionary for dataset labels
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

def map_all_label(row):
    lbl = str(row.get("label", "")).strip()
    src = str(row.get("source", "")).strip()
    if lbl == "san":
        if src in ["DCS", "SansinNT", "SiDiaC-v2", "Nadil"]:
            return "sanskrit"
        else:
            return "sanskrit_deva"
    return LABEL_MAPPING_ALL.get(lbl)

def load_hybrid_dataset(file_path: str, limit: int = None, limit_per_lang: int = None) -> pd.DataFrame:
    records = []
    counts = {lang: 0 for lang in LANG_KEYS}
    with open(fix_win_path(file_path), encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            row = json.loads(line)
            mapped_label = map_all_label(row)
            if mapped_label and mapped_label in LANG_KEYS:
                if limit_per_lang and counts[mapped_label] >= limit_per_lang:
                    continue
                row["target_label"] = mapped_label
                records.append(row)
                counts[mapped_label] += 1
                if limit and len(records) >= limit:
                    break
    return pd.DataFrame(records)

# Model list in order of appearance in paper tables
MODELS_TO_BENCHMARK = [
    ("XLM-R Base", "xlmr"),
    ("ConLID", "conlid"),
    ("fastText LID-176", "fasttext"),
    ("GlotLID v3", "glotlid"),
    ("NLLB LID-218", "nllb"),
    ("OpenLID-v2", "openlid"),
]

DATASET_CONFIGS = [
    ("Table 4", "FLORES+", "flores_plus.jsonl", "table4_flores_twostage.csv"),
    ("Table 5", "CommonLID", "commonlid.jsonl", "table5_commonlid_twostage.csv"),
    ("Table 6", "WiLI-2018", "wili-2018.jsonl", "table6_wili_twostage.csv"),
]

def evaluate_table(dataset_title: str, dataset_name: str, file_name: str, out_csv_name: str, 
                   limit: int = None, limit_per_lang: int = None, selected_models: list = None):
    data_dir = os.path.join(PROJ_ROOT, "data_pipeline", "datasets", "preprocessed")
    out_dir = os.path.join(PROJ_ROOT, "data_pipeline", "Final_results_CSV")
    os.makedirs(out_dir, exist_ok=True)
    
    file_path = os.path.join(data_dir, file_name)
    print("\n" + "=" * 80)
    print(f"BENCHMARKING {dataset_title}: {dataset_name} ({file_name})")
    print("=" * 80)
    
    if not os.path.exists(file_path):
        print(f"[ERROR] Dataset not found at: {file_path}")
        return None

    df = load_hybrid_dataset(file_path, limit=limit, limit_per_lang=limit_per_lang)
    print(f"Loaded {len(df)} samples across {df['target_label'].nunique()} languages.")
    
    # Check language support in this dataset
    lang_counts = df["target_label"].value_counts().to_dict()
    print("Class distribution:")
    for h, k in COLUMN_LANGUAGES:
        print(f"  {h:10s} ({k:15s}): {lang_counts.get(k, 0)}")

    table_rows = []
    out_path = os.path.join(out_dir, out_csv_name)
    existing_df = None
    if os.path.exists(out_path):
        try:
            existing_df = pd.read_csv(out_path)
            table_rows = existing_df.to_dict("records")
        except Exception:
            pass

    texts = df["text"].tolist()
    true_labels = df["target_label"].tolist()

    models_to_run = selected_models or MODELS_TO_BENCHMARK

    for display_name, m_key in models_to_run:
        print(f"\n---> Running Two-Stage Model: {display_name} ({m_key})...")
        t0 = time.time()
        try:
            router = get_two_stage_router(m_key)
        except Exception as e:
            print(f"[ERROR] Failed to load router {m_key}: {e}")
            continue

        preds = router.predict_batch(texts)
        elapsed = time.time() - t0
        throughput = len(texts) / elapsed if elapsed > 0 else 0
        print(f"Finished {len(texts)} samples in {elapsed:.1f}s ({throughput:.1f} sentences/sec)")

        # Compute per-class F1
        per_class_f1 = f1_score(true_labels, preds, average=None, labels=LANG_KEYS, zero_division=0)
        f1_dict = dict(zip(LANG_KEYS, per_class_f1))

        # Determine valid classes present in dataset
        present_classes = [k for k in LANG_KEYS if lang_counts.get(k, 0) > 0]
        present_f1s = [f1_dict[k] for k in present_classes]
        macro_f1 = np.mean(present_f1s) if present_f1s else 0.0

        row_dict = {"Model": display_name}
        for h, k in COLUMN_LANGUAGES:
            if lang_counts.get(k, 0) == 0:
                row_dict[h] = "--"
            else:
                row_dict[h] = f"{f1_dict[k]:.4f}"

        row_dict["Macro F1"] = f"{macro_f1:.4f}"
        
        # Replace or append row
        table_rows = [r for r in table_rows if r.get("Model") != display_name]
        table_rows.append(row_dict)

        # Save immediately after each model finishes
        current_df = pd.DataFrame(table_rows)
        current_df.to_csv(fix_win_path(out_path), index=False)

    result_df = pd.DataFrame(table_rows)
    print("\n" + "=" * 80)
    print(f"RESULTS FOR {dataset_title} ({dataset_name}):")
    print("=" * 80)
    print(result_df.to_string(index=False))
    print(f"\nSaved CSV to: {out_path}\n")
    return result_df

def main():
    parser = argparse.ArgumentParser(description="Generate Tables 4, 5, and 6 via Unified Two-Stage Method")
    parser.add_argument("--dataset", type=str, default="all", choices=["flores_plus", "commonlid", "wili-2018", "all"])
    parser.add_argument("--model", type=str, default="all", choices=["xlmr", "conlid", "fasttext", "glotlid", "nllb", "openlid", "all"])
    parser.add_argument("--limit", type=int, default=None, help="Overall limit per dataset")
    parser.add_argument("--limit-per-lang", type=int, default=None, help="Limit per language for balanced evaluation")
    args = parser.parse_args()

    selected_models = None
    if args.model != "all":
        selected_models = [(d, k) for d, k in MODELS_TO_BENCHMARK if k == args.model]

    configs_to_run = DATASET_CONFIGS
    if args.dataset != "all":
        configs_to_run = [c for c in DATASET_CONFIGS if args.dataset in c[2]]

    for d_title, d_name, f_name, out_csv in configs_to_run:
        evaluate_table(d_title, d_name, f_name, out_csv, 
                       limit=args.limit, limit_per_lang=args.limit_per_lang, 
                       selected_models=selected_models)

if __name__ == "__main__":
    main()
