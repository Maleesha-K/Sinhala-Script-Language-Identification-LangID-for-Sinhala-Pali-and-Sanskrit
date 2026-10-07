# Phase 1A: Traditional ML & Shallow Neural Baseline Results

This tier contains the evaluation results of our **7 from-scratch models** trained on `target_language/train` and tested across sentence-length and short fragment stress tests.

---

## 📊 Summary Results Table

| Model Architecture | Paradigm | Full Text Acc | Full Text F1 | 5-Word Acc | 5-Word F1 | 3-Word Acc | 3-Word F1 | 1-Word Acc | 1-Word F1 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Multinomial Naive Bayes** | Probabilistic ML | **0.9986** | **0.9985** | **0.9973** | **0.9972** | **0.9899** | **0.9885** | **0.8714** | **0.8584** |
| **Linear SVM** | Margin-based ML | 0.9982 | 0.9984 | 0.9891 | 0.9880 | 0.9370 | 0.9309 | 0.6503 | 0.6099 |
| **Char n-gram + LogReg** | Linear Baseline | 0.9977 | 0.9979 | 0.9837 | 0.9800 | 0.9361 | 0.9168 | 0.6985 | 0.6223 |
| **fastText (re-trained)** | Subword Embeddings | 0.9980 | 0.9980 | 0.9938 | 0.9934 | 0.9746 | 0.9702 | 0.8344 | 0.8027 |
| **Char-BiGRU** | Recurrent Deep Learning | 0.9969 | 0.9970 | 0.9705 | 0.9630 | 0.9241 | 0.9015 | 0.7617 | 0.6916 |
| **Char-CNN (1D)** | Convolutional Deep Learning | 0.9960 | 0.9963 | 0.9842 | 0.9821 | 0.9519 | 0.9434 | 0.7896 | 0.7654 |
| **XGBoost** | Gradient Boosting | 0.9946 | 0.9948 | 0.9679 | 0.9632 | 0.8886 | 0.8682 | 0.5509 | 0.4516 |

---

## 💡 Key Empirical Insights

1. **Full-Length Performance**: All 7 baselines achieve >99.4% accuracy on full sentences, indicating that Sinhala-script language identification is readily solvable with sufficient context.
2. **Short Fragment Degradation**: As input length drops to 1-word tokens, discriminative capability diverges sharply. Multinomial NB and re-trained fastText demonstrate superior robustness (87.1% and 83.4% 1-word accuracy), while margin-based and tree-based models degrade to 55–65%.

---

## 📂 Files
- `phase1_baselines_consistent.csv`: The official tabular benchmark records.
