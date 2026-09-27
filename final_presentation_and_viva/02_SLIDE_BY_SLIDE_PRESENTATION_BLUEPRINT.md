# CS3501 Final Presentation - Slide-by-Slide Blueprint

**Project:** Sinhala-Script Language Identification (LangID) for Sinhala, Pali, and Sanskrit  
**Target Duration:** 15–20 minutes presentation + 10 minutes Q&A/Viva  
**Total Slides:** 42 Slides  
**Format:** 16:9 Widescreen  

---

## Section 1: Introduction & Problem Context (Slides 1–7)
*Addresses: "Understanding of the Problem" (10 pts)*

### Slide 1: Title Slide
- **Header:** Sinhala-Script Language Identification (LangID) for Sinhala, Pali, and Sanskrit
- **Subheader:** Robust Foundation Model Adaptation & Continual Learning under Shared-Script Polysemy
- **Metadata:** Group 14 | Project 19 | October 2026 | Department of Computer Science & Engineering, University of Moratuwa
- **Visuals:** Project logo, University crest, clean dual-tone banner.

### Slide 2: Table of Contents
- **Layout:** 6 clean categorical cards (mirroring senior presentation style)
  1. Problem Description & Motivation
  2. Data Pipeline & Hybrid Benchmark Curation
  3. Model Building & Continual Adaptation (Leaf Surgery)
  4. Empirical Results & Analysis (Tables 1, 2, 3)
  5. Full-Stack Web Application & Annotation System
  6. Software Quality, Testing & Live Demonstration

### Slide 3: The Low-Resource Linguistic Reality
- **Key Message:** Script $\neq$ Language.
- **Points:**
  - Most Language Identification (LangID) systems treat Unicode script ranges as a proxy for language.
  - The Sinhala script is historically digraphic/trigraphic: it has been used for centuries to encode **Sinhala**, **Pali** (Theravada Buddhist canon), and **Sanskrit** (Buddhist and Ayurvedic treatises).
- **Visual:** Side-by-side comparison of 3 sentences in identical Sinhala script, showing how visual script features alone cannot distinguish them.

### Slide 4: The Core Problem: Zero-Shot Collapse of Foundation Models
- **Key Message:** Global SOTA foundation models completely fail on Sinhala-script Pali and Sanskrit.
- **Points:**
  - Evaluated on 6 SOTA models: XLM-RoBERTa, fastText LID-176, GlotLID v3, NLLB LID-218, OpenLID v2, and ConLID.
  - **Zero-Shot Result:** 0.00% F1 on `Pali-Sinh` and `Sanskrit-Sinh`.
  - Every single sentence is misclassified as modern Sinhala due to script bias.
- **Visual:** A stark bar chart showing 100% classification error / 0.00 F1 on Sinhala-script classical languages.

### Slide 5: The Challenge of Catastrophic Forgetting
- **Key Message:** Naive fine-tuning solves low-resource classification but destroys universal language capabilities.
- **Points:**
  - When standard supervised fine-tuning is performed on target languages, model parameters undergo representation drift.
  - In fastText LID-176, fine-tuning on only the 3 languages drops English F1 from **0.938** to **0.707**!
- **Visual:** Confusion flow illustration showing "New Knowledge In $\to$ Prior Global Knowledge Collapses".

### Slide 6: Research Objectives & Scope
- **Numbered Grid (01–04):**
  - **01. Tri-Lingual Benchmark Curation:** Establish the first non-contaminated 11-language hybrid benchmark spanning FLORES+, CommonLID, and WiLI-2018.
  - **02. Continual Model Adaptation:** Engineer adaptation strategies that acquire Pali-Sinh and Sanskrit-Sinh without catastrophic forgetting.
  - **03. Novel Hierarchical Softmax Leaf Surgery:** Design surgical tree grafting for FastText and foundation classifiers.
  - **04. Production-Grade Deployment:** Build a full-stack LangID platform with interactive evaluation and active-learning annotation.

### Slide 7: What We Have Built (Deliverables Overview)
- **4 Key Pillars:**
  1. *Curated Hybrid Datasets:* 15,000+ benchmark sentences across 11 languages with standardized BCP-47 labels.
  2. *Adapted SOTA Classifiers:* Continual FastText, Adapted GlotLID, ConLID, and NLLB with preserved global F1 (>0.97).
  3. *Inference & Annotation Platform:* Modern Next.js frontend + FastAPI microservice.
  4. *Automated Testing Suite:* Unit, integration, and load tests integrated into CI/CD.

