"""Database integrity tests.

These exercise the schema directly rather than through HTTP: unique
constraints, NOT NULL columns, foreign keys, enum storage, defaults and
cascade behaviour. They run against the migrated Postgres container, so they
verify what Alembic actually produced rather than what the models declare.
"""
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.db.session import async_session_maker
from app.utils.security import get_password_hash


async def make_user(session, *, email: str | None = None, **overrides):
    """Build and persist a user, returning it."""
    from app.db.models.user import User

    user = User(
        email=email or f"integrity_{uuid.uuid4().hex[:12]}@test.com",
        password_hash=get_password_hash("StrongPass123!"),
        display_name="Integrity User",
        **overrides,
    )
    session.add(user)
    await session.flush()
    return user


async def make_job(session, user_id, **overrides):
    """Build and persist a classification job."""
    from app.db.models.classification_job import ClassificationJob, JobStatus

    job = ClassificationJob(
        user_id=user_id,
        input_text="ශ්‍රී ලංකාව",
        model_name="sklearn_langid",
        segmentation_strategy="sentence",
        status=overrides.pop("status", JobStatus.COMPLETED),
        **overrides,
    )
    session.add(job)
    await session.flush()
    return job


async def make_segment(session, job_id, **overrides):
    """Build and persist a classified segment."""
    from app.db.models.classified_segment import ClassifiedSegment

    segment = ClassifiedSegment(
        job_id=job_id,
        segment_index=overrides.pop("segment_index", 0),
        text=overrides.pop("text", "ශ්‍රී ලංකාව"),
        predicted_language=overrides.pop("predicted_language", "sinhala"),
        confidence=overrides.pop("confidence", 0.9),
        probabilities=overrides.pop(
            "probabilities", {"sinhala": 0.9, "pali": 0.07, "sanskrit": 0.03}
        ),
        start_char_offset=0,
        end_char_offset=10,
        **overrides,
    )
    session.add(segment)
    await session.flush()
    return segment


# --- unique constraints ----------------------------------------------------

@pytest.mark.asyncio
async def test_user_email_is_unique():
    """users.email carries a unique constraint."""
    email = f"dupe_{uuid.uuid4().hex[:10]}@test.com"

    async with async_session_maker() as session:
        await make_user(session, email=email)
        await session.commit()

    with pytest.raises(IntegrityError):
        async with async_session_maker() as session:
            await make_user(session, email=email)
            await session.commit()


@pytest.mark.asyncio
async def test_model_rate_name_is_unique():
    """model_rates.model_name is unique, so a model has one rate."""
    from app.db.models.model_rate import ModelRate, ModelType

    name = f"rate_{uuid.uuid4().hex[:10]}"

    async with async_session_maker() as session:
        session.add(
            ModelRate(
                model_type=ModelType.CLASSIFICATION, model_name=name, credits_per_token=0.1
            )
        )
        await session.commit()

    with pytest.raises(IntegrityError):
        async with async_session_maker() as session:
            session.add(
                ModelRate(
                    model_type=ModelType.OCR, model_name=name, credits_per_page=0.2
                )
            )
            await session.commit()


# --- NOT NULL --------------------------------------------------------------

@pytest.mark.asyncio
async def test_user_requires_a_password_hash():
    """A user cannot be stored without credentials."""
    from app.db.models.user import User

    with pytest.raises(IntegrityError):
        async with async_session_maker() as session:
            session.add(User(email=f"nopw_{uuid.uuid4().hex[:8]}@test.com"))
            await session.commit()


@pytest.mark.asyncio
async def test_model_rate_requires_a_type():
    """model_rates.model_type is NOT NULL.

    This is the constraint that makes POST /admin/model-rates unusable: its
    schema omits model_type, so the insert can never satisfy the column.
    """
    from app.db.models.model_rate import ModelRate

    with pytest.raises(IntegrityError):
        async with async_session_maker() as session:
            session.add(ModelRate(model_name=f"typeless_{uuid.uuid4().hex[:8]}"))
            await session.commit()


@pytest.mark.asyncio
async def test_document_requires_a_size():
    """documents.size_bytes is NOT NULL."""
    from app.db.models.document import Document

    async with async_session_maker() as session:
        user = await make_user(session)
        await session.commit()
        user_id = user.id

    with pytest.raises(IntegrityError):
        async with async_session_maker() as session:
            session.add(Document(user_id=user_id, filename="sizeless.pdf"))
            await session.commit()


