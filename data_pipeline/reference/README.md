# Externally supplied result reference

`latest_three_regime_results.csv` is the team's latest comparison sheet, copied
from `Spider-plots:Comparison Tables - New Method (2).csv` (Git blob
`792d27b33aa15845c61b66118e0759a400846b6b`). Only line endings were
normalized while copying it into this branch; the CSV cell values are unchanged.

It contains zero-shot, target-only fine-tuning, and all-language rehearsal
results for the three benchmarks. Empty scores represent unavailable or
unsupported evaluations, not measured zero. WiLI-2018 has no Arabic class.

These results were supplied from a separate full run. The current checkout has
not re-downloaded the large models or repeated that run. The eight-stage
pipeline writes its own results under `datasets/benchmark_results/tables/`
when a researcher runs it; compare those outputs with this reference after a
full run rather than treating this file as generated pipeline output.
