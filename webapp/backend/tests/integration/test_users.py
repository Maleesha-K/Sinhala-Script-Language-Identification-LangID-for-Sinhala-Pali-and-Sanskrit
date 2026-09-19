"""Integration tests for the user profile endpoints.

Covers GET and PATCH /users/me, the fields a user is allowed to change, and
the authentication required to reach either route.
"""
import pytest

from app.config import settings

API = settings.API_V1_STR


# --- GET /users/me ---------------------------------------------------------

@pytest.mark.asyncio
async def test_get_me_returns_current_user(async_client, test_user):
    """GET /users/me returns the profile of the token's owner."""
    response = await async_client.get(f"{API}/users/me", headers=test_user["headers"])

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "success"

    data = body["data"]
    assert data["id"] == test_user["user"]["id"]
    assert data["email"] == test_user["email"]
    assert data["role"] == "user"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_get_me_never_exposes_password_hash(async_client, auth_headers):
    """The profile payload must not leak stored credentials."""
    response = await async_client.get(f"{API}/users/me", headers=auth_headers)

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert "password" not in data
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_get_me_includes_account_usage_fields(async_client, auth_headers):
    """The profile carries the balance and storage counters the dashboard reads."""
    response = await async_client.get(f"{API}/users/me", headers=auth_headers)

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["storage_used_bytes"] == 0
    assert float(data["credits_balance"]) > 0


@pytest.mark.asyncio
async def test_get_me_is_scoped_to_the_token(async_client, test_user, second_user):
    """Each token resolves to its own user, never another one."""
    first = await async_client.get(f"{API}/users/me", headers=test_user["headers"])
    second = await async_client.get(f"{API}/users/me", headers=second_user["headers"])

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json()["data"]["id"] == test_user["user"]["id"]
    assert second.json()["data"]["id"] == second_user["user"]["id"]
    assert first.json()["data"]["id"] != second.json()["data"]["id"]


# --- PATCH /users/me -------------------------------------------------------

@pytest.mark.asyncio
async def test_update_display_name(async_client, auth_headers):
    """PATCH /users/me updates the display name and returns the new profile."""
    response = await async_client.patch(
        f"{API}/users/me", headers=auth_headers, json={"display_name": "Renamed User"}
    )

    assert response.status_code == 200, response.text
    assert response.json()["data"]["display_name"] == "Renamed User"


@pytest.mark.asyncio
async def test_update_display_name_persists(async_client, auth_headers):
    """The updated name is still there on the next read."""
    patch = await async_client.patch(
        f"{API}/users/me", headers=auth_headers, json={"display_name": "Persisted Name"}
    )
    assert patch.status_code == 200, patch.text

    me = await async_client.get(f"{API}/users/me", headers=auth_headers)
    assert me.status_code == 200, me.text
    assert me.json()["data"]["display_name"] == "Persisted Name"


@pytest.mark.asyncio
async def test_update_with_empty_body_leaves_profile_unchanged(async_client, test_user):
    """An empty PATCH is a no-op.

    `update_user` dumps the payload with exclude_unset=True, so omitted fields
    keep their current values rather than being nulled out.
    """
    before = await async_client.get(f"{API}/users/me", headers=test_user["headers"])
    assert before.status_code == 200, before.text

    patch = await async_client.patch(
        f"{API}/users/me", headers=test_user["headers"], json={}
    )
    assert patch.status_code == 200, patch.text

    data = patch.json()["data"]
    assert data["display_name"] == before.json()["data"]["display_name"]
    assert data["email"] == test_user["email"]


@pytest.mark.asyncio
async def test_update_password_allows_login_with_new_password(async_client, test_user):
    """Changing the password re-hashes it, and the new one works at login."""
    new_password = "BrandNewPass456!"

    patch = await async_client.patch(
        f"{API}/users/me",
        headers=test_user["headers"],
        json={"password": new_password},
    )
    assert patch.status_code == 200, patch.text

    login = await async_client.post(
        f"{API}/auth/login",
        json={"email": test_user["email"], "password": new_password},
    )
    assert login.status_code == 200, login.text
    assert login.json()["data"]["access_token"]


@pytest.mark.asyncio
async def test_update_password_invalidates_the_old_password(async_client, test_user):
    """The previous password stops working once it has been replaced."""
    patch = await async_client.patch(
        f"{API}/users/me",
        headers=test_user["headers"],
        json={"password": "BrandNewPass456!"},
    )
    assert patch.status_code == 200, patch.text

    login = await async_client.post(
        f"{API}/auth/login",
        json={"email": test_user["email"], "password": test_user["password"]},
    )
    assert login.status_code == 401, login.text


