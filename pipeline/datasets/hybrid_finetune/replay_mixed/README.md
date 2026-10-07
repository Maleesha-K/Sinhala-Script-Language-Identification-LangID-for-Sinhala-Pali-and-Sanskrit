# 11-Language Uniform Rehearsal Dataset (`replay_mixed`)

A strictly class-balanced continual rehearsal dataset designed to fine-tune foundation models while preserving global multilingual competency.

---

## 📊 Class Balance & Composition

| Language Code | Language & Script | Train Samples | Val Samples | Source | Role |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`Sinh-Sinh`** | Sinhala (Sinhala script) | 9,000 | 1,000 | Target Dataset | Core Target |
| **`Pali-Sinh`** | Pali (Sinhala script) | 9,000 | 1,000 | Target Dataset | Core Target |
| **`San-Sinh`** | Sanskrit (Sinhala script) | 9,000 | 1,000 | Target Dataset | Core Target |
| **`San-Deva`** | Sanskrit (Devanagari script) | 9,000 | 1,000 | `surajp/sanskrit_classic` | Cross-Script Control |
| **`Eng-Latn`** | English (Latin script) | 9,000 | 1,000 | `CohereLabs/aya_dataset` | Global Background |
| **`Tam-Taml`** | Tamil (Tamil script) | 9,000 | 1,000 | `CohereLabs/aya_dataset` | Regional Dravidian |
| **`Hin-Deva`** | Hindi (Devanagari script) | 9,000 | 1,000 | `CohereLabs/aya_dataset` | Major Indo-Aryan |
| **`Ben-Beng`** | Bengali (Bengali script) | 9,000 | 1,000 | `CohereLabs/aya_dataset` | Eastern Indo-Aryan |
| **`Ara-Arab`** | Arabic (Arabic script) | 9,000 | 1,000 | `CohereLabs/aya_dataset` | Semitic Baseline |
| **`Fre-Latn`** | French (Latin script) | 9,000 | 1,000 | `CohereLabs/aya_dataset` | Romance Baseline |
| **`Ger-Latn`** | German (Latin script) | 9,000 | 1,000 | `CohereLabs/aya_dataset` | Germanic Baseline |
| **Total** | **11 Classes** | **99,000** | **11,000** | — | — |

---

## 📂 Synchronized Multi-Formats

- **`train_11lang_uniform.csv`**: Tabular CSV (`id`, `text`, `label`, `source`) [20.5 MB]
- **`train_11lang_uniform.txt`**: fastText supervised format (`__label__<lang> <text>`) [17.5 MB]
- **`train_11lang_uniform.jsonl`**: Standard JSON Lines [23.9 MB]
- **`val_11lang_uniform.csv`**: Validation CSV [2.28 MB]
- **`val_11lang_uniform.txt`**: Validation fastText [1.97 MB]
- **`val_11lang_uniform.jsonl`**: Validation JSON Lines [2.65 MB]
