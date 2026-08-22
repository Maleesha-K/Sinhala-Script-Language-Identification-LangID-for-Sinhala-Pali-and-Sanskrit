# XLM-RoBERTa Fine-tuning Log & Challenges

This document outlines the various approaches we took to fine-tune the `papluca/xlm-roberta-base-language-detection` model to add support for Sinhala, Pali, and Sanskrit, and documents why the initial attempts failed.

## Goal
To take an existing 20-language identification model and expand its classification head to 25 languages, specifically teaching it Sinhala (`si`), Pali (`pi`), and Sanskrit (`sa`), without losing its ability to identify the original 20 languages.

---

## Approach 1: Full Model Fine-Tuning
**Method:** We loaded the base model, replaced the classification head with a new 25-label linear layer, and attempted to train all 270M parameters of the model using standard Hugging Face `Trainer`.

**Result:** **FAILED (Out of Memory - OOM)**
- **Why it failed:** Updating all 270M parameters requires storing the model weights, gradients, and optimizer states (like Adam moments) in VRAM. This vastly exceeded the memory limits of our hardware (4GB-15GB VRAM limit on Colab), resulting in immediate CUDA Out of Memory errors before the first epoch could finish.

---

## Approach 2: LoRA (Low-Rank Adaptation)
**Method:** To solve the memory issue, we used the `peft` library to implement LoRA. We froze the entire base transformer model and injected tiny, trainable adapter matrices into the attention mechanism (`query` and `value`). We also configured PEFT to keep the `classifier` module fully trainable (`modules_to_save=["classifier"]`) so it could learn the new 25-language mappings.

**Result:** **FAILED (Catastrophic Forgetting)**
- **Why it failed:** While the memory issue was completely solved, the model suffered from severe catastrophic forgetting. The training dataset *exclusively* contained text for Sinhala, Pali, and Sanskrit. Because the `classifier` head was fully trainable, the Cross-Entropy loss heavily penalized the model whenever it produced logits for any of the other 20 languages. Without seeing any negative examples of English, French, Arabic, etc., the model actively destroyed the weights for those languages, pushing them to zero. When benchmarked, accuracy on the original languages dropped to 0%.

---

## Approach 3: High-Capacity LoRA
**Method:** Suspecting that the model simply didn't have enough trainable parameters to learn the new languages without overwriting the old ones, we increased the LoRA capacity. We increased the rank (`r`) from 16 to 64, and expanded the `target_modules` to include all linear layers (`query`, `key`, `value`, `dense`). 

**Result:** **FAILED (Catastrophic Forgetting)**
- **Why it failed:** Increasing the learning capacity did not solve the root mathematical problem. The classification head was still fully trainable, and the dataset still lacked examples of the original 20 languages. The optimizer continued to aggressively erase the weights of the unseen languages to minimize the loss on the Sinhala, Pali, and Sanskrit data.

---

## Approach 4: LoRA with Rehearsal Data (Current Plan)
**Method:** To solve catastrophic forgetting without discarding LoRA, we will use **Rehearsal (Data Mixing)**. We will mix a representative sample of data from the original languages into the training set alongside Sinhala, Pali, and Sanskrit.

**Expected Outcome:** By continually showing the model examples of the original languages during training, the Cross-Entropy loss will actively protect their weights in the classification head. The model will learn to map the new scripts to the new labels while keeping the old mappings strictly calibrated.
