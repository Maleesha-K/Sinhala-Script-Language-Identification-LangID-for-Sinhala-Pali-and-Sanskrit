from fastapi import APIRouter, Depends, Query, status
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
from app.utils.exceptions import NotFoundException, BadRequestException
from app.workers.tasks.classification_tasks import (
    process_classification_job, estimate_tokens, split_segments,
)
from app.utils.events import segment_payload
from app.services.credit_service import credit_service
from app.ml.registry import MODELS, BASELINE_MODEL, list_models
from pydantic import BaseModel, Field

router = APIRouter(prefix="/classification", tags=["classification"])

class JobCreateRequest(BaseModel):
    input_text: str = Field(..., min_length=1)
    segmentation_strategy: str = Field("sentence", pattern="^(sentence|paragraph|full_text|auto)$")
    model_name: str = Field(BASELINE_MODEL, description="Classification model id")


class ModelInfoResponse(BaseModel):
    id: str
    label: str
    description: str
    family: str
    is_baseline: bool
    available: bool
    correction_languages: List[str]

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
    model_name: str
    segmentation_strategy: str
    total_tokens: int
    created_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str] = None
    document_id: Optional[UUID] = None
    page_number: Optional[int] = None
    # Classified so far / in total, while the job runs (total unknown while queued).
    done: Optional[int] = None
    total: Optional[int] = None
    segments: Optional[List[SegmentResponse]] = None

@router.post("/jobs", response_model=BaseResponse[JobResponse], status_code=status.HTTP_201_CREATED)
async def create_classification_job(
    request: JobCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit text for language classification."""
    
    if request.model_name not in MODELS:
        raise BadRequestException(
            f"Unknown model '{request.model_name}'. Available: {', '.join(sorted(MODELS))}"
        )

    # Credits are charged by the worker once the text is segmented; reject up
    # front when the balance cannot cover the estimate so the job does not just
    # fail in the background.
    estimated_cost = await credit_service.estimate_classification_cost(
        db, request.model_name, estimate_tokens(request.input_text)
    )
    if current_user.credits_balance < estimated_cost:
        raise BadRequestException(
            f"Insufficient credits: this text needs about {float(estimated_cost):.4f} credits "
            f"but your balance is {float(current_user.credits_balance):.4f}. Please top up."
        )

    job = ClassificationJob(
        user_id=current_user.id,
        input_text=request.input_text,
        model_name=request.model_name,
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
            "model_name": job.model_name,
            "segmentation_strategy": job.segmentation_strategy,
            "total_tokens": job.total_tokens,
            "created_at": job.created_at,
            "completed_at": job.completed_at
        },
        message="Classification job started"
    )

@router.get("/jobs", response_model=BaseResponse[List[JobResponse]])
async def list_classification_jobs(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List the current user's most recent classification jobs (without segments)."""
    result = await db.execute(
        select(ClassificationJob)
        # Per-page jobs of a document are shown on the document, not here.
        .where(ClassificationJob.user_id == current_user.id, ClassificationJob.page_number.is_(None))
        .order_by(ClassificationJob.created_at.desc())
        .limit(limit)
    )
    jobs = result.scalars().all()
    return success_response(data=[
        {
            "id": job.id,
            "status": job.status,
            "model_name": job.model_name,
            "segmentation_strategy": job.segmentation_strategy,
            "total_tokens": job.total_tokens,
            "created_at": job.created_at,
            "completed_at": job.completed_at,
        } for job in jobs
    ])

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
        raise NotFoundException(item="Job")
        
    response_data = {
        "id": job.id,
        "status": job.status,
        "model_name": job.model_name,
        "segmentation_strategy": job.segmentation_strategy,
        "total_tokens": job.total_tokens,
        "created_at": job.created_at,
        "completed_at": job.completed_at,
    }
    
    response_data.update(
        error_message=job.error_message,
        document_id=job.document_id,
        page_number=job.page_number,
    )

    # Segments are saved in batches while the job runs, so return what exists.
    segments_result = await db.execute(
        select(ClassifiedSegment)
        .where(ClassifiedSegment.job_id == job.id)
        .order_by(ClassifiedSegment.segment_index)
    )
    response_data["segments"] = [segment_payload(s) for s in segments_result.scalars().all()]
    response_data["done"] = len(response_data["segments"])
    if job.status == JobStatus.PROCESSING:
        response_data["total"] = len(split_segments(job.input_text or "", job.segmentation_strategy))
    elif job.status == JobStatus.COMPLETED:
        response_data["total"] = response_data["done"]

    return success_response(data=response_data)


@router.get("/models", response_model=BaseResponse[List[ModelInfoResponse]])
async def get_available_models(current_user: User = Depends(get_current_user)):
    """List the classification models a user can choose between."""
    return success_response(data=list_models())
