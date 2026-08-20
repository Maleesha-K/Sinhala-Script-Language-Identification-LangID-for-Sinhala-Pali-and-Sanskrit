import uuid
import enum
from sqlalchemy import String, BigInteger, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, TimestampMixin

class UploadStatus(str, enum.Enum):
    UPLOADING = "uploading"
    READY = "ready"
    DELETED = "deleted"

class Document(Base, TimestampMixin):
    __tablename__ = "documents"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(128))
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    minio_key: Mapped[str | None] = mapped_column(Text)
    upload_status: Mapped[UploadStatus] = mapped_column(SQLEnum(UploadStatus), default=UploadStatus.UPLOADING, nullable=False)
    
    user = relationship("User")
    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")
