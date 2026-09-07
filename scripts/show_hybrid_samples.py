import os
import sys
import json

def fix_win_path(path):
    abs_path = os.path.abspath(path)
    if sys.platform == "win32" and not abs_path.startswith("\\\\?\\"):
        return "\\\\?\\" + abs_path
    return abs_path

sys.stdout.reconfigure(encoding='utf-8')

base_dir = fix_win_path('data_pipeline/datasets/preprocessed')
benchmarks = ['flores_plus.jsonl', 'commonlid.jsonl', 'wili-2018.jsonl']

for fname in benchmarks:
    path = os.path.join(base_dir, fname)
    print(f"==========================================")
    print(f"HYBRID DATASET: {fname}")
    print(f"==========================================")
    
    nadil_samples = {}
    other_samples = []
    
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            rec = json.loads(line)
            lbl = rec.get("label")
            src = rec.get("source")
            if src == "Nadil":
                if lbl not in nadil_samples:
                    nadil_samples[lbl] = rec
            elif src != "Nadil" and len(other_samples) < 5:
                other_samples.append(rec)
                
    print("\n1. Injected Test Dataset Samples (Sinhala-script Target Languages):")
    for lbl, s in nadil_samples.items():
        text_snippet = s['text'][:90]
        print(f"  • [{lbl.upper()}] text: '{text_snippet}...' | source: '{s['source']}'")
        
    print("\n2. Global Benchmark Samples (Other Languages & Scripts):")
    for s in other_samples:
        text_snippet = s['text'][:90]
        print(f"  • [{s['label']}] text: '{text_snippet}...' | source: '{s['source']}'")
    print("\n")
