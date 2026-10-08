import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Integer, Numeric, Text, ForeignKey, Enum as SQLEnum, DateTime, Boolean, false
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, TimestampMixin

class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    # Stopped by the user; segments classified before the stop are kept.
    CANCELLED = "cancelled"

class ClassificationJob(Base, TimestampMixin):
    __tablename__ = "classification_jobs"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), index=True)
    # Set on the per-page jobs queued by a document's OCR run.
    page_number: Mapped[int | None] = mapped_column(Integer)
    input_text: Mapped[str | None] = mapped_column(Text)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    segmentation_strategy: Mapped[str] = mapped_column(String(50), default="sentence", server_default="sentence")
    status: Mapped[JobStatus] = mapped_column(SQLEnum(JobStatus), default=JobStatus.QUEUED, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    credits_charged: Mapped[float] = mapped_column(Numeric(18, 4), default=0.0, nullable=False)
    result_minio_key: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Why a failed job failed, shown to the user.
    error_message: Mapped[str | None] = mapped_column(Text)
    # Set by the cancel endpoint while the job runs; the worker stops at its
    # next batch and marks the job CANCELLED.
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false(), nullable=False)
    
    user = relationship("User")
    document = relationship("Document")
    segments = relationship("ClassifiedSegment", back_populates="job", cascade="all, delete-orphan")
