"""
Download XLM-RoBERTa fine-tuned model from Hugging Face:
script-langid/xlm-roberta-sinhala-pali-sanskrit
Target directory: models/finetuned/xlm_roberta
"""

import os
import sys
from huggingface_hub import snapshot_download

PROJ_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TARGET_DIR = os.path.join(PROJ_ROOT, "models", "finetuned", "xlm_roberta")

def fix_win_path(path: str) -> str:
    abs_path = os.path.abspath(path)
    if sys.platform == "win32" and not abs_path.startswith("\\\\?\\"):
        return "\\\\?\\" + abs_path
    return abs_path

def main():
    os.makedirs(TARGET_DIR, exist_ok=True)
    print(f"Downloading script-langid/xlm-roberta-sinhala-pali-sanskrit to {TARGET_DIR}...")
    
    snapshot_download(
        repo_id="script-langid/xlm-roberta-sinhala-pali-sanskrit",
        local_dir=TARGET_DIR,
        local_dir_use_symlinks=False
    )
    print("\nDownload complete! Files in directory:")
    for root, dirs, files in os.walk(TARGET_DIR):
        for f in files:
            p = os.path.join(root, f)
            sz = os.path.getsize(p) / (1024 * 1024)
            print(f"  {f}: {sz:.2f} MB")

if __name__ == "__main__":
    main()
