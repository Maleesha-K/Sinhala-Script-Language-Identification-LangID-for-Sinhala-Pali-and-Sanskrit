import os
import shutil
import json

def to_win_long(path):
    p_abs = os.path.abspath(path)
    if os.name == 'nt' and not p_abs.startswith('\\\\?\\'):
        return '\\\\?\\' + p_abs
    return p_abs

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PIPELINE = os.path.join(REPO_ROOT, "data_pipeline")
PIPELINE = os.path.join(REPO_ROOT, "pipeline")

print(f"Migrating and organizing from {DATA_PIPELINE} into {PIPELINE}...")

# ----------------------------------------------------
# 1. Migrate & Organize Scripts
# ----------------------------------------------------
SCRIPT_MAPPINGS = {
    # 01.download
    os.path.join(DATA_PIPELINE, "scripts", "01.download"): os.path.join(PIPELINE, "scripts", "01.download"),
    # 02.preprocess
    os.path.join(DATA_PIPELINE, "scripts", "02.preprocess"): os.path.join(PIPELINE, "scripts", "02.preprocess"),
    # 03.dataset_checking
    os.path.join(DATA_PIPELINE, "scripts", "03.dataset_checking"): os.path.join(PIPELINE, "scripts", "03.dataset_checking"),
    # 04.benchmark -> 04.benchmark_zero_shot
    os.path.join(DATA_PIPELINE, "scripts", "04.benchmark"): os.path.join(PIPELINE, "scripts", "04.benchmark_zero_shot"),
    # 05.finetune_dataset -> 05.prepare_datasets
    os.path.join(DATA_PIPELINE, "scripts", "05.finetune_dataset"): os.path.join(PIPELINE, "scripts", "05.prepare_datasets"),
    # 06.finetune_models -> 06.train_models
    os.path.join(DATA_PIPELINE, "scripts", "06.finetune_models"): os.path.join(PIPELINE, "scripts", "06.train_models"),
    # 07.benchmark_finetuned -> 07.benchmark_evaluation
    os.path.join(DATA_PIPELINE, "scripts", "07.benchmark_finetuned"): os.path.join(PIPELINE, "scripts", "07.benchmark_evaluation"),
}

for src_dir, dst_dir in SCRIPT_MAPPINGS.items():
    src_long = to_win_long(src_dir)
    dst_long = to_win_long(dst_dir)
    if os.path.exists(src_long):
        os.makedirs(dst_long, exist_ok=True)
        for item in os.listdir(src_long):
            s_item = os.path.join(src_long, item)
            d_item = os.path.join(dst_long, item)
            if os.path.isfile(s_item):
                shutil.copy2(s_item, d_item)
                print(f"Copied script: {item} -> {os.path.basename(dst_dir)}")

# Copy traditional baseline scripts into 00.traditional_baselines
trad_dir = to_win_long(os.path.join(PIPELINE, "scripts", "00.traditional_baselines"))
os.makedirs(trad_dir, exist_ok=True)
for base_script in ["benchmark_phase1_baselines.py", "benchmark_phase2_baselines.py"]:
    src_p = to_win_long(os.path.join(REPO_ROOT, "scripts", base_script))
    if os.path.exists(src_p):
        shutil.copy2(src_p, os.path.join(trad_dir, base_script))
        print(f"Copied baseline script: {base_script} -> 00.traditional_baselines")

# ----------------------------------------------------
# 2. Populate Models configs, weights & READMEs
# ----------------------------------------------------
# Copy char_ngram_logreg weights
src_logreg = to_win_long(os.path.join(DATA_PIPELINE, "models", "00_traditional_ml_baselines", "char_ngram_logreg"))
dst_logreg = to_win_long(os.path.join(PIPELINE, "models", "00_traditional_ml_baselines", "char_ngram_logreg"))
if os.path.exists(src_logreg):
    os.makedirs(dst_logreg, exist_ok=True)
    for f in os.listdir(src_logreg):
        s = os.path.join(src_logreg, f)
        d = os.path.join(dst_logreg, f)
        if os.path.isfile(s):
            shutil.copy2(s, d)
            print(f"Copied logreg model: {f}")

# Copy fasttext_leaf_surgery configs
src_leaf = to_win_long(os.path.join(DATA_PIPELINE, "models", "02_target_only_sota", "fasttext_leaf_surgery"))
dst_leaf = to_win_long(os.path.join(PIPELINE, "models", "02_target_only_sota", "fasttext_leaf_surgery"))
if os.path.exists(src_leaf):
    os.makedirs(dst_leaf, exist_ok=True)
    for f in ["config.json", "vocab.json"]:
        s = os.path.join(src_leaf, f)
        if os.path.exists(s):
            shutil.copy2(s, os.path.join(dst_leaf, f))
            print(f"Copied leaf surgery config: {f}")

# Copy fasttext_continual configs
src_cont = to_win_long(os.path.join(DATA_PIPELINE, "models", "03_global_rehearsal_sota", "fasttext_continual"))
dst_cont = to_win_long(os.path.join(PIPELINE, "models", "03_global_rehearsal_sota", "fasttext_continual"))
if os.path.exists(src_cont):
    os.makedirs(dst_cont, exist_ok=True)
    for f in ["config.json", "vocab.json"]:
        s = os.path.join(src_cont, f)
        if os.path.exists(s):
            shutil.copy2(s, os.path.join(dst_cont, f))
            print(f"Copied continual config: {f}")

print("\nReorganization script copy step completed!")
