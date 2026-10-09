# A Benchmark and Production Platform for Sinhala-Script Language Identification
## Disambiguating Sinhala, Pali, and Sanskrit in Closed- and Open-World Contexts

**Final Project Report**  
**Department of Computer Science and Engineering**  
**University of Moratuwa, Sri Lanka**  

**Student team:** Maleesha Kumarasinghe, Vihanga Nimsara, and Nadil Kulathunge  
**Index number:** **[INSERT THE REQUIRED INDEX NUMBER]**  
**Academic year:** 2026

*Submitted in partial fulfilment of the requirements of the degree programme of the Department of Computer Science and Engineering, University of Moratuwa.*

<!-- PAGE BREAK: 1 / 17 -->

# Abstract

Language identification is commonly used to route text into multilingual search, translation, optical character recognition, and corpus-building pipelines. A script-based shortcut is unreliable for the Sinhala writing system because modern Sinhala, canonical Pali, and classical Sanskrit can all be written with Sinhala characters. This project develops a benchmark and an accompanying software platform to distinguish those three languages while retaining useful behaviour on languages written in other scripts. The benchmark contains 74,318 target-language sentences partitioned by document into training, validation, and test sets. Seven models trained from scratch are compared on full sentences and on five-word, three-word, and single-word fragments. Six multilingual model families are also evaluated in open-world settings formed from the target test set and FLORES+, CommonLID, and WiLI-2018. The reported results show that complete-sentence classification is relatively easy for the closed-world models: all seven exceed 0.984 macro-F1, with a linear support-vector machine reaching 0.9960. Single-word identification is substantially harder; multinomial Naive Bayes achieves 0.8584 macro-F1 and outperforms the other tested baselines. Off-the-shelf multilingual models fail to recognize Sinhala-script Pali and Sanskrit without adaptation. Target-only fine-tuning can then damage recognition of background languages, particularly for XLM-RoBERTa. Balanced multilingual rehearsal addresses this trade-off: adapted GlotLID v3 and NLLB LID-218 reach 0.9954 and 0.9948 macro-F1, respectively, on the FLORES+ hybrid suite. A web platform makes the classifiers available through text and document workflows with asynchronous processing, optional OCR, annotation, and model selection. The principal contribution is a reproducible evaluation of shared-script language identification and a practical architecture for applying its findings to digital collections.

# Table of Contents

| Section | Page |
|---|---:|
| Abstract and Table of Contents | 2 |
| 1. Introduction | 3 |
| 2. Literature Review | 4 |
| 3. System Models and Design | 5 |
| 3.1 Requirements and Use Cases | 5 |
| 3.2 System Architecture | 6 |
| 3.3 Logical and Process Views | 7 |
| 3.4 Database Design | 8 |
| 3.5 Dataset and Experimental Design | 9 |
| 3.6 Model Design and Selection | 10 |
| 4. Implementation | 11 |
| 4.1 Procedure and Materials | 11 |
| 4.2 Core Algorithms | 12 |
| 4.3 Main Interfaces | 13 |
| 5. Testing and Analysis | 14 |
| 5.1 Software Verification | 14 |
| 5.2 Benchmark Results and Analysis | 15 |
| 6. Conclusion and Future Work | 16 |
| References | 17 |

<!-- PAGE BREAK: 2 / 17 -->

# 1. Introduction

Language identification (LangID) assigns a language label to a piece of text. Although it is sometimes treated as a solved preliminary task, the assigned label has consequences throughout a language-processing system. Web-crawl filters use it to construct training corpora; translation services use it to select a model; digital libraries use it to catalogue and search documents. An incorrect label can therefore propagate into translation errors, misleading search results, and contaminated datasets. Surveys and large-scale web-corpus studies have documented how difficult reliable identification becomes when inputs are short, noisy, or drawn from under-represented varieties [1], [2].

The Sinhala script illustrates a specific failure mode. The Unicode Sinhala block is U+0D80–U+0DFF, but its use is not restricted to modern Sinhala. Pali Buddhist literature and classical Sanskrit can also appear in this script. Historical sources describe the longstanding role of Sinhala-script writing in Theravada textual transmission [3]. A classifier trained to associate the entire block with one national language may therefore confuse three linguistically different texts that share their visible characters. In the benchmark supplied with this project, off-the-shelf multilingual systems have zero recall for Sinhala-script Pali and Sanskrit before adaptation. This is a language-label problem, not merely a script-detection problem.

The project has two linked goals. The research goal is to determine which model families distinguish Sinhala, Pali, and Sanskrit when the available context ranges from a full sentence to a single word, and whether adaptation to this local ambiguity can preserve performance on unrelated languages. The engineering goal is to place the resulting models in a usable platform for text classification and document analysis. The system is relevant to digitised Buddhist collections, Sanskrit materials in Sinhala orthography, mixed-language commentaries, web-text cleaning, and historical document indexing.

The work proceeds in closed- and open-world settings. In the closed world, every input belongs to one of three Sinhala-script classes: **Sinh-Sinh** (Sinhala in Sinhala script), **Pali-Sinh**, or **San-Sinh**. In the open world, these classes coexist with eight background language–script classes, including Devanagari Sanskrit and several regional and global languages. This distinction matters: a highly accurate three-class model cannot safely classify arbitrary internet text unless it can first reject or route non-target inputs.

