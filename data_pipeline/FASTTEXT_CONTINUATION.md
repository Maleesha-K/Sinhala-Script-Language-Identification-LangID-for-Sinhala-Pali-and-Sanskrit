**Continue training fastText LID-176 on your 11 groups**

This package imports both complete pretrained matrices from the official
`lid.176.bin`, verifies the original model, adds Pali, and trains the inherited
parameters. It uses ordinary supervised hierarchical negative log-likelihood.
The default experiment has no distillation, extra-language replay, frozen
embeddings, vocabulary rebuilding, or replacement classifier.

Your prepared inputs are:

```
data_pipeline/datasets/finetuning/train_mixed_11groups.jsonl
data_pipeline/datasets/finetuning/val_mixed_11groups.jsonl
data_pipeline/datasets/finetuning/dataset_11groups_report.json
```

The new 77,473/8,887-record files were not available when this code was built.
Their counts and validation status come from your Claude Code summary. The
notebook checks the actual files again before training.

**1. Copy the code into your existing repository**

Merge the archive's `data_pipeline` folder into the same folder in your repo.
These are new files; keep your existing dataset preparation notebooks.

| File under `data_pipeline/` | Purpose |
|---|---|
| `fasttext_continual/__init__.py` | Public model import |
| `fasttext_continual/features.py` | Original vocabulary IDs, UTF-8 hashing, character features and EOS |
| `fasttext_continual/model.py` | Load pretrained weights, retain the tree, add Pali, save/load |
| `fasttext_continual/data.py` | Read your schema, map labels, check splits and cache feature IDs |
| `fasttext_continual/verify.py` | Mandatory import, expansion, gradient and reload checks |
| `fasttext_continual/train.py` | Supervised SGD, validation, checkpoints and epoch-boundary resume |
| `fasttext_continual/evaluate.py` | Native/custom comparison with every output label available |
| `fasttext_continual/requirements.txt` | Dependencies for this experiment |
| `scripts/06.finetune_models/fastText_LID_176_continued.ipynb` | Colab workflow |

Use Python 3.11 or later. Commands below run from the repository root, not from
inside `data_pipeline`. No C++ compilation or separate repository is needed.

**2. Make the code available to Colab**

In your local terminal, create an experiment branch if you do not already have
one. If you have an experiment branch, use it and set the notebook's `BRANCH`
accordingly. Commit any existing dataset-builder changes separately if desired.

```bash
git switch -c experiment/fasttext-continuation
git add data_pipeline/fasttext_continual
git add data_pipeline/scripts/06.finetune_models/fastText_LID_176_continued.ipynb
git add FASTTEXT_CONTINUATION.md VALIDATION_REPORT.json
git commit -m "Add continued training of pretrained fastText LID-176"
git push -u origin experiment/fasttext-continuation
```

The new model checkpoints are directories containing `weights.pt`, `config.json`
and `vocab.json`. Keep the entire checkpoint directories out of Git, not just
their `.pt` files. If using the local commands below, add this pattern to your
root `.gitignore`:

```
/data_pipeline/models/continual/
```

**3. Put your generated dataset files in Google Drive**

Create `MyDrive/langid_finetuning_data` and copy all three prepared files there.
The notebook copies them into the runtime for reading. Your git-ignored dataset
files will not arrive with `git clone`.

Open the new notebook in Google Colab using File > Open notebook > GitHub and
select your repository, branch and notebook. Alternatively, upload the notebook
file. A CPU runtime is sufficient for verification; a GPU can run the custom
PyTorch trainer. Run cells in order.

At the top, set:

- `BRANCH`: the branch containing these new code files.
- `DRIVE_DATA_DIR`: the folder with your prepared files.
- `DRIVE_EXPERIMENT_DIR`: a new folder for this experiment's initialization,
  pilot and full training checkpoints.

The notebook downloads the official 126 MB uncompressed checkpoint and checks
its SHA-256. It does not use `.ftz` or `.vec` files.

**4. Run the import verification before training**

The verification checks exact copied weights, feature IDs, hidden vectors,
top predictions and returned scores against native fastText. It then checks
that expansion preserves the other languages' initial probabilities, that
checkpoints reload identically, and that a gradient step changes inherited
input weights, inherited decision weights and the new Pali node.

