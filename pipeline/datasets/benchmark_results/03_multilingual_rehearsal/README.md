# Phase 3 (Table 3): Multilingual Rehearsal Continual Results

Documents the empirical recovery achieved via **continual learning with multilingual experience rehearsal** (`replay_mixed`).

---

## 🏆 Key Empirical Findings

By fine-tuning foundation models with rehearsal buffers containing balanced global languages (from Aya) and cross-script Sanskrit (from `sanskrit_classic`):
1. **Target Language Retention**: Models achieve **>99.3% Macro F1** on Sinhala, Pali, and Sanskrit in Sinhala script.
2. **Global Benchmark Recovery**: Catastrophic forgetting is successfully mitigated. Accuracy on FLORES+, WiLI-2018, and CommonLID is preserved to within 1–2% of the original foundation model performance.
3. **Cross-Script Disambiguation**: The model reliably differentiates `san_Sinh` from `san_Deva`.

---

## 📂 Result Files

- `fasttext_lid_176_finetuned_all_langs_flores_plus.csv`
- `fasttext_lid_176_finetuned_all_langs_wili-2018.csv`
- `fasttext_lid_176_finetuned_all_langs_commonlid.csv`
- `fasttext_lid_176_finetuned_all_langs_nadil.csv`
- `fasttext_lid_176_finetuned_all_langs_tatoeba.csv`
- `openlid_v2_finetuned_all_langs_flores_plus.csv`
- `openlid_v2_finetuned_all_langs_wili-2018.csv`
- `openlid_v2_finetuned_all_langs_commonlid.csv`
- `fasttext_lid_176_finetuned_augmented_flores_plus.csv`
- `fasttext_lid_176_finetuned_augmented_wili-2018.csv`
- `fasttext_lid_176_finetuned_augmented_commonlid.csv`
- `fasttext_lid_176_finetuned_augmented_nadil.csv`
- `fasttext_lid_176_finetuned_augmented_tatoeba.csv`