The project outcomes are a document-partitioned corpus of 74,318 target sentences, an experimental comparison of seven from-scratch classifiers, hybrid evaluation suites for six multilingual model families, an analysis of catastrophic forgetting, and a web application that exposes classification and document workflows. The report first reviews related work, then specifies requirements and design, explains the implementation, evaluates the evidence, and closes with limitations and future development. Numerical results in this report are taken from the supplied research paper; platform descriptions are grounded in the project implementation. They are kept separate so that an experimental result is not mistaken for a production-service guarantee.

<!-- PAGE BREAK: 3 / 17 -->

# 2. Literature Review

Traditional LangID systems rely heavily on character or word patterns. The fastText text-classification architecture uses subword features and efficient label prediction, which makes it attractive for large multilingual inventories [4]. GlotLID extends language coverage to low-resource languages and demonstrates the practical importance of broad training data [5]. The NLLB project similarly built language-identification components to support massively multilingual translation [6]. These systems are useful global baselines, but coverage in a label inventory does not ensure that a language is represented in every script in which it is historically written. A model may know Pali or Sanskrit in another orthography while still treating Sinhala-script input as Sinhala.

OpenLID provided an openly available multilingual dataset and model, while ConLID investigated supervised contrastive learning for low-resource identification [7], [8]. XLM-RoBERTa represents a different model family: a pretrained multilingual transformer whose shared parameters may transfer across languages [9]. The advantage of shared parameters creates a corresponding adaptation risk. If a model is fine-tuned only on three local classes, it can alter representations used by background languages. The present benchmark tests this risk explicitly instead of reporting only target-language accuracy.

Evaluation design is as important as architecture. A random sentence split can leak near-duplicate phrases from a source work into both training and test sets, particularly where formulaic or repeated liturgical text is common. The supplied research paper therefore groups sentences by document before splitting. It also tests fragment lengths because OCR output, dictionary headwords, catalogue entries, and search queries are often much shorter than a sentence. Full-sentence accuracy alone would conceal a major deployment weakness.

For broader evaluation, the project uses three external test resources. FLORES+ supplies a multilingual benchmark derived from the FLORES-101 evaluation tradition [10]. CommonLID targets language identification on web data [11]. WiLI-2018 offers a written-language identification benchmark with a different distribution [12]. Combining the held-out Sinhala-script test set with these background suites allows target recognition and global-language retention to be assessed together. It also prevents an apparently successful specialist model from being judged only within its narrow three-class setting.

This project differs from the reviewed systems in three ways. First, the linguistic distinction is within one script, so a script detector is insufficient. Second, the benchmark spans full sentences down to isolated words rather than a single convenient input length. Third, multilingual adaptation is assessed for both gains on Pali-Sinh and San-Sinh and losses on unrelated languages. The accompanying platform turns this research into a workflow with model choice, document OCR, segment-level results, and expert corrections. It is not a claim that a web interface improves model accuracy; rather, the interface supplies a route by which the measured models can be used and audited.

<!-- PAGE BREAK: 4 / 17 -->

# 3. System Models and Design

## 3.1 Requirements and Use Cases

The primary research requirement is to accept Sinhala-script text and return a language label that distinguishes Sinhala, Pali, and Sanskrit. The deployed system must also account for the fact that a document may include background languages or multiple segments. A user should be able to submit raw text, choose an available classifier, choose a segmentation strategy, and inspect each predicted segment with a confidence value. For scanned or image-based documents, the user should be able to upload a file, request text extraction or OCR, and review the extracted pages before interpreting classifications. Domain experts should be able to record corrections for a segment, while an administrator can review which corrections are suitable for future training. These functions are represented by the main use cases in Fig. 1.

```text
                   +------------------------------------------+
                   |  Sinhala-Script LangID Platform         |
                   |                                          |
Researcher/User --->  Submit text / select model            |
         |         |  Upload document / select OCR engine     |
         |         |  View segments, labels, confidence       |
         +-------->|  Correct a predicted label              |
                   |                                          |
Administrator ---->|  Review annotations / manage settings  |
                   |  Inspect usage and processing status    |
                   +------------------------------------------+
```

**Fig. 1. Main actors and use cases of the language-identification platform.**

The use cases impose non-functional requirements. The application should return a clear failure state rather than silently substituting a label when extraction or model loading fails. Long OCR and document jobs should run asynchronously so that the interface remains responsive. A user's documents, jobs, and corrections must be associated with that user and protected by authentication and authorisation checks. Classification records need provenance: model identifier, segmentation strategy, segment offsets, and timestamp should remain available for interpretation. The data pipeline must preserve document grouping between training and testing; otherwise measured accuracy can be inflated by text repetition. The evaluation should report macro-F1, because the three target classes are not equally sized and a dominant class can obscure minority-class errors.

The system boundary is deliberately narrower than a fully automatic manuscript-transcription service. The benchmark is based on clean digital text, while OCR is a separate upstream stage. A wrong OCR character can change the evidence available to the classifier, so classification confidence cannot be interpreted as an OCR-quality score. Similarly, an approved user correction is not automatically a new training example; review and data-governance steps are required before retraining. These distinctions keep the functional design aligned with the evidence available from the research paper and source implementation.