---

## Section 2: Data Pipeline & Benchmark Engineering (Slides 8–14)
*Addresses: "Quality of Analysis" (30 pts) & "Appropriate use of Technology" (20 pts)*

### Slide 8: End-to-End Data Pipeline Architecture
- **Visual Flow:** Raw Data Acquisition $\to$ Normalization & Cleaning $\to$ Script-Disambiguation $\to$ Deduplication $\to$ Train/Test Partitioning.
- **Points:** Transparent multi-stage pipeline ensuring strict disjoint splits between training and evaluation corpora.

### Slide 9: Data Sources & Corpus Diversity
- **Table / Cards:**
  - *Sinhala (Modern):* CC-100, OSCAR, Wikipedia, News corpora.
  - *Pali (Sinhala script):* Chaṭṭha Saṅgāyana Tipiṭaka, Buddha Jayanti Tripitaka editions.
  - *Sanskrit (Sinhala script):* DCS (Digital Corpus of Sanskrit), SansinNT, SiDiaC-v2, and historical palm-leaf transcriptions.
  - *Devanagari Sanskrit & Global Background Languages:* Verified academic subsets.

### Slide 10: Unicode Normalization & Script Disambiguation
- **Key Technical Details:**
  - Sinhala Unicode block (`U+0D80` to `U+0DFF`) handling: Zero-Width Joiner (ZWJ, `U+200D`) and Zero-Width Non-Joiner (ZWNJ, `U+200C`) touching consonants (bandi akuru).
  - Normalization of archaic diacritics and Sanskrit-specific ligatures in Sinhala script.
- **Visual:** Before/after diagram of unicode canonical decomposition and ligature standardization.

### Slide 11: Deduplication & Data Leakage Prevention
- **Crucial Defense Slide for Viva:**
  - Strict MinHash LSH and exact n-gram matching between training sets and test benchmarks.
  - Complete document-level separation to eliminate test-set contamination.
- **Visual:** Flowchart showing deduplication filtering out overlapping texts.

### Slide 12: Standardized 11-Language Benchmark Design
- **BCP-47 Conforming Schema:** `[Language]-[Script]`
  - *Target Triad:* Sinhala (`Sinh-Sinh`), Pali (`Pali-Sinh`), Sanskrit (`San-Sinh`).
  - *Sister Classical/Modern Indo-Aryan:* Sanskrit in Devanagari (`San-Deva`), Hindi (`Hin-Deva`), Bengali (`Ben-Beng`).
  - *Dravidian Neighbor:* Tamil (`Tam-Taml`).
  - *Global Benchmarks:* English (`Eng-Latn`), French (`Fre-Latn`), German (`Ger-Latn`), Arabic (`Ara-Arab`).

### Slide 13: The Three Standard Benchmark Datasets
- **Visual:** 3 columns showcasing the benchmark splits:
  - **FLORES+ (Integrated):** Sentence-level high-quality parallel benchmark.
  - **CommonLID (Integrated):** Web-scraped realistic noisy language samples.
  - **WiLI-2018 (Integrated):** Long-form Wikipedia multilingual test suite (15,047 samples).

### Slide 14: Rehearsal Dataset Construction (The Aya Anchor Data)
- **Key Insight:** To prevent catastrophic forgetting during continual fine-tuning, we constructed an anchor rehearsal corpus from multilingual datasets (Aya / CC), preserving exemplar tokens across non-target languages.

---

## Section 3: Model Building & Continual Adaptation (Slides 15–22)
*Addresses: "Innovation / Creativity" (20 pts) & "Technology / Tools" (20 pts)*

### Slide 15: Foundation Model Landscape & Architectures Tested
- **Model Comparison Table:**
  - **FastText LID-176:** Subword n-grams + Hierarchical Softmax (126 MB, microsecond latency).
  - **GlotLID v3:** Specialized language identification over 2,100 languages.
  - **NLLB LID-218:** Meta’s No Language Left Behind classifier.
  - **ConLID:** Contrastive representation learning for low-resource LangID.
  - **OpenLID-v2:** Global open LangID model.
  - **XLM-RoBERTa Base:** Deep multilingual transformer encoder.

