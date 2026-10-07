# Datasets Ecosystem

This directory houses all experimental datasets for **Sinhala-Script Language Identification (LangID)** across Sinhala, Pali, and Sanskrit, including global multilingual benchmarks and continual rehearsal datasets.

---

## 📁 Directory Structure

```
pipeline/datasets/
├── target_language/           # Core 3-class Sinhala-script dataset
│   ├── train/                 # 60,285 samples (.csv, .txt, .jsonl)
│   ├── validation/            # 6,986 samples (.csv, .txt, .jsonl)
│   └── test/                  # 7,047 samples (.csv, .txt, .jsonl, .json)
│
├── hybrid_benchmark/          # Out-of-domain multilingual evaluation suites
│   ├── flores_plus/           # FLORES+ evaluation benchmark (208 langs, 229,687 records)
│   ├── wili_2018/             # WiLI-2018 Wikipedia benchmark (237 langs, 241,047 records)
│   └── commonlid/             # CommonLID noisy web benchmark (112 langs, 380,277 records)
│
├── hybrid_finetune/           # Continual learning & rehearsal datasets
│   ├── replay_mixed/          # 11-class balanced rehearsal (99k train, 11k val)
│   ├── sanskrit_devanagari/   # Devanagari Sanskrit corpus (surajp/sanskrit_classic)
│   └── aya_dataset/           # 7 non-Sanskrit background languages extraction
│
└── benchmark_results/         # Benchmark predictions and performance metrics
    ├── 00_traditional_ml_baselines/  # 7 from-scratch ML & shallow neural baselines
    ├── 01_zero_shot/                 # Out-of-the-box foundation models
    ├── 02_target_only/               # Fine-tuned on target only (catastrophic forgetting)
    ├── 03_multilingual_rehearsal/    # Continual rehearsal fine-tuning (forgetting mitigated)
    └── compute_metrics.py            # Automated Accuracy & Macro F1 evaluator
```

---

## 📊 Summary of Dataset Pillars

| Pillar | Focus | Languages | Total Samples | Formats |
| :--- | :--- | :--- | :--- | :--- |
| **`target_language`** | Primary task: Sinhala-script LangID | `sin_Sinh`, `pli_Sinh`, `san_Sinh` | **74,318** | CSV, fastText (`.txt`), JSONL |
| **`hybrid_benchmark`** | Evaluation of zero-shot & generalisation | 208+ global languages | **851,011** | JSONL, Gzip JSONL |
| **`hybrid_finetune`** | Rehearsal training against catastrophic forgetting | 11 balanced classes (3 target + 8 background) | **110,000** | CSV, fastText (`.txt`), JSONL |
| **`benchmark_results`** | Empirical findings across all 4 research phases | Prediction outputs & evaluations | — | CSV, Python script |

---

## 🚀 Quick Start for Collaborators

### Python (Pandas)
```python
import pandas as pd

# Load core training split
train_df = pd.read_csv("pipeline/datasets/target_language/train/train.csv")
print(train_df['label'].value_counts())

# Load 11-language continual rehearsal split
replay_df = pd.read_csv("pipeline/datasets/hybrid_finetune/replay_mixed/train_11lang_uniform.csv")
print(replay_df['label'].value_counts())
```

### fastText CLI
```bash
# Train fastText baseline model
fasttext supervised -input pipeline/datasets/target_language/train/train.txt \
                    -output saved_models/fasttext_target \
                    -lr 0.5 -epoch 25 -wordNgrams 3
```

### Evaluating Benchmark Results
```bash
python pipeline/datasets/benchmark_results/compute_metrics.py
```
