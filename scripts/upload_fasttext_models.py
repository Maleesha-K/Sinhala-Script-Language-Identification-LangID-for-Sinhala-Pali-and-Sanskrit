"""Upload the 2 Continual Learning (Hierarchical Softmax Leaf Surgery) fastText models to Hugging Face:

1. Table 2: Target-Only Continual Training
   - Local: data_pipeline/models/continual/target_only_exp/best/ (weights.pt, config.json, vocab.json)
   - HF Repo: script-langid/fasttext-leaf-surgery-target-only

2. Table 3: Multilingual Rehearsal Continual Training
   - Local: data_pipeline/models/continual/11lang_rehearsal_exp/best/ (weights.pt, config.json, vocab.json)
   - HF Repo: script-langid/fasttext-leaf-surgery-11lang

Usage:
    python scripts/upload_fasttext_models.py --token <YOUR_HF_WRITE_TOKEN>
"""

import os
import sys
import argparse
from pathlib import Path
from huggingface_hub import HfApi, create_repo

PROJ_ROOT = Path(__file__).resolve().parent.parent
ORG = "script-langid"

README_TARGET_ONLY = """---
license: cc-by-nc-4.0
language:
- sin
- pli
- san
tags:
- language-identification
- fasttext
- continual-learning
- leaf-surgery
- table-2-target-only
- sinhala
- pali
- sanskrit
pipeline_tag: text-classification
base_model: facebook/fasttext-language-identification
---

# fastText Continual Leaf Surgery: Target-Only Training (Table 2)

This model represents our **Continual Learning (Leaf Surgery)** architecture trained strictly on the target dataset (Table 2 in the research paper):
> **"A Benchmark for Sinhala-Script Language Identification: Disambiguating Sinhala, Pali, and Sanskrit in Closed and Open World Contexts"**  
> *University of Moratuwa, Department of Computer Science & Engineering*

## 1. Architecture & Innovation
Instead of fine-tuning with a replacement flat softmax head (which ruins fastText's Huffman tree and causes catastrophic forgetting), our method surgically splits the Sinhala (`si`) leaf node in the binary Huffman tree into modern Sinhala and canonical Pali branches.

All original 176 language decision nodes are retained intact, and the model is trained strictly on target text (`train.csv`).

## 2. Checkpoint Files
- `weights.pt`: PyTorch weights containing inherited input embedding and expanded output hierarchical decision parameters (124.5 MB).
- `config.json`: Tree paths, Huffman bit codes, and label mapping.
- `vocab.json`: Subword vocabulary and hashes.

## 3. How to Load and Run Inference in Python
```python
from data_pipeline.fasttext_continual.model import ContinualLID

# Loads weights.pt, config.json, and vocab.json automatically from Hugging Face
model = ContinualLID.from_pretrained("script-langid/fasttext-leaf-surgery-target-only")

# Inference example:
text = "මනොපුබ්බඞ්ගමා ධම්මා මනොසෙට්ඨා මනොමයා"
prediction, score = model.predict(text)
print(f"Language: {prediction}, Score: {score:.4f}")
# Output: Language: pi, Score: 0.99...
```
"""

README_REHEARSAL_11LANG = """---
license: cc-by-nc-4.0
language:
- sin
- pli
- san
- en
- ta
- hi
- bn
- ar
- fr
- de
tags:
- language-identification
- fasttext
- continual-learning
- leaf-surgery
- table-3-multilingual-rehearsal
pipeline_tag: text-classification
base_model: facebook/fasttext-language-identification
---

# fastText Continual Leaf Surgery: 11-Language Multilingual Rehearsal (Table 3)

This model represents our **Continual Learning (Leaf Surgery)** architecture trained with the 11-language balanced rehearsal buffer (Table 3 in the research paper):
> **"A Benchmark for Sinhala-Script Language Identification: Disambiguating Sinhala, Pali, and Sanskrit in Closed and Open World Contexts"**  
> *University of Moratuwa, Department of Computer Science & Engineering*

## 1. Architecture & Innovation
- **Hierarchical Softmax Leaf Surgery**: The Sinhala (`si`) leaf node in the official Facebook `lid.176.bin` Huffman tree was split into Sinhala and Pali branches.
- **Multilingual Rehearsal**: Fine-tuned on the balanced 11-language Aya dataset buffer (3 target languages in Sinhala script + 8 global/anchor languages: English, Tamil, Hindi, Bengali, Arabic, French, German, and Sanskrit Devanagari) to preserve cross-lingual representations.

## 2. Benchmark Performance (11-Language Evaluation)
- **WiLI-2018 (Macro-F1):** **0.9811** (Accuracy: 98.00%)
- **CommonLID (Macro-F1):** **0.9486** (Accuracy: 96.82%)
- **FLORES+ (Macro-F1):** **0.9395** (Accuracy: 92.71%)

## 3. How to Load and Run Inference in Python
```python
from data_pipeline.fasttext_continual.model import ContinualLID

# Loads weights.pt, config.json, and vocab.json automatically from Hugging Face
model = ContinualLID.from_pretrained("script-langid/fasttext-leaf-surgery-11lang")

# Inference example:
text = "නමෝ තස්ස භගවතෝ අරහතෝ සම්මා සම්බුද්ධස්ස"
prediction, score = model.predict(text)
print(f"Language: {prediction}, Score: {score:.4f}")
# Output: Language: pi, Score: 0.99...
```
"""

