import uuid
import enum
from sqlalchemy import String, Numeric, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, TimestampMixin

class RecordType(str, enum.Enum):
    CLASSIFICATION = "classification"
    OCR = "ocr"
    STORAGE = "storage"

class UsageRecord(Base, TimestampMixin):
    __tablename__ = "usage_records"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    record_type: Mapped[RecordType] = mapped_column(SQLEnum(RecordType), nullable=False)
    model_name: Mapped[str | None] = mapped_column(String(128))
    quantity: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    credits_charged: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))  # Not a strict FK to avoid circular deps / allow deletion
    
    user = relationship("User")
