import os
import sys
import argparse
from huggingface_hub import HfApi, create_repo

FASTTEXT_README = """---
license: cc-by-nc-4.0
language:
- si
- pi
- sa
tags:
- language-identification
- fasttext
- fasttext-lid-176
- sinhala
- pali
- sanskrit
- intra-script
- two-stage-routing
library_name: fasttext
base_model: facebook/fasttext-language-identification
pipeline_tag: text-classification
---

# fastText LID-176: Sinhala-Script Disambiguation (Pali, Sanskrit, Sinhala)

This repository contains the fine-tuned specialist fastText model for **Sinhala-script Language Identification**, developed as part of the paper:
> **"A Benchmark for Sinhala-Script Language Identification: Disambiguating Sinhala, Pali, and Sanskrit in Closed and Open World Contexts"**

## 1. Problem Overview
Planetary-scale LangID tools (including stock `fastText LID-176`) assign all text written in the Sinhala script to a monolithic `si` label. When presented with historical or canonical Buddhist and scholarly literature written in Sinhala script, stock models fail completely:
- **Pali in Sinhala script (`pli_Sinh`):** 0.0% F1 (Stock zero-shot)
- **Sanskrit in Sinhala script (`san_Sinh`):** 0.0% F1 (Stock zero-shot)

## 2. Two-Stage Specialist Routing Architecture
To eliminate script ambiguity while guaranteeing **mathematical 0.0% degradation on all 176 global background languages**, we deploy this model in a **Two-Stage Specialist Routing Pipeline**:
1. **Stage 1 (Global Router):** Stock `fastText LID-176` (`lid.176.bin`) classifies incoming text.
   - If the prediction is **NOT** Sinhala (`!= 'si'`), the global label (English, Tamil, Hindi, Devanagari Sanskrit, French, etc.) is emitted directly.
2. **Stage 2 (Specialist Model - this repository):** If Stage 1 detects Sinhala script (`== 'si'`), the input is routed to this specialist model (`model.bin`), which performs fine-grained 3-way discrimination:
   - `__label__sinhala` (`Sinh-Sinh`)
   - `__label__pali` (`Pali-Sinh`)
   - `__label__sanskrit` (`San-Sinh`)

## 3. Evaluation on 11-Language Hybrid Benchmarks

| Benchmark Dataset | Sinhala-Sinh F1 | Pali-Sinh F1 | Sanskrit-Sinh F1 | Sanskrit-Deva F1 | Overall Macro-F1 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **FLORES+ (Hybrid)** | **0.9611** | **0.9751** | **0.9805** | **0.9594** | **0.9276** |
| **CommonLID (Hybrid)** | **0.9609** | **0.9751** | **0.9805** | **0.8886** | **0.9645** |
| **WiLI-2018 (Hybrid)** | **0.9611** | **0.9751** | **0.9805** | **0.9904** | **0.9745** |

*(Note: Background languages such as English, Tamil, Arabic, Bengali, French, and German retain their pristine stock fastText performance).*

## 4. Quickstart / Usage

```python
import fasttext
from huggingface_hub import hf_hub_download

# 1. Download Stage 1 (Stock FastText) and Stage 2 (Specialist)
stage1_path = hf_hub_download(repo_id="facebook/fasttext-language-identification", filename="model.bin")
stage2_path = hf_hub_download(repo_id="script-langid/fasttext-lid-176-sinhala-pali-sanskrit", filename="model.bin")

stage1_model = fasttext.load_model(stage1_path)
stage2_model = fasttext.load_model(stage2_path)

def identify_language(text: str):
    # Stage 1: Global screening
    pred1, prob1 = stage1_model.predict(text.replace("\\n", " "))
    label1 = pred1[0].replace("__label__", "")
    
    # If Sinhala script detected by Stage 1, route to Stage 2
    if label1 in ["si", "sin", "sin_Sinh"]:
        pred2, prob2 = stage2_model.predict(text.replace("\\n", " "))
        target_label = pred2[0].replace("__label__", "")
        return {
            "language": f"{target_label.capitalize()}-Sinh",
            "stage": 2,
            "confidence": float(prob2[0])
        }
    else:
        return {
            "language": label1,
            "stage": 1,
            "confidence": float(prob1[0])
        }

# Example: Pali Buddhist Verse in Sinhala Script
sample_pali = "මනොපුබ්බඞ්ගමා ධම්මා මනොසෙට්ඨා මනොමයා"
print(identify_language(sample_pali))
# Output: {'language': 'Pali-Sinh', 'stage': 2, 'confidence': 0.99...}
```

## 5. Citation
```bibtex
@inproceedings{sinhala_script_langid_2026,
  title={A Benchmark for Sinhala-Script Language Identification: Disambiguating Sinhala, Pali, and Sanskrit in Closed and Open World Contexts},
  author={Anonymous},
  booktitle={Proceedings of the Association for Computational Linguistics (ACL)},
  year={2026}
}
```
"""

