"""
================================================================================
Master Two-Stage Benchmarking CLI for 5 SOTA Models
================================================================================
Evaluates:
  1. fastText LID-176
  2. OpenLID-v2
  3. NLLB LID-218
  4. GlotLID v3
  5. ConLID

Against 11-language hybrid benchmarks:
  - FLORES+ (flores_plus.jsonl)
  - CommonLID (commonlid.jsonl)
  - WiLI-2018 (wili-2018.jsonl)

Usage:
  python scripts/benchmark_all_5_twostage.py --model all --dataset flores_plus --limit 200
  python scripts/benchmark_all_5_twostage.py --model fasttext --dataset all
================================================================================
"""

import os
import sys
import json
import argparse
import time
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, f1_score

# Ensure project root is in sys.path
PROJ_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJ_ROOT not in sys.path:
    sys.path.insert(0, PROJ_ROOT)

from scripts.two_stage_routers import get_two_stage_router, ALL_BENCHMARK_LANGUAGES

def fix_win_path(path: str) -> str:
    abs_path = os.path.abspath(path)
    if sys.platform == "win32" and not abs_path.startswith("\\\\?\\"):
        return "\\\\?\\" + abs_path
    return abs_path

# Comprehensive label resolution dictionary mapping raw dataset labels to standardized names
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

def load_dataset(file_path: str, limit: int = None, limit_per_lang: int = None) -> pd.DataFrame:
    records = []
    counts = {lang: 0 for lang in ALL_BENCHMARK_LANGUAGES}
    with open(fix_win_path(file_path), encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if not line.strip(): continue
            row = json.loads(line)
            mapped_label = map_all_label(row)
            if mapped_label and mapped_label in ALL_BENCHMARK_LANGUAGES:
                if limit_per_lang and counts[mapped_label] >= limit_per_lang:
                    continue
                row["target_label"] = mapped_label
                records.append(row)
                counts[mapped_label] += 1
                if limit and len(records) >= limit:
                    break
    return pd.DataFrame(records)

def evaluate_model_on_dataset(router, model_key: str, dataset_name: str, df: pd.DataFrame, results_dir: str) -> dict:
    print(f"\n[{router.name}] Evaluating on {len(df)} samples from {dataset_name}...")
    start_time = time.time()
    
    texts = df["text"].tolist()
    preds = router.predict_batch(texts)
    
    elapsed = time.time() - start_time
    throughput = len(texts) / elapsed if elapsed > 0 else 0
    
    true_labels = df["target_label"].tolist()
    acc = accuracy_score(true_labels, preds)
    macro_f1 = f1_score(true_labels, preds, average="macro", labels=ALL_BENCHMARK_LANGUAGES, zero_division=0)
    
    print("=" * 65)
    print(f"RESULTS: {router.name} on {dataset_name}")
    print("=" * 65)
    print(f"Accuracy:   {acc * 100:.2f}%")
    print(f"Macro F1:   {macro_f1 * 100:.2f}%")
    print(f"Throughput: {throughput:.1f} sentences/sec")
    print("=" * 65)
    print(classification_report(true_labels, preds, labels=ALL_BENCHMARK_LANGUAGES, digits=4, zero_division=0))
    
    # Save individual prediction CSV
    out_df = df[["text", "label", "source"]].copy()
    out_df["true_label"] = true_labels
    out_df["predicted_label"] = preds
    csv_path = os.path.join(results_dir, f"{model_key}_twostage_{dataset_name}.csv")
    out_df.to_csv(fix_win_path(csv_path), index=False)
    print(f"Saved predictions to: {csv_path}")
    
    return {
        "model": router.name,
        "dataset": dataset_name,
        "samples": len(df),
        "accuracy": acc,
        "macro_f1": macro_f1,
        "throughput_sps": throughput
    }

def main():
    parser = argparse.ArgumentParser(description="Benchmark Two-Stage SOTA Models")
    parser.add_argument("--model", type=str, default="all", choices=["fasttext", "openlid", "nllb", "glotlid", "conlid", "all"])
    parser.add_argument("--dataset", type=str, default="all", choices=["flores_plus", "commonlid", "wili-2018", "all"])
    parser.add_argument("--limit", type=int, default=None, help="Total sample limit for quick sanity checking")
    parser.add_argument("--limit-per-lang", type=int, default=None, help="Sample limit per language for balanced evaluation")
    args = parser.parse_args()

    data_dir = os.path.join(PROJ_ROOT, "data_pipeline", "datasets", "preprocessed")
    results_dir = os.path.join(PROJ_ROOT, "data_pipeline", "datasets", "benchmark_results")
    summary_dir = os.path.join(PROJ_ROOT, "data_pipeline", "Final_results_CSV")
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(summary_dir, exist_ok=True)

    models_to_run = ["fasttext", "openlid", "nllb", "glotlid", "conlid"] if args.model == "all" else [args.model]
    datasets_to_run = ["flores_plus", "commonlid", "wili-2018"] if args.dataset == "all" else [args.dataset]

    all_summaries = []

    for m_key in models_to_run:
        print(f"\n{'#' * 70}")
        print(f"INITIALIZING TWO-STAGE MODEL: {m_key.upper()}")
        print(f"{'#' * 70}")
        try:
            router = get_two_stage_router(m_key)
        except Exception as e:
            print(f"[ERROR] Could not load router for {m_key}: {e}")
            continue

        for d_key in datasets_to_run:
            file_path = os.path.join(data_dir, f"{d_key}.jsonl")
            if not os.path.exists(file_path):
                print(f"[WARNING] Dataset file not found: {file_path}")
                continue
            
            df = load_dataset(file_path, limit=args.limit, limit_per_lang=args.limit_per_lang)
            if df.empty:
                print(f"[WARNING] No valid samples found in {file_path}")
                continue

            summary = evaluate_model_on_dataset(router, m_key, d_key, df, results_dir)
            all_summaries.append(summary)

    if all_summaries:
        summary_df = pd.DataFrame(all_summaries)
        summary_csv = os.path.join(summary_dir, "all_5_twostage_comparison.csv")
        summary_df.to_csv(summary_csv, index=False)
        print("\n" + "=" * 70)
        print("CONSOLIDATED BENCHMARK SUMMARY")
        print("=" * 70)
        print(summary_df.to_string(index=False))
        print(f"\nSaved consolidated summary to: {summary_csv}")

if __name__ == "__main__":
    main()
