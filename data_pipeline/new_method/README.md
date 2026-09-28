# Sinhala-script LangID: continued training and rehearsal

This package runs the three requested experiments for **NLLB LID-218 (lid218e), GlotLID v3, and ConLID**. It updates pretrained weights and keeps the full original set of output labels. It does not replace a model with an 11-class classifier.

**The ZIP does not copy your research data or pretrained model weights. Put the supplied files in `data/` before running.** The notebooks download the official checkpoints. No F1 values are invented; the notebooks calculate them from your data.

## What the three tables mean

| Table | Model weights | Additional training data |
|---|---|---|
| 1: Zero-shot | Original released checkpoint | None |
| 2: Target-only fine-tuning | Original weights, with missing target labels appended | Your `train.csv` only |
| 3: Rehearsal fine-tuning | Same expanded initialization as Table 2 | Your `train.csv` plus training examples from eight older languages |

Every table evaluates the same eleven language-script categories separately on **CommonLID, FLORES+, and WiLI-2018**. Predictions may be any language the model supports. Predictions outside the eleven are counted as errors; they are never forced into the eleven categories.

Table 2 measures forgetting. Do not call a score drop catastrophic before seeing its size and consistency. Table 3 measures whether rehearsal helps. Eight languages provide evidence only for those eight. They do not prove that all original languages were retained.

## Run order

1. Extract this ZIP. Keep the folder structure.
2. Open `notebooks/00_Setup_and_Data.ipynb` in Jupyter, VS Code, or Colab. It installs packages and builds the native continuation program.
3. Add your data, check the column settings in `config.json`, and run the data audit.
4. Run `01_NLLB.ipynb`, `02_GlotLID.ipynb`, and `03_ConLID.ipynb`, one at a time.
5. Run `04_Three_Results_Tables.ipynb`. The final CSV and LaTeX tables appear in `results/main_seed42/tables/`.
6. `05_Load_Trained_Models.ipynb` shows how to use the saved models.

For local use, Python 3.10-3.12 on Linux/WSL2 is the intended setup. Install a C++ compiler (`sudo apt-get install -y g++` on Ubuntu). Windows users can use WSL2 or Colab. From the extracted folder:

```bash
python -m pip install -r requirements.txt
python scripts/build_native.py
python scripts/run_model.py nllb
python scripts/run_model.py glotlid
python scripts/run_model.py conlid
```

For Colab, upload this ZIP through the Files pane, extract it to `/content`, then upload/open one of the included notebooks. The notebook locates `/content/lid_finetuning_bundle` automatically. Put the CSV, JSONL, and JSON files under that folder's `data/` directory. Colab files disappear when a runtime is reset: download your results and checkpoints or copy them to your own persistent drive.

The checkpoints are large. Allow about **20 GB of free disk space** for all downloads and saved models, and preferably **12-16 GB RAM**. These are planning estimates, not measured requirements for your dataset. FastText training is CPU-based. ConLID can use CPU or CUDA. Set `device` to `cpu` if your GPU runs out of memory; reducing `conlid_batch_size` also helps. A GPU is not required.

## Files you must provide

| File | Contents | Purpose |
|---|---|---|
| `data/train.csv` | Three target categories | Target training |
| `data/val.csv` | Separate target documents | Validation |
| `data/test.csv` | Three target categories | Additional target-only reporting |
| `data/train_mixed_11groups.jsonl` | Targets plus eight older categories | Rehearsal training; use directly |
| `data/val_mixed_11groups.jsonl` | All eleven categories | Rehearsal validation |
| `data/dataset_11groups_report.json` | Dataset construction/audit report | Provenance only; not model input |
| `data/preprocessed/commonlid.jsonl` | CommonLID benchmark | Evaluation |
| `data/preprocessed/flores_plus.jsonl` | FLORES+ benchmark | Evaluation |
| `data/preprocessed/wili-2018.jsonl` | WiLI-2018 benchmark | Evaluation |

The supplied files use `text`, `label`, `group`, and `group_id`; `config.json` is already set for them. See `data/README.md`. The supplied target splits share one `group_id` across train, validation, and test, so strict group-disjoint enforcement is disabled in the default configuration. Exact-text overlap is still rejected. Report this limitation, or rebuild those splits by group and then set `require_document_ids` to `true`.

