# Character-level Bidirectional GRU (Char-BiGRU)

**Architecture Paradigm**: Recurrent Neural Network with Gated Recurrent Units over character sequence

---

## 📈 Benchmark Performance
- **Full Sentence Accuracy**: 99.69% (Macro F1: 0.9970)
- **1-Word Stress Test Accuracy**: 76.17%

---

## 🚀 Training & Evaluation
To train and benchmark this model across full, 5-word, 3-word, and 1-word inputs:
```bash
python pipeline/scripts/00.traditional_baselines/benchmark_phase1_baselines.py
```
