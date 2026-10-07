# fastText (Trained From Scratch)

**Architecture Paradigm**: Averaged Subword Embeddings with Hierarchical Softmax / Negative Sampling

---

## 📈 Benchmark Performance
- **Full Sentence Accuracy**: 99.80% (Macro F1: 0.9980)
- **1-Word Stress Test Accuracy**: 83.44%

---

## 🚀 Training & Evaluation
To train and benchmark this model across full, 5-word, 3-word, and 1-word inputs:
```bash
python pipeline/scripts/00.traditional_baselines/benchmark_phase1_baselines.py
```