# --- foreign keys ----------------------------------------------------------

@pytest.mark.asyncio
async def test_document_requires_an_existing_user():
    """documents.user_id is a foreign key to users."""
    from app.db.models.document import Document

    with pytest.raises(IntegrityError):
        async with async_session_maker() as session:
            session.add(
                Document(
                    user_id=uuid.uuid4(),  # no such user
                    filename="orphan.pdf",
                    size_bytes=10,
                    mime_type="application/pdf",
                )
            )
            await session.commit()


@pytest.mark.asyncio
async def test_classification_job_requires_an_existing_user():
    """classification_jobs.user_id is a foreign key to users."""
    from app.db.models.classification_job import ClassificationJob

    with pytest.raises(IntegrityError):
        async with async_session_maker() as session:
            session.add(
                ClassificationJob(
                    user_id=uuid.uuid4(),
                    input_text="orphan",
                    model_name="sklearn_langid",
                )
            )
            await session.commit()


@pytest.mark.asyncio
async def test_segment_requires_an_existing_job():
    """classified_segments.job_id is a foreign key to classification_jobs."""
    with pytest.raises(IntegrityError):
        async with async_session_maker() as session:
            await make_segment(session, uuid.uuid4())
            await session.commit()


@pytest.mark.asyncio
async def test_annotation_requires_an_existing_segment():
    """annotations.segment_id is a foreign key to classified_segments."""
    from app.db.models.annotation import Annotation

    async with async_session_maker() as session:
        user = await make_user(session)
        await session.commit()
        user_id = user.id

    with pytest.raises(IntegrityError):
        async with async_session_maker() as session:
            session.add(
                Annotation(
                    segment_id=uuid.uuid4(),
                    user_id=user_id,
                    corrected_language="pali",
                )
            )
            await session.commit()


@pytest.mark.asyncio
async def test_document_page_requires_an_existing_document():
    """document_pages.document_id is a foreign key to documents."""
    from app.db.models.document_page import DocumentPage

    with pytest.raises(IntegrityError):
        async with async_session_maker() as session:
            session.add(DocumentPage(document_id=uuid.uuid4(), page_number=1))
            await session.commit()


@pytest.mark.asyncio
async def test_usage_record_requires_an_existing_user():
    """usage_records.user_id is a foreign key to users."""
    from app.db.models.usage_record import RecordType, UsageRecord

    with pytest.raises(IntegrityError):
        async with async_session_maker() as session:
            session.add(
                UsageRecord(
                    user_id=uuid.uuid4(),
                    record_type=RecordType.OCR,
                    quantity=1,
                    credits_charged=1,
                )
            )
            await session.commit()


@pytest.mark.asyncio
async def test_usage_record_job_id_is_not_a_foreign_key():
    """usage_records.job_id is deliberately unconstrained.

    It points at either a classification job or a document, so the model
    leaves it as a bare UUID. A record can therefore outlive the row it
    references, which is why the usage breakdown tolerates missing joins.
    """
    from app.db.models.usage_record import RecordType, UsageRecord

    async with async_session_maker() as session:
        user = await make_user(session)
        record = UsageRecord(
            user_id=user.id,
            record_type=RecordType.OCR,
            quantity=1,
            credits_charged=1,
            job_id=uuid.uuid4(),  # references nothing
        )
        session.add(record)
        await session.commit()  # must not raise
        assert record.id is not None


# --- cascades --------------------------------------------------------------

@pytest.mark.asyncio
async def test_deleting_a_document_deletes_its_pages():
    """Document.pages cascades with delete-orphan."""
    from app.db.models.document import Document, UploadStatus
    from app.db.models.document_page import DocumentPage

    async with async_session_maker() as session:
        user = await make_user(session)
        document = Document(
            user_id=user.id,
            filename="cascade.pdf",
            size_bytes=100,
            mime_type="application/pdf",
            upload_status=UploadStatus.READY,
        )
        session.add(document)
        await session.flush()
        session.add(DocumentPage(document_id=document.id, page_number=1))
        await session.commit()
        document_id = document.id

    async with async_session_maker() as session:
        document = await session.get(Document, document_id)
        await session.delete(document)
        await session.commit()

    async with async_session_maker() as session:
        remaining = await session.execute(
            select(func.count())
            .select_from(DocumentPage)
            .where(DocumentPage.document_id == document_id)
        )
        assert remaining.scalar() == 0


