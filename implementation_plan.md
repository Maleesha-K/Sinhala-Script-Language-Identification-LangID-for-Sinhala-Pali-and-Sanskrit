# Generate FastText Benchmark Comparison CSV Plan

This plan details the creation of a standalone CSV file based on [`Comparison Tables - Final copy.csv`](file:///c:/Users/User/Desktop/Vscode/Sinhala-Script%20Language%20Identification%20%28LangID%29%20for%20Sinhala,%20Pali%20and%20Sanskrit/Sinhala-Script-Language-Identification-LangID-for-Sinhala-Pali-and-Sanskrit/Comparison%20Tables%20-%20Final%20copy.csv) containing all zero-shot and fine-tuned evaluation values for the **fastText LID-176** model.

---

## User Review Required

> [!IMPORTANT]
> **Output CSV File**: `Comparison Tables - FastText Finetuned.csv`
> The new CSV will replicate the exact 38-column structure of `Comparison Tables - Final copy.csv` and populate the fastText LID-176 row under both **Zero shot Results** and **FineTuning Results** across `flores_plus`, `commonlid`, and `wili-2018`.

---

## Proposed Changes

### Script / CSV Generation

#### [NEW] [`generate_fasttext_comparison_csv.py`](file:///c:/Users/User/Desktop/Vscode/Sinhala-Script%20Language%20Identification%20%28LangID%29%20for%20Sinhala,%20Pali%20and%20Sanskrit/Sinhala-Script-Language-Identification-LangID-for-Sinhala-Pali-and-Sanskrit/scripts/generate_fasttext_comparison_csv.py)
- Read `Comparison Tables - Final copy.csv`.
- Fill in the zero-shot and fine-tuned values for `fastText LID-176`:
  - **Zero-Shot (`flores_plus`)**: `si`: 0.5438, `san_Deva`: 0.9594, `en`: 0.7213, `ta`: 1.0, `hi`: 1.0, `bn`: 1.0, `ar`: 0.6667, `fr`: 0.9873, `de`: 0.9892
  - **Zero-Shot (`commonlid`)**: `si`: 0.5438, `san_Deva`: 0.8886, `en`: 0.9725, `ta`: 0.9643, `hi`: 0.9816, `bn`: 0.9936, `ar`: 0.9947, `fr`: 0.9447, `de`: 0.9672
  - **Zero-Shot (`wili-2018`)**: `si`: 0.5438, `san_Deva`: 0.9904, `en`: 0.9434, `ta`: 0.995, `hi`: 0.9904, `bn`: 0.9529, `fr`: 0.9779, `de`: 0.985
  - **Fine-Tuned (`flores_plus`)**: `sinhala`: 0.6047, `pali`: 0.6268, `sanskrit`: 0.6331
  - **Fine-Tuned (`commonlid`)**: `sinhala`: 0.0851, `pali`: 0.4258, `sanskrit`: 0.3521
  - **Fine-Tuned (`wili-2018`)**: `sinhala`: 0.7559, `pali`: 0.6625, `sanskrit`: 0.6071
- Save to `Comparison Tables - FastText Finetuned.csv`.

---

## Verification Plan

### Automated Verification
- Run `python scripts/generate_fasttext_comparison_csv.py`.
- Verify the generated CSV file exists and matches the row and column structure of `Comparison Tables - Final copy.csv`.

### Manual Verification
- Inspect the generated CSV table for accuracy and formatting.
