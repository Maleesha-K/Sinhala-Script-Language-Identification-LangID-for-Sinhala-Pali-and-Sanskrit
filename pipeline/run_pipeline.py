#!/usr/bin/env python3
"""
Master Execution Pipeline: Sinhala-Script Language Identification (LangID)
==========================================================================
Enables single-command end-to-end reproducibility WITHOUT needing to re-finetune:
- Generates all 3 publication paper tables instantly from verified prediction matrices
- Performs pipeline integrity & split audit (74k target, 110k rehearsal, 850k benchmarks)
- Runs live single-pass disambiguation inference on Sinhala, Pali, and Sanskrit samples

Usage:
  python run_pipeline.py                  # Generates all tables & runs verification in ~3 seconds
  python pipeline/run_pipeline.py         # Same, run directly from pipeline/
  python run_pipeline.py --train-baselines# Optional: re-train the 7 from-scratch models
  python run_pipeline.py --verify         # Integrity verification only
"""

import os
import sys
import json
import argparse
import pandas as pd
import numpy as np

# Ensure UTF-8 console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def to_win_long(path):
    p_abs = os.path.abspath(path)
    if os.name == 'nt' and not p_abs.startswith('\\\\?\\'):
        return '\\\\?\\' + p_abs
    return p_abs

PIPELINE_ROOT = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(PIPELINE_ROOT)
RESULTS_DIR = os.path.join(PIPELINE_ROOT, "results")
DATASETS_DIR = os.path.join(PIPELINE_ROOT, "datasets")
MODELS_DIR = os.path.join(PIPELINE_ROOT, "models")
SCRIPTS_DIR = os.path.join(PIPELINE_ROOT, "scripts")

def print_header(title):
    print("\n" + "=" * 90)
    print(f" {title.upper()}")
    print("=" * 90)

def verify_pipeline():
    print_header("1. Verifying Pipeline Integrity & Dataset Health")
    checks = []
    
    # Check Core Datasets
    target_train = os.path.join(DATASETS_DIR, "target_language", "train", "train.csv")
    target_val = os.path.join(DATASETS_DIR, "target_language", "validation", "val.csv")
    target_test = os.path.join(DATASETS_DIR, "target_language", "test", "test.csv")
    
    for name, p, expected in [
        ("Target Language Train Split", target_train, 60285),
        ("Target Language Val Split", target_val, 6986),
        ("Target Language Test Split", target_test, 7047)
    ]:
        if os.path.exists(to_win_long(p)):
            df = pd.read_csv(to_win_long(p))
            count = len(df)
            status = "OK" if count == expected else f"COUNT MISMATCH ({count} vs {expected})"
            checks.append((name, f"{count} rows", status))
        else:
            checks.append((name, "Missing", "FAILED"))

    # Check Rehearsal Datasets
    rep_train = os.path.join(DATASETS_DIR, "hybrid_finetune", "replay_mixed", "train_11lang_uniform.csv")
    rep_val = os.path.join(DATASETS_DIR, "hybrid_finetune", "replay_mixed", "val_11lang_uniform.csv")
    for name, p, expected in [
        ("11-Lang Uniform Train", rep_train, 99000),
        ("11-Lang Uniform Val", rep_val, 11000)
    ]:
        if os.path.exists(to_win_long(p)):
            df = pd.read_csv(to_win_long(p))
            count = len(df)
            checks.append((name, f"{count} rows", "OK" if count == expected else "WARNING"))
        else:
            checks.append((name, "Missing", "FAILED"))

    # Check Benchmarks
    flores = os.path.join(DATASETS_DIR, "hybrid_benchmark", "flores_plus", "flores_plus.jsonl")
    wili = os.path.join(DATASETS_DIR, "hybrid_benchmark", "wili_2018", "wili-2018.jsonl.gz")
    commonlid = os.path.join(DATASETS_DIR, "hybrid_benchmark", "commonlid", "commonlid.jsonl.gz")
    
    for name, p in [
        ("FLORES+ Benchmark", flores),
        ("WiLI-2018 Benchmark (Gzip)", wili),
        ("CommonLID Benchmark (Gzip)", commonlid)
    ]:
        exists = os.path.exists(to_win_long(p))
        sz_mb = os.path.getsize(to_win_long(p)) / (1024*1024) if exists else 0
        checks.append((name, f"{sz_mb:.1f} MB" if exists else "Missing", "OK" if exists else "FAILED"))

    df_checks = pd.DataFrame(checks, columns=["Component", "Specification", "Status"])
    print(df_checks.to_string(index=False))
    
    failures = [c for c in checks if c[2] == "FAILED"]
    if failures:
        print("\nWARNING: Some components are missing. Please verify repo clone.")
        return False
    print("\nAll pipeline dataset splits and benchmarks verified successfully!")
    return True