@pytest.mark.asyncio
async def test_deleting_a_job_deletes_its_segments():
    """ClassificationJob.segments cascades with delete-orphan."""
    from app.db.models.classification_job import ClassificationJob
    from app.db.models.classified_segment import ClassifiedSegment

    async with async_session_maker() as session:
        user = await make_user(session)
        job = await make_job(session, user.id)
        await make_segment(session, job.id)
        await session.commit()
        job_id = job.id

    async with async_session_maker() as session:
        job = await session.get(ClassificationJob, job_id)
        await session.delete(job)
        await session.commit()

    async with async_session_maker() as session:
        remaining = await session.execute(
            select(func.count())
            .select_from(ClassifiedSegment)
            .where(ClassifiedSegment.job_id == job_id)
        )
        assert remaining.scalar() == 0


@pytest.mark.asyncio
async def test_deleting_a_segment_deletes_its_annotations():
    """ClassifiedSegment.annotations cascades with delete-orphan."""
    from app.db.models.annotation import Annotation
    from app.db.models.classified_segment import ClassifiedSegment

    async with async_session_maker() as session:
        user = await make_user(session)
        job = await make_job(session, user.id)
        segment = await make_segment(session, job.id)
        session.add(
            Annotation(
                segment_id=segment.id, user_id=user.id, corrected_language="pali"
            )
        )
        await session.commit()
        segment_id = segment.id

    async with async_session_maker() as session:
        segment = await session.get(ClassifiedSegment, segment_id)
        await session.delete(segment)
        await session.commit()

    async with async_session_maker() as session:
        remaining = await session.execute(
            select(func.count())
            .select_from(Annotation)
            .where(Annotation.segment_id == segment_id)
        )
        assert remaining.scalar() == 0


@pytest.mark.asyncio
async def test_user_with_documents_cannot_be_deleted():
    """documents.user_id has no ON DELETE rule, so the parent is pinned.

    Deleting a user with content raises rather than silently orphaning or
    removing it; account deletion would need to clear these rows first.
    """
    from app.db.models.document import Document, UploadStatus
    from app.db.models.user import User

    async with async_session_maker() as session:
        user = await make_user(session)
        session.add(
            Document(
                user_id=user.id,
                filename="pinned.pdf",
                size_bytes=10,
                mime_type="application/pdf",
                upload_status=UploadStatus.READY,
            )
        )
        await session.commit()
        user_id = user.id

    with pytest.raises((IntegrityError, DBAPIError)):
        async with async_session_maker() as session:
            user = await session.get(User, user_id)
            await session.delete(user)
            await session.commit()


# --- defaults and enums ----------------------------------------------------

@pytest.mark.asyncio
async def test_user_defaults():
    """A new user starts as an active, zero-usage regular account."""
    from app.db.models.user import UserRole

    async with async_session_maker() as session:
        user = await make_user(session)
        await session.commit()
        await session.refresh(user)

        assert user.role == UserRole.USER
        assert user.is_active is True
        assert user.storage_used_bytes == 0
        assert float(user.credits_balance) == 0.0
        assert user.created_at is not None
        assert user.updated_at is not None


@pytest.mark.asyncio
async def test_job_defaults_to_queued():
    """A job with no explicit status is queued."""
    from app.db.models.classification_job import ClassificationJob, JobStatus

    async with async_session_maker() as session:
        user = await make_user(session)
        job = ClassificationJob(
            user_id=user.id, input_text="text", model_name="sklearn_langid"
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)

        assert job.status == JobStatus.QUEUED
        assert job.total_tokens == 0
        assert float(job.credits_charged) == 0.0
        assert job.segmentation_strategy == "sentence"
        assert job.completed_at is None


@pytest.mark.asyncio
async def test_annotation_defaults_to_unreviewed():
    """A correction starts outside the training set."""
    from app.db.models.annotation import Annotation

    async with async_session_maker() as session:
        user = await make_user(session)
        job = await make_job(session, user.id)
        segment = await make_segment(session, job.id)
        annotation = Annotation(
            segment_id=segment.id, user_id=user.id, corrected_language="pali"
        )
        session.add(annotation)
        await session.commit()
        await session.refresh(annotation)

        assert annotation.admin_reviewed is False
        assert annotation.is_valid_for_training is False
        assert annotation.reviewed_by is None
        assert annotation.reviewed_at is None


