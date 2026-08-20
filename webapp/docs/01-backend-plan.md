# LangID Platform — Backend Plan (FastAPI)

> **Framework**: FastAPI  
> **Language**: Python 3.12+  
> **ORM**: SQLAlchemy 2.0 (async)  
> **Task Queue**: Celery + Redis  
> **Object Storage**: MinIO (S3-compatible)  
> **Auth**: JWT (access + refresh tokens)

---

## 1. Project Structure

```
webapp/backend/
├── alembic/                          # Database migrations
│   ├── versions/
│   └── env.py
├── alembic.ini
├── app/
│   ├── __init__.py
│   ├── main.py                       # FastAPI app factory, lifespan, CORS
│   ├── config.py                     # Pydantic Settings (env-based config)
│   ├── dependencies.py               # Shared FastAPI dependencies (get_db, get_current_user, etc.)
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py                # Async engine + sessionmaker
│   │   ├── base.py                   # DeclarativeBase
│   │   └── models/                   # SQLAlchemy ORM models
│   │       ├── __init__.py
│   │       ├── user.py
│   │       ├── subscription.py
│   │       ├── tier.py
│   │       ├── system_config.py
│   │       ├── model_rate.py
│   │       ├── usage_record.py
│   │       ├── document.py
│   │       ├── document_page.py
│   │       ├── classification_job.py
│   │       ├── classified_segment.py
│   │       └── annotation.py
│   │
│   ├── schemas/                      # Pydantic request/response schemas
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── tier.py
│   │   ├── billing.py
│   │   ├── document.py
│   │   ├── classification.py
│   │   ├── annotation.py
│   │   └── admin.py
│   │
│   ├── api/                          # Route handlers (thin controllers)
│   │   ├── __init__.py
│   │   ├── router.py                 # Aggregate router
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── documents.py
│   │   │   ├── classification.py
│   │   │   ├── annotations.py
│   │   │   ├── billing.py
│   │   │   └── admin/
│   │   │       ├── __init__.py
│   │   │       ├── tiers.py
│   │   │       ├── models.py
│   │   │       ├── config.py
│   │   │       ├── annotations.py
│   │   │       └── users.py
│   │   └── health.py
│   │
│   ├── services/                     # Business logic layer
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── billing_service.py
│   │   ├── document_service.py
│   │   ├── classification_service.py
│   │   ├── ocr_service.py
│   │   ├── storage_service.py
│   │   ├── annotation_service.py
│   │   └── admin_service.py
│   │
│   ├── workers/                      # Celery tasks
│   │   ├── __init__.py
│   │   ├── celery_app.py
│   │   ├── ocr_tasks.py
│   │   └── classification_tasks.py
│   │
│   ├── ml/                           # ML model loading & inference
│   │   ├── __init__.py
│   │   ├── model_registry.py         # Dynamic model loader
│   │   ├── base_classifier.py        # Abstract base class
│   │   ├── langid_classifier.py      # Current sklearn model
│   │   ├── base_ocr.py              # Abstract base class for OCR
│   │   └── text_extractor.py        # PDF text extraction (non-OCR)
│   │
│   ├── storage/                      # MinIO / S3 abstraction
│   │   ├── __init__.py
│   │   └── minio_client.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── security.py               # Password hashing, JWT encode/decode
│       ├── pagination.py             # Cursor/offset pagination helpers
│       ├── text_processing.py        # Sentence splitting, tokenization
│       └── exceptions.py             # Custom exception classes
│
├── tests/
│   ├── conftest.py                   # Fixtures (test db, test client)
│   ├── test_auth.py
│   ├── test_classification.py
│   ├── test_billing.py
│   └── ...
│
├── pyproject.toml                    # Dependencies & tooling config
├── Dockerfile
└── docker-compose.yml                # PostgreSQL, Redis, MinIO, API, Worker
```

---

## 2. Module Breakdown

### 2.1 Authentication & Authorization (`api/v1/auth.py` + `services/auth_service.py`)

| Endpoint                 | Method | Auth     | Description                        |
| :----------------------- | :----- | :------- | :--------------------------------- |
| `/api/v1/auth/signup`    | POST   | Public   | Register new user account          |
| `/api/v1/auth/login`     | POST   | Public   | Returns access + refresh JWT       |
| `/api/v1/auth/refresh`   | POST   | Refresh  | Rotate access token                |
| `/api/v1/auth/logout`    | POST   | User     | Invalidate refresh token           |
| `/api/v1/auth/me`        | GET    | User     | Get current user profile           |

