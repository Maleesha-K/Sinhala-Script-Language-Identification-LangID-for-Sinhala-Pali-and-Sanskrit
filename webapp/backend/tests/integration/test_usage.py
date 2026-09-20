"""Integration tests for the usage endpoint.

GET /usage/breakdown merges two sources into a single activity feed:
classification jobs and uploaded documents (OCR). OCR cost is not stored on
the document, so it is summed from usage_records; classification cost is read
from the job row itself. Rows are seeded directly, since no worker runs.
"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.config import settings

API = settings.API_V1_STR


async def seed_job(
    user_id: str,
    *,
    text: str = "ශ්‍රී ලංකාව",
    status=None,
    credits: float = 1.5,
    created_at: datetime | None = None,
) -> str:
    """Insert a classification job and return its id."""
    from app.db.models.classification_job import ClassificationJob, JobStatus
    from app.db.session import async_session_maker

    async with async_session_maker() as session:
        job = ClassificationJob(
            user_id=uuid.UUID(user_id),
            input_text=text,
            model_name="sklearn_langid",
            segmentation_strategy="sentence",
            status=status or JobStatus.COMPLETED,
            credits_charged=credits,
        )
        if created_at:
            job.created_at = created_at
        session.add(job)
        await session.commit()
        return str(job.id)


async def seed_document(
    user_id: str,
    *,
    filename: str = "scan.pdf",
    ocr_credits: float | None = None,
    created_at: datetime | None = None,
) -> str:
    """Insert a document, optionally with an OCR usage record, and return its id."""
    from app.db.models.document import Document, UploadStatus
    from app.db.models.usage_record import RecordType, UsageRecord
    from app.db.session import async_session_maker

    async with async_session_maker() as session:
        document = Document(
            user_id=uuid.UUID(user_id),
            filename=filename,
            size_bytes=1024,
            mime_type="application/pdf",
            minio_key=f"user_{user_id}/{uuid.uuid4()}_{filename}",
            upload_status=UploadStatus.READY,
        )
        if created_at:
            document.created_at = created_at
        session.add(document)
        await session.flush()

        if ocr_credits is not None:
            session.add(
                UsageRecord(
                    user_id=uuid.UUID(user_id),
                    record_type=RecordType.OCR,
                    model_name="tesseract",
                    quantity=3,
                    credits_charged=ocr_credits,
                    job_id=document.id,
                )
            )

        await session.commit()
        return str(document.id)


def find(activities: list[dict], activity_id: str) -> dict:
    """Pick one activity out of the feed by id."""
    return next(item for item in activities if item["id"] == activity_id)


# --- shape -----------------------------------------------------------------

@pytest.mark.asyncio
async def test_breakdown_is_empty_for_new_user(async_client, auth_headers):
    """A user who has done nothing gets a balance and no activity."""
    response = await async_client.get(f"{API}/usage/breakdown", headers=auth_headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "success"

    data = body["data"]
    assert data["activities"] == []
    assert float(data["credits_balance"]) > 0  # free tier credits


@pytest.mark.asyncio
async def test_breakdown_reports_current_balance(async_client, auth_headers, test_user):
    """The balance mirrors the user's current credit total."""
    from sqlalchemy import select

    from app.db.models.user import User
    from app.db.session import async_session_maker

    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.id == uuid.UUID(test_user["user"]["id"]))
        )
        user = result.scalar_one()
        user.credits_balance = 42.5
        await session.commit()

    response = await async_client.get(f"{API}/usage/breakdown", headers=auth_headers)

    assert response.status_code == 200, response.text
    assert float(response.json()["data"]["credits_balance"]) == pytest.approx(42.5)


# --- classification activities ---------------------------------------------

@pytest.mark.asyncio
async def test_breakdown_includes_classification_job(
    async_client, auth_headers, test_user
):
    """A classification job appears as an activity with its charged cost."""
    job_id = await seed_job(test_user["user"]["id"], credits=2.25)

    response = await async_client.get(f"{API}/usage/breakdown", headers=auth_headers)

    assert response.status_code == 200, response.text
    activity = find(response.json()["data"]["activities"], job_id)
    assert activity["activity_type"] == "classification"
    assert activity["status"] == "completed"
    assert activity["cost"] == pytest.approx(2.25)
    assert activity["name"].startswith("LangID: ")


