# Validation and limits

Validation date: 21 September 2026.

## Executed checks

- Six automated tests passed on small generated checkpoints and synthetic data. They cover pretrained input/output weight preservation during label expansion, real encoder/head updates during training, standard fastText serialization, ConLID serialization, full-label prediction scoring, document-overlap rejection, both independent and sequential initialization, zero-shot prediction imports, and complete three-model table export.
- The native fastText executable was built from the bundled C++ source with GCC. A resulting adapted `.bin` was loaded and checked using `fasttext-wheel` 0.9.2.
- ConLID feature IDs and probabilities were compared with the downloaded official `epfl-nlp/ConLID/model.py` on nine multilingual probes, using the same small generated checkpoint. The exported expanded checkpoint also loaded with the official inference code. This validates architecture/serialization compatibility on a small checkpoint, not full-checkpoint language accuracy.
- All six notebooks passed the notebook format validator. Every Python source file and notebook code cell parsed successfully.
- The header of the official NLLB `lid218e.bin` was read: fastText binary version 12, dimension 256, supervised softmax, 1,000,000 buckets, character ngrams 2–5. This supports the native backend choice. GlotLID's paper documents its softmax architecture.

The small model's scores are only software tests. They are not included as research results.

## Not executed

The supplied target CSVs, mixed JSONL files, and FLORES+ schema and label counts were inspected. Full-size pretrained checkpoints were not trained in the authoring environment. End-to-end integration was exercised with small structurally compatible checkpoints instead. The notebooks perform the full downloads when the user runs them, or accept already-downloaded checkpoints via `local_path`.

The optional Wikipedia streaming sampler was not run over the full eight-language corpus here. Its data source, snapshot names, schema, and article-level splitting code were checked; the installed dataset API and source availability are checked during execution. Review sampled text quality before research use.

The supervisor's voice recording could not be transcribed here. Implementation follows the user's written account and includes both interpretations of the third stage.

## Reproduce the software checks

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
```

The delivered tests generate temporary test data and weights; they do not download or train the full research models.

## Authoring environment

Python 3.12.14; NumPy 2.3.5; pandas 2.2.3; PyTorch 2.14.0+cpu; safetensors 0.8.0; huggingface_hub 1.32.0; nbformat 5.11.1; pytest 9.1.1; fasttext-wheel 0.9.2. Actual user runs record their own `environment.txt` and checkpoint/data hashes. Version ranges in `requirements.txt` allow compatible installations rather than requiring this exact authoring runtime.
