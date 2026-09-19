"""Integration tests for the authentication endpoints.

Covers signup, login, token refresh, and the token `type` claim enforced by
`get_current_user` in app/dependencies.py.
"""
from datetime import timedelta

import pytest

from app.config import settings
from tests.conftest import unique_email

API = settings.API_V1_STR


# --- signup ----------------------------------------------------------------

@pytest.mark.asyncio
async def test_signup_creates_user(async_client):
    """POST /auth/signup returns 201 and the created user, without secrets."""
    email = unique_email("signup")
    response = await async_client.post(
        f"{API}/auth/signup",
        json={"email": email, "password": "StrongPass123!", "display_name": "New User"},
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "success"

    data = body["data"]
    assert data["email"] == email
    assert data["display_name"] == "New User"
    assert data["role"] == "user"
    assert data["is_active"] is True
    assert "id" in data

    # Credentials must never be echoed back.
    assert "password" not in data
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_signup_grants_free_tier_credits(async_client):
    """A new user starts on the free tier, so they get a positive credit balance."""
    response = await async_client.post(
        f"{API}/auth/signup",
        json={"email": unique_email("credits"), "password": "StrongPass123!"},
    )

    assert response.status_code == 201, response.text
    assert float(response.json()["data"]["credits_balance"]) > 0


@pytest.mark.asyncio
async def test_signup_with_duplicate_email_returns_400(async_client):
    """The second signup for an email is rejected by the uniqueness check."""
    email = unique_email("dupe")
    payload = {"email": email, "password": "StrongPass123!"}

    first = await async_client.post(f"{API}/auth/signup", json=payload)
    assert first.status_code == 201, first.text

    second = await async_client.post(f"{API}/auth/signup", json=payload)
    assert second.status_code == 400, second.text
    assert second.json()["status"] == "failed"
    assert "already exists" in second.json()["message"]


@pytest.mark.asyncio
async def test_signup_with_invalid_email_returns_422(async_client):
    """Pydantic's EmailStr rejects a malformed address before any DB work."""
    response = await async_client.post(
        f"{API}/auth/signup",
        json={"email": "not-an-email", "password": "StrongPass123!"},
    )
    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_signup_with_short_password_returns_422(async_client):
    """UserCreate enforces a minimum password length of 8."""
    response = await async_client.post(
        f"{API}/auth/signup",
        json={"email": unique_email("short"), "password": "short"},
    )
    assert response.status_code == 422, response.text


# --- login -----------------------------------------------------------------

@pytest.mark.asyncio
async def test_login_returns_tokens(async_client, test_user):
    """Valid credentials yield an access and a refresh token."""
    response = await async_client.post(
        f"{API}/auth/login",
        json={"email": test_user["email"], "password": test_user["password"]},
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"
    assert data["access_token"] != data["refresh_token"]


@pytest.mark.asyncio
async def test_login_with_wrong_password_returns_401(async_client, test_user):
    """A wrong password is rejected."""
    response = await async_client.post(
        f"{API}/auth/login",
        json={"email": test_user["email"], "password": "DefinitelyWrong123!"},
    )
    assert response.status_code == 401, response.text
    assert response.json()["status"] == "failed"


@pytest.mark.asyncio
async def test_login_with_unknown_email_returns_401(async_client):
    """An unregistered email is rejected with the same status as a bad password."""
    response = await async_client.post(
        f"{API}/auth/login",
        json={"email": unique_email("ghost"), "password": "StrongPass123!"},
    )
    assert response.status_code == 401, response.text


@pytest.mark.asyncio
async def test_login_does_not_reveal_whether_email_exists(async_client, test_user):
    """Unknown email and wrong password return an identical message.

    Differing responses would let an attacker enumerate registered accounts.
    """
    wrong_password = await async_client.post(
        f"{API}/auth/login",
        json={"email": test_user["email"], "password": "DefinitelyWrong123!"},
    )
    unknown_email = await async_client.post(
        f"{API}/auth/login",
        json={"email": unique_email("ghost"), "password": "DefinitelyWrong123!"},
    )

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json()["message"] == unknown_email.json()["message"]


@pytest.mark.asyncio
async def test_login_for_inactive_user_returns_401(async_client, test_user):
    """Deactivating a user blocks further logins."""
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

    response = await async_client.post(
        f"{API}/auth/login",
        json={"email": test_user["email"], "password": test_user["password"]},
    )
    assert response.status_code == 401, response.text
    assert "Inactive" in response.json()["message"]


# --- refresh ---------------------------------------------------------------

@pytest.mark.asyncio
async def test_refresh_returns_new_tokens(async_client, test_user):
    """A valid refresh token is exchanged for a fresh token pair."""
    response = await async_client.post(
        f"{API}/auth/refresh", json={"refresh_token": test_user["refresh_token"]}
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refreshed_access_token_is_usable(async_client, test_user):
    """The access token handed back by /refresh authenticates a protected route."""
    refresh = await async_client.post(
        f"{API}/auth/refresh", json={"refresh_token": test_user["refresh_token"]}
    )
    assert refresh.status_code == 200, refresh.text

    new_access = refresh.json()["data"]["access_token"]
    me = await async_client.get(
        f"{API}/users/me", headers={"Authorization": f"Bearer {new_access}"}
    )
    assert me.status_code == 200, me.text
    assert me.json()["data"]["email"] == test_user["email"]


@pytest.mark.asyncio
async def test_refresh_with_malformed_token_returns_401(async_client):
    """A token that is not valid JWT is rejected."""
    response = await async_client.post(
        f"{API}/auth/refresh", json={"refresh_token": "not.a.jwt"}
    )
    assert response.status_code == 401, response.text


@pytest.mark.asyncio
async def test_refresh_rejects_an_access_token(async_client, test_user):
    """An access token cannot stand in for a refresh token.

    `refresh_tokens` requires the payload's `type` claim to be "refresh".
    """
    response = await async_client.post(
        f"{API}/auth/refresh", json={"refresh_token": test_user["access_token"]}
    )
    assert response.status_code == 401, response.text
    assert "Invalid refresh token" in response.json()["message"]


# --- token type enforcement on protected routes ----------------------------

@pytest.mark.asyncio
async def test_refresh_token_cannot_be_used_as_access_token(async_client, test_user):
    """A refresh token must not authenticate a protected route.

    `get_current_user` (app/dependencies.py) requires `type == "access"`.
    Without that check, a long-lived refresh token would grant API access for
    its full lifetime.
    """
    response = await async_client.get(
        f"{API}/users/me",
        headers={"Authorization": f"Bearer {test_user['refresh_token']}"},
    )
    assert response.status_code == 401, response.text
    assert response.json()["status"] == "failed"


@pytest.mark.asyncio
async def test_protected_route_without_token_returns_401(async_client):
    """A protected route requires an Authorization header."""
    response = await async_client.get(f"{API}/users/me")
    assert response.status_code == 401, response.text


@pytest.mark.asyncio
async def test_protected_route_with_garbage_token_returns_401(async_client):
    """A non-JWT bearer value is rejected."""
    response = await async_client.get(
        f"{API}/users/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert response.status_code == 401, response.text


@pytest.mark.asyncio
async def test_expired_access_token_returns_401(async_client, test_user):
    """An expired access token is rejected."""
    from app.utils.security import create_access_token

    expired = create_access_token(
        subject=test_user["user"]["id"], expires_delta=timedelta(minutes=-5)
    )
    response = await async_client.get(
        f"{API}/users/me", headers={"Authorization": f"Bearer {expired}"}
    )
    assert response.status_code == 401, response.text


@pytest.mark.asyncio
async def test_token_signed_with_wrong_secret_returns_401(async_client, test_user):
    """A token forged with the wrong signing key is rejected."""
    from datetime import datetime, timezone

    from jose import jwt

    forged = jwt.encode(
        {
            "sub": str(test_user["user"]["id"]),
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        },
        "an-attackers-secret-key",
        algorithm=settings.ALGORITHM,
    )
    response = await async_client.get(
        f"{API}/users/me", headers={"Authorization": f"Bearer {forged}"}
    )
    assert response.status_code == 401, response.text
