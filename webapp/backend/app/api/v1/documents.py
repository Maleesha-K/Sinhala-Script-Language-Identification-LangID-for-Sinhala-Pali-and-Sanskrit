from fastapi import APIRouter, Depends, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID
from typing import List
import uuid

from app.db.models.user import User
from app.db.models.document import Document, UploadStatus
from app.dependencies import get_db, get_current_user
from app.schemas.response import BaseResponse, success_response
from app.schemas.document import DocumentResponse, OCREngineResponse
from app.services.storage_service import storage_service
from app.workers.tasks.ocr_tasks import process_document_ocr, process_document_ocr_surya
from app.workers.tasks.classification_tasks import split_segments
from app.ocr.registry import OCR_ENGINES, DEFAULT_OCR_ENGINE, list_ocr_engines
from app.ml.registry import MODELS
from app.db.models.classification_job import ClassificationJob, JobStatus
from app.db.models.classified_segment import ClassifiedSegment
from app.services.credit_service import credit_service
from app.utils.events import job_payload, page_payload, segment_payload
from app.utils.exceptions import AppException, BadRequestException, NotFoundException

router = APIRouter(prefix="/documents", tags=["documents"])

def _ocr_task_for(queue: str | None):
    """Celery task for an engine: Surya's own, or the shared OCR task (routed to
    the `ocr` queue, see celery_app)."""
    return process_document_ocr_surya if queue == "surya" else process_document_ocr

@router.get("/ocr-engines", response_model=BaseResponse[List[OCREngineResponse]])
async def get_ocr_engines():
    """List the OCR engines a user can choose between when uploading."""
    return success_response(data=list_ocr_engines())

