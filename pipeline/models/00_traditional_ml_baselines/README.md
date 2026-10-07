# 00: Traditional ML & Shallow Neural Baselines

Contains from-scratch baseline implementations and models evaluating Sinhala-script language identification without large pretrained weights.

---

## 🏛 The 7 Baselines

| Model | Paradigm | Full Acc | Full F1 | 1-Word Acc | Location |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Multinomial NB** | Probabilistic ML | **0.9986** | **0.9985** | **0.8714** | `multinomial_nb/` |
| **Linear SVM** | Margin-based Linear | 0.9982 | 0.9984 | 0.6503 | `linear_svm/` |
| **Char n-gram + LogReg** | Subword Logistic Regression | 0.9977 | 0.9979 | 0.6985 | `char_ngram_logreg/` |
| **fastText (scratch)** | Subword Embeddings | 0.9980 | 0.9980 | 0.8344 | `fasttext_scratch/` |
| **Char-BiGRU** | Recurrent Deep Learning | 0.9969 | 0.9970 | 0.7617 | `char_bigru/` |
| **Char-CNN (1D)** | Convolutional Deep Learning | 0.9960 | 0.9963 | 0.7896 | `char_cnn/` |
| **XGBoost** | Gradient Tree Boosting | 0.9946 | 0.9948 | 0.5509 | `xgboost/` |

---

## 🚀 Execution Commands
- **Phase 1 Target Benchmark**: `python pipeline/scripts/00.traditional_baselines/benchmark_phase1_baselines.py`
- **Phase 2 11-Language Rehearsal Benchmark**: `python pipeline/scripts/00.traditional_baselines/benchmark_phase2_baselines.py`
- **Char n-gram LogReg Inference**: `python pipeline/models/00_traditional_ml_baselines/char_ngram_logreg/infer.py`
