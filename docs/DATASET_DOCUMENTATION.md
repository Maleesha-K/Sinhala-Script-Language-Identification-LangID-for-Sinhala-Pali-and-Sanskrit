# LangID Dataset: Final Documentation

**Dataset Version**: Final (Cleaned)  
**File**: `data/processed/master_clean.csv`  
**Task**: Language Identification (LangID) for Sinhala, Pali, and Sanskrit in Sinhala script.

---

## 1. Executive Summary

This dataset represents the first dedicated benchmark for distinguishing **Sinhala, Pali, and Sanskrit** when entirely written in the **Sinhala script**. It addresses a critical gap in language identification by differentiating closely related classical languages sharing the same script, solving the problem of NLP systems mistakenly classifying all Sinhala-script text as Sinhala.

The final, cleaned dataset contains **224,959 high-quality sentence-level rows**. It has undergone rigorous programmatic auditing to ensure it provides an unambiguous, fair, and perfectly balanced training signal.

---

## 2. Dataset Architecture & Schema

| Feature | Value |
|:---|:---|
| **Total Rows** | 224,959 |
| **Core Classification Task Rows** | 131,496 (Sinhala, Pali, Sanskrit) |
| **Out-of-Distribution Task Rows** | 93,463 (Mixed/Code-switched) |
| **Columns** | 8 |
| **Format** | UTF-8 Encoded CSV |

### Schema Breakdown

| Column | Type | Description |
|:---|:---|:---|
| `id` | `string` | Unique identifier per sentence (e.g., `sipakosa_468088`, `wiki_sa_020591`). |
| `text` | `string` | The sentence text. Guaranteed to contain valid Sinhala Unicode characters (U+0D80–U+0DFF) and be > 10 characters long. |
| `label` | `string` | Language label: `sinhala`, `pali`, `sanskrit`, or `mixed`. |
| `source` | `string` | High-level origin (e.g., `SiPaKosa`, `wiki_sa`, `SansinNT`, `SiDiaC`). |
| `subcorpus` | `string` | Finer-grained provenance (e.g., `tripitaka`, `old-books`, `wiki`). |
| `group_id` | `string` | Document-level ID to prevent train/test leakage for sentences originating from the same document. |
| `is_core` | `bool` | `True` for `sinhala`/`pali`/`sanskrit`; `False` for `mixed`. |
| `split` | `string` | Machine learning split: `train`, `val`, or `test`. |

---

## 3. Data Sources & Provenance

The dataset is constructed by intelligently merging multiple digital humanities and historical sources:

| Source | Rows | % of Total | Core Languages | Description |
|:---|---:|---:|:---|:---|
| **SiPaKosa** | 180,948 | 80.44% | Sinhala, Pali, Mixed | Hugging Face corpus (`RaniduG/SiPaKosa-Sent`) containing Buddhist tripitaka, old books, and related texts. |
| **wiki_sa** | 33,589 | 14.93% | Sanskrit | Extracted from the Sanskrit Wikipedia dump and programmatically transliterated from Devanagari to Sinhala script using `aksharamukha`. |
| **SansinNT** | 7,952 | 3.53% | Sanskrit | Sanskrit translation of the New Testament (USFX XML format) published natively in Sinhala script. |
| **SiDiaC** | 2,470 | 1.10% | Sinhala | Historical/diachronic Sinhala sentences from a collection of 185 OCR'd books. |

---

## 4. Class Balance (The "Core" Task)

A major milestone of this dataset is resolving the heavy class imbalance present in raw data. By strategically downsampling over-represented classes and augmenting the under-represented Sanskrit class (via transliteration), the benchmark achieves near-perfect balance for the core 3-way classification task.

| Language | Rows | Proportion (Core) |
|:---|---:|---:|
| **Pali** | 49,986 | 38.01% |
| **Sanskrit** | 41,541 | 31.59% |
| **Sinhala** | 39,969 | 30.39% |

> [!TIP]
> **Imbalance Ratio: 1.25×** (largest vs. smallest). This allows downstream ML models to train without suffering from the "majority class problem", where they simply guess the most frequent language.

*(Note: An additional 93,463 rows labeled `mixed` are provided for advanced models that attempt to detect code-switching).*

---

## 5. Machine Learning Splits (Train / Val / Test)

The dataset provides pre-computed dataset splits designed to strictly prevent **data leakage**.

Splits are determined at the **`group_id` level**. This guarantees that all sentences belonging to the same original document (e.g., the same Bible chapter or the same book) stay together in a single split. A model will never be evaluated on a document it was partially trained on.

### Stratified Distribution (80% / 10% / 10%)

| Label | Train | Val | Test | TOTAL |
|:---|---:|---:|---:|---:|
| **mixed** | 74,770 | 9,346 | 9,347 | **93,463** |
| **pali** | 39,989 | 4,999 | 4,998 | **49,986** |
| **sanskrit** | 33,890 | 4,159 | 3,492 | **41,541** |
| **sinhala** | 32,066 | 4,046 | 3,857 | **39,969** |
| **Overall** | **180,715** | **22,550** | **21,694** | **224,959** |

*Overall proportions: 80.33% Train / 10.02% Val / 9.64% Test.*

---

## 6. Text Quality & Integrity Certifications

The final dataset `master_clean.csv` passed a comprehensive, automated 18-point audit.

### ✅ 1. Contradictory Label Resolution
* **Issue**: Initially, ~13,000 strings appeared under conflicting labels (e.g., marked both as "sinhala" and "mixed").
* **Resolution**: If a text was assigned a core label and `mixed`, the core label was prioritized. If it was assigned multiple core labels (e.g., both Pali and Sinhala), it was discarded as fatally ambiguous.
* **Result**: **0 contradictory rows.** Unambiguous gradient signals for the model.

### ✅ 2. Script Enforcement
* **Issue**: OCR artifacts and transliteration debris resulted in rows containing only punctuation or English numerals.
* **Resolution**: Rows containing zero Sinhala Unicode block characters (U+0D80–U+0DFF) were stripped.
* **Result**: **100% of rows contain valid Sinhala script characters.**

### ✅ 3. Length Constraints
* **Issue**: Micro-texts (e.g., single characters or spaces) lacked enough signal for LangID classification.
* **Resolution**: Rows shorter than 10 characters were stripped.
* **Result**: All texts have sufficient context. (Mean length: ~85 characters / ~12 words).

### ✅ 4. Duplicate & Leakage Integrity
* **Duplicates**: **0** exact duplicates exist in the dataset.
* **Null Values**: **0** nulls or empty strings across all columns.
* **Leakage Check**: **PASS**. All 182,168 `group_ids` are verified to appear in exactly one split boundary.

---

## 7. Next Steps for Researchers

1. **Target Filtering**: For standard ML models (e.g., fastText, Naive Bayes, BERT), filter the dataset to `df[df.is_core == True]` to perform the pure 3-way classification task.
2. **Standardized Splits**: Rely exclusively on the provided `split` column. Do not use random `train_test_split` functions, as random shuffling ignores document boundaries and artificially inflates accuracy metrics.
3. **Advanced Detection**: Researchers exploring code-mixing detection can use the `mixed` label as an additional out-of-distribution class.
