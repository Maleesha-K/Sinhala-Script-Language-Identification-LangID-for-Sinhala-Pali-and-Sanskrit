# Stress & Performance Testing Guide

**LangID Platform — Local Docker-Based Stress & Performance Testing**

This document covers the complete setup and execution plan for stress and performance testing the LangID Platform API using **Locust** (load test runner) and **Docker Compose** (isolated target environment). This testing is run entirely locally — no cloud infrastructure required.

---

## Table of Contents

1. [Overview & Goals](#1-overview--goals)
2. [Architecture Under Test](#2-architecture-under-test)
3. [Performance Testing Stack](#3-performance-testing-stack)
4. [Environment Setup](#4-environment-setup)
   - 4.1 [Docker Target Stack](#41-docker-target-stack)
   - 4.2 [Locust Setup](#42-locust-setup)
   - 4.3 [Directory Structure](#43-directory-structure)
5. [Docker Compose Configuration](#5-docker-compose-configuration)
   - 5.1 [Extended docker-compose for Stress Testing](#51-extended-docker-compose-for-stress-testing)
6. [Locust Test Files](#6-locust-test-files)
   - 6.1 [Authentication Load Tests](#61-authentication-load-tests)
   - 6.2 [Classification Pipeline Load Tests](#62-classification-pipeline-load-tests)
   - 6.3 [Document Upload Load Tests](#63-document-upload-load-tests)
   - 6.4 [Mixed Workload Scenario (Full E2E)](#64-mixed-workload-scenario-full-e2e)
7. [Running Stress Tests](#7-running-stress-tests)
   - 7.1 [Web UI Mode](#71-web-ui-mode)
   - 7.2 [Headless / CLI Mode](#72-headless--cli-mode)
   - 7.3 [Distributed Mode](#73-distributed-mode)
8. [Performance Benchmarks & Acceptance Criteria](#8-performance-benchmarks--acceptance-criteria)
9. [Test Scenarios (RUP Mapping)](#9-test-scenarios-rup-mapping)
10. [Monitoring During Tests](#10-monitoring-during-tests)
11. [Reports & Outputs](#11-reports--outputs)
12. [Failover & Recovery Testing](#12-failover--recovery-testing)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. Overview & Goals

### What we are testing

The LangID Platform API is a FastAPI application backed by:
- **PostgreSQL** — persistent data (users, documents, jobs, segments)
- **Redis** — Celery broker + result backend
- **MinIO** — object storage for PDFs
- **Celery Workers** — async OCR and classification processing

Stress and performance testing is designed to answer:
1. **Throughput**: How many requests per second can the API sustain at each endpoint?
2. **Latency**: What are the P50, P90, P95, and P99 response times under load?
3. **Bottleneck Discovery**: Which service (FastAPI, Postgres, Redis, Celery Worker) becomes the bottleneck first?
4. **Scalability**: Does performance degrade gracefully as user count grows?
5. **Stability**: Does the API remain stable under sustained peak load for an extended period?
6. **Failover**: Does the system handle a crashed dependency (Redis, Postgres) gracefully?

### RUP Template Coverage

| RUP Section | Test Type Here |
|---|---|
| Performance Profiling | Baseline + peak response time measurement per endpoint |
| Load Testing | Ramping virtual user load (1 → 50 → 200 users) |
| Failover and Recovery Testing | Kill Redis / Postgres mid-test and observe behaviour |

---

## 2. Architecture Under Test

```
[Locust Virtual Users]
         │
         ▼  HTTP requests
  ┌──────────────┐
  │  FastAPI App │  ← target: http://localhost:8000
  │  (uvicorn)   │
  └──────┬───────┘
         │
    ┌────┴────────┐
    │             │
    ▼             ▼
[PostgreSQL]   [Redis]
 port 5432     port 6379
                  │
                  ▼
           [Celery Worker]
           (OCR + LangID)
                  │
                  ▼
              [MinIO]
             port 9010
```

All services run in Docker containers via `docker compose`. The FastAPI app is also containerised for stress testing (to simulate a production-like environment), unlike development where it runs natively.

---

## 3. Performance Testing Stack

| Tool | Purpose | Install |
|---|---|---|
| **Locust** | Load test runner with web UI and CLI | `pip install locust` |
| **Docker Compose** | Runs the entire application stack in isolation | Already installed |
| **docker stats** | Live CPU/memory/network monitoring per container | Built-in Docker CLI |
| **Locust CSV reports** | Per-endpoint RPS, latency, failure rate | Built into Locust |
| **py-spy** (optional) | CPU profiling of the FastAPI process | `pip install py-spy` |

---

## 4. Environment Setup

### 4.1 Docker Target Stack

The stress test runs the **full application stack** (FastAPI + Celery Worker + Postgres + Redis + MinIO) inside Docker. This is important because:

- It isolates the test from your local Python environment
- It accurately simulates production (containerised) resource limits
- It allows monitoring each container's CPU/memory independently

### 4.2 Locust Setup

Locust runs **outside** Docker on your host machine and fires HTTP requests at the containerised FastAPI app.

```bash
# Create a virtual environment for Locust
python3 -m venv webapp/testing/stress/.venv
source webapp/testing/stress/.venv/bin/activate

# Install Locust
pip install locust
```

### 4.3 Directory Structure

```
webapp/testing/
├── README.md                    # This file (general testing README)
├── stress/
│   ├── README.md                # This stress testing document
│   ├── docker-compose.stress.yml  # Extended compose for stress environment
│   ├── Dockerfile.api           # Dockerfile for containerised FastAPI
│   ├── requirements.txt         # Locust + helpers
│   ├── locustfiles/
│   │   ├── auth_load.py         # Auth endpoint load tests
│   │   ├── classification_load.py  # Classification pipeline load tests
│   │   ├── document_load.py     # Document upload/list load tests
│   │   └── mixed_workload.py    # Full E2E mixed scenario
│   ├── fixtures/
│   │   └── sample_sinhala.txt   # Sample Sinhala text for classification
│   ├── reports/                 # Generated CSV and HTML reports
│   └── scripts/
│       ├── setup.sh             # Bootstraps the Docker stack + seeds data
│       └── teardown.sh          # Stops all containers and cleans up
```

---

## 5. Docker Compose Configuration

### 5.1 Extended docker-compose for Stress Testing

Create `webapp/testing/stress/docker-compose.stress.yml`:

```yaml
version: '3.8'

# This compose file EXTENDS the base webapp/docker-compose.yml
# It adds the FastAPI app and Celery worker as containers,
# plus resource limits to simulate a controlled production environment.

services:
  # ── Infrastructure (same as base compose) ──────────────────────────────────
  db:
    image: postgres:15-alpine
    container_name: stress_postgres
    restart: always
    environment:
      POSTGRES_USER: langid
      POSTGRES_PASSWORD: langid_password
      POSTGRES_DB: langid_db
    ports:
      - "5433:5432"          # Use port 5433 to avoid conflict with dev DB
    volumes:
      - stress_postgres_data:/var/lib/postgresql/data
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 512M
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U langid -d langid_db"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: stress_redis
    restart: always
    ports:
      - "6380:6379"          # Use port 6380 to avoid conflict with dev Redis
    volumes:
      - stress_redis_data:/data
    deploy:
      resources:
        limits:
          cpus: "0.5"
          memory: 128M
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  minio:
    image: minio/minio:latest
    container_name: stress_minio
    restart: always
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    command: server /data --console-address ":9001"
    ports:
      - "9020:9000"
      - "9021:9001"
    volumes:
      - stress_minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ── Application ─────────────────────────────────────────────────────────────
  api:
    build:
      context: ../../backend
      dockerfile: ../../testing/stress/Dockerfile.api
    container_name: stress_api
    restart: always
    ports:
      - "8000:8000"
    environment:
      POSTGRES_USER: langid
      POSTGRES_PASSWORD: langid_password
      POSTGRES_SERVER: db
      POSTGRES_PORT: "5432"
      POSTGRES_DB: langid_db
      REDIS_HOST: redis
      REDIS_PORT: "6379"
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
      MINIO_SECURE: "false"
      SECRET_KEY: stress-test-secret-key-not-for-production
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy
    deploy:
      resources:
        limits:
          cpus: "2.0"       # Limit to 2 CPUs to simulate a small server
          memory: 1G

  worker:
    build:
      context: ../../backend
      dockerfile: Dockerfile.worker
    container_name: stress_worker
    restart: always
    environment:
      POSTGRES_USER: langid
      POSTGRES_PASSWORD: langid_password
      POSTGRES_SERVER: db
      POSTGRES_PORT: "5432"
      POSTGRES_DB: langid_db
      REDIS_HOST: redis
      REDIS_PORT: "6379"
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
      MINIO_SECURE: "false"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    deploy:
      resources:
        limits:
          cpus: "2.0"
          memory: 1G

volumes:
  stress_postgres_data:
  stress_redis_data:
  stress_minio_data:
```

### Dockerfile for FastAPI (stress environment)

Create `webapp/testing/stress/Dockerfile.api`:

```dockerfile
FROM python:3.12-slim

# Install Tesseract for OCR
RUN apt-get update && apt-get install -y tesseract-ocr && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv and dependencies
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy application code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Run migrations then start API
CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4"]
```

---

## 6. Locust Test Files

### 6.1 Authentication Load Tests

File: `locustfiles/auth_load.py`

Tests the login, signup, and token refresh endpoints under load. This is a **lightweight CPU** test — auth is almost entirely I/O bound (DB lookup + JWT signing).

```python
"""
Auth Load Test
--------------
Tests:
  - POST /api/v1/auth/login         → Simulates user login
  - POST /api/v1/auth/signup        → Simulates user registration
  - POST /api/v1/auth/refresh       → Simulates token refresh

Covers (RUP):
  - Performance Profiling: baseline response times for auth endpoints
  - Load Testing: concurrent login storm (spike test)
  - Security & Access Control: ensure 401 is returned quickly under load
"""
import uuid
from locust import HttpUser, task, between, constant_throughput


class AuthUser(HttpUser):
    """Simulates a user authenticating against the API."""
    
    # Wait 1–3 seconds between tasks (simulates human think time)
    wait_time = between(1, 3)
    
    # Shared pool of credentials created during setup
    host = "http://localhost:8000"
    
    def on_start(self):
        """Each virtual user signs up and logs in before running tasks."""
        self.email = f"loadtest_{uuid.uuid4().hex[:8]}@test.com"
        self.password = "LoadTest123!"
        
        # Signup
        signup_resp = self.client.post(
            "/api/v1/auth/signup",
            json={"email": self.email, "password": self.password, "display_name": "Load Test User"},
            name="/auth/signup"
        )
        
        if signup_resp.status_code != 201:
            signup_resp.failure(f"Signup failed: {signup_resp.text}")
            return
        
        # Login to get tokens
        login_resp = self.client.post(
            "/api/v1/auth/login",
            json={"email": self.email, "password": self.password},
            name="/auth/login"
        )
        
        if login_resp.status_code != 200:
            login_resp.failure(f"Login failed: {login_resp.text}")
            return
        
        data = login_resp.json().get("data", {})
        self.access_token = data.get("access_token")
        self.refresh_token = data.get("refresh_token")
        self.auth_headers = {"Authorization": f"Bearer {self.access_token}"}
    
    @task(3)
    def login(self):
        """Simulate a login — most frequent auth operation."""
        self.client.post(
            "/api/v1/auth/login",
            json={"email": self.email, "password": self.password},
            name="/auth/login"
        )
    
    @task(1)
    def refresh_token(self):
        """Simulate token refresh — periodic, less frequent."""
        if not hasattr(self, "refresh_token"):
            return
        resp = self.client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": self.refresh_token},
            name="/auth/refresh"
        )
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            self.access_token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")
            self.auth_headers = {"Authorization": f"Bearer {self.access_token}"}
    
    @task(1)
    def invalid_login_attempt(self):
        """
        Simulates brute-force probing. Marked as expected failure.
        The API should respond quickly with 401, not hang.
        """
        with self.client.post(
            "/api/v1/auth/login",
            json={"email": "notexist@test.com", "password": "wrong"},
            name="/auth/login [invalid]",
            catch_response=True
        ) as response:
            if response.status_code == 401:
                response.success()  # This is the expected outcome
            else:
                response.failure(f"Expected 401, got {response.status_code}")
```

### 6.2 Classification Pipeline Load Tests

File: `locustfiles/classification_load.py`

This is the **heaviest** load test. The classification pipeline involves:
1. Creating a job (DB write + Redis task dispatch)
2. Celery worker picks up the task (CPU-bound ML inference)
3. Results are stored back in Postgres

```python
"""
Classification Pipeline Load Test
----------------------------------
Tests:
  - POST /api/v1/classification/jobs  → Submit text for language ID
  - GET  /api/v1/classification/jobs/{id} → Poll for results

Covers (RUP):
  - Performance Profiling: end-to-end job completion time (P50, P95, P99)
  - Load Testing: queue saturation test (how many jobs can Celery handle?)
  - Load Testing: simulates peak classification traffic

Key metrics to watch:
  - Job queue depth (visible in Redis: redis-cli llen celery)
  - Celery worker CPU (visible in: docker stats stress_worker)
  - Time from submission to COMPLETED status
"""
import time
import uuid
import random
from locust import HttpUser, task, between

# Sample Sinhala/Pali/Sanskrit text corpus for classification requests
SAMPLE_TEXTS = [
    # Sinhala
    "ශ්‍රී ලංකාව දකුණු ආසියාවේ ඇති කුඩා රටකි. ඉන්දියාව ශ්‍රී ලංකාවේ ආසන්නතම ඉන්දියාවකි.",
    "ලංකාවේ ජනතාව ශ්‍රී ලාංකිකයන් ලෙස හඳුන්වනු ලැබේ. ජාතික භාෂාව සිංහල හා දෙමළ වේ.",
    "බෞද්ධ ධර්මය ශ්‍රී ලංකාවේ ප්‍රධාන ආගම වේ. ගල් ගහකින් ආරම්භ වූ ශිෂ්ටාචාරයක් ශ්‍රී ලංකාවේ ඇත.",
    # Pali (Buddhist canonical texts)
    "Namo tassa bhagavato arahato sammāsambuddhassa",
    "Sabbe sattā sukhitā hontu. Sabbe sattā averā hontu. Sabbe sattā abyāpajjhā hontu.",
    "Dhammaṃ saraṇaṃ gacchāmi. Saṅghaṃ saraṇaṃ gacchāmi.",
    # Sanskrit
    "सर्वे भवन्तु सुखिनः। सर्वे सन्तु निरामयाः।",
    "ॐ नमो भगवते वासुदेवाय। ॐ शान्तिः शान्तिः शान्तिः।",
    "यत्र योगेश्वरः कृष्णो यत्र पार्थो धनुर्धरः।",
    # Mixed (multiple languages in one text)
    "ශ්‍රී ලංකාවේ Namo tassa bhagavato sabbe sattā sukhitā hontu. සර්වේ භවන්තු සුඛිනාහ।",
]

class ClassificationUser(HttpUser):
    """Simulates a user submitting text for language identification."""
    
    wait_time = between(2, 5)
    host = "http://localhost:8000"
    
    def on_start(self):
        """Create unique user and authenticate."""
        self.email = f"classify_{uuid.uuid4().hex[:8]}@test.com"
        self.password = "ClassifyTest123!"
        
        self.client.post("/api/v1/auth/signup", json={
            "email": self.email,
            "password": self.password,
            "display_name": "Classifier User"
        })
        
        resp = self.client.post("/api/v1/auth/login", json={
            "email": self.email,
            "password": self.password
        })
        
        if resp.status_code == 200:
            token = resp.json()["data"]["access_token"]
            self.headers = {"Authorization": f"Bearer {token}"}
        else:
            self.headers = {}
    
    @task(3)
    def submit_and_poll_classification(self):
        """
        Submit a text for classification and poll until completed.
        Measures the full round-trip time for the async pipeline.
        """
        text = random.choice(SAMPLE_TEXTS)
        strategy = random.choice(["sentence", "paragraph", "full_text"])
        
        # 1. Submit job
        submit_resp = self.client.post(
            "/api/v1/classification/jobs",
            json={"input_text": text, "segmentation_strategy": strategy},
            headers=self.headers,
            name="/classification/jobs [submit]"
        )
        
        if submit_resp.status_code != 201:
            submit_resp.failure(f"Job submission failed: {submit_resp.text}")
            return
        
        job_id = submit_resp.json()["data"]["id"]
        
        # 2. Poll for completion (max 30 seconds, 1-second intervals)
        start = time.time()
        while time.time() - start < 30:
            time.sleep(1)
            
            poll_resp = self.client.get(
                f"/api/v1/classification/jobs/{job_id}",
                headers=self.headers,
                name="/classification/jobs/{id} [poll]"
            )
            
            if poll_resp.status_code == 200:
                status = poll_resp.json()["data"]["status"]
                if status == "completed":
                    break
                elif status == "failed":
                    poll_resp.failure(f"Job {job_id} failed")
                    break
            else:
                poll_resp.failure(f"Poll failed with {poll_resp.status_code}")
                break
    
    @task(1)
    def submit_long_text(self):
        """
        Tests with longer mixed-language text to stress the segmentation + ML pipeline.
        """
        long_text = " ".join(SAMPLE_TEXTS * 3)  # ~900 characters
        
        with self.client.post(
            "/api/v1/classification/jobs",
            json={"input_text": long_text, "segmentation_strategy": "sentence"},
            headers=self.headers,
            name="/classification/jobs [long text]",
            catch_response=True
        ) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Long text submission failed: {response.text}")
    
    @task(1)
    def submit_without_auth(self):
        """
        Tests that unauthenticated requests are rejected quickly (401).
        Ensures the auth middleware doesn't add significant overhead under load.
        """
        with self.client.post(
            "/api/v1/classification/jobs",
            json={"input_text": "test text"},
            name="/classification/jobs [no auth]",
            catch_response=True
        ) as response:
            if response.status_code == 401:
                response.success()
            else:
                response.failure(f"Expected 401, got {response.status_code}")
```

### 6.3 Document Upload Load Tests

File: `locustfiles/document_load.py`

Tests the file upload pipeline (MinIO upload + Celery OCR task dispatch). This is primarily **I/O bound** (network + disk).

```python
"""
Document Upload Load Test
--------------------------
Tests:
  - POST /api/v1/documents/upload   → Upload a PDF file
  - GET  /api/v1/documents          → List user documents
  - GET  /api/v1/documents/{id}     → Get specific document

Covers (RUP):
  - Performance Profiling: upload throughput (MB/s), list query time
  - Load Testing: concurrent uploads to MinIO + Postgres write burst

Key metrics:
  - MinIO container CPU/memory (docker stats stress_minio)
  - Postgres write throughput (pg_stat_activity during test)
"""
import io
import uuid
import random
from locust import HttpUser, task, between

# Generate a minimal valid PDF in memory (avoids filesystem dependency)
MINIMAL_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Contents 4 0 R>>endobj\n"
    b"4 0 obj<</Length 44>>stream\n"
    b"BT /F1 12 Tf 100 700 Td (Stress Test) Tj ET\n"
    b"endstream\n"
    b"endobj\n"
    b"xref\n0 5\n0000000000 65535 f\n"
    b"trailer<</Size 5/Root 1 0 R>>\n"
    b"%%EOF"
)


class DocumentUser(HttpUser):
    """Simulates a user uploading and managing documents."""
    
    wait_time = between(2, 5)
    host = "http://localhost:8000"
    uploaded_doc_ids: list = []
    
    def on_start(self):
        """Create unique user and authenticate."""
        self.email = f"docuser_{uuid.uuid4().hex[:8]}@test.com"
        self.password = "DocTest123!"
        
        self.client.post("/api/v1/auth/signup", json={
            "email": self.email,
            "password": self.password,
            "display_name": "Doc User"
        })
        
        resp = self.client.post("/api/v1/auth/login", json={
            "email": self.email, "password": self.password
        })
        
        if resp.status_code == 200:
            token = resp.json()["data"]["access_token"]
            self.headers = {"Authorization": f"Bearer {token}"}
        else:
            self.headers = {}
    
    @task(3)
    def upload_document(self):
        """Upload a PDF file. Tests MinIO write + Postgres insert + Celery dispatch."""
        filename = f"test_{uuid.uuid4().hex[:6]}.pdf"
        
        resp = self.client.post(
            "/api/v1/documents/upload",
            headers=self.headers,
            files={"file": (filename, io.BytesIO(MINIMAL_PDF), "application/pdf")},
            name="/documents/upload"
        )
        
        if resp.status_code == 201:
            doc_id = resp.json()["data"]["id"]
            self.uploaded_doc_ids.append(doc_id)
        else:
            resp.failure(f"Upload failed: {resp.text}")
    
    @task(4)
    def list_documents(self):
        """List user documents. Tests Postgres SELECT performance under concurrent load."""
        self.client.get(
            "/api/v1/documents",
            headers=self.headers,
            name="/documents [list]"
        )
    
    @task(2)
    def get_document(self):
        """Get a specific document. Tests point-query performance."""
        if not self.uploaded_doc_ids:
            return
        doc_id = random.choice(self.uploaded_doc_ids)
        self.client.get(
            f"/api/v1/documents/{doc_id}",
            headers=self.headers,
            name="/documents/{id} [get]"
        )
```

### 6.4 Mixed Workload Scenario (Full E2E)

File: `locustfiles/mixed_workload.py`

The **primary stress test scenario**. Simulates a realistic mix of user behaviours concurrently, matching the real production traffic pattern.

```python
"""
Mixed Workload Stress Test
---------------------------
This is the PRIMARY stress test scenario for the LangID Platform.
It combines all user types at realistic weights to simulate production traffic.

User distribution:
  - 50% read-heavy users (browsing, listing, polling)
  - 30% classification users (submitting text, polling results)
  - 20% upload users (uploading documents, checking status)

Covers (RUP):
  - Load Testing: average and peak workload simulation
  - Performance Profiling: full-system bottleneck detection
  - Failover Testing: system behaviour when a service is unavailable
"""
import uuid
import io
import time
import random
from locust import HttpUser, task, between, LoadTestShape

SAMPLE_TEXTS = [
    "ශ්‍රී ලංකාව දකුණු ආසියාවේ ඇති කුඩා රටකි.",
    "Namo tassa bhagavato arahato sammāsambuddhassa",
    "सर्वे भवन्तु सुखिनः। सर्वे सन्तु निरामयाः।",
    "ලංකාවේ ජනතාව ශ්‍රී ලාංකිකයන් ලෙස හඳුන්වනු ලැබේ.",
    "Sabbe sattā sukhitā hontu. Sabbe sattā averā hontu.",
]

MINIMAL_PDF = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF"

# ── Helper mixin for authentication ─────────────────────────────────────────────

def authenticate(user_instance, prefix: str):
    """Creates a unique test user and logs them in."""
    user_instance.email = f"{prefix}_{uuid.uuid4().hex[:8]}@stress.com"
    user_instance.password = "Stress123!"
    
    user_instance.client.post("/api/v1/auth/signup", json={
        "email": user_instance.email,
        "password": user_instance.password,
        "display_name": f"Stress User {prefix}"
    })
    
    resp = user_instance.client.post("/api/v1/auth/login", json={
        "email": user_instance.email,
        "password": user_instance.password
    })
    
    if resp.status_code == 200:
        token = resp.json()["data"]["access_token"]
        user_instance.headers = {"Authorization": f"Bearer {token}"}
    else:
        user_instance.headers = {}


# ── User Classes ─────────────────────────────────────────────────────────────────

class ReadHeavyUser(HttpUser):
    """
    Represents a typical browsing user.
    Accounts for ~50% of simulated traffic.
    Primarily tests read path: Postgres SELECT, auth middleware overhead.
    """
    wait_time = between(1, 4)
    weight = 5

    def on_start(self):
        authenticate(self, "reader")
        self.doc_ids = []
    
    @task(5)
    def health_check(self):
        self.client.get("/health", name="/health")
    
    @task(4)
    def list_documents(self):
        self.client.get("/api/v1/documents", headers=self.headers, name="/documents [list]")
    
    @task(2)
    def get_user_profile(self):
        self.client.get("/api/v1/users/me", headers=self.headers, name="/users/me")
    
    @task(1)
    def poll_old_job(self):
        """Polls a random (likely non-existent) job — tests 404 under load."""
        fake_id = uuid.uuid4()
        with self.client.get(
            f"/api/v1/classification/jobs/{fake_id}",
            headers=self.headers,
            name="/classification/jobs/{id} [404 poll]",
            catch_response=True
        ) as response:
            if response.status_code == 404:
                response.success()


class ClassificationUser(HttpUser):
    """
    Represents a power user submitting texts for classification.
    Accounts for ~30% of simulated traffic.
    Tests the async pipeline: Redis queue, Celery worker, Postgres write.
    """
    wait_time = between(3, 8)
    weight = 3
    
    def on_start(self):
        authenticate(self, "classifier")
        self.job_ids = []
    
    @task(3)
    def submit_classification(self):
        text = random.choice(SAMPLE_TEXTS)
        resp = self.client.post(
            "/api/v1/classification/jobs",
            json={"input_text": text, "segmentation_strategy": "sentence"},
            headers=self.headers,
            name="/classification/jobs [submit]"
        )
        if resp.status_code == 201:
            self.job_ids.append(resp.json()["data"]["id"])
    
    @task(4)
    def poll_job(self):
        if not self.job_ids:
            return
        job_id = random.choice(self.job_ids)
        self.client.get(
            f"/api/v1/classification/jobs/{job_id}",
            headers=self.headers,
            name="/classification/jobs/{id} [poll]"
        )


class UploaderUser(HttpUser):
    """
    Represents a user uploading PDF documents.
    Accounts for ~20% of simulated traffic.
    Tests MinIO write throughput + Celery OCR task queuing.
    """
    wait_time = between(5, 15)
    weight = 2
    
    def on_start(self):
        authenticate(self, "uploader")
        self.doc_ids = []
    
    @task(2)
    def upload_document(self):
        resp = self.client.post(
            "/api/v1/documents/upload",
            headers=self.headers,
            files={"file": (f"test_{uuid.uuid4().hex[:4]}.pdf", io.BytesIO(MINIMAL_PDF), "application/pdf")},
            name="/documents/upload"
        )
        if resp.status_code == 201:
            self.doc_ids.append(resp.json()["data"]["id"])
    
    @task(3)
    def list_documents(self):
        self.client.get("/api/v1/documents", headers=self.headers, name="/documents [list]")


# ── Load Shape ────────────────────────────────────────────────────────────────────

class StepLoadShape(LoadTestShape):
    """
    Implements a realistic load ramp:
    
    Phase 1 (0–2 min):   Warm-up      —  10 users (baseline)
    Phase 2 (2–5 min):   Ramp-up      —  50 users (normal load)
    Phase 3 (5–10 min):  Peak         — 100 users (peak load)
    Phase 4 (10–12 min): Spike        — 200 users (stress)
    Phase 5 (12–15 min): Cool-down    —  20 users (recovery verification)
    
    Configure via Locust CLI:
      locust -f mixed_workload.py --headless --run-time 15m
    """
    
    stages = [
        {"duration": 120,  "users": 10,  "spawn_rate": 2},   # Warm-up
        {"duration": 300,  "users": 50,  "spawn_rate": 5},   # Normal load
        {"duration": 600,  "users": 100, "spawn_rate": 10},  # Peak load
        {"duration": 720,  "users": 200, "spawn_rate": 20},  # Stress spike
        {"duration": 900,  "users": 20,  "spawn_rate": 5},   # Cool-down
    ]
    
    def tick(self):
        run_time = self.get_run_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                return stage["users"], stage["spawn_rate"]
        return None  # Stop after all stages
```

---

## 7. Running Stress Tests

### 7.1 Web UI Mode

The **recommended starting point** — gives you a live dashboard showing RPS, response times, and failure rates.

#### Step 1: Start the full application stack

```bash
# From webapp/ directory
cd webapp/testing/stress

# Start all containers (first run will build the API image)
docker compose -f docker-compose.stress.yml up --build -d

# Wait for all services to be healthy
docker compose -f docker-compose.stress.yml ps
# All containers should show "healthy" status

# Run Alembic migrations (one-time setup)
docker exec stress_api sh -c "uv run alembic upgrade head"
```

#### Step 2: Start Locust with the Web UI

```bash
# Activate venv
source webapp/testing/stress/.venv/bin/activate

# Navigate to stress dir
cd webapp/testing/stress

# Start Locust UI for mixed workload test
locust -f locustfiles/mixed_workload.py --host=http://localhost:8000

# OR for a specific test:
locust -f locustfiles/auth_load.py --host=http://localhost:8000
locust -f locustfiles/classification_load.py --host=http://localhost:8000
locust -f locustfiles/document_load.py --host=http://localhost:8000
```

#### Step 3: Open the Locust Web UI

Navigate to: **http://localhost:8089**

Configure the test:
- **Number of users**: Start with `10`, increase in subsequent runs
- **Spawn rate**: `2` (users per second to add)
- **Host**: `http://localhost:8000`

Click **"Start swarming"** to begin.

### 7.2 Headless / CLI Mode

Run without a browser for scripted/automated execution.

```bash
# Run mixed workload with step load shape for 15 minutes
locust \
  -f locustfiles/mixed_workload.py \
  --host=http://localhost:8000 \
  --headless \
  --run-time=15m \
  --csv=reports/mixed_workload_$(date +%Y%m%d_%H%M%S) \
  --html=reports/mixed_workload_$(date +%Y%m%d_%H%M%S).html

# Run auth load test: 50 users, 10 spawn rate, 5 minutes
locust \
  -f locustfiles/auth_load.py \
  --host=http://localhost:8000 \
  --headless \
  --users=50 \
  --spawn-rate=10 \
  --run-time=5m \
  --csv=reports/auth_$(date +%Y%m%d_%H%M%S) \
  --html=reports/auth_$(date +%Y%m%d_%H%M%S).html

# Run classification load: 20 users (Celery is the bottleneck here)
locust \
  -f locustfiles/classification_load.py \
  --host=http://localhost:8000 \
  --headless \
  --users=20 \
  --spawn-rate=5 \
  --run-time=10m \
  --csv=reports/classification_$(date +%Y%m%d_%H%M%S) \
  --html=reports/classification_$(date +%Y%m%d_%H%M%S).html
```

#### Convenience run scripts

Create `webapp/testing/stress/scripts/run_mixed.sh`:

```bash
#!/bin/bash
set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_DIR="$(dirname "$0")/../reports"
mkdir -p "$REPORT_DIR"

echo "==> Starting Docker stack..."
docker compose -f "$(dirname "$0")/../docker-compose.stress.yml" up -d --wait

echo "==> Running Alembic migrations..."
docker exec stress_api sh -c "uv run alembic upgrade head" 2>/dev/null || true

echo "==> Starting Locust mixed workload test..."
locust \
  -f "$(dirname "$0")/../locustfiles/mixed_workload.py" \
  --host=http://localhost:8000 \
  --headless \
  --run-time=15m \
  --csv="$REPORT_DIR/mixed_$TIMESTAMP" \
  --html="$REPORT_DIR/mixed_$TIMESTAMP.html"

echo "==> Test complete. Report: $REPORT_DIR/mixed_$TIMESTAMP.html"
```

Make it executable:
```bash
chmod +x webapp/testing/stress/scripts/run_mixed.sh
```

### 7.3 Distributed Mode

If your local machine has many cores and you want to push higher user counts (500+), run Locust in distributed mode:

```bash
# Terminal 1: Start Locust master
locust -f locustfiles/mixed_workload.py --master --host=http://localhost:8000

# Terminal 2+: Start worker processes (one per CPU core)
locust -f locustfiles/mixed_workload.py --worker --master-host=localhost
locust -f locustfiles/mixed_workload.py --worker --master-host=localhost
```

---

## 8. Performance Benchmarks & Acceptance Criteria

These are the **target thresholds** for the stress test to "pass". If any of these are violated, the endpoint needs optimisation.

### API Response Time Targets (under 50 concurrent users)

| Endpoint | P50 (median) | P95 | P99 | Max Error Rate |
|---|---|---|---|---|
| `GET /health` | < 20ms | < 50ms | < 100ms | 0% |
| `POST /auth/login` | < 100ms | < 300ms | < 500ms | 0% |
| `POST /auth/signup` | < 150ms | < 400ms | < 700ms | 0% |
| `GET /users/me` | < 50ms | < 150ms | < 300ms | 0% |
| `GET /documents` (list) | < 80ms | < 250ms | < 500ms | 0% |
| `POST /documents/upload` | < 500ms | < 1500ms | < 3000ms | < 1% |
| `POST /classification/jobs` (submit only) | < 100ms | < 300ms | < 500ms | 0% |
| `GET /classification/jobs/{id}` (poll) | < 50ms | < 150ms | < 300ms | 0% |
| End-to-end classification time | < 5s | < 15s | < 30s | < 2% |

### Throughput Targets (under 50 concurrent users)

| Endpoint | Minimum RPS |
|---|---|
| `GET /health` | 200 RPS |
| `POST /auth/login` | 50 RPS |
| `GET /documents` | 100 RPS |
| `POST /classification/jobs` | 20 RPS |

### Stability Target

- **No memory leaks**: API container RSS memory should not grow more than 10% after 10 minutes of sustained load.
- **No connection pool exhaustion**: PostgreSQL `max_connections` should not be exceeded.
- **No Redis timeouts**: All cache operations should complete within 100ms.

---

## 9. Test Scenarios (RUP Mapping)

### Scenario A: Baseline Performance Profile

**Purpose**: Measure single-user latency to establish a clean baseline.

```bash
locust -f locustfiles/mixed_workload.py \
  --host=http://localhost:8000 \
  --headless --users=1 --spawn-rate=1 --run-time=2m \
  --csv=reports/baseline
```

**What to look for**: Each endpoint's P50 under 1 user. If baseline is already slow, you have a performance bug.

---

### Scenario B: Normal Load (50 Users)

**Purpose**: Simulate typical daily traffic.

```bash
locust -f locustfiles/mixed_workload.py \
  --host=http://localhost:8000 \
  --headless --users=50 --spawn-rate=5 --run-time=5m \
  --csv=reports/normal_50users
```

**Pass criteria**: All response time targets in Section 8 are met.

---

### Scenario C: Peak Load (100 Users)

**Purpose**: Simulate peak usage without breaking.

```bash
locust -f locustfiles/mixed_workload.py \
  --host=http://localhost:8000 \
  --headless --users=100 --spawn-rate=10 --run-time=5m \
  --csv=reports/peak_100users
```

**Pass criteria**: Error rate < 1%, P99 response time < 2× P50 baseline.

---

### Scenario D: Stress / Spike Test (200 Users — pushed beyond capacity)

**Purpose**: Find the breaking point. At some user count, the system will degrade. Document where.

```bash
locust -f locustfiles/mixed_workload.py \
  --host=http://localhost:8000 \
  --headless --users=200 --spawn-rate=20 --run-time=5m \
  --csv=reports/stress_200users
```

**What to look for**: When does the error rate spike? Which endpoint fails first? Check `docker stats` while this runs.

---

### Scenario E: Soak / Endurance Test (50 Users for 30 Minutes)

**Purpose**: Detect memory leaks, connection leaks, gradual degradation over time.

```bash
locust -f locustfiles/mixed_workload.py \
  --host=http://localhost:8000 \
  --headless --users=50 --spawn-rate=5 --run-time=30m \
  --csv=reports/soak_30min
```

**What to look for**: Does P95 response time increase over time? Does the container's memory grow?

---

### Scenario F: Classification-Specific Load (Celery Worker Saturation)

**Purpose**: How many concurrent classification jobs can the Celery worker handle before queuing builds up?

```bash
locust -f locustfiles/classification_load.py \
  --host=http://localhost:8000 \
  --headless --users=30 --spawn-rate=3 --run-time=10m \
  --csv=reports/classification_saturation
```

**Monitor during test**:
```bash
# Watch Redis queue depth
watch -n 1 "docker exec stress_redis redis-cli llen celery"

# Watch worker CPU
docker stats stress_worker --no-stream --format "{{.CPUPerc}} CPU | {{.MemUsage}} MEM"
```

---

## 10. Monitoring During Tests

Run these in separate terminals while Locust is executing.

### Live Container Stats

```bash
# All containers, refreshed every 2 seconds
docker stats stress_api stress_worker stress_postgres stress_redis stress_minio \
  --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
```

### Postgres Connection Count

```bash
watch -n 2 "docker exec stress_postgres psql -U langid -d langid_db -c \
  \"SELECT count(*) as connections, state FROM pg_stat_activity GROUP BY state;\""
```

### Redis Queue Depth (Celery backlog)

```bash
watch -n 1 "docker exec stress_redis redis-cli llen celery"
```

### FastAPI Process Profiling with py-spy

While a test is running, attach `py-spy` to the uvicorn process inside the container:

```bash
# Get the PID of uvicorn inside the container
PID=$(docker exec stress_api pgrep -f uvicorn | head -1)

# Run py-spy for 60 seconds and dump a flamegraph
docker exec stress_api py-spy record -o /tmp/profile.svg --pid $PID --duration 60

# Copy flamegraph to host
docker cp stress_api:/tmp/profile.svg reports/flamegraph_$(date +%Y%m%d_%H%M%S).svg

# Open in browser
xdg-open reports/flamegraph_*.svg
```

---

## 11. Reports & Outputs

### Locust CSV Output Files

When using `--csv=reports/run_name`, Locust produces:

| File | Contents |
|---|---|
| `run_name_stats.csv` | Per-endpoint RPS, median, P95, P99, failure count |
| `run_name_stats_history.csv` | Time-series data — latency and RPS over time |
| `run_name_failures.csv` | All unique failure messages |
| `run_name_exceptions.csv` | Python exceptions in Locust workers |

### Locust HTML Report

The `--html=reports/run_name.html` flag generates a self-contained interactive HTML report with:
- Response time distribution charts (P50, P95, P99)
- RPS over time charts
- Failure counts per endpoint

Open it directly in your browser:
```bash
xdg-open reports/mixed_workload_20250919_235000.html
```

### Comparing Multiple Runs

To compare runs across different scenarios:

```bash
# Install csvkit for quick CLI comparison
pip install csvkit

# Compare P95 response times across two CSV reports
csvjoin -c "Name" reports/normal_50users_stats.csv reports/peak_100users_stats.csv \
  | csvcut -c Name,"95%","95%2" | csvlook
```

---

## 12. Failover & Recovery Testing

This section tests the system's resilience when infrastructure dependencies fail mid-test.

### Test 1: Redis Failure During Classification Load

**What happens when Redis (Celery broker) goes down while jobs are being submitted?**

```bash
# Terminal 1: Start classification load test
locust -f locustfiles/classification_load.py \
  --host=http://localhost:8000 --users=20 --spawn-rate=5

# Terminal 2: Kill Redis after 2 minutes
sleep 120 && docker stop stress_redis

# Expected behaviour:
# - API returns 500/503 for /classification/jobs POST (Celery can't dispatch)
# - Existing jobs in the DB remain queued
# - GET /classification/jobs/{id} still works (just returns "queued" status)

# Restore Redis after 2 more minutes
sleep 120 && docker start stress_redis

# Expected recovery:
# - API resumes accepting new jobs within ~30 seconds
# - Celery worker reconnects and processes previously queued jobs
```

**Document in your report**: Time to first failure, time to recovery, number of failed requests.

---

### Test 2: Postgres Failure During Normal Load

**What happens when the database goes down?**

```bash
# Terminal 1: Start normal mixed load
locust -f locustfiles/mixed_workload.py \
  --host=http://localhost:8000 --users=50 --spawn-rate=10

# Terminal 2: Kill Postgres after 1 minute
sleep 60 && docker stop stress_postgres

# Expected behaviour:
# - All endpoints requiring DB return 500
# - /health endpoint may still return 200 (if it doesn't check DB)
# - No data corruption

# Restore
sleep 60 && docker start stress_postgres

# Expected recovery:
# - API resumes within 30 seconds (SQLAlchemy connection pool reconnects)
```

---

### Test 3: Simulate Slow Database (Resource Starvation)

**Simulate a degraded database by limiting CPU.**

```bash
# Update docker-compose.stress.yml to limit Postgres to 0.1 CPU and restart
docker compose -f docker-compose.stress.yml up -d --scale db=1

# Apply resource update on the fly
docker update --cpus="0.1" stress_postgres

# Run 30 users
locust -f locustfiles/mixed_workload.py \
  --host=http://localhost:8000 --users=30 --spawn-rate=5 --run-time=3m

# Expected behaviour: P95 for DB-touching endpoints degrades but API doesn't crash
# Restore
docker update --cpus="1.0" stress_postgres
```

---

### Teardown

After all tests are complete:

```bash
# Stop and remove all stress test containers + volumes
cd webapp/testing/stress
docker compose -f docker-compose.stress.yml down -v

# This removes: stress_postgres, stress_redis, stress_minio, stress_api, stress_worker
# and deletes all volume data (fresh start next time)
```

---

## 13. Troubleshooting

| Problem | Cause | Solution |
|---|---|---|
| `Connection refused` when starting Locust | FastAPI container is not running or not healthy | Check `docker compose -f docker-compose.stress.yml ps`. Wait for `healthy` status on all services. |
| `Migrations failed` during startup | Postgres container not fully initialised when API starts | The `depends_on: condition: service_healthy` healthcheck should prevent this. If it still fails, wait 30 seconds and retry: `docker exec stress_api sh -c "uv run alembic upgrade head"` |
| Locust shows 500 errors for all endpoints | Environment variables wrong in docker-compose | Check `docker logs stress_api` for startup errors |
| Classification jobs stuck in "queued" | Celery worker is not connected to Redis | Check `docker logs stress_worker`. Ensure Redis is healthy. |
| `docker build` fails | Missing Dockerfile or wrong context path | Ensure `Dockerfile.api` is in `webapp/testing/stress/`. Run `docker build -f webapp/testing/stress/Dockerfile.api webapp/backend/` to test. |
| Locust error: `ModuleNotFoundError: locust` | Locust venv not activated | Run `source webapp/testing/stress/.venv/bin/activate` before locust commands |
| High error rates immediately | Test users failing to sign up (email collisions or timing) | `uuid.hex[:8]` should prevent this — if it persists, increase the suffix length to `[:12]` |
| `max_connections` error from Postgres | Too many concurrent DB connections | Reduce `--users` count, or add a PgBouncer connection pooler in `docker-compose.stress.yml` |
| Docker containers OOM-killed during test | Resource limits too tight | Increase `memory` in the `deploy.resources.limits` section of `docker-compose.stress.yml` |

---

*Update this document whenever new API endpoints are added — each new route should have a corresponding Locust task in the appropriate test file.*
