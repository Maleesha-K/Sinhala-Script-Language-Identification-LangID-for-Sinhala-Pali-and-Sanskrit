import os
import uuid
import pytest
import pytest_asyncio
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
    # env.py will use the overridden settings.DATABASE_URL
    command.upgrade(alembic_cfg, "head")

run_migrations()

API = settings.API_V1_STR

# Test isolation strategy
# ---------------------------------------------------------------------------
# Containers are session-scoped and the app's endpoints each commit through the
# global `async_session_maker`, so a transaction-rollback fixture cannot wrap a
# request without breaking the commit-heavy service layer. Instead every fixture
# below mints a unique email per test, so tests never collide on the users.email
# unique constraint and can run in any order.

def unique_email(prefix: str = "user") -> str:
    """Return an email address that is unique to this test invocation."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}@test.com"


@pytest.fixture(scope="session", autouse=True)
def cleanup_containers():
    yield
    postgres.stop()
    redis.stop()

@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_between_tests():
    """Drop pooled DB connections at the end of each test.

    The app holds a module-level async engine, but pytest-asyncio runs every
    test on a fresh event loop. A connection pooled on a previous loop breaks
    when reused ("'NoneType' object has no attribute 'send'" on Windows), so
    the pool is disposed while its own loop is still running.
    """
    from app.db.session import engine

    yield
    await engine.dispose()


@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


async def _register_and_login(client: AsyncClient, email: str, password: str) -> dict:
    """Sign a user up, log them in, and return the created user plus its tokens."""
    signup = await client.post(
        f"{API}/auth/signup",
        json={"email": email, "password": password, "display_name": "Test User"},
    )
    assert signup.status_code == 201, signup.text

    login = await client.post(
        f"{API}/auth/login", json={"email": email, "password": password}
    )
    assert login.status_code == 200, login.text

    tokens = login.json()["data"]
    return {
        "user": signup.json()["data"],
        "email": email,
        "password": password,
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "headers": {"Authorization": f"Bearer {tokens['access_token']}"},
    }


@pytest_asyncio.fixture
async def test_user(async_client) -> dict:
    """A freshly registered regular user with its tokens and auth headers."""
    return await _register_and_login(
        async_client, unique_email("user"), "TestPass123!"
    )


@pytest_asyncio.fixture
async def auth_headers(test_user) -> dict:
    """Authorization headers for a regular user."""
    return test_user["headers"]


@pytest_asyncio.fixture
async def second_user(async_client) -> dict:
    """A second, unrelated user - used to assert cross-user ownership isolation."""
    return await _register_and_login(
        async_client, unique_email("other"), "OtherPass123!"
    )


@pytest_asyncio.fixture
async def second_user_headers(second_user) -> dict:
    """Authorization headers for the second user."""
    return second_user["headers"]


@pytest_asyncio.fixture
async def admin_user(async_client) -> dict:
    """An admin user.

    Signup always creates role=USER, so the account is promoted to ADMIN with a
    direct DB write before logging in and minting the token.
    """
    from sqlalchemy import select
    from app.db.session import async_session_maker
    from app.db.models.user import User, UserRole

    email = unique_email("admin")
    password = "AdminPass123!"

    signup = await async_client.post(
        f"{API}/auth/signup",
        json={"email": email, "password": password, "display_name": "Admin User"},
    )
    assert signup.status_code == 201, signup.text

    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one()
        user.role = UserRole.ADMIN
        await session.commit()

    login = await async_client.post(
        f"{API}/auth/login", json={"email": email, "password": password}
    )
    assert login.status_code == 200, login.text

    tokens = login.json()["data"]
    return {
        "user": signup.json()["data"],
        "email": email,
        "password": password,
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "headers": {"Authorization": f"Bearer {tokens['access_token']}"},
    }


@pytest_asyncio.fixture
async def admin_headers(admin_user) -> dict:
    """Authorization headers for an admin user."""
    return admin_user["headers"]
