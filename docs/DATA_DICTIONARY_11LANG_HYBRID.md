# Data Dictionary: 11-Language Uniform Hybrid Dataset (Phase 2)

---

## 1. Overview & Purpose
This dataset was constructed to benchmark baseline and state-of-the-art (SOTA) language identification models in an **Open-World Global Context** (Phase 2). 

### Core Design Principles:
1. **Zero Test-Set Contamination:** No sentence was sampled from official evaluation benchmarks (FLORES+, CommonLID, or WiLI-2018). All benchmark evaluations remain strictly out-of-distribution.
2. **Perfect Uniform Balance (Option B):** Exactly **10,000 sentences per class** across all 11 target and global language-script pairs (total: **110,000 sentences**). Every class holds an identical $9.09\%$ share of the corpus, eliminating majority-class bias.
3. **Stratified Partitioning:** A strictly stratified 90/10 split ensuring identical class distributions in both training and validation sets.

---

## 2. File Specifications

| File Path | Description | Rows | Rows per Class | Encoding |
| :--- | :--- | :--- | :--- | :--- |
| `data_pipeline/datasets/finetuning/train_11lang_uniform.csv` | Training Split (90%) | **99,000** | Exactly 9,000 | UTF-8 |
| `data_pipeline/datasets/finetuning/val_11lang_uniform.csv` | Validation Split (10%) | **11,000** | Exactly 1,000 | UTF-8 |
| **Combined Total** | **Complete Dataset** | **110,000** | **Exactly 10,000** | **UTF-8** |

---

## 3. Schema & Column Descriptions

| Column Name | Data Type | Nullable | Description | Example |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `string` | No | Unique sentence identifier prefixed with split type | `train_11lang_000042` |
| `text` | `string` | No | Full sentence text cleaned and normalized | `සම්මා සම්බුද්ධස්ස නමෝ තස්ස` |
| `label` | `string` | No | Standard BCP-47 formatted `[Lang]-[Script]` tag | `Pali-Sinh` |
| `source` | `string` | No | Name of the originating source repository/corpus | `target_train` |

---

## 4. Class Taxonomy & Provenance Breakdown

| # | BCP-47 Tag | Language | Script | Unicode Block | Primary Provenance | Train Rows | Val Rows | Total Rows |
| :-: | :--- | :--- | :--- | :--- | :--- | :-: | :-: | :-: |
| 1 | **`Sinh-Sinh`** | Sinhala | Sinhala | `U+0D80–U+0DFF` | `data/Nadil/train.csv` (`pali-sinhala-parallel`, `SiPaKosa`) | 9,000 | 1,000 | 10,000 |
| 2 | **`Pali-Sinh`** | Pali | Sinhala | `U+0D80–U+0DFF` | `data/Nadil/train.csv` (`pali-sinhala-parallel`, `SiDiaC-v2`) | 9,000 | 1,000 | 10,000 |
| 3 | **`San-Sinh`** | Sanskrit | Sinhala | `U+0D80–U+0DFF` | `data/Nadil/train.csv` (`SansinNT`, `DCS` via *Aksharamukha*) | 9,000 | 1,000 | 10,000 |
| 4 | **`San-Deva`** | Sanskrit | Devanagari | `U+0900–U+097F` | `surajp/sanskrit_classic` (Hugging Face) | 9,000 | 1,000 | 10,000 |
| 5 | **`Eng-Latn`** | English | Latin | `U+0000–U+007F` | Tatoeba Corpus (`tatoeba/sentences.csv`) | 9,000 | 1,000 | 10,000 |
| 6 | **`Tam-Taml`** | Tamil | Tamil | `U+0B80–U+0BFF` | Wikimedia Wikipedia (`20231101.ta`) | 9,000 | 1,000 | 10,000 |
| 7 | **`Hin-Deva`** | Hindi | Devanagari | `U+0900–U+097F` | Tatoeba Corpus (`tatoeba/sentences.csv`) | 9,000 | 1,000 | 10,000 |
| 8 | **`Ben-Beng`** | Bengali | Bengali | `U+0980–U+09FF` | Tatoeba Corpus (`tatoeba/sentences.csv`) | 9,000 | 1,000 | 10,000 |
| 9 | **`Ara-Arab`** | Arabic | Arabic | `U+0600–U+06FF` | Tatoeba Corpus (`tatoeba/sentences.csv`) | 9,000 | 1,000 | 10,000 |
| 10 | **`Fre-Latn`** | French | Latin | `U+0000–U+007F` | Tatoeba Corpus (`tatoeba/sentences.csv`) | 9,000 | 1,000 | 10,000 |
| 11 | **`Ger-Latn`** | German | Latin | `U+0000–U+007F` | Tatoeba Corpus (`tatoeba/sentences.csv`) | 9,000 | 1,000 | 10,000 |
| | **TOTAL** | | | | | **99,000** | **11,000** | **110,000** |

