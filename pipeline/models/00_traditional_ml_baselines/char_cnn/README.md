# Character-level 1D CNN

**Architecture Paradigm**: 1D Convolutional Neural Network learning local character pattern filters

---

## 📈 Benchmark Performance
- **Full Sentence Accuracy**: 99.60% (Macro F1: 0.9963)
- **1-Word Stress Test Accuracy**: 78.96%

---

## 🚀 Training & Evaluation
To train and benchmark this model across full, 5-word, 3-word, and 1-word inputs:
```bash
python pipeline/scripts/00.traditional_baselines/benchmark_phase1_baselines.py
```
