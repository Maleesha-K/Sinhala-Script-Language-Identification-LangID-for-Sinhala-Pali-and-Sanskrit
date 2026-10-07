"""Populate all pipeline/datasets directories:
1. hybrid_benchmark/ (flores_plus, wili_2018, commonlid)
2. hybrid_finetune/ (sanskrit_devanagari, replay_mixed, aya_dataset)
3. benchmark_results/ (00_traditional_ml_baselines, 01_zero_shot, 02_target_only, 03_multilingual_rehearsal)
"""

import os
import sys
import shutil
import gzip
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PIPELINE = REPO_ROOT / "pipeline"
DATASETS_DIR = PIPELINE / "datasets"

PREP_DIR = REPO_ROOT / "data_pipeline" / "datasets" / "preprocessed"
RAW_DIR = REPO_ROOT / "data_pipeline" / "datasets" / "raw_download"
FINETUNE_SRC = REPO_ROOT / "data_pipeline" / "datasets" / "finetuning"
RESULTS_SRC = REPO_ROOT / "data_pipeline" / "datasets" / "benchmark_results"

def to_win_long(p: Path) -> str:
    s = str(p.resolve())
    if os.name == "nt" and not s.startswith("\\\\?\\"):
        return "\\\\?\\" + s
    return s

def safe_link_or_copy(src: Path, dst: Path):
    src_long = to_win_long(src)
    dst_long = to_win_long(dst)
    if not os.path.exists(src_long):
        print(f"  [MISSING] {src.name}")
        return False
    os.makedirs(dst.parent, exist_ok=True)
    if os.path.exists(dst_long):
        print(f"  [EXISTS] {dst.name}")
        return True
    try:
        os.link(src_long, dst_long)
        print(f"  [LINKED] {src.name} -> {dst.name}")
        return True
    except Exception:
        shutil.copy2(src_long, dst_long)
        print(f"  [COPIED] {src.name} -> {dst.name}")
        return True

