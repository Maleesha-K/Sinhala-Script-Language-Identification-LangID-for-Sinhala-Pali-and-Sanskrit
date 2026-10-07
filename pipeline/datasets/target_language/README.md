# Target Language Dataset

This directory contains the primary benchmark dataset for **Sinhala-Script Language Identification (LangID)**, addressing the identification of three distinct languages written in the **Sinhala script**:
1. **Sinhala** (`sin_Sinh` / `sinhala`)
2. **Pali** (`pli_Sinh` / `pali`)
3. **Sanskrit** (`san_Sinh` / `sanskrit`)

---

## 📈 Dataset Splits & Distribution

| Split | Directory | Sinhala | Pali | Sanskrit | Total Samples | Share |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Train** | `train/` | 26,675 | 23,490 | 10,120 | **60,285** | 81.12% |
| **Validation** | `validation/` | 3,090 | 2,725 | 1,171 | **6,986** | 9.40% |
| **Test** | `test/` | 3,118 | 2,748 | 1,181 | **7,047** | 9.48% |
| **Total** | | **32,883** | **28,963** | **12,472** | **74,318** | **100.0%** |

---

## 📂 Multi-Format Support

Every split is provided in three synchronized formats for immediate compatibility:

- **`.csv`**: Tabular format (`text`, `label`) for Pandas, PyTorch DataLoaders, and Scikit-Learn.
- **`.txt`**: Supervised fastText format (`__label__<lang> <text>`).
- **`.jsonl`**: Standard JSON Lines format for Hugging Face `datasets` and modern transformer pipelines.
- **`fasttext_eval_data.json`**: Pre-formatted test split dictionary located in `test/`.

---

## 🔬 Linguistic Context

All three languages share the identical Unicode Sinhala block (`U+0D80`–`U+0DFF`), making character set detection impossible. Disambiguation requires:
- Character n-gram morpho-phonology (e.g., Pali consonant clusters, Sanskrit aspirated clusters and visarga `ඃ`, Sinhala unique vowels `ඇ`/`ඈ`).
- Lexical and syntactic cues.
