import io
import logging
from decimal import Decimal
from uuid import UUID
from app.workers.celery_app import celery_app
from app.db.session import async_session_maker
from app.db.models.document import Document, UploadStatus
from app.utils.events import document_channel, job_payload, page_payload, publish
from sqlalchemy import select
import asyncio

logger = logging.getLogger(__name__)


async def _cancel_requested(session, document_id) -> bool:
    # A column select reads the database, not the session's cached object.
    result = await session.execute(select(Document.cancel_requested).where(Document.id == document_id))
    return bool(result.scalar_one())


async def _queue_page_classification(session, owner_id, document_id, page, model_name, channel):
    """Classify a page as soon as it is OCR'd, in its own job on the default queue."""
    from app.db.models.classification_job import ClassificationJob, JobStatus
    from app.workers.tasks.classification_tasks import process_classification_job

    job = ClassificationJob(
        user_id=owner_id,
        document_id=document_id,
        page_number=page.page_number,
        input_text=page.extracted_text,
        model_name=model_name,
        # OCR'd lines wrap mid-sentence; see split_segments("document").
        segmentation_strategy="document",
        status=JobStatus.QUEUED,
        error_message=None,
        cancel_requested=False,
    )
    session.add(job)
    await session.commit()
    publish(channel, {"type": "page_job", "page_number": page.page_number, "job": job_payload(job)})
    process_classification_job.delay(str(job.id))


