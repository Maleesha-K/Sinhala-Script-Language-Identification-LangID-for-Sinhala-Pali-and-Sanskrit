import argparse
import os
import json

def check_dataset(input_file):
    """
    Validates the standardized JSONL dataset to ensure it meets pipeline requirements.
    """
    print(f"Checking dataset at {input_file}...")
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    required_keys = {"text", "label"}
    valid_labels = {"sin", "san", "pal"} # Sinhala, Sanskrit, Pali
    
    errors = 0
    line_num = 0
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            line_num += 1
            try:
                record = json.loads(line)
                
                # Check schema
                if not required_keys.issubset(record.keys()):
                    print(f"Line {line_num}: Missing required keys. Found: {list(record.keys())}")
                    errors += 1
                
                # Check labels
                if record.get("label") not in valid_labels:
                    print(f"Line {line_num}: Invalid label '{record.get('label')}'. Expected one of {valid_labels}")
                    errors += 1
                    
                # Check text emptiness
                if not record.get("text") or not str(record.get("text")).strip():
                    print(f"Line {line_num}: Empty text field.")
                    errors += 1
                    
            except json.JSONDecodeError:
                print(f"Line {line_num}: Invalid JSON.")
                errors += 1

    if errors == 0:
        print(f"Dataset check passed! Validated {line_num} records.")
    else:
        print(f"Dataset check failed with {errors} errors.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check standardized dataset")
    parser.add_argument("--input", type=str, required=True, help="Input file path (.jsonl)")
    args = parser.parse_args()
    
    check_dataset(args.input)
