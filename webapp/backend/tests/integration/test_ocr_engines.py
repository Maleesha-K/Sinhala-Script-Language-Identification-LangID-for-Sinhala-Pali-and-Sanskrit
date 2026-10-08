"""Integration tests for OCR engine selection.

The API side mocks storage and both Celery tasks. The worker side runs the
real `_process_document_async` against the test database, with storage and
the engines' `extract_text` patched, so no MinIO, Tesseract or Surya model is
needed.
"""
import uuid
from io import BytesIO

import fitz
import pytest
from sqlalchemy import select

from app.config import settings

API = settings.API_V1_STR


def make_pdf(pages: int = 2) -> bytes:
    doc = fitz.open()
    for i in range(pages):
        doc.new_page().insert_text((72, 72), f"page {i + 1}")
    return doc.tobytes()


@pytest.fixture
def mock_storage(mocker):
    storage = mocker.patch("app.api.v1.documents.storage_service")
    storage.upload_document.return_value = True
    return storage


@pytest.fixture
def mock_tasks(mocker):
    return {
        "default": mocker.patch("app.api.v1.documents.process_document_ocr"),
        "surya": mocker.patch("app.api.v1.documents.process_document_ocr_surya"),
    }


async def upload(client, headers, **form) -> "httpx.Response":
    return await client.post(
        f"{API}/documents/upload",
        headers=headers,
        files={"file": ("doc.pdf", BytesIO(make_pdf()), "application/pdf")},
        data=form,
    )


# --- engine list -------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_ocr_engines(async_client, auth_headers):
    response = await async_client.get(f"{API}/documents/ocr-engines", headers=auth_headers)

    assert response.status_code == 200, response.text
    engines = {e["id"]: e for e in response.json()["data"]}
    assert set(engines) == {"tesseract", "surya"}
    assert engines["tesseract"]["is_default"] is True
    assert engines["surya"]["is_default"] is False


@pytest.mark.asyncio
async def test_list_ocr_engines_requires_a_token(async_client):
    response = await async_client.get(f"{API}/documents/ocr-engines")
    assert response.status_code == 401


# --- upload ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_upload_defaults_to_tesseract(async_client, auth_headers, mock_storage, mock_tasks):
    response = await upload(async_client, auth_headers)

    assert response.status_code == 201, response.text
    doc = response.json()["data"]
    assert doc["ocr_engine"] == "tesseract"
    mock_tasks["default"].delay.assert_called_once_with(doc["id"])
    mock_tasks["surya"].delay.assert_not_called()


@pytest.mark.asyncio
async def test_upload_with_surya_goes_to_the_surya_queue(
    async_client, auth_headers, mock_storage, mock_tasks
):
    response = await upload(async_client, auth_headers, ocr_engine="surya")

    assert response.status_code == 201, response.text
    doc = response.json()["data"]
    assert doc["ocr_engine"] == "surya"
    mock_tasks["surya"].delay.assert_called_once_with(doc["id"])
    mock_tasks["default"].delay.assert_not_called()


@pytest.mark.asyncio
async def test_upload_with_unknown_engine_returns_400(
    async_client, auth_headers, mock_storage, mock_tasks
):
    response = await upload(async_client, auth_headers, ocr_engine="abbyy")

    assert response.status_code == 400, response.text
    assert "Unknown OCR engine" in response.json()["message"]
    mock_storage.upload_document.assert_not_called()


def test_ocr_tasks_are_routed_away_from_classification():
    """OCR never occupies the classification worker: pages it has read are
    classified on the default queue while later pages are still being OCR'd."""
    from app.workers.celery_app import celery_app

    route = lambda name: celery_app.amqp.router.route({}, name)["queue"].name
    assert route("process_document_ocr_surya") == "surya"
    assert route("process_document_ocr") == "ocr"
    assert route("process_classification_job") == "celery"


# --- worker ------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("engine_id, patch_target", [
    ("tesseract", "app.ocr.tesseract_engine.TesseractEngine.extract_text"),
    ("surya", "app.ocr.surya_engine.SuryaEngine.extract_text"),
])
async def test_worker_uses_the_documents_engine(
    async_client, auth_headers, mock_storage, mock_tasks, mocker, engine_id, patch_target
):
    from app.db.models.document import Document
    from app.db.models.document_page import DocumentPage
    from app.db.models.usage_record import UsageRecord
    from app.db.session import async_session_maker
    from app.services.storage_service import storage_service
    from app.workers.tasks.ocr_tasks import _process_document_async

    doc = (await upload(async_client, auth_headers, ocr_engine=engine_id)).json()["data"]
    mocker.patch.object(storage_service, "get_document_bytes", return_value=make_pdf(2))
    extract = mocker.patch(patch_target, return_value=f"text from {engine_id}")

    result = await _process_document_async(doc["id"])

    assert result["status"] == "success", result
    assert extract.call_count == 2
    doc_id = uuid.UUID(doc["id"])
    async with async_session_maker() as session:
        document = (await session.execute(select(Document).where(Document.id == doc_id))).scalar_one()
        pages = (await session.execute(
            select(DocumentPage).where(DocumentPage.document_id == doc_id).order_by(DocumentPage.page_number)
        )).scalars().all()
        usage = (await session.execute(
            select(UsageRecord).where(UsageRecord.job_id == doc_id)
        )).scalars().all()

    assert document.upload_status.value == "ready"
    assert [p.ocr_model for p in pages] == [engine_id, engine_id]
    assert [p.extracted_text for p in pages] == [f"text from {engine_id}"] * 2
    # Billed at the chosen engine's rate, for both pages.
    assert [(u.model_name, float(u.quantity)) for u in usage] == [(engine_id, 2.0)]


def test_surya_engine_joins_recognised_lines(mocker):
    """SuryaEngine returns the recognised lines joined top to bottom."""
    from types import SimpleNamespace

    from PIL import Image

    from app.ocr.surya_engine import SuryaEngine

    engine = SuryaEngine()
    lines = [SimpleNamespace(text="බුද්ධං සරණං ගච්ඡාමි."), SimpleNamespace(text="ධම්මං සරණං ගච්ඡාමි.")]
    engine._recognition = mocker.Mock(return_value=[SimpleNamespace(text_lines=lines)])
    engine._detection = object()

    text = engine.extract_text(Image.new("L", (10, 10)))

    assert text == "බුද්ධං සරණං ගච්ඡාමි.\nධම්මං සරණං ගච්ඡාමි."
    image_arg = engine._recognition.call_args[0][0][0]
    assert image_arg.mode == "RGB"
    assert engine._recognition.call_args.kwargs["det_predictor"] is engine._detection