<!-- PAGE BREAK: 5 / 17 -->

## 3.2 System Architecture

The platform uses a layered architecture in which the browser interface communicates with a backend API. The frontend presents classification forms, document lists, result views, and annotation controls. The API validates requests, authenticates users, records jobs, and exposes model metadata. A model registry gives each classifier a stable identifier, display label, and loader; this prevents the interface from assuming that every model has the same output space. In the repository, the three-way baseline and several adapted multilingual models are registered separately. A task queue handles longer-running classification and OCR work, while the database stores users, documents, pages, jobs, segments, and corrections.

```text
  Browser interface (Next.js / React)
      |   text, upload, model choice, annotation
      v
  REST API and status channel (FastAPI)
      |             |                 |
      |             |                 +--> Authentication / usage rules
      |             +--> SQLAlchemy data access --> Relational database
      v
  Model registry --> classifier adapters --> baseline / adapted models
      |
      +--> Celery workers --> OCR registry --> PDF text / Tesseract / Surya
                    |
                    +--> document storage and page results
```

**Fig. 2. High-level platform architecture and principal data flows.**

Figure 2 separates the interface, API, inference, asynchronous workers, persistence, and extraction services. This separation allows new classifiers to be added behind a common prediction interface without rewriting the entire user experience. It also lets OCR and classification jobs expose queued, processing, completed, or failed states. In the codebase, a classification request persists a job before queueing work; the worker later creates classified segments. Each segment stores its text, predicted language, confidence, probability map, and character offsets. This arrangement supports both result highlighting and later annotation.

There are two model-operation contexts. A baseline classifier is appropriate when the input has already been restricted to the target triad. A multilingual model is needed when arbitrary background languages may appear. Exposing both is useful for comparison, but the interface must make their label-space difference visible. The architecture therefore maintains model metadata and a list of valid correction labels. It should not offer an English correction against a three-class model that cannot produce English.

The project uses OCR engines through an abstraction so that a document can be handled by an engine selected at upload. Direct PDF text extraction is preferable when a valid text layer exists; OCR is used where the source is an image or scanned page. The resulting text is still shown for review because errors from page segmentation, font recognition, or historical glyphs can affect the downstream prediction. This design reflects the research limitation that the benchmark metrics were measured on clean text, not on a representative corpus of degraded palm-leaf scans.

<!-- PAGE BREAK: 6 / 17 -->

## 3.3 Logical and Process Views

The implementation's main logical entities are the user, document, document page, classification job, classified segment, and annotation. A user owns documents and jobs. A document has one or more pages, each of which can carry extracted text and an extraction status. A job may be submitted from text or linked to a document. A completed job has ordered classified segments, and each segment may receive one or more proposed corrections. The model registry is a service component rather than a database table: it maps a model identifier to a loader and the classifier's supported labels. Figure 3 gives a compact class view.

```text
User 1 ---- * Document 1 ---- * DocumentPage
  |                 
  +------ * ClassificationJob 1 ---- * ClassifiedSegment
                                      |
                                      +---- * Annotation ---- 1 User

ModelRegistry ----> BaseClassifier
                       ^
                       |-- three-class scikit-learn adapter
                       |-- fastText-family adapter
                       |-- continual/adapted adapter
```

**Fig. 3. Logical relationships between persistent entities and model adapters.**

The main processing sequence begins with an authenticated request. The API checks the chosen model identifier and validates the request. It creates a job record and queues the work. A worker obtains the model through the registry, segments the input according to the selected strategy, runs prediction, writes ordered result segments, and updates the job state. The frontend then retrieves the job and presents language labels beside the original text. If a user disputes a label, a correction is attached to the relevant segment for later review. The sequence is illustrated in Fig. 4.

```text
User        Frontend          API/DB             Worker/Model
 | submit      |                |                     |
 |------------>| POST /jobs     |                     |
 |             |--------------->| validate + persist |
 |             |                |------ queue ------->|
 |             |<--- job ID ----|                     | segment + predict
 | poll/view   |--------------->|<---- save results --|
 |<-- labels --|<-- segments ---|                     |
 | correction  |--------------->| save annotation     |
```

**Fig. 4. Sequence of text classification and subsequent correction.**

The sequence view makes two failure boundaries explicit. If validation fails, no worker job should be accepted. If the worker or model fails after a job has been accepted, the persisted state should become failed rather than remaining queued indefinitely. A document follows an analogous route but introduces extraction before classification. The document text layer is read if available; otherwise OCR is applied to page images. Keeping extraction and language classification as distinguishable stages makes it possible to diagnose whether a surprising label was caused by text recognition, segmentation, or the classifier itself.

<!-- PAGE BREAK: 7 / 17 -->

## 3.4 Database Design

The database records both the operational workflow and the evidence needed to audit it. The `users` entity identifies the submitting person. `documents` stores file metadata, ownership, selected OCR engine, and upload state. `document_pages` stores page numbers, extraction method, extracted text, OCR model, and processing state. `classification_jobs` stores the chosen model, segmentation strategy, input or document association, status, token count, and completion time. `classified_segments` stores ordered pieces of text and their predictions. `annotations` records a proposed corrected language, the submitting user, review state, and whether it is valid for training. Figure 5 summarises the primary relationships.

