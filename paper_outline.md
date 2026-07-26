# Paper outline — mapped to results you already have

Target: short paper (6–8 pages). Every section below already has evidence in your
notebooks. Nothing here requires a new model.

---

## 1. Introduction

The claim: **script ≠ language.** Sinhala script encodes three languages. Every
deployed LangID system collapses them into one.

Contributions (state these explicitly as a numbered list):
1. The first sentence-level LangID benchmark for Sinhala / Pali / Sanskrit in
   Sinhala script — 74,318 sentences, 5 sources, group-aware splits.
2. Evidence that current LangID systems fail completely on this task
   (macro-F1 0.18; F1 = 0.00 on Pali and Sanskrit).
3. A model comparison showing the bottleneck is **labelled data, not model
   capacity** — a 2 MB character n-gram model matches a 1.1 GB transformer.
4. A hard-case evaluation protocol (short fragments + leave-one-source-out) that
   reveals the differences full-sentence accuracy hides.

## 2. Related work
- LangID: lid.176, langdetect, CLD3, GlotLID.
- Script-vs-language confusion in low-resource LangID.
- The two corpora you build on: SiPaKosa, SiDiaC-v2.0. Cite DCS and SansinNT.

## 3. The benchmark
- Source table: name, language, size, licence, how it was obtained.
- **Say plainly that both Sanskrit sources are transliterated, not natively
  composed in Sinhala script** (DCS via aksharamukha from SLP1; SansinNT appears
  transliterated from Devanagari). Note they may not be fully independent.
- Cleaning: markup stripping, dedup (4,145 removed), min length.
- Splitting: `GroupShuffleSplit` on (label, source) pairs at book/chapter level.
  Explain *why*: splitting on label alone put all SiDiaC Pali in train.

## 4. Experimental setup
- Same split for every model. Metric: macro-F1 (state correctly — it is
  *sensitive* to the minority class, not immune to imbalance).
- Model families: off-the-shelf → char n-gram → word embeddings → char/word
  neural → transformers.

## 5. Results

### 5.1 Existing tools fail (this is your problem statement, with numbers)
| Tool | acc | macro-F1 | F1 Pali | F1 Sanskrit |
|---|---|---|---|---|
| fastText lid.176 | 0.373 | 0.181 | 0.00 | 0.00 |
| GlotLID v3 | 0.373 | 0.182 | 0.00 | 0.00 |

**Include the raw GlotLID label table.** It is your strongest single figure:
GlotLID has `pli` and `san` labels, yet assigned `sin_Sinh` to 3,005/3,027 Pali
and 1,325/1,327 Sanskrit sentences. The labels exist; they are tied to Devanagari.

### 5.2 Trained models close the gap
char n-gram 0.999 · char-BiGRU 0.997 · char-CNN 0.996 · fastText retrained 0.998 ·
XLM-R LangID fine-tuned 0.998 · word-BiGRU 0.977 · Word2Vec+LogReg 0.967 ·
GlotLID-features+head 0.970 · mBERT (broke 422 correct predictions).

Framing: **the missing piece was labelled data in this script, not model capacity.**

### 5.3 Full sentences are saturated — the real test is fragments
| Words | char n-gram | fastText | XLM-R | GlotLID+head |
|---|---|---|---|---|
| full | 0.999 | 0.998 | 0.998 | 0.970 |
| 5 | 0.987 | 0.993 | 0.979 | 0.842 |
| 3 | 0.945 | 0.967 | 0.908 | 0.746 |
| 1 | 0.679 | 0.791 | 0.662 | 0.549 |

Key finding: the ranking **inverts**. The transformer wins nothing and loses on
fragments. Character n-grams degrade most gracefully — consistent with the
diagnostic signal being sub-word orthography (e.g. Pali `-ං`, `ඤ්ඤ`; Sanskrit
conjuncts and visarga `ඃ`).

### 5.4 Cross-source generalisation (leave-one-source-out)
Baseline: DCS 0.992 · SansinNT 0.964 · SiPaKosa 0.973 · parallel 0.991 ·
**SiDiaC-v2 0.814**. Discuss why SiDiaC is hardest (OCR'd historical text,
code-mixed commentary).

### 5.5 Error analysis
Qualitative table of the ~11 sentences the baseline gets wrong. Be honest: several
are label noise or transliterated proper nouns (`" පේද්‍රික්`, `“ජේම්ස් කැමල් "`
labelled Pali). Say so — it strengthens the paper.

## 6. Limitations
Transliterated Sanskrit; SiPaKosa Sinhala under-represented in test (39 rows);
no dedicated code-mixed test set yet; sentence-level only.

## 7. Conclusion + release
Dataset, splits, and models released; recommend char n-gram / fastText as the
default preprocessing component for Sinhala-script NLP pipelines.