`train_mixed_11groups.jsonl` already contains the three target categories and the eight older categories. Do not concatenate `train.csv` with it again, because that would duplicate target training examples. The same rule applies to the mixed validation file.

Never use FLORES/FLORES+ devtest, UDHR evaluation text, or your current test rows as rehearsal training data. Keep Sanskrit-Devanagari separate from Sanskrit-Sinhala. Arabic is configured as Modern Standard Arabic (`arb_Arab`); `ara_Arab` is explicitly mapped to this evaluation category, but Arabic dialect labels are not merged.

## Your existing zero-shot results

Use the **same released checkpoint** as your earlier experiment. Set each model's `local_path` or exact Hub `revision` if necessary. Download revisions are locked in `models_lock.json`; checkpoint hashes and installed versions are saved.

The default recomputes zero-shot results on all three benchmark files with the same label policy, preprocessing, and unrestricted prediction rule. Compatible per-example predictions can be configured separately for each benchmark. Aggregate F1 values alone cannot prove protocol equivalence.

## Two possible interpretations of “fine-tune again”

The default `replay_start: "base"` gives a controlled comparison: both arms start from the same expanded pretrained checkpoint. Only the training mixture differs.

If your supervisor intends **recovery after forgetting**, set `replay_start` to `"target_only"` before starting and use a new `output_dir`. Then the third stage continues the target-only checkpoint with mixed data. Report this as sequential recovery. It has an additional training stage, so improvement is not a compute-matched estimate of rehearsal alone.

## Training and measurement choices

- All original embedding rows and classifier rows are loaded. Missing `pli_Sinh` or `san_Sinh` rows are appended; any existing rows are reused.
- Default budget per arm is `target_passes * len(train.csv)` presented examples. Both arms therefore have the same example budget. The mixed pool is shuffled and cycled without replacement within each pass. A guard requires the budget to cover its entire pool at least once. The replay arm sees fewer target examples within this matched budget. Actual budgets and mixture sizes are logged.
- Default learning rate is 0.05 and `target_passes` is 3. These are starting settings, not tuned recommendations. Use validation data to select settings and then freeze them before the final test run. Use fresh output directories for changed settings.
- ConLID uses supervised cross-entropy adaptation. Its pretrained weights come from the contrastive-learning model, but this code does **not** reproduce the original contrastive pretraining objective.
- The native fastText backend uses the original feature extraction, hashes, and softmax updates. It supports the dense softmax checkpoints used here. It refuses incompatible/quantized/hierarchical-softmax models instead of changing their architecture.
- Native training is single-threaded for repeatability. ConLID GPU runs may have small numerical variation. For the paper, run multiple seeds (e.g. 42, 43, 44) and report mean and standard deviation separately.
- F1 is one-vs-rest for each language. The macro averages give each evaluated category equal weight. Each benchmark is reported separately.

There is an extra `initialized/` diagnostic evaluation after label expansion but before any updates. New classes can change decisions even before fine-tuning. Use this diagnostic to distinguish effects of label expansion from weight-update forgetting; it is not one of the three requested main tables.

## Outputs

Each model has `zero_shot/`, `initialized/`, `target_only/`, and `replay/` folders. Benchmark results are stored below `benchmarks/commonlid/`, `benchmarks/flores_plus/`, and `benchmarks/wili_2018/`. Trained folders also contain model weights. Validation and supplemental target-test results are separate.

The table notebook produces:

- `table_1_zero_shot.csv` / `.tex`
- `table_2_target_only.csv` / `.tex`
- `table_3_replay.csv` / `.tex`
- Forgetting, recovery, and residual-change CSVs.

Positive `zero-shot F1 - target-only F1` means a drop. Positive `replay F1 - target-only F1` means improvement. Do not clamp negative values away.

Completed, unchanged runs can be rerun safely. A changed data file, checkpoint, or configuration requires a new output directory. Interrupted phases restart from their intended starting checkpoint; they do not resume an optimizer mid-run. Run one notebook at a time.

Read `METHOD_AND_CITATIONS.md` for the research justification, and use `references.bib` in Overleaf. Read `VALIDATION.md` for exactly what was tested. Pretrained weights have their own upstream terms; the ZIP does not redistribute them.