**Implementation Notes:**
- Passwords hashed with `bcrypt` via `passlib`.
- JWT access tokens: 15-min expiry. Refresh tokens: 7-day expiry, stored in DB for revocation.
- Role-based access: `require_role("admin")` dependency for admin routes.
- Rate limiting on login/signup via Redis sliding window.

### 2.2 User Management (`api/v1/users.py` + `services/user_service.py`)

| Endpoint                        | Method | Auth  | Description                    |
| :------------------------------ | :----- | :---- | :----------------------------- |
| `/api/v1/users/me`              | GET    | User  | Profile + usage summary        |
| `/api/v1/users/me`              | PATCH  | User  | Update display name etc.       |
| `/api/v1/users/me/usage`        | GET    | User  | Detailed usage history         |
| `/api/v1/users/me/subscription` | GET    | User  | Current subscription details   |
| `/api/v1/users/me/subscription` | POST   | User  | Subscribe to a tier            |
| `/api/v1/users/me/credits`      | GET    | User  | Credits balance & history      |

### 2.3 Tier & Billing Management

#### Admin Config (`api/v1/admin/tiers.py`, `api/v1/admin/config.py`)

| Endpoint                              | Method | Auth  | Description                           |
| :------------------------------------ | :----- | :---- | :------------------------------------ |
| `/api/v1/admin/tiers`                 | GET    | Admin | List all tiers                        |
| `/api/v1/admin/tiers`                 | POST   | Admin | Create a new tier                     |
| `/api/v1/admin/tiers/{id}`            | PATCH  | Admin | Update tier pricing/limits            |
| `/api/v1/admin/tiers/{id}`            | DELETE | Admin | Soft-delete a tier                    |
| `/api/v1/admin/config`                | GET    | Admin | Get all system config                 |
| `/api/v1/admin/config/{key}`          | PUT    | Admin | Set a config value                    |

**Configurable Keys:**
- `usd_to_credits` — Exchange rate: 1 USD = X credits
- `free_storage_bytes` — Free storage allowance (default: 200MB = 209715200)
- `storage_rate_per_gb_credits` — Monthly cost per GB in credits
- `system_currency_name` — Display name for credits (e.g., "LangCoins")

#### Admin Model Rates (`api/v1/admin/models.py`)

| Endpoint                            | Method | Auth  | Description                         |
| :---------------------------------- | :----- | :---- | :---------------------------------- |
| `/api/v1/admin/models`              | GET    | Admin | List all model rate configs         |
| `/api/v1/admin/models`              | POST   | Admin | Register a new model + rate         |
| `/api/v1/admin/models/{id}`         | PATCH  | Admin | Update a model's rate               |
| `/api/v1/admin/models/{id}`         | DELETE | Admin | Deactivate a model                  |

### 2.4 Document Management (`api/v1/documents.py` + `services/document_service.py`)

| Endpoint                                     | Method | Auth | Description                        |
| :------------------------------------------- | :----- | :--- | :--------------------------------- |
| `/api/v1/documents`                          | GET    | User | List user's documents (paginated)  |
| `/api/v1/documents/upload`                   | POST   | User | Upload a document (multipart)      |
| `/api/v1/documents/{id}`                     | GET    | User | Get document metadata              |
| `/api/v1/documents/{id}/download`            | GET    | User | Download original file             |
| `/api/v1/documents/{id}`                     | DELETE | User | Delete document & free storage     |
| `/api/v1/documents/{id}/extract`             | POST   | User | Extract text via PDF read          |
| `/api/v1/documents/{id}/ocr`                 | POST   | User | Run OCR on document pages          |
| `/api/v1/documents/{id}/pages`               | GET    | User | List pages + extracted text        |
| `/api/v1/documents/{id}/pages/{page_num}`    | GET    | User | Get a specific page's content      |

**Implementation Notes:**
- Upload via `UploadFile` with streaming to MinIO.
- Track `storage_used_bytes` on the user record. Validate against free tier + paid storage.
- PDF text extraction uses `PyMuPDF` (fitz) for non-OCR reading.
- OCR dispatched as Celery task; status polled or pushed via WebSocket.
- Storage billing calculated monthly via a scheduled Celery beat task.

### 2.5 Classification (`api/v1/classification.py` + `services/classification_service.py`)

| Endpoint                                  | Method | Auth | Description                             |
| :---------------------------------------- | :----- | :--- | :-------------------------------------- |
| `/api/v1/classify/text`                   | POST   | User | Classify raw text input                 |
| `/api/v1/classify/document/{doc_id}`      | POST   | User | Classify an uploaded document           |
| `/api/v1/classify/jobs`                   | GET    | User | List user's classification jobs         |
| `/api/v1/classify/jobs/{job_id}`          | GET    | User | Get job status + results                |
| `/api/v1/classify/jobs/{job_id}/segments` | GET    | User | Get classified segments (paginated)     |
| `/api/v1/classify/models`                 | GET    | User | List available classification models    |

