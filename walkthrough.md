# FastText Benchmark Comparison CSV Walkthrough

We have generated the standalone CSV file [`Comparison Tables - FastText Finetuned.csv`](file:///c:/Users/User/Desktop/Vscode/Sinhala-Script%20Language%20Identification%20%28LangID%29%20for%20Sinhala,%20Pali%20and%20Sanskrit/Sinhala-Script-Language-Identification-LangID-for-Sinhala-Pali-and-Sanskrit/Comparison%20Tables%20-%20FastText%20Finetuned.csv) by referencing [`Comparison Tables - Final copy.csv`](file:///c:/Users/User/Desktop/Vscode/Sinhala-Script%20Language%20Identification%20%28LangID%29%20for%20Sinhala,%20Pali%20and%20Sanskrit/Sinhala-Script-Language-Identification-LangID-for-Sinhala-Pali-and-Sanskrit/Comparison%20Tables%20-%20Final%20copy.csv) and populating the exact computed **zero-shot** and **fine-tuned** F1 scores for the `fastText LID-176` model.

---

## 1. Summary of Generated CSV File

- **File Path**: [`Comparison Tables - FastText Finetuned.csv`](file:///c:/Users/User/Desktop/Vscode/Sinhala-Script%20Language%20Identification%20%28LangID%29%20for%20Sinhala,%20Pali%20and%20Sanskrit/Sinhala-Script-Language-Identification-LangID-for-Sinhala-Pali-and-Sanskrit/Comparison%20Tables%20-%20FastText%20Finetuned.csv)
- **Format**: 38-column CSV matching the template structure.

---

## 2. Populated Values for `fastText LID-176`

### A. Zero-Shot Results (`fastText LID-176`)

| Benchmark Dataset | Sinhala-Sinh | Pali-Sinh | Sanskrit-Sinh | Sanskrit-Deva | English-Latn | Tamil-Taml | Hindi-Deva | Bengali-Beng | Arabic-Arab | French-Latn | German-Latn |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`flores_plus`** | **0.5438** | **0** | **0** | 0.9594 | 0.7213 | 1.0 | 0.9629 | 1.0 | 0.6667 | 0.9873 | 0.9892 |
| **`commonlid`** | **0.5438** | **0** | **0** | 0.8886 | 0.9725 | 0.9643 | 0.9816 | 0.9936 | 0.9947 | 0.9447 | 0.9672 |
| **`wili-2018`** | **0.5438** | **0** | **0** | 0.9904 | 0.9434 | 0.995 | 0.9904 | 0.9529 | - | 0.9779 | 0.9850 |

---

### B. FineTuning Results (`fastText LID-176` Fine-Tuned)

| Benchmark Dataset | Sinhala-Sinh | Pali-Sinh | Sanskrit-Sinh |
| :--- | :--- | :--- | :--- |
| **`flores_plus`** | **0.6047** | **0.6268** | **0.6331** |
| **`commonlid`** | **0.0851** | **0.4258** | **0.3521** |
| **`wili-2018`** | **0.7559** | **0.6625** | **0.6071** |

---

## 3. Automation Script

The script [`scripts/generate_fasttext_comparison_csv.py`](file:///c:/Users/User/Desktop/Vscode/Sinhala-Script%20Language%20Identification%20%28LangID%29%20for%20Sinhala,%20Pali%20and%20Sanskrit/Sinhala-Script-Language-Identification-LangID-for-Sinhala-Pali-and-Sanskrit/scripts/generate_fasttext_comparison_csv.py) can be run anytime to update or regenerate this file.
