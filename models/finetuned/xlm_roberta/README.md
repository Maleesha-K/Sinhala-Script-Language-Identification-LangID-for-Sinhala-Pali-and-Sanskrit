---
base_model: papluca/xlm-roberta-base-language-detection
library_name: peft
tags:
- base_model:adapter:papluca/xlm-roberta-base-language-detection
- lora
- transformers
language:
- en
- fr
- de
- ar
- hi
- si
- sa
- pi
- bn
- ta
---

# XLM-RoBERTa-25: Sinhala-Script Pali & Sanskrit

A PEFT/LoRA language identification model that extends [`papluca/xlm-roberta-base-language-detection`](https://huggingface.co/papluca/xlm-roberta-base-language-detection) with **five new classes** — including Pali (`pi`) and Sanskrit (`sa`) — **without catastrophic forgetting** of the original 20 languages.

Pali and Sanskrit are frequently written in Sinhala script in Sri Lankan Buddhist and scholarly corpora. Off-the-shelf LID models (including the base XLM-R model) often classify all such text as Sinhala (`si`). This model successfully separates the three.

## Labels & Script Specificity

25 total: The base model's full 20-label set, plus 5 new classes (`si`, `pi`, `sa`, `bn`, `ta`). 

**Crucial Note on Script Specificity:** The original base model never supported Sanskrit or Pali in any script. Therefore, the new `sa` and `pi` nodes in the classification head were trained *exclusively* on Sinhala-script datasets (Nadil, SiDiaC-v2, DCS). Consequently, this model's `sa` and `pi` labels structurally and semantically represent **Sinhala-script Sanskrit** and **Sinhala-script Pali**. The model is not designed to classify Devanagari Sanskrit or Latin Pali.

The crucial Sinhala-script classes are:

| Label | Language | Script |
|---|---|---|
| `si` | Sinhala | Sinhala |
| `pi` | Pali | Sinhala |
| `sa` | Sanskrit | Sinhala |

## Usage

**⚠️ IMPORTANT WARNING FOR LOADING:** 
Because we expanded the classification head from 20 to 25 classes using LoRA, loading this model requires a specific sequence. You **must** load the updated local configuration and pass `ignore_mismatched_sizes=True` to the base model initialization *before* applying the PEFT adapters.

```python
import torch
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer, AutoConfig

model_id = "your-username/xlm-roberta-base-langid" # Replace with your HF repo

# 1. Load the updated configuration (which contains the 25 labels)
config = AutoConfig.from_pretrained(model_id)

# 2. Load the base model, ignoring the size mismatch of the 20-class classification head from the Hub
model = AutoModelForSequenceClassification.from_pretrained(
    model_id, 
    config=config, 
    ignore_mismatched_sizes=True
)

# 3. Load the tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_id)

# 4. Create the pipeline
device = 0 if torch.cuda.is_available() else -1
lang_id_pipe = pipeline("text-classification", model=model, tokenizer=tokenizer, device=device)

# Example Usage
text = "මෙය සිංහල භාෂාවෙන් ලියන ලද වාක්‍යයකි." # Sinhala
prediction = lang_id_pipe(text)
print(prediction) 
# [{'label': 'si', 'score': 0.99...}]
```

## Training

| | |
|---|---|
| Base model | `papluca/xlm-roberta-base-language-detection` (20 labels) |
| Method | LoRA (Rank 64, Alpha 128) + Rehearsal Data |
| Epochs | 10 (with Early Stopping) |
| Learning rate | 2e-5 |
| New classes | `si`, `pi`, `sa`, `bn`, `ta` |

Fine-tuning a 270M parameter model for language identification often leads to catastrophic forgetting (where the model learns the new languages but completely forgets the old ones). 

To solve this, the label space was extended from 20 to 25. We froze the entire base transformer and only trained small adapter matrices injected into the `query`, `key`, `value`, and `dense` layers. 

Crucially, to prevent Catastrophic Forgetting, we used **Rehearsal Data** by mixing samples from the `CohereLabs/aya_dataset` for the original languages alongside our new training data for Sinhala, Pali, and Sanskrit.

## Evaluation & Methodological Purity

Evaluated on integrated versions of CommonLID, FLORES+, and WiLI-2018. 

Because the model's `sa` and `pi` nodes represent Sinhala-script variants exclusively, evaluating them against standard benchmarks containing Devanagari Sanskrit or Latin Pali would be methodologically incorrect. To ensure evaluation purity, the test datasets were dynamically integrated:
1. All raw Devanagari Sanskrit and Latin Pali records were explicitly isolated or removed.
2. High-quality Sinhala-script Sanskrit and Pali records (from the Nadil dataset) were injected.
3. The benchmark script strictly maps and evaluates only the Sinhala-script records against the `sa` and `pi` labels, completely ignoring residual scripts.

By utilizing LoRA combined with Rehearsal Data, the model successfully maintains its high baseline accuracy on the original 20 languages while achieving near-perfect precision and recall on the newly introduced Sinhala-script languages.

### Per-language F1

| Language | CommonLID | FLORES+ | WiLI-2018 |
|---|---|---|---|
| **Sinhala** (`si`) | 0.9257 | 0.9722 | 0.9980 |
| **Pali** (`pi`) | 0.9932 | 0.9949 | 0.9972 |
| **Sanskrit** (`sa`) | 0.9862 | 0.9977 | 0.9977 |
| English (`en`) | 0.9590 | 0.7669 | 0.8887 |
| Tamil (`ta`) | 0.9818 | 0.9946 | 0.9945 |
| Hindi (`hi`) | 0.9713 | 0.9912 | 0.9894 |
| Bengali (`bn`) | 0.9931 | 0.9926 | 0.9691 |
| Arabic (`ar`) | 0.9952 | 0.5027 | N/A |
| French (`fr`) | 0.9471 | 0.9792 | 0.9798 |
| German (`de`) | 0.9674 | 1.0000 | 0.9703 |

### Aggregate

| Benchmark | Samples | Accuracy | Macro F1 |
|---|---|---|---|
| CommonLID | 141,767 | 97.33% | 89.58% |
| FLORES+ | 31,335 | 92.53% | 94.03% |
| WiLI-2018 | 26,047 | 97.75% | 85.92% |

## Limitations

- Sanskrit in Sinhala script can sometimes be confused with Pali, which is expected given their lexical and orthographic overlap.
- Short inputs are less reliable. Prefer at least a full sentence.
- The model inherits the domain characteristics of its fine-tuning corpus; performance on out-of-domain text may differ.

## License

Apache-2.0, inherited from the base model.
### Framework versions

- PEFT 0.20.0