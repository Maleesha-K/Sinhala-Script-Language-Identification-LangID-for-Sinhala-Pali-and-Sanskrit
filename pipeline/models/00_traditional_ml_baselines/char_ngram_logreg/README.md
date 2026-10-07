# Character n-gram + Logistic Regression

**Architecture Paradigm**: Linear Classifier over subword character n-grams (3-5 grams)

---

## 📈 Benchmark Performance
- **Full Sentence Accuracy**: 99.77% (Macro F1: 0.9979)
- **1-Word Stress Test Accuracy**: 69.85%

---

## 🚀 Training & Evaluation
To train and benchmark this model across full, 5-word, 3-word, and 1-word inputs:
```bash
python pipeline/scripts/00.traditional_baselines/benchmark_phase1_baselines.py
```