async def _process_document_async(document_id: str):
    """OCR a document page by page. Each page is saved and published as soon as
    it is read, and queued for classification when the document has a model.

    A cancel (Document.cancel_requested) is checked before each page: the pages
    read so far are kept, the rest are marked cancelled and refunded."""
    doc_uuid = UUID(document_id)
    async with async_session_maker() as session:
        result = await session.execute(select(Document).where(Document.id == doc_uuid))
        doc = result.scalar_one_or_none()
        
        if not doc:
            return {"status": "error", "message": "Document not found"}

        from app.services.storage_service import storage_service
        import fitz
        from PIL import Image
        from app.ocr.registry import get_ocr_engine
        from app.db.models.document_page import DocumentPage, ExtractionMethod, PageStatus

        from app.services.credit_service import credit_service
        from app.db.session import engine

        # Read before any rollback: expired attributes cannot lazy-load in async.
        owner_id = doc.user_id
        engine_id = doc.ocr_engine
        lid_model = doc.lid_model
        channel = document_channel(document_id)

        def publish_document(status: UploadStatus, message: str = ""):
            publish(channel, {"type": "document", "status": status.value, "message": message})

        def publish_page(page):
            publish(channel, {"type": "page", "page": page_payload(page)})

        async def finish(status: UploadStatus, message: str = ""):
            await session.refresh(doc)
            doc.upload_status = status
            await session.commit()
            publish_document(status, message)

        async def mark_failed(message: str, refund: bool = False):
            # Drop any pages added by the failed run before recording the failure.
            await session.rollback()
            if refund:
                await credit_service.refund_ocr(session, owner_id, doc_uuid)
            await finish(UploadStatus.FAILED, message)
            return {"status": "error", "message": message}

        try:
            if await _cancel_requested(session, doc_uuid):
                await finish(UploadStatus.CANCELLED, "Cancelled before OCR started.")
                return {"status": "cancelled", "document_id": document_id, "read_pages": 0}

            # Fetch PDF from MinIO
            doc_bytes = storage_service.get_document_bytes(doc.minio_key)
            if not doc_bytes:
                return await mark_failed("Could not download document from storage")

            charged = False
            try:
                pdf_document = fitz.open(stream=doc_bytes, filetype="pdf")
                total_pages = len(pdf_document)
                ocr_engine = get_ocr_engine(engine_id)

                # Deduct credits at the chosen engine's per-page rate
                success = await credit_service.charge_ocr_page(
                    session, owner_id, doc_uuid, engine_id, num_pages=total_pages
                )
                if not success:
                    return await mark_failed("Insufficient credits for OCR")
                charged = True

                # Every page is listed (pending) before the first is read.
                pages = [
                    DocumentPage(document_id=doc_uuid, page_number=n + 1, status=PageStatus.PENDING)
                    for n in range(total_pages)
                ]
                session.add_all(pages)
                await session.commit()
                for page in pages:
                    publish_page(page)
            except Exception as e:
                logger.exception("OCR setup failed for document %s", document_id)
                # The user is not billed for an OCR run that produced nothing.
                return await mark_failed(str(e), refund=charged)

            failed = cancelled = 0
            for index, page in enumerate(pages):
                # Checkpoint: on cancel, keep the pages read so far and mark the
                # rest as not read.
                if await _cancel_requested(session, doc_uuid):
                    for rest in pages[index:]:
                        await session.refresh(rest)
                        rest.status = PageStatus.CANCELLED
                    await session.commit()
                    for rest in pages[index:]:
                        publish_page(rest)
                    cancelled = len(pages) - index
                    break

                # A rollback below expires every loaded object; reload this one.
                await session.refresh(page)
                page.status = PageStatus.PROCESSING
                await session.commit()
                publish_page(page)
                try:
                    pdf_page = pdf_document.load_page(page.page_number - 1)
                    # Render to high-res image for OCR
                    pix = pdf_page.get_pixmap(dpi=ocr_engine.render_dpi)
                    img = Image.open(io.BytesIO(pix.tobytes()))
                    page.extracted_text = ocr_engine.extract_text(img).strip()
                    page.extraction_method = ExtractionMethod.OCR
                    page.ocr_model = engine_id
                    page.status = PageStatus.COMPLETED
                    await session.commit()
                except Exception:
                    logger.exception("OCR failed for page %s of document %s", page.page_number, document_id)
                    await session.rollback()
                    await session.refresh(page)
                    page.status = PageStatus.FAILED
                    await session.commit()
                    publish_page(page)
                    failed += 1
                    continue
                publish_page(page)

                # Not when the document was cancelled while this page was read.
                if lid_model and page.extracted_text and not await _cancel_requested(session, doc_uuid):
                    try:
                        await _queue_page_classification(
                            session, owner_id, doc_uuid, page, lid_model, channel
                        )
                    except Exception:
                        logger.exception("Could not queue classification of page %s", page.page_number)
                        await session.rollback()

            # Pages that could not be read, or were cancelled, are not billed.
            if failed or cancelled:
                await credit_service.refund_ocr(
                    session, owner_id, doc_uuid, Decimal(failed + cancelled) / Decimal(total_pages)
                )
            if cancelled:
                read = total_pages - cancelled - failed
                await finish(UploadStatus.CANCELLED, f"Cancelled after {read} of {total_pages} pages.")
                return {"status": "cancelled", "document_id": document_id, "read_pages": read}
            if total_pages and failed == total_pages:
                await finish(UploadStatus.FAILED, "OCR failed on every page")
                return {"status": "error", "message": "OCR failed on every page"}
            await finish(UploadStatus.READY)
            return {"status": "success", "document_id": document_id, "failed_pages": failed}
        finally:
            await engine.dispose()

@celery_app.task(name="process_document_ocr", bind=True, max_retries=3)
def process_document_ocr(self, document_id: str):
    """
    Celery task that OCRs every page of an uploaded PDF.
    Uses asyncio.run to execute the async DB operations inside the sync Celery worker.
    """
    try:
        # Run the async DB logic in a new event loop
        result = asyncio.run(_process_document_async(document_id))
        return result
    except Exception as exc:
        # Mark as failed in DB on error (omitted for brevity, but should happen in prod)
        self.retry(exc=exc, countdown=10)


@celery_app.task(name="process_document_ocr_surya", bind=True, max_retries=3)
def process_document_ocr_surya(self, document_id: str):
    """
    Same pipeline as process_document_ocr, routed to the dedicated `surya`
    queue (see celery_app task_routes) so Surya's models are loaded by a single
    worker process instead of every process in the shared pool.
    """
    try:
        return asyncio.run(_process_document_async(document_id))
    except Exception as exc:
        self.retry(exc=exc, countdown=10)
