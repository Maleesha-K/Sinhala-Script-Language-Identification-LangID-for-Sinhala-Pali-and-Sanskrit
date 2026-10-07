"""Populate pipeline/datasets/target_language with train, validation, and test splits.

Ensures:
1. train/ -> train.csv (60,285 rows), train.txt, train.jsonl
2. validation/ -> val.csv (6,986 rows), valid.txt, val.jsonl
3. test/ -> test.csv (7,047 rows), test.txt, test.jsonl, fasttext_eval_data.json
"""

import os
import sys
import shutil
import json
import pandas as pd
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PIPELINE_ROOT = REPO_ROOT / "pipeline"
TARGET_DIR = PIPELINE_ROOT / "datasets" / "target_language"

NADIL_DIR = REPO_ROOT / "data" / "Nadil"
PREP_DIR = REPO_ROOT / "data_pipeline" / "datasets" / "preprocessed"

def to_win_long(p: Path) -> str:
    s = str(p.resolve())
    if os.name == "nt" and not s.startswith("\\\\?\\"):
        return "\\\\?\\" + s
    return s

def link_or_copy(src: Path, dst: Path):
    src_long = to_win_long(src)
    dst_long = to_win_long(dst)
    
    if not os.path.exists(src_long):
        print(f"  [MISSING] {src}")
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

def csv_to_jsonl(csv_path: Path, jsonl_path: Path):
    if os.path.exists(to_win_long(jsonl_path)):
        print(f"  [EXISTS] {jsonl_path.name}")
        return
    print(f"  [GENERATING] {jsonl_path.name} from {csv_path.name}...")
    df = pd.read_csv(csv_path)
    with open(to_win_long(jsonl_path), 'w', encoding='utf-8') as f:
        for _, row in df.iterrows():
            rec = {
                "text": str(row.get('text', '')),
                "label": str(row.get('label', '')),
                "source": "Nadil"
            }
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    print(f"  [DONE] Created {jsonl_path.name} ({len(df)} records)")

def csv_to_fasttext_txt(csv_path: Path, txt_path: Path):
    if os.path.exists(to_win_long(txt_path)):
        print(f"  [EXISTS] {txt_path.name}")
        return
    print(f"  [GENERATING] {txt_path.name} from {csv_path.name}...")
    df = pd.read_csv(csv_path)
    with open(to_win_long(txt_path), 'w', encoding='utf-8') as f:
        for _, row in df.iterrows():
            lbl = str(row.get('label', '')).strip()
            txt = str(row.get('text', '')).strip().replace('\n', ' ')
            f.write(f"__label__{lbl} {txt}\n")
    print(f"  [DONE] Created {txt_path.name} ({len(df)} records)")

def populate():
    print("=== Populating pipeline/datasets/target_language ===")
    
    # 1. TRAIN SPLIT
    train_dir = TARGET_DIR / "train"
    os.makedirs(to_win_long(train_dir), exist_ok=True)
    
    link_or_copy(NADIL_DIR / "train.csv", train_dir / "train.csv")
    link_or_copy(NADIL_DIR / "train.txt", train_dir / "train.txt")
    csv_to_jsonl(train_dir / "train.csv", train_dir / "train.jsonl")
    
    train_readme = train_dir / "README.md"
    with open(to_win_long(train_readme), 'w', encoding='utf-8') as f:
        f.write("""# Target Language Training Split (N=60,285)

Trained strictly on the three target languages in Sinhala script.

## Class Distribution:
- **Sinhala (`sin_Sinh` / `sinhala`)**: 26,675 samples (44.25%)
- **Pali (`pli_Sinh` / `pali`)**: 23,490 samples (38.96%)
- **Sanskrit (`san_Sinh` / `sanskrit`)**: 10,120 samples (16.79%)
- **Total**: 60,285 samples

## Files:
- `train.csv`: Tabular CSV format (`text`, `label`)
- `train.txt`: fastText supervised training format (`__label__<lang> <text>`)
- `train.jsonl`: Standardized JSON Lines format
""")
    print("  [README] Created train/README.md")
    
    # 2. VALIDATION SPLIT
    val_dir = TARGET_DIR / "validation"
    os.makedirs(to_win_long(val_dir), exist_ok=True)
    
    link_or_copy(NADIL_DIR / "val.csv", val_dir / "val.csv")
    link_or_copy(NADIL_DIR / "valid.txt", val_dir / "valid.txt")
    csv_to_jsonl(val_dir / "val.csv", val_dir / "val.jsonl")
    
    val_readme = val_dir / "README.md"
    with open(to_win_long(val_readme), 'w', encoding='utf-8') as f:
        f.write("""# Target Language Validation Split (N=6,986)

Used for hyperparameter tuning and model checkpoint validation.

## Class Distribution:
- **Sinhala (`sin_Sinh` / `sinhala`)**: 2,895 samples (41.44%)
- **Pali (`pli_Sinh` / `pali`)**: 2,800 samples (40.08%)
- **Sanskrit (`san_Sinh` / `sanskrit`)**: 1,291 samples (18.48%)
- **Total**: 6,986 samples

## Files:
- `val.csv`: Tabular CSV format (`text`, `label`)
- `valid.txt`: fastText supervised validation format (`__label__<lang> <text>`)
- `val.jsonl`: Standardized JSON Lines format
""")
    print("  [README] Created validation/README.md")
    
    # 3. TEST SPLIT
    test_dir = TARGET_DIR / "test"
    os.makedirs(to_win_long(test_dir), exist_ok=True)
    
    link_or_copy(NADIL_DIR / "test.csv", test_dir / "test.csv")
    link_or_copy(NADIL_DIR / "fasttext_eval_data.json", test_dir / "fasttext_eval_data.json")
    
    # If nadil.jsonl exists in preprocessed, link it as test.jsonl
    if (PREP_DIR / "nadil.jsonl").exists():
        link_or_copy(PREP_DIR / "nadil.jsonl", test_dir / "test.jsonl")
    else:
        csv_to_jsonl(test_dir / "test.csv", test_dir / "test.jsonl")
        
    csv_to_fasttext_txt(test_dir / "test.csv", test_dir / "test.txt")
    
    test_readme = test_dir / "README.md"
    with open(to_win_long(test_readme), 'w', encoding='utf-8') as f:
        f.write("""# Target Language Held-Out Test Split (N=7,047)

Held-out benchmark evaluation split from the Nadil corpus. Used for Table 1, Table 2, and Table 3 reporting.

## Class Distribution:
- **Pali (`pli_Sinh` / `pali`)**: 3,027 samples (42.95%)
- **Sinhala (`sin_Sinh` / `sinhala`)**: 2,693 samples (38.22%)
- **Sanskrit (`san_Sinh` / `sanskrit`)**: 1,327 samples (18.83%)
- **Total**: 7,047 samples

## Files:
- `test.csv`: Tabular CSV format (`text`, `label`)
- `test.txt`: fastText supervised test format (`__label__<lang> <text>`)
- `test.jsonl`: Standardized JSON Lines format
- `fasttext_eval_data.json`: Pre-tokenized evaluation records for fastText benchmarks
""")
    print("  [README] Created test/README.md")
    
    print("\n[SUCCESS] Successfully populated pipeline/datasets/target_language!")

if __name__ == "__main__":
    populate()
