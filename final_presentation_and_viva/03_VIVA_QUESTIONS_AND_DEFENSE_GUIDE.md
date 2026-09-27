# CS3501 Final Viva & Oral Defense Preparation Guide

**Project:** Sinhala-Script Language Identification (LangID) for Sinhala, Pali, and Sanskrit  
**Target:** Final Viva Defense (Academic Evaluation Panel)  
**Department:** Computer Science & Engineering, University of Moratuwa  

---

## 1. Top 10 Anticipated Viva Questions & Model Answers

### Q1: "Why is Language Identification challenging for Sinhala, Pali, and Sanskrit? Isn't script detection enough?"
**Strong Model Answer:**
> *"Most commercial and academic LangID systems use Unicode script detection as a heuristic shortcut. For instance, if characters fall in the range `U+0D80–U+0DFF`, systems automatically label it as Sinhala. However, Sinhala script is digraphic and historically trigraphic: the entire Theravada Pali Canon (Tipiṭaka) and centuries of Sanskrit scholastic literature in Sri Lanka are written exclusively in the Sinhala script. Because the underlying phonemes, character sets, and orthographic patterns are encoded with the exact same Unicode range, script-level classifiers collapse completely. This requires deep morphological, phonotactic, and subword-level feature extraction."*

---

### Q2: "Why did you choose fastText as your primary adapted foundation model over larger transformer architectures like XLM-RoBERTa?"
**Strong Model Answer:**
> *"We benchmarked both! XLM-RoBERTa achieves excellent contextual representations, but Language Identification is a foundational first-stage pipeline component in search engines, corpus collection, and OCR systems where throughput and latency are paramount. FastText executes in ~0.12 milliseconds on CPU with a tiny memory footprint of 126 MB, whereas XLM-RoBERTa requires GPU acceleration and takes ~18.5 milliseconds per sentence (over 150x slower). FastText's subword character n-gram architecture (3-to-6-grams) is uniquely suited for morphologically rich agglutinative languages like Sinhala and inflected classical languages like Pali and Sanskrit, without the heavy computational overhead."*

---

### Q3: "What is 'Catastrophic Forgetting', and where did you observe it in your project?"
**Strong Model Answer:**
> *"Catastrophic forgetting occurs when a neural network or classifier trained on task A loses its performance on task A when fine-tuned on task B. We demonstrated this empirically in Table 2: when we fine-tuned stock fastText LID-176 solely on our 3 target languages (Sinhala, Pali, Sanskrit), it learned the target languages with >0.98 F1, but its performance on background languages dropped dramatically—for example, English F1 dropped from 0.938 to 0.707, and Tamil dropped significantly. This proved that standard fine-tuning is impractical for open-world LangID."*

---

### Q4: "Explain your innovation: What is Hierarchical Softmax Leaf Surgery, and how does it prevent forgetting?"
**Strong Model Answer:**
> *"FastText optimizes computation using a Huffman binary tree for hierarchical softmax. Normally, retraining FastText reshuffles the binary tree structure and overwrites the output matrix weights $\mathbf{W}_{\text{out}}$, causing complete catastrophic forgetting. In our Leaf Surgery methodology, we preserved the pre-existing Huffman tree and the ancestral node weights for all 176 pre-trained languages. We then surgically graft new leaf nodes for `Pali-Sinh` and `Sanskrit-Sinh` into the tree under appropriate shared parent nodes, updating only the parameters associated with the new leaves while maintaining an anchor rehearsal replay for background languages. This guarantees that pre-trained language decision boundaries remain intact while acquiring new language capabilities."*

---

### Q5: "How did you ensure there was no Data Leakage between your training and test datasets?"
**Strong Model Answer:**
> *"Data leakage prevention was one of our core experimental guarantees. First, all evaluation was conducted on three strictly independent, established benchmark datasets: FLORES+ (Integrated), CommonLID (Integrated), and WiLI-2018 (Integrated). Second, we applied MinHash LSH and exact sentence-level deduplication to eliminate any verbatim or near-duplicate sentences between our training corpus (Aya / custom corpora) and the benchmark test sets. Third, for classical Pali and Sanskrit texts, splits were created at the document and chapter level rather than random sentence shuffling, preventing stylistic or lexical leakage."*

---

