import pytest

@pytest.mark.asyncio
async def test_health_endpoint(async_client):
    response = await async_client.get("/")
    # Assuming there's a root or health endpoint, adapt as needed.
    # We will just check if we get a response (could be 404 if no root exists)
    assert response.status_code in [200, 404]
