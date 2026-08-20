# LangID Platform — System Architecture Overview

> **Product**: Sinhala-Script Language Identification (LangID) Platform  
> **Purpose**: Classify Sinhala-script text/documents into Sinhala, Pali, and Sanskrit at the sentence/phrase level.  
> **Stack**: Next.js 15 (Frontend) · FastAPI (Backend) · PostgreSQL + Redis + MinIO

---

## 1. High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                         CLIENT (Browser)                          │
│                     Next.js 15 (App Router)                       │
│   ┌──────────┐  ┌────────────┐  ┌────────────┐  ┌─────────────┐  │
│   │ Auth UI  │  │ Dashboard  │  │ Classifier │  │  Admin Panel │  │
│   └──────────┘  └────────────┘  └────────────┘  └─────────────┘  │
└──────────────────────────┬─────────────────────────────────────────┘
                           │ HTTPS / REST + WebSocket
                           ▼
┌────────────────────────────────────────────────────────────────────┐
│                     API GATEWAY (FastAPI)                          │
│   ┌──────────┐  ┌────────────┐  ┌──────────────┐  ┌───────────┐  │
│   │ Auth     │  │ Billing /  │  │ Classification│  │ Admin     │  │
│   │ Service  │  │ Metering   │  │ Pipeline      │  │ Config    │  │
│   └──────────┘  └────────────┘  └──────────────┘  └───────────┘  │
│   ┌──────────┐  ┌────────────┐  ┌──────────────┐                  │
│   │ Document │  │ OCR        │  │ Annotation   │                  │
│   │ Storage  │  │ Service    │  │ / Feedback   │                  │
│   └──────────┘  └────────────┘  └──────────────┘                  │
└───────┬──────────────┬──────────────┬──────────────┬──────────────┘
        │              │              │              │
        ▼              ▼              ▼              ▼
   ┌─────────┐   ┌──────────┐   ┌─────────┐   ┌──────────┐
   │PostgreSQL│   │  Redis   │   │  MinIO   │   │ ML Model │
   │ (Primary │   │ (Cache / │   │ (Object  │   │ Workers  │
   │  Store)  │   │  Queue)  │   │ Storage) │   │ (Celery) │
   └─────────┘   └──────────┘   └─────────┘   └──────────┘
