import os
import json
import csv
import re

# Auto-resolve the project root if running manually
if not os.path.exists("Makefile") and os.path.exists("../../Makefile"):
    os.chdir("../../")

proj_root = os.path.abspath(".")

print("Loading Nadil test dataset...")
nadil_test_path = os.path.join(proj_root, "data", "Nadil", "test.csv")
if not os.path.exists(nadil_test_path):
    nadil_test_path = os.path.join(proj_root, "data_pipeline", "datasets", "finetuning", "test.csv")

if not os.path.exists(nadil_test_path):
    raise FileNotFoundError(f"Could not find test dataset at {nadil_test_path}")

nadil_records = []
with open(nadil_test_path, mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        text_val = str(row.get('text', '')).strip()
        label_val = str(row.get('label', '')).strip()
        if text_val and label_val:
            nadil_records.append({
                "text": text_val,
                "label": label_val,
                "source": "Nadil",
            })

print(f"Loaded {len(nadil_records)} test records from Nadil dataset.")

benchmarks = [
    os.path.join('data_pipeline', 'datasets', 'preprocessed', 'flores_plus.jsonl'),
    os.path.join('data_pipeline', 'datasets', 'preprocessed', 'commonlid.jsonl'),
    os.path.join('data_pipeline', 'datasets', 'preprocessed', 'wili-2018.jsonl'),
    os.path.join('datasets', 'preprocessed', 'flores_plus.jsonl'),
    os.path.join('datasets', 'preprocessed', 'commonlid.jsonl'),
    os.path.join('datasets', 'preprocessed', 'wili-2018.jsonl'),
]

# Explicit labels to remove (Sinhala script target languages)
explicit_sinhala_script_labels = {
    'sin_Sinh', 'sin', 'sinhala', 'si',
    'pli', 'pali', 'pli_Latn', 'pli_Sinh', 'pi',
    'san_Sinh', 'sanskrit'
}

def is_devanagari_sanskrit(record):
    lbl = str(record.get("label", "")).strip()
    src = str(record.get("source", "")).strip()
    txt = str(record.get("text", "")).strip()
    
    if lbl in ['san_Deva', 'sa']:
        return True
    
    if lbl == 'san':
        # If source is known Sinhala script source, it is NOT Devanagari
        if src in ['DCS', 'SansinNT', 'SiDiaC-v2', 'Nadil']:
            return False
        # If text contains Devanagari characters, it IS Devanagari Sanskrit
        if re.search(r'[\u0900-\u097F]', txt):
            return True 
        # If text contains Sinhala characters, it is NOT Devanagari
        if re.search(r'[\u0D80-\u0DFF]', txt):
            return False
        # Default for raw benchmarks (FLORES+, WiLI-2018) is Devanagari Sanskrit
        return True
        
    return False

processed_files = set()

for benchmark_file in benchmarks:
    abs_bench = os.path.abspath(benchmark_file)
    if abs_bench in processed_files or not os.path.exists(benchmark_file):
        continue
    processed_files.add(abs_bench)
    
    print(f"Processing {benchmark_file}...")
    valid_records = []
    removed_count = 0
    devanagari_kept = 0
    
    with open(benchmark_file, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            record = json.loads(line)
            lbl = str(record.get("label", "")).strip()
            
            # Check if this record is Devanagari Sanskrit
            if is_devanagari_sanskrit(record):
                record["label"] = "san_Deva"
                valid_records.append(record)
                devanagari_kept += 1
            elif lbl in explicit_sinhala_script_labels:
                removed_count += 1
            else:
                valid_records.append(record)
    
    print(f"Removed {removed_count} Sinhala-script target records from {benchmark_file}.")
    print(f"Preserved {devanagari_kept} Devanagari Sanskrit (san_Deva) records in {benchmark_file}.")
    
    # Inject Nadil test records
    valid_records.extend(nadil_records)
    
    # Save back to file
    with open(benchmark_file, "w", encoding="utf-8") as f:
        for record in valid_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            
    print(f"Injected {len(nadil_records)} Nadil test records. New total: {len(valid_records)} records in {benchmark_file}.\n")

print("Integration complete!")