---

## 5. Detailed Source Provenance

### A. Target Sinhala-Script Classes (`Sinh-Sinh`, `Pali-Sinh`, `San-Sinh`)
Drawn from the project's internal curated training pool (`data/Nadil/train.csv`):
* **`Sinh-Sinh`:** Sampled from 26,675 available sentences originating from `pali-sinhala-parallel` (canonical Buddhist commentary translations) and `SiPaKosa` (Tripitaka literature).
* **`Pali-Sinh`:** Sampled from 23,490 available sentences originating from canonical Pali texts in Sinhala script (`pali-sinhala-parallel`) and historical Buddhist publications (`SiDiaC-v2`).
* **`San-Sinh`:** Sampled from 10,120 available sentences originating from native Sinhala-script Sanskrit publications (`SansinNT`), the Digital Corpus of Sanskrit (`DCS`) transliterated via Aksharamukha, and scholarly citations (`SiDiaC-v2`).

### B. Sanskrit in Devanagari (`San-Deva`)
* Extracted from the **`surajp/sanskrit_classic`** corpus on Hugging Face (342,033 sentences).
* Contains classical Sanskrit epics and philosophical prose formatted in standard Devanagari.
* Explicitly included to force models to differentiate language vs. script (distinguishing `San-Sinh` from `San-Deva`, and `Hin-Deva` from `San-Deva`).

### C. Tamil in Tamil Script (`Tam-Taml`)
* Extracted from the official **Wikimedia Tamil Wikipedia dump (`wikimedia/wikipedia/20231101.ta`)**.
* Contains encyclopedic Tamil sentences written in native Tamil script (`U+0B80–U+0BFF`).

### D. Global Multilingual Background Classes
Extracted from the **Tatoeba Project Corpus** (`data_pipeline/datasets/raw_download/tatoeba/sentences.csv`):
* `Eng-Latn` (English, Latin script)
* `Hin-Deva` (Hindi, Devanagari script)
* `Ben-Beng` (Bengali, Bengali script)
* `Ara-Arab` (Arabic, Arabic script)
* `Fre-Latn` (French, Latin script)
* `Ger-Latn` (German, Latin script)

---

## 6. Preprocessing & Quality Assurance Pipeline

1. **Sentence Length Constraints:**
   * Minimum length: **15 characters**
   * Minimum word count: **3 words**
   * Maximum word count: **60 words**
   * Eliminates single-word noise, website navigation headers, and book titles.
2. **Whitespace Normalization:**
   * Consecutive tabs, spaces, and newline sequences collapsed into single spaces (`\s+ -> ' '`).
3. **Within-Class Deduplication:**
   * Exact-match duplicates removed prior to sampling.
4. **Stratified Splitting:**
   * Random seed fixed to `42` (`random.seed(42)` and `random_state=42`) for 100% deterministic reproducibility.
   * Split ratio: 90% train ($9,000 \times 11 = 99,000$), 10% validation ($1,000 \times 11 = 11,000$).

---

## 7. Verification & Python Usage Example

```python
import pandas as pd

# Load the training set
train_df = pd.read_csv("data_pipeline/datasets/finetuning/train_11lang_uniform.csv")
val_df = pd.read_csv("data_pipeline/datasets/finetuning/val_11lang_uniform.csv")

print("Train shape:", train_df.shape)  # Expected: (99000, 4)
print("Val shape:  ", val_df.shape)    # Expected: (11000, 4)

# Verify uniform class balance
print("\nTrain class balance:")
print(train_df["label"].value_counts())  # Exactly 9,000 for each of the 11 classes

print("\nValidation class balance:")
print(val_df["label"].value_counts())    # Exactly 1,000 for each of the 11 classes
```
