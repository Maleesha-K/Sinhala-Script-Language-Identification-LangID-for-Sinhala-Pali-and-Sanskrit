# Fine-Tuning Method: NLLB (lid218e), GlotLID v3, and ConLID

A complete description of what the `new_method` pipeline does, end to end, at the level of detail needed to reproduce or defend it.

All numbers below are read from the committed run in `results/main_seed42/` (seed 42).

---

## 1. The question the experiment asks

Three Sinhala-script categories — Sinhala (`sin_Sinh`), Pali (`pli_Sinh`), and Sanskrit-in-Sinhala-script (`san_Sinh`) — are poorly served by existing LID models. Pali and Sanskrit in Sinhala script are not in any of the three base checkpoints' label sets at all.

Adding them by fine-tuning risks **catastrophic forgetting**: the model learns the new categories and degrades on the languages it already knew. So the experiment runs three conditions and measures both sides:

| Condition     | What it is                                                           | What it measures            |
| ------------- | -------------------------------------------------------------------- | --------------------------- |
| `zero_shot`   | The original checkpoint, untouched                                   | Baseline capability         |
| `target_only` | Fine-tuned on the 3 target categories only                           | Does forgetting occur?      |
| `replay`      | Fine-tuned on targets**mixed with** 8 previously-supported languages | Does rehearsal mitigate it? |

A fourth stage, `initialized`, is evaluated as a control (see §4).

The eight replay languages are `san_Deva`, `eng_Latn`, `tam_Taml`, `hin_Deva`, `ben_Beng`, `arb_Arab`, `fra_Latn`, `deu_Latn` (`lidlab/data.py:6`).

**Method name:** rehearsal-based fine-tuning / experience replay, following Chaudhry et al. (2019) and the mixed fine-tuning of Chu et al. (2017). See [METHOD_AND_CITATIONS.md](METHOD_AND_CITATIONS.md).

---

## 2. The three base models

Resolved to exact commit SHAs and locked in [models_lock.json](models_lock.json) on first download. If the config's `repo_id`/`revision`/`filename` later disagrees with the lock, the run aborts rather than silently using a different checkpoint ([backends.py:38-39](lidlab/backends.py#L38-L39)).

| Model       | Checkpoint                                               | Revision    | Labels | dim | Architecture                  |
| ----------- | -------------------------------------------------------- | ----------- | ------ | --- | ----------------------------- |
| **NLLB**    | `facebook/fasttext-language-identification`, `model.bin` | `3af127d4…` | 218    | 256 | fastText supervised, softmax  |
| **GlotLID** | `cis-lmu/glotlid`, `model_v3.bin`                        | `85cd6716…` | 2102   | 256 | fastText supervised, softmax  |
| **ConLID**  | `epfl-nlp/ConLID` (snapshot)                             | `bb370277…` | 2099   | 256 | PyTorch EmbeddingBag + linear |

NLLB here means **lid218e**, Meta's fastText language identifier — _not_ an NLLB translation transformer. This is stated explicitly in the notebook and in METHOD_AND_CITATIONS.md because the naming invites confusion.

NLLB and GlotLID share the same fastText backend and are handled by identical code. ConLID is a different architecture and has its own backend.

---

## 3. Data

### 3.1 Splits

Built by `scripts/05.finetune_dataset/build_11groups.py`, reported in [data/dataset_11groups_report.json](data/dataset_11groups_report.json).

| Split              | Rows   | Contents                           |
| ------------------ | ------ | ---------------------------------- |
| `train`            | 60,285 | 3 target categories only           |
| `validation`       | 6,986  | 3 target categories                |
| `target_test`      | 7,047  | 3 target categories                |
| `mixed_train`      | 77,473 | 11 categories (targets + 8 replay) |
| `mixed_validation` | 8,887  | 11 categories                      |

Target-only training pool: `sin_Sinh` 26,675 / `pli_Sinh` 23,490 / `san_Sinh` 10,120.

Mixed pool adds: `tam_Taml` 4,500, `san_Deva` 4,500, `arb_Arab` 3,034, `eng_Latn` 2,681, `ben_Beng` 988, `fra_Latn` 959, `hin_Deva` 724, `deu_Latn` 161.

**The replay data is 22.65% of the mixed pool and is heavily unbalanced** — Tamil and Devanagari-Sanskrit get 4,500 rows each while German gets 161. This is recorded as `replay_fraction_in_pool` in every `complete.json` and is a real limitation to disclose (§10).