**Classification Pipeline:**

```
Input Text/Document
        │
        ▼
┌─────────────────┐
│  Text Extraction │  (if document: PDF read or OCR)
└────────┬────────┘
         ▼
┌─────────────────┐
│ Sentence Splitter│  Split into sentences/phrases
│ (text_processing)│  Track char offsets
└────────┬────────┘
         ▼
┌─────────────────┐
│  Tokenizer &    │  Count tokens for billing
│  Token Counter  │
└────────┬────────┘
         ▼
┌─────────────────┐
│  ML Model       │  Predict per-segment language
│  Inference      │  Return language + confidence + probabilities
└────────┬────────┘
         ▼
┌─────────────────┐
│  Result Assembly │  Build structured result with segments
│  & Persist      │  Store in DB + MinIO (full JSON)
└────────┬────────┘
         ▼
┌─────────────────┐
│  Billing Meter  │  Charge credits based on token count × model rate
└─────────────────┘
```

**Key Design — Sentence-Level Classification:**

The core differentiator is **segment-level** (sentence/phrase) classification, not whole-document. The `text_processing.py` module handles:

1. Splitting text into sentences using Sinhala-aware rules (sentence-ending punctuation: `।`, `.`, `?`, `!`, newlines).
2. Each sentence becomes a `classified_segment` with `start_char_offset` and `end_char_offset`.
3. Results are returned as an ordered list of segments with their predicted language.

### 2.6 Annotations & Feedback (`api/v1/annotations.py`)

#### User Endpoints

| Endpoint                                    | Method | Auth | Description                        |
| :------------------------------------------ | :----- | :--- | :--------------------------------- |
| `/api/v1/annotations`                       | POST   | User | Submit a correction on a segment   |
| `/api/v1/annotations/mine`                  | GET    | User | List user's submitted annotations  |
| `/api/v1/annotations/{id}`                  | PATCH  | User | Update own annotation              |
| `/api/v1/annotations/{id}`                  | DELETE | User | Delete own annotation              |

#### Admin Review Endpoints (`api/v1/admin/annotations.py`)

| Endpoint                                          | Method | Auth  | Description                              |
| :------------------------------------------------ | :----- | :---- | :--------------------------------------- |
| `/api/v1/admin/annotations`                       | GET    | Admin | List all annotations (filterable)        |
| `/api/v1/admin/annotations/pending`               | GET    | Admin | Annotations awaiting review              |
| `/api/v1/admin/annotations/{id}/review`           | POST   | Admin | Mark as valid/invalid for training       |
| `/api/v1/admin/annotations/batch-review`          | POST   | Admin | Batch review multiple annotations        |
| `/api/v1/admin/annotations/export`                | GET    | Admin | Export validated annotations (CSV/JSON)  |
| `/api/v1/admin/annotations/stats`                 | GET    | Admin | Annotation statistics dashboard data     |

### 2.7 Admin User Management (`api/v1/admin/users.py`)

| Endpoint                            | Method | Auth  | Description                       |
| :---------------------------------- | :----- | :---- | :-------------------------------- |
| `/api/v1/admin/users`               | GET    | Admin | List all users (paginated)        |
| `/api/v1/admin/users/{id}`          | GET    | Admin | Get user details + usage          |
| `/api/v1/admin/users/{id}`          | PATCH  | Admin | Update user role, active status   |
| `/api/v1/admin/users/{id}/usage`    | GET    | Admin | Detailed usage for a user         |

---

## 3. ML Model Integration Architecture

```python
# app/ml/base_classifier.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class SegmentResult:
    """Result for a single text segment."""
    text: str
    predicted_language: str
    confidence: float
    probabilities: dict[str, float]
    start_char_offset: int
    end_char_offset: int

class BaseClassifier(ABC):
    """Abstract base for all classification models."""

    @abstractmethod
    def predict_segments(
        self, segments: list[str]
    ) -> list[SegmentResult]:
        """Classify a batch of text segments."""
        ...

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the unique model identifier."""
        ...
```

```python
# app/ml/base_ocr.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class OCRPageResult:
    """OCR output for a single page."""
    page_number: int
    text: str
    confidence: float

class BaseOCR(ABC):
    """Abstract base for all OCR engines."""

    @abstractmethod
    def process_page(self, image_bytes: bytes) -> OCRPageResult:
        """OCR a single page image."""
        ...

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the unique model identifier."""
        ...
```

