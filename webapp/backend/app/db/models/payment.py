import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Numeric, ForeignKey, Enum as SQLEnum, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, TimestampMixin

class PaymentGateway(str, enum.Enum):
    PAYHERE = "payhere"
    MANUAL = "manual"

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentTransaction(Base, TimestampMixin):
    __tablename__ = "payment_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    gateway: Mapped[PaymentGateway] = mapped_column(
        SQLEnum(PaymentGateway, values_callable=lambda x: [e.value for e in x]), 
        default=PaymentGateway.PAYHERE, 
        nullable=False
    )
    order_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    payhere_payment_id: Mapped[str | None] = mapped_column(String(64), unique=True, index=True, nullable=True)
    package_name: Mapped[str] = mapped_column(String(128), nullable=False)
    amount_lkr: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="LKR", nullable=False)
    credits_amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(PaymentStatus, values_callable=lambda x: [e.value for e in x]), 
        default=PaymentStatus.PENDING, 
        nullable=False, 
        index=True
    )
    payment_method: Mapped[str | None] = mapped_column(String(64), nullable=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSON, default=dict)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user = relationship("User", back_populates="payments")
