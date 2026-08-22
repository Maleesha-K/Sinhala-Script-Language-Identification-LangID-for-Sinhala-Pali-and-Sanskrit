from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from decimal import Decimal
import uuid

from app.db.models.user import User
from app.db.models.model_rate import ModelRate, ModelType
from app.db.models.usage_record import UsageRecord, RecordType
from app.db.models.classification_job import ClassificationJob
from app.db.models.document import Document

class CreditService:
    async def get_or_create_rate(self, db: AsyncSession, model_name: str, model_type: ModelType, default_credits_per_token: float = 0.0, default_credits_per_page: float = 0.0) -> ModelRate:
        """Fetch the rate for a model, or create a default one if it doesn't exist."""
        result = await db.execute(select(ModelRate).where(ModelRate.model_name == model_name))
        rate = result.scalar_one_or_none()
        
        if not rate:
            rate = ModelRate(
                model_name=model_name,
                model_type=model_type,
                credits_per_token=default_credits_per_token,
                credits_per_page=default_credits_per_page,
                is_active=True
            )
            db.add(rate)
            await db.commit()
            await db.refresh(rate)
            
        return rate

    async def charge_classification(self, db: AsyncSession, user_id: uuid.UUID, job_id: uuid.UUID, model_name: str, tokens: int) -> bool:
        """Charges a user for a classification job based on the number of tokens."""
        # Get rate (default to 0.001 per token if not set)
        rate = await self.get_or_create_rate(
            db, model_name, ModelType.CLASSIFICATION, default_credits_per_token=0.001
        )
        
        if not rate.is_active:
            raise ValueError(f"Model {model_name} is currently inactive.")
            
        cost = Decimal(tokens) * Decimal(rate.credits_per_token)
        
        # Check balance
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            return False
            
        if user.credits_balance < cost:
            return False
            
        # Deduct credits
        user.credits_balance -= cost
        
        # Update job
        await db.execute(
            update(ClassificationJob)
            .where(ClassificationJob.id == job_id)
            .values(credits_charged=cost)
        )
        
        # Record usage
        usage = UsageRecord(
            user_id=user_id,
            record_type=RecordType.CLASSIFICATION,
            model_name=model_name,
            quantity=tokens,
            credits_charged=cost,
            job_id=job_id
        )
        db.add(usage)
        await db.commit()
        return True

    async def charge_ocr_page(self, db: AsyncSession, user_id: uuid.UUID, document_id: uuid.UUID, model_name: str, num_pages: int = 1) -> bool:
        """Charges a user for OCR pages."""
        # Get rate (default to 0.1 per page if not set)
        rate = await self.get_or_create_rate(
            db, model_name, ModelType.OCR, default_credits_per_page=0.1
        )
        
        if not rate.is_active:
            raise ValueError(f"Model {model_name} is currently inactive.")
            
        cost = Decimal(num_pages) * Decimal(rate.credits_per_page)
        
        # Check balance
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            return False
            
        if user.credits_balance < cost:
            return False
            
        # Deduct credits
        user.credits_balance -= cost
        
        # Record usage
        usage = UsageRecord(
            user_id=user_id,
            record_type=RecordType.OCR,
            model_name=model_name,
            quantity=num_pages,
            credits_charged=cost,
            job_id=document_id  # Using document_id in the job_id field for relation
        )
        db.add(usage)
        await db.commit()
        return True

credit_service = CreditService()
