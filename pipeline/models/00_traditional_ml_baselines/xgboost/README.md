# XGBoost (Extreme Gradient Boosting)

**Architecture Paradigm**: Gradient Boosted Decision Trees over character n-gram frequencies

---

## 📈 Benchmark Performance
- **Full Sentence Accuracy**: 99.46% (Macro F1: 0.9948)
- **1-Word Stress Test Accuracy**: 55.09%

---

## 🚀 Training & Evaluation
To train and benchmark this model across full, 5-word, 3-word, and 1-word inputs:
```bash
python pipeline/scripts/00.traditional_baselines/benchmark_phase1_baselines.py
```
