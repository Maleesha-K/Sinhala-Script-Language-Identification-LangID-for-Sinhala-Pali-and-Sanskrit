output_dir = 'datasets/raw_download/flores_plus'

import os
# Auto-resolve the project root if running manually
if not os.path.exists("Makefile") and os.path.exists("../../Makefile"):
    os.chdir("../../")

import os
from datasets import load_dataset

print(f"Downloading FLORES+ dataset to {output_dir}...")
os.makedirs(output_dir, exist_ok=True)

# Load the dataset (devtest split) using HF_TOKEN from environment
hf_token = os.environ.get("HF_TOKEN")
if not hf_token:
    print("Warning: HF_TOKEN environment variable not set. Download may fail if dataset is gated.")

ds = load_dataset("openlanguagedata/flores_plus", split="devtest", token=hf_token)

# Save the dataset to the output directory as JSONL
raw_file_path = os.path.join(output_dir, "raw_data.jsonl")
ds.to_json(raw_file_path, force_ascii=False)

print(f"Downloaded FLORES+ dataset and saved to {raw_file_path}")

