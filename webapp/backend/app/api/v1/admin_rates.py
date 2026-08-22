from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.db.models.user import User, UserRole
from app.db.models.model_rate import ModelRate, ModelType
from app.dependencies import get_db, get_current_user
from app.schemas.response import BaseResponse, success_response

router = APIRouter(prefix="/admin-rates", tags=["admin-rates"])

# Dependency to check for admin
async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return current_user

# Schemas
class ModelRateBase(BaseModel):
    model_type: ModelType
    model_name: str
    credits_per_token: float = Field(default=0.0, ge=0)
    credits_per_page: float = Field(default=0.0, ge=0)
    is_active: bool = True

class ModelRateCreate(ModelRateBase):
    pass

class ModelRateUpdate(BaseModel):
    credits_per_token: Optional[float] = Field(None, ge=0)
    credits_per_page: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None

class ModelRateResponse(ModelRateBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)

@router.get("/available-models", response_model=BaseResponse[List[dict]])
async def list_available_models(
    admin: User = Depends(get_admin_user)
):
    """List all available models in the system (Admin only)"""
    available_models = [
        {"model_name": "sklearn_langid", "model_type": ModelType.CLASSIFICATION.value, "description": "Standard scikit-learn Language ID model"},
        {"model_name": "tesseract", "model_type": ModelType.OCR.value, "description": "Tesseract OCR engine"}
    ]
    return success_response(data=available_models)

@router.get("", response_model=BaseResponse[List[ModelRateResponse]])
async def list_rates(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """List all model rates (Admin only)"""
    result = await db.execute(select(ModelRate).order_by(ModelRate.model_name))
    rates = result.scalars().all()
    return success_response(data=rates)

@router.post("", response_model=BaseResponse[ModelRateResponse], status_code=status.HTTP_201_CREATED)
async def create_rate(
    request: ModelRateCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Create a new model rate (Admin only)"""
    # Check if exists
    result = await db.execute(select(ModelRate).where(ModelRate.model_name == request.model_name))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Rate for this model name already exists")
        
    rate = ModelRate(**request.model_dump())
    db.add(rate)
    await db.commit()
    await db.refresh(rate)
    return success_response(data=rate, message="Model rate created successfully")

@router.put("/{rate_id}", response_model=BaseResponse[ModelRateResponse])
async def update_rate(
    rate_id: UUID,
    request: ModelRateUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Update an existing model rate (Admin only)"""
    result = await db.execute(select(ModelRate).where(ModelRate.id == rate_id))
    rate = result.scalar_one_or_none()
    
    if not rate:
        raise HTTPException(status_code=404, detail="Model rate not found")
        
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rate, key, value)
        
    await db.commit()
    await db.refresh(rate)
    return success_response(data=rate, message="Model rate updated successfully")

@router.delete("/{rate_id}")
async def delete_rate(
    rate_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Delete a model rate (Admin only)"""
    result = await db.execute(select(ModelRate).where(ModelRate.id == rate_id))
    rate = result.scalar_one_or_none()
    
    if not rate:
        raise HTTPException(status_code=404, detail="Model rate not found")
        
    await db.delete(rate)
    await db.commit()
    return success_response(message="Model rate deleted successfully")