@router.post("/upload", response_model=BaseResponse[DocumentResponse], status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    ocr_engine: str = Form(DEFAULT_OCR_ENGINE),
    lid_model: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Uploads a PDF document to MinIO and queues an OCR/Text Extraction task."""
    
    if not file.filename.lower().endswith(".pdf"):
        raise BadRequestException(message="Only PDF files are currently supported")

    engine = OCR_ENGINES.get(ocr_engine)
    if engine is None:
        raise BadRequestException(
            message=f"Unknown OCR engine '{ocr_engine}'. Available: {', '.join(sorted(OCR_ENGINES))}"
        )

    # Model that classifies each page as soon as it is OCR'd; empty: OCR only.
    lid_model = lid_model or None
    if lid_model is not None:
        if lid_model not in MODELS:
            raise BadRequestException(
                message=f"Unknown model '{lid_model}'. Available: {', '.join(sorted(MODELS))}"
            )
        # Raises when an administrator has disabled the model.
        await credit_service.estimate_classification_cost(db, lid_model, 0)

    # Read file content
    content = await file.read()
    file_size = len(content)
    
    # Generate unique object name for MinIO
    object_name = f"user_{current_user.id}/{uuid.uuid4()}_{file.filename}"
    
    # Upload to MinIO
    upload_success = storage_service.upload_document(object_name, content, file.content_type)
    if not upload_success:
        raise AppException(message="Failed to upload document to storage", status_code=500)

    # Create DB Record
    new_doc = Document(
        user_id=current_user.id,
        filename=file.filename,
        size_bytes=file_size,
        mime_type=file.content_type,
        minio_key=object_name,
        upload_status=UploadStatus.UPLOADING,
        ocr_engine=engine.id,
        lid_model=lid_model,
    )
    
    db.add(new_doc)
    current_user.storage_used_bytes += file_size
    await db.commit()
    await db.refresh(new_doc)

    # Queue Celery Task
    _ocr_task_for(engine.queue).delay(str(new_doc.id))

    return success_response(data=new_doc, message="Document uploaded and processing started")

@router.get("", response_model=BaseResponse[List[DocumentResponse]])
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Lists all documents belonging to the current user."""
    result = await db.execute(select(Document).where(Document.user_id == current_user.id).order_by(Document.created_at.desc()))
    docs = result.scalars().all()
    return success_response(data=docs, message="Documents retrieved")

@router.get("/{document_id}", response_model=BaseResponse[DocumentResponse])
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Gets a specific document and its presigned download URL."""
    result = await db.execute(select(Document).where(Document.id == document_id, Document.user_id == current_user.id))
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise NotFoundException(item="Document")
        
    # We could attach the presigned URL here, or have a separate endpoint for it.
    # For now, we just return the document metadata.
    return success_response(data=doc, message="Document retrieved")

@router.get("/{document_id}/download")
async def get_document_download_url(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generates a pre-signed URL to securely download the document from MinIO."""
    result = await db.execute(select(Document).where(Document.id == document_id, Document.user_id == current_user.id))
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise NotFoundException(item="Document")
        
    url = storage_service.get_presigned_url(doc.minio_key)
    if not url:
        raise AppException(message="Failed to generate download link", status_code=500)
        
    return success_response(data={"download_url": url}, message="Download URL generated")

@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Deletes a document from the database and MinIO."""
    result = await db.execute(select(Document).where(Document.id == document_id, Document.user_id == current_user.id))
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise NotFoundException(item="Document")
        
    # Delete from MinIO
    if doc.minio_key:
        storage_service.delete_document(doc.minio_key)
        
    # Keep the per-page classification jobs (billing and annotation history),
    # detached from the deleted document.
    await db.execute(
        update(ClassificationJob).where(ClassificationJob.document_id == doc.id).values(document_id=None)
    )

    # Delete from DB
    await db.delete(doc)
    current_user.storage_used_bytes = max(0, current_user.storage_used_bytes - doc.size_bytes)
    await db.commit()
    
    return success_response(message="Document deleted successfully")

from app.db.models.document_page import DocumentPage

def _job_total(job: ClassificationJob, done: int) -> int | None:
    """Segments a job will produce: known once it runs (unknown while queued)."""
    if job.status == JobStatus.PROCESSING:
        return len(split_segments(job.input_text or "", job.segmentation_strategy))
    return done if job.status == JobStatus.COMPLETED else None


@router.get("/{document_id}/pages")
async def get_document_pages(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Pages of a document with their OCR text and, when the document was
    uploaded with a model, each page's classification so far."""
    doc_result = await db.execute(select(Document).where(Document.id == document_id, Document.user_id == current_user.id))
    doc = doc_result.scalar_one_or_none()
    
    if not doc:
        raise NotFoundException(item="Document")
        
    pages_result = await db.execute(
        select(DocumentPage)
        .where(DocumentPage.document_id == document_id)
        .order_by(DocumentPage.page_number)
    )
    pages = pages_result.scalars().all()

    jobs_result = await db.execute(
        select(ClassificationJob)
        .where(ClassificationJob.document_id == document_id, ClassificationJob.page_number.is_not(None))
        .order_by(ClassificationJob.created_at)
    )
    # The latest job per page wins.
    jobs = {job.page_number: job for job in jobs_result.scalars().all()}

    segments_by_job: dict = {job.id: [] for job in jobs.values()}
    if segments_by_job:
        segments_result = await db.execute(
            select(ClassifiedSegment)
            .where(ClassifiedSegment.job_id.in_(segments_by_job))
            .order_by(ClassifiedSegment.segment_index)
        )
        for segment in segments_result.scalars().all():
            segments_by_job[segment.job_id].append(segment_payload(segment))

    data = []
    for page in pages:
        item = page_payload(page)
        job = jobs.get(page.page_number)
        item["classification"] = None
        if job is not None:
            segments = segments_by_job[job.id]
            item["classification"] = {
                **job_payload(job, len(segments), _job_total(job, len(segments))),
                "segments": segments,
            }
        data.append(item)
    return success_response(data=data, message="Document pages retrieved")
