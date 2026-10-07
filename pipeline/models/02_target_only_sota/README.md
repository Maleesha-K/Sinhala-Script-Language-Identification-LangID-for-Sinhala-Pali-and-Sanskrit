# 02: Target-Only SOTA Specialist Models (Catastrophic Forgetting)

This tier documents models adapted **strictly to target languages** (`sin_Sinh`, `pli_Sinh`, `san_Sinh`).

---

## ⚠️ The Catastrophic Forgetting Paradox
While achieving >99.5% accuracy on in-domain Sinhala, Pali, and Sanskrit, these models suffer **severe catastrophic forgetting**, losing their general-purpose multilingual capabilities on global benchmarks (FLORES+, WiLI-2018, CommonLID).

---

## 📂 Models
- `fasttext_leaf_surgery/`: Novel leaf expansion technique appending target nodes to hierarchical softmax tree.
- `conlid/`, `openlid_v3/`, `glotlid_v3/`, `nllb_lid218/`, `xlm_roberta/`: Specialist target-only fine-tuned checkpoints.
