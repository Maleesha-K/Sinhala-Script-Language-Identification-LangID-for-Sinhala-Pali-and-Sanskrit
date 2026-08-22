from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

from app.db.models.user import User
from app.db.models.classification_job import ClassificationJob
from app.db.models.document import Document
from app.db.models.usage_record import UsageRecord, RecordType
from app.dependencies import get_db, get_current_user
from app.schemas.response import BaseResponse, success_response

router = APIRouter(prefix="/usage", tags=["usage"])

class ActivityItem(BaseModel):
    id: UUID
    activity_type: str # "classification" or "ocr"
    name: str
    status: str
    cost: float
    created_at: datetime

class UsageBreakdownResponse(BaseModel):
    credits_balance: float
    activities: List[ActivityItem]

@router.get("/breakdown", response_model=BaseResponse[UsageBreakdownResponse])
async def get_usage_breakdown(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a comprehensive usage breakdown including queued and processed tasks."""
    
    # 1. Fetch Classification Jobs
    jobs_result = await db.execute(
        select(ClassificationJob)
        .where(ClassificationJob.user_id == current_user.id)
        .order_by(ClassificationJob.created_at.desc())
        .limit(100)
    )
    jobs = jobs_result.scalars().all()
    
    # 2. Fetch Documents (OCR)
    docs_result = await db.execute(
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
        .limit(100)
    )
    docs = docs_result.scalars().all()
    
    # 3. Fetch OCR Usage Records (to get cost per document)
    doc_ids = [doc.id for doc in docs]
    ocr_usage = {}
    if doc_ids:
        usage_result = await db.execute(
            select(UsageRecord.job_id, func.sum(UsageRecord.credits_charged).label("total_cost"))
            .where(UsageRecord.job_id.in_(doc_ids), UsageRecord.record_type == RecordType.OCR)
            .group_by(UsageRecord.job_id)
        )
        for row in usage_result.all():
            ocr_usage[row.job_id] = float(row.total_cost)

    # 4. Unify into Activity Items
    activities = []
    
    for job in jobs:
        # Snippet for name
        snippet = job.input_text[:40] + "..." if len(job.input_text) > 40 else job.input_text
        activities.append(ActivityItem(
            id=job.id,
            activity_type="classification",
            name=f"LangID: {snippet}",
            status=job.status.value,
            cost=float(job.credits_charged),
            created_at=job.created_at
        ))
        
    for doc in docs:
        cost = ocr_usage.get(doc.id, 0.0)
        activities.append(ActivityItem(
            id=doc.id,
            activity_type="ocr",
            name=f"OCR: {doc.filename}",
            status=doc.upload_status.value,
            cost=cost,
            created_at=doc.created_at
        ))
        
    # Sort unified list by created_at descending
    activities.sort(key=lambda x: x.created_at, reverse=True)
    
    response_data = UsageBreakdownResponse(
        credits_balance=float(current_user.credits_balance),
        activities=activities
    )
    
    return success_response(data=response_data, message="Usage breakdown retrieved successfully")
