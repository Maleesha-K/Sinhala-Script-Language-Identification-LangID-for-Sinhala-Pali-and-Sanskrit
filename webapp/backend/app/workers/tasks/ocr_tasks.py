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
        import pytesseract
        from PIL import Image
        import io
        from app.db.models.document_page import DocumentPage, ExtractionMethod, PageStatus

        # Fetch PDF from MinIO
        doc_bytes = storage_service.get_document_bytes(doc.minio_key)
        if not doc_bytes:
            return {"status": "error", "message": "Could not download document from storage"}

        try:
            pdf_document = fitz.open(stream=doc_bytes, filetype="pdf")
            total_pages = len(pdf_document)
            
            # Deduct credits
            from app.services.credit_service import credit_service
            success = await credit_service.charge_ocr_page(
                session, doc.user_id, doc.id, "tesseract", num_pages=total_pages
            )
            
            if not success:
                doc.upload_status = UploadStatus.DELETED # Or a FAILED state if added
                await session.commit()
                return {"status": "error", "message": "Insufficient credits for OCR"}
            
            for page_num in range(total_pages):
                page = pdf_document.load_page(page_num)
                # Render to high-res image for OCR
                pix = page.get_pixmap(dpi=300)
                img = Image.open(io.BytesIO(pix.tobytes()))
                
                # Perform OCR for Sinhala, Sanskrit, and English
                extracted_text = pytesseract.image_to_string(img, lang="sin+san+eng")
                
                doc_page = DocumentPage(
                    document_id=doc.id,
                    page_number=page_num + 1,
                    extracted_text=extracted_text.strip(),
                    extraction_method=ExtractionMethod.OCR,
                    ocr_model="tesseract",
                    status=PageStatus.COMPLETED
                )
                session.add(doc_page)
                
            doc.upload_status = UploadStatus.READY
            await session.commit()
            return {"status": "success", "document_id": document_id}
            
        except Exception as e:
            print(f"OCR Error for document {document_id}: {e}")
            return {"status": "error", "message": str(e)}

@celery_app.task(name="process_document_ocr", bind=True, max_retries=3)
def process_document_ocr(self, document_id: str):
    """
    Mock Celery task for processing a document.
    Uses asyncio.run to execute the async DB operations inside the sync Celery worker.
    """
    try:
        # Run the async DB logic in a new event loop
        result = asyncio.run(_process_document_async(document_id))
        return result
    except Exception as exc:
        # Mark as failed in DB on error (omitted for brevity, but should happen in prod)
        self.retry(exc=exc, countdown=10)
