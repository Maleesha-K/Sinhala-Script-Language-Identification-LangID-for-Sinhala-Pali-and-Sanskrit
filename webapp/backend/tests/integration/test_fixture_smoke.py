import pytest
from app.config import settings

API = settings.API_V1_STR


@pytest.mark.asyncio
async def test_auth_headers_reach_protected_route(async_client, auth_headers):
    r = await async_client.get(f"{API}/users/me", headers=auth_headers)
    assert r.status_code == 200, r.text
    assert r.json()["data"]["role"] == "user"


@pytest.mark.asyncio
async def test_second_user_is_distinct(async_client, test_user, second_user):
    assert test_user["email"] != second_user["email"]
    assert test_user["user"]["id"] != second_user["user"]["id"]


@pytest.mark.asyncio
async def test_admin_headers_pass_require_admin(async_client, admin_headers):
    me = await async_client.get(f"{API}/users/me", headers=admin_headers)
    assert me.status_code == 200, me.text
    assert me.json()["data"]["role"] == "admin"

    tiers = await async_client.get(f"{API}/admin/tiers", headers=admin_headers)
    assert tiers.status_code == 200, tiers.text


@pytest.mark.asyncio
async def test_regular_user_forbidden_on_admin_route(async_client, auth_headers):
    r = await async_client.get(f"{API}/admin/tiers", headers=auth_headers)
    assert r.status_code == 403, r.text


@pytest.mark.asyncio
async def test_fixtures_are_reusable_across_tests(async_client, auth_headers):
    r = await async_client.get(f"{API}/users/me", headers=auth_headers)
    assert r.status_code == 200, r.text
