# LangID Platform — Testing Guide

A comprehensive reference for setting up, writing, and running tests for the **Sinhala-Script Language Identification Platform** (`webapp`). This guide covers the **Backend** (FastAPI) and **Frontend** (Next.js) test suites, including unit testing, integration testing, environment setup, test authoring patterns, and reporting.

---

## Table of Contents

1. [Project Architecture Overview](#1-project-architecture-overview)
2. [Test Strategy & Coverage Map](#2-test-strategy--coverage-map)
3. [Backend Testing (FastAPI / Python)](#3-backend-testing-fastapi--python)
   - 3.1 [Prerequisites](#31-prerequisites)
   - 3.2 [Framework & Tooling](#32-framework--tooling)
   - 3.3 [Setting Up the Test Environment](#33-setting-up-the-test-environment)
   - 3.4 [Understanding `conftest.py`](#34-understanding-conftestpy)
   - 3.5 [Directory Structure](#35-directory-structure)
   - 3.6 [Writing Unit Tests](#36-writing-unit-tests)
   - 3.7 [Writing Integration Tests](#37-writing-integration-tests)
   - 3.8 [Running Backend Tests](#38-running-backend-tests)
   - 3.9 [Backend Test Reports](#39-backend-test-reports)
4. [Frontend Testing (Next.js / TypeScript)](#4-frontend-testing-nextjs--typescript)
   - 4.1 [Prerequisites](#41-prerequisites)
   - 4.2 [Framework & Tooling](#42-framework--tooling)
   - 4.3 [Setting Up the Test Environment](#43-setting-up-the-test-environment)
   - 4.4 [Directory Structure](#44-directory-structure)
   - 4.5 [Writing Unit / Component Tests](#45-writing-unit--component-tests)
   - 4.6 [Writing E2E Integration Tests (Playwright)](#46-writing-e2e-integration-tests-playwright)
   - 4.7 [Running Frontend Tests](#47-running-frontend-tests)
   - 4.8 [Frontend Test Reports](#48-frontend-test-reports)
5. [Stress & Performance Testing](#5-stress--performance-testing)
   - 5.1 [Prerequisites & Setup](#51-prerequisites--setup)
   - 5.2 [Running the Tests](#52-running-the-tests)
   - 5.3 [Test Scenarios](#53-test-scenarios)
6. [Complete Coverage Checklist (RUP Template Mapping)](#6-complete-coverage-checklist-rup-template-mapping)
7. [CI/CD Integration Notes](#7-cicd-integration-notes)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Project Architecture Overview

Understanding the application architecture is essential for knowing *what* to test and *how* different modules interact.

```
webapp/
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── api/v1/             # HTTP route handlers
│   │   │   ├── auth.py         # POST /auth/signup, /auth/login, /auth/refresh
│   │   │   ├── users.py        # GET/PATCH /users/me
│   │   │   ├── documents.py    # CRUD for uploaded documents
│   │   │   ├── classification.py # POST /classification/submit, /classify/text
│   │   │   ├── annotations.py  # CRUD for language annotations
│   │   │   ├── usage.py        # GET /usage/summary, /usage/records
│   │   │   ├── admin.py        # Admin user/subscription management
│   │   │   ├── admin_rates.py  # Admin model rate management
│   │   │   └── websockets.py   # WS /ws/jobs/{job_id}
│   │   ├── db/
│   │   │   ├── models/         # SQLAlchemy ORM models
│   │   │   │   ├── user.py, document.py, annotation.py
│   │   │   │   ├── classification_job.py, classified_segment.py
│   │   │   │   ├── subscription.py, tier.py, usage_record.py
│   │   │   │   ├── model_rate.py, system_config.py
│   │   │   └── session.py      # AsyncEngine + SessionMaker
│   │   ├── ml/
│   │   │   ├── base.py         # Abstract classifier base class
│   │   │   └── sklearn_langid.py # Scikit-learn LangID classifier
│   │   ├── services/           # Business logic layer
│   │   │   ├── auth_service.py, user_service.py
│   │   │   ├── credit_service.py, storage_service.py
│   │   │   └── admin_service.py
│   │   ├── workers/
│   │   │   ├── celery_app.py   # Celery app + Redis broker config
│   │   │   └── tasks/
│   │   │       ├── ocr_tasks.py         # Celery task: OCR processing
│   │   │       └── classification_tasks.py # Celery task: LangID
│   │   ├── config.py           # Pydantic Settings
│   │   ├── dependencies.py     # FastAPI dependency injection (get_db, auth)
│   │   └── main.py             # FastAPI app entrypoint
│   ├── tests/
│   │   ├── conftest.py         # Fixtures + Testcontainers + Alembic setup
│   │   ├── unit/               # Pure unit tests (no I/O)
│   │   └── integration/        # Integration tests with real DB + Redis
│   ├── alembic/                # Database migration scripts
│   └── pyproject.toml
│
└── frontend/                   # Next.js 16 application
    ├── src/
    │   ├── app/
    │   │   ├── page.tsx             # Landing / Home page
    │   │   ├── auth/                # Login / signup pages
    │   │   ├── dashboard/           # User dashboard
    │   │   └── admin/               # Admin panel pages
    │   ├── components/
    │   │   ├── ui/                  # Shadcn/base-ui primitives
    │   │   ├── dashboard/           # Dashboard-specific components
    │   │   ├── documents/           # Document upload/list components
    │   │   ├── layout/              # Sidebar, Navbar, etc.
    │   │   └── admin/               # Admin panel components
    │   ├── context/                 # React context providers
    │   └── lib/                     # Utility functions, API clients
    ├── src/__tests__/               # Vitest unit/component tests
    ├── tests/e2e/                   # Playwright E2E tests
    ├── vitest.config.ts
    ├── playwright.config.ts
    └── package.json
```

---

## 2. Test Strategy & Coverage Map

We adopt a two-level strategy that maps directly to the RUP testing template provided for this project:

| RUP Template Section | Testing Layer | Framework | Description |
|---|---|---|---|
| **Function Testing** | Unit + Integration | pytest / Vitest | Verify business logic and API contracts |
| **Data & Database Integrity** | Integration (Backend) | pytest + testcontainers | Verify ORM models, constraints, migrations |
| **User Interface Testing** | E2E Integration (Frontend) | Playwright | Verify UI navigation, forms, and state |
| **Security & Access Control** | Unit + Integration (Backend) | pytest + httpx | Verify JWT auth and RBAC |
| **Configuration Testing** | Unit (Backend) | pytest | Verify settings overrides and env parsing |
| **Failover & Recovery** | Integration (Backend) | pytest | Verify graceful errors on service unavailability |

### Application Areas to Test

| Area | Module Path(s) | Test Level |
|---|---|---|
| Authentication (signup, login, refresh, JWT) | `api/v1/auth.py`, `services/auth_service.py` | Unit + Integration |
| User Profile | `api/v1/users.py`, `services/user_service.py` | Integration |
| Document Upload & Management | `api/v1/documents.py` | Integration |
| Language Classification (text input) | `api/v1/classification.py` | Integration |
| ML Model (Scikit-learn LangID) | `ml/sklearn_langid.py` | Unit |
| OCR Celery Task | `workers/tasks/ocr_tasks.py` | Unit (mocked) |
| Classification Celery Task | `workers/tasks/classification_tasks.py` | Unit (mocked) |
| Credit / Subscription System | `services/credit_service.py` | Unit + Integration |
| Annotations CRUD | `api/v1/annotations.py` | Integration |
| Admin Panel APIs | `api/v1/admin.py`, `api/v1/admin_rates.py` | Integration |
| Usage Records | `api/v1/usage.py` | Integration |
| DB Models & Relationships | `db/models/*.py` | Integration |
| Frontend: Auth Pages | `src/app/auth/` | E2E (Playwright) |
| Frontend: Dashboard | `src/app/dashboard/` | E2E (Playwright) |
| Frontend: Document Upload Form | `src/components/documents/` | Unit (Vitest) + E2E |
| Frontend: Admin Panel | `src/app/admin/` | E2E (Playwright) |

---

## 3. Backend Testing (FastAPI / Python)

### 3.1 Prerequisites

Before running backend tests, ensure the following are installed:

- **Python 3.12+**: Check with `python3 --version`
- **uv** (Python package manager): Install from [https://docs.astral.sh/uv/](https://docs.astral.sh/uv/)
- **Docker Engine**: Testcontainers requires Docker to spin up Postgres and Redis containers.
  - Verify with: `docker --version` and `docker ps`
  - On Linux, ensure your user is in the `docker` group: `sudo usermod -aG docker $USER`

### 3.2 Framework & Tooling

| Tool | Purpose |
|---|---|
| `pytest` | Primary test runner |
| `pytest-asyncio` | Run async test functions natively with `asyncio` |
| `pytest-mock` | Provides the `mocker` fixture for mocking with `unittest.mock` |
| `httpx` (AsyncClient) | HTTP client to call FastAPI routes in tests without a real server |
| `testcontainers[postgres,redis]` | Automatically spins up isolated Docker containers for Postgres and Redis |
| `alembic` | Runs schema migrations against the test database container |

### 3.3 Setting Up the Test Environment

#### Step 1: Sync dependencies

From the `backend/` directory, run:

```bash
cd webapp/backend
uv sync --all-extras
```

This installs all production dependencies *and* the `dev` extras (`pytest`, `pytest-asyncio`, `httpx`, `testcontainers`, `pytest-mock`, etc.) from the `[project.optional-dependencies] dev` section in `pyproject.toml`.

#### Step 2: Verify Docker is running

```bash
docker info
# Should display Docker Engine info without errors
```

#### Step 3: Confirm the test suite initialises

```bash
uv run pytest --collect-only
```

You should see the test files collected without any errors. The containers will start at this point.

### 3.4 Understanding `conftest.py`

The file at `tests/conftest.py` is the central hub for the backend test setup. It runs **automatically** before any test is collected.

```python
# tests/conftest.py — annotated walkthrough

import os
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from alembic.config import Config
from alembic import command

# ── 1. MinIO Mock ──────────────────────────────────────────────────────────────
# MinIO's StorageService tries to connect immediately on import.
# We mock the Minio class at the module level BEFORE the app is imported
# to prevent a ConnectionRefusedError during test collection.
patcher = patch("minio.Minio")
patcher.start()

# ── 2. Docker Containers ───────────────────────────────────────────────────────
# Testcontainers starts real Docker containers that are destroyed after tests.
# This ensures tests NEVER touch your local development database.
postgres = PostgresContainer("postgres:15-alpine")
redis = RedisContainer("redis:7-alpine")
postgres.start()
redis.start()

# ── 3. Environment Override ────────────────────────────────────────────────────
# We override the environment variables BEFORE importing `app`.
# This is critical: pydantic-settings reads env vars at import time,
# so the Settings object will reflect the testcontainer's dynamic port.
os.environ["POSTGRES_USER"] = postgres.username
os.environ["POSTGRES_PASSWORD"] = postgres.password
os.environ["POSTGRES_SERVER"] = postgres.get_container_host_ip()
os.environ["POSTGRES_PORT"] = str(postgres.get_exposed_port(5432))
os.environ["POSTGRES_DB"] = postgres.dbname
os.environ["REDIS_HOST"] = redis.get_container_host_ip()
os.environ["REDIS_PORT"] = str(redis.get_exposed_port(6379))

from app.main import app  # Import AFTER env vars are set

# ── 4. Alembic Migrations ──────────────────────────────────────────────────────
# Applies all pending database migrations to the fresh container.
# Integration tests will see the same schema as production.
def run_migrations():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

run_migrations()

# ── 5. Fixtures ────────────────────────────────────────────────────────────────
@pytest.fixture(scope="session", autouse=True)
def cleanup_containers():
    """Stops and removes all Docker containers after the test session."""
    yield
    postgres.stop()
    redis.stop()

@pytest.fixture
async def async_client():
    """Provides an async HTTP client bound to the FastAPI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
```

**Key design decisions:**
- Containers are started at **module scope** (once per session) for speed.
- Environment variables are patched **before** `app` is imported — this is required for Pydantic Settings to pick them up.
- The `async_client` fixture is **function-scoped** by default — each test gets a fresh client but shares the same DB.

### 3.5 Directory Structure

```
backend/tests/
├── conftest.py              # Session-level setup: containers, migrations, fixtures
├── unit/
│   ├── test_unit.py         # Sample unit test placeholder
│   ├── test_auth_service.py # JWT token creation, password hashing
│   ├── test_ml_classifier.py# ML model: predict() output validation
│   ├── test_credit_service.py # Credit deduction logic
│   └── test_config.py       # Pydantic settings / env parsing
└── integration/
    ├── test_integration.py  # Sample integration test placeholder
    ├── test_auth.py         # Signup, login, refresh token flows
    ├── test_users.py        # User profile read / update
    ├── test_documents.py    # Document upload, list, delete
    ├── test_classification.py # Text classification endpoint
    ├── test_annotations.py  # Annotation CRUD
    ├── test_admin.py        # Admin-only endpoints + RBAC
    ├── test_usage.py        # Usage records
    └── test_db_integrity.py # ORM model constraints
```

### 3.6 Writing Unit Tests

Unit tests belong in `tests/unit/`. They test **pure functions** and **logic in isolation**, without touching the database, filesystem, or network.

#### Pattern: Test a utility function

```python
# tests/unit/test_auth_service.py
from app.services.auth_service import AuthService

def test_password_hashing():
    """Password hashing should produce a unique, verifiable hash."""
    service = AuthService()
    hashed = service.hash_password("my-secret-password")
    
    assert hashed != "my-secret-password"                    # Should not be plain text
    assert service.verify_password("my-secret-password", hashed)  # Should verify
    assert not service.verify_password("wrong-password", hashed)   # Wrong password fails
```

#### Pattern: Test the ML Classifier

```python
# tests/unit/test_ml_classifier.py
from app.ml.sklearn_langid import SklearnLangIDClassifier

def test_predict_returns_valid_label():
    """Classifier must return a label from the known set {sinhala, pali, sanskrit}."""
    classifier = SklearnLangIDClassifier()
    result = classifier.predict("ශ්‍රී ලංකාව ලස්සන රටකි")  # Sinhala text
    
    assert result is not None
    assert result["language"] in ["sinhala", "pali", "sanskrit", "unknown"]
    assert 0.0 <= result["confidence"] <= 1.0

def test_predict_with_empty_string():
    """Classifier should handle empty input gracefully."""
    classifier = SklearnLangIDClassifier()
    result = classifier.predict("")
    assert result is not None  # Should not raise, should return a default
```

#### Pattern: Mock external dependencies with `pytest-mock`

```python
# tests/unit/test_credit_service.py
import pytest

@pytest.mark.asyncio
async def test_deduct_credit_calls_db(mocker):
    """CreditService.deduct() should update the user's credit balance in the DB."""
    mock_db = mocker.AsyncMock()  # Mock the DB session
    mock_user = mocker.MagicMock(credit_balance=100)
    
    from app.services.credit_service import CreditService
    service = CreditService()
    await service.deduct(db=mock_db, user=mock_user, amount=10)
    
    assert mock_user.credit_balance == 90
    mock_db.commit.assert_called_once()
```

#### Pattern: Test Celery tasks without a real worker

```python
# tests/unit/test_ocr_task.py
import pytest
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_ocr_task_calls_tesseract(mocker):
    """OCR task should invoke pytesseract.image_to_string for each page."""
    mock_tesseract = mocker.patch("app.workers.tasks.ocr_tasks.pytesseract.image_to_string")
    mock_tesseract.return_value = "sample OCR output"
    
    # Call the inner async logic of the task, not .delay() or .apply_async()
    from app.workers.tasks.ocr_tasks import _run_ocr_on_page
    result = await _run_ocr_on_page(image_path="/fake/path.png")
    
    mock_tesseract.assert_called_once()
    assert result == "sample OCR output"
```

### 3.7 Writing Integration Tests

Integration tests belong in `tests/integration/`. They use the real PostgreSQL container (already migrated) and the `async_client` fixture to test complete HTTP request/response flows.

#### Pattern: Authentication flow

```python
# tests/integration/test_auth.py
import pytest

@pytest.mark.asyncio
async def test_signup_creates_user(async_client):
    """POST /auth/signup should create a new user and return a 201."""
    payload = {
        "email": "testuser@example.com",
        "password": "StrongPassword123!",
        "full_name": "Test User"
    }
    response = await async_client.post("/api/v1/auth/signup", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert "password" not in data  # Password must never be in response

@pytest.mark.asyncio
async def test_login_returns_tokens(async_client):
    """POST /auth/login should return both access and refresh tokens."""
    # First create the user
    await async_client.post("/api/v1/auth/signup", json={
        "email": "logintest@example.com", "password": "Pass123!", "full_name": "Login Test"
    })
    # Now login
    response = await async_client.post("/api/v1/auth/login", json={
        "email": "logintest@example.com", "password": "Pass123!"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_with_wrong_password_returns_401(async_client):
    """POST /auth/login with wrong credentials should return 401."""
    response = await async_client.post("/api/v1/auth/login", json={
        "email": "logintest@example.com", "password": "WrongPassword"
    })
    assert response.status_code == 401
```

#### Pattern: Helper fixture for an authenticated client

Add this fixture to `conftest.py` or a module-level fixture file for reuse across integration tests:

```python
# tests/conftest.py (add this helper fixture)
import pytest

@pytest.fixture
async def auth_headers(async_client) -> dict:
    """Creates a test user and returns authorization headers."""
    await async_client.post("/api/v1/auth/signup", json={
        "email": "fixture_user@test.com",
        "password": "TestPass123!",
        "full_name": "Fixture User"
    })
    login_resp = await async_client.post("/api/v1/auth/login", json={
        "email": "fixture_user@test.com",
        "password": "TestPass123!"
    })
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
async def admin_headers(async_client) -> dict:
    """Returns authorization headers for an admin user.
    Note: Requires INITIAL_ADMIN_EMAIL and INITIAL_ADMIN_PASSWORD env vars to be set
    for the admin user to be seeded, or create an admin manually here.
    """
    # Implementation depends on admin seeding strategy
    ...
```

#### Pattern: Document upload test

```python
# tests/integration/test_documents.py
import pytest
from io import BytesIO

@pytest.mark.asyncio
async def test_upload_document(async_client, auth_headers, mocker):
    """POST /documents should accept a PDF file and return document metadata."""
    # Mock MinIO storage to avoid actual file upload
    mocker.patch("app.services.storage_service.StorageService.upload_file", return_value="fake-object-key")
    
    fake_pdf = BytesIO(b"%PDF-1.4 fake content")
    fake_pdf.name = "test.pdf"
    
    response = await async_client.post(
        "/api/v1/documents",
        headers=auth_headers,
        files={"file": ("test.pdf", fake_pdf, "application/pdf")}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "test.pdf"
    assert "id" in data
```

#### Pattern: Database integrity test

```python
# tests/integration/test_db_integrity.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import AsyncSessionLocal

@pytest.mark.asyncio
async def test_user_email_unique_constraint():
    """The users table should reject duplicate email addresses."""
    async with AsyncSessionLocal() as session:
        await session.execute(text(
            "INSERT INTO users (email, hashed_password, full_name) "
            "VALUES ('unique@test.com', 'hash', 'User A')"
        ))
        await session.commit()
        
        with pytest.raises(Exception):  # Expect IntegrityError
            await session.execute(text(
                "INSERT INTO users (email, hashed_password, full_name) "
                "VALUES ('unique@test.com', 'hash2', 'User B')"
            ))
            await session.commit()
```

#### Pattern: RBAC / Security test

```python
# tests/integration/test_admin.py
import pytest

@pytest.mark.asyncio
async def test_regular_user_cannot_access_admin_endpoint(async_client, auth_headers):
    """A non-admin user accessing an admin-only route should receive 403."""
    response = await async_client.get(
        "/api/v1/admin/users",
        headers=auth_headers  # Regular user token
    )
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_unauthenticated_request_returns_401(async_client):
    """Any protected route without a token should return 401."""
    response = await async_client.get("/api/v1/users/me")
    assert response.status_code == 401
```

### 3.8 Running Backend Tests

All commands are run from the `webapp/backend/` directory.

```bash
# Run the full test suite
uv run pytest

# Run only unit tests
uv run pytest tests/unit/

# Run only integration tests
uv run pytest tests/integration/

# Run a specific test file
uv run pytest tests/integration/test_auth.py

# Run a specific test by name
uv run pytest tests/integration/test_auth.py::test_login_returns_tokens

# Run with verbose output
uv run pytest -v

# Run with stdout capture disabled (see print statements)
uv run pytest -s

# Run and stop on the first failure
uv run pytest -x

# Run only tests marked with a specific marker
uv run pytest -m "slow"      # requires @pytest.mark.slow on tests
```

### 3.9 Backend Test Reports

#### Terminal summary (default)

The `pytest.ini` is already configured with `-v --tb=short` for concise tracebacks.

#### HTML report

Install `pytest-html` and generate a full HTML report:

```bash
uv pip install pytest-html
uv run pytest --html=reports/backend_report.html --self-contained-html
```

Open `backend/reports/backend_report.html` in your browser.

#### Coverage report

Install `pytest-cov`:

```bash
uv pip install pytest-cov
uv run pytest --cov=app --cov-report=html:reports/coverage_html
```

Open `backend/reports/coverage_html/index.html` in your browser.

```bash
# For a quick terminal coverage summary
uv run pytest --cov=app --cov-report=term-missing
```

#### JUnit XML (for CI/CD systems like GitHub Actions, Jenkins)

```bash
uv run pytest --junitxml=reports/junit.xml
```

---

## 4. Frontend Testing (Next.js / TypeScript)

### 4.1 Prerequisites

- **Node.js 20+**: Check with `node --version`
- **npm**: Included with Node.js
- **Chromium browser binaries**: Required by Playwright. Already downloaded after initial setup.

### 4.2 Framework & Tooling

| Tool | Purpose |
|---|---|
| `Vitest` | Ultra-fast unit and component test runner (Vite-native) |
| `@testing-library/react` | Render React components and query the DOM in tests |
| `@testing-library/jest-dom` | Custom DOM matchers: `toBeInTheDocument()`, `toBeVisible()`, etc. |
| `jsdom` | Simulates a browser DOM environment in Node.js (for Vitest) |
| `@vitejs/plugin-react` | Enables JSX/TSX transformation in Vitest |
| `Playwright` | Full browser automation for E2E / integration tests |

### 4.3 Setting Up the Test Environment

From the `webapp/frontend/` directory:

```bash
# Install all dependencies (includes testing libs)
npm install

# Playwright browsers were installed on initial setup.
# If you need to reinstall them:
npx playwright install
```

> **Note:** On the first setup, run `npx playwright install --with-deps` if your system is missing browser dependencies (requires sudo for system packages).

### 4.4 Directory Structure

```
frontend/
├── vitest.config.ts             # Vitest configuration (unit/component tests)
├── vitest.setup.ts              # jest-dom matchers import
├── playwright.config.ts         # Playwright configuration (E2E tests)
├── src/
│   └── __tests__/               # Unit / component tests live here
│       ├── sample.test.tsx      # Placeholder
│       ├── components/
│       │   ├── LoginForm.test.tsx
│       │   ├── DocumentUpload.test.tsx
│       │   └── AnnotationPanel.test.tsx
│       └── lib/
│           └── utils.test.ts
└── tests/
    └── e2e/                     # Playwright E2E tests live here
        ├── sample.spec.ts       # Placeholder
        ├── auth.spec.ts         # Login, signup, logout flows
        ├── dashboard.spec.ts    # Dashboard navigation
        ├── document-upload.spec.ts # Upload and view results
        └── admin.spec.ts        # Admin panel flows
```

### 4.5 Writing Unit / Component Tests

Unit tests are located in `src/__tests__/` and use `.test.tsx` or `.test.ts` extensions. They are picked up automatically by Vitest.

#### Pattern: Test a React component renders correctly

```typescript
// src/__tests__/components/LoginForm.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import LoginForm from '@/components/auth/LoginForm';

describe('LoginForm', () => {
  it('renders email and password inputs', () => {
    render(<LoginForm onSubmit={vi.fn()} />);
    
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /log in/i })).toBeInTheDocument();
  });

  it('shows validation error for invalid email', async () => {
    render(<LoginForm onSubmit={vi.fn()} />);
    
    const emailInput = screen.getByLabelText(/email/i);
    fireEvent.change(emailInput, { target: { value: 'not-an-email' } });
    fireEvent.blur(emailInput);
    
    expect(await screen.findByText(/invalid email/i)).toBeInTheDocument();
  });

  it('calls onSubmit with form data when valid', async () => {
    const mockSubmit = vi.fn();
    render(<LoginForm onSubmit={mockSubmit} />);
    
    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'user@test.com' }
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'Password123!' }
    });
    fireEvent.click(screen.getByRole('button', { name: /log in/i }));
    
    // Wait for async form submission
    await vi.waitFor(() => {
      expect(mockSubmit).toHaveBeenCalledWith({
        email: 'user@test.com',
        password: 'Password123!'
      });
    });
  });
});
```

#### Pattern: Test a Zod validation schema

```typescript
// src/__tests__/lib/validation.test.ts
import { describe, it, expect } from 'vitest';
import { loginSchema } from '@/lib/schemas'; // your Zod schema

describe('loginSchema', () => {
  it('accepts valid credentials', () => {
    const result = loginSchema.safeParse({
      email: 'user@example.com',
      password: 'ValidPass123!'
    });
    expect(result.success).toBe(true);
  });

  it('rejects empty email', () => {
    const result = loginSchema.safeParse({ email: '', password: 'ValidPass123!' });
    expect(result.success).toBe(false);
  });

  it('rejects password shorter than 8 characters', () => {
    const result = loginSchema.safeParse({ email: 'a@b.com', password: 'short' });
    expect(result.success).toBe(false);
  });
});
```

#### Pattern: Test a utility function

```typescript
// src/__tests__/lib/utils.test.ts
import { describe, it, expect } from 'vitest';
import { formatLanguageLabel } from '@/lib/utils';

describe('formatLanguageLabel', () => {
  it('capitalizes sinhala correctly', () => {
    expect(formatLanguageLabel('sinhala')).toBe('Sinhala');
  });
  it('handles unknown language', () => {
    expect(formatLanguageLabel('unknown')).toBe('Unknown');
  });
});
```

#### Pattern: Mock API calls with `vi.mock`

```typescript
// src/__tests__/components/DocumentList.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import DocumentList from '@/components/documents/DocumentList';

// Mock the axios API module
vi.mock('@/lib/api', () => ({
  api: {
    get: vi.fn().mockResolvedValue({
      data: [
        { id: '1', filename: 'sinhala_text.pdf', status: 'classified', created_at: '2025-01-01' }
      ]
    })
  }
}));

describe('DocumentList', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  });

  it('renders a list of documents', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <DocumentList />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('sinhala_text.pdf')).toBeInTheDocument();
    });
  });
});
```

### 4.6 Writing E2E Integration Tests (Playwright)

E2E tests live in `tests/e2e/` and use the `.spec.ts` extension. Playwright automatically starts the Next.js dev server before running them (configured in `playwright.config.ts`).

#### Pattern: User authentication flow

```typescript
// tests/e2e/auth.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('user can sign up and reach the dashboard', async ({ page }) => {
    await page.goto('/auth/signup');
    
    await page.getByLabel('Full Name').fill('Test User');
    await page.getByLabel('Email').fill('e2etest@example.com');
    await page.getByLabel('Password').fill('Password123!');
    await page.getByRole('button', { name: /sign up/i }).click();
    
    // After successful signup, the user should be redirected to dashboard
    await expect(page).toHaveURL('/dashboard');
    await expect(page.getByText('Welcome, Test User')).toBeVisible();
  });

  test('shows error for wrong credentials', async ({ page }) => {
    await page.goto('/auth/login');
    
    await page.getByLabel('Email').fill('wrong@example.com');
    await page.getByLabel('Password').fill('WrongPassword');
    await page.getByRole('button', { name: /log in/i }).click();
    
    await expect(page.getByText(/invalid credentials/i)).toBeVisible();
  });

  test('unauthenticated user is redirected to login', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL('/auth/login');
  });
});
```

#### Pattern: Document upload and classification flow

```typescript
// tests/e2e/document-upload.spec.ts
import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('Document Upload', () => {
  // Log in before each test
  test.beforeEach(async ({ page }) => {
    await page.goto('/auth/login');
    await page.getByLabel('Email').fill('e2etest@example.com');
    await page.getByLabel('Password').fill('Password123!');
    await page.getByRole('button', { name: /log in/i }).click();
    await page.waitForURL('/dashboard');
  });

  test('user can upload a PDF document', async ({ page }) => {
    await page.goto('/dashboard/documents');
    
    // Trigger file input
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(path.join(__dirname, 'fixtures/sinhala_sample.pdf'));
    
    await page.getByRole('button', { name: /upload/i }).click();
    
    // Expect the document to appear in the list
    await expect(page.getByText('sinhala_sample.pdf')).toBeVisible({ timeout: 10000 });
  });

  test('classification results are displayed after processing', async ({ page }) => {
    await page.goto('/dashboard/documents');
    
    // Click on an already-classified document
    await page.getByText('sinhala_sample.pdf').click();
    
    // Expect classification results to be visible
    await expect(page.getByTestId('classification-results')).toBeVisible();
    await expect(page.getByText(/sinhala|pali|sanskrit/i)).toBeVisible();
  });
});
```

#### Pattern: Admin panel access test

```typescript
// tests/e2e/admin.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Admin Panel', () => {
  test('admin can view all users', async ({ page }) => {
    // Login as admin
    await page.goto('/auth/login');
    await page.getByLabel('Email').fill(process.env.ADMIN_EMAIL!);
    await page.getByLabel('Password').fill(process.env.ADMIN_PASSWORD!);
    await page.getByRole('button', { name: /log in/i }).click();
    await page.waitForURL('/dashboard');
    
    await page.goto('/admin/users');
    await expect(page.getByRole('table')).toBeVisible();
    await expect(page.getByRole('row')).toHaveCount.callCount > 1; // At least 1 user row
  });

  test('regular user cannot access admin page', async ({ page }) => {
    // Login as regular user
    await page.goto('/auth/login');
    await page.getByLabel('Email').fill('e2etest@example.com');
    await page.getByLabel('Password').fill('Password123!');
    await page.getByRole('button', { name: /log in/i }).click();
    
    await page.goto('/admin/users');
    // Should be redirected or shown an access denied page
    await expect(page).not.toHaveURL('/admin/users');
  });
});
```

### 4.7 Running Frontend Tests

All commands are run from the `webapp/frontend/` directory.

```bash
# Run all Vitest unit/component tests (interactive watch mode)
npm run test

# Run Vitest once (CI mode, no watch)
npm run test -- --run

# Run a specific test file
npm run test -- --run src/__tests__/components/LoginForm.test.tsx

# Run all Playwright E2E tests
npm run test:e2e

# Run E2E tests in headed mode (see the browser)
npx playwright test --headed

# Run a specific Playwright test file
npx playwright test tests/e2e/auth.spec.ts

# Run E2E tests in UI mode (interactive Playwright UI)
npx playwright test --ui
```

### 4.8 Frontend Test Reports

#### Vitest terminal output

Vitest shows a colour-coded pass/fail report in the terminal by default.

#### Vitest HTML report

```bash
npm run test -- --run --reporter=html
# Opens at: http://localhost:51204 (or similar port printed in terminal)
```

#### Vitest coverage

```bash
npm install -D @vitest/coverage-v8  # install once
npm run test -- --run --coverage
# Coverage report at: frontend/coverage/index.html
```

#### Playwright HTML report

After running `npm run test:e2e`, Playwright automatically generates an HTML report:

```bash
# Open the last Playwright report
npx playwright show-report
# Report is saved at: frontend/playwright-report/index.html
```

The report includes:
- Pass/fail status per test
- Screenshots on failure
- Video recordings of failed tests (if configured)
- Network traces for debugging

#### Playwright trace viewer (for debugging failures)

Playwright saves traces on first retry. You can view them with:

```bash
npx playwright show-trace path/to/trace.zip
```

---

## 5. Stress & Performance Testing

For a complete guide to our Docker-based Locust testing infrastructure, see the dedicated README at [`webapp/testing/stress/README.md`](file:///home/vihanga/Desktop/programming/Sinhala-Script-Language-Identification-LangID-for-Sinhala-Pali-and-Sanskrit/webapp/testing/stress/README.md).

### 5.1 Prerequisites & Setup

The stress testing environment is isolated from local development. It uses a dedicated `docker-compose.stress.yml` which runs the entire application stack (API, Worker, Postgres, Redis, MinIO) with resource limits to simulate production.

To bootstrap the environment:
```bash
cd webapp/testing/stress
bash scripts/setup.sh
```
This command builds the Docker images, starts the containers, waits for them to become healthy, runs database migrations, and provisions a Python virtual environment with Locust.

### 5.2 Running the Tests

**Automated Mixed Workload (Headless)**
Run the primary load simulation (15 minutes, ramping from 10 to 200 users) using the helper script. HTML and CSV reports are automatically saved to `webapp/testing/stress/reports/`.
```bash
cd webapp/testing/stress
bash scripts/run_mixed.sh
```

**Interactive (Web UI)**
1. Activate the Locust virtual environment: `source webapp/testing/stress/.venv/bin/activate`
2. Run locust: `locust -f locustfiles/mixed_workload.py --host=http://localhost:8000`
3. Open `http://localhost:8089` in your browser.

**Cleanup**
```bash
cd webapp/testing/stress
bash scripts/teardown.sh
```

### 5.3 Test Scenarios

Stress test files are stored in `webapp/testing/stress/locustfiles/`:
- `mixed_workload.py`: The main E2E test balancing read-heavy users (50%), classification power-users (30%), and document uploaders (20%).
- `auth_load.py`: Isolated testing of the authentication endpoints.
- `classification_load.py`: Tests the ML async pipeline and Celery queue saturation.
- `document_load.py`: Tests MinIO upload throughput and concurrent database writes.

---

## 6. Complete Coverage Checklist (RUP Template Mapping)

Use this checklist to track which areas of the RUP template have been covered by actual test cases.

### 6.1 Function Testing

| Feature / Use Case | Test File | Test Level | Status |
|---|---|---|---|
| User Registration (valid input) | `integration/test_auth.py` | Integration | ⬜ |
| User Registration (duplicate email) | `integration/test_auth.py` | Integration | ⬜ |
| Login (valid credentials) | `integration/test_auth.py` | Integration | ⬜ |
| Login (invalid credentials) | `integration/test_auth.py` | Integration | ⬜ |
| Token Refresh | `integration/test_auth.py` | Integration | ⬜ |
| Get User Profile | `integration/test_users.py` | Integration | ⬜ |
| Update User Profile | `integration/test_users.py` | Integration | ⬜ |
| Upload Document (PDF) | `integration/test_documents.py` | Integration | ⬜ |
| List Documents | `integration/test_documents.py` | Integration | ⬜ |
| Delete Document | `integration/test_documents.py` | Integration | ⬜ |
| Classify Text (direct input) | `integration/test_classification.py` | Integration | ⬜ |
| Submit Document for Classification | `integration/test_classification.py` | Integration | ⬜ |
| ML Predict function | `unit/test_ml_classifier.py` | Unit | ⬜ |
| ML handles edge cases (empty, Unicode) | `unit/test_ml_classifier.py` | Unit | ⬜ |
| OCR task invokes tesseract | `unit/test_ocr_task.py` | Unit | ⬜ |
| Get Usage Summary | `integration/test_usage.py` | Integration | ⬜ |
| Get Usage Records | `integration/test_usage.py` | Integration | ⬜ |
| Create Annotation | `integration/test_annotations.py` | Integration | ⬜ |
| Update Annotation | `integration/test_annotations.py` | Integration | ⬜ |
| Delete Annotation | `integration/test_annotations.py` | Integration | ⬜ |
| Admin: List Users | `integration/test_admin.py` | Integration | ⬜ |
| Admin: Update User Tier | `integration/test_admin.py` | Integration | ⬜ |
| Admin: Create Model Rate | `integration/test_admin.py` | Integration | ⬜ |

### 6.2 Data & Database Integrity Testing

| Test Scenario | Test File | Status |
|---|---|---|
| User email unique constraint | `integration/test_db_integrity.py` | ⬜ |
| Document foreign key to User enforced | `integration/test_db_integrity.py` | ⬜ |
| ClassificationJob references Document | `integration/test_db_integrity.py` | ⬜ |
| ClassifiedSegment references Job | `integration/test_db_integrity.py` | ⬜ |
| Annotation references Document | `integration/test_db_integrity.py` | ⬜ |
| UsageRecord references User | `integration/test_db_integrity.py` | ⬜ |
| Alembic migrations apply cleanly | `conftest.py` (auto-run) | ✅ |
| DB session returns async connection | `unit/test_config.py` | ⬜ |

### 6.3 User Interface Testing (Frontend)

| UI Scenario | Test File | Tool | Status |
|---|---|---|---|
| Login form renders all fields | `src/__tests__/LoginForm.test.tsx` | Vitest | ⬜ |
| Login form shows validation errors | `src/__tests__/LoginForm.test.tsx` | Vitest | ⬜ |
| Signup form submits correctly | `src/__tests__/SignupForm.test.tsx` | Vitest | ⬜ |
| Document list renders file names | `src/__tests__/DocumentList.test.tsx` | Vitest | ⬜ |
| Classification results component renders labels | `src/__tests__/ClassificationResults.test.tsx` | Vitest | ⬜ |
| User can sign up via UI | `tests/e2e/auth.spec.ts` | Playwright | ⬜ |
| User can log in via UI | `tests/e2e/auth.spec.ts` | Playwright | ⬜ |
| Unauthenticated redirect to login | `tests/e2e/auth.spec.ts` | Playwright | ⬜ |
| User can upload a document via UI | `tests/e2e/document-upload.spec.ts` | Playwright | ⬜ |
| Classification results displayed after job completes | `tests/e2e/document-upload.spec.ts` | Playwright | ⬜ |
| Admin can view users table | `tests/e2e/admin.spec.ts` | Playwright | ⬜ |
| Regular user is denied access to admin UI | `tests/e2e/admin.spec.ts` | Playwright | ⬜ |

### 6.4 Performance Profiling

| Scenario | Test File | Tool | Status |
|---|---|---|---|
| Single user response time baseline (all endpoints) | `stress/locustfiles/mixed_workload.py` (1 user) | Locust | ✅ |
| End-to-end async classification time | `stress/locustfiles/classification_load.py` | Locust | ✅ |
| Document upload throughput to MinIO | `stress/locustfiles/document_load.py` | Locust | ✅ |

### 6.5 Load Testing

| Scenario | Test File | Tool | Status |
|---|---|---|---|
| Authentication login storm (spike test) | `stress/locustfiles/auth_load.py` | Locust | ✅ |
| Peak mixed workload (ramping to 200 users) | `stress/locustfiles/mixed_workload.py` | Locust | ✅ |
| Celery ML worker saturation test | `stress/locustfiles/classification_load.py` | Locust | ✅ |

### 6.6 Security & Access Control Testing

| Scenario | Test File | Status |
|---|---|---|
| Protected endpoint rejects missing token (401) | `integration/test_auth.py` | ⬜ |
| Protected endpoint rejects expired token (401) | `integration/test_auth.py` | ⬜ |
| Admin endpoint rejects regular user (403) | `integration/test_admin.py` | ⬜ |
| Password is hashed, never stored plain text | `unit/test_auth_service.py` | ⬜ |
| JWT verification logic tested | `unit/test_auth_service.py` | ⬜ |
| User cannot view another user's documents | `integration/test_documents.py` | ⬜ |
| User cannot delete another user's annotations | `integration/test_annotations.py` | ⬜ |

### 6.7 Configuration Testing

| Scenario | Test File | Status |
|---|---|---|
| Settings correctly parse from environment variables | `unit/test_config.py` | ⬜ |
| DATABASE_URL is correctly formed | `unit/test_config.py` | ⬜ |
| REDIS_URL is correctly formed | `unit/test_config.py` | ⬜ |
| Missing required env var raises error at startup | `unit/test_config.py` | ⬜ |

### 6.8 Failover & Recovery Testing

| Scenario | Test File | Status |
|---|---|---|
| API returns 503 when DB is unavailable | `integration/test_resilience.py` | ⬜ |
| API returns 503 when Redis is unavailable | `integration/test_resilience.py` | ⬜ |
| Celery task retries on transient DB failure | `unit/test_ocr_task.py` | ⬜ |
| FastAPI startup does not crash if MinIO is unreachable | Covered by MinIO mock in `conftest.py` | ✅ |

---

## 7. CI/CD Integration Notes

### GitHub Actions Example

Create `.github/workflows/test.yml`:

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v2
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: cd webapp/backend && uv sync --all-extras
      - name: Run tests
        run: cd webapp/backend && uv run pytest --junitxml=reports/junit.xml --cov=app --cov-report=xml
      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: backend-test-results
          path: webapp/backend/reports/

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - name: Install dependencies
        run: cd webapp/frontend && npm ci
      - name: Install Playwright browsers
        run: cd webapp/frontend && npx playwright install --with-deps
      - name: Run unit tests
        run: cd webapp/frontend && npm run test -- --run --coverage
      - name: Run E2E tests
        run: cd webapp/frontend && npm run test:e2e
      - name: Upload Playwright report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-report
          path: webapp/frontend/playwright-report/
```

---

## 8. Troubleshooting

### Backend

| Problem | Cause | Solution |
|---|---|---|
| `ConnectionRefusedError` on MinIO during collection | `storage_service.py` tries to connect at import time | The `minio.Minio` mock in `conftest.py` should handle this. Ensure `patcher.start()` is called before the app import. |
| `TypeError: str expected, not int` on container ports | `get_exposed_port()` returns `int` in some versions | Wrap with `str()`: `str(postgres.get_exposed_port(5432))` — already fixed in `conftest.py` |
| `Docker daemon is not running` | Docker is stopped | Start Docker: `sudo systemctl start docker` |
| Pydantic `ValidationError` for DB settings | App was imported before env vars were set | Ensure environment variables are set in `conftest.py` **before** `from app.main import app` |
| `alembic.util.exc.CommandError` during migration | Alembic can't find `alembic.ini` | Run pytest from the `backend/` directory where `alembic.ini` lives |
| Tests pass individually but fail together | Test pollution (shared state between tests) | Use unique emails/names per test; roll back transactions between tests using a transaction fixture |

### Frontend

| Problem | Cause | Solution |
|---|---|---|
| `Cannot find package 'vite'` | `vite` was not installed as a direct dep | Run `npm install -D vite --legacy-peer-deps` |
| Playwright `test()` called in wrong context | Vitest was picking up `.spec.ts` files | Ensure `tests/e2e/**` is listed in `exclude` in `vitest.config.ts` |
| `Vite config uses features unsupported by native configLoader` | `vitest.config.ts` is treated as CJS | Add `"type": "module"` to `package.json`, or rename config to `vitest.config.mjs` |
| `ERR_ERESOLVE` during npm install | Peer dependency conflicts | Use `--legacy-peer-deps` flag: `npm install --legacy-peer-deps` |
| Playwright `toHaveTitle` fails | App title doesn't match the placeholder assertion | Update the assertion in `sample.spec.ts` to match your actual app title |
| Playwright test hangs waiting for server | Next.js dev server took too long to start | Increase `timeout` in `playwright.config.ts` `webServer` section |

---

*This document is expected to be updated as new features are added. Maintain a 1:1 correspondence between each feature module and its associated test file.*
