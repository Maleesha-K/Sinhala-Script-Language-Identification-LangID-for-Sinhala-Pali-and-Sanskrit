import os
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from alembic.config import Config
from alembic import command

# Mock MinIO before importing app to avoid connection errors during test collection
patcher = patch("minio.Minio")
patcher.start()

# Start testcontainers before app import so pydantic settings picks up the env vars
postgres = PostgresContainer("postgres:15-alpine")
redis = RedisContainer("redis:7-alpine")
postgres.start()
redis.start()

os.environ["POSTGRES_USER"] = postgres.username
os.environ["POSTGRES_PASSWORD"] = postgres.password
os.environ["POSTGRES_SERVER"] = postgres.get_container_host_ip()
os.environ["POSTGRES_PORT"] = str(postgres.get_exposed_port(5432))
os.environ["POSTGRES_DB"] = postgres.dbname

os.environ["REDIS_HOST"] = redis.get_container_host_ip()
os.environ["REDIS_PORT"] = str(redis.get_exposed_port(6379))

from app.main import app
from app.config import settings

# Run Alembic migrations programmatically
def run_migrations():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

run_migrations()

@pytest.fixture(scope="session", autouse=True)
def cleanup_containers():
    yield
    postgres.stop()
    redis.stop()

@pytest.fixture
async def async_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