### Slide 16: Novel Methodology: Hierarchical Softmax Leaf Surgery
- **The Core Innovation (Highlight this for Innovation 20 pts!):**
  - Why standard retraining fails on FastText: Retraining rewrites the Huffman coding tree and scrambles output vector space.
  - **Our Solution:** Direct surgical insertion of new leaves into the hierarchical softmax binary tree.
- **Visual:** Binary tree diagram showing existing language tree preserved, with targeted branch extension for `Pali-Sinh` and `San-Sinh`.

### Slide 17: Mathematical Formulation of Leaf Surgery
- **Equations & Algorithm:**
  - Probability computation along the tree path: $P(y|x) = \prod_{j=1}^{d} \sigma(\mathbf{w}_j^\top \mathbf{x})$.
  - Freezing ancestral path weights of the background languages while computing targeted gradient updates strictly for the new leaf parameters and shared input representations.

### Slide 18: Continual Rehearsal Replay Mechanism
- **Workflow Diagram:**
  - Balanced multi-objective training: Target loss $\mathcal{L}_{\text{target}}$ + Rehearsal preservation loss $\mathcal{L}_{\text{rehearsal}}$.
  - Keeps representation drift bounded within an $\epsilon$-ball of original embeddings.

### Slide 19: Baseline Architectures for Comparison
- **Classical ML Baselines implemented from scratch:**
  - Multinomial Naive Bayes (Character 3-to-5-grams).
  - Linear Support Vector Machine (TF-IDF subwords).
  - Logistic Regression + Character n-grams.

### Slide 20: Two-Stage Hierarchical Routing Architecture
- **Diagram:**
  - Stage 1: Fast Unicode Script Gating (identifies Latin, Devanagari, Arabic, Sinhala, etc. in 0.05ms).
  - Stage 2: Fine-grained disambiguation within shared scripts (e.g. Sinhala vs Pali vs Sanskrit).
- **Advantage:** Maximum throughput with surgical accuracy.

### Slide 21: Training Environment & Hyperparameter Optimization
- **Table:** Learning rate schedules, epochs, subword dimension ($d=256$), loss convergence curves, hardware setup (CUDA GPU + high-throughput multi-core CPU inference).

### Slide 22: Convergence & Training Loss Curves
- **Visual:** Loss curves showing stable convergence without gradient explosion or representation collapse.

---

## Section 4: Empirical Results, Validation & Benchmarks (Slides 23–29)
*Addresses: "Quality of Analysis and/or Results" (30 pts - Highest Weight!)*

### Slide 23: Experimental Protocol & Metric Selection
- **Why Macro F1?**
  - Explain why standard accuracy is misleading due to class imbalances in specialized test sets.
  - Evaluation protocol: Strictly unseen test partitions across FLORES+, CommonLID, and WiLI-2018.

### Slide 24: Table 1 - Zero-Shot Benchmark Results (The Collapse)
- **Table / Heatmap:** Showing Table 1 from `Comparison Tables - Final Corrected.csv`.
- **Highlight:** 0.00% zero-shot detection on Sinhala Pali and Sanskrit by all models. Modern Sinhala F1 is falsely elevated due to false positives.

### Slide 25: Table 2 - Target-Only Fine-Tuning (The Forgetting Trap)
- **Table:** Showing Table 2.
- **Highlight:** Target languages reach 0.98–0.99 F1, BUT English and German plummet in FastText (English falls to 0.707).
- **Takeaway:** Proves the critical necessity of continual learning.

### Slide 26: Table 3 - Continual Learning / Leaf Surgery Results (The Triumph)
- **Table:** Showing Table 3.
- **Highlight:**
  - Target languages achieve state-of-the-art: Sinhala (0.976), Pali (0.988), Sanskrit-Sinh (0.989).
  - Background languages fully preserved: English (0.956), Tamil (0.974), Hindi (0.989), French (0.984), German (0.988).
  - Overall WiLI-2018 Macro F1 reaches **0.9793**!

### Slide 27: Cross-Dataset Generalization (FLORES+ vs CommonLID vs WiLI)
- **Side-by-Side Comparison:** Demonstrating model robustness on clean parallel text (FLORES+), noisy web text (CommonLID), and long-form encyclopedic text (WiLI-2018).

### Slide 28: Confusion Matrix & Error Analysis
- **Confusion Matrix Heatmap:**
  - Analyzing remaining borderline tokens between Pali and Buddhist Hybrid Sanskrit.
  - Demonstrates near-zero confusion with modern Sinhala.

