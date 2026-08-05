import argparse
import os
import json
import csv

def preprocess_data(input_dir, output_file):
    """
    Transforms the raw dataset into a standardized JSONL format.
    Standard format: {"text": "...", "label": "...", "source": "..."}
    """
    print(f"Preprocessing data from {input_dir}...")
    
    raw_file_path = os.path.join(input_dir, "raw_data.txt")
    if not os.path.exists(raw_file_path):
        print(f"Error: {raw_file_path} not found.")
        return

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    processed_count = 0
    with open(raw_file_path, "r", encoding="utf-8") as f_in, \
         open(output_file, "w", encoding="utf-8") as f_out:
         
        reader = csv.DictReader(f_in)
        for row in reader:
            # Transform to standard schema
            standard_record = {
                "text": row["text"],
                "label": row["label"],
                "source": "flores_plus"
            }
            # Write as JSON Lines
            f_out.write(json.dumps(standard_record, ensure_ascii=False) + "\n")
            processed_count += 1
            
    print(f"Successfully processed {processed_count} records to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preprocess FLORES+ dataset")
    parser.add_argument("--input", type=str, required=True, help="Input directory containing raw data")
    parser.add_argument("--output", type=str, required=True, help="Output file path (.jsonl)")
    args = parser.parse_args()
    
    preprocess_data(args.input, args.output)
