# Target Language Training Split (N=60,285)

Trained strictly on the three target languages in Sinhala script.

## Class Distribution:
- **Sinhala (`sin_Sinh` / `sinhala`)**: 26,675 samples (44.25%)
- **Pali (`pli_Sinh` / `pali`)**: 23,490 samples (38.96%)
- **Sanskrit (`san_Sinh` / `sanskrit`)**: 10,120 samples (16.79%)
- **Total**: 60,285 samples

## Files:
- `train.csv`: Tabular CSV format (`text`, `label`)
- `train.txt`: fastText supervised training format (`__label__<lang> <text>`)
- `train.jsonl`: Standardized JSON Lines format