```text
users (id PK)
  |1                  |1
  |                   +------< classification_jobs (id PK, user_id FK,
  |                               document_id FK?, model_name, status)
  |                                      |1
  +------< documents (id PK, user_id FK) | 
  |              |1                      +------< classified_segments
  |              +------< document_pages             (id PK, job_id FK)
  |                        (id PK, document_id FK)              |1
  +------------------------------------------------------------+---< annotations
                                              (id PK, segment_id FK, user_id FK)
```

**Fig. 5. Entity–relationship view of the platform's principal records.**

The schema uses generated identifiers instead of filenames or text values as primary keys. This is important because multiple users can upload files with the same name and because a text segment may recur across documents. Foreign keys make ownership and provenance explicit. The `segment_index` and character offsets allow a result to be placed back into its original input rather than existing only as an isolated prediction. A probability map is stored with each segment so that later analysis can distinguish a confident error from an ambiguous decision. For a document, the page table preserves extraction status independently of the overall file, which is necessary when only some pages fail OCR.

The annotation table intentionally separates an unreviewed correction from an approved training label. Its review fields support a human-in-the-loop process in which expert feedback can be examined before it influences a later model version. This protects against accidental or malicious changes to the benchmark. The operational database must not be treated as the benchmark's source of truth: benchmark splits are immutable research artefacts, while user-uploaded data are variable and may carry privacy or copyright restrictions.

At the storage boundary, the application should validate file type and size, restrict access to the owner or authorised administrator, and keep secrets outside the database tables exposed to ordinary users. Result retrieval should filter by user ID as well as job ID. The database design does not itself guarantee security; these rules must be enforced in the API and verified by tests. Backup and retention policies are also needed before handling sensitive archival documents in a real deployment. This report describes the implemented schema and the operational controls it implies, without claiming a completed external security audit.

<!-- PAGE BREAK: 8 / 17 -->

## 3.5 Dataset and Experimental Design

The target corpus contains 74,318 sentences in three classes. Sinhala contributes 32,263 sentences, Pali 29,317, and Sanskrit 12,738. The supplied paper reports document-level grouping before a split into 60,285 training, 6,986 validation, and 7,047 test sentences. Grouping is important because a canonical work may repeat formulaic phrases, names, or verses. If sentences from the same work appeared in both training and test sets, a model could memorise textual identity rather than learn language-specific evidence. The class distribution and split sizes are shown in Table 1.

**Table 1. Target-language corpus and document-grouped split.**

| Class | Training | Validation | Test | Total |
|---|---:|---:|---:|---:|
| Sinhala (Sinh-Sinh) | 26,675 | 2,895 | 2,693 | 32,263 |
| Pali (Pali-Sinh) | 23,490 | 2,800 | 3,027 | 29,317 |
| Sanskrit (San-Sinh) | 10,120 | 1,291 | 1,327 | 12,738 |
| **Total** | **60,285** | **6,986** | **7,047** | **74,318** |

The Sinhala data are drawn from SiPaKosa and Pali–Sinhala parallel material. Pali data include canonical and commentary text from SiDiaC-v2.0 and parallel material [13]. Sanskrit data combine the historical SansinNT collection, material from the Digital Corpus of Sanskrit, and a small SiDiaC subset [14]. The Digital Corpus of Sanskrit portion is transliterated into Sinhala script using Aksharamukha [15]. This composition offers more coverage than a single source, but source identity, domain, and orthographic origin can all become confounders. A classifier might learn the style of a collection rather than the language itself. Document grouping reduces one form of leakage; cross-source testing and additional native-script Sanskrit would further strengthen the benchmark.

The closed-world evaluation tests the same held-out target sentences at four input lengths: complete sentence, first five words, first three words, and first word. This stress test is a controlled reduction of context, not a separate corpus of naturally occurring one-word queries. Macro-F1 is computed from per-class F1 scores so that each language contributes equally. For open-world evaluation, the target test set is combined with background material for eight additional language–script categories: Sanskrit in Devanagari, Hindi, Bengali, Tamil, English, French, German, and Arabic. The paper constructs hybrid suites from FLORES+, CommonLID, and WiLI-2018. These suites allow adaptation to be evaluated against both target discrimination and retention of unrelated languages.

Dataset provenance should travel with every experiment: source collection, document/group identifier, language–script tag, processing method, split, and any transliteration flag. The distinction between language and script is particularly important here. `San-Sinh` and `San-Deva` are the same language in different scripts, whereas `Sinh-Sinh`, `Pali-Sinh`, and `San-Sinh` are different languages in one script. A pipeline that collapses either dimension would reproduce the ambiguity the project is intended to solve.

<!-- PAGE BREAK: 9 / 17 -->

## 3.6 Model Design and Selection

The model design follows the two evaluation settings rather than imposing one classifier on every input. For a collection known to contain only the three Sinhala-script target classes, a compact closed-world classifier can be trained from the target training split. The paper compares multinomial Naive Bayes, linear support-vector machine, logistic regression, XGBoost, character convolutional network, character bidirectional GRU, and fastText trained from scratch. The sparse models use character n-grams; the fastText model uses character subwords. These features are appropriate because language-specific morphology can survive when an input contains only one word. Conversely, a model that depends heavily on sentence context may lose its most informative evidence when text is truncated.

