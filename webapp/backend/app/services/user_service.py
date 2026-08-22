import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.utils.security import get_password_hash
from app.utils.exceptions import NotFoundException, BadRequestException

class UserService:
    async def get_by_id(self, db: AsyncSession, user_id: uuid.UUID) -> User | None:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()
        
    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalars().first()
        
    async def create_user(self, db: AsyncSession, user_in: UserCreate) -> User:
        user = await self.get_by_email(db, email=user_in.email)
        if user:
            raise BadRequestException(message="A user with this email already exists.")
            
        hashed_password = get_password_hash(user_in.password)
        
        # Get or create Free Tier
        from app.db.models.tier import TierDefinition
        result = await db.execute(select(TierDefinition).where(TierDefinition.price_usd == 0))
        free_tier = result.scalar_one_or_none()
        
        if not free_tier:
            free_tier = TierDefinition(
                name="Free Tier",
                price_usd=0,
                included_credits=1000,
                ocr_pages_included=50,
                is_active=True
            )
            db.add(free_tier)
            await db.commit()
            await db.refresh(free_tier)
            
        db_user = User(
            email=user_in.email,
            password_hash=hashed_password,
            display_name=user_in.display_name,
            credits_balance=free_tier.included_credits,
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user
        
    async def update_user(self, db: AsyncSession, user_id: uuid.UUID, user_in: UserUpdate) -> User:
        user = await self.get_by_id(db, user_id)
        if not user:
            raise NotFoundException(item="User")
            
        update_data = user_in.model_dump(exclude_unset=True)
        if "password" in update_data:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["password_hash"] = hashed_password
            
        for field, value in update_data.items():
            setattr(user, field, value)
            
        await db.commit()
        await db.refresh(user)
        return user

user_service = UserService()
