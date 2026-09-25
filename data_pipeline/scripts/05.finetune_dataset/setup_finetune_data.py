# [COLAB SETUP]
import sys
import os

if "google.colab" in sys.modules:
    print("Running in Google Colab. Setting up environment...")
    
    # Mount Google Drive to persist the datasets and cloned repository
    from google.colab import drive
    drive.mount('/content/drive')
    
    repo_path = '/content/drive/MyDrive/Sinhala-Script-Language-Identification-LangID-for-Sinhala-Pali-and-Sanskrit'
    
    if not os.path.exists(repo_path):
        print(f"Cloning repository into {repo_path}...")
        os.makedirs('/content/drive/MyDrive', exist_ok=True)
        os.system(f'git clone https://github.com/Maleesha-K/Sinhala-Script-Language-Identification-LangID-for-Sinhala-Pali-and-Sanskrit.git {repo_path}')
        
    os.chdir(repo_path + '/data_pipeline')
    print("Installing base dependencies...")
    os.system('pip install -q pandas scikit-learn gdown')
    print("Setup complete!")


output_dir = 'datasets/finetuning'
preprocessed_dir = 'datasets/preprocessed'


import os
import subprocess
import pandas as pd
import json

# Auto-resolve the project root if running manually
if not os.path.exists("Makefile") and os.path.exists("../../Makefile"):
    os.chdir("../../")

os.makedirs(output_dir, exist_ok=True)

TRAIN_GDRIVE_LINK = "https://drive.google.com/uc?id=1RNioMTZEmS0g5FR8gWoYQtKgj3dvdmEi"
VAL_GDRIVE_LINK = "https://drive.google.com/uc?id=1NIjeKZvZwfIHr2XcHSj358PesUomUog5"

try:
    import gdown
except ImportError:
    print("Installing gdown...")
    subprocess.run(["pip", "install", "-q", "gdown"])
    import gdown

print(f"Downloading training dataset...")
train_csv_path = os.path.join(output_dir, "train.csv")
if not os.path.exists(train_csv_path): gdown.download(url=TRAIN_GDRIVE_LINK, output=train_csv_path)

print(f"\nDownloading validation dataset...")
val_csv_path = os.path.join(output_dir, "val.csv")
if not os.path.exists(val_csv_path): gdown.download(url=VAL_GDRIVE_LINK, output=val_csv_path)

# Unified Label Mapping
LABEL_MAP = {
    "sinhala": "sin",
    "sanskrit": "san",
    "pali": "pli"
}

def transform_to_jsonl(csv_path, jsonl_path):
    df = pd.read_csv(csv_path)
    if 'label' in df.columns:
        df['label'] = df['label'].str.lower().map(lambda x: LABEL_MAP.get(x, x))
    
    # Select columns as in benchmark transformation (id, text, label, source)
    cols_to_keep = ['id', 'text', 'label', 'source']
    # keep only existing columns
    cols_to_keep = [c for c in cols_to_keep if c in df.columns]
    
    df = df[cols_to_keep]
    
    with open(jsonl_path, 'w', encoding='utf-8') as f:
        for record in df.to_dict(orient='records'):
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    print(f"Transformed {csv_path} -> {jsonl_path} ({len(df)} records)")
    return df

print("\nTransforming datasets to JSONL...")
train_df = transform_to_jsonl(train_csv_path, os.path.join(output_dir, "train.jsonl"))
val_df = transform_to_jsonl(val_csv_path, os.path.join(output_dir, "val.jsonl"))


