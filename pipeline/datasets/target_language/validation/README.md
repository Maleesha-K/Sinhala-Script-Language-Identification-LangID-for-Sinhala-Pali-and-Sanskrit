# Target Language Validation Split (N=6,986)

Used for hyperparameter tuning and model checkpoint validation.

## Class Distribution:
- **Sinhala (`sin_Sinh` / `sinhala`)**: 2,895 samples (41.44%)
- **Pali (`pli_Sinh` / `pali`)**: 2,800 samples (40.08%)
- **Sanskrit (`san_Sinh` / `sanskrit`)**: 1,291 samples (18.48%)
- **Total**: 6,986 samples

## Files:
- `val.csv`: Tabular CSV format (`text`, `label`)
- `valid.txt`: fastText supervised validation format (`__label__<lang> <text>`)
- `val.jsonl`: Standardized JSON Lines format
