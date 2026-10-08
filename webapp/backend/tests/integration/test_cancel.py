"""Cancelling classification jobs and document processing.

Workers run for real against the test database and Redis. A cancel arriving
mid-run is simulated by patching the workers' checkpoint (`_cancel_requested`)
to report it at a chosen point.
"""
import uuid
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.config import settings

from tests.integration.test_streaming import (
    FakeClassifier, Listener, make_job, mock_page_job_queue, mock_storage, mock_upload_tasks,  # noqa: F401
    net_usage, page_jobs, run_job, run_ocr, upload,
)

API = settings.API_V1_STR


async def set_job(job_id, **values):
    from app.db.models.classification_job import ClassificationJob
    from app.db.session import async_session_maker

    async with async_session_maker() as session:
        job = await session.get(ClassificationJob, uuid.UUID(str(job_id)))
        for k, v in values.items():
            setattr(job, k, v)
        await session.commit()


async def get_job(client, headers, job_id) -> dict:
    return (await client.get(f"{API}/classification/jobs/{job_id}", headers=headers)).json()["data"]


# --- classification ----------------------------------------------------------

@pytest.mark.asyncio
async def test_cancelling_a_queued_job_stops_it_before_it_runs(async_client, auth_headers, mocker):
    job = await make_job(async_client, auth_headers, mocker, "එක. දෙක.")

    response = await async_client.post(f"{API}/classification/jobs/{job['id']}/cancel", headers=auth_headers)
    assert response.status_code == 200, response.text
    assert response.json()["data"]["status"] == "cancelled"

    # The worker picking it up later does nothing and charges nothing.
    classifier = FakeClassifier()
    events, _ = await run_job(mocker, job["id"], classifier)
    assert classifier.calls == [] and events == []
    data = await get_job(async_client, auth_headers, job["id"])
    assert data["status"] == "cancelled" and data["segments"] == []
    assert await net_usage(job["id"]) == 0


@pytest.mark.asyncio
async def test_cancelling_a_running_job_requests_a_stop(async_client, auth_headers, mocker):
    from app.db.models.classification_job import JobStatus

    job = await make_job(async_client, auth_headers, mocker, "එක. දෙක.")
    await set_job(job["id"], status=JobStatus.PROCESSING)
    listener = Listener(f"job_updates:{job['id']}")

    response = await async_client.post(f"{API}/classification/jobs/{job['id']}/cancel", headers=auth_headers)

    assert response.status_code == 200, response.text
    assert response.json()["data"] == {"id": job["id"], "status": "processing", "cancel_requested": True}
    assert listener.events()[-1] == {
        "type": "status", "status": "processing", "cancel_requested": True, "message": "Cancelling…",
    }
    assert (await get_job(async_client, auth_headers, job["id"]))["cancel_requested"] is True


@pytest.mark.asyncio
async def test_a_cancelled_job_keeps_its_segments_and_refunds_the_rest(async_client, auth_headers, mocker):
    from app.workers.tasks.classification_tasks import BATCH_SIZE

    text = " ".join(f"වාක්‍යය {i}." for i in range(BATCH_SIZE * 2 + 4))
    job = await make_job(async_client, auth_headers, mocker, text)
    # Checkpoints: before charging, before batch 1, before batch 2 (cancel).
    mocker.patch(
        "app.workers.tasks.classification_tasks._cancel_requested", side_effect=[False, False, True]
    )

    events, _ = await run_job(mocker, job["id"], FakeClassifier())

    assert events[-1]["status"] == "cancelled"
    assert events[-1]["message"] == f"Cancelled after {BATCH_SIZE} of {BATCH_SIZE * 2 + 4} segments."
    data = await get_job(async_client, auth_headers, job["id"])
    assert data["status"] == "cancelled"
    assert [s["segment_index"] for s in data["segments"]] == list(range(BATCH_SIZE))
    assert data["done"] == data["total"] == BATCH_SIZE

    # Every sentence here is 2 tokens, so the kept share is BATCH_SIZE / all.
    from app.services.credit_service import DEFAULT_CREDITS_PER_TOKEN
    total_tokens = 2 * (BATCH_SIZE * 2 + 4)
    charged = Decimal(total_tokens) * Decimal(str(DEFAULT_CREDITS_PER_TOKEN))
    kept = charged * Decimal(BATCH_SIZE) / Decimal(BATCH_SIZE * 2 + 4)
    assert abs(await net_usage(job["id"]) - kept) < Decimal("0.0002")


