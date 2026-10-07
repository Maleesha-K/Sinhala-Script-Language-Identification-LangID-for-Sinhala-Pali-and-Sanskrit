"""
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
    if os.name == 'nt' and not p_abs.startswith('\\\\?\\'):
        return '\\\\?\\' + p_abs
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
        print("\n=== Benchmark Summary ===")
        print(res_df.to_string(index=False))

if __name__ == '__main__':
    main()
