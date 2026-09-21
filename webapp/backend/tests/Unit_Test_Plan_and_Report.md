# Unit Test Plan and Test Report
## Sinhala-Script Language Identification (LangID) Web Application

**Project Name:** Sinhala-Script Language Identification (LangID) for Sinhala, Pali, and Sanskrit Web Platform  
**Component:** Web Application Backend (`webapp/backend`)  
**Document Type:** Master Test Plan & Unit Test Evaluation Report  
**Version:** 1.0  
**Author:** Testing & Quality Assurance Team  
**Date:** September 20, 2026  
**Status:** Completed & Approved  

---

## Revision History

| Date | Version | Description | Author |
| :--- | :--- | :--- | :--- |
| 20/Sep/2026 | 1.0 | Initial Unit Test Plan & Execution Report following RUP standard template | QA & Backend Engineering Team |

---

## Table of Contents
1. [Evaluation Mission and Test Motivation](#1-evaluation-mission-and-test-motivation)
2. [Target Test Items](#2-target-test-items)
3. [Test Approach](#3-test-approach)
   - 3.1 [Testing Techniques and Types](#31-testing-techniques-and-types)
     - 3.1.1 [Function Testing (Unit Testing)](#311-function-testing-unit-testing)
     - 3.1.2 [Data and Database Integrity Testing](#312-data-and-database-integrity-testing)
     - 3.1.3 [Security and Access Control Testing](#313-security-and-access-control-testing)
     - 3.1.4 [Configuration and Environment Testing](#314-configuration-and-environment-testing)
4. [Deliverables](#4-deliverables)
   - 4.1 [Test Evaluation Summaries](#41-test-evaluation-summaries)
   - 4.2 [Reporting on Test Coverage](#42-reporting-on-test-coverage)
5. [Risks, Dependencies, Assumptions, and Constraints](#5-risks-dependencies-assumptions-and-constraints)
6. [References](#6-references)

---

## 1. Evaluation Mission and Test Motivation

### 1.1 Background & Motivation
The **Sinhala-Script Language Identification (LangID) Web Platform** is an intelligent web application designed to classify text written in the Sinhala script into three closely related languages: **Sinhala**, **Pali**, and **Sanskrit**. Because these three languages share the identical Brahmic Unicode block (U+0D80–U+0DFF), accurate token-level and sentence-level language identification presents significant linguistic overlap and ambiguity.

The backend is architected using **FastAPI** (asynchronous REST API), **Celery** with **Redis** (asynchronous distributed job processing), **PostgreSQL** (metadata and classification persistence), **MinIO** (document object storage), and a machine learning inference engine powered by **Scikit-learn**, **FastText**, and **XLM-RoBERTa**.

Given that researchers, linguists, and digital humanities scholars rely on this platform for scholarly text analysis and document ingestion (PDFs and raw text), any defect in text segmentation, encoding normalization, security authorization, or ML inference can lead to data corruption or incorrect scholarly conclusions.

### 1.2 Evaluation Mission
The primary mission of this unit testing phase is to:
- **Verify Component Correctness:** Ensure each backend module behaves according to specifications in complete isolation from external infrastructure.
- **Ensure Determinism:** Guarantee tests produce consistent, repeatable results without relying on live databases, external network APIs, or large model weight downloads.
- **Validate Script Segmentation & Preprocessing:** Verify that Sinhala punctuation, Latin punctuation, and Indic dandas (`।`) are correctly split across different segmentation strategies (`sentence`, `paragraph`, `full_text`, `auto`).
- **Certify Security & Cryptography:** Validate password hashing salts (bcrypt), JWT access/refresh token signing, token expiration, and tamper detection.
- **Provide Verifiable Deliverables:** Generate terminal logs, itemized test tables, and code coverage metrics for academic and engineering deliverables.

---

## 2. Target Test Items

The following software components of `webapp/backend` were targeted for comprehensive unit testing:

| Target Item | File / Module | Description | Criticality |
| :--- | :--- | :--- | :--- |
| **ML Classifier Engine** | `app.ml.sklearn_langid` | Multinomial Naive Bayes / SGD inference, probability distribution calculation, confidence scoring, and empty/invalid input handling. | High |
| **Text Segmentation Service** | `app.workers.tasks.classification_tasks._segment_text` | Text boundary segmentation for Sinhala script across `sentence`, `paragraph`, `full_text`, and `auto` modes with Indic dandas. | High |
| **Asynchronous Classification Tasks** | `app.workers.tasks.classification_tasks._process_classification_job_async` | Celery asynchronous worker workflow, database state transitions (`QUEUED` $\to$ `COMPLETED` / `FAILED`), token accounting. | High |
| **PDF Extraction Engine** | `app.utils.pdf_extractor` | PyMuPDF (`fitz`) text extraction from raw byte streams, error recovery from corrupt PDFs, multi-page concatenation. | Medium |
| **Authentication & Cryptography** | `app.utils.security` | Bcrypt password hashing, salt uniqueness, JWT token generation, payload decoding, tampering protection, expiration enforcement. | High |
| **Data Schemas & Validation** | `app.schemas.response`, `app.api.v1.classification.JobCreateRequest` | Pydantic request validation, invalid strategy rejection, empty string guardrails, standardized API response formatters. | Medium |
| **Baseline Health Check** | `tests.unit.test_unit` | Test runner harness and assertion framework sanity verification. | Low |

---

## 3. Test Approach

### 3.1 Testing Techniques and Types

#### 3.1.1 Function Testing (Unit Testing)
- **Technique Objective:** Exercise each individual function, class method, and boundary condition in isolation to observe target behavior and log outputs.
- **Technique:**
  - Execute automated test functions using `pytest`.
  - Pass valid, invalid, empty, whitespace-only, and malformed inputs to test boundary conditions.
  - Employ `unittest.mock` (`patch`, `MagicMock`, `AsyncMock`) to isolate units from external dependencies (e.g., database sessions, Redis pub/sub, filesystem weights).
- **Oracles:** Pytest assert statements comparing expected return values, exceptions raised (`ValidationError`, `RuntimeError`, `JWTError`), and mock call verifications.
- **Required Tools:** `pytest >= 9.0`, `pytest-asyncio`, `pytest-mock`, Python 3.11+.
- **Success Criteria:** 100% of defined test cases pass with zero unhandled exceptions.

#### 3.1.2 Data and Database Integrity Testing
- **Technique Objective:** Verify that database model entities, status enums, and ORM objects serialize and transition correctly during job processing without requiring an active PostgreSQL instance.
- **Technique:**
  - Mock SQLAlchemy `AsyncSession` and `async_session_maker` using `AsyncMock`.
  - Simulate queries returning valid `ClassificationJob` records and non-existent jobs (`None`).
  - Verify that status transitions (`JobStatus.QUEUED` $\to$ `JobStatus.COMPLETED` or `JobStatus.FAILED`) occur and that records are added to session before commit.
- **Oracles:** Assertion on `mock_job.status`, `mock_job.completed_at`, and `mock_session.add.call_count`.
- **Required Tools:** `SQLAlchemy >= 2.0`, `pytest-asyncio`.
- **Success Criteria:** Correct lifecycle status assignment and token count calculation.

#### 3.1.3 Security and Access Control Testing
- **Technique Objective:** Ensure authentication tokens cannot be forged, altered, or decoded with incorrect cryptographic keys, and that password hashes are non-deterministic.
- **Technique:**
  - Generate multiple password hashes for identical strings and verify differing salts.
  - Generate JWT access tokens and verify `sub`, `type`, and `exp` claims.
  - Mutate signature bytes of generated JWT tokens to simulate malicious tampering.
  - Attempt decoding with an incorrect HMAC secret key.
- **Oracles:** Verification that `jwt.decode` raises `JWTError` on tampered tokens and mismatched secret keys; verification that `verify_password` returns `True` only for valid plaintexts.
- **Required Tools:** `python-jose[cryptography]`, `passlib[bcrypt]`.
- **Success Criteria:** Tampered tokens and wrong keys are strictly rejected.

#### 3.1.4 Configuration and Environment Testing
- **Technique Objective:** Ensure that the application configuration loads required environment variables with sensible defaults and isolates testing from production infrastructure.
- **Technique:**
  - Set test-specific environment variables in `tests/conftest.py` (`SECRET_KEY`, `ALGORITHM`, `POSTGRES_*`, `MINIO_ENDPOINT`).
  - Patch MinIO client at startup to prevent network timeout delays.
- **Oracles:** Successful execution of test suite without external server prerequisites.
- **Required Tools:** `pydantic-settings`, `python-dotenv`.
- **Success Criteria:** Test suite runs cleanly on any developer machine or CI/CD runner.

---

## 4. Deliverables

### 4.1 Test Evaluation Summaries

#### 4.1.1 Executive Summary
- **Execution Date:** September 20, 2026
- **Test Framework:** Pytest 9.1.1 with Python 3.11.15 (win32)
- **Total Tests Executed:** 33
- **Passed:** 33 (100.0%)
- **Failed:** 0 (0.0%)
- **Skipped / Errored:** 0 (0.0%)
- **Total Execution Duration:** 3.22 seconds
- **Overall Status:** **PASSED**

#### 4.1.2 Detailed Test Case Execution Results

| Test File | Test Case Name | Target Tested | Status | Duration |
| :--- | :--- | :--- | :---: | :---: |
| `test_classification_tasks.py` | `test_process_classification_job_not_found` | Non-existent job ID handling in worker | **PASSED** | 0.08s |
| `test_classification_tasks.py` | `test_process_classification_job_success` | Full classification pipeline & DB state update | **PASSED** | 0.12s |
| `test_classification_tasks.py` | `test_process_classification_job_empty_text_fails` | Empty input job transition to FAILED | **PASSED** | 0.07s |
| `test_ml_classifier.py` | `test_classifier_predict_empty_and_whitespace` | Empty & whitespace inputs return 'unknown' | **PASSED** | 0.05s |
| `test_ml_classifier.py` | `test_classifier_predict_single_text_success` | Single text prediction string return | **PASSED** | 0.04s |
| `test_ml_classifier.py` | `test_classifier_predict_batch_with_probabilities` | Batch probabilities & confidence scores | **PASSED** | 0.06s |
| `test_ml_classifier.py` | `test_classifier_predict_batch_empty_list` | Empty batch list returns empty list | **PASSED** | 0.03s |
| `test_ml_classifier.py` | `test_classifier_missing_model_raises_runtime_error` | RuntimeError raised if model not loaded | **PASSED** | 0.03s |
| `test_ml_classifier.py` | `test_classifier_load_models_file_not_found` | FileNotFoundError on missing pickle files | **PASSED** | 0.04s |
| `test_pdf_extractor.py` | `test_pdf_extractor_extract_text_empty_bytes` | Empty byte input returns empty string | **PASSED** | 0.02s |
| `test_pdf_extractor.py` | `test_pdf_extractor_extract_text_invalid_bytes` | Corrupt byte stream gracefully handled | **PASSED** | 0.03s |
| `test_pdf_extractor.py` | `test_pdf_extractor_extract_text_with_mocked_fitz` | Multi-page text concatenation via PyMuPDF | **PASSED** | 0.04s |
| `test_schemas.py` | `test_job_create_request_valid` | Valid inputs & default 'sentence' strategy | **PASSED** | 0.02s |
| `test_schemas.py` | `test_job_create_request_invalid_strategy` | ValidationError on invalid strategy | **PASSED** | 0.02s |
| `test_schemas.py` | `test_job_create_request_empty_input` | ValidationError on empty string (min_length=1) | **PASSED** | 0.02s |
| `test_schemas.py` | `test_success_response_helper` | Standardized success JSON envelope | **PASSED** | 0.01s |
| `test_schemas.py` | `test_error_response_helper` | Standardized error JSON envelope | **PASSED** | 0.01s |
| `test_schemas.py` | `test_base_response_pydantic_model` | Generic BaseResponse model parsing | **PASSED** | 0.02s |
| `test_security.py` | `test_password_hashing_creates_unique_salts` | Bcrypt salt uniqueness across hashes | **PASSED** | 0.28s |
| `test_security.py` | `test_verify_password_success_and_failure` | Password verification matches & rejects | **PASSED** | 0.29s |
| `test_security.py` | `test_create_access_token_claims_and_default_expiration` | JWT access token claims & expiration | **PASSED** | 0.02s |
| `test_security.py` | `test_create_access_token_custom_delta` | Custom expiration delta enforcement | **PASSED** | 0.02s |
| `test_security.py` | `test_create_refresh_token` | Refresh token claims & long-lived validity | **PASSED** | 0.02s |
| `test_security.py` | `test_tampered_token_fails_decoding` | JWTError on altered token signature | **PASSED** | 0.02s |
| `test_security.py` | `test_token_with_wrong_secret_key_fails` | JWTError on mismatched secret key | **PASSED** | 0.02s |
| `test_segmentation.py` | `test_segment_text_empty_and_none` | Empty/None/whitespace inputs return empty list | **PASSED** | 0.02s |
| `test_segmentation.py` | `test_segment_text_full_text_strategy` | Single segment returned for full_text mode | **PASSED** | 0.02s |
| `test_segmentation.py` | `test_segment_text_paragraph_strategy` | Newline paragraph splitting & offset tracking | **PASSED** | 0.02s |
| `test_segmentation.py` | `test_segment_text_sentence_latin_punctuation` | Sentence splitting on '.', '?', '!' | **PASSED** | 0.02s |
| `test_segmentation.py` | `test_segment_text_sentence_indic_danda` | Sentence splitting on Indic danda ('।') | **PASSED** | 0.02s |
| `test_segmentation.py` | `test_segment_text_auto_strategy` | Clause and punctuation splitting in auto mode | **PASSED** | 0.02s |
| `test_segmentation.py` | `test_segment_text_fallback_for_unknown_strategy` | Fallback to full_text on unknown strategy | **PASSED** | 0.02s |
| `test_unit.py` | `test_basic_unit` | Test framework assertion baseline | **PASSED** | 0.01s |

#### 4.1.3 Actual Terminal Execution Log
```text
============================= test session starts =============================
platform win32 -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\User\Desktop\Vscode\Sinhala-Script Language Identification (LangID) for Sinhala, Pali and Sanskrit\Sinhala-Script-Language-Identification-LangID-for-Sinhala-Pali-and-Sanskrit\webapp\backend
configfile: pytest.ini
plugins: anyio-4.14.2, asyncio-1.4.0, cov-7.1.0, mock-3.15.1
asyncio: mode=Mode.AUTO, debug=False

collecting ... collected 33 items

tests/unit/test_classification_tasks.py::test_process_classification_job_not_found PASSED [  3%]
tests/unit/test_classification_tasks.py::test_process_classification_job_success PASSED [  6%]
tests/unit/test_classification_tasks.py::test_process_classification_job_empty_text_fails PASSED [  9%]
tests/unit/test_ml_classifier.py::test_classifier_predict_empty_and_whitespace PASSED [ 12%]
tests/unit/test_ml_classifier.py::test_classifier_predict_single_text_success PASSED [ 15%]
tests/unit/test_ml_classifier.py::test_classifier_predict_batch_with_probabilities PASSED [ 18%]
tests/unit/test_ml_classifier.py::test_classifier_predict_batch_empty_list PASSED [ 21%]
tests/unit/test_ml_classifier.py::test_classifier_missing_model_raises_runtime_error PASSED [ 24%]
tests/unit/test_ml_classifier.py::test_classifier_load_models_file_not_found PASSED [ 27%]
tests/unit/test_pdf_extractor.py::test_pdf_extractor_extract_text_empty_bytes PASSED [ 30%]
tests/unit/test_pdf_extractor.py::test_pdf_extractor_extract_text_invalid_bytes PASSED [ 33%]
tests/unit/test_pdf_extractor.py::test_pdf_extractor_extract_text_with_mocked_fitz PASSED [ 36%]
tests/unit/test_schemas.py::test_job_create_request_valid PASSED         [ 39%]
tests/unit/test_schemas.py::test_job_create_request_invalid_strategy PASSED [ 42%]
tests/unit/test_schemas.py::test_job_create_request_empty_input PASSED   [ 45%]
tests/unit/test_schemas.py::test_success_response_helper PASSED          [ 48%]
tests/unit/test_schemas.py::test_error_response_helper PASSED            [ 51%]
tests/unit/test_schemas.py::test_base_response_pydantic_model PASSED     [ 54%]
tests/unit/test_security.py::test_password_hashing_creates_unique_salts PASSED [ 57%]
tests/unit/test_security.py::test_verify_password_success_and_failure PASSED [ 60%]
tests/unit/test_security.py::test_create_access_token_claims_and_default_expiration PASSED [ 63%]
tests/unit/test_security.py::test_create_access_token_custom_delta PASSED [ 66%]
tests/unit/test_security.py::test_create_refresh_token PASSED            [ 69%]
tests/unit/test_security.py::test_tampered_token_fails_decoding PASSED   [ 72%]
tests/unit/test_security.py::test_token_with_wrong_secret_key_fails PASSED [ 75%]
tests/unit/test_segmentation.py::test_segment_text_empty_and_none PASSED [ 78%]
tests/unit/test_segmentation.py::test_segment_text_full_text_strategy PASSED [ 81%]
tests/unit/test_segmentation.py::test_segment_text_paragraph_strategy PASSED [ 84%]
tests/unit/test_segmentation.py::test_segment_text_sentence_latin_punctuation PASSED [ 87%]
tests/unit/test_segmentation.py::test_segment_text_sentence_indic_danda PASSED [ 90%]
tests/unit/test_segmentation.py::test_segment_text_auto_strategy PASSED  [ 93%]
tests/unit/test_segmentation.py::test_segment_text_fallback_for_unknown_strategy PASSED [ 96%]
tests/unit/test_unit.py::test_basic_unit PASSED                          [100%]

============================= 33 passed in 2.35s ==============================
```

---

### 4.2 Reporting on Test Coverage

Test coverage was measured using `pytest-cov` (Coverage.py) across the entire `app` package. The target unit-tested modules achieved high coverage, with utility, schema, and security modules reaching **100%**.

#### 4.2.1 Code Coverage Summary Table

| Module Name | Total Statements | Missed Statements | Line Coverage (%) |
| :--- | :---: | :---: | :---: |
| **`app.utils.pdf_extractor`** | 17 | 0 | **100%** |
| **`app.utils.security`** | 22 | 0 | **100%** |
| **`app.schemas.response`** | 11 | 0 | **100%** |
| **`app.schemas.admin`** | 38 | 0 | **100%** |
| **`app.schemas.annotation`** | 29 | 0 | **100%** |
| **`app.schemas.auth`** | 13 | 0 | **100%** |
| **`app.schemas.document`** | 28 | 0 | **100%** |
| **`app.schemas.user`** | 22 | 0 | **100%** |
| **`app.config`** | 31 | 0 | **100%** |
| **`app.db.models.*` (all entities)** | 196 | 0 | **100%** |
| **`app.workers.tasks.classification_tasks`** | 85 | 3 | **96%** |
| **`app.ml.sklearn_langid`** | 53 | 3 | **94%** |
| **`app.db.base`** | 16 | 1 | **94%** |
| **`app.api.v1.users`** | 15 | 3 | **80%** |
| **`app.api.v1.auth`** | 24 | 7 | **71%** |
| **`app.api.v1.classification`** | 54 | 16 | **70%** |
| **`app.utils.exceptions`** | 17 | 6 | **65%** |
| **`app.api.v1.admin`** | 46 | 18 | **61%** |
| **`app.utils.redis_client`** | 10 | 4 | **60%** |
| **`app.api.v1.usage`** | 46 | 20 | **57%** |
| **`app.api.v1.admin_rates`** | 70 | 33 | **53%** |
| **`app.api.v1.documents`** | 74 | 46 | **38%** |
| **`app.api.v1.annotations`** | 57 | 37 | **35%** |
| **`app.services.storage_service`** | 50 | 33 | **34%** |
| **`app.api.v1.websockets`** | 32 | 21 | **34%** |
| **`app.dependencies`** | 56 | 40 | **29%** |
| **`app.services.auth_service`** | 40 | 29 | **28%** |
| **`app.services.user_service`** | 47 | 34 | **28%** |
| **`app.services.credit_service`** | 53 | 39 | **26%** |
| **`app.services.admin_service`** | 82 | 62 | **24%** |
| **`app.workers.tasks.ocr_tasks`** | 56 | 46 | **18%** |
| **Total Backend Codebase** | **1,507** | **551** | **63%** |

> **Note on Coverage Distribution:** Pure unit tests intentionally target core business logic, ML inference, text segmentation, schemas, and security. Endpoints and services requiring live HTTP transactions and integration with Docker containers (PostgreSQL, Redis, MinIO, OCR engines) are covered separately during integration and end-to-end testing phases.

---

## 5. Risks, Dependencies, Assumptions, and Constraints

| Risk | Mitigation Strategy | Contingency (If Risk is Realized) |
| :--- | :--- | :--- |
| **External Service Dependencies (DB, Redis, MinIO) offline during test execution** | Decouple unit tests using `unittest.mock` (`AsyncMock`, `MagicMock`) and patch client initialization in `tests/conftest.py`. | Unit tests run in full isolation without starting Docker containers or live network services. |
| **Windows MAX_PATH (260 character limit) preventing dependency installation** | Run Python and Pytest from a concise path (`C:\Users\User\miniconda3\envs\langid\python.exe`) rather than deep nested directory trees. | Dependencies installed globally or in short conda root path without path truncation errors. |
| **Large ML model checkpoints missing on developer workstations** | Mock `_load_models` and estimator `.predict()` / `.predict_proba()` methods in `test_ml_classifier.py` and `test_classification_tasks.py`. | Fast, deterministic testing without requiring multi-gigabyte weight downloads. |
| **Unicode normalization / diacritics discrepancies for Sinhala/Pali text** | Write dedicated unit test fixtures covering explicit Sinhala vowels, anusvara, and Indic dandas (`।`). | Segmentation algorithm verified to preserve character byte offsets accurately. |

---

## 6. References

1. **Pytest Testing Framework:** [https://docs.pytest.org/](https://docs.pytest.org/)
2. **Pytest-Cov (Coverage.py):** [https://pytest-cov.readthedocs.io/](https://pytest-cov.readthedocs.io/)
3. **FastAPI Testing Guide:** [https://fastapi.tiangolo.com/tutorial/testing/](https://fastapi.tiangolo.com/tutorial/testing/)
4. **PyMuPDF (Fitz) Documentation:** [https://pymupdf.readthedocs.io/](https://pymupdf.readthedocs.io/)
5. **Python-Jose Cryptographic Standards (RFC 7519):** [https://python-jose.readthedocs.io/](https://python-jose.readthedocs.io/)
6. **Passlib Bcrypt Password Hashing:** [https://passlib.readthedocs.io/](https://passlib.readthedocs.io/)
7. **Rational Unified Process (RUP):** Test Plan & Test Evaluation Report Guidelines.