@pytest.mark.asyncio
async def test_classification_name_holds_a_text_snippet(
    async_client, auth_headers, test_user
):
    """Short input is shown in full, so the row is recognisable."""
    job_id = await seed_job(test_user["user"]["id"], text="කෙටි පෙළ")

    response = await async_client.get(f"{API}/usage/breakdown", headers=auth_headers)

    activity = find(response.json()["data"]["activities"], job_id)
    assert activity["name"] == "LangID: කෙටි පෙළ"


@pytest.mark.asyncio
async def test_long_classification_text_is_truncated(
    async_client, auth_headers, test_user
):
    """Long input is cut to 40 characters and ellipsised."""
    long_text = "අ" * 100
    job_id = await seed_job(test_user["user"]["id"], text=long_text)

    response = await async_client.get(f"{API}/usage/breakdown", headers=auth_headers)

    activity = find(response.json()["data"]["activities"], job_id)
    assert activity["name"] == f"LangID: {'අ' * 40}..."


@pytest.mark.asyncio
async def test_breakdown_includes_queued_jobs(async_client, auth_headers, test_user):
    """Work still in flight is listed, not just finished work."""
    from app.db.models.classification_job import JobStatus

    job_id = await seed_job(
        test_user["user"]["id"], status=JobStatus.QUEUED, credits=0
    )

    response = await async_client.get(f"{API}/usage/breakdown", headers=auth_headers)

    activity = find(response.json()["data"]["activities"], job_id)
    assert activity["status"] == "queued"
    assert activity["cost"] == pytest.approx(0)


# --- OCR activities --------------------------------------------------------

@pytest.mark.asyncio
async def test_breakdown_includes_document(async_client, auth_headers, test_user):
    """An uploaded document appears as an OCR activity."""
    document_id = await seed_document(
        test_user["user"]["id"], filename="manuscript.pdf", ocr_credits=4.0
    )

    response = await async_client.get(f"{API}/usage/breakdown", headers=auth_headers)

    activity = find(response.json()["data"]["activities"], document_id)
    assert activity["activity_type"] == "ocr"
    assert activity["name"] == "OCR: manuscript.pdf"
    assert activity["status"] == "ready"
    assert activity["cost"] == pytest.approx(4.0)


@pytest.mark.asyncio
async def test_document_without_usage_record_costs_zero(
    async_client, auth_headers, test_user
):
    """A document with no usage record is reported at zero cost."""
    document_id = await seed_document(test_user["user"]["id"], ocr_credits=None)

    response = await async_client.get(f"{API}/usage/breakdown", headers=auth_headers)

    activity = find(response.json()["data"]["activities"], document_id)
    assert activity["cost"] == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_ocr_cost_sums_multiple_records(async_client, auth_headers, test_user):
    """Several OCR charges against one document are summed.

    A multi-page document can be billed page by page, so the endpoint groups
    usage_records by job_id rather than taking a single row.
    """
    from app.db.models.usage_record import RecordType, UsageRecord
    from app.db.session import async_session_maker

    document_id = await seed_document(test_user["user"]["id"], ocr_credits=1.0)

    async with async_session_maker() as session:
        session.add(
            UsageRecord(
                user_id=uuid.UUID(test_user["user"]["id"]),
                record_type=RecordType.OCR,
                model_name="tesseract",
                quantity=2,
                credits_charged=2.5,
                job_id=uuid.UUID(document_id),
            )
        )
        await session.commit()

    response = await async_client.get(f"{API}/usage/breakdown", headers=auth_headers)

    activity = find(response.json()["data"]["activities"], document_id)
    assert activity["cost"] == pytest.approx(3.5)


@pytest.mark.asyncio
async def test_non_ocr_records_are_not_counted_as_ocr_cost(
    async_client, auth_headers, test_user
):
    """Only OCR records contribute to a document's cost.

    The query filters on record_type, so a storage charge sharing the same
    job_id must not inflate the OCR figure.
    """
    from app.db.models.usage_record import RecordType, UsageRecord
    from app.db.session import async_session_maker

    document_id = await seed_document(test_user["user"]["id"], ocr_credits=1.0)

    async with async_session_maker() as session:
        session.add(
            UsageRecord(
                user_id=uuid.UUID(test_user["user"]["id"]),
                record_type=RecordType.STORAGE,
                model_name=None,
                quantity=1,
                credits_charged=99.0,
                job_id=uuid.UUID(document_id),
            )
        )
        await session.commit()

    response = await async_client.get(f"{API}/usage/breakdown", headers=auth_headers)

    activity = find(response.json()["data"]["activities"], document_id)
    assert activity["cost"] == pytest.approx(1.0)