@pytest.mark.asyncio
async def test_update_never_returns_the_new_password(async_client, auth_headers):
    """A password change must not echo the credential back."""
    response = await async_client.patch(
        f"{API}/users/me", headers=auth_headers, json={"password": "BrandNewPass456!"}
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert "password" not in data
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_update_with_short_password_returns_422(async_client, auth_headers):
    """UserUpdate enforces the same 8 character minimum as signup."""
    response = await async_client.patch(
        f"{API}/users/me", headers=auth_headers, json={"password": "short"}
    )
    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_update_with_overlong_display_name_returns_422(async_client, auth_headers):
    """display_name is capped at 128 characters."""
    response = await async_client.patch(
        f"{API}/users/me", headers=auth_headers, json={"display_name": "x" * 129}
    )
    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_update_ignores_privileged_fields(async_client, test_user):
    """Unknown keys cannot escalate a role or hand out credits.

    UserUpdate only declares display_name and password and leaves Pydantic's
    default "ignore" policy in place, so extra keys are stripped during
    validation and never reach the model.
    """
    response = await async_client.patch(
        f"{API}/users/me",
        headers=test_user["headers"],
        json={
            "display_name": "Still A User",
            "role": "admin",
            "is_active": False,
            "credits_balance": 999999,
            "email": "attacker@test.com",
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["display_name"] == "Still A User"  # the one allowed field applied
    assert data["role"] == "user"
    assert data["is_active"] is True
    assert data["email"] == test_user["email"]
    assert float(data["credits_balance"]) != 999999


@pytest.mark.asyncio
async def test_update_does_not_affect_other_users(async_client, test_user, second_user):
    """A PATCH is scoped to the caller and leaves other accounts alone."""
    patch = await async_client.patch(
        f"{API}/users/me",
        headers=test_user["headers"],
        json={"display_name": "Only Mine"},
    )
    assert patch.status_code == 200, patch.text

    other = await async_client.get(f"{API}/users/me", headers=second_user["headers"])
    assert other.status_code == 200, other.text
    assert other.json()["data"]["display_name"] != "Only Mine"
    assert other.json()["data"]["id"] == second_user["user"]["id"]


# --- authentication --------------------------------------------------------

@pytest.mark.asyncio
async def test_get_me_without_token_returns_401(async_client):
    """GET /users/me requires a bearer token."""
    response = await async_client.get(f"{API}/users/me")
    assert response.status_code == 401, response.text


@pytest.mark.asyncio
async def test_patch_me_without_token_returns_401(async_client):
    """PATCH /users/me requires a bearer token."""
    response = await async_client.patch(
        f"{API}/users/me", json={"display_name": "Anonymous"}
    )
    assert response.status_code == 401, response.text


@pytest.mark.asyncio
async def test_get_me_with_invalid_token_returns_401(async_client):
    """A malformed bearer value is rejected."""
    response = await async_client.get(
        f"{API}/users/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert response.status_code == 401, response.text


@pytest.mark.asyncio
async def test_patch_me_with_invalid_token_returns_401(async_client):
    """PATCH is protected by the same dependency as GET."""
    response = await async_client.patch(
        f"{API}/users/me",
        headers={"Authorization": "Bearer not-a-real-token"},
        json={"display_name": "Anonymous"},
    )
    assert response.status_code == 401, response.text


@pytest.mark.asyncio
async def test_patch_me_with_refresh_token_returns_401(async_client, test_user):
    """A refresh token must not authorise a profile change."""
    response = await async_client.patch(
        f"{API}/users/me",
        headers={"Authorization": f"Bearer {test_user['refresh_token']}"},
        json={"display_name": "Anonymous"},
    )
    assert response.status_code == 401, response.text


@pytest.mark.asyncio
async def test_deactivated_user_cannot_read_profile(async_client, test_user):
    """An existing token stops working once the account is deactivated."""
    from sqlalchemy import select

    from app.db.models.user import User
    from app.db.session import async_session_maker

    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.email == test_user["email"])
        )
        user = result.scalar_one()
        user.is_active = False
        await session.commit()

    response = await async_client.get(f"{API}/users/me", headers=test_user["headers"])
    assert response.status_code == 401, response.text
    assert "Inactive" in response.json()["message"]
