from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from uuid import UUID
from datetime import datetime, timezone
from typing import List, Optional

from app.db.models.user import User
from app.db.models.annotation import Annotation
from app.db.models.classified_segment import ClassifiedSegment
from app.dependencies import get_db, get_current_user, require_admin
from app.schemas.response import BaseResponse, success_response
from app.schemas.annotation import AnnotationCreate, AnnotationReview, AnnotationResponse, AnnotationAdminResponse

router = APIRouter(prefix="/annotations", tags=["annotations"])

@router.post("", response_model=BaseResponse[AnnotationResponse], status_code=status.HTTP_201_CREATED)
async def create_annotation(
    request: AnnotationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Users submit a correction (annotation) for a misclassified segment.
    """
    # Verify the segment exists
    result = await db.execute(select(ClassifiedSegment).where(ClassifiedSegment.id == request.segment_id))
    segment = result.scalar_one_or_none()
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
        
    # Check if user already annotated this segment
    existing = await db.execute(select(Annotation).where(
        Annotation.segment_id == request.segment_id,
        Annotation.user_id == current_user.id
    ))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="You have already submitted a correction for this segment")
        
    annotation = Annotation(
        segment_id=request.segment_id,
        user_id=current_user.id,
        corrected_language=request.corrected_language.lower(),
        comment=request.comment
    )
    
    db.add(annotation)
    await db.commit()
    await db.refresh(annotation)
    
    return success_response(data=AnnotationResponse.model_validate(annotation), message="Correction submitted successfully")

@router.get("", response_model=BaseResponse[List[AnnotationAdminResponse]])
async def get_annotations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    pending_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Admin: Get list of annotations (queue for review).
    """
    query = select(Annotation).options(selectinload(Annotation.segment), selectinload(Annotation.user))
    
    if pending_only:
        query = query.where(Annotation.admin_reviewed == False)
        
    query = query.order_by(Annotation.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    annotations = result.scalars().all()
    
    data = []
    for ann in annotations:
        ann_dict = AnnotationResponse.model_validate(ann).model_dump()
        ann_dict["original_text"] = ann.segment.text
        ann_dict["predicted_language"] = ann.segment.predicted_language
        ann_dict["user_email"] = ann.user.email
        data.append(AnnotationAdminResponse(**ann_dict))
        
    return success_response(data=data)

@router.put("/{annotation_id}/review", response_model=BaseResponse[AnnotationResponse])
async def review_annotation(
    annotation_id: UUID,
    request: AnnotationReview,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Admin: Mark an annotation as reviewed and specify if it's valid for training.
    """
    result = await db.execute(select(Annotation).where(Annotation.id == annotation_id))
    annotation = result.scalar_one_or_none()
    
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")
        
    annotation.admin_reviewed = True
    annotation.reviewed_by = admin_user.id
    annotation.is_valid_for_training = request.is_valid_for_training
    annotation.reviewed_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(annotation)
    
    return success_response(data=AnnotationResponse.model_validate(annotation), message="Annotation reviewed")