@pytest.mark.asyncio
async def test_cancel_rejects_finished_and_other_users_jobs(
    async_client, auth_headers, second_user_headers, mocker
):
    job = await make_job(async_client, auth_headers, mocker, "එක.")
    await run_job(mocker, job["id"], FakeClassifier())

    finished = await async_client.post(f"{API}/classification/jobs/{job['id']}/cancel", headers=auth_headers)
    assert finished.status_code == 400
    assert "completed" in finished.json()["message"]

    other = await make_job(async_client, auth_headers, mocker, "දෙක.")
    response = await async_client.post(f"{API}/classification/jobs/{other['id']}/cancel", headers=second_user_headers)
    assert response.status_code == 404


# --- documents ---------------------------------------------------------------

@pytest.mark.asyncio
async def test_cancelled_ocr_keeps_read_pages_and_refunds_the_rest(
    async_client, auth_headers, mock_storage, mock_upload_tasks, mock_page_job_queue, mocker
):
    doc = await upload(async_client, auth_headers, pages=4)
    # Checkpoints: before starting, before pages 1, 2, then 3 (cancel).
    mocker.patch("app.workers.tasks.ocr_tasks._cancel_requested", side_effect=[False, False, False, True])

    result, events = await run_ocr(mocker, doc, 4, ["one", "two", "three", "four"])

    assert result == {"status": "cancelled", "document_id": doc["id"], "read_pages": 2}
    final = {e["page"]["page_number"]: e["page"]["status"] for e in events if e["type"] == "page"}
    assert final == {1: "completed", 2: "completed", 3: "cancelled", 4: "cancelled"}
    assert events[-1] == {"type": "document", "status": "cancelled", "message": "Cancelled after 2 of 4 pages."}

    pages = (await async_client.get(f"{API}/documents/{doc['id']}/pages", headers=auth_headers)).json()["data"]
    assert [(p["status"], p["extracted_text"]) for p in pages] == [
        ("completed", "one"), ("completed", "two"), ("cancelled", None), ("cancelled", None),
    ]
    assert await net_usage(doc["id"]) == 2 * Decimal("0.1")  # two of four pages billed


@pytest.mark.asyncio
async def test_cancelling_a_document_before_ocr_starts_is_immediate(
    async_client, auth_headers, mock_storage, mock_upload_tasks, mock_page_job_queue, mocker
):
    doc = await upload(async_client, auth_headers, pages=2)

    response = await async_client.post(f"{API}/documents/{doc['id']}/cancel", headers=auth_headers)
    assert response.status_code == 200, response.text
    assert response.json()["data"]["upload_status"] == "cancelled"

    # The queued OCR run then stops without reading or charging anything.
    result, _ = await run_ocr(mocker, doc, 2, ["a", "b"])
    assert result["status"] == "cancelled"
    assert await net_usage(doc["id"]) == 0


@pytest.mark.asyncio
async def test_cancelling_a_document_cancels_its_unfinished_page_jobs(
    async_client, auth_headers, mock_storage, mock_upload_tasks, mock_page_job_queue, mocker
):
    from app.db.models.classification_job import JobStatus

    doc = await upload(async_client, auth_headers, pages=3, lid_model="sklearn_langid")
    await run_ocr(mocker, doc, 3, ["පළමු.", "දෙවන.", "තෙවන."])
    queued, running, done = await page_jobs(doc["id"])
    await set_job(running.id, status=JobStatus.PROCESSING)
    await set_job(done.id, status=JobStatus.COMPLETED)

    response = await async_client.post(f"{API}/documents/{doc['id']}/cancel", headers=auth_headers)
    assert response.status_code == 200, response.text

    jobs = {j.page_number: j for j in await page_jobs(doc["id"])}
    assert jobs[1].status == JobStatus.CANCELLED               # never started
    assert (jobs[2].status, jobs[2].cancel_requested) == (JobStatus.PROCESSING, True)  # stops at its next batch
    assert jobs[3].status == JobStatus.COMPLETED               # finished work is untouched

    # Nothing left to cancel once every job is final.
    await set_job(running.id, status=JobStatus.CANCELLED)
    again = await async_client.post(f"{API}/documents/{doc['id']}/cancel", headers=auth_headers)
    assert again.status_code == 400
