from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any

from app.db.models.user import User
from app.db.models.classification_job import ClassificationJob, JobStatus
from app.db.models.classified_segment import ClassifiedSegment
from app.dependencies import get_db, get_current_user
from app.schemas.response import BaseResponse, success_response
from app.workers.tasks.classification_tasks import process_classification_job
from pydantic import BaseModel, Field

router = APIRouter(prefix="/classification", tags=["classification"])

class JobCreateRequest(BaseModel):
    input_text: str = Field(..., min_length=1)
    segmentation_strategy: str = Field("sentence", pattern="^(sentence|paragraph|full_text|auto)$")

class SegmentResponse(BaseModel):
    id: UUID
    segment_index: int
    text: str
    predicted_language: str
    confidence: float
    probabilities: Dict[str, float]
    start_char_offset: int
    end_char_offset: int

class JobResponse(BaseModel):
    id: UUID
    status: JobStatus
    segmentation_strategy: str
    total_tokens: int
    created_at: datetime
    completed_at: Optional[datetime]
    segments: Optional[List[SegmentResponse]] = None

@router.post("/jobs", response_model=BaseResponse[JobResponse], status_code=status.HTTP_201_CREATED)
async def create_classification_job(
    request: JobCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit text for language classification."""
    
    # 1. Deduct credits logic (Mocked for now, assuming sufficient credits)
    # 2. Create Job
    job = ClassificationJob(
        user_id=current_user.id,
        input_text=request.input_text,
        model_name="sklearn_langid",
        segmentation_strategy=request.segmentation_strategy,
        status=JobStatus.QUEUED
    )
    
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    # 3. Queue celery task
    process_classification_job.delay(str(job.id))
    
    return success_response(
        data={
            "id": job.id,
            "status": job.status,
            "segmentation_strategy": job.segmentation_strategy,
            "total_tokens": job.total_tokens,
            "created_at": job.created_at,
            "completed_at": job.completed_at
        },
        message="Classification job started"
    )

@router.get("/jobs/{job_id}", response_model=BaseResponse[JobResponse])
async def get_classification_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the status and results of a classification job."""
    
    result = await db.execute(select(ClassificationJob).where(ClassificationJob.id == job_id, ClassificationJob.user_id == current_user.id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    response_data = {
        "id": job.id,
        "status": job.status,
        "segmentation_strategy": job.segmentation_strategy,
        "total_tokens": job.total_tokens,
        "created_at": job.created_at,
        "completed_at": job.completed_at,
    }
    
    if job.status == JobStatus.COMPLETED:
        # Fetch segments
        segments_result = await db.execute(
            select(ClassifiedSegment)
            .where(ClassifiedSegment.job_id == job.id)
            .order_by(ClassifiedSegment.segment_index)
        )
        segments = segments_result.scalars().all()
        response_data["segments"] = [
            {
                "id": s.id,
                "segment_index": s.segment_index,
                "text": s.text,
                "predicted_language": s.predicted_language,
                "confidence": float(s.confidence),
                "probabilities": s.probabilities,
                "start_char_offset": s.start_char_offset,
                "end_char_offset": s.end_char_offset
            } for s in segments
        ]
        
    return success_response(data=response_data)
