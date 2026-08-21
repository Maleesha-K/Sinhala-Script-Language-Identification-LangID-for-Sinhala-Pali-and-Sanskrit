from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List
from app.db.models.user import User
from app.dependencies import get_db, require_admin
from app.schemas.response import BaseResponse, success_response
from app.schemas.admin import (
    TierResponse, TierCreate, TierUpdate,
    SystemConfigResponse, SystemConfigUpdate,
    ModelRateResponse, ModelRateCreate, ModelRateUpdate
)
from app.services.admin_service import admin_service

router = APIRouter(prefix="/admin", tags=["admin"])

# --- Tiers ---
@router.get("/tiers", response_model=BaseResponse[List[TierResponse]])
async def get_tiers(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
) -> dict:
    tiers = await admin_service.get_tiers(db)
    return success_response(data=tiers, message="Tiers retrieved")

@router.post("/tiers", response_model=BaseResponse[TierResponse], status_code=status.HTTP_201_CREATED)
async def create_tier(
    tier_in: TierCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
) -> dict:
    tier = await admin_service.create_tier(db, tier_in)
    return success_response(data=tier, message="Tier created")

@router.put("/tiers/{tier_id}", response_model=BaseResponse[TierResponse])
async def update_tier(
    tier_id: UUID,
    tier_in: TierUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
) -> dict:
    tier = await admin_service.update_tier(db, tier_id, tier_in)
    return success_response(data=tier, message="Tier updated")

# --- System Config ---
@router.get("/config", response_model=BaseResponse[SystemConfigResponse])
async def get_config(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
) -> dict:
    config = await admin_service.get_system_config(db)
    return success_response(data=config, message="System config retrieved")

@router.put("/config", response_model=BaseResponse[SystemConfigResponse])
async def update_config(
    config_in: SystemConfigUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
) -> dict:
    config = await admin_service.update_system_config(db, config_in)
    return success_response(data=config, message="System config updated")

# --- Model Rates ---
@router.get("/model-rates", response_model=BaseResponse[List[ModelRateResponse]])
async def get_model_rates(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
) -> dict:
    rates = await admin_service.get_model_rates(db)
    return success_response(data=rates, message="Model rates retrieved")

@router.post("/model-rates", response_model=BaseResponse[ModelRateResponse], status_code=status.HTTP_201_CREATED)
async def create_model_rate(
    rate_in: ModelRateCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
) -> dict:
    rate = await admin_service.create_model_rate(db, rate_in)
    return success_response(data=rate, message="Model rate created")

@router.put("/model-rates/{rate_id}", response_model=BaseResponse[ModelRateResponse])
async def update_model_rate(
    rate_id: UUID,
    rate_in: ModelRateUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
) -> dict:
    rate = await admin_service.update_model_rate(db, rate_id, rate_in)
    return success_response(data=rate, message="Model rate updated")
