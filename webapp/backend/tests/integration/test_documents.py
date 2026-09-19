"""Integration tests for the document endpoints.

MinIO and Celery are mocked throughout: `documents.py` imports both
`storage_service` and `process_document_ocr` into its own namespace, so the
patch targets are `app.api.v1.documents.*` rather than the source modules.
No worker runs in the test suite, so an uploaded document stays in its initial
UPLOADING state and the OCR task is only asserted to have been queued.
"""
import uuid
from io import BytesIO

import pytest

from app.config import settings

API = settings.API_V1_STR

PDF_BYTES = b"%PDF-1.4 fake pdf content"


@pytest.fixture
def mock_storage(mocker):
    """Stub the MinIO-backed storage service used by the documents router."""
    storage = mocker.patch("app.api.v1.documents.storage_service")
    storage.upload_document.return_value = True
    storage.delete_document.return_value = True
    storage.get_presigned_url.return_value = "https://minio.test/signed-url"
    return storage


@pytest.fixture
def mock_ocr_task(mocker):
    """Stub the Celery task so no broker or worker is required."""
    return mocker.patch("app.api.v1.documents.process_document_ocr")


def pdf_upload(filename: str = "sample.pdf") -> dict:
    """Build a multipart file payload for httpx."""
    return {"file": (filename, BytesIO(PDF_BYTES), "application/pdf")}