For the broader open world, an existing multilingual model supplies a global label space that a three-class classifier does not have. The paper evaluates fastText LID-176, GlotLID v3, NLLB LID-218, OpenLID, ConLID, and XLM-RoBERTa Base. Their zero-shot target failure establishes that global pretraining alone does not resolve the shared-script distinction. Adding only target-language examples can repair the local categories but may damage background recognition. To test a more conservative update, the study mixes target examples with multilingual rehearsal data from Aya [16]. Its stated objective is a balanced combination of target and rehearsal losses:

`L = α L_target + (1 − α) L_rehearsal`, with `α = 0.5`.

The loss expresses the design trade-off directly. `L_target` teaches the model to separate Sinhala, Pali, and Sanskrit in Sinhala script. `L_rehearsal` penalises loss of ability on background languages. A balanced coefficient does not guarantee preservation, so performance is measured on all eleven classes after adaptation. In particular, XLM-RoBERTa's severe target-only collapse in the reported results shows why a target-only validation score would be an inadequate model-selection criterion.

Model selection depends on the expected input. For a pre-filtered Sinhala-script collection with short fragments, the paper's evidence favours a character n-gram method such as multinomial Naive Bayes. For unrestricted multilingual ingest, an adapted model with a broad label space and a background-retention test is safer. GlotLID v3 and NLLB LID-218 have the strongest reported FLORES+ hybrid macro-F1 after rehearsal. The paper also reports a much lower inference cost for a fastText-family model than for XLM-RoBERTa on its measured hardware. These results support a practical separation between low-resource archival use and high-throughput open-world routing; they do not imply that one trained checkpoint will remain best under every OCR quality, genre, or hardware condition.

Evaluation measures include per-class precision, recall, F1, and macro-F1. Macro-F1 is the unweighted mean of class F1 values, so poor Pali or Sanskrit recognition cannot be hidden by the larger Sinhala class. Accuracy and latency remain useful operational measures, but they answer different questions. A production model should additionally report unsupported labels, low-confidence decisions, and failures caused by upstream extraction. These are proposed operational checks, whereas the numeric benchmark findings are the reported research results.

<!-- PAGE BREAK: 10 / 17 -->

# 4. Implementation

## 4.1 Procedure and Materials

Implementation began with corpus assembly and label normalisation. Sentences from the identified Sinhala, Pali, and Sanskrit sources were associated with document-level groups and a language–script tag. Sanskrit material from the Digital Corpus of Sanskrit was transliterated into Sinhala script, while native Sinhala-script sources were retained in their original orthography. The grouped split was then frozen before feature extraction or model fitting. This ordering is essential: fitting a vectoriser on the full corpus before the split would expose held-out character statistics to training, even if the final classifier never saw test labels.

The closed-world experiments used the training split for parameter fitting, the validation split for selection or early stopping, and the test split for the final comparison. Character n-gram vectorisers represent sequences of Sinhala Unicode characters rather than relying on whitespace-delimited words alone. The paper's configuration specifies 1–5 character n-grams for several classical models. Its fastText baseline uses 3–6 character subwords. Neural character models use a finite character vocabulary and embeddings. Each trained model was evaluated against identical full-sentence and truncated test variants, which makes the input-length comparison meaningful.

The open-world experiments begin with pretrained multilingual checkpoints and a common set of eleven language–script evaluation categories. The held-out target test data are combined with the official background test material of FLORES+, CommonLID, or WiLI-2018. Zero-shot performance is measured first. Adapted models are then assessed after target-only training and after training with multilingual rehearsal. This three-condition design exposes both the gain from local supervision and the cost of forgetting. The data and model artifacts should be versioned together with random seeds and preprocessing rules so that a later reproduction does not silently change the evaluation population.

The application implementation uses a Next.js/React frontend, a FastAPI backend, SQLAlchemy models, and Celery workers. The backend model registry wraps available classifiers behind a common prediction contract. The document workflow supports PDF text extraction and selectable OCR adapters, including Tesseract and Surya. Classification and OCR results are persisted with job status so that a long-running request is not tied to a single browser connection. The same repository contains frontend and backend test modules, but this report does not infer a test-pass percentage merely from their presence.

The principal materials were the project corpus, three external benchmark suites, pretrained multilingual model families, Python-based machine-learning libraries, and a local web stack. No physical manuscript scanning campaign is claimed. The primary study evaluates digital text; the OCR interface extends its accessibility but is not evidence that the paper's macro-F1 transfers unchanged to faded or damaged pages. This distinction should be preserved when demonstrating the application or reporting its potential cultural-heritage impact.

<!-- PAGE BREAK: 11 / 17 -->

## 4.2 Core Algorithms

The benchmark pipeline in Fig. 6 is organised to keep training and test evidence separate. The pseudocode shows the logical procedure rather than source code tied to one library. `group_split` must operate on source-document identifiers, and all learned text transformations must be fitted using only the training partition. The fragment variants are created from held-out test sentences after the split, so the model sees the same examples under progressively less context.

<!-- In the final Google Doc, put this pseudocode in a bordered text box using Courier New, 8 pt. -->

