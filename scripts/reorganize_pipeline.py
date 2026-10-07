"""Reorganize data_pipeline into the story-aligned structure.

Structure:
datasets/
├── target_language/
│   ├── train/
│   ├── validation/
│   └── test/
├── hybrid_benchmark/
│   ├── flores_plus/
│   ├── wili_2018/
│   └── commonlid/
├── hybrid_finetune/
│   ├── aya_dataset/
│   ├── sanskrit_devanagari/
│   └── replay_mixed/
└── benchmark_results/
    ├── 00_traditional_ml_baselines/
    ├── 01_zero_shot/
    ├── 02_target_only/
    └── 03_multilingual_rehearsal/

models/
├── 00_traditional_ml_baselines/
│   ├── multinomial_nb/
│   ├── linear_svm/
│   ├── char_ngram_logreg/
│   ├── xgboost/
│   ├── fasttext_scratch/
│   ├── char_cnn/
│   └── char_bigru/
├── 01_baseline_pretrained/
├── 02_target_only_sota/
└── 03_global_rehearsal_sota/
"""

import os
import sys
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PIPELINE = REPO_ROOT / "data_pipeline"
DATASETS_DIR = PIPELINE / "datasets"
MODELS_DIR = PIPELINE / "models"

def to_win_long(p: Path) -> str:
    s = str(p.resolve())
    if os.name == "nt" and not s.startswith("\\\\?\\"):
        return "\\\\?\\" + s
    return s

def safe_mkdir(p: Path):
    os.makedirs(to_win_long(p), exist_ok=True)

def safe_copy_or_link(src: Path, dst: Path):
    src_long = to_win_long(src)
    dst_long = to_win_long(dst)
    
    if not os.path.exists(src_long):
        print(f"  [MISSING] {src.name}")
        return False
        
    safe_mkdir(dst.parent)
    
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