If a check fails, stop and inspect the exception. Do not train through a parity
failure or remove the assertion to make the cell pass.

It saves:

```
initialization/base176/          original imported model
initialization/init177/          expanded model BEFORE training
initialization/parity_report.json
```

The expansion replaces the Sinhala leaf with a Sinhala/Pali decision. Its new
weight vector starts at zero. At initialization, the old Sinhala probability
is divided equally between Sinhala and Pali. All other language paths are
unchanged. This is an explicit experimental design choice, not an official
fastText fine-tuning API or a claim that this is the optimal tree placement.

**5. Run the CPU pilot**

The notebook uses up to 64 training and 16 validation examples per group for
one epoch. This checks the training pipeline on your real file schema. It is
not a research result and its checkpoint is not the full experiment.

**6. Run the full experiment**

The full training cell starts again from `init177`, not from the pilot.

| Setting | First experiment |
|---|---|
| Optimizer | SGD, no momentum or weight decay |
| Learning rate | 0.01, constant |
| Batch size | 64 |
| Epochs | 5 |
| Trainable parameters | Entire inherited input/output matrices and the new decision node |
| Sampling | Seeded shuffle, natural dataset distribution |
| Loss | Mean supervised hierarchical NLL |
| Model selection | Highest validation language-level macro-F1 among trained epochs |

These are pilot hyperparameters, not tuned or published best settings. The
PyTorch trainer uses exact sigmoid/BCE and minibatches. It does not reproduce
the native C++ training loop's sigmoid lookup table or asynchronous updates.
It does continue from the full pretrained weights and inherited hierarchy.

Your class imbalance remains visible in this first baseline. `--balance group`
is an optional separate experiment using inverse-frequency group weights.
It does not add examples to German's 18-example validation set. Give that run
a different output folder and change only the documented setting.

Every complete epoch is saved to Drive as `epoch-001/`, etc. `best/` contains
the best trained checkpoint. `last.json` identifies the most recent complete
epoch; `history.json` records losses and validation metrics. An interruption
within an epoch loses that partial epoch. Rerunning the notebook training cell
resumes from the last complete epoch with the same settings and next shuffle.
SGD has no momentum state in this implementation. GPU reductions can vary
slightly across runs.

Five model checkpoints plus best/ and initialization use roughly a gigabyte.
The downloaded base model and runtime feature arrays are additional temporary
files. Feature IDs are cached; the vectors themselves remain trainable.

**7. Interpret evaluation consistently**

| Dataset language | Model output |
|---|---|
| `sin` | `si` |
| `pli` | `pi` |
| `san` in either script | `sa` |
| `eng`, `tam`, `hin`, `ben` | `en`, `ta`, `hi`, `bn` |
| `arb`, `fra`, `deu` | `ar`, `fr`, `de` |

There are 177 available model labels and 10 gold languages in these 11
language-script groups. All outputs compete at prediction time. The trainer
does not restrict predictions to the ten languages appearing in training.

The report's `language_macro_f1` averages the ten languages represented in the
gold dataset. Both Sanskrit scripts count as `sa`. Out-of-set predictions
still count as errors for their true language. The report also gives support
and accuracy/recall for each of the 11 script groups, plus language precision,
recall and F1. Gold script metadata is never used to alter predictions.

These group accuracies are NOT the old table's 11-class F1 scores. Do not label
them as such. Comparing with your old table requires consistent gold-label
mapping and metric definitions for the original and continued models.

The notebook compares the native 176 model, the untrained 177 expansion and the
best trained model on validation. The separate expansion baseline distinguishes
the effect of adding Pali from the effect of training.

After fixing model selection, run the optional final benchmark cell. It uses
the repository's `data/phase2_eval/eval_*_11lang.csv` files with their explicit
language-script labels. It fails clearly if files are missing. For other
benchmark files, supply `text`, `label`, and `group` or `script`; Sanskrit must
explicitly distinguish the two scripts. No benchmark examples enter training
or validation.

Evaluation on these 11 groups cannot establish retained performance on all
original languages. Save the full-output predictions/metrics and later add an
independent, broader retention benchmark before making that claim.

**8. Load the trained model**

From your repository root or the notebook, use:

```python
from data_pipeline.fasttext_continual import ContinualLID
model = ContinualLID.from_pretrained("/path/to/full_none/best")
labels, scores = model.predict("සිංහල භාෂාව ශ්‍රී ලංකාවේ භාවිතා වේ.", k=3)
print(labels, scores)
```