```text
PROCEDURE BUILD_AND_EVALUATE_TARGET_BENCHMARK(records)
    validate language–script labels and source-document IDs
    normalise Unicode consistently; preserve original provenance
    (train, validation, test) <- group_split(records, by=document_id)
    FOR each model in seven_closed_world_models DO
        fit preprocessing on train only
        train model on train; use validation for selection
        FOR length in {full_sentence, 5_words, 3_words, 1_word} DO
            test_variant <- truncate(test, length)
            predictions <- model.predict(test_variant.text)
            report per_class_F1 and macro_F1 against test_variant.labels
        END FOR
    END FOR
END PROCEDURE
```

**Fig. 6. Pseudocode for grouped closed-world training and fragment evaluation.**

The second procedure describes how an operational text request reaches a result without assuming that all models have identical labels. A user-selected model is resolved by a registry. The input is segmented and each segment is scored. The output retains offsets, probabilities, and provenance. In a real application, authentication and resource checks precede job creation, and exceptions must set a terminal failed status. The algorithm is not a claim that model confidence is calibrated; confidence should be interpreted with its model and input condition.

<!-- In the final Google Doc, put this pseudocode in a bordered text box using Courier New, 8 pt. -->

```text
PROCEDURE CLASSIFY_TEXT(user, text, model_id, strategy)
    require authenticated user and non-empty text
    model_info <- registry.lookup(model_id)
    require model_info exists and checkpoint is available
    job <- save_job(user, model_id, strategy, status=QUEUED)
    enqueue(job.id)

WORKER PROCESS(job.id)
    set job.status = PROCESSING
    TRY
        spans <- segment(job.input_text, job.strategy)
        classifier <- registry.load(job.model_id)
        FOR each ordered span DO
            label, confidence, probabilities <- classifier.predict(span.text)
            save_segment(job.id, span.offsets, label,
                         confidence, probabilities)
        END FOR
        set job.status = COMPLETED
    CATCH error
        record safe diagnostic; set job.status = FAILED
    END TRY
END WORKER
```

**Fig. 7. Pseudocode for asynchronous segment-level inference.**

Both algorithms preserve traceability. The benchmark records which split and input length produced a score; the service records which model and segmentation method produced each visible label. This matters when a single-word result differs from a full-sentence result or when an OCR correction changes the input text. A reproducible research pipeline and an auditable user workflow are complementary, not interchangeable.

<!-- PAGE BREAK: 12 / 17 -->

## 4.3 Main Interfaces

The main interface is a text-classification workspace. The user enters or pastes text, selects a model, chooses a segmentation strategy, and submits a job. After processing, the view shows each segment with its predicted language and confidence. A model list should disclose whether an option is the three-class baseline or an adapted multilingual classifier, because that choice changes what labels the user can reasonably expect. The result view should preserve the original text order and make low-confidence or disputed segments easy to find.

**[Insert an actual screenshot of the running text-classification page here. The screenshot should show the input, model selector, and resulting labelled segments.]**

**Fig. 8. Text-classification interface showing model selection and segment-level results.**

The document workspace accepts a file and an OCR-engine choice. A document list presents processing state; a document detail page displays page-level extracted text and classification output. This is a practical requirement rather than a cosmetic feature. If a scanned page produces poor text, an expert needs to see the extraction before trusting the language label. Page numbers and statuses help localise errors to individual pages rather than treating an entire file as an indivisible success or failure.

**[Insert an actual screenshot of the running document detail page here. The screenshot should show a page, extracted text, processing status, and any language annotation controls.]**

**Fig. 9. Document-processing interface with extracted text and review controls.**

The correction flow attaches a proposed language label to a specific classified segment. The user can add a comment, and an administrator can review whether the correction is suitable for training. This is especially useful for mixed-language commentaries where nearby segments may switch between Sinhala explanation and Pali or Sanskrit quotation. Corrections should remain linked to the original model output, not overwrite it, because the difference between prediction and expert judgement is valuable error-analysis evidence.

Interface behaviour must also make asynchronous states understandable. A queued job is not a missing result; a failed OCR page should not be presented as an empty page; an unavailable model should be visibly unavailable before submission. The implementation has separate pages for classification jobs, documents, annotations, usage, and administration. For the final formatted report, the two required screenshots should be captured from the actual running project build. The text above specifies what those images should demonstrate; no screenshot has been fabricated for this Markdown draft.

<!-- PAGE BREAK: 13 / 17 -->

# 5. Testing and Analysis

## 5.1 Software Verification

Software verification covers the paths that could change or misrepresent a language decision. At unit level, the model adapters should return a valid label, confidence, and probability representation for supported inputs; segmentation should preserve text order and offsets; and model lookup should reject unknown identifiers. API-level tests should check authentication, user ownership, invalid input, unavailable checkpoints, job creation, and retrieval of ordered segments. Document tests should exercise successful text extraction, OCR-engine selection, per-page failure, and a mixed success/failure document. Annotation tests should verify that a user can correct an owned segment, cannot change another user's record, and cannot bypass administrator review to mark a correction as training-ready.

**Table 2. Core software test cases and acceptance criteria.**

| Test area | Representative input or action | Required result |
|---|---|---|
| Text validation | Empty text or unknown model ID | Rejected before enqueueing |
| Model registry | Registered model with missing checkpoint | Reported unavailable; no false result |
| Segmentation | Sentence, paragraph, full-text selection | Ordered spans and valid character offsets |
| Job lifecycle | Successful and failing worker tasks | Terminal completed or failed state |
| Authorisation | Access to another user's job/document | Denied without exposing content |
| OCR | Page with and without readable text layer | Extraction method recorded per page |
| Annotation | User correction followed by review | Prediction retained; review state recorded |

