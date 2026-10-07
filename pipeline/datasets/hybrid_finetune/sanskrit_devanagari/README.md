# Sanskrit Devanagari Corpus (`san_Deva`)

Source: `surajp/sanskrit_classic` (Hugging Face)

---

## 🎯 Motivation

In standard multilingual models, Sanskrit vocabulary is strongly associated with the Devanagari script (`san_Deva`). When evaluating or fine-tuning models on Sinhala-script Sanskrit (`san_Sinh`), models frequently confuse lexical affinity with orthographic script features.

By incorporating a dedicated `san_Deva` corpus into our experiments:
1. We teach models to distinguish Sanskrit in Sinhala script (`san_Sinh`) from classical Sanskrit in Devanagari script (`san_Deva`).
2. We evaluate whether cross-script transfer occurs for Sanskrit.

---

## 📂 Available Formats

- **`sanskrit_devanagari.csv`**: Tabular format (`id`, `text`, `label`, `source`) with 342,031 rows [53.3 MB].
- **`sanskrit_devanagari.txt`**: fastText supervised format (`__label__san_Deva <text>`) [43.3 MB].
- **`sanskrit_devanagari.jsonl`**: Standard JSON Lines format [68.3 MB].
- **`combined.txt`**: Raw cleaned sentence lines [1.4 MB].
