from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.db.models.tier import TierDefinition
from app.db.models.system_config import SystemConfig
from app.db.models.model_rate import ModelRate
from app.schemas.admin import TierCreate, TierUpdate, SystemConfigUpdate, ModelRateCreate, ModelRateUpdate
from app.utils.exceptions import AppException
from fastapi import status

class AdminService:
    async def get_tiers(self, db: AsyncSession):
        result = await db.execute(select(TierDefinition))
        return result.scalars().all()

    async def create_tier(self, db: AsyncSession, tier_in: TierCreate):
        tier = TierDefinition(**tier_in.model_dump())
        db.add(tier)
        await db.commit()
        await db.refresh(tier)
        return tier

    async def update_tier(self, db: AsyncSession, tier_id: UUID, tier_in: TierUpdate):
        result = await db.execute(select(TierDefinition).where(TierDefinition.id == tier_id))
        tier = result.scalar_one_or_none()
        if not tier:
            raise AppException(status_code=status.HTTP_404_NOT_FOUND, detail="Tier not found")
        
        update_data = tier_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tier, field, value)
            
        await db.commit()
        await db.refresh(tier)
        return tier
        
    async def delete_tier(self, db: AsyncSession, tier_id: UUID):
        result = await db.execute(select(TierDefinition).where(TierDefinition.id == tier_id))
        tier = result.scalar_one_or_none()
        if not tier:
            raise AppException(status_code=status.HTTP_404_NOT_FOUND, detail="Tier not found")
            
        if tier.price_usd == 0:
            from app.utils.exceptions import BadRequestException
            raise BadRequestException(message="The Free Tier cannot be deleted because it is the default tier for new users.")
        
        await db.delete(tier)
        await db.commit()
        return {"success": True}
        
    async def get_system_config(self, db: AsyncSession):
        result = await db.execute(select(SystemConfig).where(SystemConfig.key == "usd_to_credits"))
        config = result.scalar_one_or_none()
        if not config:
            # Create a default config if none exists
            config = SystemConfig(key="usd_to_credits", value={"rate": 100.0})
            db.add(config)
            await db.commit()
            await db.refresh(config)
            
        from app.schemas.admin import SystemConfigResponse
        return SystemConfigResponse(usd_to_credits_rate=config.value.get("rate", 100.0))
        
    async def update_system_config(self, db: AsyncSession, config_in: SystemConfigUpdate):
        result = await db.execute(select(SystemConfig).where(SystemConfig.key == "usd_to_credits"))
        config = result.scalar_one_or_none()
        if not config:
            config = SystemConfig(key="usd_to_credits", value={"rate": config_in.usd_to_credits_rate})
            db.add(config)
        else:
            config.value = {"rate": config_in.usd_to_credits_rate}
        
        await db.commit()
        from app.schemas.admin import SystemConfigResponse
        return SystemConfigResponse(usd_to_credits_rate=config.value.get("rate", 100.0))

    async def get_model_rates(self, db: AsyncSession):
        result = await db.execute(select(ModelRate))
        return result.scalars().all()

    async def create_model_rate(self, db: AsyncSession, rate_in: ModelRateCreate):
        rate = ModelRate(**rate_in.model_dump())
        db.add(rate)
        await db.commit()
        await db.refresh(rate)
        return rate
        
    async def update_model_rate(self, db: AsyncSession, rate_id: UUID, rate_in: ModelRateUpdate):
        result = await db.execute(select(ModelRate).where(ModelRate.id == rate_id))
        rate = result.scalar_one_or_none()
        if not rate:
            raise AppException(status_code=status.HTTP_404_NOT_FOUND, detail="Model rate not found")
            
        update_data = rate_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(rate, field, value)
            
        await db.commit()
        await db.refresh(rate)
        return rate

admin_service = AdminService()