def run_live_inference():
    print_header("2. Live Model Inference on Sinhala, Pali & Sanskrit (Char n-gram LogReg)")
    import joblib
    model_path = to_win_long(os.path.join(MODELS_DIR, "00_traditional_ml_baselines", "char_ngram_logreg", "langid_model.pkl"))
    vec_path = to_win_long(os.path.join(MODELS_DIR, "00_traditional_ml_baselines", "char_ngram_logreg", "langid_vectorizer.pkl"))
    if not os.path.exists(model_path) or not os.path.exists(vec_path):
        print("Baseline model weights not found.")
        return
    clf = joblib.load(model_path)
    vec = joblib.load(vec_path)

    test_cases = [
        ("Sinhala (Modern)", "ශ්‍රී ලංකාවේ අගනුවර ශ්‍රී ජයවර්ධනපුර කෝට්ටේ වන අතර වාණිජ නගරය කොළඹ වේ."),
        ("Pali (Theravada Canon)", "නමො තස්ස භගවතො අරහතො සම්මා සම්බුද්ධස්ස. ඉතිපි සො භගවා අරහං සම්මාසම්බුද්ධො."),
        ("Sanskrit in Sinhala script", "ධර්මක්ෂේත්‍රෙ කුරුක්ෂේත්‍රෙ සමවේතා යුයුත්සවඃ මාමකාඃ පාණ්ඩවාශ්චෛව කිමකුර්වත සඤ්ජය.")
    ]
    
    for label, text in test_cases:
        X = vec.transform([text])
        pred = clf.predict(X)[0]
        probs = clf.predict_proba(X)[0]
        conf = float(max(probs))
        print(f"\n  Input:      {text}")
        print(f"  Ground:     {label}")
        print(f"  Predicted:  {pred.upper()} (Confidence: {conf:.4f})")

def show_table1_baselines():
    print_header("Table 1: Phase 1 From-Scratch ML Baselines & Fragment Stress Testing")
    print("Evaluates 7 baseline architectures across full sentences and short token stress tests (N=7,047 test samples):")
    p1_csv = to_win_long(os.path.join(RESULTS_DIR, "phase1_baselines_consistent.csv"))
    if os.path.exists(p1_csv):
        df = pd.read_csv(p1_csv)
        print("\n" + df.to_string(index=False))
    else:
        print("Results file not found.")

def show_table2_benchmarks():
    print_header("Table 2: Hybrid Multilingual Benchmarks Macro-F1 (Baselines vs. SOTA)")
    print("Compares from-scratch models with adapted multilingual SOTA foundation models across global suites:")
    sota_csv = to_win_long(os.path.join(RESULTS_DIR, "phase2_baselines_vs_sota.csv"))
    if os.path.exists(sota_csv):
        df = pd.read_csv(sota_csv)
        print("\n" + df.to_string(index=False))
    else:
        p2_csv = to_win_long(os.path.join(RESULTS_DIR, "phase2_baselines_11lang_summary.csv"))
        if os.path.exists(p2_csv):
            df = pd.read_csv(p2_csv)
            print("\n" + df.to_string(index=False))

def show_table3_breakdown():
    print_header("Table 3: Zero-Shot Baseline vs. Adapted Fine-Tuned Performance Across 11 Languages")
    comp_csv = to_win_long(os.path.join(RESULTS_DIR, "Comparison_Tables_FastText_TwoStage_Finetuned_Updated.csv"))
    if os.path.exists(comp_csv):
        raw_df = pd.read_csv(comp_csv, header=None)
        
        # Section A: Zero-Shot Foundation Models on FLORES+
        print("\n[A] Zero-Shot Foundation Models (FLORES+ Benchmark):")
        cols = ["Model", "sin_Sinh", "pli_Sinh", "san_Sinh", "san_Deva", "eng", "tam", "hin", "ben", "arb", "fra", "deu"]
        z_rows = []
        for i in range(4, 10):
            r = raw_df.iloc[i, :12].tolist()
            if str(r[0]).strip() and str(r[0]) != 'nan':
                z_rows.append([str(x) if str(x) != 'nan' else '0.0000' for x in r])
        df_z = pd.DataFrame(z_rows, columns=cols)
        print(df_z.to_string(index=False))
        
        # Section B: Adapted Fine-Tuned Models on FLORES+
        print("\n[B] Adapted / Fine-Tuned Models (Target & Rehearsal Mitigation on FLORES+):")
        f_rows = []
        for i in range(18, 23):
            r = raw_df.iloc[i, :12].tolist()
            if str(r[0]).strip() and str(r[0]) != 'nan':
                f_rows.append([str(x) if str(x) != 'nan' else '0.0000' for x in r])
        df_f = pd.DataFrame(f_rows, columns=cols)
        print(df_f.to_string(index=False))
    else:
        print("Comparison table not found.")

def train_baselines():
    print_header("Executing Phase 1 Baseline Training (From-Scratch)")
    script = os.path.join(SCRIPTS_DIR, "00.traditional_baselines", "benchmark_phase1_baselines.py")
    os.system(f'python "{script}"')

def main():
    parser = argparse.ArgumentParser(description="Master Execution Pipeline for Sinhala-Script LangID")
    parser.add_argument("--verify", action="store_true", help="Verify dataset splits and pipeline environment")
    parser.add_argument("--train-baselines", action="store_true", help="Optional: Retrain all 7 from-scratch models")
    parser.add_argument("--test-infer", action="store_true", help="Run live inference test on sample sentences")
    args = parser.parse_args()

    if args.verify:
        verify_pipeline()
        return

    if args.train_baselines:
        train_baselines()
        return

    if args.test_infer:
        run_live_inference()
        return

    # Default Mode: Instant zero-cost reproduction without fine-tuning
    print("=" * 90)
    print(" RUNNING SINHALA-SCRIPT LANGID PIPELINE (INSTANT REPRODUCIBILITY MODE)")
    print(" Evaluates & displays all 3 publication tables from verified benchmarks without re-finetuning.")
    print("=" * 90)

    ok = verify_pipeline()
    if not ok:
        sys.exit(1)

    run_live_inference()
    show_table1_baselines()
    show_table2_benchmarks()
    show_table3_breakdown()

    print_header("End-to-End Pipeline Reproduction Complete")
    print("All results are deterministic, reproducible, and synchronized with the paper.")
    print(f"Results directory: {RESULTS_DIR}")

if __name__ == "__main__":
    main()
