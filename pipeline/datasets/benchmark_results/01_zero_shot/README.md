# Phase 1B (Table 1): Foundation Zero-Shot Results

Evaluates out-of-the-box foundation models across global multilingual benchmarks and target languages without any domain adaptation.

---

## 🎯 Evaluated Foundation Models

- **fastText `lid.176`**: 176-language global identifier by Facebook Research.
- **OpenLID v2**: 201-language state-of-the-art fastText-based identifier.
- **GlotLID / NLLB-200**: Massive multilingual neural representations.

---

## 📉 Evaluated Benchmarks & Key Findings

1. **Global Benchmarks (FLORES+, WiLI-2018, CommonLID)**:
   - Foundation models perform strongly on high-resource languages (e.g. English, French, German >95%).
2. **Failure on Sinhala-Script Pali & Sanskrit**:
   - Because standard models lack Sinhala-script annotations for Pali and Sanskrit, all Pali and Sanskrit text in Sinhala script is either misclassified as Sinhala (`sin_Sinh`), misclassified as other Indic scripts, or rejected.

---

## 📂 Result Files

- `fasttext_lid_176_zero_shot_flores_plus.csv`
- `fasttext_lid_176_zero_shot_wili-2018.csv`
- `fasttext_lid_176_zero_shot_commonlid.csv`
- `openlid_v2_flores_plus.csv`
- `openlid_v2_wili-2018.csv`
- `openlid_v2_commonlid.csv`
- `fasttext_lid_176_finetuned_benchmark_zero_shot.csv`
- `fasttext_lid_176_finetuned_augmented_benchmark_zero_shot.csv`
- `fasttext_lid_176_finetuned_all_langs_benchmark_zero_shot.csv`
