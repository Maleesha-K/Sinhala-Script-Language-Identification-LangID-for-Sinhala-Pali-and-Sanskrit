# Hybrid Finetuning & Continual Learning Datasets

This directory contains datasets designed to fine-tune foundation models (such as fastText `lid.176` and OpenLID) to recognize low-resource Sinhala-script languages **without suffering catastrophic forgetting** on global languages.

---

## 🧠 Continual Learning Strategy

When a pre-trained model is fine-tuned strictly on target languages (`sin_Sinh`, `pli_Sinh`, `san_Sinh`), its weights adapt exclusively to these classes, causing catastrophic forgetting of its original global language capabilities.

To solve this, we employ **Experience Replay / Rehearsal Finetuning**:
1. **Target Languages (3 classes)**: Sinhala, Pali, and Sanskrit in Sinhala script.
2. **Cross-Script Control (1 class)**: Sanskrit in Devanagari script (`san_Deva`) from `surajp/sanskrit_classic`.
3. **Global Background Rehearsal (7 classes)**: English, Tamil, Hindi, Bengali, Arabic, French, and German from `CohereLabs/aya_dataset`.

---

## 📁 Subdirectories

### 1. `replay_mixed/`
The fully assembled, balanced 11-language continual training split:
- `train_11lang_uniform.csv` / `.txt` / `.jsonl`: **99,000 samples** (9,000 balanced per class across 11 languages).
- `val_11lang_uniform.csv` / `.txt` / `.jsonl`: **11,000 samples** (1,000 balanced per class across 11 languages).

### 2. `sanskrit_devanagari/`
The Devanagari Sanskrit background corpus (`surajp/sanskrit_classic`, 342,031 lines):
- `sanskrit_devanagari.csv`, `sanskrit_devanagari.txt`, `sanskrit_devanagari.jsonl`.
- Ensures models distinguish script variants of Sanskrit rather than confounding script with language.

### 3. `aya_dataset/`
Extraction pipeline and specifications for the 7 non-Sanskrit background languages from `CohereLabs/aya_dataset`:
- Contains `extract_aya_rehearsal.py` for reproducible streaming extraction.
