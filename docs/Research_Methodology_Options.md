# Research Methodology: ACL Paper Options

As we prepare our paper for ACL, we need to decide on the core narrative and methodology for evaluating our models. We have two primary paths we can take. Below is a detailed breakdown of how each option impacts what we train on, how we structure the paper, and what our final conclusions will be.

---

## Option 1: Continual Learning & Adaptation (Our Current Approach)
**The Concept:** Train our baselines strictly on the 3 Sinhala-script languages to prove disambiguation is possible. Then, take pre-trained global SOTA models and use engineering tricks (LoRA, Head Extension, Two-Stage Routing) to teach them the new languages *without* forgetting the global ones.

### 1. What Do We Train On?
*   **Baselines (Phase 1):** You train your CNNs, Naive Bayes, and SVMs **only** on your custom 3-language dataset (Sinhala, Pali, Sanskrit). 
*   **SOTA Models (Phase 2):** You take pre-trained global models (that already know 100 languages) and apply adaptation strategies (like Two-Stage Routing or LoRA). You train these adaptations using primarily your 3-language dataset to teach the model the new dialects without touching its core global knowledge.

### 2. How to Align the Research Paper Structure
If we choose this option, the paper reads like an "Advanced Systems Engineering" paper:
1.  **Introduction:** State the problem (Sinhala script is overloaded).
2.  **Experiment 1 (Closed-World):** We test baselines on just the 3 target languages to prove that character n-grams can solve the disambiguation problem better than transformers on short fragments.
3.  **Experiment 2 (Open-World):** We acknowledge that in the real world, models must also classify English and Tamil. We show that standard fine-tuning causes *catastrophic forgetting*. We then introduce our 5 mitigation strategies (Routing, LoRA, etc.).
4.  **Results:** Show how our adapted SOTA models achieve 0.97+ F1 on the Hybrid Benchmarks.

### 3. The Final Conclusion
**"We successfully solved a critical script-ambiguity problem for historical texts. More importantly, we demonstrated that utilizing Parameter-Efficient Fine-Tuning (PEFT) and architectural routing allows massive multilingual transformers to learn rare dialects without catastrophically forgetting their global language capabilities."**

### PROS & CONS
*   **Pros:** Very high novelty for ACL (Continual Learning is a hot topic); computationally cheap (no massive 11-language training required); highly practical for industry deployment.
*   **Cons:** Requires complex explanations of engineering patches (C++ edits, LoRA); reviewers might question why Phase 1 and Phase 2 use different datasets.

---

## Option 2: Joint Multilingual Training
**The Concept:** We combine our custom Sinhala/Pali/Sanskrit data with thousands of rows of English, French, Tamil, etc., to create a massive 11-language training dataset. We train all models on this exact dataset.

### 1. What Do We Train On?
*   **Data Preparation:** You must heavily engineer a massive unified dataset. You take your Sinhala/Pali/Sanskrit data and combine it with English, Arabic, Tamil, etc., from FLORES+ to make an 11-language dataset. You must carefully balance the row counts so the model doesn't become biased.
*   **Baselines & SOTA:** You train your Naive Bayes, CNNs, and fine-tune your Transformers simultaneously on all 11 languages at once.

### 2. How to Align the Research Paper Structure
If we choose this option, the paper reads like a "Mathematical Capacity & Architecture" paper:
1.  **Introduction:** State the problem (Multilingual models struggle when microscopic script differences are mixed with macroscopic global languages).
2.  **Dataset Construction:** Detail how you built and carefully balanced the massive 11-language corpus.
3.  **Experiment 1 (Capacity Limits):** We test all 13 models on the 11-language dataset to see which architectures completely fail when forced to learn so many diverse classes.
4.  **Experiment 2 (Fragment Stress Testing):** We test the surviving models on 1-word and 3-word fragments across all 11 languages to see which architecture is the most robust.

### 3. The Final Conclusion
**"We demonstrate that when forced to classify both macro-languages (Arabic vs English) and micro-dialects (Pali vs Sanskrit in the same script), large transformers maintain the mathematical capacity to handle 11 languages. However, on short text fragments, character n-gram models remain vastly superior, proving that subword tokenizers are inadequate for fine-grained historical script disambiguation in a highly multilingual space."**

### PROS & CONS
*   **Pros:** Methodological purity (every model is trained and tested on the exact same 11-language dataset); very easy to compare models directly against each other.
*   **Cons:** A data engineering nightmare (you will spend weeks fixing class imbalances); training CNNs on 11 languages takes massive GPU power; "training a classifier on 11 languages" is less novel to ACL reviewers than "solving catastrophic forgetting."

---

### Summary Recommendation
If our goal is to publish at **ACL**, Option 1 is highly recommended. It positions the paper not just as a "Dataset" paper, but as an "Advanced Systems Engineering" paper that solves Catastrophic Forgetting for low-resource script dialects.