def populate_hybrid_benchmark():
    print("\n--- Populating hybrid_benchmark ---")
    bm_dir = DATASETS_DIR / "hybrid_benchmark"
    
    # 1. FLORES+
    flores_dir = bm_dir / "flores_plus"
    os.makedirs(to_win_long(flores_dir), exist_ok=True)
    safe_link_or_copy(PREP_DIR / "flores_plus.jsonl", flores_dir / "flores_plus.jsonl")
    with open(to_win_long(flores_dir / "README.md"), "w", encoding="utf-8") as f:
        f.write("""# FLORES+ Evaluation Benchmark

Contains high-quality translation evaluation records across all 11 evaluation languages:
- Sinhala (`sin_Sinh`), Pali (`pli_Sinh`), Sanskrit (`san_Sinh`)
- Global Background: `san_Deva`, `eng_Latn`, `tam_Taml`, `hin_Deva`, `ben_Beng`, `arb_Arab`, `fra_Latn`, `deu_Latn`

## Files:
- `flores_plus.jsonl`: Standardized JSON Lines evaluation format (~61.9 MB)
""")

    # 2. WiLI-2018
    wili_dir = bm_dir / "wili_2018"
    os.makedirs(to_win_long(wili_dir), exist_ok=True)
    safe_link_or_copy(PREP_DIR / "wili-2018.jsonl", wili_dir / "wili-2018.jsonl")
    # Also create gzipped copy for lightweight Git tracking (<61MB)
    gz_wili = wili_dir / "wili-2018.jsonl.gz"
    if not os.path.exists(to_win_long(gz_wili)) and (PREP_DIR / "wili-2018.jsonl").exists():
        print("  [GZIPPING] wili-2018.jsonl -> wili-2018.jsonl.gz...")
        with open(to_win_long(PREP_DIR / "wili-2018.jsonl"), "rb") as f_in, gzip.open(to_win_long(gz_wili), "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    with open(to_win_long(wili_dir / "README.md"), "w", encoding="utf-8") as f:
        f.write("""# WiLI-2018 Evaluation Benchmark

Wikipedia Language Identification benchmark (paragraph-level classification).

## Files:
- `wili-2018.jsonl`: Standardized JSON Lines evaluation format (~142.4 MB)
- `wili-2018.jsonl.gz`: Compressed format for Git storage and fast transfer (~60.8 MB)
""")

    # 3. CommonLID
    common_dir = bm_dir / "commonlid"
    os.makedirs(to_win_long(common_dir), exist_ok=True)
    safe_link_or_copy(PREP_DIR / "commonlid.jsonl", common_dir / "commonlid.jsonl")
    gz_common = common_dir / "commonlid.jsonl.gz"
    if not os.path.exists(to_win_long(gz_common)) and (PREP_DIR / "commonlid.jsonl").exists():
        print("  [GZIPPING] commonlid.jsonl -> commonlid.jsonl.gz...")
        with open(to_win_long(PREP_DIR / "commonlid.jsonl"), "rb") as f_in, gzip.open(to_win_long(gz_common), "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    with open(to_win_long(common_dir / "README.md"), "w", encoding="utf-8") as f:
        f.write("""# CommonLID Evaluation Benchmark

Diverse web-crawled Language Identification benchmark across global languages.

## Files:
- `commonlid.jsonl`: Standardized JSON Lines evaluation format (~134.6 MB)
- `commonlid.jsonl.gz`: Compressed format for Git storage and fast transfer (~37.8 MB)
""")

def populate_hybrid_finetune():
    print("\n--- Populating hybrid_finetune ---")
    ft_dir = DATASETS_DIR / "hybrid_finetune"
    
    # 1. Sanskrit Devanagari
    sanskrit_dir = ft_dir / "sanskrit_devanagari"
    os.makedirs(to_win_long(sanskrit_dir), exist_ok=True)
    safe_link_or_copy(RAW_DIR / "sanskrit_classic" / "combined.txt", sanskrit_dir / "combined.txt")
    with open(to_win_long(sanskrit_dir / "README.md"), "w", encoding="utf-8") as f:
        f.write("""# Sanskrit Devanagari Background Corpus (`san_Deva`)

Source: `surajp/sanskrit_classic` (Hugging Face)
Used as the Devanagari Sanskrit background corpus to train models to distinguish Sanskrit in Sinhala script from classical Sanskrit in Devanagari script.

## Files:
- `combined.txt`: Raw Sanskrit text in Devanagari script (~1.4 MB)
""")

    # 2. Replay Mixed
    replay_dir = ft_dir / "replay_mixed"
    os.makedirs(to_win_long(replay_dir), exist_ok=True)
    safe_link_or_copy(FINETUNE_SRC / "train_11lang_uniform.csv", replay_dir / "train_11lang_uniform.csv")
    safe_link_or_copy(FINETUNE_SRC / "val_11lang_uniform.csv", replay_dir / "val_11lang_uniform.csv")
    with open(to_win_long(replay_dir / "README.md"), "w", encoding="utf-8") as f:
        f.write("""# 11-Language Multilingual Rehearsal Splits

Combines the 3 target languages (`sin_Sinh`, `pli_Sinh`, `san_Sinh`) with the 8 global background languages (`san_Deva`, `eng_Latn`, `tam_Taml`, `hin_Deva`, `ben_Beng`, `arb_Arab`, `fra_Latn`, `deu_Latn`).

## Files:
- `train_11lang_uniform.csv`: Uniformly sampled multi-language training split (~20.5 MB)
- `val_11lang_uniform.csv`: Uniformly sampled validation split (~2.28 MB)
""")

    # 3. Aya Dataset Info
    aya_dir = ft_dir / "aya_dataset"
    os.makedirs(to_win_long(aya_dir), exist_ok=True)
    with open(to_win_long(aya_dir / "README.md"), "w", encoding="utf-8") as f:
        f.write("""# Aya Dataset Rehearsal Cache (`CohereLabs/aya_dataset`)

Provides samples for the 7 non-Sanskrit background rehearsal languages:
- English (`eng_Latn`)
- Tamil (`tam_Taml`)
- Hindi (`hin_Deva`)
- Bengali (`ben_Beng`)
- Arabic (`arb_Arab`)
- French (`fra_Latn`)
- German (`deu_Latn`)

Extracted and sampled via `scripts/05.prepare_datasets/` with seeded sampling (seed=42).
""")

def populate_benchmark_results():
    print("\n--- Populating benchmark_results ---")
    res_dir = DATASETS_DIR / "benchmark_results"
    
    # 00. Traditional ML Baselines
    res_00 = res_dir / "00_traditional_ml_baselines"
    os.makedirs(to_win_long(res_00), exist_ok=True)
    safe_link_or_copy(REPO_ROOT / "results" / "phase1_baselines_consistent.csv", res_00 / "phase1_baselines_consistent.csv")
    with open(to_win_long(res_00 / "README.md"), "w", encoding="utf-8") as f:
        f.write("""# Phase 1A: Traditional ML & Shallow Neural Baseline Results

Records evaluation results for the 7 from-scratch models across full sentences, 5-word, 3-word, and 1-word fragment stress tests.

## Files:
- `phase1_baselines_consistent.csv`: Full Acc/F1, 5w, 3w, and 1w metrics
""")

    # 01. Zero-Shot (Table 1)
    res_01 = res_dir / "01_zero_shot"
    os.makedirs(to_win_long(res_01), exist_ok=True)
    with open(to_win_long(res_01 / "README.md"), "w", encoding="utf-8") as f:
        f.write("""# Phase 1B (Table 1): Foundation Zero-Shot Results

Out-of-the-box baseline evaluation of foundation models across FLORES+, WiLI-2018, CommonLID, and held-out target data.
""")

    # 02. Target-Only (Table 2)
    res_02 = res_dir / "02_target_only"
    os.makedirs(to_win_long(res_02), exist_ok=True)
    with open(to_win_long(res_02 / "README.md"), "w", encoding="utf-8") as f:
        f.write("""# Phase 2 (Table 2): Target-Only Specialist Results

Evaluation of models fine-tuned solely on target languages, demonstrating catastrophic forgetting on global benchmarks.
""")

    # 03. Multilingual Rehearsal (Table 3)
    res_03 = res_dir / "03_multilingual_rehearsal"
    os.makedirs(to_win_long(res_03), exist_ok=True)
    with open(to_win_long(res_03 / "README.md"), "w", encoding="utf-8") as f:
        f.write("""# Phase 3 (Table 3): Multilingual Rehearsal Continual Results

Evaluation of models trained with continual rehearsal / replay, demonstrating mitigation of catastrophic forgetting.
""")

    # Distribute existing CSVs
    if RESULTS_SRC.exists():
        for f in RESULTS_SRC.glob("*.csv"):
            name = f.name.lower()
            if "zero_shot" in name or (name.startswith("openlid_v2_") and "finetuned" not in name and "twostage" not in name):
                safe_link_or_copy(f, res_01 / f.name)
            elif "twostage" in name or "target3" in name or "no_rehearsal" in name:
                safe_link_or_copy(f, res_02 / f.name)
            elif "finetuned" in name or "rehearsal" in name or "replay" in name or "all_langs" in name:
                safe_link_or_copy(f, res_03 / f.name)

    # Clean up any leftover .gitkeep in populated folders
    for d in [res_00, res_01, res_02, res_03]:
        gk = d / ".gitkeep"
        if gk.exists():
            gk.unlink()

def main():
    print("=== Populating all remaining pipeline/datasets ===")
    populate_hybrid_benchmark()
    populate_hybrid_finetune()
    populate_benchmark_results()
    print("\n[SUCCESS] Completed populating all pipeline/datasets directories!")

if __name__ == "__main__":
    main()
