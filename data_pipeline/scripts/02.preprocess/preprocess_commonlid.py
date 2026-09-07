import os
import json

proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
os.chdir(proj_root)

input_dir = os.path.join(proj_root, "data_pipeline", "datasets", "raw_download", "commonlid")
output_file = os.path.join(proj_root, "data_pipeline", "datasets", "preprocessed", "commonlid.jsonl")

print(f"Preprocessing data from {input_dir}...")
raw_file_path = os.path.join(input_dir, "raw_data.jsonl")

if not os.path.exists(raw_file_path):
    print(f"Error: {raw_file_path} not found.")
else:
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    processed_count = 0
    with open(raw_file_path, "r", encoding="utf-8") as f_in, \
         open(output_file, "w", encoding="utf-8") as f_out:
         
        for line in f_in:
            if not line.strip(): continue
            row = json.loads(line)
            lbl = row.get("tag", row.get("label", row.get("iso_639_3", "")))
            standard_record = {
                "text": row["text"],
                "label": lbl,
                "source": "commonlid"
            }
            f_out.write(json.dumps(standard_record, ensure_ascii=False) + "\n")
            processed_count += 1
            
    print(f"Successfully processed {processed_count} records to {output_file}")
