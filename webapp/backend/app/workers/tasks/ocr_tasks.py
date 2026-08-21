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

        # Simulate heavy OCR / ML work (mocked)
        # In the future, we'd fetch the file from MinIO, process with PyMuPDF/Tesseract, 
        # save the JSON result back to MinIO
        
        await asyncio.sleep(5) # Mock delay
        
        doc.upload_status = UploadStatus.READY
        await session.commit()
        return {"status": "success", "document_id": document_id}

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
