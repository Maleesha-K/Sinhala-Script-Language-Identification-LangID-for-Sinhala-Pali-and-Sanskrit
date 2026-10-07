# Aya Background Rehearsal Dataset (`CohereLabs/aya_dataset`)

This directory documents the background multilingual extraction pipeline built on the **Aya Dataset** by Cohere For AI.

---

## 🌍 Why These 7 Background Languages?

The 7 non-Sanskrit background rehearsal languages were systematically chosen to balance regional proximity, linguistic typology, and global representation:

1. **English (`eng_Latn`)**: Universal global baseline and dominant anchor language.
2. **Tamil (`tam_Taml`)**: Co-official language of Sri Lanka and Dravidian geographic neighbor.
3. **Hindi (`hin_Deva`)**: High-resource Indo-Aryan sister language (shares vocabulary roots with Sanskrit/Pali).
4. **Bengali (`ben_Beng`)**: Eastern Indo-Aryan language with shared Sanskrit loanwords and distinct Indic script.
5. **Arabic (`arb_Arab`)**: Afro-Asiatic / Semitic representative, high-resource global benchmark.
6. **French (`fra_Latn`)**: Western Romance language baseline.
7. **German (`deu_Latn`)**: Western Germanic language baseline.

*(Note: Sanskrit in Devanagari script is not available in Aya and is sourced from `surajp/sanskrit_classic` in `pipeline/datasets/hybrid_finetune/sanskrit_devanagari/`).*

---

## 🛠 Extraction Script

Run the standalone streaming extraction script to re-download or inspect the exact sample quota:

```bash
python pipeline/datasets/hybrid_finetune/aya_dataset/extract_aya_rehearsal.py
```

The extracted samples are compiled into `pipeline/datasets/hybrid_finetune/replay_mixed/train_11lang_uniform.csv` and `val_11lang_uniform.csv`.
