import os
import sys
import json
import gzip
import pandas as pd

def to_win_long(path):
    p_abs = os.path.abspath(path)
    if os.name == 'nt' and not p_abs.startswith('\\\\?\\'):
        return '\\\\?\\' + p_abs
    return p_abs

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASETS_DIR = os.path.join(REPO_ROOT, "pipeline", "datasets")

print(f"Working on datasets in: {DATASETS_DIR}")

# ==========================================
# 1. Multi-format for hybrid_finetune/replay_mixed
# ==========================================
def process_replay_mixed():
    replay_dir = os.path.join(DATASETS_DIR, "hybrid_finetune", "replay_mixed")
    splits = [
        ("train_11lang_uniform.csv", "train_11lang_uniform.txt", "train_11lang_uniform.jsonl"),
        ("val_11lang_uniform.csv", "val_11lang_uniform.txt", "val_11lang_uniform.jsonl")
    ]
    
    for csv_name, txt_name, jsonl_name in splits:
        csv_path = to_win_long(os.path.join(replay_dir, csv_name))
        txt_path = to_win_long(os.path.join(replay_dir, txt_name))
        jsonl_path = to_win_long(os.path.join(replay_dir, jsonl_name))
        
        if not os.path.exists(csv_path):
            print(f"Skipping {csv_name}, file not found.")
            continue
            
        print(f"Processing {csv_name} -> {txt_name}, {jsonl_name}...")
        df = pd.read_csv(csv_path)
        
        # fastText txt format
        with open(txt_path, 'w', encoding='utf-8') as f_txt:
            for _, row in df.iterrows():
                lbl = str(row['label']).strip()
                txt = str(row['text']).replace('\n', ' ').replace('\r', ' ').strip()
                f_txt.write(f"__label__{lbl} {txt}\n")
                
        # jsonl format
        with open(jsonl_path, 'w', encoding='utf-8') as f_jsonl:
            for _, row in df.iterrows():
                record = {
                    "id": row.get('id', ''),
                    "text": str(row['text']).strip(),
                    "label": str(row['label']).strip(),
                    "source": str(row.get('source', '')).strip()
                }
                f_jsonl.write(json.dumps(record, ensure_ascii=False) + '\n')
                
        print(f"  Created {txt_name} ({os.path.getsize(txt_path) / (1024*1024):.2f} MB)")
        print(f"  Created {jsonl_name} ({os.path.getsize(jsonl_path) / (1024*1024):.2f} MB)")

