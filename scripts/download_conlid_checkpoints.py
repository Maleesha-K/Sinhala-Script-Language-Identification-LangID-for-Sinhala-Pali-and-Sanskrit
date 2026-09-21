import os
import sys
from huggingface_hub import snapshot_download

proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
checkpoints_dir = os.path.join(proj_root, "models", "benchmark", "ConLID", "checkpoints")

print(f"Downloading ConLID model checkpoints from Hugging Face ('epfl-nlp/ConLID') to {checkpoints_dir}...")
os.makedirs(checkpoints_dir, exist_ok=True)

snapshot_download(repo_id="epfl-nlp/ConLID", local_dir=checkpoints_dir)
print("[OK] ConLID checkpoints download complete!")
