import pandas as pd
from sklearn.metrics import f1_score
import glob
import os
import sys

def main():
    base_dir = r"c:\Users\User\Desktop\Vscode\Sinhala-Script Language Identification (LangID) for Sinhala, Pali and Sanskrit\Sinhala-Script-Language-Identification-LangID-for-Sinhala-Pali-and-Sanskrit\data_pipeline\datasets\benchmark_results"
    
    files = glob.glob(os.path.join(base_dir, "*.csv"))
    if not files:
        print("No csv files found!")
        sys.exit(1)
        
    for file_path in files:
        if 'zero_shot' in file_path or 'tatoeba' in file_path:
            continue # Skip these or evaluate? We only need flores, commonlid, wili, nadil based on the final table
        
        df = pd.read_csv(file_path)
        ds_name = os.path.basename(file_path)
        print(f"\n--- {ds_name} ---")
        if 'true_label' not in df.columns:
            print("No true_label column.")
            continue
            
        labels = df['true_label'].unique()
        print(f"Labels found: {labels}")
        for label in labels:
            if pd.isna(label): continue
            
            y_true = (df['true_label'] == label).astype(int)
            y_pred = (df['predicted_label'] == label).astype(int)
            
            f1 = f1_score(y_true, y_pred)
            print(f"{label}: {f1:.4f}")

if __name__ == '__main__':
    main()
