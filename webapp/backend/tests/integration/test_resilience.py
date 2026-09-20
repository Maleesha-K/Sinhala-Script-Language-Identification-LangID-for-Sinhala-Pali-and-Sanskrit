import pytest
from httpx import AsyncClient
from unittest.mock import patch
import sqlalchemy.exc
import redis.exceptions

@pytest.mark.asyncio
async def test_api_returns_503_on_db_outage(async_client: AsyncClient):
    """
    Test that if the database is unreachable (raising OperationalError),
    the API returns a 503 Service Unavailable instead of a 500 Internal Server Error.
    """
    # We patch AsyncSession.execute to simulate a DB connection failure
    with patch(
        "sqlalchemy.ext.asyncio.AsyncSession.execute", 
        side_effect=sqlalchemy.exc.OperationalError(statement="test", params={}, orig=Exception("Connection refused"))
    ):
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password"}
        )
        
    assert response.status_code == 503
    assert response.json() == {
        "status": "failed",
        "message": "Service Unavailable: Database connection failed",
        "data": None
    }

@pytest.mark.asyncio
async def test_api_returns_503_on_redis_outage(async_client: AsyncClient, auth_headers: dict, mocker):
    """
    Test that if Redis is unreachable (raising ConnectionError when pushing a celery task),
    the API returns a 503 Service Unavailable instead of a 500.
    """
    # We patch the celery delay method directly
    with patch(
        "app.api.v1.classification.process_classification_job.delay",
        side_effect=redis.exceptions.ConnectionError("Connection refused")
    ):
        response = await async_client.post(
            "/api/v1/classification/jobs",
            json={"input_text": "test text"},
            headers=auth_headers
        )
            
        # The exception handler should catch the redis connection error
        assert response.status_code == 503
        assert response.json() == {
            "status": "failed",
            "message": "Service Unavailable: Cache connection failed",
            "data": None
        }