The repository includes backend unit and integration test modules for classification, documents, authentication, users, OCR engines, annotations, usage, administrative functions, resilience, and database integrity, as well as a frontend test setup. These files show intended verification coverage. This report does **not** present a pass count or coverage percentage for them, because no validated execution log was supplied with the paper and the available local Python environment did not run the suite. That distinction is important: a test file is evidence of a test case, not evidence that the current build passed it. Before final deployment, the suite should be executed in a locked environment and its command, dependency versions, date, failures, and coverage report archived with the release.

Security testing should include request authentication, object ownership, upload validation, and attempted access to administrator functions. Performance testing should measure API acceptance latency separately from worker completion time, since queueing can make a request appear fast while the actual job is slow. Failure testing should include Redis unavailability, database errors, OCR timeout, malformed PDFs, model load failure, and duplicate job submissions. For each scenario, the expected result is a recoverable, visible state with no silent language prediction. These are system acceptance criteria, not results of a completed external audit.

The machine-learning tests are reported separately in Section 5.2. They use held-out target sentences and three hybrid suites rather than the application test fixtures. A web UI that passes its unit tests does not establish scientific generalisation; conversely, a high macro-F1 does not establish secure or reliable service operation. Both kinds of evidence are required for a responsible release.

<!-- PAGE BREAK: 14 / 17 -->

## 5.2 Benchmark Results and Analysis

All seven from-scratch models exceed 0.984 macro-F1 on full target-language sentences, but their rankings change when context is removed. Table 3 reproduces the supplied paper's held-out results. The linear SVM leads on full sentences at 0.9960, while multinomial Naive Bayes leads the single-word condition at 0.8584. The difference indicates that a model selected only by full-sentence performance may be unsuitable for catalogue headwords, short OCR fragments, or search terms. Character n-grams can preserve inflectional evidence when sentence-level syntax disappears.

**Table 3. Closed-world macro-F1 on the held-out target test set.**

| Architecture | Full sentence | 5 words | 3 words | 1 word |
|---|---:|---:|---:|---:|
| Multinomial Naive Bayes | 0.9947 | 0.9782 | 0.9520 | **0.8584** |
| fastText from scratch | 0.9958 | 0.9768 | 0.9416 | 0.8027 |
| Character CNN | 0.9950 | 0.9749 | 0.9388 | 0.7654 |
| Character BiGRU | 0.9948 | 0.9710 | 0.9255 | 0.6916 |
| Linear SVM | **0.9960** | **0.9801** | **0.9532** | 0.6099 |
| Logistic regression | 0.9955 | 0.9780 | 0.9482 | 0.6054 |
| XGBoost | 0.9842 | 0.9554 | 0.9102 | 0.5891 |

In open-world zero-shot testing, the pretrained models do not identify Sinhala-script Pali and Sanskrit as separate classes. Target-only adaptation repairs local labels but produces very different background outcomes. XLM-RoBERTa's FLORES+ hybrid macro-F1 falls to 0.1170 after target-only fine-tuning, whereas rehearsal raises it to 0.8740. The model's strong target performance in the collapsed condition is therefore misleading when viewed in isolation. Table 4 summarises the macro-F1 reported for the three hybrid suites after rehearsal; the values are rounded to three decimals here.

**Table 4. Open-world macro-F1 after multilingual rehearsal.**

| Model | FLORES+ | CommonLID | WiLI-2018 |
|---|---:|---:|---:|
| XLM-RoBERTa Base | 0.874 | 0.838 | 0.825 |
| fastText LID-176 | 0.940 | 0.949 | 0.979 |
| ConLID | 0.987 | 0.946 | 0.969 |
| GlotLID v3 | **0.995** | 0.969 | 0.978 |
| NLLB LID-218 | 0.995 | **0.970** | 0.978 |
| OpenLID | 0.851 | 0.776 | 0.802 |

The paper reports 0.12 ms per sentence on a commodity CPU for adapted fastText-family models, compared with approximately 18.52 ms per sentence and more than 1.2 GB of VRAM for XLM-RoBERTa on an NVIDIA A100. Hardware and batching differ, so these figures should be used as indicative deployment profiles rather than a universal speed ratio. More importantly, the reported results concern clean digital text. They do not measure the combined OCR-plus-LangID error rate, calibration under historical fonts, or accuracy on every language outside the eleven-class suite. Those remain evaluation gaps.

<!-- PAGE BREAK: 15 / 17 -->

# 6. Conclusion and Future Work

This project addresses a concrete language-identification failure: the Sinhala script is shared by modern Sinhala, canonical Pali, and classical Sanskrit, but general-purpose models often act as if the script implied only Sinhala. The supplied research paper establishes a document-grouped target benchmark of 74,318 sentences and evaluates both closed-world classification and open-world adaptation. The central result is not merely that a classifier can separate three languages on full sentences. It is that performance changes sharply with input length and with the surrounding label space. A linear SVM achieves 0.9960 macro-F1 on complete sentences, yet multinomial Naive Bayes is substantially stronger on isolated words. Unadapted multilingual models miss Sinhala-script Pali and Sanskrit; target-only tuning can then destroy unrelated-language performance. Balanced multilingual rehearsal offers a better compromise, with GlotLID v3 and NLLB LID-218 reaching approximately 0.995 macro-F1 on the reported FLORES+ hybrid evaluation.

