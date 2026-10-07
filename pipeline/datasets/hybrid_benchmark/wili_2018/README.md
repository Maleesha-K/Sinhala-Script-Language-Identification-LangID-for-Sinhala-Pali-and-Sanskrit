# WiLI-2018 Evaluation Benchmark

The **WiLI-2018** (Wikipedia Language Identification) benchmark contains paragraph-length text extracts from Wikipedia across 237 languages.

---

## 📊 Dataset Statistics

- **Total Records**: 241,047
- **Number of Languages**: 237
- **Files**:
  - `wili-2018.jsonl.gz`: Compressed for Git and fast downloads (~60.8 MB).
  - `wili-2018.jsonl`: Uncompressed (~142.4 MB, automatically ignored by `.gitignore` to prevent GitHub 100MB limit errors).

### Key Language Counts:
- `pali`: 3,027 samples
- `sinhala`: 2,693 samples
- `sanskrit`: 1,327 samples
- Background languages (`eng`, `tam`, `hin`, `ben`, `fra`, `deu`): 1,000 samples each.

---

## 🐍 Loading directly from compressed `.gz`

```python
import gzip
import json

with gzip.open("pipeline/datasets/hybrid_benchmark/wili_2018/wili-2018.jsonl.gz", "rt", encoding="utf-8") as f:
    for line in f:
        record = json.loads(line)
        # record['text'], record['label']
        break
```