@pytest.mark.asyncio
async def test_enum_columns_round_trip():
    """Enum values survive a write and read as Python enums."""
    from app.db.models.document import Document, UploadStatus
    from app.db.models.user import User, UserRole

    async with async_session_maker() as session:
        user = await make_user(session, role=UserRole.ADMIN)
        document = Document(
            user_id=user.id,
            filename="enum.pdf",
            size_bytes=1,
            mime_type="application/pdf",
            upload_status=UploadStatus.DELETED,
        )
        session.add(document)
        await session.commit()
        user_id, document_id = user.id, document.id

    async with async_session_maker() as session:
        stored_user = await session.get(User, user_id)
        stored_document = await session.get(Document, document_id)

        assert stored_user.role is UserRole.ADMIN
        assert stored_document.upload_status is UploadStatus.DELETED


@pytest.mark.asyncio
async def test_segment_probabilities_round_trip_as_json():
    """JSONB keeps the probability map intact, not stringified."""
    probabilities = {"sinhala": 0.72, "pali": 0.21, "sanskrit": 0.07}

    async with async_session_maker() as session:
        user = await make_user(session)
        job = await make_job(session, user.id)
        segment = await make_segment(session, job.id, probabilities=probabilities)
        await session.commit()
        segment_id = segment.id

    async with async_session_maker() as session:
        from app.db.models.classified_segment import ClassifiedSegment

        stored = await session.get(ClassifiedSegment, segment_id)
        assert stored.probabilities == probabilities
        assert stored.probabilities["sinhala"] == pytest.approx(0.72)


@pytest.mark.asyncio
async def test_timestamps_update_on_write():
    """updated_at advances when a row changes, created_at does not."""
    async with async_session_maker() as session:
        user = await make_user(session)
        await session.commit()
        await session.refresh(user)
        user_id = user.id
        created_at, first_updated = user.created_at, user.updated_at

    async with async_session_maker() as session:
        from app.db.models.user import User

        stored = await session.get(User, user_id)
        stored.display_name = "Renamed"
        await session.commit()
        await session.refresh(stored)

        assert stored.created_at == created_at
        assert stored.updated_at >= first_updated


@pytest.mark.asyncio
async def test_numeric_precision_is_preserved():
    """credits_per_token keeps 8 decimal places, as declared."""
    from app.db.models.model_rate import ModelRate, ModelType

    async with async_session_maker() as session:
        rate = ModelRate(
            model_type=ModelType.CLASSIFICATION,
            model_name=f"precise_{uuid.uuid4().hex[:10]}",
            credits_per_token=0.00012345,
        )
        session.add(rate)
        await session.commit()
        rate_id = rate.id

    async with async_session_maker() as session:
        stored = await session.get(ModelRate, rate_id)
        assert float(stored.credits_per_token) == pytest.approx(0.00012345)


@pytest.mark.asyncio
async def test_system_config_is_keyed_by_string():
    """system_config uses its key as the primary key."""
    from app.db.models.system_config import SystemConfig

    key = f"test_key_{uuid.uuid4().hex[:8]}"

    async with async_session_maker() as session:
        session.add(SystemConfig(key=key, value={"rate": 100.0}))
        await session.commit()

    with pytest.raises(IntegrityError):
        async with async_session_maker() as session:
            session.add(SystemConfig(key=key, value={"rate": 200.0}))
            await session.commit()


# --- migrations ------------------------------------------------------------

@pytest.mark.asyncio
async def test_expected_tables_exist():
    """Alembic produced every table the models expect."""
    from sqlalchemy import text

    expected = {
        "users",
        "documents",
        "document_pages",
        "classification_jobs",
        "classified_segments",
        "annotations",
        "usage_records",
        "subscriptions",
        "tier_definitions",
        "model_rates",
        "system_config",
    }

    async with async_session_maker() as session:
        result = await session.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public'"
            )
        )
        actual = {row[0] for row in result.all()}

    assert expected <= actual, f"missing tables: {expected - actual}"


@pytest.mark.asyncio
async def test_completed_at_is_timezone_aware():
    """Timestamps are stored with a timezone, so comparisons are unambiguous."""
    from app.db.models.classification_job import ClassificationJob

    async with async_session_maker() as session:
        user = await make_user(session)
        job = await make_job(
            session, user.id, completed_at=datetime.now(timezone.utc)
        )
        await session.commit()
        job_id = job.id

    async with async_session_maker() as session:
        stored = await session.get(ClassificationJob, job_id)
        assert stored.completed_at.tzinfo is not None
        assert stored.created_at.tzinfo is not None
