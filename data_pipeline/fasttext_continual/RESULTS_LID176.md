# lid.176 Continuation — Full Experimental Results (seed 42)

Continued training of the official fastText `lid.176.bin` on the 11-group mixed
dataset, using the hierarchical-softmax continuation code in this folder.
Independent of `data_pipeline/new_method/`, which was not modified.

**Headline: the method works. The original configuration did not.** The first
run (lr 0.01) produced Pali accuracy 0.000 and never predicted `pi` once. That
was a learning-rate failure, not a capability limit. At lr 2.0 with linear
decay, the same code reaches **0.9949 validation macro-F1 with Pali at 0.9968**,
and 0.9877 mean target-3 accuracy on held-out benchmarks.

---

## 1. Why lid.176 needs different code

`new_method/native/continue.cc:26-27` aborts on this checkpoint by design.
lid.176 is a **hierarchical-softmax** model: labels are Huffman-tree leaves and
a label's score is a product of sigmoids along its root-to-leaf path, with
internal decision nodes shared between labels. There is no per-label output row
to append, so the zero-row append used for NLLB/GlotLID does not apply.

This folder instead performs **leaf surgery** (`model.py:175`, `add_pali`): the
Sinhala leaf becomes a new decision node with `si` on the left branch and `pi`
on the right. The node is zero-initialized, so the old Sinhala probability mass
divides exactly evenly until training starts.

## 2. Provenance

| Item | Value |
|---|---|
| Base checkpoint | `lid.176.bin`, SHA-256 `7e69ec5451bc261cc7844e49e4792a85d7f09c06789ec800fc4a44aec362764e` |
| Base config | dim 16, minn 2, maxn 4, bucket 2,000,000, wordNgrams 1, 176 labels |
| torch / Python / numpy | 2.14.0+cpu / 3.11.9 / 1.26.4 |
| Train / validation | 77,473 / 8,887 rows, 11 groups |
| Seed | 42 |

The downloaded hash matches `VALIDATION_REPORT.json` exactly, so this is the
same base the code was originally validated against.

## 3. Verification gate — passed

`verify.py` against native fastText on 378 texts sampled from the real splits:

| Check | Result |
|---|---|
| Top-1 parity vs native | 378 / 378 |
| Native scores compared | 11,873 |
| Max hidden-state error | 2.38e-07 |
| Max score error | 4.77e-07 |
| Input / output weights identical | true / true |
| Expansion invariants | passed |
| Checkpoint round-trip | passed |
| Gradient check | all parameters trainable, finite loss 0.7096 |

The expansion invariant (`verify.py:148-150`) asserts the other 175 languages
keep identical probabilities after adding Pali, and that `P(si)+P(pi)` equals
the old `P(si)`. It held. Loss 0.7096 ≈ ln(2) confirms the even split.

Split validation on real data: all 11 groups, **0** duplicate normalized texts,
**0** train/validation overlap. All trained checkpoints keep the original 176
labels as an intact prefix with `pi` appended at index 176 — the same invariant
`new_method`'s `finish()` asserts.

## 4. The learning-rate sweep

Validation, 5 epochs unless noted, batch 64, constant LR unless noted:

| Config | Loss | Macro-F1 | Accuracy | Pali | Sanskrit-Sinh | `pi` predicted |
|---|---|---|---|---|---|---|
| lr 0.01 (original) | 0.7304 | 0.8117 | 0.5785 | **0.0000** | 0.3153 | **0** |
| lr 0.01, 20 epochs | — | 0.9040 | 0.7607 | 0.3076 | — | 865 |
| lr 0.01 + warm-start | — | 0.8119 | 0.5789 | 0.0004 | — | 1 |
| lr 0.05 | 0.4644 | 0.9505 | 0.8809 | 0.6792 | 0.9125 | — |
| lr 0.1 + decay | — | 0.9520 | 0.8856 | 0.6942 | — | 1,950 |
| lr 0.2 | 0.0926 | 0.9873 | 0.9893 | 0.9950 | 0.9737 | — |
| lr 0.5 | 0.0411 | 0.9918 | 0.9927 | 0.9957 | 0.9861 | 2,791 |
| lr 0.5 + decay (3 ep) | 0.0892 | 0.9879 | 0.9894 | 0.9950 | 0.9737 | 2,815 |
| lr 0.5 + group balance (3 ep) | 0.1178 | 0.9882 | 0.9848 | 0.9800 | 0.9822 | 2,768 |
| lr 1.0 + decay (3 ep) | 0.0474 | 0.9911 | 0.9922 | 0.9954 | 0.9861 | 2,811 |
| **lr 2.0 + decay** | — | **0.9949** | **0.9950** | **0.9968** | — | 2,810 |

