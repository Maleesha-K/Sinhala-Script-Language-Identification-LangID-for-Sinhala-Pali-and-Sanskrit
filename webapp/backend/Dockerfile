FROM python:3.12-slim

# Install system dependencies including Tesseract and language packs
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-sin \
    tesseract-ocr-san \
    tesseract-ocr-eng \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for Python dependency management
RUN curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="/usr/local/bin" sh

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock README.md ./

# Install dependencies using uv (with Surya OCR and CPU-only torch)
RUN uv sync --frozen --extra surya

# Copy the rest of the application
COPY . .

# Set environment variables for Python
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app

# One image serves the API and both Celery workers; docker-compose.yml sets each
# service's command. The default runs the Celery worker for the default queue.
CMD ["celery", "-A", "app.workers.celery_app", "worker", "-Q", "celery", "--loglevel=info"]
