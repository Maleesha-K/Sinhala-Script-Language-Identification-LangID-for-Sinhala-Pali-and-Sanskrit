# LangID Experimental Pipeline

A clean, story-aligned folder structure for Language Identification (LangID) across Sinhala, Pali, and Sanskrit in the Sinhala script alongside global multilingual evaluation.

---

## Directory Hierarchy

```text
pipeline/
├── datasets/
│   ├── target_language/                   # Target Sinhala Script Dataset (Sinhala, Pali, Sanskrit)
│   │   ├── train/                         # Training Split
│   │   ├── validation/                    # Validation Split
│   │   └── test/                          # Held-out Target Test Split
│   │
│   ├── hybrid_benchmark/                  # Global Evaluation Benchmarks
│   │   ├── flores_plus/                   # FLORES+ (Devanagari Sanskrit + 8 Global Languages + Nadil Test)
│   │   ├── wili_2018/                     # WiLI-2018 paragraph benchmark
│   │   └── commonlid/                     # CommonLID diverse web benchmark
│   │
│   ├── hybrid_finetune/                   # Multilingual Rehearsal & Continual Learning
│   │   ├── aya_dataset/                   # CohereLabs/aya_dataset (8 global background languages)
│   │   ├── sanskrit_devanagari/           # surajp/sanskrit_classic corpus (san_Deva)
│   │   └── replay_mixed/                  # 11-Group Replay Dataset (Targets + 8 Rehearsal Languages)
│   │
│   └── benchmark_results/                 # Model Predictions and Metric Score Matrices
│       ├── 00_traditional_ml_baselines/   # 7 ML Baselines (Full sentence & fragment stress test CSVs)
│       ├── 01_zero_shot/                  # Table 1: Foundation Pretrained Zero-Shot outputs
│       ├── 02_target_only/                # Table 2: Target-Only Local Specialist SOTA outputs
│       └── 03_multilingual_rehearsal/     # Table 3: Global Rehearsal Continual SOTA outputs
│
├── models/
│   ├── 00_traditional_ml_baselines/       # 7 From-Scratch ML & Shallow Neural Models
│   │   ├── multinomial_nb/                # Multinomial Naive Bayes
│   │   ├── linear_svm/                    # Linear Support Vector Classifier
│   │   ├── char_ngram_logreg/             # Char n-gram + Logistic Regression
│   │   ├── xgboost/                       # XGBoost classifier
│   │   ├── fasttext_scratch/              # fastText trained from scratch on target
│   │   ├── char_cnn/                      # Char-CNN (1D-CNN)
│   │   └── char_bigru/                    # Char-BiGRU
│   │
│   ├── 01_baseline_pretrained/            # Table 1: Foundation Pretrained SOTA Models (Zero-Shot)
│   │   ├── fasttext_lid176/               # fastText official lid.176.bin
│   │   ├── openlid_v3/                    # OpenLID v3 official model
│   │   ├── glotlid_v3/                    # GlotLID v3 official model
│   │   ├── nllb_lid218/                   # NLLB lid218e official model
│   │   ├── conlid/                        # ConLID official checkpoint
│   │   └── xlm_roberta_base/              # HuggingFace xlm-roberta-base snapshot
│   │
│   ├── 02_target_only_sota/               # Table 2: Local Language Trained SOTA Models (Target-Only)
│   │   ├── fasttext_leaf_surgery/         # fastText leaf-surgery target-only
│   │   ├── openlid_v3/                    # OpenLID target-only adapted model
│   │   ├── glotlid_v3/                    # GlotLID target-only adapted model
│   │   ├── nllb_lid218/                   # NLLB lid218e target-only adapted model
│   │   ├── conlid/                        # ConLID target-only adapted model
│   │   └── xlm_roberta/                   # XLM-RoBERTa target-only adapter
│   │
│   └── 03_global_rehearsal_sota/          # Table 3: Global Language Trained SOTA Models (Rehearsal)
│       ├── fasttext_continual/            # fastText 11-lang rehearsal leaf-surgery
│       ├── openlid_v3/                    # OpenLID 11-lang rehearsal model
│       ├── glotlid_v3/                    # GlotLID replay model
│       ├── nllb_lid218/                   # NLLB lid218e replay model
│       ├── conlid/                        # ConLID replay model
│       └── xlm_roberta/                   # XLM-RoBERTa multilingual rehearsal model
│
├── scripts/
│   ├── 00.traditional_baselines/          # Traditional 7 ML baseline runners
│   ├── 01.download/                       # Download benchmarks and raw data
│   ├── 02.preprocess/                     # Standardize to jsonl & integrate test sets
│   ├── 03.dataset_checking/               # Validation checks & audits
│   ├── 04.benchmark_zero_shot/            # Table 1 zero-shot evaluation runners
│   ├── 05.prepare_datasets/               # Split construction for target & replay
│   ├── 06.train_models/                   # Training runners: Target-Only & Rehearsal
│   └── 07.benchmark_evaluation/           # Table 2 & Table 3 evaluation runners
│
└── paths.py                               # Centralized path configuration module
```

---

## Path Reference

You can import all predefined paths directly via:

```python
from pipeline.paths import (
    TARGET_TRAIN_CSV,
    TARGET_VAL_CSV,
    TARGET_TEST_CSV,
    FLORES_PLUS_JSONL,
    WILI_2018_JSONL,
    COMMONLID_JSONL,
    TRAIN_11LANG_UNIFORM,
    MODELS_TRADITIONAL_ML,
    MODELS_BASELINE_PRETRAINED,
    MODELS_TARGET_ONLY_SOTA,
    MODELS_GLOBAL_REHEARSAL_SOTA,
)
```