Monotone in LR across nearly two orders of magnitude, with no instability even
at lr 2.0. **The original lr 0.01 was roughly 50× too low.**

## 5. Root cause, diagnosed directly

Before sweeping, I measured the si/pi decision node on the lr 0.01 model. It was
learning the right direction — mean sigmoid output was higher on Pali text
(0.4123) than Sinhala (0.3447), and that separation grew every epoch — but the
absolute level plateaued near 0.41. The maximum over 600 Pali samples at epoch 5
was 0.4575, still below 0.5, so `argmax` always took the `si` branch.

Simulating a different cutoff on the *same* lr 0.01 weights:

| Threshold | Pali recall | Sinhala kept | Sanskrit-Sinh kept |
|---|---|---|---|
| 0.50 | 0.0000 | 1.0000 | 1.0000 |
| 0.42 | 0.3308 | 0.9975 | 0.9977 |
| 0.40 | 0.7535 | 0.9916 | 0.9783 |
| **0.38** | **0.9507** | **0.9610** | 0.8970 |
| 0.37 | 0.9775 | 0.9115 | 0.8164 |

The representation had already separated the languages; only the 0.5 cutoff
blocked it. That established a trainable-offset problem rather than a capacity
ceiling, and predicted that a larger LR would fix it.

The 20-epoch lr 0.01 run confirms it directly — the node creeps toward the
threshold and crosses only at the very end:

| Epoch | Node mean on Pali | Pali accuracy | `pi` predicted |
|---|---|---|---|
| 0 | 0.5000 | 0.0000 | 0 |
| 1 | 0.4090 | 0.0000 | 0 |
| 5 | 0.4177 | 0.0000 | 0 |
| 10 | 0.4317 | 0.0014 | 4 |
| 15 | 0.4479 | 0.0432 | 121 |
| 20 | 0.4809 | 0.3076 | 865 |

lr 0.01 would have eventually worked. It was ~50× slower than necessary.

## 6. Held-out benchmarks

Filtered to the 11 categories, Sanskrit resolved by script, unrestricted top-1
over the full 176/177-label space:

| Benchmark | Model | Accuracy | Macro-F1 | Target-3 | Replay-8 | Outside-11 |
|---|---|---|---|---|---|---|
| CommonLID | base | 0.9290 | 0.7840 | 0.3257 | 0.9543 | 1,342 |
| (n=94,274) | lr 0.01 | 0.9340 | 0.8072 | 0.4155 | 0.9708 | 1,236 |
| | lr 0.5 | 0.9767 | 0.9712 | 0.9850 | 0.9645 | 880 |
| | **lr 2.0+decay** | **0.9769** | **0.9714** | **0.9877** | 0.9634 | **763** |
| FLORES+ | base | 0.6591 | 0.7442 | 0.3257 | 0.9277 | 247 |
| (n=16,155) | lr 0.01 | 0.6856 | 0.7646 | 0.4155 | 0.9375 | 190 |
| | lr 0.5 | 0.9303 | 0.9292 | 0.9850 | 0.9374 | 34 |
| | **lr 2.0+decay** | **0.9314** | **0.9297** | **0.9877** | 0.9374 | **19** |
| WiLI-2018 | base | 0.6962 | 0.7979 | 0.3257 | 0.9811 | 37 |
| (n=15,034) | lr 0.01 | 0.7195 | 0.8129 | 0.4155 | 0.9813 | 34 |
| | lr 0.5 | 0.9817 | 0.9794 | 0.9850 | 0.9798 | 25 |
| | **lr 2.0+decay** | **0.9828** | **0.9798** | **0.9877** | 0.9796 | **21** |

Per-language F1 on CommonLID, base → lr 0.5:

| Lang | Base | lr 0.5 | Δ |
|---|---|---|---|
| `pi` | 0.0000 | 0.9929 | **+0.9929** |
| `si` | 0.5438 | 0.9814 | **+0.4376** |
| `sa` | 0.4914 | 0.9323 | **+0.4409** |
| `fr` | 0.9437 | 0.9522 | +0.0085 |
| `ta` | 0.9643 | 0.9756 | +0.0113 |
| `en` | 0.9716 | 0.9751 | +0.0035 |
| `ar` | 0.9947 | 0.9941 | −0.0006 |
| `bn` | 0.9936 | 0.9914 | −0.0022 |
| `de` | 0.9672 | 0.9646 | −0.0026 |
| `hi` | 0.9702 | 0.9526 | −0.0176 |

The `si` gain is precision recovery: the base model dumped all Sinhala-script
text into `si` (the §7 signature in `new_method`). Forgetting is mild — Hindi
−0.0176 is the worst, and out-of-set predictions fell from 1,342 to 763.

