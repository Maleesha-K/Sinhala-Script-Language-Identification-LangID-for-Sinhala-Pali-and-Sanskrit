# Linear Support Vector Machine (LinearSVC)

**Architecture Paradigm**: Maximum-Margin Linear Classifier over subword n-grams

---

## 📈 Benchmark Performance
- **Full Sentence Accuracy**: 99.82% (Macro F1: 0.9984)
- **1-Word Stress Test Accuracy**: 65.03%

---

## 🚀 Training & Evaluation
To train and benchmark this model across full, 5-word, 3-word, and 1-word inputs:
```bash
python pipeline/scripts/00.traditional_baselines/benchmark_phase1_baselines.py
```
