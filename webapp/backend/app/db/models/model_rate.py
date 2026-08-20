import uuid
import enum
from sqlalchemy import String, Boolean, Numeric, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, TimestampMixin

class ModelType(str, enum.Enum):
    CLASSIFICATION = "classification"
    OCR = "ocr"

class ModelRate(Base, TimestampMixin):
    __tablename__ = "model_rates"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_type: Mapped[ModelType] = mapped_column(SQLEnum(ModelType), nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    credits_per_token: Mapped[float] = mapped_column(Numeric(18, 8), default=0.0)
    credits_per_page: Mapped[float] = mapped_column(Numeric(18, 4), default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
