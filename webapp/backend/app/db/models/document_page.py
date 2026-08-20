import uuid
import enum
from sqlalchemy import String, Integer, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, TimestampMixin

class ExtractionMethod(str, enum.Enum):
    PDF_READ = "pdf_read"
    OCR = "ocr"

class PageStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DocumentPage(Base, TimestampMixin):
    __tablename__ = "document_pages"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    extracted_text: Mapped[str | None] = mapped_column(Text)
    extraction_method: Mapped[ExtractionMethod | None] = mapped_column(SQLEnum(ExtractionMethod))
    ocr_model: Mapped[str | None] = mapped_column(String(128))
    minio_page_image_key: Mapped[str | None] = mapped_column(Text)
    status: Mapped[PageStatus] = mapped_column(SQLEnum(PageStatus), default=PageStatus.PENDING, nullable=False)
    
    document = relationship("Document", back_populates="pages")
