# 01: Pretrained Foundation Baseline Models

Houses configurations, download instructions, and zero-shot evaluators for standard global foundation models before domain adaptation.

---

## 🌐 Foundation Model Lineup

| Model | Checkpoint Source | Languages | Parameter Size |
| :--- | :--- | :--- | :--- |
| **fastText lid.176** | Meta AI | 176 | ~126 MB |
| **OpenLID v3** | Hugging Face | 201 | ~1.2 GB |
| **GlotLID v3** | CIS LMU | 2000+ | ~1.6 GB |
| **NLLB-LID-218** | Meta AI | 218 | ~1.1 GB |
| **ConLID** | Hugging Face | Multi | ~500 MB |
| **XLM-RoBERTa Base**| Hugging Face | 100 | ~1.1 GB |

---

## 🔬 Evaluation
Zero-shot benchmarks are executed via `pipeline/scripts/04.benchmark_zero_shot/`.
