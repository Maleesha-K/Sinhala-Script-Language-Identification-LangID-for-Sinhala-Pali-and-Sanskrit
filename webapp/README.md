# LangID Web Application

Web platform for the Sinhala-script language identification models: users paste
text or upload PDFs, the text is OCR'd and segmented, and each segment is
classified as Sinhala, Pali or Sanskrit (or named as another language).

Results stream: a PDF uploaded with a model is classified page by page, each
page as soon as its OCR finishes, and the document view shows every page's
text and highlighted languages while later pages are still being read. Pasted
text shows its segments in batches as they are classified.

Everything runs from one file, `docker-compose.yml`:

| Service | What it does |
|---|---|
| `caddy` | Only public entry point. HTTPS (automatic Let's Encrypt certificate) and routing |
| `frontend` | Next.js app. Calls the backend over the internal Docker network |
| `backend` | FastAPI. Runs database migrations on start and creates the first admin |
| `celery_worker` | Classification jobs (holds the models) |
| `celery_ocr_worker` | Tesseract OCR, separate so OCR never delays the classification of pages already read |
| `celery_surya_worker` | Surya OCR jobs (CPU, one process) |
| `db`, `redis`, `minio` | Postgres, Celery broker and job events, document storage |

Workers publish progress to Redis, and the backend relays it to the browser over
WebSockets (`/api/v1/ws/jobs/{id}`, `/api/v1/ws/documents/{id}`; the event
format is documented in `backend/app/utils/events.py`).

Caddy routes `/api/v1/*` (REST and progress WebSockets) to the backend,
`/langid-docs/*` (signed document downloads) to MinIO, and everything else to
the frontend. Postgres, Redis and MinIO also listen on `127.0.0.1` for local
development; they are never exposed publicly.

## Hosting on a VPS

### 1. Choose a server

Measured with every model in use:

| Component | RAM |
|---|---|
| Whole stack at idle | ~0.6 GB |
| `celery_worker` with all six classification models loaded | ~5.9 GB |
| `celery_surya_worker` while reading a page | ~5.1 GB |

- **16 GB RAM** runs everything comfortably.
- **8 GB RAM** works if you leave out Surya OCR or some of the large models
  (see [Models](#models)): models are only loaded once someone uses them, but
  all of them together with Surya do not fit.
- **CPU:** text classification and Tesseract OCR are light. Surya OCR is not:
  about 4 minutes per page on 2 vCPUs, during which the rest of the site slows
  down. Choose 4+ vCPUs if users will OCR documents with Surya regularly.
- **Disk:** ~20 GB free (Docker images ~8 GB, fine-tuned models ~5 GB, Surya
  weights 1.5 GB, plus uploaded documents).

Add swap as a safety net on any size (`fallocate -l 4G /swapfile && chmod 600
/swapfile && mkswap /swapfile && swapon /swapfile`, then add it to `/etc/fstab`).

### 2. Prepare the server

1. Install Docker Engine with the Compose plugin
   (<https://docs.docker.com/engine/install/>).
2. Point your domain's DNS **A record** at the server's IP address.
3. Open ports **80** and **443** (TCP, and 443/UDP for HTTP/3) in the firewall.
   Port 80 is needed for the certificate challenge.

### 3. Get the code and the models

```bash
git clone https://github.com/Maleesha-K/Sinhala-Script-Language-Identification-LangID-for-Sinhala-Pali-and-Sanskrit.git langid
cd langid
```

The baseline model (`models/langid_model.pkl`, `models/langid_vectorizer.pkl`)
comes with the repository. The fine-tuned checkpoints are not in git; copy them
from the machine that ran the pipeline:

```bash
# run on the training machine, from the repository root
rsync -avR --progress \
  data_pipeline/models/./03_global_rehearsal_sota/*/seed42/best \
  user@your-server:langid/data_pipeline/models/
```

See [Models](#models) for what each directory is and how to copy only some.

### 4. Configure

```bash
cd webapp
cp .env.example .env
```

Edit `.env`:

- `DOMAIN`: your domain, e.g. `langid.example.com`.
- `SECRET_KEY`, `POSTGRES_PASSWORD`, `MINIO_ROOT_PASSWORD`: long random values,
  e.g. `openssl rand -hex 32`. MinIO needs at least 8 characters.
- `INITIAL_ADMIN_EMAIL`, `INITIAL_ADMIN_PASSWORD`: the admin account created on
  first start.
- PayHere: leave unset for the sandbox merchant; set `PAYHERE_MERCHANT_ID`,
  `PAYHERE_MERCHANT_SECRET` and `PAYHERE_MODE=live` to take real payments. The
  payment notification URL is `https://$DOMAIN/api/payments/payhere/notify`.

Keep `.env` private and backed up: changing the Postgres or MinIO password after
the first start does not change the passwords stored in their volumes.

### 5. Start

```bash
docker compose up -d --build
```

The first build takes a while (PyTorch and Surya). Check progress with
`docker compose ps` and `docker compose logs -f`. When `backend` is healthy,
open `https://$DOMAIN` and sign in with the admin account. The model picker
marks any model whose files are missing as unavailable.

The first Surya OCR job downloads its weights (~1.5 GB) and is slow; later jobs
reuse them from the `surya_models` volume.

## Models

The backend serves six classifiers. Inside the containers the model files are
mounted read-only from two host directories:

| Host directory (default) | Container path | `.env` override |
|---|---|---|
| `models/` | `/models` | `BASELINE_MODELS_DIR` |
| `data_pipeline/models/03_global_rehearsal_sota/` | `/finetuned` | `FINETUNED_MODELS_DIR` |

| Model id (web app) | Files | Size |
|---|---|---|
| `sklearn_langid` (baseline) | `models/langid_model.pkl`, `models/langid_vectorizer.pkl` | <1 MB |
| `nllb_finetuned` | `nllb_lid218/seed42/best/model.bin` | 1.1 GB |
| `glotlid_finetuned` | `glotlid_v3/seed42/best/model.bin` | 1.6 GB |
| `openlid_finetuned` | `openlid_v3/seed42/best/model.bin` | 1.2 GB |
| `conlid_finetuned` | `conlid/seed42/best/` (`config.json`, `vocab.json`, `labels.json`, `model.safetensors`) | 1.1 GB |
| `lid176_leaf_surgery` | `lid176/seed42/best/` (`config.json`, `vocab.json`, `weights.pt`) | 126 MB |

The fine-tuned models are the **rehearsal** checkpoints of `data_pipeline`
stage 07 (`run_pipeline.py --only 07`), selected on validation. They keep the
eight replay languages, so text in another language is reported as that
language instead of being forced into Sinhala, Pali or Sanskrit. Inputs get the
same normalisation as in the pipeline (`backend/app/ml/text.py` copies
`normalise` from `data_pipeline/lidpipe/text.py`), and the web app's predictions match the pipeline's on its
test data.

- **Leaving a model out:** don't copy its directory. It shows as unavailable
  and uses no RAM. On a small server, `lid176` plus `openlid_v3` or
  `nllb_lid218` keeps memory low.
- **After retraining:** copy the new `best/` directories over the old ones and
  run `docker compose restart celery_worker backend`.
- **Other checkpoints:** `LANGID_FINETUNED_DIR` and `LANGID_SEED` choose the
  phase directory and seed; `NLLB_MODEL_PATH`, `GLOTLID_MODEL_PATH`,
  `OPENLID_MODEL_PATH`, `CONLID_MODEL_PATH` and `LID176_MODEL_PATH` override
  single models (paths inside the container). See `backend/app/ml/paths.py`.

The model ids above are stored with each job and used for billing rates, so
keep them stable.

## Operating the server

```bash
docker compose ps                         # status
docker compose logs -f celery_worker      # follow one service
docker compose restart celery_worker      # e.g. after replacing models

git pull && docker compose up -d --build  # deploy a new version (runs migrations)
```

Back up the database and the uploaded documents regularly:

```bash
docker compose exec -T db pg_dump -U langid langid_db | gzip > langid_db_$(date +%F).sql.gz
docker run --rm -v webapp_minio_data:/data -v "$PWD":/backup alpine \
  tar czf /backup/minio_$(date +%F).tar.gz -C /data .
```

(`webapp_` is the Compose project name, taken from the directory name.)

### Tuning

| `.env` | Default | Effect |
|---|---|---|
| `API_WORKERS` | 2 | Uvicorn processes. Each uses ~0.2-0.4 GB |
| `CELERY_CONCURRENCY` | 1 | Parallel classification jobs. Each process loads its own copy of the models (up to ~5.9 GB), so raise it only with RAM to spare |
| `OCR_CONCURRENCY` | 1 | Parallel Tesseract OCR runs (~0.3 GB each, CPU-bound) |

To run without Surya OCR, stop its worker (`docker compose stop
celery_surya_worker`). Jobs that request Surya then wait in the queue, so tell
users to pick Tesseract.

## Local development

Start Postgres, Redis, MinIO and the Celery workers in Docker, and the API with
auto-reload on the host:

```bash
cp .env.example .env          # set DOMAIN=localhost; passwords must match backend/.env
cd backend
cp .env.example .env          # first time only
uv sync --extra surya --extra dev
./run.sh                      # API on http://localhost:8000, docs at /docs
```

Then the frontend:

```bash
cd frontend
npm install --legacy-peer-deps
npm run dev                   # http://localhost:3000
```

The frontend reads `NEXT_PUBLIC_API_URL` from `frontend/.env.local`
(`http://localhost:8000/api/v1`).

Tests: `cd backend && uv run pytest` (integration tests start their own
Postgres and Redis with testcontainers), and `cd frontend && npm test`.
