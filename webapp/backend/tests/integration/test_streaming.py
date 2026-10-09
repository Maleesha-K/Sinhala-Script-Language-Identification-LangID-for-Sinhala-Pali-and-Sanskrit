"""Integration tests for streamed OCR and classification.

The workers run for real against the test database and Redis, with storage,
the OCR engine and the classifier patched. Events are read from Redis pub/sub
the way the WebSockets relay them (see app/utils/events.py).
"""
import json
import uuid
from decimal import Decimal
from io import BytesIO

import fitz
import pytest
from sqlalchemy import func, select

from app.config import settings

API = settings.API_V1_STR
TESSERACT = "app.ocr.tesseract_engine.TesseractEngine.extract_text"


def make_pdf(pages: int) -> bytes:
    doc = fitz.open()
    for i in range(pages):
        doc.new_page().insert_text((72, 72), f"page {i + 1}")
    return doc.tobytes()


class Listener:
    """Collects the events published on a channel."""

    def __init__(self, channel: str):
        from app.utils.redis_client import sync_redis_client
        self.pubsub = sync_redis_client.pubsub()
        self.pubsub.subscribe(channel)

    def events(self) -> list[dict]:
        out = []
        while (message := self.pubsub.get_message(timeout=0.2)) is not None:
            if message["type"] == "message":
                out.append(json.loads(message["data"]))
        self.pubsub.close()
        return out


class FakeClassifier:
    def __init__(self, fail: bool = False):
        self.fail = fail
        self.calls = []

    def predict_batch(self, texts):
        if self.fail:
            raise RuntimeError("model exploded")
        self.calls.append(len(texts))
        return [
            {"language": "sinhala", "confidence": 0.9,
             "probabilities": {"sinhala": 0.9, "pali": 0.05, "sanskrit": 0.05}}
            for _ in texts
        ]


@pytest.fixture
def mock_storage(mocker):
    storage = mocker.patch("app.api.v1.documents.storage_service")
    storage.upload_document.return_value = True
    return storage


@pytest.fixture
def mock_upload_tasks(mocker):
    mocker.patch("app.api.v1.documents.process_document_ocr")
    mocker.patch("app.api.v1.documents.process_document_ocr_surya")


@pytest.fixture
def mock_page_job_queue(mocker):
    """The OCR worker queues page jobs; record them instead of running them."""
    return mocker.patch("app.workers.tasks.classification_tasks.process_classification_job.delay")