async def upload_document(client, headers, filename: str = "sample.pdf") -> dict:
    """Upload a PDF and return the created document record."""
    response = await client.post(
        f"{API}/documents/upload", headers=headers, files=pdf_upload(filename)
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


# --- upload ----------------------------------------------------------------

@pytest.mark.asyncio
async def test_upload_document(async_client, auth_headers, mock_storage, mock_ocr_task):
    """POST /documents/upload stores the file and returns its metadata."""
    response = await async_client.post(
        f"{API}/documents/upload", headers=auth_headers, files=pdf_upload("report.pdf")
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "success"

    data = body["data"]
    assert data["filename"] == "report.pdf"
    assert data["mime_type"] == "application/pdf"
    assert data["size_bytes"] == len(PDF_BYTES)
    assert data["upload_status"] == "uploading"
    assert "id" in data


@pytest.mark.asyncio
async def test_upload_sends_file_to_storage(
    async_client, auth_headers, mock_storage, mock_ocr_task
):
    """The uploaded bytes are handed to the storage service under a user-scoped key."""
    document = await upload_document(async_client, auth_headers, "scoped.pdf")

    mock_storage.upload_document.assert_called_once()
    object_name, data, content_type = mock_storage.upload_document.call_args[0]
    assert data == PDF_BYTES
    assert content_type == "application/pdf"
    assert object_name.startswith(f"user_{document['user_id']}/")
    assert object_name.endswith("scoped.pdf")


@pytest.mark.asyncio
async def test_upload_queues_ocr_task(
    async_client, auth_headers, mock_storage, mock_ocr_task
):
    """The OCR task is queued with the new document's id."""
    document = await upload_document(async_client, auth_headers)

    mock_ocr_task.delay.assert_called_once_with(document["id"])


@pytest.mark.asyncio
async def test_upload_rejects_non_pdf(
    async_client, auth_headers, mock_storage, mock_ocr_task
):
    """Only PDFs are accepted, so a .txt upload is refused.

    NOTE: documents.py raises a bare HTTPException, so the body is FastAPI's
    {"detail": ...} rather than the {status, message, data} envelope every
    other router returns via AppException. This asserts current behaviour;
    see test_error_envelope_is_inconsistent_with_other_routers below.
    """
    response = await async_client.post(
        f"{API}/documents/upload",
        headers=auth_headers,
        files={"file": ("notes.txt", BytesIO(b"plain text"), "text/plain")},
    )

    assert response.status_code == 400, response.text
    assert "Only PDF" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_rejects_non_pdf_before_touching_storage(
    async_client, auth_headers, mock_storage, mock_ocr_task
):
    """A rejected file is never uploaded and never queues work."""
    await async_client.post(
        f"{API}/documents/upload",
        headers=auth_headers,
        files={"file": ("image.png", BytesIO(b"\x89PNG"), "image/png")},
    )

    mock_storage.upload_document.assert_not_called()
    mock_ocr_task.delay.assert_not_called()


@pytest.mark.asyncio
async def test_upload_accepts_uppercase_pdf_extension(
    async_client, auth_headers, mock_storage, mock_ocr_task
):
    """The extension check is case-insensitive."""
    response = await async_client.post(
        f"{API}/documents/upload",
        headers=auth_headers,
        files={"file": ("REPORT.PDF", BytesIO(PDF_BYTES), "application/pdf")},
    )
    assert response.status_code == 201, response.text


@pytest.mark.asyncio
async def test_upload_returns_500_when_storage_fails(
    async_client, auth_headers, mock_storage, mock_ocr_task
):
    """A storage failure surfaces as an error and queues no work."""
    mock_storage.upload_document.return_value = False

    response = await async_client.post(
        f"{API}/documents/upload", headers=auth_headers, files=pdf_upload()
    )

    assert response.status_code == 500, response.text
    mock_ocr_task.delay.assert_not_called()


@pytest.mark.asyncio
async def test_upload_without_token_returns_401(async_client, mock_storage):
    """Uploading requires authentication."""
    response = await async_client.post(f"{API}/documents/upload", files=pdf_upload())
    assert response.status_code == 401, response.text


@pytest.mark.asyncio
async def test_error_envelope_is_inconsistent_with_other_routers(
    async_client, auth_headers, mock_storage, mock_ocr_task
):
    """Documents errors use FastAPI's shape; auth errors use the app envelope.

    This is a real inconsistency in the API, not a test artefact: documents.py
    raises bare HTTPException while the rest of the app raises AppException,
    which the handler in main.py renders as {status, message, data}. A client
    reading `message` on a document error gets nothing. Pinning it here so the
    difference is visible, and so this test fails if the routers are unified
    (at which point the assertions above should move to `message`).
    """
    document_error = await async_client.post(
        f"{API}/documents/upload",
        headers=auth_headers,
        files={"file": ("notes.txt", BytesIO(b"plain text"), "text/plain")},
    )
    # A bad token raises AppException inside the dependency, so it is rendered
    # by the handler. (A *missing* token is a third shape again: FastAPI's
    # security scheme returns {"detail": "Not authenticated"} before any
    # handler runs, which is why this compares against a bad token instead.)
    app_error = await async_client.get(
        f"{API}/users/me", headers={"Authorization": "Bearer not-a-real-token"}
    )

    assert document_error.status_code == 400
    assert set(document_error.json()) == {"detail"}

    assert app_error.status_code == 401
    assert set(app_error.json()) == {"status", "message", "data"}


# --- list ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_documents_empty_for_new_user(async_client, auth_headers):
    """A user with no uploads gets an empty list."""
    response = await async_client.get(f"{API}/documents", headers=auth_headers)

    assert response.status_code == 200, response.text
    assert response.json()["data"] == []


@pytest.mark.asyncio
async def test_list_documents_returns_uploads(
    async_client, auth_headers, mock_storage, mock_ocr_task
):
    """Uploaded documents appear in the list."""
    first = await upload_document(async_client, auth_headers, "one.pdf")
    second = await upload_document(async_client, auth_headers, "two.pdf")

    response = await async_client.get(f"{API}/documents", headers=auth_headers)

    assert response.status_code == 200, response.text
    returned_ids = {doc["id"] for doc in response.json()["data"]}
    assert returned_ids == {first["id"], second["id"]}


@pytest.mark.asyncio
async def test_list_documents_excludes_other_users(
    async_client, auth_headers, second_user_headers, mock_storage, mock_ocr_task
):
    """The listing is scoped to the caller."""
    mine = await upload_document(async_client, auth_headers, "mine.pdf")
    theirs = await upload_document(async_client, second_user_headers, "theirs.pdf")

    response = await async_client.get(f"{API}/documents", headers=auth_headers)

    assert response.status_code == 200, response.text
    returned_ids = {doc["id"] for doc in response.json()["data"]}
    assert mine["id"] in returned_ids
    assert theirs["id"] not in returned_ids


@pytest.mark.asyncio
async def test_list_documents_without_token_returns_401(async_client):
    """Listing requires authentication."""
    response = await async_client.get(f"{API}/documents")
    assert response.status_code == 401, response.text


# --- get -------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_document(async_client, auth_headers, mock_storage, mock_ocr_task):
    """A document can be fetched by id by its owner."""
    document = await upload_document(async_client, auth_headers, "fetch.pdf")

    response = await async_client.get(
        f"{API}/documents/{document['id']}", headers=auth_headers
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["id"] == document["id"]
    assert data["filename"] == "fetch.pdf"


@pytest.mark.asyncio
async def test_get_missing_document_returns_404(async_client, auth_headers):
    """An unknown id is a 404."""
    response = await async_client.get(
        f"{API}/documents/{uuid.uuid4()}", headers=auth_headers
    )
    assert response.status_code == 404, response.text


@pytest.mark.asyncio
async def test_get_another_users_document_returns_404(
    async_client, auth_headers, second_user_headers, mock_storage, mock_ocr_task
):
    """Another user's document is indistinguishable from a missing one.

    The query filters on user_id, so a 404 (rather than 403) avoids confirming
    that the id exists at all.
    """
    theirs = await upload_document(async_client, second_user_headers, "private.pdf")

    response = await async_client.get(
        f"{API}/documents/{theirs['id']}", headers=auth_headers
    )
    assert response.status_code == 404, response.text


@pytest.mark.asyncio
async def test_get_document_with_malformed_id_returns_422(async_client, auth_headers):
    """A non-UUID path parameter fails validation."""
    response = await async_client.get(
        f"{API}/documents/not-a-uuid", headers=auth_headers
    )
    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_get_document_without_token_returns_401(async_client):
    """Fetching requires authentication."""
    response = await async_client.get(f"{API}/documents/{uuid.uuid4()}")
    assert response.status_code == 401, response.text


# --- download url ----------------------------------------------------------

@pytest.mark.asyncio
async def test_get_download_url(async_client, auth_headers, mock_storage, mock_ocr_task):
    """The download route returns a presigned URL for the stored object."""
    document = await upload_document(async_client, auth_headers, "download.pdf")

    response = await async_client.get(
        f"{API}/documents/{document['id']}/download", headers=auth_headers
    )

    assert response.status_code == 200, response.text
    assert response.json()["data"]["download_url"] == "https://minio.test/signed-url"
    mock_storage.get_presigned_url.assert_called_once()


@pytest.mark.asyncio
async def test_download_url_returns_500_when_signing_fails(
    async_client, auth_headers, mock_storage, mock_ocr_task
):
    """An empty URL from storage is reported as a failure."""
    document = await upload_document(async_client, auth_headers)
    mock_storage.get_presigned_url.return_value = ""

    response = await async_client.get(
        f"{API}/documents/{document['id']}/download", headers=auth_headers
    )
    assert response.status_code == 500, response.text


@pytest.mark.asyncio
async def test_download_url_for_another_users_document_returns_404(
    async_client, auth_headers, second_user_headers, mock_storage, mock_ocr_task
):
    """A download link is never issued for someone else's document."""
    theirs = await upload_document(async_client, second_user_headers, "private.pdf")

    response = await async_client.get(
        f"{API}/documents/{theirs['id']}/download", headers=auth_headers
    )
    assert response.status_code == 404, response.text


@pytest.mark.asyncio
async def test_download_url_without_token_returns_401(async_client):
    """The download route requires authentication."""
    response = await async_client.get(f"{API}/documents/{uuid.uuid4()}/download")
    assert response.status_code == 401, response.text


# --- pages -----------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_pages_empty_before_ocr_runs(
    async_client, auth_headers, mock_storage, mock_ocr_task
):
    """No worker runs in tests, so a fresh document has no pages yet."""
    document = await upload_document(async_client, auth_headers)

    response = await async_client.get(
        f"{API}/documents/{document['id']}/pages", headers=auth_headers
    )

    assert response.status_code == 200, response.text
    assert response.json()["data"] == []


@pytest.mark.asyncio
async def test_get_pages_returns_pages_in_order(
    async_client, auth_headers, mock_storage, mock_ocr_task
):
    """Pages are returned ordered by page number.

    The OCR worker normally writes these rows; the test inserts them directly
    and deliberately out of order to prove the endpoint sorts them.
    """
    from app.db.models.document_page import DocumentPage, ExtractionMethod, PageStatus
    from app.db.session import async_session_maker

    document = await upload_document(async_client, auth_headers, "paged.pdf")

    async with async_session_maker() as session:
        for page_number in (3, 1, 2):
            session.add(
                DocumentPage(
                    document_id=uuid.UUID(document["id"]),
                    page_number=page_number,
                    extracted_text=f"text of page {page_number}",
                    extraction_method=ExtractionMethod.PDF_READ,
                    status=PageStatus.COMPLETED,
                )
            )
        await session.commit()

    response = await async_client.get(
        f"{API}/documents/{document['id']}/pages", headers=auth_headers
    )

    assert response.status_code == 200, response.text
    pages = response.json()["data"]
    assert [page["page_number"] for page in pages] == [1, 2, 3]
    assert pages[0]["extracted_text"] == "text of page 1"
    assert pages[0]["status"] == "completed"


@pytest.mark.asyncio
async def test_get_pages_for_missing_document_returns_404(async_client, auth_headers):
    """Pages of an unknown document are a 404."""
    response = await async_client.get(
        f"{API}/documents/{uuid.uuid4()}/pages", headers=auth_headers
    )
    assert response.status_code == 404, response.text


@pytest.mark.asyncio
async def test_get_pages_for_another_users_document_returns_404(
    async_client, auth_headers, second_user_headers, mock_storage, mock_ocr_task
):
    """Extracted text is not readable across accounts."""
    theirs = await upload_document(async_client, second_user_headers, "private.pdf")

    response = await async_client.get(
        f"{API}/documents/{theirs['id']}/pages", headers=auth_headers
    )
    assert response.status_code == 404, response.text


@pytest.mark.asyncio
async def test_get_pages_without_token_returns_401(async_client):
    """The pages route requires authentication."""
    response = await async_client.get(f"{API}/documents/{uuid.uuid4()}/pages")
    assert response.status_code == 401, response.text


# --- delete ----------------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_document(async_client, auth_headers, mock_storage, mock_ocr_task):
    """A document can be deleted by its owner."""
    document = await upload_document(async_client, auth_headers, "delete.pdf")

    response = await async_client.delete(
        f"{API}/documents/{document['id']}", headers=auth_headers
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "success"


@pytest.mark.asyncio
async def test_deleted_document_is_gone(
    async_client, auth_headers, mock_storage, mock_ocr_task
):
    """The record no longer resolves after deletion."""
    document = await upload_document(async_client, auth_headers)

    delete = await async_client.delete(
        f"{API}/documents/{document['id']}", headers=auth_headers
    )
    assert delete.status_code == 200, delete.text

    get = await async_client.get(
        f"{API}/documents/{document['id']}", headers=auth_headers
    )
    assert get.status_code == 404, get.text


@pytest.mark.asyncio
async def test_delete_removes_object_from_storage(
    async_client, auth_headers, mock_storage, mock_ocr_task
):
    """Deleting the record also removes the stored file, so no orphan is left."""
    await upload_document(async_client, auth_headers, "orphan.pdf")
    stored_key = mock_storage.upload_document.call_args[0][0]

    documents = await async_client.get(f"{API}/documents", headers=auth_headers)
    document_id = documents.json()["data"][0]["id"]

    await async_client.delete(f"{API}/documents/{document_id}", headers=auth_headers)

    mock_storage.delete_document.assert_called_once_with(stored_key)


@pytest.mark.asyncio
async def test_delete_cascades_to_pages(
    async_client, auth_headers, mock_storage, mock_ocr_task
):
    """Page rows are removed with their document via the delete-orphan cascade."""
    from sqlalchemy import select

    from app.db.models.document_page import DocumentPage, PageStatus
    from app.db.session import async_session_maker

    document = await upload_document(async_client, auth_headers, "cascade.pdf")
    document_id = uuid.UUID(document["id"])

    async with async_session_maker() as session:
        session.add(
            DocumentPage(
                document_id=document_id,
                page_number=1,
                extracted_text="page text",
                status=PageStatus.COMPLETED,
            )
        )
        await session.commit()

    delete = await async_client.delete(
        f"{API}/documents/{document['id']}", headers=auth_headers
    )
    assert delete.status_code == 200, delete.text

    async with async_session_maker() as session:
        result = await session.execute(
            select(DocumentPage).where(DocumentPage.document_id == document_id)
        )
        assert result.scalars().all() == []


@pytest.mark.asyncio
async def test_delete_missing_document_returns_404(async_client, auth_headers):
    """Deleting an unknown id is a 404."""
    response = await async_client.delete(
        f"{API}/documents/{uuid.uuid4()}", headers=auth_headers
    )
    assert response.status_code == 404, response.text


@pytest.mark.asyncio
async def test_delete_another_users_document_returns_404(
    async_client, auth_headers, second_user_headers, mock_storage, mock_ocr_task
):
    """One user cannot delete another user's document."""
    theirs = await upload_document(async_client, second_user_headers, "private.pdf")

    response = await async_client.delete(
        f"{API}/documents/{theirs['id']}", headers=auth_headers
    )
    assert response.status_code == 404, response.text

    # The owner can still see it.
    still_there = await async_client.get(
        f"{API}/documents/{theirs['id']}", headers=second_user_headers
    )
    assert still_there.status_code == 200, still_there.text


@pytest.mark.asyncio
async def test_delete_without_token_returns_401(async_client):
    """Deleting requires authentication."""
    response = await async_client.delete(f"{API}/documents/{uuid.uuid4()}")
    assert response.status_code == 401, response.text