`native_scores=True` is the default: scores match fastText's small per-branch
epsilon convention and are not exactly normalized. For mathematically
normalized hierarchical probabilities, use `native_scores=False`.

Keep all three files together: `weights.pt`, `vocab.json`, `config.json`. The
explicit expanded hierarchy needs this loader; `fasttext.load_model()` cannot
load this directory. No native `.bin` export is claimed.

The loader also accepts a future Hugging Face model repository ID containing
these three files. The Python code must first be available to the researcher;
publishing an installable package and a model card is a separate release step.
No model has been uploaded by this package.

**Checks completed for this code package**

The unmodified official checkpoint matched native fastText top-1 predictions
on 794 examples (32 samples from each of the 24 labels in your earlier uploaded
mixed dataset, plus 26 edge-case/multilingual probes). All 3,000 tested token
feature-ID sequences matched exactly. The maximum returned score difference
was approximately 2.98e-7. Both imported matrices were identical to the source.

Expansion invariants, save/reload, inherited/new-parameter gradient updates,
and both evaluation entry points passed. A two-epoch CPU training integrity
check on 176 training/44 validation examples matched a one-epoch-plus-resume
run exactly. This tiny check used older uploaded examples and synthetic
Sanskrit-Devanagari text; it supplies no research performance evidence.

The notebook passed notebook-format and Python-cell syntax validation. The
Colab runtime, CUDA path, your new full dataset and a future Hub download were
not executed here. Details are in `VALIDATION_REPORT.json`.

**Optional: run without the notebook**

Install dependencies from the repository root:

```bash
python -m pip install -r data_pipeline/fasttext_continual/requirements.txt
```

Download the official base checkpoint to
`data_pipeline/models/benchmark/fastText/lid.176.bin` using the link below, then:

```bash
python -m data_pipeline.fasttext_continual.verify --base-bin data_pipeline/models/benchmark/fastText/lid.176.bin --data data_pipeline/datasets/finetuning/train_mixed_11groups.jsonl --data data_pipeline/datasets/finetuning/val_mixed_11groups.jsonl --out data_pipeline/models/continual/initialization

python -m data_pipeline.fasttext_continual.train --init data_pipeline/models/continual/initialization/init177 --train data_pipeline/datasets/finetuning/train_mixed_11groups.jsonl --val data_pipeline/datasets/finetuning/val_mixed_11groups.jsonl --out data_pipeline/models/continual/pilot --epochs 1 --pilot-per-group 64 --pilot-val-per-group 16 --device cpu

python -m data_pipeline.fasttext_continual.train --init data_pipeline/models/continual/initialization/init177 --train data_pipeline/datasets/finetuning/train_mixed_11groups.jsonl --val data_pipeline/datasets/finetuning/val_mixed_11groups.jsonl --out data_pipeline/models/continual/full_none --epochs 5 --lr 0.01 --batch-size 64 --balance none --device cpu

python -m data_pipeline.fasttext_continual.evaluate --checkpoint data_pipeline/models/continual/full_none/best --data data_pipeline/datasets/finetuning/val_mixed_11groups.jsonl --out data_pipeline/models/continual/full_none/final_validation.json
```

Use `--device cuda` when CUDA is available. To resume, rerun the same train
command with `--resume`. Change only the total `--epochs` if you want to extend
the run. Dataset hashes, initialization hashes and training settings are
checked. A new hyperparameter experiment needs a new output folder.

**Implementation references and attribution**

- [Official LID-176 model and license](https://fasttext.cc/docs/en/language-identification.html)
- [Download lid.176.bin](https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin)
- [Feature extraction and hashing](https://github.com/facebookresearch/fastText/blob/v0.9.2/src/dictionary.cc)
- [Hierarchical tree and inference scores](https://github.com/facebookresearch/fastText/blob/v0.9.2/src/loss.cc)
- [Original feature averaging and gradient updates](https://github.com/facebookresearch/fastText/blob/v0.9.2/src/model.cc)

The code archive includes the applicable fastText source notice. The original
weights are distributed under CC-BY-SA 3.0. Retain their attribution and license
information when preparing the eventual model release; this code archive
contains no model weights or datasets.
