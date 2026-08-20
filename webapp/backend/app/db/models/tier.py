import uuid
from sqlalchemy import String, Boolean, Numeric, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, TimestampMixin

class TierDefinition(Base, TimestampMixin):
    __tablename__ = "tier_definitions"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    price_usd: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    included_credits: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    ocr_pages_included: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    subscriptions = relationship("Subscription", back_populates="tier")