Replay sources: the Aya dataset (`CohereLabs/aya_dataset`, revision `f9ea0458…`) and `surajp/sanskrit_classic` for `san_Deva` (zip SHA-256 recorded). Sampling was `random.sample` over a deduplicated pool with a per-language seeded RNG derived from seed 42 — explicitly _not_ the first N rows. Cap 5,000/language, 90/10 grouped split keyed on normalized text.

Quality filters applied at build time: min 15 chars, min 3 words, max 60 words, script-purity threshold 0.7.

### 3.2 Benchmarks

Three broad LID benchmarks, filtered to the 11 reported categories:

| Benchmark | Original rows | Retained | Removed                          |
| --------- | ------------- | -------- | -------------------------------- |
| CommonLID | 380,277       | 93,428   | 814 dup, 34 conflicting, 4 empty |
| FLORES+   | 229,687       | 16,155   | —                                |
| WiLI-2018 | 241,047       | 15,016   | 31 dup                           |

### 3.3 Preprocessing (`lidlab/data.py`)

Every text passes through `clean_text`: **NFC** Unicode normalization, then NUL / BOM / zero-width-space stripped to spaces, whitespace collapsed, trimmed.

Labels are canonicalized through an alias map (`si`→`sin_Sinh`, `ara_Arab`→`arb_Arab`, `Sinhala-Sinh`→`sin_Sinh`, …) so that inconsistent upstream tags resolve to one scheme.

