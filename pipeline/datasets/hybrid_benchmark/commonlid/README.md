# CommonLID Evaluation Benchmark

The **CommonLID** benchmark evaluates real-world, noisy web extracts across 112 languages.

---

## 📊 Dataset Statistics

- **Total Records**: 380,277
- **Number of Languages**: 112
- **Files**:
  - `commonlid.jsonl.gz`: Compressed for Git and fast downloads (~37.8 MB).
  - `commonlid.jsonl`: Uncompressed (~134.6 MB, automatically ignored by `.gitignore` to prevent GitHub 100MB limit errors).

### Key Language Counts:
- `pali`: 3,027 samples
- `sinhala`: 2,693 samples
- `sanskrit`: 1,327 samples
- `eng`: 27,461 samples
- `arb`: 26,152 samples
- `hin`: 3,666 samples
- `fra`: 3,233 samples

---

## 🐍 Loading directly from compressed `.gz`

```python
import gzip
import json

with gzip.open("pipeline/datasets/hybrid_benchmark/commonlid/commonlid.jsonl.gz", "rt", encoding="utf-8") as f:
    for line in f:
        record = json.loads(line)
        # record['text'], record['label']
        break
```
