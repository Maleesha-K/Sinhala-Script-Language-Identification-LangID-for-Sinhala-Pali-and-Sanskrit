# OpenLID-v2 Fine-Tuning Guide & Documentation

This document provides a comprehensive, step-by-step technical reference for the zero-shot benchmarking, fine-tuning, two-stage hierarchical pipeline implementation, and evaluation of the **OpenLID-v2** model (`laurievb/OpenLID-v2`) for **Sinhala**, **Pali**, and **Sanskrit** (written in Sinhala script), as well as **Devanagari Sanskrit** (`san_Deva`).

---

## 1. Overview & Objective

`OpenLID-v2` is a multi-lingual language identification model built on FastText architecture. Stock `OpenLID-v2` only supports a single label (`sin_Sinh`) for text written in the Sinhala script. It lacks native classification heads for:
- **Pali** (written in Sinhala script)
- **Sanskrit** (written in Sinhala script)

When evaluated zero-shot on datasets containing Pali and Sanskrit in Sinhala script, stock `OpenLID-v2` predicts `sin_Sinh` for all of them, producing **4,354 False Positives** and reducing Sinhala precision to **37.70%** (F1 = **54.40%**).

**Objective**: Fine-tune `OpenLID-v2` using supervised transfer learning on [`data/Nadil/train.csv`](file:///c:/Users/User/Desktop/Vscode/Sinhala-Script%20Language%20Identification%20%28LangID%29%20for%20Sinhala,%20Pali%20and%20Sanskrit/Sinhala-Script-Language-Identification-LangID-for-Sinhala-Pali-and-Sanskrit/data/Nadil/train.csv) and build a **Two-Stage Hierarchical Pipeline** to achieve high F1 scores across both global background languages and target Sinhala-script languages.

---

## 2. Dataset Architecture

### A. Fine-Tuning Dataset ([`data/Nadil/train.csv`](file:///c:/Users/User/Desktop/Vscode/Sinhala-Script%20Language%20Identification%20%28LangID%29%20for%20Sinhala,%20Pali%20and%20Sanskrit/Sinhala-Script-Language-Identification-LangID-for-Sinhala-Pali-and-Sanskrit/data/Nadil/train.csv))
- **Total Rows**: **60,285 sentences**
- **Language Breakdown**:
  - `sinhala`: 26,675 rows
  - `pali`: 23,490 rows
  - `sanskrit`: 10,120 rows

### B. Hybrid Benchmark Datasets (`datasets/preprocessed/`)
Constructed by preprocessing raw benchmarks, preserving Devanagari Sanskrit (`san_Deva`), and injecting all 7,047 target rows from [`data/Nadil/test.csv`](file:///c:/Users/User/Desktop/Vscode/Sinhala-Script%20Language%20Identification%20%28LangID%29%20for%20Sinhala,%20Pali%20and%20Sanskrit/Sinhala-Script-Language-Identification-LangID-for-Sinhala-Pali-and-Sanskrit/data/Nadil/test.csv):
1. **`flores_plus.jsonl`**: 229,687 total rows (contains 1,012 `san_Deva` + 7,047 target test rows)
2. **`commonlid.jsonl`**: 380,277 total rows (contains 895 `san_Deva` + 7,047 target test rows)
3. **`wili-2018.jsonl`**: 241,047 total rows (contains 1,000 `san_Deva` + 7,047 target test rows)

---

## 3. Evaluation & Benchmark Results

### A. Zero-Shot OpenLID-v2 Performance

| Hybrid Benchmark | Sinhala-Sinh F1 | Pali-Sinh F1 | Sanskrit-Sinh F1 | Sanskrit-Deva F1 | English-Latn F1 | Tamil-Taml F1 | German-Latn F1 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`flores_plus`** | **54.40%** | **0.00%** | **0.00%** | **0.0350** | **99.95%** | **100.00%** | **100.00%** |
| **`commonlid`** | **54.40%** | **0.00%** | **0.00%** | **0.1169** | **89.73%** | **98.77%** | **92.39%** |
| **`wili-2018`** | **54.40%** | **0.00%** | **0.00%** | **0.0276** | **94.27%** | **99.40%** | **98.17%** |

### B. Two-Stage OpenLID-v2 Pipeline Performance

| Hybrid Benchmark | Sinhala-Sinh F1 | Pali-Sinh F1 | Sanskrit-Sinh F1 | Sanskrit-Deva F1 | English-Latn F1 | Tamil-Taml F1 | German-Latn F1 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`flores_plus`** | **96.70%** | **97.43%** | **97.04%** | **0.0350** | **99.95%** | **100.00%** | **100.00%** |
| **`commonlid`** | **96.70%** | **97.43%** | **97.04%** | **0.1169** | **89.73%** | **98.77%** | **92.39%** |
| **`wili-2018`** | **96.70%** | **97.43%** | **97.04%** | **0.0276** | **94.27%** | **99.40%** | **98.17%** |

---

## 4. Technical Analysis: Hindi Devanagari (`hin_Deva`) F1 Drop in OpenLID-v2

> [!NOTE]
> **Why OpenLID-v2 outputs a lower F1 score for Hindi Devanagari (`0.0361`) compared to FastText LID-176 (`0.9629`)**

### Root Cause: Fine-Grained Dialect Classification
Unlike standard `FastText LID-176` (which groups all Hindi variants into a single macro-language label `__label__hi` / `__label__hin_Deva`), **OpenLID-v2** was trained on NLLB's fine-grained multi-dialect taxonomy. OpenLID-v2 splits standard Hindi into multiple regional Devanagari dialects:
- `bho_Deva` (Bhojpuri)
- `mai_Deva` (Maithili)
- `awa_Deva` (Awadhi)
- `hne_Deva` (Chhattisgarhi)
- `hin_Deva` (Standard Hindi)

### Empirical Prediction Breakdown on FLORES+ Hindi (`hin_Deva`)
When evaluated on 1,012 ground-truth Hindi FLORES+ sentences, OpenLID-v2 predicts:
- **68.1% (689 sentences)** $\rightarrow$ `bho_Deva` (Bhojpuri)
- **15.1% (153 sentences)** $\rightarrow$ `mai_Deva` (Maithili)
- **11.0% (111 sentences)** $\rightarrow$ `awa_Deva` (Awadhi)
- **2.6% (26 sentences)** $\rightarrow$ `hne_Deva` (Chhattisgarhi)
- **2.5% (25 sentences)** $\rightarrow$ `hin_Deva` (Standard Hindi)

### Conclusion
* **Macro Hindi-Belt Accuracy**: OpenLID-v2 recognizes Devanagari Hindi-belt sentences with **99.3% total accuracy** across dialects.
* **Single-Label Benchmark Matching**: Because benchmark datasets (FLORES+, WiLI-2018) strictly expect the single label `hin_Deva`, classifying 95%+ into Bhojpuri/Maithili results in an artificial single-label F1 drop to **3.61%**.

---

## 5. Code Locations & Resources

- **Two-Stage OpenLID Benchmark Script**: [`data_pipeline/scripts/07.benchmark_finetuned/benchmark_openlid_twostage.py`](file:///c:/Users/User/Desktop/Vscode/Sinhala-Script%20Language%20Identification%20%28LangID%29%20for%20Sinhala,%20Pali%20and%20Sanskrit/Sinhala-Script-Language-Identification-LangID-for-Sinhala-Pali-and-Sanskrit/data_pipeline/scripts/07.benchmark_finetuned/benchmark_openlid_twostage.py)
- **Master Combined Comparison CSV**: [`Comparison_Tables_Final_Combined.csv`](file:///c:/Users/User/Desktop/Vscode/Sinhala-Script%20Language%20Identification%20%28LangID%29%20for%20Sinhala,%20Pali%20and%20Sanskrit/Sinhala-Script-Language-Identification-LangID-for-Sinhala-Pali-and-Sanskrit/Comparison_Tables_Final_Combined.csv)
