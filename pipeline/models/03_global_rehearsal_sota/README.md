# 03: Global Multilingual Rehearsal SOTA Models (Forgetting Mitigated)

This tier houses continual learning models trained using **experience replay buffers** (`pipeline/datasets/hybrid_finetune/replay_mixed/`).

---

## 🏆 Key Breakthrough
- **Preserved Target Accuracy**: >99.3% Macro F1 on Sinhala, Pali, and Sanskrit in Sinhala script.
- **Mitigated Catastrophic Forgetting**: Preserves global multilingual identification accuracy across FLORES+, WiLI-2018, and CommonLID within 1–2% of the original foundation models.
- **Cross-Script Sanskrit Resolution**: Reliably differentiates `san_Sinh` from `san_Deva`.

---

## 📂 Checkpoint Repository
Trained continual checkpoints are hosted on Hugging Face:
- **Organization**: [https://huggingface.co/script-langid](https://huggingface.co/script-langid)
- Run `python scripts/sync_hf_organization.py` to synchronize model artifacts.
