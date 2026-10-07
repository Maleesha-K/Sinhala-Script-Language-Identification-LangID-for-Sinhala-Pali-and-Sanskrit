# Hybrid Multilingual Benchmarks

This directory contains standard global benchmarks used to measure **out-of-domain robustness** and detect **catastrophic forgetting** when foundation models are adapted to Sinhala-script low-resource languages.

---

## 📚 Included Benchmarks

| Benchmark | Source Domain | Languages | Total Rows | File Size | Primary Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **FLORES+** | Professional multi-way parallel translations | 208 | 229,687 | 61.9 MB (`.jsonl`) | Clean, high-quality parallel evaluation across 208 languages |
| **WiLI-2018** | Wikipedia paragraphs | 237 | 241,047 | 60.8 MB (`.jsonl.gz`) | Academic standard for paragraph-length language identification |
| **CommonLID** | Diverse web crawl extracts | 112 | 380,277 | 37.8 MB (`.jsonl.gz`) | Noisy, real-world web text evaluation |

---

## 🎯 Target Languages within Benchmarks

Each benchmark contains instances of our target and related Indo-Aryan languages:
- **Sinhala** (`sinhala` / `sin_Sinh`)
- **Pali** (`pali` / `pli_Sinh`)
- **Sanskrit in Sinhala script** (`sanskrit` / `san_Sinh`)
- **Sanskrit in Devanagari script** (`san_Deva`)
- **Global background rehearsal set**: English (`eng`), Tamil (`tam`), Hindi (`hin`), Bengali (`ben`), Arabic (`arb`), French (`fra`), German (`deu`).

---

## 💾 Storage & GitHub Notes

To ensure smooth cloning without exceeding GitHub's 100 MB per-file limit:
- `flores_plus.jsonl` is committed uncompressed (~61.9 MB).
- `wili-2018.jsonl.gz` (~60.8 MB) and `commonlid.jsonl.gz` (~37.8 MB) are tracked in compressed format.
- Uncompressed `.jsonl` files for WiLI and CommonLID (>130 MB each) are automatically ignored by `.gitignore`.

### Reading Gzipped JSONL in Python:
```python
import gzip
import json

def read_jsonl_gz(filepath):
    with gzip.open(filepath, "rt", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)

# Example:
for record in read_jsonl_gz("pipeline/datasets/hybrid_benchmark/wili_2018/wili-2018.jsonl.gz"):
    # process record
    break
```
