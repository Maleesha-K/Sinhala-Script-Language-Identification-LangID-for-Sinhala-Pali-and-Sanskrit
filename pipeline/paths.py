"""Centralized Path Configuration for the 'pipeline' Folder.

Provides clean path references for:
1. Target Language Dataset (Sinhala, Pali, Sanskrit in Sinhala script)
2. Hybrid Evaluation Benchmarks (FLORES+, WiLI-2018, CommonLID)
3. Hybrid Finetune & Rehearsal Datasets (Aya, Devanagari Sanskrit, Mixed Replay)
4. Traditional 7 ML Baseline Models
5. Pretrained Baseline Foundation Models (Table 1)
6. Target-Only Local SOTA Models (Table 2)
7. Global Multilingual Rehearsal SOTA Models (Table 3)
"""

import os
from pathlib import Path

# Resolve pipeline root directory
PIPELINE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PIPELINE_ROOT.parent

# Top-level directories
DATASETS_DIR = PIPELINE_ROOT / "datasets"
MODELS_DIR = PIPELINE_ROOT / "models"
SCRIPTS_DIR = PIPELINE_ROOT / "scripts"
RESULTS_DIR = DATASETS_DIR / "benchmark_results"

# --- 1. Target Language Dataset Splits ---
TARGET_DIR = DATASETS_DIR / "target_language"
TARGET_TRAIN_CSV = TARGET_DIR / "train" / "train.csv"
TARGET_TRAIN_TXT = TARGET_DIR / "train" / "train.txt"
TARGET_VAL_CSV = TARGET_DIR / "validation" / "val.csv"
TARGET_VAL_TXT = TARGET_DIR / "validation" / "valid.txt"
TARGET_TEST_CSV = TARGET_DIR / "test" / "test.csv"

# --- 2. Hybrid Evaluation Benchmarks ---
BENCHMARK_DIR = DATASETS_DIR / "hybrid_benchmark"
FLORES_PLUS_JSONL = BENCHMARK_DIR / "flores_plus" / "flores_plus.jsonl"
FLORES_PLUS_INTEGRATED = BENCHMARK_DIR / "flores_plus" / "flores_plus_integrated.jsonl"
WILI_2018_JSONL = BENCHMARK_DIR / "wili_2018" / "wili-2018.jsonl"
WILI_2018_INTEGRATED = BENCHMARK_DIR / "wili_2018" / "wili-2018_integrated.jsonl"
COMMONLID_JSONL = BENCHMARK_DIR / "commonlid" / "commonlid.jsonl"
COMMONLID_INTEGRATED = BENCHMARK_DIR / "commonlid" / "commonlid_integrated.jsonl"

# --- 3. Hybrid Finetune & Multilingual Rehearsal Datasets ---
FINETUNE_DIR = DATASETS_DIR / "hybrid_finetune"
REPLAY_MIXED_DIR = FINETUNE_DIR / "replay_mixed"
TRAIN_11LANG_UNIFORM = REPLAY_MIXED_DIR / "train_11lang_uniform.csv"
VAL_11LANG_UNIFORM = REPLAY_MIXED_DIR / "val_11lang_uniform.csv"
TRAIN_MIXED_11GROUPS = REPLAY_MIXED_DIR / "train_mixed_11groups.jsonl"
VAL_MIXED_11GROUPS = REPLAY_MIXED_DIR / "val_mixed_11groups.jsonl"
SANSKRIT_DEVA_FILE = FINETUNE_DIR / "sanskrit_devanagari" / "combined.txt"

# --- 4. Benchmark Results by Story Phase ---
RESULTS_ML_BASELINES = RESULTS_DIR / "00_traditional_ml_baselines"
RESULTS_ZERO_SHOT = RESULTS_DIR / "01_zero_shot"
RESULTS_TARGET_ONLY = RESULTS_DIR / "02_target_only"
RESULTS_REHEARSAL = RESULTS_DIR / "03_multilingual_rehearsal"

# --- 5. Models Tiers ---
MODELS_TRADITIONAL_ML = MODELS_DIR / "00_traditional_ml_baselines"
MODELS_BASELINE_PRETRAINED = MODELS_DIR / "01_baseline_pretrained"
MODELS_TARGET_ONLY_SOTA = MODELS_DIR / "02_target_only_sota"
MODELS_GLOBAL_REHEARSAL_SOTA = MODELS_DIR / "03_global_rehearsal_sota"

def to_win_long(p: Path) -> str:
    """Add Windows extended path prefix if needed to avoid 260 char limit."""
    s = str(p.resolve())
    if os.name == "nt" and not s.startswith("\\\\?\\"):
        return "\\\\?\\" + s
    return s

def check_exists(p: Path) -> bool:
    """Check existence safely across all platforms including Windows with long paths."""
    return os.path.exists(to_win_long(p))
