from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class AnnotationCreate(BaseModel):
    segment_id: UUID
    corrected_language: str = Field(..., description="The user's corrected language (e.g., 'sinhala', 'pali', 'sanskrit')")
    comment: Optional[str] = Field(None, description="Optional user comment about the misclassification")

class AnnotationReview(BaseModel):
    is_valid_for_training: bool = Field(..., description="Whether this annotation is approved as training data")

class AnnotationClear(BaseModel):
    annotation_ids: List[UUID] = Field(..., min_length=1, description="Approved annotations to clear from the export table")

class AnnotationClearResponse(BaseModel):
    cleared: int

class AnnotationResponse(BaseModel):
    id: UUID
    segment_id: UUID
    user_id: UUID
    corrected_language: str
    comment: Optional[str]
    admin_reviewed: bool
    reviewed_by: Optional[UUID]
    is_valid_for_training: bool
    created_at: datetime
    reviewed_at: Optional[datetime]
    cleared_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AnnotationAdminResponse(AnnotationResponse):
    original_text: str
    predicted_language: str
    previous_text: Optional[str] = None
    next_text: Optional[str] = None
    user_email: str
    
    class Config:
        from_attributes = True