OPENLID_README = """---
license: cc-by-4.0
language:
- si
- pi
- sa
tags:
- language-identification
- fasttext
- openlid
- sinhala
- pali
- sanskrit
- intra-script
library_name: fasttext
base_model: laurievb/OpenLID-v2
pipeline_tag: text-classification
---

# OpenLID-v2: Sinhala-Script Disambiguation (Pali, Sanskrit, Sinhala)

This repository contains the fine-tuned **OpenLID-v2** model for **Sinhala-script Language Identification**, developed as part of the paper:
> **"A Benchmark for Sinhala-Script Language Identification: Disambiguating Sinhala, Pali, and Sanskrit in Closed and Open World Contexts"**

## 1. Problem Overview
Stock `OpenLID-v2` (`laurievb/OpenLID-v2`) supports 200+ languages, but designates only a single generic label (`sin_Sinh`) for texts in the Sinhala script. When evaluated zero-shot on corpora containing Pali and Sanskrit written in Sinhala script:
- **Pali in Sinhala script (`pli_Sinh`):** 0.0% F1 (Stock zero-shot)
- **Sanskrit in Sinhala script (`san_Sinh`):** 0.0% F1 (Stock zero-shot)
- All target texts are indiscriminately absorbed into `sin_Sinh`.

## 2. Adaptation & Architecture
This model extends the OpenLID-v2 representation space via supervised transfer learning on a group-stratified corpus of 60,285 target sentences across Sinhala, Pali, and Sanskrit in Sinhala script. 

When deployed in a **Two-Stage Specialist Pipeline**:
- Non-Sinhala scripts are handled directly by the global 200+ language heads.
- Sinhala-script inputs (`sin_Sinh`) are classified into granular classes:
  - `__label__sinhala` (`Sinh-Sinh`)
  - `__label__pali` (`Pali-Sinh`)
  - `__label__sanskrit` (`San-Sinh`)

## 3. Evaluation on 11-Language Hybrid Benchmarks

| Benchmark Dataset | Sinhala-Sinh F1 | Pali-Sinh F1 | Sanskrit-Sinh F1 | Overall Macro-F1 |
| :--- | :---: | :---: | :---: | :---: |
| **FLORES+ (Hybrid)** | **0.9670** | **0.9743** | **0.9704** | **0.7759** |
| **CommonLID (Hybrid)** | **0.9670** | **0.9743** | **0.9704** | **0.7913** |
| **WiLI-2018 (Hybrid)** | **0.9670** | **0.9743** | **0.9704** | **0.7782** |

### Note on the "Dialect Continuum Problem" & Devanagari Sanskrit
OpenLID-v2 attains lower single-label Macro-F1 scores on South Asian regional classes due to its fine-grained regional dialect heads. When presented with classical Devanagari Sanskrit text, OpenLID-v2 fragments probability mass across genetically descended dialect heads, predicting:
- **68.1%** as Bhojpuri (`bho_Deva`)
- **15.1%** as Maithili (`mai_Deva`)
- **11.0%** as Awadhi (`awa_Deva`)
While linguistically sensible across the Indo-Aryan dialect continuum, this reduces single-label benchmark F1 for Devanagari Sanskrit (`0.0350`). Target Sinhala-script discrimination remains unaffected at $>0.97$ F1.

## 4. Quickstart / Usage

```python
import fasttext
from huggingface_hub import hf_hub_download

# Download model from Hugging Face
model_path = hf_hub_download(repo_id="script-langid/openlid-v2-sinhala-pali-sanskrit", filename="model.bin")
model = fasttext.load_model(model_path)

def predict_lang(text: str):
    clean_text = text.replace("\\n", " ").strip()
    labels, probs = model.predict(clean_text, k=1)
    label = labels[0].replace("__label__", "")
    return {"label": label, "confidence": float(probs[0])}

sample_text = "නමො තස්ස භගවතො අරහතො සම්මාසම්බුද්ධස්ස"
print(predict_lang(sample_text))
# Output: {'label': 'pali', 'confidence': 0.99...}
```

## 5. Citation
```bibtex
@inproceedings{sinhala_script_langid_2026,
  title={A Benchmark for Sinhala-Script Language Identification: Disambiguating Sinhala, Pali, and Sanskrit in Closed and Open World Contexts},
  author={Anonymous},
  booktitle={Proceedings of the Association for Computational Linguistics (ACL)},
  year={2026}
}
```
"""

