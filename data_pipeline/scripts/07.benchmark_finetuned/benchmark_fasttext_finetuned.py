import os
import json
import glob
import pandas as pd
import fasttext

# Auto-resolve the project root if running manually
if not os.path.exists("Makefile") and os.path.exists("../../Makefile"):
    os.chdir("../../")

input_dir = 'datasets/preprocessed'
output_dir = 'datasets/benchmark_results'
model_path = '../models/fasttext_finetuned.bin'
if not os.path.exists(model_path):
    model_path = 'models/fasttext_finetuned.bin'

print(f"Loading finetuned model from {model_path}...")
model = fasttext.load_model(model_path)
model_name = "fastText LID-176 Finetuned"

dataset_files = glob.glob(os.path.join(input_dir, "*.jsonl"))
if not dataset_files:
    print(f"No datasets found in {input_dir}.")

for file_path in dataset_files:
    dataset_name = os.path.splitext(os.path.basename(file_path))[0]
    print(f"\nLoading {dataset_name}...")
    
    records = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
                
    df = pd.DataFrame(records)
    if df.empty:
        continue
        
    texts = df["text"].astype(str).str.replace("\n", " ").tolist()
    print(f"Evaluating {len(texts)} samples with {model_name}...")
    preds, _ = model.predict(texts, k=1)
    
    results = df[["text", "label", "source"]].copy()
    
    results["true_label"] = df["label"]
    results["predicted_label"] = [p[0].replace("__label__", "") for p in preds]
    
    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, f"fasttext_lid_176_finetuned_augmented_{dataset_name}.csv")
    results.to_csv(out_file, index=False)
    print(f"Saved predictions to {out_file}")
