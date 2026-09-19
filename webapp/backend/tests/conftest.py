import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch

# Mock MinIO before importing app to avoid connection errors during test collection
patcher = patch("minio.Minio")
patcher.start()

from app.main import app

@pytest.fixture
async def async_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