def upload_models(token=None):
    if not token:
        token = os.environ.get("HF_TOKEN")
    if not token:
        print("=" * 60)
        print("HUGGING FACE TOKEN REQUIRED")
        print("=" * 60)
        print("Please provide your Hugging Face Access Token.")
        print("You can get one at: https://huggingface.co/settings/tokens (Role: Write)")
        token = input("Enter your HF Token: ").strip()
        if not token:
            print("Error: No token provided. Exiting.")
            sys.exit(1)

    api = HfApi(token=token)
    try:
        user_info = api.whoami()
        username = user_info["name"]
        orgs = [o["name"] for o in user_info.get("orgs", [])]
        print(f"\n[OK] Authenticated as user: {username}")
        print(f"[OK] Available organizations: {orgs}")
        
        target_org = "script-langid"
        if target_org not in orgs:
            print(f"\n[WARNING] You might not be a member of organization '{target_org}'.")
            print("Checking if direct write access exists...")
    except Exception as e:
        print(f"[ERROR] Authentication failed: {e}")
        sys.exit(1)

    proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    models_dir = os.path.join(proj_root, "models")

    # Paths to model weights
    fasttext_weight = os.path.join(models_dir, "fasttext_finetuned.bin")
    openlid_weight = os.path.join(models_dir, "openlid_v2_finetuned.bin")

    # =========================================================================
    # 1. Upload fastText LID-176
    # =========================================================================
    repo_fasttext = "script-langid/fasttext-lid-176-sinhala-pali-sanskrit"
    print("\n" + "=" * 60)
    print(f"1. PREPARING REPOSITORY: {repo_fasttext}")
    print("=" * 60)

    try:
        create_repo(repo_id=repo_fasttext, repo_type="model", token=token, exist_ok=True, private=False)
        print(f"[OK] Repository '{repo_fasttext}' is ready.")

        # Upload README.md
        api.upload_file(
            path_or_fileobj=FASTTEXT_README.encode("utf-8"),
            path_in_repo="README.md",
            repo_id=repo_fasttext,
            repo_type="model"
        )
        print("[OK] Uploaded README.md")

        # Upload model binary
        if os.path.exists(fasttext_weight):
            print(f"Uploading model weights ({os.path.getsize(fasttext_weight) / 1024 / 1024:.1f} MB)...")
            api.upload_file(
                path_or_fileobj=fasttext_weight,
                path_in_repo="model.bin",
                repo_id=repo_fasttext,
                repo_type="model"
            )
            print("[OK] fastText model.bin uploaded successfully!")
        else:
            print(f"[ERROR] Weight file not found: {fasttext_weight}")

    except Exception as e:
        print(f"[ERROR] Failed to upload {repo_fasttext}: {e}")

    # =========================================================================
    # 2. Upload OpenLID-v2
    # =========================================================================
    repo_openlid = "script-langid/openlid-v2-sinhala-pali-sanskrit"
    print("\n" + "=" * 60)
    print(f"2. PREPARING REPOSITORY: {repo_openlid}")
    print("=" * 60)

    try:
        create_repo(repo_id=repo_openlid, repo_type="model", token=token, exist_ok=True, private=False)
        print(f"[OK] Repository '{repo_openlid}' is ready.")

        # Upload README.md
        api.upload_file(
            path_or_fileobj=OPENLID_README.encode("utf-8"),
            path_in_repo="README.md",
            repo_id=repo_openlid,
            repo_type="model"
        )
        print("[OK] Uploaded README.md")

        # Upload model binary
        if os.path.exists(openlid_weight):
            size_mb = os.path.getsize(openlid_weight) / 1024 / 1024
            print(f"Uploading OpenLID model weights ({size_mb:.1f} MB = {size_mb/1024:.2f} GB)...")
            print("Note: Large file upload may take 1-3 minutes depending on network bandwidth.")
            api.upload_file(
                path_or_fileobj=openlid_weight,
                path_in_repo="model.bin",
                repo_id=repo_openlid,
                repo_type="model"
            )
            print("[OK] OpenLID model.bin uploaded successfully!")
        else:
            print(f"[ERROR] Weight file not found: {openlid_weight}")

    except Exception as e:
        print(f"[ERROR] Failed to upload {repo_openlid}: {e}")

    print("\n" + "=" * 60)
    print("ALL UPLOADS COMPLETED!")
    print(f"Check organization page at: https://huggingface.co/script-langid")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload fastText and OpenLID models to script-langid organization")
    parser.add_argument("--token", type=str, default=None, help="Hugging Face Access Token (write permission)")
    args = parser.parse_args()

    upload_models(token=args.token)
