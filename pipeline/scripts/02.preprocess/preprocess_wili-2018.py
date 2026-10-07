import os
import json

proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
os.chdir(proj_root)

input_dir = os.path.join(proj_root, "data_pipeline", "datasets", "raw_download", "wili-2018")
output_file = os.path.join(proj_root, "data_pipeline", "datasets", "preprocessed", "wili-2018.jsonl")

print(f"Preprocessing data from {input_dir}...")

splits = [("x_train.txt", "y_train.txt"), ("x_test.txt", "y_test.txt")]

missing = [
    fname for pair in splits for fname in pair
    if not os.path.exists(os.path.join(input_dir, fname))
]
if missing:
    print(f"Error: missing files in {input_dir}: {missing}")
else:
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    processed_count = 0
    with open(output_file, "w", encoding="utf-8") as f_out:
        for x_name, y_name in splits:
            x_path = os.path.join(input_dir, x_name)
            y_path = os.path.join(input_dir, y_name)
            
            with open(x_path, "r", encoding="utf-8") as f_x, \
                 open(y_path, "r", encoding="utf-8") as f_y:
                for text_line, label_line in zip(f_x, f_y):
                    text = text_line.strip()
                    label = label_line.strip()
                    if text and label:
                        standard_record = {
                            "text": text,
                            "label": label,
                            "source": "wili-2018"
                        }
                        f_out.write(json.dumps(standard_record, ensure_ascii=False) + "\n")
                        processed_count += 1
                        
    print(f"Successfully processed {processed_count} records to {output_file}")
