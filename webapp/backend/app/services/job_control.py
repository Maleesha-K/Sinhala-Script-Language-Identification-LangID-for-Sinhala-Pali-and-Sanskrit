"""Cancelling classification jobs and document processing.

Cancelling is cooperative: work that has not started is cancelled at once;
running work gets `cancel_requested` and the worker stops at its next
checkpoint (the next batch of segments, or the next page), keeping what it
has saved and refunding the rest.
"""

from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.classification_job import ClassificationJob, JobStatus
from app.db.models.document import Document, UploadStatus
from app.db.models.document_page import DocumentPage
from app.utils.events import document_channel, job_channel, job_payload, publish

ACTIVE_JOB_STATUSES = (JobStatus.QUEUED, JobStatus.PROCESSING)


async def cancel_job(db: AsyncSession, job: ClassificationJob) -> None:
    """Cancel a queued or running job and publish the change."""
    now = datetime.now(timezone.utc)
    # Conditional updates, so a worker changing the status meanwhile wins cleanly.
    queued = await db.execute(
        update(ClassificationJob)
        .where(ClassificationJob.id == job.id, ClassificationJob.status == JobStatus.QUEUED)
        .values(status=JobStatus.CANCELLED, cancel_requested=True, completed_at=now)
    )
    if queued.rowcount == 0:
        await db.execute(
            update(ClassificationJob)
            .where(ClassificationJob.id == job.id, ClassificationJob.status == JobStatus.PROCESSING)
            .values(cancel_requested=True)
        )
    await db.commit()
    await db.refresh(job)

    stopped = job.status == JobStatus.CANCELLED
    publish(job_channel(job.id), {
        "type": "status", "status": job.status.value, "cancel_requested": True,
        "message": "Cancelled before classification started." if stopped else "Cancelling…",
    })
    if job.document_id:
        publish(document_channel(job.document_id), {
            "type": "page_job", "page_number": job.page_number, "job": job_payload(job),
        })


async def cancel_document(db: AsyncSession, doc: Document) -> bool:
    """Cancel a document's OCR and its unfinished page jobs. False when
    nothing is left to cancel."""
    jobs = (await db.execute(
        select(ClassificationJob).where(
            ClassificationJob.document_id == doc.id,
            ClassificationJob.status.in_(ACTIVE_JOB_STATUSES),
        )
    )).scalars().all()
    ocr_running = doc.upload_status == UploadStatus.UPLOADING
    if not ocr_running and not jobs:
        return False

    if ocr_running:
        doc.cancel_requested = True
        # No pages yet: the OCR run has not started (or has just started; the
        # worker then sees the request at its first checkpoint), so the
        # document is final now.
        has_pages = (await db.execute(
            select(DocumentPage.id).where(DocumentPage.document_id == doc.id).limit(1)
        )).first() is not None
        if not has_pages:
            doc.upload_status = UploadStatus.CANCELLED
        await db.commit()
        await db.refresh(doc)
        publish(document_channel(doc.id), {
            "type": "document", "status": doc.upload_status.value, "cancel_requested": True,
            "message": "Cancelled before OCR started." if not has_pages else "Cancelling…",
        })

    for job in jobs:
        await cancel_job(db, job)
    return True
