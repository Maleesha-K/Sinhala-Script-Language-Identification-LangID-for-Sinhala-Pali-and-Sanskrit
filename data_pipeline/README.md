# Sinhala-script LangID pipeline

Reproducible pipeline for language identification of **Sinhala, Pali and
Sanskrit written in Sinhala script**, with retention of 8 other languages
(Sanskrit-Devanagari, English, Tamil, Hindi, Bengali, Modern Standard Arabic,
French, German). One command runs every stage, validates output manifests and
checks deterministic artifacts against the pinned reference hashes. A full run
and score comparison are still needed to verify the reported model results.

## Quick start

```bash
cp .env.example .env            # then put your Hugging Face token in HF_TOKEN
uv sync                         # install the locked environment
uv run python run_pipeline.py   # or: make all
```

With your Hugging Face account, accept the terms of these gated datasets first
(preflight tells you if you have not):
[FLORES+](https://huggingface.co/datasets/openlanguagedata/flores_plus),
[CommonLID](https://huggingface.co/datasets/commoncrawl/CommonLID),
[OpenLID-v2](https://huggingface.co/datasets/laurievb/OpenLID-v2).

The source CSVs needed to rebuild the published target split are included in
`source_data/target/`; their SHA-256 hashes and provenance are recorded there.
The externally supplied three-regime comparison sheet is kept in `reference/`.
It is a comparison reference, not a result regenerated or verified by this
checkout. No full model run is required to inspect or test the repository.

Useful options:

| command | what it does |
|---|---|
| `run_pipeline.py --preflight-only` (`make preflight`) | only check `.env`, token, dataset access, tools, GPU, disk |
| `run_pipeline.py --stages 01-04` | a range (stages run in numeric order) |
| `run_pipeline.py --only 03` | one stage |
| `run_pipeline.py --from 05` | resume from a stage |
| `run_pipeline.py --force` | re-run even if a stage is up to date |
| `run_pipeline.py --dry-run` | show what would run |
| `run_pipeline.py --smoke --stages 05-08` | plumbing check in minutes: tiny subsamples, one grid point; writes only under `smoke/` |
| `run_pipeline.py --only 07 --models nllb_lid218,conlid` | restrict model stages to some models |
| `run_pipeline.py --only 07 --models xlmr` | train the deferred XLM-R model (hours on a laptop GPU) |
| `uv run pytest` (`make test`) | unit tests, incl. invariants of the produced data |

### GPU (Linux and Windows)
PyTorch models (LID-176 leaf surgery, ConLID, XLM-R, Char-CNN/BiGRU) use CUDA when
available. `uv sync` installs a CUDA 13.0 build of PyTorch on both Linux (PyPI)
and Windows (PyTorch's cu130 index, configured in `pyproject.toml`); it needs an
NVIDIA driver with CUDA 13 support (>= 580). Preflight reports the device and
**fails** if an NVIDIA GPU is present but PyTorch cannot use it, with the fix.
On Windows, run `deactivate` first if another virtualenv is active, so `uv`
uses `data_pipeline/.venv`. fastText models and the sklearn/XGBoost baselines run on CPU.

## `.env`

| key | required | meaning |
|---|---|---|
| `HF_TOKEN` | yes | Hugging Face read token |
| `HF_ORG` | no (`script-langid`) | organisation holding this project's datasets/models |
| `HF_TARGET_DATASET` | no (`sinhala-script-lid`) | name of the target-language dataset repo |
| `HF_PUBLISH_PRIVATE` | no (`1`) | maintainers: new repos are created private |
| `HF_HOME` | no | Hugging Face cache location |
| `PIPELINE_DEVICE` | no (`auto`) | where PyTorch models run: `auto` (CUDA if usable), `cuda`, `cpu` |
| `SKIP_GPU_MODELS` | no (`0`) | `1` skips GPU-only models instead of failing preflight |

## What a run shows you

1. **Preflight**: one `OK`/`WARN`/`FAIL` line per check, each failure with its fix.
2. **Each stage**: the output of every script, including `[PASS]`/`[FAIL]` lines.
3. **After each stage**: outputs verified against their sha256 manifests, and a
   **reference check** against `config/reference_outputs.json` (`MATCH` = your
   files are byte-identical to the maintainers' run; `DIFF` stops the run).
4. **At the end**: a summary table (stage, status, time, reference check, report
   paths), printed and saved to `logs/<run>/summary.md`. Every stage's full output
   is in `logs/<run>/<stage>.log`; environment details in `logs/<run>/run_metadata.json`.

## Stages

| id | stage | outputs | human-readable report |
|---|---|---|---|
| 01 | download | `datasets/hybrid_benchmark/*/raw`, `datasets/target_language`, `datasets/hybrid_finetune/openlid_v2/raw` | `datasets/target_language/split_report.json` |
| 02 | preprocess | `datasets/hybrid_benchmark/*/{clean,eval}.jsonl` | `datasets/hybrid_benchmark/*/manifest.json` (`summary`) |
| 03 | prepare datasets | `datasets/hybrid_finetune/replay_mixed/`, `datasets/target_fragments/` | `replay_mixed/replay_report.json`, `target_fragments/fragments_report.json` |
| 04 | dataset checking | `datasets/audit/` | **`datasets/audit/audit_report.md`** |
| 05 | traditional baselines | `models/00_traditional_ml_baselines`, `datasets/benchmark_results/00_traditional_ml_baselines` | `tables/table0_baselines.md`, `tables/figure_baselines_short_text.png` (after 08) |
| 06 | zero-shot benchmark | `datasets/benchmark_results/01_zero_shot` | |
| 07 | fine-tuning | `models/02_target_only_sota`, `models/03_global_rehearsal_sota` (`selection_log.csv`, `chosen.json`, `best/`) | |
| 08 | evaluation + tables | `datasets/benchmark_results/{02_target_only,03_multilingual_rehearsal,tables}` | **`datasets/benchmark_results/tables/results.md`** |

### 01 Download
Every input is pinned in `config/locks.json` (Hugging Face revision or sha256):
FLORES+ devtest, CommonLID test, WiLI-2018 (Zenodo; **test split only**), the
target dataset, and OpenLID-v2 parquet files for the 8 replay labels. Raw files
are stored byte-for-byte; row counts are checked against the lock.

### 02 Preprocess (benchmarks)
Every text is **NFC-normalised** (`lidpipe/text.py`; zero-width characters other
than ZWJ/ZWNJ removed, whitespace collapsed). Labels are `<ISO 639-3>_<ISO 15924>`
(`config/labels.yaml`):
- FLORES+ uses its own script field, so romanised Arabic (`arb_Latn`) stays
  separate, and native `sin_Sinh` / `san_Deva` rows are kept.
- WiLI and CommonLID carry no script; it is derived per language and asserted
  for every scored language. WiLI `als` is mapped to `gsw` (Alemannic).
- **Arabic policy:** `arb_Arab` is ISO `arb` (Modern Standard Arabic) in Arabic
  script only. Macrolanguage `ara` and dialects are never mapped in, so WiLI has
  no `arb_Arab` (declared absent). LID-176's prediction `ar` is credited as `arb`
  (it cannot output anything finer); this is a documented limitation.
- Exact duplicates removed; texts carrying two labels are kept but excluded from
  scoring when both labels are scored; rows are **flagged** (`short`,
  `no_letters`, `wrong_script`), not dropped, so scores can be reported with and
  without them.
- `clean.jsonl` = the benchmark as published (every language), never mixed with our data.
- `eval.jsonl` = the **hybrid** 11-label set that is scored: the benchmark's own
  rows for the 8 replay labels, with its Sinhala-script rows (`sin_Sinh`, and
  `pli_Sinh`/`san_Sinh` if any) **replaced by the whole target test split**
  (`datasets/target_language/test`, the leakage-free successor of the old
  `test.csv`). Every row records `origin` (`benchmark` / `target_test`); the
  manifest `summary.hybrid` records how many benchmark rows were replaced. The
  target rows are identical in all three hybrids, so Sinhala/Pali/Sanskrit are
  scored on the same data everywhere and only the distractor languages differ.
  `absent_by_design` in `labels.yaml` describes the benchmark itself.

### 03 Prepare datasets (rehearsal)
OpenLID-v2 (Burchell et al., ACL 2023), the curated LID training set, gives the
8 replay labels. OpenLID sub-sources that are a benchmark's origin are excluded
wholesale (`replay.exclude_sources`: OpenLID contains WiLI-2018). Per label:
seeded random candidates, the same normalisation,
segmentation and filters as the target data, exact and MinHash near-duplicate
removal, **decontamination** against every benchmark eval set (exact and
near-duplicate) and the target data, then a balanced sample (10,000 train /
1,250 validation per label). `mixed_{train,validation}.jsonl` = target split +
replay split.

**Short-text stress-test fragments** (`prepare_fragments.py`, config
`fragments`): from every target test sentence, a contiguous run of k = 5, 3
and 1 words starting at a seeded random word (sentences with ≤ k words are kept
whole), as in the original phase-1 study. Words are whitespace tokens with at
least one letter, and each row's start is seeded by (seed, k, sample_id), so
fragments are reproducible and independent of file order. Output
`datasets/target_fragments/target_test_{5,3,1}w.jsonl` (same `sample_id` and
label as the source row).

### 04 Dataset checking
`check_datasets.py` prints a `[PASS]`/`[FAIL]` line per check and writes them all
to `datasets/audit/audit_report.md`. Any `FAIL` stops the pipeline. Checks:

- **benchmarks**: files match manifests (raw and processed); labels well-formed
  and in the allowed set; all text NFC; unique `sample_id`; no duplicate
  (text, label); benchmark-origin eval rows ⊂ clean; **hybrid**: none of the
  benchmark's own target-label rows remain, the target rows are exactly the
  target test split, built from the current test file, and share no text with
  benchmark rows; every scored label present except declared-absent replay
  labels, and declared absences really absent from the benchmark; no eval text
  with two scored labels; Arabic policy (`arb_Arab` only from raw `arb`); expected script per
  language; WiLI test split only; raw row counts equal the pins.
- **target release**: files match manifest and the pinned release; labels, NFC,
  unique ids; units ≤ 200 characters and in Sinhala script; all three labels in
  every split; no text and no document block shared between splits; **no
  near-duplicates across splits** (MinHash LSH, re-computed); provenance of the
  parallel corpus verified at build time.
- **replay / mixed**: manifests; labels, NFC, ids; balanced per label;
  `mixed = target + replay` exactly; replay train/validation share no text and
  no near-duplicate.
- **fragments**: manifest; labels, NFC, ids; one fragment per target test row
  with the same id and label; exactly k words (fewer only for shorter
  sentences); each a contiguous run of its source sentence's words; rebuilt
  identically from the config seed.
- **contamination**: no benchmark eval text and no target test text in any
  training or validation set (exact); no replay text near-duplicating a
  benchmark eval text (re-computed); target test disjoint from every
  benchmark's own rows.

### Evaluation (stages 05, 06, 08): one evaluator, one scorer
Every model is scored by `lidpipe/evaluate.py` on the same four sets: the target
test split alone, and the hybrid 11-label eval sets of FLORES+, WiLI-2018 and
CommonLID (benchmark replay-label rows + the target test split).
- Predictions are unrestricted and mapped by `canonical_prediction`
  (`lidpipe/labels.py`); a script-less output (`sa`) takes the input's script.
- One-vs-rest F1 per label; labels absent from a set are NaN and excluded from
  macro averages (never counted as 0); `macro_target3` (target test),
  `macro_all` (hybrid benchmarks, with their `macro_target3`/`macro_replay8`
  split in the table CSVs); 1000-sample bootstrap 95% CIs; scores reported on
  all rows and on unflagged rows.
- Per set: `predictions.csv`, `per_label.csv`, `confusion.csv`, `summary.json`.
- `make_tables.py` builds every table **only from `predictions.csv`**, after
  checking that all models were scored on identical samples and that each
  macro-F1 recomputes exactly.

### 05 Baselines and 07 fine-tuning: one protocol
`lidpipe/training.py` (config `training`, `baselines`): for each value of a
3-point grid, start from the pinned checkpoint (or from scratch for baselines),
train up to 3 epochs, score validation after each epoch, keep the best
(lr, epoch). Target-only: train on target train, select on target validation
`macro_target3`. Rehearsal: train on mixed train, select on mixed validation
`macro_all`. Test sets are never used for selection.

| model | method |
|---|---|
| NLLB-218, GlotLID v3, OpenLID v3 | native fastText continued training of all weights; missing labels appended with zero rows; each model trained on its own label for a language (OpenLID v3 `ara_Arab`) |
| fastText LID-176 | `fasttext_continual`: parity-verified import, Pali leaf added under Sinhala, all weights trained (SGD) |
| ConLID | cross-entropy over the full output space, sparse SGD (`lidlab`) |
| XLM-R LangID (`papluca/xlm-roberta-base-language-detection`) | pretrained 20-language LID head extended with the missing labels (original rows kept, new rows zero); LoRA (r=16) on attention + head, AdamW; **training deferred** (`training.deferred_models`), zero-shot runs in stage 06 |
| baselines | NB, linear SVM, char n-gram LogReg (OvR), XGBoost (CPU), fastText from scratch, Char-CNN, Char-BiGRU |

**Baselines (stage 05)** are trained from scratch on the target train split only
(`baselines.phases: [target_only]`) and selected on target validation. They are
not scored on the 11-language benchmarks (they only know the 3 target labels);
instead they get the **short-text stress test**: macro-F1 over `sin_Sinh`,
`pli_Sinh`, `san_Sinh` on the target test split as full sentences and as 5-, 3-
and 1-word fragments. Stage 08 turns this into `tables/table0_baselines.*` and
`tables/figure_baselines_short_text.{png,pdf}` (macro-F1 vs input length, one
line per baseline, the three best at one word highlighted).

Arabic: LID-176 (`ar`) and OpenLID v3 (`ara_Arab`) only have the macrolanguage
label; it is credited as `arb_Arab` (documented limitation).

## Target dataset (Sinhala / Pali / Sanskrit in Sinhala script)

Built once by maintainers (`scripts/maintainer/resplit_target.py`) and published
to `$HF_ORG/$HF_TARGET_DATASET`. Method (parameters in `config/pipeline.yaml`,
`target_split`):

1. Sources pooled, NFC-normalised, non-Sinhala-script text removed.
2. **Provenance**: the Pali-Sinhala parallel rows are verified row-by-row against
   the public corpus `sinhala-nlp/pali-sinhala` (pinned).
3. **Documents**: source document ids; for the parallel corpus (canonical order)
   a sutta starts at each Pali incipit *evaṃ me sutaṃ*; both sides of a
   translation pair share a document.
4. **Split unit**: contiguous block of ≤ 25 rows within a document.
5. **Sentence-level units** (as in FLORES+/OpenLID), packed to ≤ 200 characters,
   which removes the length cue between sources.
6. Exact duplicates and label conflicts removed; **near-duplicates** removed with
   MinHash LSH over character 5-grams, Jaccard ≥ 0.8 (Broder 1997; Lee et al. 2022).
7. Group-stratified 80/10/10 split (seed 42).
8. Verified: 0 exact and 0 near-duplicate pairs across splits.

## Maintainers

```bash
# rebuild the target release (prints PASS/FAIL for provenance and leakage,
# and whether it reproduces the release pinned in config/locks.json)
uv run python scripts/maintainer/resplit_target.py [--input-dir source_data/target] [--update-lock]

# publish it to $HF_ORG/$HF_TARGET_DATASET and pin the revision in locks.json
# (needs a token with write access to the organisation)
uv run python scripts/maintainer/publish_target_hf.py

# after a clean run, store its output hashes as the reference researchers compare to
uv run python run_pipeline.py --record-reference
```

## Layout

```text
data_pipeline/
├── run_pipeline.py      # single entry point
├── config/              # pipeline.yaml, labels.yaml, locks.json, reference_outputs.json
├── lidpipe/             # shared library: text, labels, metrics, dedup, manifests, preflight, stages
├── scripts/             # 01..08 stage scripts, maintainer/, legacy/ (old notebooks, not run)
├── tests/               # unit tests and data invariants
├── datasets/            # produced data (gitignored)
└── logs/                # per-run logs and summary.md (gitignored)
```
