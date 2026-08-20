from app.db.base import Base
from app.db.models.user import User
from app.db.models.tier import TierDefinition
from app.db.models.subscription import Subscription
from app.db.models.system_config import SystemConfig
from app.db.models.model_rate import ModelRate
from app.db.models.usage_record import UsageRecord
from app.db.models.document import Document
from app.db.models.document_page import DocumentPage
from app.db.models.classification_job import ClassificationJob
from app.db.models.classified_segment import ClassifiedSegment
from app.db.models.annotation import Annotation

# This exposes all models for Alembic's env.py
__all__ = [
    "Base",
    "User",
    "TierDefinition",
    "Subscription",
    "SystemConfig",
    "ModelRate",
    "UsageRecord",
    "Document",
    "DocumentPage",
    "ClassificationJob",
    "ClassifiedSegment",
    "Annotation",
]