def upload_continual_models(token: str):
    api = HfApi(token=token)
    try:
        user = api.whoami()
        print(f"Authenticated as: {user['name']}")
    except Exception as e:
        print(f"Error: Authentication failed: {e}")
        sys.exit(1)

    # -----------------------------------------------------------------------
    # 1. Model 1: Table 2 Target-Only Continual Model
    # -----------------------------------------------------------------------
    repo_t2 = f"{ORG}/fasttext-leaf-surgery-target-only"
    folder_t2 = PROJ_ROOT / "data_pipeline" / "models" / "continual" / "target_only_exp" / "best"

    print("\n" + "=" * 70)
    print(f"1. UPLOADING TABLE 2 CONTINUAL MODEL: {repo_t2}")
    print("=" * 70)
    create_repo(repo_id=repo_t2, repo_type="model", token=token, exist_ok=True, private=False)

    print("Uploading README.md (Model Card)...")
    api.upload_file(
        path_or_fileobj=README_TARGET_ONLY.encode("utf-8"),
        path_in_repo="README.md",
        repo_id=repo_t2,
        repo_type="model"
    )

    if folder_t2.exists():
        print(f"Uploading files from {folder_t2} (weights.pt, config.json, vocab.json)...")
        api.upload_folder(
            folder_path=str(folder_t2),
            repo_id=repo_t2,
            repo_type="model"
        )
        print(f"[OK] Successfully uploaded {repo_t2}!")
    else:
        print(f"[ERROR] Local checkpoint folder not found: {folder_t2}")

    # -----------------------------------------------------------------------
    # 2. Model 2: Table 3 Multilingual Rehearsal Continual Model
    # -----------------------------------------------------------------------
    repo_t3 = f"{ORG}/fasttext-leaf-surgery-11lang"
    folder_t3 = PROJ_ROOT / "data_pipeline" / "models" / "continual" / "11lang_rehearsal_exp" / "best"

    print("\n" + "=" * 70)
    print(f"2. UPLOADING TABLE 3 CONTINUAL MODEL: {repo_t3}")
    print("=" * 70)
    create_repo(repo_id=repo_t3, repo_type="model", token=token, exist_ok=True, private=False)

    print("Uploading README.md (Model Card)...")
    api.upload_file(
        path_or_fileobj=README_REHEARSAL_11LANG.encode("utf-8"),
        path_in_repo="README.md",
        repo_id=repo_t3,
        repo_type="model"
    )

    if folder_t3.exists():
        print(f"Uploading files from {folder_t3} (weights.pt, config.json, vocab.json)...")
        api.upload_folder(
            folder_path=str(folder_t3),
            repo_id=repo_t3,
            repo_type="model"
        )
        print(f"[OK] Successfully uploaded {repo_t3}!")
    else:
        print(f"[ERROR] Local checkpoint folder not found: {folder_t3}")

    print("\n" + "=" * 70)
    print("ALL UPLOADS COMPLETED SUCCESSFULLY!")
    print(f"1. Table 2 Model: https://huggingface.co/{repo_t2}")
    print(f"2. Table 3 Model: https://huggingface.co/{repo_t3}")
    print("=" * 70)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload Continual fastText models to Hugging Face")
    parser.add_argument("--token", type=str, required=True, help="Hugging Face Access Token (write role)")
    args = parser.parse_args()

    upload_continual_models(token=args.token)
