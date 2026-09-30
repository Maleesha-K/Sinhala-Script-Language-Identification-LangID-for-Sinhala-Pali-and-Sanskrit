"""Download Continual FastText Leaf Surgery model from Hugging Face Hub.

Usage:
    python scripts/download_models.py [--repo-id script-langid/fasttext-leaf-surgery-11lang]
"""

import os
import argparse
from pathlib import Path
from huggingface_hub import snapshot_download

DEFAULT_REPO_ID = "script-langid/fasttext-leaf-surgery-11lang"
DEFAULT_TARGET_DIR = "data_pipeline/models/continual/11lang_rehearsal_exp/best"

def main():
    parser = argparse.ArgumentParser(description="Download model from Hugging Face Hub")
    parser.add_argument("--repo-id", default=DEFAULT_REPO_ID, help="Hugging Face repo ID")
    parser.add_argument("--dest", default=DEFAULT_TARGET_DIR, help="Destination directory")
    args = parser.parse_args()

    dest = Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {args.repo_id} from Hugging Face Hub to {dest}...")
    snapshot_download(
        repo_id=args.repo_id,
        local_dir=str(dest),
        allow_patterns=["config.json", "vocab.json", "weights.pt", "README.md", "*.json"]
    )
    print(f"Model downloaded successfully to {dest}!")

if __name__ == "__main__":
    main()