```

---

## 2. Database Design

### 2.1 Why These Databases?

| Database       | Role                                         | Why                                                                                       |
| :------------- | :------------------------------------------- | :---------------------------------------------------------------------------------------- |
| **PostgreSQL** | Primary relational store                     | ACID-compliant, JSON support, excellent for billing/audit, mature ecosystem with SQLAlchemy |
| **Redis**      | Caching, rate limiting, session store, queues | Sub-ms latency, pub/sub for real-time status, Celery broker                                |
| **MinIO**      | Object/file storage (S3-compatible)          | Self-hosted, no vendor lock-in, stores uploaded documents & OCR outputs                    |

### 2.2 PostgreSQL Schema (Entity Overview)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  USERS & AUTH                                                                │
│  ┌─────────────┐    ┌──────────────────┐                                     │
│  │   users      │───▶│  user_sessions    │                                    │
│  │ (id, email,  │    │ (refresh tokens)  │                                    │
│  │  role, ...)  │    └──────────────────┘                                     │
│  └──────┬──────┘                                                             │
│         │                                                                    │
│  BILLING & TIERS                                                             │
│  ┌──────▼──────┐    ┌──────────────────┐    ┌────────────────────┐           │
│  │ subscriptions│───▶│  usage_records    │    │  tier_definitions  │           │
│  │ (user→tier) │    │ (tokens, pages,  │    │ (name, price_usd,  │           │
│  └─────────────┘    │  storage bytes)  │    │  ocr_pages, ...)   │           │
│                     └──────────────────┘    └────────────────────┘           │
│  ┌──────────────────┐    ┌─────────────────────────┐                         │
│  │  model_rates      │    │  system_config           │                        │
│  │ (model_id,        │    │ (usd_to_credits,         │                        │
│  │  credits_per_tok) │    │  storage_rate_per_gb ...) │                        │
│  └──────────────────┘    └─────────────────────────┘                         │
│                                                                              │
│  DOCUMENTS & STORAGE                                                         │
│  ┌─────────────────┐    ┌──────────────────────┐                             │
│  │   documents      │───▶│  document_pages       │                            │
│  │ (user_id, name,  │    │ (page_num, ocr_text, │                            │
│  │  size, minio_key)│    │  ocr_model, status)  │                            │
│  └────────┬────────┘    └──────────────────────┘                             │
│           │                                                                  │
│  CLASSIFICATION RESULTS                                                      │
│  ┌────────▼────────┐    ┌──────────────────────┐                             │
│  │ classification   │───▶│ classified_segments   │                            │
│  │ _jobs            │    │ (text, lang, conf,   │                            │
│  │ (doc/text, model,│    │  start_idx, end_idx) │                            │
│  │  status, ...)    │    └──────────┬───────────┘                            │
│  └─────────────────┘               │                                         │
│                                    │                                         │
│  ANNOTATIONS & FEEDBACK                                                      │
│  ┌─────────────────────────────────▼─────────┐                               │
│  │        annotations                         │                              │
│  │ (segment_id, user_id, corrected_lang,     │                              │
│  │  comment, admin_verified, verified_by,    │                              │
│  │  is_valid_for_training)                   │                              │
│  └───────────────────────────────────────────┘                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Detailed Table Definitions

#### `users`
| Column           | Type         | Notes                                      |
| :--------------- | :----------- | :----------------------------------------- |
| `id`             | UUID (PK)    | `gen_random_uuid()`                        |
| `email`          | VARCHAR(320) | UNIQUE, NOT NULL                           |
| `password_hash`  | TEXT         | bcrypt hashed                              |
| `display_name`   | VARCHAR(128) |                                            |
| `role`           | ENUM         | `user`, `admin`                            |
| `is_active`      | BOOLEAN      | default `true`                             |
| `storage_used_bytes` | BIGINT   | Running total of file storage              |
| `credits_balance`| DECIMAL(18,4)| Current system currency balance            |
| `created_at`     | TIMESTAMPTZ  |                                            |
| `updated_at`     | TIMESTAMPTZ  |                                            |

#### `tier_definitions`
| Column             | Type         | Notes                                     |
| :----------------- | :----------- | :---------------------------------------- |
| `id`               | UUID (PK)    |                                           |
| `name`             | VARCHAR(64)  | e.g. "Basic", "Pro"                       |
| `price_usd`        | DECIMAL(10,2)| Monthly price in USD                      |
| `included_credits` | DECIMAL(18,4)| System currency credits included/month    |
| `ocr_pages_included`| INTEGER     | Free OCR pages per month                  |
| `is_active`        | BOOLEAN      | Soft-delete / hide tier                   |
| `created_at`       | TIMESTAMPTZ  |                                           |

#### `subscriptions`
| Column              | Type         | Notes                                   |
| :------------------ | :----------- | :-------------------------------------- |
| `id`                | UUID (PK)    |                                         |
| `user_id`           | UUID (FK)    | → `users.id`                            |
| `tier_id`           | UUID (FK)    | → `tier_definitions.id`, nullable (PAYG)|
| `billing_cycle_start`| DATE        |                                         |
| `billing_cycle_end` | DATE         |                                         |
| `status`            | ENUM         | `active`, `cancelled`, `past_due`       |
| `created_at`        | TIMESTAMPTZ  |                                         |

#### `system_config`
| Column    | Type         | Notes                                             |
| :-------- | :----------- | :------------------------------------------------ |
| `key`     | VARCHAR (PK) | e.g. `usd_to_credits`, `free_storage_bytes`, `storage_rate_per_gb_credits` |
| `value`   | JSONB        | Flexible value storage                            |
| `updated_at` | TIMESTAMPTZ |                                                  |
| `updated_by` | UUID (FK) | → `users.id` (admin who last changed it)          |

#### `model_rates`
| Column             | Type         | Notes                                     |
| :------------------ | :----------- | :---------------------------------------- |
| `id`               | UUID (PK)    |                                           |
| `model_type`       | ENUM         | `classification`, `ocr`                   |
| `model_name`       | VARCHAR(128) | e.g. "langid_v1", "tesseract_sinhala"     |
| `credits_per_token`| DECIMAL(18,8)| For classification models                 |
| `credits_per_page` | DECIMAL(18,4)| For OCR models                            |
| `is_active`        | BOOLEAN      |                                           |
| `created_at`       | TIMESTAMPTZ  |                                           |

#### `usage_records`
| Column         | Type         | Notes                                        |
| :------------- | :----------- | :------------------------------------------- |
| `id`           | UUID (PK)    |                                              |
| `user_id`      | UUID (FK)    | → `users.id`                                |
| `record_type`  | ENUM         | `classification`, `ocr`, `storage`           |
| `model_name`   | VARCHAR(128) | Which model was used                         |
| `quantity`      | DECIMAL(18,4)| Tokens, pages, or GB-months                 |
| `credits_charged`| DECIMAL(18,4)|                                             |
| `job_id`       | UUID         | → classification_jobs.id or NULL             |
| `created_at`   | TIMESTAMPTZ  |                                              |

#### `documents`
| Column         | Type         | Notes                                        |
| :------------- | :----------- | :------------------------------------------- |
| `id`           | UUID (PK)    |                                              |
| `user_id`      | UUID (FK)    | → `users.id`                                |
| `filename`     | VARCHAR(512) | Original filename                            |
| `mime_type`    | VARCHAR(128) |                                              |
| `size_bytes`   | BIGINT       |                                              |
| `minio_key`    | TEXT         | Object key in MinIO                          |
| `upload_status`| ENUM         | `uploading`, `ready`, `deleted`              |
| `created_at`   | TIMESTAMPTZ  |                                              |

#### `document_pages`
| Column         | Type         | Notes                                        |
| :------------- | :----------- | :------------------------------------------- |
| `id`           | UUID (PK)    |                                              |
| `document_id`  | UUID (FK)    | → `documents.id`                             |
| `page_number`  | INTEGER      |                                              |
| `extracted_text`| TEXT        | Text from PDF read or OCR                    |
| `extraction_method`| ENUM     | `pdf_read`, `ocr`                            |
| `ocr_model`    | VARCHAR(128) | Model used if OCR                            |
| `minio_page_image_key`| TEXT  | Page image stored for reference              |
| `status`       | ENUM         | `pending`, `processing`, `completed`, `failed`|
| `created_at`   | TIMESTAMPTZ  |                                              |

#### `classification_jobs`
| Column          | Type         | Notes                                       |
| :-------------- | :----------- | :------------------------------------------ |
| `id`            | UUID (PK)    |                                             |
| `user_id`       | UUID (FK)    | → `users.id`                               |
| `document_id`   | UUID (FK)    | → `documents.id`, nullable (for raw text)   |
| `input_text`    | TEXT         | Raw text input (if no document)             |
| `model_name`    | VARCHAR(128) | Classification model used                   |
| `status`        | ENUM         | `queued`,`processing`,`completed`,`failed`  |
| `total_tokens`  | INTEGER      |                                             |
| `credits_charged`| DECIMAL(18,4)|                                            |
| `result_minio_key`| TEXT       | Full result JSON stored in MinIO            |
| `created_at`    | TIMESTAMPTZ  |                                             |
| `completed_at`  | TIMESTAMPTZ  |                                             |

#### `classified_segments`
| Column             | Type         | Notes                                    |
| :------------------ | :----------- | :--------------------------------------- |
| `id`               | UUID (PK)    |                                          |
| `job_id`           | UUID (FK)    | → `classification_jobs.id`               |
| `segment_index`    | INTEGER      | Order within the document                |
| `text`             | TEXT         | The sentence/phrase                      |
| `predicted_language`| VARCHAR(32) | `sinhala`, `pali`, `sanskrit`, `mixed`   |
| `confidence`       | DECIMAL(5,4) | 0.0000 – 1.0000                         |
| `probabilities`    | JSONB        | `{"sinhala": 0.85, "pali": 0.10, ...}`   |
| `start_char_offset`| INTEGER     | Character offset in source text          |
| `end_char_offset`  | INTEGER      |                                          |

#### `annotations`
| Column                  | Type         | Notes                              |
| :----------------------- | :----------- | :--------------------------------- |
| `id`                    | UUID (PK)    |                                    |
| `segment_id`            | UUID (FK)    | → `classified_segments.id`         |
| `user_id`               | UUID (FK)    | → `users.id` (who annotated)      |
| `corrected_language`    | VARCHAR(32)  | User's correction                  |
| `comment`               | TEXT         | Optional note                      |
| `admin_reviewed`        | BOOLEAN      | Has an admin reviewed this?        |
| `reviewed_by`           | UUID (FK)    | → `users.id` (admin)              |
| `is_valid_for_training` | BOOLEAN      | Admin marks if usable              |
| `reviewed_at`           | TIMESTAMPTZ  |                                    |
| `created_at`            | TIMESTAMPTZ  |                                    |

---

## 3. Storage Architecture (MinIO)

```
langid-bucket/
├── documents/{user_id}/{document_id}/
│   ├── original.pdf                    # Uploaded file
│   └── pages/
│       ├── page_001.png                # Extracted page images
│       ├── page_002.png
│       └── ...
├── results/{job_id}/
│   ├── classification_result.json      # Full structured result
│   └── ocr_result.json                 # OCR output per page
└── annotations/{annotation_id}/
    └── context.json                    # Snapshot for training
```

---

## 4. Key Design Decisions

1. **System Currency (Credits)**: All charges are normalized to an internal "credits" currency. Admin sets the USD→credits rate. This decouples billing from USD and allows flexible pricing.

2. **Per-Token Metering**: Classification is charged per token processed. Each model has its own `credits_per_token` rate. Token count is recorded in `classification_jobs.total_tokens`.

3. **Per-Page OCR Billing**: OCR is charged per page. Each OCR model has its own `credits_per_page` rate.

4. **Storage Billing**: First 200MB free (configurable via `system_config.free_storage_bytes`). After that, monthly charge per GB via `system_config.storage_rate_per_gb_credits`.

5. **Extensible Model Registry**: Both OCR and classification models are rows in `model_rates`. Adding a new model = inserting a new row. No code changes needed.

6. **Annotation Pipeline for Fine-tuning**: User corrections flow to `annotations` table. Admin reviews and marks `is_valid_for_training`. Export pipeline can query validated annotations for model fine-tuning.

7. **Async Processing**: Long-running OCR and classification jobs use Celery workers with Redis as broker. WebSocket or polling for status updates.