def run():
    print("=== Reorganizing data_pipeline datasets and models ===")
    
    # 1. Target Language
    t_train = DATASETS_DIR / "target_language" / "train"
    t_val = DATASETS_DIR / "target_language" / "validation"
    t_test = DATASETS_DIR / "target_language" / "test"
    
    safe_copy_or_link(DATASETS_DIR / "finetuning" / "train.csv", t_train / "train.csv")
    safe_copy_or_link(REPO_ROOT / "data" / "Nadil" / "train.txt", t_train / "train.txt")
    safe_copy_or_link(DATASETS_DIR / "finetuning" / "val.csv", t_val / "val.csv")
    safe_copy_or_link(REPO_ROOT / "data" / "Nadil" / "valid.txt", t_val / "valid.txt")
    safe_copy_or_link(REPO_ROOT / "data" / "Nadil" / "test.csv", t_test / "test.csv")
    
    # 2. Hybrid Benchmark
    prep = DATASETS_DIR / "preprocessed"
    hb_flores = DATASETS_DIR / "hybrid_benchmark" / "flores_plus"
    hb_wili = DATASETS_DIR / "hybrid_benchmark" / "wili_2018"
    hb_common = DATASETS_DIR / "hybrid_benchmark" / "commonlid"
    
    safe_copy_or_link(prep / "flores_plus.jsonl", hb_flores / "flores_plus.jsonl")
    safe_copy_or_link(prep / "flores_plus_integrated.jsonl", hb_flores / "flores_plus_integrated.jsonl")
    safe_copy_or_link(prep / "wili-2018.jsonl", hb_wili / "wili-2018.jsonl")
    safe_copy_or_link(prep / "wili-2018_integrated.jsonl", hb_wili / "wili-2018_integrated.jsonl")
    safe_copy_or_link(prep / "commonlid.jsonl", hb_common / "commonlid.jsonl")
    safe_copy_or_link(prep / "commonlid_integrated.jsonl", hb_common / "commonlid_integrated.jsonl")
    
    # 3. Hybrid Finetune
    hf_mixed = DATASETS_DIR / "hybrid_finetune" / "replay_mixed"
    safe_copy_or_link(DATASETS_DIR / "finetuning" / "train_11lang_uniform.csv", hf_mixed / "train_11lang_uniform.csv")
    safe_copy_or_link(DATASETS_DIR / "finetuning" / "val_11lang_uniform.csv", hf_mixed / "val_11lang_uniform.csv")
    safe_copy_or_link(DATASETS_DIR / "raw_download" / "sanskrit_classic" / "combined.txt", DATASETS_DIR / "hybrid_finetune" / "sanskrit_devanagari" / "combined.txt")
    
    # 4. Benchmark Results
    bench_res = DATASETS_DIR / "benchmark_results"
    res_00 = bench_res / "00_traditional_ml_baselines"
    res_01 = bench_res / "01_zero_shot"
    res_02 = bench_res / "02_target_only"
    res_03 = bench_res / "03_multilingual_rehearsal"
    
    safe_copy_or_link(REPO_ROOT / "results" / "phase1_baselines_consistent.csv", res_00 / "phase1_baselines_consistent.csv")
    
    for f in list(bench_res.glob("*.csv")):
        name = f.name.lower()
        if "zero_shot" in name or (name.startswith("openlid_v2_") and "finetuned" not in name and "twostage" not in name):
            safe_copy_or_link(f, res_01 / f.name)
        elif "twostage" in name or "target3" in name or "no_rehearsal" in name:
            safe_copy_or_link(f, res_02 / f.name)
        elif "finetuned" in name or "rehearsal" in name or "replay" in name or "all_langs" in name:
            safe_copy_or_link(f, res_03 / f.name)
            
    # 5. Traditional ML Baselines
    ml_00 = MODELS_DIR / "00_traditional_ml_baselines"
    safe_copy_or_link(REPO_ROOT / "models" / "langid_model.pkl", ml_00 / "char_ngram_logreg" / "langid_model.pkl")
    safe_copy_or_link(REPO_ROOT / "models" / "langid_vectorizer.pkl", ml_00 / "char_ngram_logreg" / "langid_vectorizer.pkl")
    safe_copy_or_link(REPO_ROOT / "models" / "fasttext_finetuned.bin", ml_00 / "fasttext_scratch" / "fasttext_scratch.bin")
    safe_mkdir(ml_00 / "multinomial_nb")
    safe_mkdir(ml_00 / "linear_svm")
    safe_mkdir(ml_00 / "xgboost")
    safe_mkdir(ml_00 / "char_cnn")
    safe_mkdir(ml_00 / "char_bigru")
    
    # 6. Foundation Baseline Pretrained (Table 1)
    m_01 = MODELS_DIR / "01_baseline_pretrained"
    safe_copy_or_link(REPO_ROOT / "models" / "lid.176.bin", m_01 / "fasttext_lid176" / "lid.176.bin")
    safe_copy_or_link(REPO_ROOT / "models" / "lid.176.vec", m_01 / "fasttext_lid176" / "lid.176.vec")
    
    # 7. Local Target-Only SOTA Models (Table 2)
    m_02 = MODELS_DIR / "02_target_only_sota"
    ft_t = MODELS_DIR / "continual" / "target_only_exp" / "best"
    if ft_t.exists():
        for f in ft_t.glob("*"):
            safe_copy_or_link(f, m_02 / "fasttext_leaf_surgery" / f.name)
    safe_copy_or_link(REPO_ROOT / "models" / "finetuned" / "openlid_v3_target3.bin", m_02 / "openlid_v3" / "openlid_v3_target3.bin")
    safe_copy_or_link(REPO_ROOT / "models" / "finetuned" / "fasttext_lid176_target3.bin", m_02 / "fasttext_lid176" / "fasttext_lid176_target3.bin")
    safe_copy_or_link(REPO_ROOT / "models" / "finetuned" / "glotlid_2104_finetuned.bin", m_02 / "glotlid_v3" / "glotlid_2104_finetuned.bin")
    safe_copy_or_link(REPO_ROOT / "models" / "finetuned" / "nllb_lid_220_finetuned.bin", m_02 / "nllb_lid218" / "nllb_lid_220_finetuned.bin")
    
    # 8. Global Rehearsal SOTA Models (Table 3)
    m_03 = MODELS_DIR / "03_global_rehearsal_sota"
    ft_r = MODELS_DIR / "continual" / "11lang_rehearsal_exp" / "best"
    if ft_r.exists():
        for f in ft_r.glob("*"):
            safe_copy_or_link(f, m_03 / "fasttext_continual" / f.name)
    safe_copy_or_link(REPO_ROOT / "models" / "openlid_v3_finetuned.bin", m_03 / "openlid_v3" / "openlid_v3_finetuned.bin")
    safe_copy_or_link(REPO_ROOT / "models" / "fasttext_11lang_scratch.bin", m_03 / "fasttext" / "fasttext_11lang_scratch.bin")

    print("\n[SUCCESS] Reorganization script completed successfully!")

if __name__ == "__main__":
    run()
