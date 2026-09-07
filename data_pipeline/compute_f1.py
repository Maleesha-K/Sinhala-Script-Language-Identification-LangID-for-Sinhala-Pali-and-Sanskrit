import pandas as pd
from sklearn.metrics import f1_score
import os

datasets = ['flores_plus', 'commonlid', 'wili-2018']
base_dir = r'\\?\c:\Users\User\Desktop\Vscode\Sinhala-Script Language Identification (LangID) for Sinhala, Pali and Sanskrit\Sinhala-Script-Language-Identification-LangID-for-Sinhala-Pali-and-Sanskrit\data_pipeline\datasets\benchmark_results'
labels = ['sinhala', 'pali', 'sanskrit']

for d in datasets:
    file_path = os.path.join(base_dir, f'fasttext_lid_176_finetuned_augmented_{d}.csv')
    if not os.path.exists(file_path):
        continue
        
    df = pd.read_csv(file_path)
    print(f'\nDataset: {d}')
    for l in labels:
        y_true = (df['true_label'] == l).astype(int)
        y_pred = (df['predicted_label'] == l).astype(int)
        
        score = f1_score(y_true, y_pred, zero_division=0)
        print(f'  {l}: {score:.4f}')
