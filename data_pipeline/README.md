# Sinhala-script LangID pipeline

Reproducible pipeline for language identification of **Sinhala, Pali and
Sanskrit written in Sinhala script**, with retention of 8 other languages
(Sanskrit-Devanagari, English, Tamil, Hindi, Bengali, Modern Standard Arabic,
French, German). One command runs every stage, validates every output and tells
you whether you reproduced the published data byte-for-byte.

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

Useful options:

| command | what it does |
|---|---|
| `run_pipeline.py --preflight-only` (`make preflight`) | only check `.env`, token, dataset access, tools, GPU, disk |
| `run_pipeline.py --stages 01-04` | a range (stages run in numeric order) |
| `run_pipeline.py --only 03` | one stage |
| `run_pipeline.py --from 05` | resume from a stage |
| `run_pipeline.py --force` | re-run even if a stage is up to date |
| `run_pipeline.py --dry-run` | show what would run |
| `uv run pytest` (`make test`) | unit tests, incl. invariants of the produced data |

## `.env`

| key | required | meaning |
|---|---|---|
| `HF_TOKEN` | yes | Hugging Face read token |
| `HF_ORG` | no (`script-langid`) | organisation holding this project's datasets/models |
| `HF_TARGET_DATASET` | no (`sinhala-script-lid`) | name of the target-language dataset repo |
| `HF_PUBLISH_PRIVATE` | no (`1`) | maintainers: new repos are created private |
| `HF_HOME` | no | Hugging Face cache location |
| `PIPELINE_DEVICE` | no (`auto`) | `auto`, `cpu` or `cuda` |
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
| 03 | prepare datasets | `datasets/hybrid_finetune/replay_mixed/` | `replay_mixed/replay_report.json` |
| 04 | dataset checking | `datasets/audit/` | **`datasets/audit/audit_report.md`** |
| 05-08 | baselines, zero-shot, training, evaluation | not implemented yet | |

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
- `eval.jsonl` = the 11 scored labels. Benchmarks never contain target test data.

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

### 04 Dataset checking
`check_datasets.py` prints a `[PASS]`/`[FAIL]` line per check and writes them all
to `datasets/audit/audit_report.md`. Any `FAIL` stops the pipeline. Checks:

- **benchmarks**: files match manifests (raw and processed); labels well-formed
  and in the allowed set; all text NFC; unique `sample_id`; no duplicate
  (text, label); eval ⊂ clean; every scored label present except declared
  absences, and declared absences really absent; no eval text with two scored
  labels; Arabic policy (`arb_Arab` only from raw `arb`); expected script per
  language; WiLI test split only; raw row counts equal the pins.
- **target release**: files match manifest and the pinned release; labels, NFC,
  unique ids; units ≤ 200 characters and in Sinhala script; all three labels in
  every split; no text and no document block shared between splits; **no
  near-duplicates across splits** (MinHash LSH, re-computed); provenance of the
  parallel corpus verified at build time.
- **replay / mixed**: manifests; labels, NFC, ids; balanced per label;
  `mixed = target + replay` exactly; replay train/validation share no text and
  no near-duplicate.
- **contamination**: no benchmark eval text and no target test text in any
  training or validation set (exact); no replay text near-duplicating a
  benchmark eval text (re-computed); target test disjoint from benchmarks.

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
uv run python scripts/maintainer/resplit_target.py [--update-lock]

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
├── scripts/             # 01.download 02.preprocess 03.prepare_datasets 04.dataset_checking maintainer
├── tests/               # unit tests and data invariants
├── datasets/            # produced data (gitignored)
└── logs/                # per-run logs and summary.md (gitignored)
```
