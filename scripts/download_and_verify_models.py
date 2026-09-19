"""
================================================================================
Model Verification and Download Utility for 5 SOTA LangID Models
================================================================================
Checks and downloads the stock foundation models for:
  1. fastText LID-176
  2. OpenLID-v2
  3. NLLB LID-218
  4. GlotLID v3
  5. ConLID
and verifies local fine-tuned specialists.
================================================================================
"""

import os
import sys
import subprocess
from huggingface_hub import hf_hub_download, snapshot_download

# Project Root
PROJ_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(PROJ_ROOT)

def fix_win_path(path):
    abs_path = os.path.abspath(path)
    if sys.platform == "win32" and not abs_path.startswith("\\\\?\\"):
        return "\\\\?\\" + abs_path
    return abs_path

# Expected local directory paths
MODELS_DIR = os.path.join(PROJ_ROOT, "models")
BENCHMARK_DIR = os.path.join(MODELS_DIR, "benchmark")

PATHS = {
    "fasttext_stock": os.path.join(BENCHMARK_DIR, "fastText", "lid.176.bin"),
    "fasttext_stock_root": os.path.join(MODELS_DIR, "lid.176.bin"),
    "fasttext_specialist": os.path.join(MODELS_DIR, "fasttext_finetuned.bin"),
    "openlid_stock": os.path.join(BENCHMARK_DIR, "OpenLID", "model.bin"),
    "openlid_specialist": os.path.join(MODELS_DIR, "openlid_v2_finetuned.bin"),
    "nllb_stock": os.path.join(BENCHMARK_DIR, "NLLB", "model.bin"),
    "glotlid_stock": os.path.join(BENCHMARK_DIR, "GlotLID", "model.bin"),
    "conlid_repo": os.path.join(BENCHMARK_DIR, "ConLID", "repo"),
    "conlid_checkpoints": os.path.join(BENCHMARK_DIR, "ConLID", "checkpoints"),
}

def verify_fasttext():
    print("\n--- 1. fastText LID-176 ---")
    stock_path = PATHS["fasttext_stock"]
    if not os.path.exists(stock_path) and os.path.exists(PATHS["fasttext_stock_root"]):
        stock_path = PATHS["fasttext_stock_root"]
    
    if os.path.exists(stock_path):
        print(f"  [OK] Stock model found at: {stock_path} ({os.path.getsize(stock_path) / (1024*1024):.1f} MB)")
    else:
        print("  Downloading fastText LID-176 stock model...")
        os.makedirs(os.path.dirname(PATHS["fasttext_stock"]), exist_ok=True)
        import urllib.request
        url = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin"
        urllib.request.urlretrieve(url, PATHS["fasttext_stock"])
        print(f"  [OK] Downloaded to {PATHS['fasttext_stock']}")

    if os.path.exists(PATHS["fasttext_specialist"]):
        print(f"  [OK] Fine-tuned specialist found at: {PATHS['fasttext_specialist']} ({os.path.getsize(PATHS['fasttext_specialist']) / (1024*1024):.1f} MB)")
    else:
        print(f"  [WARNING] Specialist not found at {PATHS['fasttext_specialist']}")

def verify_openlid():
    print("\n--- 2. OpenLID-v2 ---")
    stock_path = PATHS["openlid_stock"]
    if os.path.exists(stock_path):
        print(f"  [OK] Stock model found at: {stock_path} ({os.path.getsize(stock_path) / (1024*1024):.1f} MB)")
    else:
        print("  Downloading OpenLID-v2 stock model from HuggingFace ('laurievb/OpenLID-v2')...")
        os.makedirs(os.path.dirname(stock_path), exist_ok=True)
        downloaded = hf_hub_download(repo_id="laurievb/OpenLID-v2", filename="model.bin")
        # Copy or symlink to local target path
        import shutil
        shutil.copy2(downloaded, stock_path)
        print(f"  [OK] Downloaded & copied to {stock_path}")

    if os.path.exists(PATHS["openlid_specialist"]):
        print(f"  [OK] Fine-tuned specialist found at: {PATHS['openlid_specialist']} ({os.path.getsize(PATHS['openlid_specialist']) / (1024*1024):.1f} MB)")
    else:
        print(f"  [WARNING] Specialist not found at {PATHS['openlid_specialist']}")

def verify_nllb():
    print("\n--- 3. NLLB LID-218 ---")
    stock_path = PATHS["nllb_stock"]
    if os.path.exists(stock_path):
        print(f"  [OK] Stock model found at: {stock_path} ({os.path.getsize(stock_path) / (1024*1024):.1f} MB)")
    else:
        print("  Downloading NLLB LID-218 stock model from HuggingFace ('facebook/fasttext-language-identification')...")
        os.makedirs(os.path.dirname(stock_path), exist_ok=True)
        downloaded = hf_hub_download(repo_id="facebook/fasttext-language-identification", filename="model.bin")
        import shutil
        shutil.copy2(downloaded, stock_path)
        print(f"  [OK] Downloaded & copied to {stock_path}")

def verify_glotlid():
    print("\n--- 4. GlotLID v3 ---")
    stock_path = PATHS["glotlid_stock"]
    if os.path.exists(stock_path):
        print(f"  [OK] Stock model found at: {stock_path} ({os.path.getsize(stock_path) / (1024*1024):.1f} MB)")
    else:
        print("  Downloading GlotLID v3 stock model from HuggingFace ('cis-lmu/glotlid')...")
        os.makedirs(os.path.dirname(stock_path), exist_ok=True)
        downloaded = hf_hub_download(repo_id="cis-lmu/glotlid", filename="model.bin")
        import shutil
        shutil.copy2(downloaded, stock_path)
        print(f"  [OK] Downloaded & copied to {stock_path}")

def verify_conlid():
    print("\n--- 5. ConLID ---")
    repo_dir = PATHS["conlid_repo"]
    checkpoints_dir = PATHS["conlid_checkpoints"]
    
    # 1. Clone repository wrapper if missing
    if os.path.exists(os.path.join(repo_dir, "model.py")):
        print(f"  [OK] ConLID repository wrapper found at: {repo_dir}")
    else:
        print(f"  Cloning ConLID official repository into {repo_dir}...")
        os.makedirs(os.path.dirname(repo_dir), exist_ok=True)
        subprocess.run(["git", "clone", "https://github.com/epfl-nlp/language-identification.git", repo_dir], check=True)
        print(f"  [OK] Cloned to {repo_dir}")

    # 2. Download checkpoints from HF if missing
    if os.path.exists(checkpoints_dir) and any(os.scandir(checkpoints_dir)):
        print(f"  [OK] ConLID checkpoints found at: {checkpoints_dir}")
    else:
        print(f"  Downloading ConLID model checkpoints from Hugging Face ('epfl-nlp/ConLID')...")
        os.makedirs(checkpoints_dir, exist_ok=True)
        snapshot_download(repo_id="epfl-nlp/ConLID", local_dir=checkpoints_dir)
        print(f"  [OK] Checkpoints saved to {checkpoints_dir}")

def main():
    print("=" * 70)
    print("VERIFYING LOCAL REPOSITORY SETUP FOR 5 SOTA MODELS")
    print("=" * 70)
    verify_fasttext()
    verify_openlid()
    verify_nllb()
    verify_glotlid()
    verify_conlid()
    print("\n" + "=" * 70)
    print("VERIFICATION COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
