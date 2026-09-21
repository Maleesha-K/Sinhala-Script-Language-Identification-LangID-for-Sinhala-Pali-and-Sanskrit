"""
================================================================================
Download 3 Remaining Fine-Tuned Models from Hugging Face (`script-langid`)
================================================================================
Downloads:
  1. NLLB LID-220: script-langid/nllb-lid-220-sinhala-pali-sanskrit
  2. GlotLID-2104: script-langid/glotlid-2104-sinhala-pali-sanskrit
  3. ConLID: script-langid/conlid-sinhala-pali-sanskrit
================================================================================
"""

import os
import sys
import shutil
from huggingface_hub import hf_hub_download, snapshot_download

PROJ_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FINETUNED_DIR = os.path.join(PROJ_ROOT, "models", "finetuned")
os.makedirs(FINETUNED_DIR, exist_ok=True)

def fix_win_path(path):
    abs_path = os.path.abspath(path)
    if sys.platform == "win32" and not abs_path.startswith("\\\\?\\"):
        return "\\\\?\\" + abs_path
    return abs_path

def download_nllb():
    target_path = os.path.join(FINETUNED_DIR, "nllb_lid_220_finetuned.bin")
    if os.path.exists(target_path):
        size_mb = os.path.getsize(target_path) / (1024 * 1024)
        print(f"[1/3 NLLB] Already exists at: {target_path} ({size_mb:.2f} MB)")
        return target_path

    print("\n[1/3 NLLB] Downloading NLLB LID-220 fine-tuned model ('script-langid/nllb-lid-220-sinhala-pali-sanskrit')...")
    downloaded = hf_hub_download(
        repo_id="script-langid/nllb-lid-220-sinhala-pali-sanskrit",
        filename="model.bin"
    )
    shutil.copy2(downloaded, target_path)
    size_mb = os.path.getsize(target_path) / (1024 * 1024)
    print(f"[1/3 NLLB] Successfully saved to: {target_path} ({size_mb:.2f} MB)")
    return target_path

def download_glotlid():
    target_path = os.path.join(FINETUNED_DIR, "glotlid_2104_finetuned.bin")
    if os.path.exists(target_path):
        size_mb = os.path.getsize(target_path) / (1024 * 1024)
        print(f"[2/3 GlotLID] Already exists at: {target_path} ({size_mb:.2f} MB)")
        return target_path

    print("\n[2/3 GlotLID] Downloading GlotLID-2104 fine-tuned model ('script-langid/glotlid-2104-sinhala-pali-sanskrit')...")
    downloaded = hf_hub_download(
        repo_id="script-langid/glotlid-2104-sinhala-pali-sanskrit",
        filename="model.bin"
    )
    shutil.copy2(downloaded, target_path)
    size_mb = os.path.getsize(target_path) / (1024 * 1024)
    print(f"[2/3 GlotLID] Successfully saved to: {target_path} ({size_mb:.2f} MB)")
    return target_path

def download_conlid():
    target_dir = os.path.join(FINETUNED_DIR, "conlid")
    os.makedirs(target_dir, exist_ok=True)
    safetensors_path = os.path.join(target_dir, "model.safetensors")
    
    if os.path.exists(safetensors_path):
        size_mb = os.path.getsize(safetensors_path) / (1024 * 1024)
        print(f"[3/3 ConLID] Already exists at: {target_dir} ({size_mb:.2f} MB)")
        return target_dir

    print("\n[3/3 ConLID] Downloading ConLID fine-tuned model ('script-langid/conlid-sinhala-pali-sanskrit')...")
    snapshot_download(
        repo_id="script-langid/conlid-sinhala-pali-sanskrit",
        local_dir=target_dir
    )
    size_mb = os.path.getsize(safetensors_path) / (1024 * 1024)
    print(f"[3/3 ConLID] Successfully saved to: {target_dir} (model.safetensors: {size_mb:.2f} MB)")
    return target_dir

def main():
    print("=" * 70)
    print("DOWNLOADING REMAINING 3 FINE-TUNED MODELS FROM script-langid")
    print("=" * 70)
    download_nllb()
    download_glotlid()
    download_conlid()
    print("\n" + "=" * 70)
    print("ALL 3 FINE-TUNED MODELS DOWNLOADED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    main()
