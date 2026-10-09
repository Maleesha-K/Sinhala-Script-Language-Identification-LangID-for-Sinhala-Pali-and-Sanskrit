# Target-corpus source files

These are the three original CSV inputs previously kept in `data/Nadil/`.
`scripts/maintainer/resplit_target.py` uses them to rebuild the published
Sinhala/Pali/Sanskrit target release. Their contents were moved without changes.

| File | SHA-256 |
| --- | --- |
| `train.csv` | `1bb41eb038c0d069a5cd8a765e1a9cf69e4e50036b24ffb9aed644d1884f7ce8` |
| `val.csv` | `982c99c8729dad658ad12f44903976d15820a83b998fecdff6e00af429b2ceb3` |
| `test.csv` | `c91fb4dfa27e2e78be70e1b16ce040c26e6d0c040b8a5c6b47a8e82f74867315` |

Do not use these legacy splits directly as the benchmark test data. Rebuild the
leakage-checked target release with the maintainer script or use the pinned
published release downloaded by stage 01.
