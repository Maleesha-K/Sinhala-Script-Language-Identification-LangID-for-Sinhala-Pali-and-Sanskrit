# Method and citations

## Name of the method

The proposed mitigation is **rehearsal-based fine-tuning**, also called experience replay when older examples are replayed. The model trains on new target examples together with examples representing earlier knowledge. If the eight-language texts are newly collected, describe them as rehearsal data for previously supported languages; do not claim they are the exact original pretraining examples.

## Papers that support this choice

| Paper | Relevant evidence | Scope of the citation |
|---|---|---|
| [Chaudhry et al. (2019), On Tiny Episodic Memories in Continual Learning](https://arxiv.org/abs/1902.10486) | Jointly trains on current examples and stored examples from older tasks; studies retention with small memories. | Direct support for the experience-replay principle. It does not study this Sinhala-script LID experiment. |
| [Chu, Dabre, and Kurohashi (2017), An Empirical Comparison of Domain Adaptation Methods for Neural Machine Translation](https://aclanthology.org/P17-2061/) | Section 3.3 resumes training an existing model on a mixture of in-domain and out-of-domain data. | A close NLP precedent for mixed fine-tuning. It uses translation, domain tags, and sampling choices; your implementation adapts the mixing principle. |
| [Dabre and Sumita (2019), NICT's Supervised Neural Machine Translation Systems for the WMT19 Translation Robustness Task](https://aclanthology.org/W19-5362/) | Applies mixed fine-tuning in a later translation system. | A further application of the method; not evidence that your eight-language mixture will necessarily work. |

These papers justify an established mitigation strategy. They do not establish that exactly eight languages are sufficient, guarantee zero forgetting, or make the mixing method itself novel.

## Suggested methods wording

We compare the original pretrained models with target-only and rehearsal-based adaptation. Target-only adaptation uses Sinhala, Pali, and Sanskrit written in the Sinhala script. Rehearsal-based adaptation combines the same training data with examples from eight previously supported language-script categories. This follows the experience-replay principle of training on current and older-task examples (Chaudhry et al., 2019) and the related mixed fine-tuning approach used in NLP (Chu et al., 2017). Both adaptation conditions retain the original output labels and append only missing target labels. We evaluate all conditions on the same CommonLID, FLORES+, and WiLI-2018 benchmark files using unrestricted predictions and per-category F1.

Use this wording only if you run the default independent arms. For `replay_start="target_only"`, replace the first two adaptation sentences with an explicit account of the sequential target-only-then-rehearsal stages. Report that stage 3 receives additional training.

## Model references

- [NLLB Team (2022), No Language Left Behind: Scaling Human-Centered Machine Translation](https://arxiv.org/abs/2207.04672). The relevant component is **lid218e**, not an NLLB translation transformer. [Meta's model card](https://huggingface.co/facebook/fasttext-language-identification) explicitly identifies this checkpoint as the NLLB LID release. Actual label counts are read from the downloaded checkpoint.
- [Kargaran et al. (2023), GlotLID: Language Identification for Low-Resource Languages](https://aclanthology.org/2023.findings-emnlp.410/). This bundle selects **v3** and records its exact checkpoint. The paper's original version and the v3 release are not interchangeable. [Version documentation](https://huggingface.co/cis-lmu/glotlid).
- [Foroutan et al. (2025), ConLID: Supervised Contrastive Learning for Low-Resource Language Identification](https://arxiv.org/abs/2506.15304). Uses the [EPFL checkpoint](https://huggingface.co/epfl-nlp/ConLID). This package fine-tunes it with cross-entropy; it does not claim to reproduce the authors' complete contrastive training recipe.

## What to report in the paper

Record checkpoint revisions/hashes, label mappings, source and size of every split, document grouping, seed, learning rate, optimizer, example budget, replay fraction, and whether replay starts from the base or target-only model. Report target-three and replay-eight macro F1 separately. Keep the full eleven-category table so that gains on new targets cannot conceal drops on older categories.

Retaining classifier rows keeps older predictions possible; it does not guarantee retention. Softmax training can update older classifier rows even without positive examples of those languages. Shared embeddings can also change. To claim broader multilingual retention, add held-out languages outside the replay set to a separately reported retention evaluation.

## Source data and implementation


fastText continuation uses bundled [fastText v0.9.2](https://github.com/facebookresearch/fastText/tree/v0.9.2) with narrowly documented additions in `native/continue.cc`. ConLID feature extraction and inference shapes were checked against the [official implementation](https://github.com/epfl-nlp/ConLID/blob/main/model.py). Its inference encoder detaches pooled features; the trainable implementation in this package keeps encoder gradients.
