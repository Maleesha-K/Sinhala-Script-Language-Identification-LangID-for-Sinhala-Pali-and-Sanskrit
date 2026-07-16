import os
import csv
import re
import uuid

# Configuration
INPUT_DIR = r"c:\Users\User\Desktop\Vscode\Sinhala-Script Language Identification (LangID) for Sinhala, Pali and Sanskrit\Sinhala-Script-Language-Identification-LangID-for-Sinhala-Pali-and-Sanskrit\data\processed\raw\Pali"
OUTPUT_FILE = r"c:\Users\User\Desktop\Vscode\Sinhala-Script Language Identification (LangID) for Sinhala, Pali and Sanskrit\Sinhala-Script-Language-Identification-LangID-for-Sinhala-Pali-and-Sanskrit\data\processed\pali_only_dataset.csv"

def has_sinhala_chars(text):
    return bool(re.search(r'[\u0D80-\u0DFF]', text))

def clean_text(text):
    text = text.strip()
    return text

def process():
    rows = []
    
    for filename in os.listdir(INPUT_DIR):
        if not filename.endswith(".txt"):
            continue
            
        # Bypass Windows MAX_PATH length limitation
        filepath = "\\\\?\\" + os.path.abspath(os.path.join(INPUT_DIR, filename))
        source_name = filename.replace(".txt", "")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for i, line in enumerate(lines):
            cleaned = clean_text(line)
            # Apply same constraints as the master dataset: >10 chars and has Sinhala characters
            if len(cleaned) >= 10 and has_sinhala_chars(cleaned):
                row_id = f"pali_{uuid.uuid4().hex[:8]}"
                rows.append({
                    "id": row_id,
                    "text": cleaned,
                    "label": "pali",
                    "source": "raw_pali_folder",
                    "subcorpus": source_name,
                    "group_id": source_name,
                    "is_core": True,
                    "split": "train" # Default split to match schema
                })
                
    with open(OUTPUT_FILE, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ["id", "text", "label", "source", "subcorpus", "group_id", "is_core", "split"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        
    print(f"Dataset successfully created at {OUTPUT_FILE} with {len(rows)} rows.")

if __name__ == "__main__":
    process()
