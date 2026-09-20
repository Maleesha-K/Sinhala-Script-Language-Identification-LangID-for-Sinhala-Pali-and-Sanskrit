# LangID Platform — Iteration 1 Test Plan Reference

**Version 1.0**

## Revision History
| Date | Version | Description | Author |
|---|---|---|---|
| 2026-09-20 | 1.0 | Initial Test Plan based on RUP Template, incorporating backend, frontend, and stress testing. | QA Team |

---

## 1. Evaluation Mission and Test Motivation

**Motivation:** The Sinhala-Script Language Identification (LangID) Platform aims to correctly identify whether a given text snippet is Sinhala, Pali, or Sanskrit, and segment mixed-language texts accordingly. The motivation for this test effort is to ensure that the ML pipeline is accurate, the FastAPI backend is robust and performant under load, and the Next.js frontend provides a seamless user experience.

**Mission:** 
- Verify that the core language identification model and OCR integration work flawlessly.
- Find important problems and assess perceived quality risks.
- Advise on the product's performance characteristics and capacity limits (via rigorous load testing).
- Ensure data integrity when interacting with Postgres, Redis, and MinIO.

## 2. Target Test Items

The following items are targets for testing:
- **FastAPI Backend (`webapp/backend`)**: All REST API endpoints (Auth, Documents, Classification, Users).
- **Next.js Frontend (`webapp/frontend`)**: UI components, pages, and API integration.
- **ML Pipeline & Celery Workers**: The asynchronous tasks handling OCR and text classification (`SklearnLangIDClassifier`).
- **Infrastructure**: Postgres database, Redis broker, and MinIO object storage.

## 3. Test Approach

Testing is conducted using a combination of automated unit testing (pytest, Vitest), end-to-end testing (Playwright), and performance/load testing (Locust). We rely heavily on isolated containerized environments (Docker) to ensure that the test environment accurately reflects production.

### 3.1 Testing Techniques and Types

#### 3.1.1 Data and Database Integrity Testing
**Technique Objective:** Exercise database access methods independently to observe target behavior and data corruption.
**Technique:** Invoking SQLAlchemy async database sessions, creating/modifying models (Users, Documents, ClassificationJobs), and asserting that constraints (like unique emails, foreign keys) are enforced.
**Oracles:** Pytest assertions on DB state after transactions. Alembic migration tests.
**Required Tools:** `pytest`, `pytest-asyncio`, `testcontainers` (Postgres, Redis), `alembic`.
**Success Criteria:** Alembic migrations apply cleanly. Transactions succeed with valid data and rollback properly on integrity errors.

#### 3.1.2 Function Testing
**Technique Objective:** Verify target-of-test functionality, including data entry, processing, and retrieval.
**Technique:** Black-box API integration tests using FastAPI's `TestClient` and `httpx.AsyncClient`. Mocking MinIO where appropriate.
**Oracles:** HTTP status codes (200, 201, 400, 401, 404, 500) and response JSON validation against Pydantic schemas.
**Required Tools:** `pytest`, `httpx`, `pytest-mock`.
**Success Criteria:** All key use-cases (registration, login, document upload, text classification, annotations) succeed with expected status codes and payloads.

#### 3.1.3 User Interface Testing
**Technique Objective:** Ensure UI provides appropriate access, navigation, and state management.
**Technique:** Component testing (rendering, state updates, validation) and End-to-End browser automation (user flows).
**Oracles:** Vitest assertions (e.g., `toBeInTheDocument()`). Playwright visual and DOM assertions (e.g., `toHaveTitle()`, `toBeVisible()`).
**Required Tools:** `Vitest`, `@testing-library/react`, `Playwright`.
**Success Criteria:** Major screens (Login, Signup, Dashboard, Admin) render correctly and user flows (e.g., signing up and uploading a document) complete without console errors.

#### 3.1.4 Performance Profiling 
**Technique Objective:** Exercise behaviors for designated functional transactions under normal workload to log target behavior and latency.
**Technique:** Baseline load testing using a single virtual user in Locust.
**Oracles:** Locust web UI and CSV reports tracking P50, P95, and P99 response times.
**Required Tools:** `Locust`, `Docker Compose` (with resource limits), `docker stats`.
**Success Criteria:** Single-user transactions succeed without failures. Target response times (e.g., Auth login < 100ms, GET health < 20ms) are met.

