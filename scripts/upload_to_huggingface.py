"""Upload Continual FastText Leaf Surgery model to Hugging Face Hub.

Target organization: https://huggingface.co/script-langid
Example usage:
    python scripts/upload_to_huggingface.py --repo-name fasttext-leaf-surgery-11lang --token <YOUR_HF_TOKEN>
"""

import os
import sys
import argparse
from pathlib import Path
from huggingface_hub import HfApi, create_repo

DEFAULT_MODEL_DIR = "data_pipeline/models/continual/11lang_rehearsal_exp/best"
DEFAULT_ORG = "script-langid"
DEFAULT_REPO_NAME = "fasttext-leaf-surgery-11lang"

README_TEMPLATE = """---
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
license: cc-by-4.0
tags:
- language-identification
- fasttext
- continual-learning
- leaf-surgery
- sinhala
- pali
- sanskrit
datasets:
- script-langid/sinhala-pali-sanskrit-target
metrics:
- f1
- accuracy
---

# FastText Continual Leaf Surgery (11-Language Rehearsal)

This model is a continual fine-tuning of Meta's `fastText LID-176` utilizing **Hierarchical Softmax Leaf Surgery**.

## Architecture & Innovation
- **Base Architecture**: Meta `fastText LID-176` (100-dim dense subword embeddings with Huffman tree hierarchical softmax).
- **Leaf Surgery**: Instead of retraining the classification head from scratch (which shuffles the Huffman tree and causes catastrophic forgetting of 176 pre-trained languages), the original hierarchical softmax binary decision paths are preserved. The Sinhala (`si`) leaf node is surgically split into an internal decision node branching into modern Sinhala and canonical Pali, with Sanskrit adaptation.
- **Continual Rehearsal**: Trained on the 11-language uniform rehearsal buffer (`train_11lang_uniform.csv`) balancing the 3 target languages in Sinhala script with 8 global and regional anchor languages (English, Tamil, Hindi, Bengali, Arabic, French, German, and Sanskrit in Devanagari).

## Benchmark Performance

| Benchmark | Macro F1 | Sinhala F1 | Pali F1 | Sanskrit F1 | Overall Accuracy |
|---|:---:|:---:|:---:|:---:|:---:|
| **WiLI-2018 (11-Lang)** | **0.9811** | 0.9766 | 0.9881 | 0.9895 | **98.00%** |
| **CommonLID (11-Lang)** | **0.9486** | 0.9766 | 0.9881 | 0.9695 | **96.82%** |
| **FLORES+ (11-Lang)** | **0.9395** | 0.9766 | 0.9881 | 0.9817 | **92.71%** |

## How to Load in Python

```python
from data_pipeline.fasttext_continual.model import ContinualLID

# Loads config.json, vocab.json, and weights.pt automatically from Hugging Face
model = ContinualLID.from_pretrained("script-langid/fasttext-leaf-surgery-11lang")

# Inference example:
text = "නමෝ තස්ස භගවතෝ අරහතෝ සම්මා සම්බුද්ධස්ස"
prediction = model.predict(text)
print(prediction)  # 'pi' (Pali)
```

## Repository & Research
- **GitHub**: [Sinhala-Script-Language-Identification-LangID-for-Sinhala-Pali-and-Sanskrit](https://github.com/Maleesha-K/Sinhala-Script-Language-Identification-LangID-for-Sinhala-Pali-and-Sanskrit)
- **Research**: University of Moratuwa, Department of Computer Science & Engineering.
"""

def main():
    parser = argparse.ArgumentParser(description="Upload Continual FastText model to Hugging Face")
    parser.add_argument("--model-dir", default=DEFAULT_MODEL_DIR, help="Local model directory containing config.json, vocab.json, weights.pt")
    parser.add_argument("--org", default=DEFAULT_ORG, help="Hugging Face organization")
    parser.add_argument("--repo-name", default=DEFAULT_REPO_NAME, help="Hugging Face repository name")
    parser.add_argument("--token", default=None, help="Hugging Face write token (or set HF_TOKEN env var)")
    parser.add_argument("--private", action="store_true", help="Make repository private")
    args = parser.parse_args()

    model_dir = Path(args.model_dir)
    if not model_dir.exists():
        print(f"Error: Model directory not found at {model_dir}")
        sys.exit(1)

    required_files = ["config.json", "vocab.json", "weights.pt"]
    for f in required_files:
        if not (model_dir / f).exists():
            print(f"Error: Missing required file '{f}' in {model_dir}")
            sys.exit(1)

    repo_id = f"{args.org}/{args.repo_name}"
    token = args.token or os.environ.get("HF_TOKEN")

    print(f"Connecting to Hugging Face Hub...")
    api = HfApi(token=token)

    print(f"Ensuring repository exists: https://huggingface.co/{repo_id}")
    create_repo(repo_id=repo_id, token=token, repo_type="model", exist_ok=True, private=args.private)

    # Write temporary README.md into directory for model card
    readme_path = model_dir / "README.md"
    readme_created = False
    if not readme_path.exists():
        readme_path.write_text(README_TEMPLATE, encoding="utf-8")
        readme_created = True

    print(f"Uploading files from {model_dir} to {repo_id}...")
    api.upload_folder(
        folder_path=str(model_dir),
        repo_id=repo_id,
        repo_type="model",
        token=token
    )

    if readme_created and readme_path.exists():
        readme_path.unlink()

    print(f"\nSuccessfully uploaded model to: https://huggingface.co/{repo_id}")
    print(f"Team members can now load this model in code using:")
    print(f'  model = ContinualLID.from_pretrained("{repo_id}")')

if __name__ == "__main__":
    main()
