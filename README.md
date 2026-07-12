# Sinhala-Script Language Identification (Sinhala / Pali / Sanskrit)

Language identification for three languages that all share the **Sinhala script**.
Because the script is the same across all three, they can only be told apart by
vocabulary, morphology and spelling habits — not by the characters used.

This README explains how to go from a fresh clone to a built `data/processed/`
folder containing `master.csv`.

---

## What we are building

The pipeline merges three raw corpora into one dataset with a common schema:

| Source | Language(s) | What a row is |
|---|---|---|
| **SiPaKosa** | sinhala, pali, mixed | one sentence |
| **SansinNT** | sanskrit | one Bible verse |
| **SiDiaC** | sinhala (historical) | one sentence from an OCR'd book |

Final output: **`data/processed/master.csv`** with these columns:

`id`, `text`, `label`, `source`, `subcorpus`, `group_id`, `is_core`, `split`

- `label` — `sinhala` | `pali` | `sanskrit` | `mixed`
- `is_core` — `True` for the three real languages; `False` for `mixed`
  (`mixed` is code-switching, not a language — filter it out for the 3-way task)
- `group_id` — the document a row came from; used so no document is split across
  train/val/test
- `split` — `train` | `val` | `test` (80/10/10)

---

## Step 0 — Prerequisites

- Python 3.11
- Git

---

## Step 1 — Clone and install

```bash
git clone <repo-url>
cd "LangID - DSE project"

python -m venv venv

# Windows (PowerShell)
venv\Scripts\Activate.ps1
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

---

## Step 2 — Get the raw data  ⚠️ READ THIS

**`data/raw/` is in `.gitignore`, so cloning the repo gives you NO data.**
You must put the raw data in place yourself. This is the step people get stuck on.

### 2a. SiPaKosa — automatic ✅

Downloads from Hugging Face:

```bash
python scripts/data_loading.py
```

Creates:
```
data/raw/SiPaKosa/sipakosa_sinhala_metadata.csv   (372,431 rows)
data/raw/SiPaKosa/sipakosa_mixed_metadata.csv     (256,644 rows)
```

### 2b. SansinNT and SiDiaC — manual ❗

There is **no download script** for these two. Get them from whoever has the
copies (ask in the group), then place them so the folders look **exactly** like
this — the loaders find files by these paths:

```
data/raw/
├── SiPaKosa/
│   ├── sipakosa_sinhala_metadata.csv
│   └── sipakosa_mixed_metadata.csv
│
├── SansinNT/
│   └── sansin_usfx.xml              <- the only file the loader reads
│
└── SiDiaC/
    └── OCR_Final/                   <- 185 folders, ONE PER BOOK
        ├── <Book Name>/
        │   ├── <Book Name>.txt
        │   └── metadata.json
        ├── <Book Name>/
        │   ├── <Book Name>.txt
        │   └── metadata.json
        └── ...
```

Notes:
- `SiDiaC/OCR_Final/` is **not** flat text files — it is one **folder** per book,
  each containing a `.txt` and a `metadata.json`. If yours is flat, you have the
  wrong copy.
- `SiDiaC/Books_PDF/` (the source PDFs) is **not needed** — the pipeline ignores it.
- Other files in `SansinNT/` (`BookNames.xml`, `sansinmetadata.xml`) are not read
  by the pipeline. Harmless to keep.

---

## Step 3 — Build `data/processed/`

Run the three loaders, then the merge. **Order matters** — `build_master.py`
reads the three CSVs the loaders produce.

```bash
python scripts/loaders/sipakosa_to_common.py
python scripts/loaders/sansin_to_common.py
python scripts/loaders/sidiac_to_common.py

python scripts/build_master.py
```

> **Windows users:** if the Sinhala text prints as `?????` or you get a
> `UnicodeEncodeError`, your console is not UTF-8. Fix it for the session:
> ```powershell
> $env:PYTHONIOENCODING = "utf-8"
> ```
> This only affects what's *printed* — the CSV files are always written as UTF-8.

Result:

```
data/processed/
├── sipakosa_common.csv
├── sansin_common.csv
├── sidiac_common.csv
└── master.csv          <- the one you train on
```

The whole thing takes a couple of minutes, mostly SiPaKosa.

---

## Step 4 — Check you got the same thing

`build_master.py` prints a report. Compare against these expected numbers —
if yours differ, something went wrong in Step 2.

**Total rows: 393,752** (SiPaKosa 372,200 · SiDiaC 13,599 · SansinNT 7,953)

| label | train | val | test | TOTAL |
|---|---|---|---|---|
| sinhala | 169,572 | 21,046 | 21,119 | **211,737** |
| pali | 53,558 | 6,695 | 6,695 | **66,948** |
| sanskrit | 6,296 | 772 | 885 | **7,953** |
| mixed | 85,691 | 10,711 | 10,712 | **107,114** |

The report must end with:

```
LEAKAGE CHECK
  PASS: all 372,645 group_ids appear in exactly one split.
```

If that says **FAIL**, do not use the data — a document is leaking across splits
and any test score you get will be inflated.

The splits use a **fixed seed (42)**, so everyone who follows these steps gets
byte-identical files. If your numbers differ, we can compare.

---

## Things you need to know before training

**1. Sanskrit is tiny.** The core 3-way balance is:

| | rows | share of core |
|---|---|---|
| sinhala | 211,737 | 73.9% |
| pali | 66,948 | 23.4% |
| **sanskrit** | **7,953** | **2.8%** |

Sinhala has **26.6× more rows** than Sanskrit. `master.csv` is deliberately left
**un-rebalanced** — handle this with class weights or resampling *at training
time*, not by editing the dataset.

**2. Filter out `mixed` for the 3-way task.**

```python
import pandas as pd

df = pd.read_csv("data/processed/master.csv", encoding="utf-8")

core = df[df.is_core]                    # the 3-way task
train = core[core.split == "train"]
test  = core[core.split == "test"]

mixed = df[~df.is_core]                  # code-mixing analysis only
```

**3. Don't make your own random split.** Use the `split` column. It is *grouped*:
a SansinNT chapter or a SiDiaC book lands entirely in one split. A naive
`train_test_split` on rows would put near-identical verses from the same chapter
in both train and test and give you a falsely high score.

**4. Known issue — duplicate text under different labels.** Deduplication removes
rows with the same `text` *and* the same `label`. If the same sentence appears
under two *different* labels, **both rows survive** — that's contradictory
training signal. This has not been resolved yet. Worth investigating.

---

## Repo layout

```
scripts/
├── data_loading.py            # downloads SiPaKosa from Hugging Face
├── loaders/
│   ├── common.py              # shared schema + text cleaning
│   ├── sipakosa_to_common.py
│   ├── sansin_to_common.py
│   └── sidiac_to_common.py
└── build_master.py            # merge + dedupe + grouped split + report

data/
├── raw/                       # gitignored — you provide this (Step 2)
└── processed/                 # gitignored — you build this (Step 3)
```

**Never edit anything in `data/raw/`.** The loaders only read from it. Everything
is reproducible from raw → processed, so if `data/processed/` gets messy, just
delete it and re-run Step 3.
