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
            raise AppException(message="Tier not found", status_code=status.HTTP_404_NOT_FOUND)
        
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
            raise AppException(message="Tier not found", status_code=status.HTTP_404_NOT_FOUND)
            
        if tier.price_usd == 0:
            from app.utils.exceptions import BadRequestException
            raise BadRequestException(message="The Free Tier cannot be deleted because it is the default tier for new users.")
        
        await db.delete(tier)
        await db.commit()
        return {"success": True}
        
    async def get_system_config(self, db: AsyncSession):
        result = await db.execute(select(SystemConfig).where(SystemConfig.key == "usd_to_credits"))
        config = result.scalar_one_or_none()
        from app.schemas.admin import SystemConfigResponse, CreditPackageConfig
        
        if not config:
            rate = 100.0
            packages = [
                {"id": "starter", "name": "Student / Starter Pack", "credits": 2500.0, "amount_lkr": 750.00, "popular": False, "description": "Ideal for students and short document experiments."},
                {"id": "standard", "name": "Standard Researcher Pack", "credits": 10000.0, "amount_lkr": 2500.00, "popular": True, "description": "Best value for continuous classification and multi-page OCR."},
                {"id": "institution", "name": "Institutional / Corpus Pack", "credits": 50000.0, "amount_lkr": 10000.00, "popular": False, "description": "High-volume tier for large historical archives and deep datasets."},
            ]
            config = SystemConfig(
                key="usd_to_credits", 
                value={
                    "rate": rate, 
                    "usd_to_credits_rate": rate,
                    "usd_to_lkr_rate": 300.0,
                    "packages": packages
                }
            )
            db.add(config)
            await db.commit()
            await db.refresh(config)
        
        rate = float(config.value.get("rate", config.value.get("usd_to_credits_rate", 100.0)))
        usd_to_lkr = float(config.value.get("usd_to_lkr_rate", 300.0))
        raw_packages = config.value.get("packages")
        
        if not raw_packages:
            raw_packages = [
                {"id": "starter", "name": "Student / Starter Pack", "credits": round(25.0 * rate), "amount_lkr": 750.00, "popular": False, "description": "Ideal for students and short document experiments."},
                {"id": "standard", "name": "Standard Researcher Pack", "credits": round(100.0 * rate), "amount_lkr": 2500.00, "popular": True, "description": "Best value for continuous classification and multi-page OCR."},
                {"id": "institution", "name": "Institutional / Corpus Pack", "credits": round(500.0 * rate), "amount_lkr": 10000.00, "popular": False, "description": "High-volume tier for large historical archives and deep datasets."},
            ]
            
        packages = [CreditPackageConfig(**p) for p in raw_packages]
        return SystemConfigResponse(
            usd_to_credits_rate=rate,
            usd_to_lkr_rate=usd_to_lkr,
            packages=packages
        )
        
    async def update_system_config(self, db: AsyncSession, config_in: SystemConfigUpdate):
        result = await db.execute(select(SystemConfig).where(SystemConfig.key == "usd_to_credits"))
        config = result.scalar_one_or_none()
        from app.schemas.admin import SystemConfigResponse, CreditPackageConfig

        rate = config_in.usd_to_credits_rate
        usd_to_lkr = config_in.usd_to_lkr_rate or 300.0
        
        if config_in.packages:
            raw_packages = [p.model_dump() for p in config_in.packages]
        else:
            raw_packages = [
                {"id": "starter", "name": "Student / Starter Pack", "credits": round(25.0 * rate), "amount_lkr": 750.00, "popular": False, "description": "Ideal for students and short document experiments."},
                {"id": "standard", "name": "Standard Researcher Pack", "credits": round(100.0 * rate), "amount_lkr": 2500.00, "popular": True, "description": "Best value for continuous classification and multi-page OCR."},
                {"id": "institution", "name": "Institutional / Corpus Pack", "credits": round(500.0 * rate), "amount_lkr": 10000.00, "popular": False, "description": "High-volume tier for large historical archives and deep datasets."},
            ]
            
        val = {
            "rate": rate,
            "usd_to_credits_rate": rate,
            "usd_to_lkr_rate": usd_to_lkr,
            "packages": raw_packages
        }
        
        if not config:
            config = SystemConfig(key="usd_to_credits", value=val)
            db.add(config)
        else:
            config.value = val
        
        await db.commit()
        await db.refresh(config)
        
        packages = [CreditPackageConfig(**p) for p in raw_packages]
        return SystemConfigResponse(
            usd_to_credits_rate=rate,
            usd_to_lkr_rate=usd_to_lkr,
            packages=packages
        )

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
            raise AppException(message="Model rate not found", status_code=status.HTTP_404_NOT_FOUND)
            
        update_data = rate_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(rate, field, value)
            
        await db.commit()
        await db.refresh(rate)
        return rate

    async def get_stats(self, db: AsyncSession):
        from sqlalchemy import func
        from app.db.models.user import User
        from app.db.models.subscription import Subscription, SubscriptionStatus
        from app.db.models.classification_job import ClassificationJob, JobStatus
        from app.schemas.admin import AdminStatsResponse

        total_users = await db.scalar(select(func.count()).select_from(User))
        active_subscriptions = await db.scalar(
            select(func.count())
            .select_from(Subscription)
            .join(TierDefinition, Subscription.tier_id == TierDefinition.id)
            .where(Subscription.status == SubscriptionStatus.ACTIVE, TierDefinition.price_usd > 0)
        )
        storage_used = await db.scalar(select(func.coalesce(func.sum(User.storage_used_bytes), 0)))
        active_jobs = await db.scalar(
            select(func.count())
            .select_from(ClassificationJob)
            .where(ClassificationJob.status.in_([JobStatus.QUEUED, JobStatus.PROCESSING]))
        )
        return AdminStatsResponse(
            total_users=total_users or 0,
            active_subscriptions=active_subscriptions or 0,
            storage_used_bytes=int(storage_used or 0),
            active_jobs=active_jobs or 0,
        )

admin_service = AdminService()