### Q6: "Why did WiLI-2018 originally show blank or zero values for Arabic in Table 1?"
**Strong Model Answer:**
> *"During our deep audit of the WiLI-2018 zero-shot benchmark scripts, we discovered a label schema mismatch. FLORES+ and CommonLID use the macrolanguage code `arb` (`arb_Arab`), whereas the raw WiLI-2018 corpus uses ISO 639-3 `ara`. The original evaluation lookup dictionary lacked the `"ara": "arb_Arab"` mapping, which resulted in 0 test instances being matched for Arabic in WiLI-2018 across all models, generating a false 0.0000 F1 score. When evaluated on the true 1,000 Arabic sentences in WiLI-2018, stock fastText LID-176 achieves an F1 of 0.9985, proving the zero-shot model was never defective; it was an evaluation key mapping omission that we diagnosed and rectified."*

---

### Q7: "Why did you use Macro F1 rather than Accuracy as your primary evaluation metric?"
**Strong Model Answer:**
> *"In multi-class language identification across diverse benchmarks, class distribution is inherently imbalanced. For instance, in our WiLI-2018 benchmark, Pali has 3,027 samples while other languages have 1,000 samples. Accuracy is dominated by majority classes and can easily mask complete failure on minority classes. Macro F1 calculates the unweighted mean of F1 scores across all classes equally:
> $$\text{Macro F1} = \frac{1}{N} \sum_{i=1}^N F1_i$$
> This strictly penalizes models that fail on low-resource classical languages, ensuring our reported performance reflects true per-class generalization."*

---

### Q8: "How does your system handle code-mixed sentences or mixed scripts (e.g., Sinhala text with English words or Pali stanzas)?"
**Strong Model Answer:**
> *"Our system operates on a dual-granularity approach. For document and sentence-level inputs, the classifier outputs calibrated class probabilities. When text exhibits script boundaries (e.g. Sinhala script mixed with Latin English), our pre-segmentation pipeline splits on punctuation and script transitions, classifying individual spans independently. Furthermore, in our web application, we display confidence distribution bars so users and linguists can inspect ambiguity directly."*

---

### Q9: "What software engineering practices did you apply in developing the full-stack system?"
**Strong Model Answer:**
> *"We treated this as a production-grade software engineering project, not just a set of Jupyter notebooks. 
> 1. **Modular Architecture:** Clean separation of concerns with a FastAPI microservice backend and a Next.js responsive frontend.
> 2. **Automated Testing:** Over 40 unit and integration tests written in PyTest, covering tokenizers, data loaders, and API contracts.
> 3. **CI/CD Automation:** GitHub Actions workflow executing automated linting and test passes on every push.
> 4. **Load & Stress Testing:** Evaluated throughput under concurrent load using Locust, sustaining sub-5ms latencies."*

---

### Q10: "What are the limitations of your project, and what is your future direction?"
**Strong Model Answer:**
> *"Current limitations include sentence length sensitivity: like most subword LangID models, predictions on single words or very short phrases (<3 words) have higher variance due to sparse character n-grams. In the future, we plan to extend our leaf-surgery methodology to Buddhist Hybrid Sanskrit and Tibetan scripts, and explore integrating zero-shot calibration with compact on-device LLMs for context-aware ambiguous boundary resolution."*

---

## 2. Viva Delivery Tips & Non-Verbal Strategy

1. **Be Confident with Numbers**: Memorize your key metrics:
   - Zero-shot baseline: **0.00 F1** on Pali-Sinh and Sanskrit-Sinh.
   - Fine-tuned target accuracy: **>0.985 F1**.
   - Preserved global WiLI-2018 Macro F1: **0.9793** (over 10 languages).
   - Inference latency: **0.12 ms** on CPU.
2. **Handle Challenging Questions Gracefully**:
   - If an examiner points out an unexpected edge case: *"That is an insightful observation. In our error analysis on Slide 28, we observed that exact phenomenon between Buddhist Hybrid Sanskrit and Pali due to shared Prakrit loanwords. Here is how our confidence thresholds mitigate that..."*
3. **Smooth Speaker Transitions**:
   - Assign clear ownership of sections (e.g., Member 1: Intro & Problem; Member 2: Data Pipeline & Benchmarking; Member 3: Leaf Surgery & ML Models; Member 4: Web App, Testing & Live Demo).
