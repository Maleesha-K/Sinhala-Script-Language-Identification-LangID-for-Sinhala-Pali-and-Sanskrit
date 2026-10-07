import time
from uuid import UUID
from app.workers.celery_app import celery_app
from app.db.session import async_session_maker
from app.db.models.document import Document, UploadStatus
from sqlalchemy import select
import asyncio

async def _process_document_async(document_id: str):
    """Async internal function to update DB using SQLAlchemy."""
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
        import io
        from app.db.models.document_page import DocumentPage, ExtractionMethod, PageStatus

        from app.services.credit_service import credit_service
        from app.db.session import engine

        # Read before any rollback: expired attributes cannot lazy-load in async.
        owner_id = doc.user_id
        engine_id = doc.ocr_engine

        async def mark_failed(message: str, refund: bool = False):
            # Drop any pages added by the failed run before recording the failure.
            await session.rollback()
            if refund:
                await credit_service.refund_ocr(session, owner_id, doc_uuid)
            doc.upload_status = UploadStatus.FAILED
            await session.commit()
            await engine.dispose()
            return {"status": "error", "message": message}

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
                session, doc.user_id, doc.id, engine_id, num_pages=total_pages
            )
            
            if not success:
                return await mark_failed("Insufficient credits for OCR")
            charged = True
            
            for page_num in range(total_pages):
                page = pdf_document.load_page(page_num)
                # Render to high-res image for OCR
                pix = page.get_pixmap(dpi=ocr_engine.render_dpi)
                img = Image.open(io.BytesIO(pix.tobytes()))
                
                extracted_text = ocr_engine.extract_text(img)
                
                doc_page = DocumentPage(
                    document_id=doc.id,
                    page_number=page_num + 1,
                    extracted_text=extracted_text.strip(),
                    extraction_method=ExtractionMethod.OCR,
                    ocr_model=engine_id,
                    status=PageStatus.COMPLETED
                )
                session.add(doc_page)
                
            doc.upload_status = UploadStatus.READY
            await session.commit()
            
            await engine.dispose()
            return {"status": "success", "document_id": document_id}
            
        except Exception as e:
            print(f"OCR Error for document {document_id}: {e}")
            # The user is not billed for an OCR run that produced nothing.
            return await mark_failed(str(e), refund=charged)

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
