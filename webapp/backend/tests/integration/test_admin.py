"""Integration tests for the admin endpoints.

Two routers are covered:

* ``/admin``      - tiers, system config, and a model-rate group backed by
                    ``admin_service``
* ``/admin-rates`` - a second, self-contained model-rate CRUD router

Three defects found while writing these tests are now fixed, and the tests
below are the regression guards for them:

1. ``POST /admin/model-rates`` could never succeed - its schema omitted the
   non-null ``model_type`` column.
2. ``admin_service`` raised ``AppException(detail=...)`` while the constructor
   takes ``message``, so every "not found" path 500d instead of 404ing.
3. A second zero-price tier was accepted, which then broke signup for every
   new user.
"""
import uuid

import pytest
import pytest_asyncio

from app.config import settings

API = settings.API_V1_STR


def unique_name(prefix: str) -> str:
    """Model rate names are unique in the schema, so each test needs its own."""
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


async def create_tier(client, headers, **overrides) -> dict:
    """Create a paid tier and return it."""
    payload = {
        "name": unique_name("Tier"),
        "price_usd": 9.99,
        "included_credits": 5000,
        "ocr_pages_included": 200,
    }
    payload.update(overrides)

    response = await client.post(f"{API}/admin/tiers", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()["data"]


async def create_rate(client, headers, **overrides) -> dict:
    """Create a model rate through the working /admin-rates router."""
    payload = {
        "model_type": "classification",
        "model_name": unique_name("model"),
        "credits_per_token": 0.001,
        "credits_per_page": 0.0,
    }
    payload.update(overrides)

    response = await client.post(f"{API}/admin-rates", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()["data"]


# --- tiers -----------------------------------------------------------------

@pytest.mark.asyncio
async def test_admin_can_list_tiers(async_client, admin_headers):
    """GET /admin/tiers returns the tier definitions."""
    response = await async_client.get(f"{API}/admin/tiers", headers=admin_headers)

    assert response.status_code == 200, response.text
    assert isinstance(response.json()["data"], list)


@pytest.mark.asyncio
async def test_admin_can_create_tier(async_client, admin_headers):
    """POST /admin/tiers creates a tier and defaults it to active."""
    name = unique_name("Pro")

    response = await async_client.post(
        f"{API}/admin/tiers",
        headers=admin_headers,
        json={
            "name": name,
            "price_usd": 19.99,
            "included_credits": 10000,
            "ocr_pages_included": 500,
        },
    )

    assert response.status_code == 201, response.text
    data = response.json()["data"]
    assert data["name"] == name
    assert data["price_usd"] == pytest.approx(19.99)
    assert data["included_credits"] == pytest.approx(10000)
    assert data["ocr_pages_included"] == 500
    assert data["is_active"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_created_tier_appears_in_listing(async_client, admin_headers):
    """A created tier is readable through the listing."""
    tier = await create_tier(async_client, admin_headers)

    response = await async_client.get(f"{API}/admin/tiers", headers=admin_headers)

    assert response.status_code == 200, response.text
    assert tier["id"] in {item["id"] for item in response.json()["data"]}


@pytest.mark.asyncio
async def test_admin_can_update_tier(async_client, admin_headers):
    """PUT /admin/tiers/{id} applies a partial update."""
    tier = await create_tier(async_client, admin_headers)

    response = await async_client.put(
        f"{API}/admin/tiers/{tier['id']}",
        headers=admin_headers,
        json={"price_usd": 29.99},
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["price_usd"] == pytest.approx(29.99)
    assert data["name"] == tier["name"]  # untouched fields are preserved


@pytest.mark.asyncio
async def test_admin_can_delete_paid_tier(async_client, admin_headers):
    """A paid tier can be removed."""
    tier = await create_tier(async_client, admin_headers)

    response = await async_client.delete(
        f"{API}/admin/tiers/{tier['id']}", headers=admin_headers
    )
    assert response.status_code == 200, response.text

    listing = await async_client.get(f"{API}/admin/tiers", headers=admin_headers)
    assert tier["id"] not in {item["id"] for item in listing.json()["data"]}


@pytest_asyncio.fixture
async def temporary_free_tier(async_client, admin_headers):
    """Create a zero-price tier and remove it again afterwards.

    A second zero-price tier breaks signup for every later test (see
    test_second_free_tier_breaks_signup), so it must not outlive its test.
    Cleanup goes through the DB because the API refuses to delete it.
    """
    tier = await create_tier(async_client, admin_headers, price_usd=0)

    yield tier

    from sqlalchemy import delete

    from app.db.models.tier import TierDefinition
    from app.db.session import async_session_maker

    async with async_session_maker() as session:
        await session.execute(
            delete(TierDefinition).where(TierDefinition.id == uuid.UUID(tier["id"]))
        )
        await session.commit()


@pytest.mark.asyncio
async def test_free_tier_cannot_be_deleted(
    async_client, admin_headers, temporary_free_tier
):
    """The zero-price tier is protected, since new users are assigned it."""
    response = await async_client.delete(
        f"{API}/admin/tiers/{temporary_free_tier['id']}", headers=admin_headers
    )

    assert response.status_code == 400, response.text
    assert "Free Tier" in response.json()["message"]

    listing = await async_client.get(f"{API}/admin/tiers", headers=admin_headers)
    assert temporary_free_tier["id"] in {
        item["id"] for item in listing.json()["data"]
    }


@pytest.mark.asyncio
async def test_signup_survives_a_second_free_tier(
    async_client, temporary_free_tier
):
    """Signup keeps working when more than one zero-price tier exists.

    Regression guard: create_user resolved the free tier with
    scalar_one_or_none(), which raised MultipleResultsFound as soon as a
    second zero-price tier was created. Since the admin API accepts such a
    tier (201), an admin could lock every new user out of registration. The
    lookup is now ordered and limited to one row.
    """
    response = await async_client.post(
        f"{API}/auth/signup",
        json={
            "email": f"after_free_{uuid.uuid4().hex[:10]}@test.com",
            "password": "StrongPass123!",
        },
    )

    assert response.status_code == 201, response.text
    assert float(response.json()["data"]["credits_balance"]) > 0


@pytest.mark.asyncio
async def test_create_tier_with_missing_fields_returns_422(async_client, admin_headers):
    """TierCreate requires name, price, credits and OCR pages."""
    response = await async_client.post(
        f"{API}/admin/tiers", headers=admin_headers, json={"name": "Incomplete"}
    )
    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_update_missing_tier_returns_404(async_client, admin_headers):
    """A missing tier is a 404, not a 500.

    Regression guard: admin_service used to build
    AppException(status_code=..., detail=...) while the constructor takes
    `message`, so the TypeError escaped to the global handler as a 500.
    """
    response = await async_client.put(
        f"{API}/admin/tiers/{uuid.uuid4()}",
        headers=admin_headers,
        json={"price_usd": 1.0},
    )

    assert response.status_code == 404, response.text
    assert response.json()["message"] == "Tier not found"


@pytest.mark.asyncio
async def test_delete_missing_tier_returns_404(async_client, admin_headers):
    """The delete path carries the same fix as the update path."""
    response = await async_client.delete(
        f"{API}/admin/tiers/{uuid.uuid4()}", headers=admin_headers
    )

    assert response.status_code == 404, response.text
    assert response.json()["message"] == "Tier not found"


# --- system config ---------------------------------------------------------

@pytest.mark.asyncio
async def test_admin_can_read_config(async_client, admin_headers):
    """GET /admin/config seeds and returns the conversion rate."""
    response = await async_client.get(f"{API}/admin/config", headers=admin_headers)

    assert response.status_code == 200, response.text
    assert response.json()["data"]["usd_to_credits_rate"] > 0


@pytest.mark.asyncio
async def test_admin_can_update_config(async_client, admin_headers):
    """PUT /admin/config changes the conversion rate."""
    response = await async_client.put(
        f"{API}/admin/config",
        headers=admin_headers,
        json={"usd_to_credits_rate": 250.0},
    )

    assert response.status_code == 200, response.text
    assert response.json()["data"]["usd_to_credits_rate"] == pytest.approx(250.0)


@pytest.mark.asyncio
async def test_config_update_persists(async_client, admin_headers):
    """The new rate is returned on the next read."""
    await async_client.put(
        f"{API}/admin/config",
        headers=admin_headers,
        json={"usd_to_credits_rate": 321.0},
    )

    response = await async_client.get(f"{API}/admin/config", headers=admin_headers)

    assert response.status_code == 200, response.text
    assert response.json()["data"]["usd_to_credits_rate"] == pytest.approx(321.0)


@pytest.mark.asyncio
async def test_config_update_requires_rate(async_client, admin_headers):
    """usd_to_credits_rate is required."""
    response = await async_client.put(
        f"{API}/admin/config", headers=admin_headers, json={}
    )
    assert response.status_code == 422, response.text


# --- model rates (/admin-rates) --------------------------------------------

@pytest.mark.asyncio
async def test_admin_can_list_available_models(async_client, admin_headers):
    """The catalogue of known models is exposed to admins."""
    response = await async_client.get(
        f"{API}/admin-rates/available-models", headers=admin_headers
    )

    assert response.status_code == 200, response.text
    names = {item["model_name"] for item in response.json()["data"]}
    assert "sklearn_langid" in names
    assert "tesseract" in names


@pytest.mark.asyncio
async def test_admin_can_create_rate(async_client, admin_headers):
    """POST /admin-rates creates a rate for a model."""
    name = unique_name("classifier")

    response = await async_client.post(
        f"{API}/admin-rates",
        headers=admin_headers,
        json={
            "model_type": "classification",
            "model_name": name,
            "credits_per_token": 0.002,
        },
    )

    assert response.status_code == 201, response.text
    data = response.json()["data"]
    assert data["model_name"] == name
    assert data["model_type"] == "classification"
    assert data["credits_per_token"] == pytest.approx(0.002)
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_admin_can_list_rates(async_client, admin_headers):
    """A created rate appears in the listing."""
    rate = await create_rate(async_client, admin_headers)

    response = await async_client.get(f"{API}/admin-rates", headers=admin_headers)

    assert response.status_code == 200, response.text
    assert rate["id"] in {item["id"] for item in response.json()["data"]}


@pytest.mark.asyncio
async def test_create_duplicate_rate_returns_400(async_client, admin_headers):
    """model_name is unique, so a second rate for it is rejected."""
    rate = await create_rate(async_client, admin_headers)

    response = await async_client.post(
        f"{API}/admin-rates",
        headers=admin_headers,
        json={
            "model_type": "classification",
            "model_name": rate["model_name"],
            "credits_per_token": 0.5,
        },
    )

    assert response.status_code == 400, response.text
    assert "already exists" in response.json()["message"]


@pytest.mark.asyncio
async def test_admin_can_update_rate(async_client, admin_headers):
    """PUT /admin-rates/{id} applies a partial update."""
    rate = await create_rate(async_client, admin_headers)

    response = await async_client.put(
        f"{API}/admin-rates/{rate['id']}",
        headers=admin_headers,
        json={"credits_per_token": 0.05},
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["credits_per_token"] == pytest.approx(0.05)
    assert data["model_name"] == rate["model_name"]


@pytest.mark.asyncio
async def test_admin_can_deactivate_rate(async_client, admin_headers):
    """A rate can be switched off without being deleted.

    credit_service refuses to charge against an inactive rate, so this is the
    switch that takes a model out of service.
    """
    rate = await create_rate(async_client, admin_headers)

    response = await async_client.put(
        f"{API}/admin-rates/{rate['id']}",
        headers=admin_headers,
        json={"is_active": False},
    )

    assert response.status_code == 200, response.text
    assert response.json()["data"]["is_active"] is False


@pytest.mark.asyncio
async def test_admin_can_delete_rate(async_client, admin_headers):
    """DELETE /admin-rates/{id} removes the rate."""
    rate = await create_rate(async_client, admin_headers)

    response = await async_client.delete(
        f"{API}/admin-rates/{rate['id']}", headers=admin_headers
    )
    assert response.status_code == 200, response.text

    listing = await async_client.get(f"{API}/admin-rates", headers=admin_headers)
    assert rate["id"] not in {item["id"] for item in listing.json()["data"]}


@pytest.mark.asyncio
async def test_update_missing_rate_returns_404(async_client, admin_headers):
    """This router raises HTTPException directly, so it 404s correctly."""
    response = await async_client.put(
        f"{API}/admin-rates/{uuid.uuid4()}",
        headers=admin_headers,
        json={"credits_per_token": 1.0},
    )
    assert response.status_code == 404, response.text


@pytest.mark.asyncio
async def test_delete_missing_rate_returns_404(async_client, admin_headers):
    """Deleting an unknown rate is a 404."""
    response = await async_client.delete(
        f"{API}/admin-rates/{uuid.uuid4()}", headers=admin_headers
    )
    assert response.status_code == 404, response.text


@pytest.mark.asyncio
async def test_create_rate_with_negative_credits_returns_422(
    async_client, admin_headers
):
    """Rates are bounded at zero by ge=0, so a negative rate is rejected."""
    response = await async_client.post(
        f"{API}/admin-rates",
        headers=admin_headers,
        json={
            "model_type": "classification",
            "model_name": unique_name("negative"),
            "credits_per_token": -1.0,
        },
    )
    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_create_rate_with_unknown_type_returns_422(async_client, admin_headers):
    """model_type is an enum of classification and ocr."""
    response = await async_client.post(
        f"{API}/admin-rates",
        headers=admin_headers,
        json={
            "model_type": "telepathy",
            "model_name": unique_name("unknown"),
            "credits_per_token": 0.1,
        },
    )
    assert response.status_code == 422, response.text


# --- model rates (/admin/model-rates) --------------------------------------

@pytest.mark.asyncio
async def test_admin_can_list_model_rates_via_admin_router(
    async_client, admin_headers
):
    """The /admin router can read rates, even though it cannot create them."""
    rate = await create_rate(async_client, admin_headers)

    response = await async_client.get(f"{API}/admin/model-rates", headers=admin_headers)

    assert response.status_code == 200, response.text
    assert rate["id"] in {item["id"] for item in response.json()["data"]}


@pytest.mark.asyncio
async def test_create_model_rate_via_admin_router(async_client, admin_headers):
    """POST /admin/model-rates creates a rate.

    Regression guard: ModelRateBase had no model_type field while
    model_rates.model_type is NOT NULL, so every insert raised IntegrityError
    and the endpoint could not succeed for any input.
    """
    name = unique_name("viaadmin")

    response = await async_client.post(
        f"{API}/admin/model-rates",
        headers=admin_headers,
        json={
            "model_type": "ocr",
            "model_name": name,
            "credits_per_page": 0.25,
        },
    )

    assert response.status_code == 201, response.text
    data = response.json()["data"]
    assert data["model_name"] == name
    assert data["model_type"] == "ocr"
    assert data["credits_per_page"] == pytest.approx(0.25)


@pytest.mark.asyncio
async def test_create_model_rate_via_admin_router_requires_type(
    async_client, admin_headers
):
    """model_type is required, so the NOT NULL column can always be filled."""
    response = await async_client.post(
        f"{API}/admin/model-rates",
        headers=admin_headers,
        json={"model_name": unique_name("typeless"), "credits_per_token": 0.5},
    )
    assert response.status_code == 422, response.text


# --- access control --------------------------------------------------------

ADMIN_READS = [
    "/admin/tiers",
    "/admin/config",
    "/admin/model-rates",
    "/admin-rates",
    "/admin-rates/available-models",
]


@pytest.mark.parametrize("path", ADMIN_READS)
@pytest.mark.asyncio
async def test_regular_user_cannot_read_admin_routes(async_client, auth_headers, path):
    """Every admin read is closed to a regular user."""
    response = await async_client.get(f"{API}{path}", headers=auth_headers)
    assert response.status_code == 403, response.text


@pytest.mark.parametrize("path", ADMIN_READS)
@pytest.mark.asyncio
async def test_admin_routes_require_a_token(async_client, path):
    """Every admin read requires authentication."""
    response = await async_client.get(f"{API}{path}")
    assert response.status_code == 401, response.text


@pytest.mark.asyncio
async def test_regular_user_cannot_create_tier(async_client, auth_headers):
    """Pricing is not user-editable."""
    response = await async_client.post(
        f"{API}/admin/tiers",
        headers=auth_headers,
        json={
            "name": unique_name("Rogue"),
            "price_usd": 0.01,
            "included_credits": 999999,
            "ocr_pages_included": 999999,
        },
    )
    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_regular_user_cannot_update_config(async_client, auth_headers):
    """A user cannot change how USD converts into credits."""
    response = await async_client.put(
        f"{API}/admin/config",
        headers=auth_headers,
        json={"usd_to_credits_rate": 999999.0},
    )
    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_regular_user_cannot_create_rate(async_client, auth_headers):
    """A user cannot set their own billing rate."""
    response = await async_client.post(
        f"{API}/admin-rates",
        headers=auth_headers,
        json={
            "model_type": "classification",
            "model_name": unique_name("rogue"),
            "credits_per_token": 0.0,
        },
    )
    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_regular_user_cannot_delete_rate(async_client, auth_headers, admin_headers):
    """A user cannot remove a rate, and the rate survives the attempt."""
    rate = await create_rate(async_client, admin_headers)

    response = await async_client.delete(
        f"{API}/admin-rates/{rate['id']}", headers=auth_headers
    )
    assert response.status_code == 403, response.text

    listing = await async_client.get(f"{API}/admin-rates", headers=admin_headers)
    assert rate["id"] in {item["id"] for item in listing.json()["data"]}


@pytest.mark.asyncio
async def test_forbidden_config_update_changes_nothing(
    async_client, auth_headers, admin_headers
):
    """A rejected admin write leaves the stored value alone."""
    await async_client.put(
        f"{API}/admin/config",
        headers=admin_headers,
        json={"usd_to_credits_rate": 150.0},
    )

    forbidden = await async_client.put(
        f"{API}/admin/config",
        headers=auth_headers,
        json={"usd_to_credits_rate": 999999.0},
    )
    assert forbidden.status_code == 403, forbidden.text

    current = await async_client.get(f"{API}/admin/config", headers=admin_headers)
    assert current.json()["data"]["usd_to_credits_rate"] == pytest.approx(150.0)
