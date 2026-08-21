from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.db.models.document import UploadStatus

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
