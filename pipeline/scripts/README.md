# Pipeline Scripts

Automated scripts and reproducible Jupyter Notebooks powering the complete experimental lifecycle.

---

## 🔄 Lifecycle Stages

```
pipeline/scripts/
├── 00.traditional_baselines/    # 7 From-scratch ML & shallow neural models
├── 01.download/                 # Global benchmark fetchers
├── 02.preprocess/               # Unicode normalization & format unification
├── 03.dataset_checking/         # Dataset validation & auditing
├── 04.benchmark_zero_shot/      # Zero-shot evaluation of foundation models
├── 05.prepare_datasets/         # Continual learning rehearsal generation
├── 06.train_models/             # Fine-tuning pipelines (specialist vs rehearsal)
└── 07.benchmark_evaluation/     # Multi-benchmark testing & metric calculation
```
