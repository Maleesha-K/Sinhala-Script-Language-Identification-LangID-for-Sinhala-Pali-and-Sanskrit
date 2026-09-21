import os
import pytest
from unittest.mock import patch, MagicMock

# Set testing environment variables for pure unit test isolation
os.environ.setdefault("POSTGRES_USER", "langid")
os.environ.setdefault("POSTGRES_PASSWORD", "langid_password")
os.environ.setdefault("POSTGRES_SERVER", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_DB", "langid_db")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("SECRET_KEY", "test_secret_key_for_unit_tests_only_12345")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("MINIO_ENDPOINT", "localhost:9000")

# Patch MinIO client to prevent external network calls during unit testing
try:
    patch("minio.Minio").start()
except Exception:
    pass
