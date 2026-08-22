from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.db.models.document import UploadStatus
from app.db.models.document_page import ExtractionMethod, PageStatus

class DocumentBase(BaseModel):
    filename: str
    mime_type: Optional[str] = None
    size_bytes: int
    minio_key: Optional[str] = None

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: UUID
    user_id: UUID
    upload_status: UploadStatus
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DocumentPageResponse(BaseModel):
    id: UUID
    document_id: UUID
    page_number: int
    extracted_text: Optional[str] = None
    extraction_method: Optional[ExtractionMethod] = None
    status: PageStatus
    model_config = ConfigDict(from_attributes=True)
