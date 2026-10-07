"""Create a clean, separate folder structure under pipeline/ for datasets, models, and scripts."""

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PIPELINE_ROOT = REPO_ROOT / "pipeline"

def to_win_long(p: Path) -> str:
    s = str(p.resolve())
    if os.name == "nt" and not s.startswith("\\\\?\\"):
        return "\\\\?\\" + s
    return s

dirs = [
    # Datasets
    "datasets/target_language/train",
    "datasets/target_language/validation",
    "datasets/target_language/test",
    "datasets/hybrid_benchmark/flores_plus",
    "datasets/hybrid_benchmark/wili_2018",
    "datasets/hybrid_benchmark/commonlid",
    "datasets/hybrid_finetune/aya_dataset",
    "datasets/hybrid_finetune/sanskrit_devanagari",
    "datasets/hybrid_finetune/replay_mixed",
    "datasets/benchmark_results/00_traditional_ml_baselines",
    "datasets/benchmark_results/01_zero_shot",
    "datasets/benchmark_results/02_target_only",
    "datasets/benchmark_results/03_multilingual_rehearsal",
    
    # Models
    "models/00_traditional_ml_baselines/multinomial_nb",
    "models/00_traditional_ml_baselines/linear_svm",
    "models/00_traditional_ml_baselines/char_ngram_logreg",
    "models/00_traditional_ml_baselines/xgboost",
    "models/00_traditional_ml_baselines/fasttext_scratch",
    "models/00_traditional_ml_baselines/char_cnn",
    "models/00_traditional_ml_baselines/char_bigru",
    "models/01_baseline_pretrained/fasttext_lid176",
    "models/01_baseline_pretrained/openlid_v3",
    "models/01_baseline_pretrained/glotlid_v3",
    "models/01_baseline_pretrained/nllb_lid218",
    "models/01_baseline_pretrained/conlid",
    "models/01_baseline_pretrained/xlm_roberta_base",
    "models/02_target_only_sota/fasttext_leaf_surgery",
    "models/02_target_only_sota/openlid_v3",
    "models/02_target_only_sota/glotlid_v3",
    "models/02_target_only_sota/nllb_lid218",
    "models/02_target_only_sota/conlid",
    "models/02_target_only_sota/xlm_roberta",
    "models/03_global_rehearsal_sota/fasttext_continual",
    "models/03_global_rehearsal_sota/openlid_v3",
    "models/03_global_rehearsal_sota/glotlid_v3",
    "models/03_global_rehearsal_sota/nllb_lid218",
    "models/03_global_rehearsal_sota/conlid",
    "models/03_global_rehearsal_sota/xlm_roberta",
    
    # Scripts
    "scripts/00.traditional_baselines",
    "scripts/01.download",
    "scripts/02.preprocess",
    "scripts/03.dataset_checking",
    "scripts/04.benchmark_zero_shot",
    "scripts/05.prepare_datasets",
    "scripts/06.train_models",
    "scripts/07.benchmark_evaluation",
]

def run():
    print(f"Creating pipeline directory scaffold at: {PIPELINE_ROOT}")
    created_count = 0
    for rel in dirs:
        d_path = PIPELINE_ROOT / rel
        long_path = to_win_long(d_path)
        os.makedirs(long_path, exist_ok=True)
        
        gitkeep = Path(long_path) / ".gitkeep"
        if not gitkeep.exists():
            with open(gitkeep, "w", encoding="utf-8") as f:
                f.write("")
        created_count += 1
        
    print(f"[SUCCESS] Created {created_count} structured directories under pipeline/ with .gitkeep")

if __name__ == "__main__":
    run()
