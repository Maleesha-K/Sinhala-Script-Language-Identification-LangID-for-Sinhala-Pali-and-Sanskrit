# Phase 2 (Table 2): Target-Only Specialist Results (Catastrophic Forgetting)

This directory documents the empirical manifestation of **catastrophic forgetting**: when foundation models are fine-tuned exclusively on the target Sinhala-script dataset.

---

## ⚠️ Empirical Observation: The Catastrophic Forgetting Paradox

When foundation models (such as fastText `lid.176` and OpenLID v2) are adapted directly onto `target_language/train`:
- **In-Domain Target Accuracy**: Rises from ~33% to **>99.5%** on Sinhala, Pali, and Sanskrit.
- **Out-of-Domain Global Accuracy**: Collapses drastically across FLORES+, WiLI-2018, and CommonLID (global multilingual accuracy falls by >40% as foreign texts are collapsed into the new target classes).

Two-stage architectures (`conlid_twostage`, `fasttext_twostage`, `glotlid_twostage`, `nllb_twostage`) mitigate part of this effect by gating Sinhala-script inputs before sub-classifying.

---

## 📂 Result Files

- `conlid_twostage_flores_plus.csv`
- `fasttext_twostage_flores_plus.csv`
- `glotlid_twostage_flores_plus.csv`
- `nllb_twostage_flores_plus.csv`
- `openlid_twostage_flores_plus.csv`
- `fasttext_lid_176_twostage_all_langs_flores_plus.csv`
- `fasttext_lid_176_twostage_all_langs_wili-2018.csv`
- `fasttext_lid_176_twostage_all_langs_commonlid.csv`
- `openlid_v2_twostage_all_langs_flores_plus.csv`
- `openlid_v2_twostage_all_langs_wili-2018.csv`
- `openlid_v2_twostage_all_langs_commonlid.csv`
