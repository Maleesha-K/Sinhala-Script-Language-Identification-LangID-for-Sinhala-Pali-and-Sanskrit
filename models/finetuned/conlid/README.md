---
license: mit
language:
- si
- pi
- sa
tags:
- language-identification
- conlid
- sinhala
- pali
- sanskrit
- intra-script
base_model: epfl-nlp/ConLID
pipeline_tag: text-classification
---

# ConLID-2101: Sinhala-Script Pali & Sanskrit

A [ConLID](https://huggingface.co/epfl-nlp/ConLID) language identification model extended with **two new Sinhala-script classes** — Pali (`pli_Sinh`) and Sanskrit (`san_Sinh`) — on top of the base model's 2099 languages.

Pali and Sanskrit are frequently written in Sinhala script in Sri Lankan Buddhist and scholarly corpora. Off-the-shelf LID models classify all such text as Sinhala, since `sin_Sinh` is the only Sinhala-script label they know. This model separates the three.

## Labels

2101 total: ConLID's original 2099-label set, plus `pli_Sinh` (id 2099) and `san_Sinh` (id 2100).

| Label | Language | Script |
|---|---|---|
| `sin_Sinh` | Sinhala | Sinhala |
| `pli_Sinh` | Pali | Sinhala |
| `san_Sinh` | Sanskrit | Sinhala |
| `san_Deva` | Sanskrit (inherited from base) | Devanagari |

## Usage

ConLID uses a **custom architecture**, not `transformers`. You need `model.py` from the
[ConLID repository](https://github.com/epfl-nlp/ConLID) to load it — `AutoModel` will not work.

```python
from huggingface_hub import snapshot_download
from model import ConLID  # from github.com/epfl-nlp/ConLID

path = snapshot_download(repo_id="script-langid/conlid-sinhala-pali-sanskrit")
model = ConLID.from_pretrained(dir=path)

labels, probs = model.predict("බුද්ධං සරණං ගච්ඡාමි", k=3)
print(labels, probs)

# batched
labels, probs = model.predict_batched(["...", "..."], k=1)
```

Requires `torch`, `numpy` and `safetensors`. Use modest batch sizes on CPU — inputs are
padded to the longest sequence in the batch, so large batches can exhaust memory.

## Training

| | |
|---|---|
| Base model | `epfl-nlp/ConLID` (2099 labels) |
| Method | Classification-head extension + end-to-end fine-tuning |
| Trainable parameters | All |
| Optimizer | AdamW |
| Learning rate | 1e-4 |
| Batch size | 8 (gradient accumulation ×4) |
| Max epochs | 10, early stopping (patience 2) on validation micro-F1 |
| New classes | `pli_Sinh`, `san_Sinh` |

The classification head was expanded from 2099 to 2101 outputs. Existing rows were copied
across and the two new rows Xavier-initialised, so the pretrained label space is preserved
at initialisation. The checkpoint published here is the best-validation-F1 epoch.

Training data: 60,285 sentences (26,675 Sinhala, 23,490 Pali, 10,120 Sanskrit) from a
group-stratified split in which every literary work, chapter or commentary is assigned
wholesale to exactly one partition, so no document leaks between train, validation and test.

## Evaluation

### Held-out target test set

On the held-out test split (7,047 sentences), with no document overlap with training:

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| **Sinhala** (`sin_Sinh`) | 0.9613 | 0.9677 | 0.9645 | 2693 |
| **Pali** (`pli_Sinh`) | 0.9718 | 0.9683 | 0.9700 | 3027 |
| **Sanskrit** (`san_Sinh`) | 0.9713 | 0.9171 | 0.9434 | 1327 |

**Accuracy 0.9584 · Macro-F1 0.9593**

### Per-language F1

Evaluated on three hybrid benchmarks — CommonLID, FLORES+, and WiLI-2018 — across both the
new Sinhala-script classes and a representative sample of original ConLID languages.

| Language | CommonLID | FLORES+ | WiLI-2018 |
|---|---|---|---|
| **Sinhala** (`sin_Sinh`) | 0.9645 | 0.9645 | 0.9645 |
| **Pali** (`pli_Sinh`) | 0.9700 | 0.9700 | 0.9700 |
| **Sanskrit** (`san_Sinh`) | 0.9434 | 0.9434 | 0.9434 |
| Sanskrit (Devanagari) (`san_Deva`) | 0.9607 | 0.9985 | 0.9924 |
| English (`eng_Latn`) | 0.8491 | 0.9960 | 0.9429 |
| Tamil (`tam_Taml`) | 0.9818 | 0.9995 | 0.9945 |
| Hindi (`hin_Deva`) | 0.9412 | 0.9970 | 0.9899 |
| Bengali (`ben_Beng`) | 0.9592 | 0.9995 | 0.9435 |
| Arabic (`arb_Arab`) | 0.7951 | 0.4003\* | n/a |
| French (`fra_Latn`) | 0.8974 | 1.0000 | 0.9809 |
| German (`deu_Latn`) | 0.8881 | 0.9970 | 0.9680 |

All three benchmarks embed the **same** 7,047 held-out target rows, so the three
Sinhala-script scores are identical across columns by construction. The background-language
columns are what differ between benchmarks.

### Aggregate

| Benchmark | Samples | Accuracy | Macro F1 |
|---|---|---|---|
| CommonLID | 77,974 | 0.7567 | 0.9228 |
| FLORES+ | 16,155 | 0.8867 | 0.9333 |
| WiLI-2018 | 14,047 | 0.9604 | 0.9690 |

Macro F1 is averaged over the 11 evaluated classes. Accuracy runs below macro F1 on
CommonLID and FLORES+ because of the Arabic dialect split described below, which costs
recall on a large Arabic partition without affecting the other ten classes.

\* Arabic is the one weak background language, and the cause is inherited from the base
model rather than introduced by fine-tuning: ConLID carries fine-grained regional Arabic
heads, so Modern Standard Arabic input is fragmented across them. On CommonLID, 6,059 of
26,152 Arabic rows are predicted `ary_Arab` (Moroccan) and 1,460 `arz_Arab` (Egyptian),
giving 0.66 recall on `arb_Arab`. The same fragmentation drives the lower FLORES+ figure.
Applications needing Arabic should merge the `*_Arab` heads before scoring.

### Base-language retention

All parameters were trainable during fine-tuning, so the background languages were
re-measured rather than assumed. On FLORES+ they sit between 0.9960 and 1.0000 for English,
Tamil, Hindi, Bengali, French and German, and Devanagari Sanskrit holds at 0.9985 — the
pretrained label space survives the extension. The lower CommonLID figures for English
(0.8491), French (0.8974) and German (0.8881) reflect that benchmark's noisier web text,
where the base model also fragments across closely related Latin-script heads
(`sco_Latn`, `srd_Latn`, `gsw_Latn`), not forgetting induced by this fine-tune.

### Against the zero-shot base model

The base ConLID model has no Sinhala-script Pali or Sanskrit label at all, so it cannot
score above zero on those classes regardless of input:

| Class | Base ConLID | This model |
|---|---|---|
| Pali (Sinhala script) | 0.0000 | 0.9700 |
| Sanskrit (Sinhala script) | 0.0000 | 0.9434 |
| Sinhala | 0.7916 | 0.9645 |

Base-model figures are from the same evaluation pipeline; it routes all Sinhala-script input
to `sin_Sinh`, which also caps its Sinhala score because the three languages are conflated.

## Limitations

- Sanskrit is the weakest target class (0.9434 F1), with recall of 0.9171; its most common
  confusion is with Pali, expected given their lexical and orthographic overlap.
- Roughly 1% of test inputs (67 of 7,047) are predicted as one of the 2098 unrelated
  background languages rather than a Sinhala-script class. A script-based pre-filter, or
  restricting the argmax to the three target labels, removes this in deployment.
- Short inputs are less reliable. Prefer a full sentence.
- Arabic is unreliable without post-processing (0.7951 CommonLID / 0.4003 FLORES+ F1), because
  the base model's regional Arabic heads fragment Modern Standard Arabic. Merge the `*_Arab`
  labels if you need Arabic.
- The Sanskrit training data is partly transliterated into Sinhala script from SLP1
  Romanization, which does not fully reflect historical scribal ligatures.

## Citation

Base model — ConLID: Supervised Contrastive Learning for Low-Resource Language Identification:

```bibtex
@article{conlid2025,
  title={ConLID: Supervised Contrastive Learning for Low-Resource Language Identification},
  journal={arXiv preprint arXiv:2506.15304},
  year={2025}
}
```

## License

MIT, inherited from the base ConLID model.