The production platform connects these findings to real workflows. It exposes multiple model families, persists text-classification jobs and segment-level evidence, supports PDF extraction and optional OCR, and permits expert corrections subject to review. Its layered design keeps the browser, API, workers, model adapters, and database distinct. That separation makes future models and OCR engines easier to introduce and makes errors more diagnosable. The software does not eliminate the scientific limitations of the benchmark: a clean-text score should not be presented as proven accuracy on faded manuscripts, noisy OCR, or a much larger collection of world languages.

The most important next step is an end-to-end evaluation on genuinely scanned documents. This should sample different ages, fonts, page qualities, and genres, and report extraction accuracy and LangID accuracy both separately and together. A second priority is more native Sinhala-script Sanskrit data. The supplied paper notes that 4,684 Sanskrit sentences were transliterated from another script; additional original-script sources would reduce reliance on synthetic orthographic conversion. A third priority is cross-source and cross-document evaluation that tests whether a model generalises beyond familiar collections and formulaic passages. Confidence calibration and an explicit abstention option would make uncertain predictions safer for archivists than a forced label.

For the platform, a release-quality verification cycle should run the unit and integration suites in a pinned environment, record reproducible pass/fail evidence, and carry out security and load testing on the complete OCR-to-classification path. Expert-approved annotations can form a carefully governed candidate pool for future training, but they should be deduplicated, checked for consent and provenance, and kept separate from frozen benchmark test sets. Rehearsal data should likewise be curated so that adaptation does not silently privilege a few background languages. These steps would transform the present benchmark and prototype into a more reliable digital-humanities service while preserving the report's core principle: language and script are related, but they are not the same label.

<!-- PAGE BREAK: 16 / 17 -->

# References

[1] T. Jauhiainen, M. Lui, M. Zampieri, T. Baldwin, and K. Lindén, “Automatic language identification in texts: A survey,” *Journal of Artificial Intelligence Research*, vol. 65, 2019.

[2] I. Caswell, T. Breiner, D. van Esch, and A. Bapna, “Language ID in the wild: Unexpected challenges on the path to a thousand-language web text corpus,” in *Proc. 28th Int. Conf. Computational Linguistics*, 2020, pp. 6588–6608.

[3] E. W. Adikaram, *The Early History of Buddhism in Ceylon*. Migoda, Ceylon: D. S. Puswella, 1946.

[4] A. Joulin, E. Grave, P. Bojanowski, and T. Mikolov, “Bag of tricks for efficient text classification,” in *Proc. 15th Conf. European Chapter of the ACL*, vol. 2, 2017, pp. 427–431.

[5] A. H. Kargaran, A. Imani, F. Yvon, and H. Schütze, “GlotLID: Language identification for low-resource languages,” in *Findings of EMNLP 2023*, 2023, pp. 6155–6218.

[6] M. R. Costa-jussà *et al*., “No language left behind: Scaling human-centered machine translation,” arXiv:2207.04672, 2022.

[7] L. Burchell, A. Birch, N. Bogoychev, and K. Heafield, “An open dataset and model for language identification,” in *Proc. 61st Annual Meeting of the ACL*, vol. 2, 2023, pp. 865–879.

[8] N. Foroutan, J. Saydaliev, G. Kim, and A. Bosselut, “ConLID: Supervised contrastive learning for low-resource language identification,” in *Proc. 19th Conf. European Chapter of the ACL*, vol. 1, 2026, pp. 6693–6708.

[9] A. Conneau *et al*., “Unsupervised cross-lingual representation learning at scale,” in *Proc. 58th Annual Meeting of the ACL*, 2020, pp. 8440–8451.

[10] N. Goyal *et al*., “The FLORES-101 evaluation benchmark for low-resource and multilingual machine translation,” *Transactions of the Association for Computational Linguistics*, vol. 10, pp. 522–538, 2022.

[11] P. O. Suarez *et al*., “CommonLID: Re-evaluating state-of-the-art language identification performance on web data,” in *Proc. 64th Annual Meeting of the ACL*, vol. 1, 2026, pp. 33063–33080.

[12] M. Thoma, “The WiLI benchmark dataset for written language identification,” arXiv:1801.07779, 2018.

[13] N. Jayatilleke and N. de Silva, “SiDiaC: Sinhala diachronic corpus,” in *Proc. 39th Pacific Asia Conf. Language, Information and Computation*, 2025, pp. 511–527.

[14] O. Hellwig, “DCS—the Digital Corpus of Sanskrit,” in *Proc. 17th World Sanskrit Conf.*, 2010.

[15] V. Rajan, “Aksharamukha: Asian script converter,” 2023. [Online]. Available: https://aksharamukha.appspot.com/. [Accessed: Oct. 8, 2026].

[16] S. Singh, F. Vargus, D. D’souza, *et al*., “Aya dataset: An open-access collection for multilingual instruction tuning,” arXiv:2402.06619, 2024.

<!-- PAGE BREAK: 17 / 17 -->
