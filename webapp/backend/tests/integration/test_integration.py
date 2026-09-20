import pytest


@pytest.mark.asyncio
async def test_health_endpoint(async_client):
    """The app exposes an unauthenticated /health check."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