## 7. Two findings that contradict my earlier report

1. **Group balancing hurts.** `--balance group` gave Pali 0.3276 at epoch 1
   against 0.9879 unbalanced, because it down-weights exactly the abundant Pali
   data the new node needs. My earlier report listed it as a likely fix.
2. **Warm-starting the node is not the answer.** At lr 0.01, warm-start reached
   Pali 0.0004 — no better than zero-init, because LR was the binding
   constraint. It also sacrifices the clean even-split invariant for nothing.

My earlier claim that dim-16 imposed a ceiling was also wrong: 16 dimensions are
sufficient for this task.

## 8. Benchmark data-integrity issue (independent of this work)

While evaluating I found that the three benchmark files under
`new_method/data/preprocessed/` contain a **byte-identical set of 5,720
Sinhala-script texts** (3,027 `pli` + 2,693 `sin`), plus near-identical `san`
counts. Verified by SHA-256: the `pli`+`sin` text sets of `commonlid.jsonl`,
`flores_plus.jsonl` and `wili-2018.jsonl` are exactly equal.

Consequences:

- Target-3 accuracy is **identical across all three benchmarks** in every row of
  the table above (0.3257 / 0.4155 / 0.9850 / 0.9877). That is one measurement
  reported three times, not three independent ones.
- The replay-8 columns *are* genuinely different per benchmark and remain valid.
- **No train/test leakage**: 0 overlap between these benchmark rows and both
  `train_mixed_11groups.jsonl` and `val_mixed_11groups.jsonl` (SHA-256 over
  NFC-normalized text). The target-3 numbers are honest, just not independent.

This affects `new_method`'s benchmark tables in the same way, since it reads the
same files. Worth checking how the Sinhala-script rows were injected before
reporting per-benchmark target-3 numbers in the paper. I did not modify those
files.

Separately, the FLORES+ `arb_Arab` artifact documented in `new_method` §7
reproduces here exactly: accuracy 0.5000 in every phase including base, with
support 2,024 = exactly double the other languages' 1,012.

## 9. Recommended configuration

```bash
python -m data_pipeline.fasttext_continual.train \
  --init data_pipeline/models/continual/exp01/init177 \
  --train data_pipeline/datasets/finetuning/train_mixed_11groups.jsonl \
  --val   data_pipeline/datasets/finetuning/val_mixed_11groups.jsonl \
  --out   <new-run-dir> \
  --epochs 5 --lr 0.5 --batch-size 64 --seed 42
```

lr 0.5 is the best result reachable with the committed trainer, which supports
only a constant LR (0.9918 macro-F1). lr 2.0 with linear decay scored slightly
higher (0.9949) but needs the decay schedule, which the committed `train.py`
does not implement. Adding a `--decay linear` flag is the one code change worth
making.

## 10. Standing comparison to `new_method`

| | NLLB / GlotLID (softmax) | lid.176 (HS) |
|---|---|---|
| Label addition | Append zero output rows | Huffman leaf surgery |
| Init guarantee | Provably no-op, bit-identical | Invariant verified, other 175 unchanged |
| Embedding dim | 256 | 16 |
| New target labels | `pli_Sinh`, `san_Sinh` | `pi` only (`sa` already existed) |
| Script distinction | Yes, script-qualified labels | **No, bare language codes** |
| Target-3 result | ~0.96–0.99 F1 | 0.9877 mean group accuracy |

lid.176 is now competitive on target-3. The remaining structural gap is that it
predicts **bare language codes**, so Sanskrit-Sinh and Sanskrit-Deva both map to
`sa` and script is never predicted. Macro-F1 here averages 10 codes, not 11
groups (`evaluate.py:21`); group accuracy is the honest column. If the paper
needs script-qualified output, lid218e remains the better base.

## 11. Reproducing

```bash
pip install -r data_pipeline/fasttext_continual/requirements.txt
curl -L -o data_pipeline/models/continual/lid.176.bin \
  https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin

python -m data_pipeline.fasttext_continual.verify \
  --base-bin data_pipeline/models/continual/lid.176.bin \
  --data data_pipeline/datasets/finetuning/train_mixed_11groups.jsonl \
  --data data_pipeline/datasets/finetuning/val_mixed_11groups.jsonl \
  --out data_pipeline/models/continual/exp01
# then the training command in §9
```

Run artifacts live under `data_pipeline/models/continual/` (gitignored):
`exp01/` (lr 0.01 baseline), `sweep/` (constant-LR sweep), `sweep2/` (decay,
balance, warm-start), `bench/` (held-out benchmark JSON).

The decay/balance/warm-start arms were run with a scratchpad harness, since the
committed `train.py` supports neither LR decay nor warm-start. The committed
module was not modified by any of this work.
