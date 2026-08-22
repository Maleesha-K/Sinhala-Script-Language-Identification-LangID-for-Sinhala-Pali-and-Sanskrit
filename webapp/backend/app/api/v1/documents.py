from fastapi import APIRouter, Depends, UploadFile, File, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import List
import uuid

from app.db.models.user import User
from app.db.models.document import Document, UploadStatus
from app.dependencies import get_db, get_current_user
from app.schemas.response import BaseResponse, success_response
from app.schemas.document import DocumentResponse
from app.services.storage_service import storage_service
from app.workers.tasks.ocr_tasks import process_document_ocr

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload", response_model=BaseResponse[DocumentResponse], status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Uploads a PDF document to MinIO and queues an OCR/Text Extraction task."""
    
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are currently supported")

    # Read file content
    content = await file.read()
    file_size = len(content)
    
    # Generate unique object name for MinIO
    object_name = f"user_{current_user.id}/{uuid.uuid4()}_{file.filename}"
    
    # Upload to MinIO
    upload_success = storage_service.upload_document(object_name, content, file.content_type)
    if not upload_success:
        raise HTTPException(status_code=500, detail="Failed to upload document to storage")

    # Create DB Record
    new_doc = Document(
        user_id=current_user.id,
        filename=file.filename,
        size_bytes=file_size,
        mime_type=file.content_type,
        minio_key=object_name,
        upload_status=UploadStatus.UPLOADING
    )
    
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)

    # Queue Celery Task
    process_document_ocr.delay(str(new_doc.id))

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
        raise HTTPException(status_code=404, detail="Document not found")
        
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
        raise HTTPException(status_code=404, detail="Document not found")
        
    url = storage_service.get_presigned_url(doc.minio_key)
    if not url:
        raise HTTPException(status_code=500, detail="Failed to generate download link")
        
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
        raise HTTPException(status_code=404, detail="Document not found")
        
    # Delete from MinIO
    if doc.minio_key:
        storage_service.delete_document(doc.minio_key)
        
    # Delete from DB
    await db.delete(doc)
    await db.commit()
    
    return success_response(message="Document deleted successfully")

from app.db.models.document_page import DocumentPage
from app.schemas.document import DocumentPageResponse

@router.get("/{document_id}/pages", response_model=BaseResponse[List[DocumentPageResponse]])
async def get_document_pages(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Gets all pages and OCR extracted text for a specific document."""
    # First check if the document belongs to the user
    doc_result = await db.execute(select(Document).where(Document.id == document_id, Document.user_id == current_user.id))
    doc = doc_result.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # Fetch pages
    pages_result = await db.execute(
        select(DocumentPage)
        .where(DocumentPage.document_id == document_id)
        .order_by(DocumentPage.page_number)
    )
    pages = pages_result.scalars().all()
    
    return success_response(data=pages, message="Document pages retrieved")
