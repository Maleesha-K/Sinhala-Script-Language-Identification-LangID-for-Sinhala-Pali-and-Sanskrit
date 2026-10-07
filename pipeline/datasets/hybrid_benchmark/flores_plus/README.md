# FLORES+ Evaluation Benchmark

The **FLORES+** evaluation dataset contains high-quality human-translated evaluation sentences across 208 languages and scripts.

---

## 📊 Dataset Statistics

- **Total Records**: 229,687
- **Number of Languages**: 208
- **File Format**: Standardized JSON Lines (`flores_plus.jsonl`, ~61.9 MB)

### Target & Key Background Language Breakdown:
| ISO / Label | Language Name | Script | Sample Count |
| :--- | :--- | :--- | :--- |
| `pali` | Pali | Sinhala | 3,027 |
| `sinhala` | Sinhala | Sinhala | 2,693 |
| `sanskrit` | Sanskrit | Sinhala | 1,327 |
| `san_Deva` | Sanskrit | Devanagari | 1,012 |
| `eng` | English | Latin | 1,012 |
| `tam` | Tamil | Tamil | 1,012 |
| `hin` | Hindi | Devanagari | 1,012 |
| `ben` | Bengali | Bengali | 1,012 |
| `arb` | Standard Arabic | Arabic | 2,024 |
| `fra` | French | Latin | 1,012 |
| `deu` | German | Latin | 1,012 |

---

## 📄 JSON Schema

Each row in `flores_plus.jsonl` follows:
```json
{
  "text": "දඹුලු රජමහා විහාරය ශ්‍රී ලංකාවේ පිහිටි ප්‍රසිද්ධ ලෙන් විහාරයකි.",
  "label": "sinhala",
  "iso": "sin_Sinh",
  "source": "flores_plus"
}
```

---

## 🐍 Python Loading Example

```python
import json

with open("pipeline/datasets/hybrid_benchmark/flores_plus/flores_plus.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        record = json.loads(line)
        # Process record
        break
```
