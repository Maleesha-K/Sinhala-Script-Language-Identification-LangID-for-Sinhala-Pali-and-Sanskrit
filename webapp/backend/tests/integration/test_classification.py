"""Integration tests for the classification endpoints.

Celery is mocked throughout: `classification.py` imports
`process_classification_job` into its own namespace, so the patch target is
`app.api.v1.classification.process_classification_job`. No worker runs in the
test suite, so a submitted job stays QUEUED; the completed-job path is set up
by writing the rows the worker would have written.
"""
import uuid
from datetime import datetime, timezone

import pytest

from app.config import settings

API = settings.API_V1_STR

SINHALA_TEXT = "ශ්‍රී ලංකාව ලස්සන රටකි"


@pytest.fixture
def mock_classification_task(mocker):
    """Stub the Celery task so no broker or worker is required."""
    return mocker.patch("app.api.v1.classification.process_classification_job")


async def create_job(client, headers, **overrides) -> dict:
    """Submit a classification job and return the created record."""
    payload = {"input_text": SINHALA_TEXT}
    payload.update(overrides)

    response = await client.post(
        f"{API}/classification/jobs", headers=headers, json=payload
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


async def complete_job(job_id: str, *, segments: list[dict] | None = None) -> None:
    """Mark a job COMPLETED and attach segments, as the worker would."""
    from sqlalchemy import select

    from app.db.models.classification_job import ClassificationJob, JobStatus
    from app.db.models.classified_segment import ClassifiedSegment
    from app.db.session import async_session_maker

    async with async_session_maker() as session:
        result = await session.execute(
            select(ClassificationJob).where(ClassificationJob.id == uuid.UUID(job_id))
        )
        job = result.scalar_one()
        job.status = JobStatus.COMPLETED
        job.total_tokens = 12
        job.completed_at = datetime.now(timezone.utc)

        for segment in segments or []:
            session.add(ClassifiedSegment(job_id=job.id, **segment))

        await session.commit()


def segment(index: int, text: str, language: str = "sinhala") -> dict:
    """Build a ClassifiedSegment row of the shape the worker produces."""
    return {
        "segment_index": index,
        "text": text,
        "predicted_language": language,
        "confidence": 0.95,
        "probabilities": {"sinhala": 0.95, "pali": 0.03, "sanskrit": 0.02},
        "start_char_offset": index * 10,
        "end_char_offset": index * 10 + len(text),
    }


# --- create job ------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_job_returns_201_queued(
    async_client, auth_headers, mock_classification_task
):
    """POST /classification/jobs accepts text and returns a queued job."""
    response = await async_client.post(
        f"{API}/classification/jobs",
        headers=auth_headers,
        json={"input_text": SINHALA_TEXT},
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "success"

    data = body["data"]
    assert data["status"] == "queued"
    assert data["segmentation_strategy"] == "sentence"  # the default
    assert data["total_tokens"] == 0  # the worker fills this in
    assert data["completed_at"] is None
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_job_queues_celery_task(
    async_client, auth_headers, mock_classification_task
):
    """The worker is handed the new job's id."""
    job = await create_job(async_client, auth_headers)

    mock_classification_task.delay.assert_called_once_with(job["id"])


@pytest.mark.asyncio
async def test_create_job_persists_input_and_model(
    async_client, auth_headers, mock_classification_task
):
    """The submitted text and the default model name are stored on the job."""
    from sqlalchemy import select

    from app.db.models.classification_job import ClassificationJob
    from app.db.session import async_session_maker

    job = await create_job(async_client, auth_headers)

    async with async_session_maker() as session:
        result = await session.execute(
            select(ClassificationJob).where(ClassificationJob.id == uuid.UUID(job["id"]))
        )
        stored = result.scalar_one()

    assert stored.input_text == SINHALA_TEXT
    assert stored.model_name == "sklearn_langid"


@pytest.mark.asyncio
async def test_create_job_is_owned_by_the_caller(
    async_client, auth_headers, test_user, mock_classification_task
):
    """The job belongs to the authenticated user."""
    from sqlalchemy import select

    from app.db.models.classification_job import ClassificationJob
    from app.db.session import async_session_maker

    job = await create_job(async_client, auth_headers)

    async with async_session_maker() as session:
        result = await session.execute(
            select(ClassificationJob).where(ClassificationJob.id == uuid.UUID(job["id"]))
        )
        stored = result.scalar_one()

    assert str(stored.user_id) == test_user["user"]["id"]


@pytest.mark.parametrize("strategy", ["sentence", "paragraph", "full_text", "auto"])
@pytest.mark.asyncio
async def test_create_job_accepts_each_valid_strategy(
    async_client, auth_headers, mock_classification_task, strategy
):
    """Every strategy allowed by the request pattern is accepted."""
    response = await async_client.post(
        f"{API}/classification/jobs",
        headers=auth_headers,
        json={"input_text": SINHALA_TEXT, "segmentation_strategy": strategy},
    )

    assert response.status_code == 201, response.text
    assert response.json()["data"]["segmentation_strategy"] == strategy


@pytest.mark.asyncio
async def test_create_job_with_empty_text_returns_422(
    async_client, auth_headers, mock_classification_task
):
    """input_text has min_length=1, so an empty string is rejected."""
    response = await async_client.post(
        f"{API}/classification/jobs",
        headers=auth_headers,
        json={"input_text": ""},
    )

    assert response.status_code == 422, response.text
    mock_classification_task.delay.assert_not_called()


@pytest.mark.asyncio
async def test_create_job_with_missing_text_returns_422(
    async_client, auth_headers, mock_classification_task
):
    """input_text is required."""
    response = await async_client.post(
        f"{API}/classification/jobs", headers=auth_headers, json={}
    )
    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_create_job_with_bad_strategy_returns_422(
    async_client, auth_headers, mock_classification_task
):
    """segmentation_strategy is constrained by a regex pattern."""
    response = await async_client.post(
        f"{API}/classification/jobs",
        headers=auth_headers,
        json={"input_text": SINHALA_TEXT, "segmentation_strategy": "by_vibes"},
    )

    assert response.status_code == 422, response.text
    mock_classification_task.delay.assert_not_called()


@pytest.mark.asyncio
async def test_create_job_strategy_is_case_sensitive(
    async_client, auth_headers, mock_classification_task
):
    """The pattern is anchored and lowercase, so SENTENCE is not accepted."""
    response = await async_client.post(
        f"{API}/classification/jobs",
        headers=auth_headers,
        json={"input_text": SINHALA_TEXT, "segmentation_strategy": "SENTENCE"},
    )
    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_create_job_rejects_strategy_substring(
    async_client, auth_headers, mock_classification_task
):
    """A value merely containing a valid strategy is rejected.

    Guards the ^...$ anchors on the pattern; without them "xsentencex" would
    slip through and reach the worker as an unknown strategy.
    """
    response = await async_client.post(
        f"{API}/classification/jobs",
        headers=auth_headers,
        json={"input_text": SINHALA_TEXT, "segmentation_strategy": "xsentencex"},
    )
    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_create_job_without_token_returns_401(
    async_client, mock_classification_task
):
    """Submitting a job requires authentication."""
    response = await async_client.post(
        f"{API}/classification/jobs", json={"input_text": SINHALA_TEXT}
    )
    assert response.status_code == 401, response.text


# --- get job ---------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_job_while_queued(
    async_client, auth_headers, mock_classification_task
):
    """A queued job reports its status and carries no segments yet."""
    job = await create_job(async_client, auth_headers)

    response = await async_client.get(
        f"{API}/classification/jobs/{job['id']}", headers=auth_headers
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["id"] == job["id"]
    assert data["status"] == "queued"
    assert data["completed_at"] is None
    assert data["segments"] is None


@pytest.mark.asyncio
async def test_get_completed_job_returns_segments(
    async_client, auth_headers, mock_classification_task
):
    """A completed job returns its classified segments."""
    job = await create_job(async_client, auth_headers)
    await complete_job(
        job["id"],
        segments=[segment(0, "ශ්‍රී ලංකාව"), segment(1, "ලස්සන රටකි")],
    )

    response = await async_client.get(
        f"{API}/classification/jobs/{job['id']}", headers=auth_headers
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["status"] == "completed"
    assert data["completed_at"] is not None
    assert data["total_tokens"] == 12

    segments = data["segments"]
    assert len(segments) == 2
    assert segments[0]["text"] == "ශ්‍රී ලංකාව"
    assert segments[0]["predicted_language"] == "sinhala"
    assert segments[0]["confidence"] == pytest.approx(0.95)
    assert segments[0]["probabilities"]["sinhala"] == pytest.approx(0.95)


@pytest.mark.asyncio
async def test_get_completed_job_orders_segments(
    async_client, auth_headers, mock_classification_task
):
    """Segments come back ordered by segment_index.

    They are inserted out of order to prove the endpoint sorts rather than
    relying on insertion order.
    """
    job = await create_job(async_client, auth_headers)
    await complete_job(
        job["id"],
        segments=[segment(2, "third"), segment(0, "first"), segment(1, "second")],
    )

    response = await async_client.get(
        f"{API}/classification/jobs/{job['id']}", headers=auth_headers
    )

    assert response.status_code == 200, response.text
    segments = response.json()["data"]["segments"]
    assert [s["segment_index"] for s in segments] == [0, 1, 2]
    assert [s["text"] for s in segments] == ["first", "second", "third"]


@pytest.mark.asyncio
async def test_get_job_omits_segments_until_completed(
    async_client, auth_headers, mock_classification_task
):
    """Segments are withheld while the job is still processing.

    Rows are attached to a job left in PROCESSING; the endpoint only reads
    them once the status is COMPLETED, so partial results are never served.
    """
    from sqlalchemy import select

    from app.db.models.classification_job import ClassificationJob, JobStatus
    from app.db.models.classified_segment import ClassifiedSegment
    from app.db.session import async_session_maker

    job = await create_job(async_client, auth_headers)

    async with async_session_maker() as session:
        result = await session.execute(
            select(ClassificationJob).where(ClassificationJob.id == uuid.UUID(job["id"]))
        )
        stored = result.scalar_one()
        stored.status = JobStatus.PROCESSING
        session.add(ClassifiedSegment(job_id=stored.id, **segment(0, "partial")))
        await session.commit()

    response = await async_client.get(
        f"{API}/classification/jobs/{job['id']}", headers=auth_headers
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["status"] == "processing"
    assert data["segments"] is None


@pytest.mark.asyncio
async def test_get_missing_job_returns_404(async_client, auth_headers):
    """An unknown job id is a 404."""
    response = await async_client.get(
        f"{API}/classification/jobs/{uuid.uuid4()}", headers=auth_headers
    )
    assert response.status_code == 404, response.text


@pytest.mark.asyncio
async def test_get_another_users_job_returns_404(
    async_client, auth_headers, second_user_headers, mock_classification_task
):
    """Another user's job is indistinguishable from a missing one.

    The query filters on user_id, so submitted text and its classification
    results are not readable across accounts.
    """
    theirs = await create_job(async_client, second_user_headers)

    response = await async_client.get(
        f"{API}/classification/jobs/{theirs['id']}", headers=auth_headers
    )
    assert response.status_code == 404, response.text


@pytest.mark.asyncio
async def test_another_users_completed_segments_are_not_readable(
    async_client, auth_headers, second_user_headers, mock_classification_task
):
    """Ownership still holds once results exist."""
    theirs = await create_job(async_client, second_user_headers)
    await complete_job(theirs["id"], segments=[segment(0, "their private text")])

    response = await async_client.get(
        f"{API}/classification/jobs/{theirs['id']}", headers=auth_headers
    )
    assert response.status_code == 404, response.text

    # The owner can still read it.
    owner_view = await async_client.get(
        f"{API}/classification/jobs/{theirs['id']}", headers=second_user_headers
    )
    assert owner_view.status_code == 200, owner_view.text
    assert owner_view.json()["data"]["segments"][0]["text"] == "their private text"


@pytest.mark.asyncio
async def test_get_job_with_malformed_id_returns_422(async_client, auth_headers):
    """A non-UUID path parameter fails validation."""
    response = await async_client.get(
        f"{API}/classification/jobs/not-a-uuid", headers=auth_headers
    )
    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_get_job_without_token_returns_401(async_client):
    """Reading a job requires authentication."""
    response = await async_client.get(f"{API}/classification/jobs/{uuid.uuid4()}")
    assert response.status_code == 401, response.text