#### 3.1.5 Load Testing
**Technique Objective:** Exercise designated transactions under varying workload conditions (peak, spike, soak) to observe system degradation.
**Technique:**
We have designed a **Mixed Workload** Locust scenario simulating production traffic:
- **ReadHeavyUser (50%)**: Browsing, listing documents, fetching profile.
- **ClassificationUser (30%)**: Submitting texts for classification, polling results.
- **UploaderUser (20%)**: Uploading PDFs to MinIO.
We employ a `StepLoadShape` to ramp up users from 10 to 50 (normal), 100 (peak), and 200 (spike test).
**Oracles:** Locust failure rate percentages, Request Per Second (RPS) metrics, and container memory/CPU usage limits.
**Required Tools:** `Locust` (headless mode), `csvkit` for report comparison, `py-spy` for profiling.
**Success Criteria:** The system successfully handles peak load (100 users) with an error rate < 1%, without exceeding connection pools or memory limits. 

#### 3.1.6 Security and Access Control Testing
**Technique Objective:** Verify application-level and system-level security constraints.
**Technique:** 
- Creating Locust tasks that intentionally submit without auth headers (`submit_no_auth`) or with invalid credentials.
- Pytest integration tests simulating Admin vs Regular User roles.
**Oracles:** Expectation of quick `401 Unauthorized` or `403 Forbidden` HTTP responses.
**Required Tools:** `pytest`, `Locust`.
**Success Criteria:** Unauthorized access attempts are rejected efficiently without placing undue load on the database or ML workers.

#### 3.1.7 Failover and Recovery Testing
**Technique Objective:** Ensure the target-of-test can successfully failover and recover from hardware, software, or network malfunctions.
**Technique:** 
Simulated outages during load testing:
1. Kill Redis (`docker stop stress_redis`) during classification load and verify FastAPI handles Celery dispatch failures (returns 500/503 gracefully). Restore Redis and verify recovery.
2. Kill Postgres (`docker stop stress_postgres`) during normal load and verify the system handles the outage without data corruption, restoring functionality once the DB restarts.
**Oracles:** System logs, Locust error types (e.g., `ConnectionRefused`), and successful post-recovery HTTP 200 responses.
**Required Tools:** `Docker`, `Locust`.
**Success Criteria:** The API resumes normal operation within 30 seconds of the dependent service being restored.

#### 3.1.8 Configuration Testing
**Technique Objective:** Verify the operation of the target-of-test on different configurations.
**Technique:** 
Running unit tests against different `.env` files. Simulating constrained resource environments in `docker-compose.stress.yml` (e.g., limiting Postgres to `cpus: 0.1` and `memory: 128M`).
**Oracles:** Pytest configuration tests. Application startup logs.
**Required Tools:** `pytest`, `Docker Compose` resource limits.
**Success Criteria:** Application successfully parses diverse valid configurations and fails fast on invalid/missing environment variables.

## 4. Deliverables

### 4.1 Test Evaluation Summaries
Produced at the end of each sprint/iteration. Contains a high-level summary of pass/fail rates for Pytest and Vitest, and Playwright screenshots for failed E2E flows.

### 4.2 Reporting on Test Coverage
- **Unit/Integration**: Generated via `pytest --cov=app --cov-report=html`.
- **Frontend**: Generated via `vitest run --coverage`.
- **Performance**: Locust CSV and HTML reports (saved with timestamps in `webapp/testing/stress/reports/`), reviewed by the team to identify newly introduced bottlenecks.

## 5. Risks, Dependencies, Assumptions, and Constraints

| Risk | Mitigation Strategy | Contingency |
|---|---|---|
| Load Test fails due to local machine limits (not app limits) | Use Docker resource constraints (`deploy.resources.limits`) to ensure the app hits a ceiling before the host machine does. | Run Locust in Distributed Mode or run on a dedicated cloud VM. |
| Test Data Pollution | Pytest uses transaction rollback fixtures (`testcontainers` with nested transactions). | Completely teardown and rebuild DB containers (`teardown.sh`). |
| Inconsistent ML Model versions | ML models are verified and baked into the Docker image or mounted consistently in the stress test environment. | Update `docker-compose` to ensure the correct volume path is mounted. |

## 6. References
- Locust Documentation: https://locust.io/
- FastAPI Testing Guide: https://fastapi.tiangolo.com/tutorial/testing/
- Playwright Documentation: https://playwright.dev/