**Sanskrit disambiguation.** Benchmarks label Sanskrit as a bare `san`/`sa` covering both scripts. `read_benchmark` resolves this per row by inspecting the actual codepoints: Sinhala block `U+0D80–U+0DFF` → `san_Sinh`, Devanagari `U+0900–U+097F` → `san_Deva` ([data.py:98-101](lidlab/data.py#L98-L101)). Without this, the target and replay Sanskrit categories would be conflated.

### 3.4 Leakage controls

Enforced at load time, before any training:

- Every text is SHA-256 hashed. Exact duplicate normalized texts **within** a split abort the run.
- Cross-role overlap (train ↔ dev ↔ test) aborts the run. Same-role overlap is allowed — `train` is intentionally a subset of `mixed_train`.
- **Benchmark rows are subtracted from every training/validation pool.** One row was dropped from `validation` for sharing text with CommonLID.
- Benchmark texts carrying conflicting labels are dropped entirely, not arbitrarily resolved.
- Document-ID grouping is checked; currently `require_document_ids: false`, so shared group IDs are logged as warnings rather than hard failures. **8 such warnings exist in this run** (1 shared group ID across each split pair).
- Script-purity check flags rows whose text lacks the expected script — 354 `sin_Sinh` train rows, 62 `target_test` rows, etc. With `strict_script_check: false` these are warnings.

All of this is written to `results/main_seed42/data_audit.json`.

---

## 4. The core technique: label-space extension without head replacement

This is the most important design decision in the pipeline.

The naive approach — replace the classifier head with a freshly-initialized one sized for the new label set — destroys every original language. This pipeline refuses to do that.

Instead, for all three models:

1. Keep the original output matrix **exactly**, rows and order unchanged.
2. **Append** rows only for target labels that are genuinely missing.
3. Initialize the new rows to **zero**, not random.
4. Leave the input embeddings / vocabulary / hash buckets completely untouched.

### fastText (NLLB, GlotLID) — `native/continue.cc`

`Dictionary::appendLabelStable` appends a label to the dictionary without rebuilding it (rehashing `word2int_` only when the load factor demands it, preserving all existing IDs). Then `FastText::fineTune`:

```cpp
auto next = std::make_shared<DenseMatrix>(dict_->nlabels(), args_->dim);
next->zero();                              // only newly appended rows stay zero
for (int i = 0; i < oldLabels; ++i)
  for (int j = 0; j < args_->dim; ++j)
    next->at(i, j) = old->at(i, j);        // original rows copied verbatim
output_ = next;
```

Guard: the run aborts unless the checkpoint is a non-quantized supervised **softmax** model. It will never silently convert hierarchical softmax ([continue.cc:26-27](native/continue.cc#L26-L27)).

### ConLID — `lidlab/backends.py`

Same idea in PyTorch (`add_labels`, [backends.py:152-160](lidlab/backends.py#L152-L160)): a wider `nn.Linear` is allocated, zeroed, and the old weight and bias rows copied into the leading slice.

### Verification

After every phase, `finish()` asserts the original labels are still present, in their original order, as a prefix of the new label list:

```python
if labels[:len(original_labels)] != original_labels:
    raise AssertionError('Original labels were removed/reordered')
```

### The `initialized` control

An **untrained** evaluation is run immediately after label extension, before any gradient step. Its purpose is to isolate the effect of _adding labels alone_ from the effect of _training_.

The result confirms the mechanism works: for all three models, `zero_shot` and `initialized` scores are **bit-identical** on all three benchmarks. Because the new rows are zero and the original rows are untouched, adding labels changes no prediction. Any subsequent change is attributable purely to training.

---

## 5. Training

### Matched compute budget

Both arms see **exactly the same number of examples**:

```
examples = target_passes × len(train) = 3 × 60,285 = 180,855
```

This is deliberate. `target_only` gets 3.000 nominal passes over its 60,285 rows; `replay` gets 2.334 passes over its 77,473 rows. **The replay arm does not get extra compute** — it trades passes for diversity. Any difference in outcome is therefore attributable to data composition, not training budget. A guard rejects a budget too small to cover the mixed set once ([experiment.py:32-33](lidlab/experiment.py#L32-L33)).

### Hyperparameters

| Setting              | Value                                                           |
| -------------------- | --------------------------------------------------------------- |
| Learning rate        | 0.05,**linearly decayed to 0** over the budget                  |
| Optimizer (fastText) | fastText's native SGD via`supervised()`                         |
| Optimizer (ConLID)   | `torch.optim.SGD`, sparse gradients (no dense Adam state)       |
| Loss                 | Cross-entropy over the**full** output space (218/2102/2099 + 2) |
| Seed                 | 42                                                              |
| Batch (ConLID)       | 32                                                              |
| Batch (fastText)     | 1 (per-example, fastText-native)                                |

The loss is computed over the entire label space, not a restricted 11-way head. This means the softmax denominator includes all original languages, so original classifier rows receive gradient even without positive examples — the mechanism by which forgetting can occur, and which this design deliberately leaves intact rather than masking.

### Shuffling

fastText: `std::shuffle` with `std::mt19937(seed)`, reshuffled each time the cursor wraps. ConLID: `np.random.default_rng(seed).permutation`, re-permuted on wrap. Both arms sample without replacement within an epoch.

### Two independent arms

With `replay_start: "base"` (the setting used here), both arms start from the **same** `initialized` checkpoint:

```
base → initialized ─┬→ target_only
                    └→ replay
```

They are independent, not sequential. The alternative `replay_start: "target_only"` would chain them into a sequential-recovery study; that is a different experiment and the code requires it be selected explicitly.

### ConLID-specific note

ConLID's released inference code **detaches** pooled features. A faithful copy would train only the linear head. This implementation keeps encoder gradients so the embedding actually learns, and asserts it at runtime:

```python
if self.model.embedding.weight.grad is None:
    raise AssertionError('Encoder gradient was detached')
```

The ConLID feature extractor is reimplemented to match the release bit-for-bit — same signed-byte FNV-1a hash, same `<word>` padding, same char n-grams (minn 2, maxn 5), same vocab offset and bucket arithmetic. **No contrastive loss is used**; this is supervised CE adaptation, and METHOD_AND_CITATIONS.md states that it does not reproduce the authors' full contrastive recipe.

---

## 6. Evaluation

Predictions are **unrestricted top-1 over the full label space** — the model may output any of its 218/2102/2101 labels. Predictions are _not_ filtered or argmax-restricted to the 11 reported categories. This is essential: restricting the output space would hide exactly the errors the experiment is looking for.

The count of out-of-11 predictions is recorded as `outside_11_predictions` and is itself a finding (§7).

Per category, one-vs-rest precision / recall / F1 / support. Reported aggregates:

- `macro_f1_11` — all 11 categories
- `macro_f1_target3` — the 3 Sinhala-script targets
- `macro_f1_replay8` — the 8 replay languages
- `accuracy`, plus a full confusion matrix

Target-3 and replay-8 are reported **separately and always**, so gains on new targets cannot conceal drops on old ones.

Each phase is evaluated on all three benchmarks, plus `validation` and the 3-label `target_test`. Notebook 04 (`make_tables`) builds the three cross-model tables and refuses to emit them unless every model and phase used byte-identical benchmark files (`benchmark_sha256` compared across all runs).

---

## 7. Results

Macro F1 over all 11 categories:

| Model       | Benchmark | zero-shot | target-only | replay     |
| ----------- | --------- | --------- | ----------- | ---------- |
| **NLLB**    | CommonLID | 0.7443    | 0.9581      | **0.9693** |
|             | FLORES+   | 0.7430    | **0.9670**  | 0.9644     |
|             | WiLI-2018 | 0.7614    | **0.9845**  | 0.9798     |
| **GlotLID** | CommonLID | 0.7429    | 0.9603      | **0.9687** |
|             | FLORES+   | 0.7397    | 0.9608      | **0.9655** |
|             | WiLI-2018 | 0.7505    | 0.9710      | **0.9790** |
| **ConLID**  | CommonLID | 0.7061    | 0.9183      | **0.9456** |
|             | FLORES+   | 0.7194    | 0.9318      | **0.9570** |
|             | WiLI-2018 | 0.7314    | 0.9433      | **0.9712** |

Split into the two halves (CommonLID):

| Model   | Phase       | target-3 F1 | replay-8 F1 |
| ------- | ----------- | ----------- | ----------- |
| NLLB    | zero-shot   | 0.1814      | 0.9554      |
|         | target-only | 0.9737      | 0.9522      |
|         | replay      | 0.9895      | 0.9617      |
| GlotLID | zero-shot   | 0.1817      | 0.9534      |
|         | target-only | 0.9846      | 0.9512      |
|         | replay      | 0.9893      | 0.9610      |
| ConLID  | zero-shot   | 0.1836      | 0.9021      |
|         | target-only | 0.9633      | 0.9015      |
|         | replay      | 0.9576      | 0.9411      |

### What the numbers actually say

**The target gain is large and real.** Target-3 F1 goes from ~0.18 to ~0.96–0.99. At zero-shot, `pli_Sinh` and `san_Sinh` score **exactly 0.000** on every benchmark — the models have no such labels. `sin_Sinh` shows the signature failure: recall 0.977 but precision 0.377, i.e. the base models dump all Sinhala-script text into `sin_Sinh` regardless of whether it is Sinhala, Pali, or Sanskrit.

**Forgetting is mild, not catastrophic.** Replay-8 F1 on CommonLID drops by only 0.0032 (NLLB), 0.0022 (GlotLID), 0.0006 (ConLID). The per-language damage is concentrated, not spread: for NLLB the worst hits are English −0.0207, French −0.0123, Hindi −0.0067; GlotLID's are Hindi −0.0095, Tamil −0.0060, Arabic −0.0047. Latin-script European languages suffer most, which is consistent with the target data being entirely Sinhala-script. The label-preserving initialization is doing most of the protective work.

**Replay helps, and helps most where forgetting was worst.** On CommonLID, replay recovers exactly the languages target-only damaged: NLLB English +0.0452, French +0.0213, German +0.0090; GlotLID English +0.0312; ConLID English +0.0373. It does this _while also_ improving target-3 for NLLB and GlotLID, so it is not a straight trade-off. The one exception is GlotLID German (−0.0081), the language with only 161 rows in the replay pool.

**The clearest replay effect is the out-of-11 prediction count**, which is not visible in F1 at all:

| Model   | zero-shot | target-only | replay    |
| ------- | --------- | ----------- | --------- |
| NLLB    | 4,460     | 5,483       | **2,869** |
| GlotLID | 8,901     | 8,856       | **2,837** |
| ConLID  | 27,634    | 27,774      | **8,861** |

Target-only training leaves stray predictions into unrelated languages untouched or worse. Replay cuts them by roughly two thirds to three quarters. This is the strongest single piece of evidence that rehearsal is doing something real to the decision boundary.

**ConLID behaves differently from the other two.** It is the only model where replay _reduces_ target-3 F1 (0.9633 → 0.9576) while sharply improving replay-8 (0.9015 → 0.9411). It has the weakest zero-shot baseline and by far the most out-of-11 predictions. Its accuracy on CommonLID at target-only is only 0.6980 despite 0.9183 macro F1 — a gap driven by the heavy class imbalance in CommonLID (41,634 Arabic and 27,443 English rows against 81 Tamil).

**One artifact to be aware of:** `arb_Arab` on FLORES+ sits at F1 ≈ 0.6667 with recall exactly 0.500 in _every_ phase including zero-shot. The raw counts make the cause unambiguous — support 2,024 (exactly double every other language's 1,012), **tp = 1,012, fn = 1,012, fp = 1**. Precision is 0.999. The model correctly identifies one full set of 1,012 rows and misses the other completely, so FLORES+ is supplying two Arabic variants (e.g. MSA plus a regional or romanized variant) collapsed under one `arb_Arab` label, and one of them is never predicted as `arb_Arab`. This is a benchmark property, not a model failure or a fine-tuning effect, and it caps FLORES+ macro F1 identically for all three models in all four phases. Worth either excluding or footnoting in the paper.

Training cost is trivial: 67–189 seconds per arm.

---

## 8. Reproducibility machinery

The pipeline is built to fail loudly rather than produce quietly-wrong results.

**Protocol signature.** A SHA-256 over the full config, data-file hashes, base-checkpoint hash, seed, budget, and original label list. Written to `protocol.json`. If anything changes and you re-run into the same `output_dir`, the run aborts:

> `Configuration/data/checkpoint changed. Use a new output_dir instead of mixing results in ...`

**Phase resumption.** Each completed phase writes `complete.json` carrying the signature. Completed phases are skipped; interrupted ones restart from their defined initial checkpoint. A phase whose signature does not match raises `Stale phase results`.

**Hashing everywhere.** Every data file, every benchmark, every base and output checkpoint is SHA-256'd and recorded.

**Environment capture.** `pip freeze` is written to `environment.txt` per model; Python version and platform go into `protocol.json`.

**Guards that abort the run:**

- Base model missing any replay language → abort (you cannot measure retention of a language the model never had)
- Non-softmax or quantized fastText checkpoint → abort
- Training labels not present in the model → abort
- Non-finite loss or logits → abort
- Text containing `__label__` → abort (fastText label leakage)
- Text yielding no ConLID features → abort rather than fabricate a prediction
- Cross-role text overlap → abort

**No test-based selection.** Fixed budget, no early stopping, no checkpoint selection on benchmark scores. Recorded literally in every `complete.json` as `'selection': 'fixed budget; no test-based selection'`.

The vendored fastText is v0.9.2, compiled at run time by `scripts/build_native.py` with `-std=c++11 -O3` (statically linked on Windows so the binary runs without MSYS2 on PATH). Only `native/continue.cc` is new; upstream sources are unmodified under their own LICENSE.

---

## 9. How to run it

```
notebook 00  →  setup and data preparation
notebook 01  →  NLLB      (all three conditions)
notebook 02  →  GlotLID
notebook 03  →  ConLID
notebook 04  →  cross-model tables
```

Each model notebook is three lines:

```python
c = load_config()
results = run_experiment(c, 'nllb')   # or 'glotlid' / 'conlid'
```

Run one model at a time — checkpoints are large. Changing data or hyperparameters requires a new `output_dir`.

---

## 10. Limitations to state in the write-up

1. **Retention is measured on 8 languages, not 218/2102.** The original labels remain available and the output rows are preserved, but retention across the full original label set is _not_ evaluated. Do not infer broad multilingual preservation from eight scores. To claim it, add held-out languages outside the replay set as a separate retention evaluation.
2. **The replay mixture is small and unbalanced** — 22.65% of the pool, from 161 German rows to 4,500 Tamil. Results do not establish that eight languages, or this particular distribution, is sufficient.
3. **Replay data is not original pretraining data.** It is newly collected text representing previously-supported languages. Describe it as rehearsal data.
4. **Single seed.** One run at seed 42; no variance estimate across seeds.
5. **No hyperparameter search.** lr 0.05 and 3 passes were fixed a priori. Honest, but unoptimized.
6. **ConLID is adapted with cross-entropy, not the authors' contrastive objective.** The feature extractor is a reimplementation verified against the release; the training recipe is deliberately different.
7. **Known data-quality warnings are unresolved**, not absent: 354 `sin_Sinh` training rows contain no Sinhala characters, 8 document-group IDs are shared across splits, and `strict_script_check` / `require_document_ids` are both off. These are logged in `data_audit.json` and should be either fixed or disclosed.
8. **The `arb_Arab` FLORES+ ceiling (§7)** is a benchmark artifact that caps macro F1 for every model.

---

## 11. File map

| Path                                               | Role                                                                  |
| -------------------------------------------------- | --------------------------------------------------------------------- |
| [config.json](config.json)                         | All settings: paths, seed, budget, lr, model sources                  |
| [lidlab/data.py](lidlab/data.py)                   | Loading, normalization, label canonicalization, leakage checks        |
| [lidlab/backends.py](lidlab/backends.py)           | Checkpoint download/locking, fastText wrapper, ConLID model + trainer |
| [lidlab/experiment.py](lidlab/experiment.py)       | Phase orchestration, protocol signature, resumption                   |
| [lidlab/metrics.py](lidlab/metrics.py)             | Scoring, summaries, cross-model tables                                |
| [native/continue.cc](native/continue.cc)           | Label-append + fine-tune for fastText (the only new C++)              |
| `results/main_seed42/<model>/<phase>/`             | Per-phase metrics, confusion,`complete.json`                          |
| `results/main_seed42/data_audit.json`              | Every leakage and quality check                                       |
| [METHOD_AND_CITATIONS.md](METHOD_AND_CITATIONS.md) | Citations and suggested paper wording                                 |

Model weights, datasets, and per-row `predictions.csv` are gitignored as regenerable artifacts; aggregate metrics are committed.
