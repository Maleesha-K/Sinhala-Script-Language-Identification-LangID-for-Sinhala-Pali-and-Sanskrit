# CS3501 Final Presentation & Viva - Grading Rubric & Strategic Analysis

**Group:** Group 14  
**Project:** Sinhala-Script Language Identification (LangID) for Sinhala, Pali, and Sanskrit  
**Evaluation Target:** Final Presentation (Slides and Viva)  
**Total Marks:** 100 Points  

---

## 1. Rubric Breakdown & Target Scoring Strategy

Based on the official LMS grading criteria for **In23-S5-CS3501**, here is the breakdown of points, what the evaluators demand for the highest tier, and our strategic alignment.

| Criterion | Max Points | Required Standard for Full Marks (Top Tier) | How Our Project Achieves Full Marks |
| :--- | :---: | :--- | :--- |
| **1. Understanding of the Problem** | **10 pts** | *Demonstrates an excellent, comprehensive understanding of the problem.* | Articulate the historical & computational challenge of **digraphic low-resource languages**: Sinhala script encodes three languages (Sinhala, Pali, Sanskrit), causing 100% zero-shot classification failure in global SOTA models (XLM-R, GlotLID, NLLB, fastText). |
| **2. Quality of Analysis and/or Results** | **30 pts** *(Highest!)* | *Exceptional analysis; results are comprehensive, insightful, and thoroughly validated.* | Present our multi-phase benchmarking: (1) Zero-shot failure discovery on 3 hybrid benchmark datasets (FLORES+, CommonLID, WiLI-2018), (2) Catastrophic forgetting analysis across 11 languages, and (3) Systematic empirical proof across 6 foundation models and classical baselines. |
| **3. Innovation / Creativity** | **20 pts** | *Outstanding innovation and creativity, significantly enhancing the project's value and uniqueness.* | Showcase our **Hierarchical Softmax Leaf Surgery** on fastText and continual rehearsal replay, non-contaminated hybrid benchmark construction, and the 2-stage script-routing architecture. |
| **4. Appropriate Use of Technology / Tools** | **20 pts** | *Excellent use of technology/tools, perfectly aligned with project needs and highly efficient.* | Full-stack pipeline: PyTorch, fastText C++ binding, HuggingFace Transformers, scikit-learn, FastAPI, React/Next.js UI, Pytest automated testing, and dataset versioning. |
| **5. Presentation** | **10 pts** | *Presentation is outstanding in organization, clarity, engagement, and professionalism.* | Clean 16:9 slide layout mirroring the senior benchmark (CoolMeal), structured narrative flow, professional data visualizations, and crisp transitions between speakers. |
| **6. Demonstration of Final Output / Product** | **10 pts** | *An excellent demonstration is provided, clearly showcasing a polished, fully functional, and effective output/product.* | Live/recorded demonstration of our Web Application & Annotation Platform: real-time LangID prediction, confidence visualizer, multi-language text analyzer, and backend API. |

---

## 2. Key Takeaways from Senior Presentation (`Coolmeal_Presentation.pdf`)

Our analysis of the seniors' 43-slide presentation revealed the structural formula that examiners reward:

1. **Clear 6-Stage Narrative Arc**:
   - `01 Problem & Context` $\to$ `02 Solution & Objectives` $\to$ `03 Data Pipeline` $\to$ `04 ML / Core Algorithms` $\to$ `05 System Architecture & Features` $\to$ `06 Comprehensive Testing & Demo`.
2. **Deep Data Pipeline Transparency (Slides 9–14)**:
   - Evaluators love seeing exactly how raw data was acquired, cleaned, validated, and formatted into clean tables.
3. **Algorithmic Step-by-Step Breakdown (Slides 15–20)**:
   - Rather than just saying "we used an ML model", they broke down the workflow into clear numbered steps with diagrams (Step 1: Data Collection $\to$ Step 2: Mapping $\to$ Step 3: Math/Calculation $\to$ Step 4: Model Training).
4. **Engineering Rigor & Multi-Level Testing (Slides 36–40)**:
   - They dedicated separate slides to **Backend Unit Testing (Pytest + GitHub Actions)**, **UI Testing**, and **Load Testing**. This proved it was not just a research script, but a production-ready software engineering project.
5. **Separation of Presentation & Live Demo (Slide 43)**:
   - Concluding the slide deck with a dedicated "DEMO" divider slide transitions smoothly into the interactive live evaluation.

---

## 3. High-Scoring Tactics for the Viva (Defense)

1. **Address Catastrophic Forgetting Early**:
   - Examiners will ask: *"Why didn't you just retrain the models from scratch or simply fine-tune them?"*
   - Answer: Standard fine-tuning on only target languages collapses background language F1 (e.g. English dropped to 0.70 in fastText). We solved this via *Hierarchical Softmax Leaf Surgery* and *Memory Rehearsal Replay*.
2. **Preempt Data Leakage Questions**:
   - Explain our strict deduplication and disjoint document-level train/validation/test splits, verifying against FLORES+, CommonLID, and WiLI-2018.
3. **Explain Metric Choice**:
   - Emphasize why **Macro F1** is strictly required rather than Accuracy: the classes have severe imbalance across long-tail classical languages.