async def upload(client, headers, pages: int = 3, **form) -> dict:
    response = await client.post(
        f"{API}/documents/upload",
        headers=headers,
        files={"file": ("doc.pdf", BytesIO(make_pdf(pages)), "application/pdf")},
        data=form,
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


async def run_ocr(mocker, doc: dict, pages: int, extract_side_effect) -> tuple[dict, list[dict]]:
    from app.services.storage_service import storage_service
    from app.utils.events import document_channel
    from app.workers.tasks.ocr_tasks import _process_document_async

    mocker.patch.object(storage_service, "get_document_bytes", return_value=make_pdf(pages))
    mocker.patch(TESSERACT, side_effect=extract_side_effect)
    listener = Listener(document_channel(doc["id"]))
    result = await _process_document_async(doc["id"])
    return result, listener.events()


async def net_usage(ref_id) -> Decimal:
    from app.db.models.usage_record import UsageRecord
    from app.db.session import async_session_maker

    async with async_session_maker() as session:
        total = await session.execute(
            select(func.coalesce(func.sum(UsageRecord.credits_charged), 0))
            .where(UsageRecord.job_id == uuid.UUID(str(ref_id)))
        )
        return Decimal(total.scalar_one())


async def page_jobs(doc_id: str):
    from app.db.models.classification_job import ClassificationJob
    from app.db.session import async_session_maker

    async with async_session_maker() as session:
        result = await session.execute(
            select(ClassificationJob)
            .where(ClassificationJob.document_id == uuid.UUID(doc_id))
            .order_by(ClassificationJob.page_number)
        )
        return result.scalars().all()


# --- OCR worker --------------------------------------------------------------

@pytest.mark.asyncio
async def test_ocr_publishes_each_page_and_queues_its_classification(
    async_client, auth_headers, mock_storage, mock_upload_tasks, mock_page_job_queue, mocker
):
    doc = await upload(async_client, auth_headers, pages=3, lid_model="sklearn_langid")
    assert doc["lid_model"] == "sklearn_langid"

    result, events = await run_ocr(mocker, doc, 3, ["text one", "  ", "text three"])

    assert result["status"] == "success", result
    page_events = [(e["page"]["page_number"], e["page"]["status"]) for e in events if e["type"] == "page"]
    # All pages are listed first, then each is processed and published in turn.
    assert page_events == [
        (1, "pending"), (2, "pending"), (3, "pending"),
        (1, "processing"), (1, "completed"),
        (2, "processing"), (2, "completed"),
        (3, "processing"), (3, "completed"),
    ]
    assert events[-1] == {"type": "document", "status": "ready", "message": ""}

    # Pages with text get a classification job as soon as they are read; the
    # blank page does not.
    jobs = await page_jobs(doc["id"])
    assert [(j.page_number, j.input_text, j.model_name) for j in jobs] == [
        (1, "text one", "sklearn_langid"), (3, "text three", "sklearn_langid"),
    ]
    # OCR'd lines wrap mid-sentence, so page jobs split sentences across them.
    assert {j.segmentation_strategy for j in jobs} == {"document"}
    assert [c.args[0] for c in mock_page_job_queue.call_args_list] == [str(j.id) for j in jobs]
    queued = [(e["page_number"], e["job"]["status"]) for e in events if e["type"] == "page_job"]
    assert queued == [(1, "queued"), (3, "queued")]
    # The page-1 job is announced before page 2 is read.
    order = [
        (e["type"], e["page_number"]) if e["type"] == "page_job"
        else (e["type"], e.get("page", {}).get("page_number"), e.get("page", {}).get("status"))
        for e in events
    ]
    assert order.index(("page_job", 1)) < order.index(("page", 2, "processing"))


@pytest.mark.asyncio
async def test_ocr_without_a_model_queues_no_classification(
    async_client, auth_headers, mock_storage, mock_upload_tasks, mock_page_job_queue, mocker
):
    doc = await upload(async_client, auth_headers, pages=2)
    assert doc["lid_model"] is None

    result, _ = await run_ocr(mocker, doc, 2, ["a", "b"])

    assert result["status"] == "success"
    assert await page_jobs(doc["id"]) == []
    mock_page_job_queue.assert_not_called()


@pytest.mark.asyncio
async def test_ocr_page_failure_keeps_other_pages_and_refunds_that_page(
    async_client, auth_headers, mock_storage, mock_upload_tasks, mock_page_job_queue, mocker
):
    doc = await upload(async_client, auth_headers, pages=3)
    charge_per_page = Decimal("0.1")

    result, events = await run_ocr(mocker, doc, 3, ["one", RuntimeError("bad page"), "three"])

    assert result == {"status": "success", "document_id": doc["id"], "failed_pages": 1}
    final = {e["page"]["page_number"]: e["page"]["status"] for e in events if e["type"] == "page"}
    assert final == {1: "completed", 2: "failed", 3: "completed"}
    assert events[-1]["status"] == "ready"
    assert await net_usage(doc["id"]) == 2 * charge_per_page


@pytest.mark.asyncio
async def test_ocr_failing_on_every_page_fails_the_document_and_refunds_it(
    async_client, auth_headers, mock_storage, mock_upload_tasks, mock_page_job_queue, mocker
):
    doc = await upload(async_client, auth_headers, pages=2)

    result, events = await run_ocr(mocker, doc, 2, RuntimeError("engine missing"))

    assert result["status"] == "error"
    assert events[-1] == {"type": "document", "status": "failed", "message": "OCR failed on every page"}
    assert await net_usage(doc["id"]) == 0


# --- classification worker ---------------------------------------------------

async def make_job(client, headers, mocker, text: str) -> dict:
    mocker.patch("app.api.v1.classification.process_classification_job")
    response = await client.post(
        f"{API}/classification/jobs", headers=headers,
        json={"input_text": text, "model_name": "sklearn_langid"},
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


async def run_job(mocker, job_id: str, classifier, extra_channels=()) -> tuple[list[dict], list[list[dict]]]:
    from app.utils.events import job_channel
    from app.workers.tasks.classification_tasks import _process_classification_job_async

    mocker.patch("app.workers.tasks.classification_tasks.get_classifier", return_value=classifier)
    listener = Listener(job_channel(job_id))
    extra = [Listener(c) for c in extra_channels]
    await _process_classification_job_async(job_id)
    return listener.events(), [l.events() for l in extra]


@pytest.mark.asyncio
async def test_classification_publishes_segments_in_batches(async_client, auth_headers, mocker):
    from app.workers.tasks.classification_tasks import BATCH_SIZE

    text = " ".join(f"වාක්‍යය {i}." for i in range(BATCH_SIZE + 4))
    job = await make_job(async_client, auth_headers, mocker, text)
    classifier = FakeClassifier()

    events, _ = await run_job(mocker, job["id"], classifier)

    assert classifier.calls == [BATCH_SIZE, 4]
    batches = [e for e in events if e["type"] == "segments"]
    assert [len(b["segments"]) for b in batches] == [BATCH_SIZE, 4]
    assert [(b["done"], b["total"]) for b in batches] == [(BATCH_SIZE, BATCH_SIZE + 4), (BATCH_SIZE + 4, BATCH_SIZE + 4)]
    assert [s["segment_index"] for b in batches for s in b["segments"]] == list(range(BATCH_SIZE + 4))
    assert all(s["id"] for b in batches for s in b["segments"])  # needed for corrections
    assert events[-1]["type"] == "status" and events[-1]["status"] == "completed"

    response = await async_client.get(f"{API}/classification/jobs/{job['id']}", headers=auth_headers)
    data = response.json()["data"]
    assert len(data["segments"]) == data["done"] == data["total"] == BATCH_SIZE + 4
    # Charged once, before any result was published.
    assert await net_usage(job["id"]) > 0


@pytest.mark.asyncio
async def test_classification_failure_refunds_and_records_the_reason(async_client, auth_headers, mocker):
    job = await make_job(async_client, auth_headers, mocker, "එක. දෙක.")

    events, _ = await run_job(mocker, job["id"], FakeClassifier(fail=True))

    assert events[-1]["status"] == "failed"
    assert events[-1]["message"] == "model exploded"
    assert await net_usage(job["id"]) == 0
    data = (await async_client.get(f"{API}/classification/jobs/{job['id']}", headers=auth_headers)).json()["data"]
    assert data["status"] == "failed"
    assert data["error_message"] == "model exploded"


@pytest.mark.asyncio
async def test_page_job_events_are_mirrored_to_the_document(
    async_client, auth_headers, mock_storage, mock_upload_tasks, mock_page_job_queue, mocker
):
    from app.utils.events import document_channel

    doc = await upload(async_client, auth_headers, pages=1, lid_model="sklearn_langid")
    await run_ocr(mocker, doc, 1, ["පළමු වාක්‍යය. දෙවන වාක්‍යය."])
    (job,) = await page_jobs(doc["id"])

    _, (doc_events,) = await run_job(mocker, str(job.id), FakeClassifier(), [document_channel(doc["id"])])

    segments = [e for e in doc_events if e["type"] == "page_segments"]
    assert [(e["page_number"], e["job_id"], len(e["segments"])) for e in segments] == [(1, str(job.id), 2)]
    statuses = [e["job"]["status"] for e in doc_events if e["type"] == "page_job"]
    assert statuses[0] == "processing" and statuses[-1] == "completed"

    # The pages endpoint returns the page with its classification.
    pages = (await async_client.get(f"{API}/documents/{doc['id']}/pages", headers=auth_headers)).json()["data"]
    assert pages[0]["status"] == "completed"
    assert pages[0]["classification"]["status"] == "completed"
    assert [s["text"].strip() for s in pages[0]["classification"]["segments"]] == ["පළමු වාක්‍යය.", "දෙවන වාක්‍යය."]
    assert pages[0]["classification"]["done"] == pages[0]["classification"]["total"] == 2

    # Per-page jobs belong to the document, not the user's job list.
    jobs = (await async_client.get(f"{API}/classification/jobs", headers=auth_headers)).json()["data"]
    assert str(job.id) not in {j["id"] for j in jobs}

    # Deleting the document keeps the billed job, detached.
    response = await async_client.delete(f"{API}/documents/{doc['id']}", headers=auth_headers)
    assert response.status_code == 200, response.text
    from app.db.models.classification_job import ClassificationJob
    from app.db.session import async_session_maker
    async with async_session_maker() as session:
        detached = await session.get(ClassificationJob, job.id)
    assert detached is not None and detached.document_id is None


# --- upload validation -------------------------------------------------------

@pytest.mark.asyncio
async def test_upload_rejects_an_unknown_model(async_client, auth_headers, mock_storage, mock_upload_tasks):
    response = await async_client.post(
        f"{API}/documents/upload",
        headers=auth_headers,
        files={"file": ("doc.pdf", BytesIO(make_pdf(1)), "application/pdf")},
        data={"lid_model": "no_such_model"},
    )
    assert response.status_code == 400
    assert "no_such_model" in response.json()["message"]
    mock_storage.upload_document.assert_not_called()