**Model Registry Pattern:**
- `model_registry.py` maintains a dictionary of available models.
- Models are registered at startup via config.
- Adding a new model = implementing the ABC + registering it.
- Rate is looked up from `model_rates` table at inference time.

---

## 4. Billing Service Logic

```python
# Pseudo-code for billing flow

class BillingService:
    async def charge_classification(
        self, user_id: UUID, model_name: str, token_count: int
    ) -> UsageRecord:
        """Charge user for classification based on token count."""
        rate = await self.get_model_rate(model_name)  # credits_per_token
        credits = token_count * rate.credits_per_token

        # Deduct from balance (tier credits first, then PAYG)
        await self.deduct_credits(user_id, credits)

        # Record usage
        return await self.record_usage(
            user_id=user_id,
            record_type="classification",
            model_name=model_name,
            quantity=token_count,
            credits_charged=credits
        )

    async def charge_ocr(
        self, user_id: UUID, model_name: str, page_count: int
    ) -> UsageRecord:
        """Charge user for OCR based on page count."""
        rate = await self.get_model_rate(model_name)  # credits_per_page

        # Check tier included pages
        subscription = await self.get_active_subscription(user_id)
        included_pages = subscription.tier.ocr_pages_included if subscription else 0
        used_pages = await self.get_used_ocr_pages_this_cycle(user_id)
        billable_pages = max(0, page_count - max(0, included_pages - used_pages))

        credits = billable_pages * rate.credits_per_page
        await self.deduct_credits(user_id, credits)

        return await self.record_usage(...)

    async def calculate_storage_charges(self) -> None:
        """Monthly cron: charge all users for excess storage."""
        free_storage = await self.get_config("free_storage_bytes")
        rate_per_gb = await self.get_config("storage_rate_per_gb_credits")

        users = await self.get_users_over_storage_limit(free_storage)
        for user in users:
            excess_bytes = user.storage_used_bytes - free_storage
            excess_gb = excess_bytes / (1024 ** 3)
            credits = excess_gb * rate_per_gb
            await self.deduct_credits(user.id, credits)
            await self.record_usage(...)
```

---

## 5. Background Tasks (Celery)

| Task                      | Trigger              | Description                                       |
| :------------------------ | :------------------- | :------------------------------------------------ |
| `ocr_document_task`       | User uploads + OCR   | Process each page through OCR model               |
| `classify_document_task`  | User requests classify| Run classification pipeline on extracted text     |
| `monthly_billing_task`    | Celery Beat (monthly)| Calculate storage charges, reset tier credits     |
| `cleanup_deleted_files`   | Celery Beat (daily)  | Remove soft-deleted files from MinIO              |

---

## 6. Key Dependencies

```toml
[project]
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "sqlalchemy[asyncio]>=2.0",
    "asyncpg>=0.30",              # Async PostgreSQL driver
    "alembic>=1.14",
    "pydantic>=2.10",
    "pydantic-settings>=2.5",
    "python-jose[cryptography]",   # JWT
    "passlib[bcrypt]",             # Password hashing
    "python-multipart",            # File uploads
    "minio>=7.2",                  # MinIO client
    "celery[redis]>=5.4",          # Task queue
    "redis>=5.0",                  # Cache + sessions
    "pymupdf>=1.24",               # PDF text extraction
    "joblib>=1.4",                 # Loading existing pkl models
    "scikit-learn>=1.5",           # Current classification model
    "httpx>=0.27",                 # Async HTTP client for tests
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
]
```

---

## 7. Error Handling Strategy

```python
# app/utils/exceptions.py

class AppException(Exception):
    """Base application exception."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code

class InsufficientCreditsError(AppException):
    """Raised when user doesn't have enough credits."""
    def __init__(self):
        super().__init__("Insufficient credits", status_code=402)

class StorageLimitError(AppException):
    """Raised when upload would exceed storage limits."""
    def __init__(self):
        super().__init__("Storage limit exceeded", status_code=413)

class ModelNotFoundError(AppException):
    """Raised when requested model doesn't exist or is inactive."""
    def __init__(self, model_name: str):
        super().__init__(f"Model '{model_name}' not found or inactive", status_code=404)
```

Global exception handler registered in `main.py` converts `AppException` → JSON response.

---

## 8. Security Considerations

1. **Input Sanitization**: All text inputs validated via Pydantic. Max text length enforced.
2. **File Upload Validation**: Mime type checking, max file size, virus scan integration point.
3. **Rate Limiting**: Redis-backed rate limiter on auth endpoints and API calls.
4. **CORS**: Configurable allowed origins. Strict in production.
5. **SQL Injection**: Prevented by SQLAlchemy parameterized queries.
6. **Secrets Management**: All secrets via environment variables / `.env` file, never hardcoded.