### Slide 29: Computational Efficiency & Inference Latency
- **Benchmark Chart:**
  - FastText / Leaf-Surgery: **~0.12 ms / query** (CPU).
  - XLM-RoBERTa: **~18.5 ms / query** (GPU).
  - Proves production viability on commodity server hardware.

---

## Section 5: Full-Stack System Architecture & Web Application (Slides 30–35)
*Addresses: "Appropriate Use of Technology" (20 pts) & "Demonstration of Output" (10 pts)*

### Slide 30: System Architecture Diagram
- **Component Flow (Mirroring Senior Slide 36):**
  - Web UI (React/Next.js + Tailwind CSS) $\to$ REST API (FastAPI) $\to$ LangID Inference Engine (Leaf-Surgically Adapted FastText / PyTorch) $\to$ SQLite/PostgreSQL Database for Annotation Logs.

### Slide 31: Application Overview & User Roles
- **Key Features:**
  - Real-time sentence and paragraph LangID.
  - Document-level file upload analysis (.txt, .pdf, .docx).
  - Linguist & researcher annotation mode for active learning.

### Slide 32: Web UI Feature: Real-Time Prediction & Probabilities
- **Visual:** High-resolution screenshots of the Web Application showing probability bar charts for Sinhala vs Pali vs Sanskrit.

### Slide 33: Web UI Feature: Mixed-Script & Chunk-Level Highlighting
- **Visual:** Screenshot showing multi-sentence text where Pali stanzas embedded inside modern Sinhala commentary are highlighted with distinct colors.

### Slide 34: Admin & Dataset Annotation Dashboard
- **Visual:** Screenshot of the Annotation interface where linguists review low-confidence predictions, provide ground-truth tags, and trigger active-learning dataset exports.

### Slide 35: REST API & Integration Capabilities
- **Visual:** Swagger/OpenAPI documentation screenshot with `/api/v1/predict` endpoint, response payload structure, and integration guide.

---

## Section 6: Quality Assurance, Testing & CI/CD (Slides 36–40)
*Addresses: "Appropriate Use of Technology" (20 pts) & "Demonstration of Output" (10 pts)*

### Slide 36: Testing Strategy & Hierarchy
- **Pyramid Diagram:**
  - Unit Testing (isolated tokenizers, preprocessing, label encoders).
  - Model Inference Regression Testing (benchmark reproducibility).
  - API Integration Testing (HTTP endpoint contracts).
  - Stress & Latency Profiling.

### Slide 37: Backend Automated Testing with PyTest
- **Visual (Mirroring Senior Slide 37):** Terminal screenshot showing PyTest test suite execution, green pass status, and test coverage metrics.

### Slide 38: CI/CD Pipeline with GitHub Actions
- **Visual:** GitHub Actions pipeline graph showing automated linting, test execution, and deployment verification on push.

### Slide 39: Load & Stress Testing
- **Visual (Mirroring Senior Slide 40):** Locust / Apache Bench graphs showing response time distribution under 100+ concurrent requests. Sub-5ms response time sustained.

### Slide 40: Technology Stack Summary
- **Visual (Mirroring Senior Slide 41):** Icon grid categorizing:
  - *Modeling & NLP:* fastText, HuggingFace, PyTorch, Scikit-learn.
  - *Backend:* FastAPI, Pydantic, Uvicorn, Python 3.11.
  - *Frontend:* React / Next.js, Tailwind CSS.
  - *Testing & DevOps:* PyTest, GitHub Actions, Docker.

---

## Section 7: Conclusion, Future Work & Demo Transition (Slides 41–42)

### Slide 41: Summary of Contributions & Research Impact
- **Bullet Points:**
  - First public SOTA solution to the tri-lingual shared-script LangID problem.
  - Published comprehensive 11-language benchmark suite.
  - Introduced Hierarchical Softmax Leaf Surgery for continual adaptation.
  - Open-source, production-ready LangID tool for cultural heritage preservation.

### Slide 42: Live Demonstration Slide
- **Visual (Mirroring Senior Slide 43):**
  - Bold, clean slide with title: **LIVE DEMONSTRATION**.
  - Direct live URL & backup video link.
  - "Interactive walk-through of the LangID engine, document analyzer, and annotation pipeline."