# --- merging and ordering --------------------------------------------------

@pytest.mark.asyncio
async def test_breakdown_merges_both_activity_types(
    async_client, auth_headers, test_user
):
    """Jobs and documents appear together in one feed."""
    job_id = await seed_job(test_user["user"]["id"])
    document_id = await seed_document(test_user["user"]["id"])

    response = await async_client.get(f"{API}/usage/breakdown", headers=auth_headers)

    activities = response.json()["data"]["activities"]
    ids = {item["id"] for item in activities}
    assert {job_id, document_id} <= ids

    types = {find(activities, job_id)["activity_type"],
             find(activities, document_id)["activity_type"]}
    assert types == {"classification", "ocr"}


@pytest.mark.asyncio
async def test_activities_are_sorted_newest_first(
    async_client, auth_headers, test_user
):
    """The merged feed is ordered by creation time, descending.

    Jobs and documents are fetched in separate queries, so the interleaving is
    done in Python; these rows are seeded with deliberately alternating
    timestamps to prove the combined list is sorted rather than concatenated.
    """
    now = datetime.now(timezone.utc)
    user_id = test_user["user"]["id"]

    oldest_job = await seed_job(user_id, created_at=now - timedelta(hours=4))
    older_document = await seed_document(user_id, created_at=now - timedelta(hours=3))
    newer_job = await seed_job(user_id, created_at=now - timedelta(hours=2))
    newest_document = await seed_document(user_id, created_at=now - timedelta(hours=1))

    response = await async_client.get(f"{API}/usage/breakdown", headers=auth_headers)

    assert response.status_code == 200, response.text
    ordered = [item["id"] for item in response.json()["data"]["activities"]]
    assert ordered == [newest_document, newer_job, older_document, oldest_job]


# --- scoping ---------------------------------------------------------------

@pytest.mark.asyncio
async def test_breakdown_excludes_other_users_activity(
    async_client, auth_headers, test_user, second_user
):
    """The feed is scoped to the caller."""
    mine = await seed_job(test_user["user"]["id"])
    theirs = await seed_job(second_user["user"]["id"])
    their_document = await seed_document(second_user["user"]["id"])

    response = await async_client.get(f"{API}/usage/breakdown", headers=auth_headers)

    ids = {item["id"] for item in response.json()["data"]["activities"]}
    assert mine in ids
    assert theirs not in ids
    assert their_document not in ids


@pytest.mark.asyncio
async def test_another_users_ocr_cost_does_not_leak(
    async_client, auth_headers, test_user, second_user
):
    """One user's usage records never contribute to another's costs."""
    from app.db.models.usage_record import RecordType, UsageRecord
    from app.db.session import async_session_maker

    document_id = await seed_document(test_user["user"]["id"], ocr_credits=1.0)

    # A record owned by the other user, but pointing at this document.
    async with async_session_maker() as session:
        session.add(
            UsageRecord(
                user_id=uuid.UUID(second_user["user"]["id"]),
                record_type=RecordType.OCR,
                model_name="tesseract",
                quantity=1,
                credits_charged=50.0,
                job_id=uuid.UUID(document_id),
            )
        )
        await session.commit()

    response = await async_client.get(
        f"{API}/usage/breakdown", headers=second_user["headers"]
    )

    ids = {item["id"] for item in response.json()["data"]["activities"]}
    assert document_id not in ids


@pytest.mark.asyncio
async def test_breakdown_without_token_returns_401(async_client):
    """The breakdown requires authentication."""
    response = await async_client.get(f"{API}/usage/breakdown")
    assert response.status_code == 401, response.text


@pytest.mark.asyncio
async def test_breakdown_with_invalid_token_returns_401(async_client):
    """A malformed bearer value is rejected."""
    response = await async_client.get(
        f"{API}/usage/breakdown", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert response.status_code == 401, response.text
