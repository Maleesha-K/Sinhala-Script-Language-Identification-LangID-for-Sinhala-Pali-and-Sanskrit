# Benchmark Evaluation Results

This directory organizes all empirical findings across the 4 core experimental phases of our research paper.

---

## 🏛 The 4 Experimental Pillars

```
pipeline/datasets/benchmark_results/
├── 00_traditional_ml_baselines/   # Phase 1A: 7 Classical ML & Shallow Neural Baselines
├── 01_zero_shot/                  # Phase 1B: Foundation Models Zero-Shot Evaluation (Table 1)
├── 02_target_only/                # Phase 2: Target-Only Specialist Finetuning (Table 2 - Catastrophic Forgetting)
├── 03_multilingual_rehearsal/     # Phase 3: Continual Rehearsal Finetuning (Table 3 - Forgetting Mitigated)
└── compute_metrics.py             # Automatic evaluation & scoring script
```

---

## 🔬 Experimental Overview

### Phase 1A: Traditional ML & Shallow Neural Baselines
7 models trained from scratch on `target_language/train` and stress-tested across short text fragments (Full, 5 words, 3 words, 1 word).

### Phase 1B: Zero-Shot Foundation Models
Evaluating general-purpose multilingual models (fastText `lid.176`, OpenLID v2, GlotLID, NLLB-200) out of the box on global benchmarks and held-out target data.

### Phase 2: Target-Only Specialist Finetuning
Demonstrating **catastrophic forgetting**: fine-tuning solely on target languages yields >99% in-domain accuracy but destroys global multilingual capabilities.

### Phase 3: Multilingual Rehearsal Finetuning
Demonstrating **continual learning recovery**: fine-tuning with 11-language balanced replay preserves >99% target language accuracy while recovering high global accuracy on FLORES+, WiLI-2018, and CommonLID.

---

## ⚡ Metric Evaluation Tool

Run `compute_metrics.py` to evaluate accuracy and macro F1 across prediction files:

```bash
python pipeline/datasets/benchmark_results/compute_metrics.py
```
