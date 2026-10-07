# Target Language Held-Out Test Split (N=7,047)

Held-out benchmark evaluation split from the Nadil corpus. Used for Table 1, Table 2, and Table 3 reporting.

## Class Distribution:
- **Pali (`pli_Sinh` / `pali`)**: 3,027 samples (42.95%)
- **Sinhala (`sin_Sinh` / `sinhala`)**: 2,693 samples (38.22%)
- **Sanskrit (`san_Sinh` / `sanskrit`)**: 1,327 samples (18.83%)
- **Total**: 7,047 samples

## Files:
- `test.csv`: Tabular CSV format (`text`, `label`)
- `test.txt`: fastText supervised test format (`__label__<lang> <text>`)
- `test.jsonl`: Standardized JSON Lines format
- `fasttext_eval_data.json`: Pre-tokenized evaluation records for fastText benchmarks
