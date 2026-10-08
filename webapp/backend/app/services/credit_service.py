from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from decimal import Decimal
import uuid

from app.db.models.user import User
from app.db.models.model_rate import ModelRate, ModelType
from app.db.models.usage_record import UsageRecord, RecordType
from app.db.models.classification_job import ClassificationJob
from app.db.models.document import Document

# Charged when an admin has not configured a rate for the model yet.
DEFAULT_CREDITS_PER_TOKEN = 0.001
DEFAULT_CREDITS_PER_PAGE = 0.1

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

    async def estimate_classification_cost(self, db: AsyncSession, model_name: str, tokens: int) -> Decimal:
        """Cost of classifying `tokens` tokens, without creating a rate row."""
        result = await db.execute(select(ModelRate).where(ModelRate.model_name == model_name))
        rate = result.scalar_one_or_none()
        if rate is not None and not rate.is_active:
            from app.utils.exceptions import BadRequestException
            raise BadRequestException(message=f"Model {model_name} is currently disabled by an administrator.")
        per_token = rate.credits_per_token if rate is not None else DEFAULT_CREDITS_PER_TOKEN
        return Decimal(tokens) * Decimal(str(per_token))

    async def charge_classification(self, db: AsyncSession, user_id: uuid.UUID, job_id: uuid.UUID, model_name: str, tokens: int) -> bool:
        """Charges a user for a classification job based on the number of tokens."""
        # Get rate (default to 0.001 per token if not set)
        rate = await self.get_or_create_rate(
            db, model_name, ModelType.CLASSIFICATION, default_credits_per_token=DEFAULT_CREDITS_PER_TOKEN
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
            db, model_name, ModelType.OCR, default_credits_per_page=DEFAULT_CREDITS_PER_PAGE
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



    async def _refund(
        self, db: AsyncSession, user_id: uuid.UUID, ref_id: uuid.UUID,
        record_type: RecordType, fraction: Decimal = Decimal(1),
    ) -> Decimal:
        """Return `fraction` of everything charged under `ref_id`.

        A negative usage record is written rather than deleting the charge, so
        the history stays auditable and the total nets out.
        """
        from sqlalchemy import func
        result = await db.execute(
            select(func.coalesce(func.sum(UsageRecord.credits_charged), 0))
            .where(UsageRecord.job_id == ref_id, UsageRecord.record_type == record_type)
        )
        amount = (Decimal(result.scalar_one()) * fraction).quantize(Decimal("0.0001"))
        if amount <= 0:
            return Decimal(0)

        user_result = await db.execute(select(User).where(User.id == user_id).with_for_update())
        user = user_result.scalar_one_or_none()
        if not user:
            return Decimal(0)

        user.credits_balance += amount
        db.add(UsageRecord(
            user_id=user_id,
            record_type=record_type,
            model_name="refund",
            quantity=0,
            credits_charged=-amount,
            job_id=ref_id
        ))
        await db.commit()
        return amount

    async def refund_ocr(
        self, db: AsyncSession, user_id: uuid.UUID, document_id: uuid.UUID, fraction: Decimal = Decimal(1)
    ) -> Decimal:
        """Return the OCR charge of a document, or `fraction` of it when only
        some pages failed."""
        return await self._refund(db, user_id, document_id, RecordType.OCR, fraction)

    async def refund_classification(
        self, db: AsyncSession, user_id: uuid.UUID, job_id: uuid.UUID, fraction: Decimal = Decimal(1)
    ) -> Decimal:
        """Return a classification job's charge after it failed, or `fraction`
        of it for the part a cancelled job did not classify."""
        refunded = await self._refund(db, user_id, job_id, RecordType.CLASSIFICATION, fraction)
        if refunded:
            await db.execute(
                update(ClassificationJob)
                .where(ClassificationJob.id == job_id)
                .values(credits_charged=ClassificationJob.credits_charged - refunded)
            )
            await db.commit()
        return refunded

credit_service = CreditService()