# ==========================================
# 2. Multi-format for hybrid_finetune/sanskrit_devanagari
# ==========================================
def process_sanskrit_devanagari():
    san_dir = os.path.join(DATASETS_DIR, "hybrid_finetune", "sanskrit_devanagari")
    txt_src = to_win_long(os.path.join(san_dir, "combined.txt"))
    csv_out = to_win_long(os.path.join(san_dir, "sanskrit_devanagari.csv"))
    ft_out = to_win_long(os.path.join(san_dir, "sanskrit_devanagari.txt"))
    jsonl_out = to_win_long(os.path.join(san_dir, "sanskrit_devanagari.jsonl"))
    
    if not os.path.exists(txt_src):
        print("combined.txt not found, skipping.")
        return
        
    print(f"Processing Sanskrit Devanagari combined.txt -> CSV, fastText, JSONL...")
    records = []
    with open(txt_src, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            cleaned = line.strip()
            if cleaned:
                records.append({
                    "id": f"san_deva_{idx+1}",
                    "text": cleaned,
                    "label": "san_Deva",
                    "source": "surajp/sanskrit_classic"
                })
                
    df = pd.DataFrame(records)
    df.to_csv(csv_out, index=False, encoding='utf-8')
    print(f"  Created sanskrit_devanagari.csv ({len(df)} rows, {os.path.getsize(csv_out) / (1024*1024):.2f} MB)")
    
    with open(ft_out, 'w', encoding='utf-8') as f_ft:
        for r in records:
            txt_clean = r["text"].replace('\n', ' ').replace('\r', ' ').strip()
            f_ft.write(f"__label__san_Deva {txt_clean}\n")
    print(f"  Created sanskrit_devanagari.txt ({os.path.getsize(ft_out) / (1024*1024):.2f} MB)")
    
    with open(jsonl_out, 'w', encoding='utf-8') as f_jsonl:
        for r in records:
            f_jsonl.write(json.dumps(r, ensure_ascii=False) + '\n')
    print(f"  Created sanskrit_devanagari.jsonl ({os.path.getsize(jsonl_out) / (1024*1024):.2f} MB)")

# ==========================================
# 3. Add standalone Aya extraction script
# ==========================================
def write_aya_extractor():
    aya_dir = os.path.join(DATASETS_DIR, "hybrid_finetune", "aya_dataset")
    script_path = to_win_long(os.path.join(aya_dir, "extract_aya_rehearsal.py"))
    code = '''"""
Extract Background Rehearsal Languages from CohereLabs/aya_dataset
-----------------------------------------------------------------
Downloads and filters the 7 non-Sanskrit rehearsal languages:
eng, tam, hin, ben, arb, fra, deu.
"""

import os
import json
from datasets import load_dataset

LANG_MAP = {
    "eng": "en",
    "tam": "ta",
    "hin": "hi",
    "ben": "bn",
    "arb": "ar",
    "fra": "fr",
    "deu": "de"
}

TRAIN_QUOTA = 5000
VAL_QUOTA = 500
TOTAL_QUOTA = TRAIN_QUOTA + VAL_QUOTA

def main():
    print("Loading CohereLabs/aya_dataset (streaming)...")
    ds = load_dataset("CohereLabs/aya_dataset", split="train", streaming=True)
    
    train_records = []
    val_records = []
    counts = {lang: 0 for lang in LANG_MAP}
    
    for row in ds:
        lang_code = row.get("language_code")
        if lang_code in LANG_MAP and counts[lang_code] < TOTAL_QUOTA:
            rec = {
                "text": row["inputs"],
                "label": lang_code,
                "source": "aya_dataset"
            }
            if counts[lang_code] < TRAIN_QUOTA:
                train_records.append(rec)
            else:
                val_records.append(rec)
            counts[lang_code] += 1
            
        if all(counts[l] == TOTAL_QUOTA for l in LANG_MAP):
            break
            
    print(f"Successfully sampled {sum(counts.values())} records across 7 languages:")
    for l, c in counts.items():
        print(f"  {l}: {c} records")

    with open("aya_rehearsal_sample.jsonl", "w", encoding="utf-8") as f:
        for r in train_records[:100]:
            f.write(json.dumps(r, ensure_ascii=False) + "\\n")
    print("Saved sample to aya_rehearsal_sample.jsonl")

if __name__ == "__main__":
    main()
'''
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(code)
    print("  Created extract_aya_rehearsal.py")

# ==========================================
# 4. Add evaluation compute_metrics.py to benchmark_results
# ==========================================
def write_compute_metrics():
    res_dir = os.path.join(DATASETS_DIR, "benchmark_results")
    script_path = to_win_long(os.path.join(res_dir, "compute_metrics.py"))
    code = '''"""
Benchmark Evaluation Metrics Calculator
----------------------------------------
Computes Accuracy, Macro F1, and per-class metrics across benchmark prediction CSVs.
Supports Windows long path names safely.
"""

import os
import sys
import glob
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, classification_report

def to_win_long(path):
    p_abs = os.path.abspath(path)
    if os.name == 'nt' and not p_abs.startswith('\\\\\\\\?\\\\'):
        return '\\\\\\\\?\\\\' + p_abs
    return p_abs

def evaluate_csv(filepath):
    try:
        df = pd.read_csv(to_win_long(filepath))
        if 'true_label' not in df.columns or 'predicted_label' not in df.columns:
            return None
            
        y_true = df['true_label'].astype(str)
        y_pred = df['predicted_label'].astype(str)
        
        acc = accuracy_score(y_true, y_pred)
        macro_f1 = f1_score(y_true, y_pred, average='macro', zero_division=0)
        return {
            "file": os.path.basename(filepath),
            "samples": len(df),
            "accuracy": acc,
            "macro_f1": macro_f1
        }
    except Exception as e:
        print(f"Error evaluating {filepath}: {e}")
        return None

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_files = glob.glob(os.path.join(base_dir, "**", "*.csv"), recursive=True)
    
    print(f"Found {len(csv_files)} benchmark CSV files.")
    results = []
    for csv_file in sorted(csv_files):
        res = evaluate_csv(csv_file)
        if res:
            results.append(res)
            
    if results:
        res_df = pd.DataFrame(results)
        print("\\n=== Benchmark Summary ===")
        print(res_df.to_string(index=False))

if __name__ == '__main__':
    main()
'''
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(code)
    print("  Created compute_metrics.py in benchmark_results")

if __name__ == "__main__":
    process_replay_mixed()
    process_sanskrit_devanagari()
    write_aya_extractor()
    write_compute_metrics()
    print("Dataset multi-format generation complete!")
