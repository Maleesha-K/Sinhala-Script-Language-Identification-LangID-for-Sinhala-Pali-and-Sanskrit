from uuid import UUID
import re
from datetime import datetime, timezone
import asyncio

from sqlalchemy import select
from app.workers.celery_app import celery_app
from app.db.session import async_session_maker
from app.db.models.classification_job import ClassificationJob, JobStatus
from app.db.models.classified_segment import ClassifiedSegment
from app.ml.registry import get_classifier
from app.utils.events import (
    document_channel, job_channel, job_payload, publish, segment_payload,
)
import logging

logger = logging.getLogger(__name__)

def estimate_tokens(text: str) -> int:
    """Billable token count: whitespace-separated words."""
    return len(text.split())

def split_segments(text: str, strategy: str) -> list[dict]:
    """
    Segments the given text according to the strategy.
    Returns a list of dicts with 'text', 'start', 'end'.
    """
    if not text:
        return []
        
    if strategy == "full_text":
        return [{"text": text, "start": 0, "end": len(text)}]
        
    elif strategy == "paragraph":
        segments = []
        for match in re.finditer(r'(?:[^\n][\n]?)+', text):
            segment_text = match.group(0)
            if segment_text.strip():
                segments.append({
                    "text": segment_text,
                    "start": match.start(),
                    "end": match.end()
                })
        return segments
        
    elif strategy == "sentence":
        # Split by typical sentence boundaries and newlines: ., !, ?, ।, \n
        segments = []
        for match in re.finditer(r'[^.!?।\n]+(?:[.!?।\n]+|$)', text):
            segment_text = match.group(0)
            if segment_text.strip():
                segments.append({
                    "text": segment_text,
                    "start": match.start(),
                    "end": match.end()
                })
        return segments
        
    elif strategy == "auto":
        # Aggressive split by newlines, punctuation, and special characters
        segments = []
        for match in re.finditer(r'[^.!?।\n,;:\(\)\[\]]+(?:[.!?।\n,;:\(\)\[\]]+|$)', text):
            segment_text = match.group(0)
            if segment_text.strip():
                segments.append({
                    "text": segment_text,
                    "start": match.start(),
                    "end": match.end()
                })
        return segments
        
    return [{"text": text, "start": 0, "end": len(text)}]

# Segments are classified, saved and published in batches of this size, so
# results appear while a long text is still being classified.
BATCH_SIZE = 16


def _segment_language(pred: dict) -> str:
    # Outside the three target categories, record the language the model
    # actually detected rather than a bare "other".
    language = pred["language"]
    if language == "other" and pred.get("detected_language"):
        language = pred["detected_language"][:32]
    return language


class _Progress:
    """Publishes a job's progress to its own channel and, for the per-page jobs
    of a document, to the document's channel."""

    def __init__(self, job):
        self.job = job
        self.job_id = str(job.id)
        self.document_id = job.document_id
        self.page_number = job.page_number
        self.done = 0
        self.total = None

    def status(self, progress: int, message: str = ""):
        publish(job_channel(self.job_id), {
            "type": "status", "status": self.job.status.value, "progress": progress,
            "message": message, "done": self.done, "total": self.total,
        })
        if self.document_id:
            publish(document_channel(self.document_id), {
                "type": "page_job", "page_number": self.page_number,
                "job": job_payload(self.job, self.done, self.total),
            })

    def segments(self, records):
        segments = [segment_payload(r) for r in records]
        publish(job_channel(self.job_id), {
            "type": "segments", "segments": segments, "done": self.done, "total": self.total,
        })
        if self.document_id:
            publish(document_channel(self.document_id), {
                "type": "page_segments", "page_number": self.page_number,
                "job_id": self.job_id, "segments": segments,
            })


async def _process_classification_job_async(job_id_str: str):
    job_uuid = UUID(job_id_str)
    from app.services.credit_service import credit_service
    from app.db.session import engine

    async with async_session_maker() as session:
        result = await session.execute(select(ClassificationJob).where(ClassificationJob.id == job_uuid))
        job = result.scalar_one_or_none()
        
        if not job:
            logger.error(f"ClassificationJob {job_id_str} not found")
            return

        progress = _Progress(job)
        user_id, model_name = job.user_id, job.model_name
        charged = False
        try:
            job.status = JobStatus.PROCESSING
            await session.commit()
            progress.status(5, "Starting segmentation...")

            text_to_process = job.input_text or ""
            if not text_to_process.strip():
                raise ValueError("No text provided for classification.")

            # 1. Segmentation
            segments_info = split_segments(text_to_process, job.segmentation_strategy)
            texts = [s["text"].strip() for s in segments_info]
            progress.total = len(texts)

            # 2. Charge up front: results are visible as soon as they are saved.
            job.total_tokens = sum(estimate_tokens(t) for t in texts)
            if not await credit_service.charge_classification(
                session, user_id, job.id, model_name, job.total_tokens
            ):
                raise ValueError("Insufficient credits for classification")
            charged = True

            # 3. Classify, save and publish batch by batch.
            classifier = get_classifier(model_name)
            progress.status(10, f"Classifying with {model_name}...")
            for start in range(0, len(texts), BATCH_SIZE):
                predictions = classifier.predict_batch(texts[start:start + BATCH_SIZE])
                records = []
                for i, pred in enumerate(predictions, start):
                    seg_info = segments_info[i]
                    records.append(ClassifiedSegment(
                        job_id=job.id,
                        segment_index=i,
                        text=seg_info["text"],
                        predicted_language=_segment_language(pred),
                        confidence=pred["confidence"],
                        probabilities=pred["probabilities"],
                        start_char_offset=seg_info["start"],
                        end_char_offset=seg_info["end"]
                    ))
                session.add_all(records)
                await session.commit()
                progress.done += len(records)
                progress.segments(records)
                progress.status(10 + 90 * progress.done // max(progress.total, 1))

            # 4. Finalize Job
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc)
            await session.commit()
            logger.info(f"ClassificationJob {job_id_str} completed successfully.")
            progress.status(100, "Job finished successfully.")

        except Exception as e:
            logger.exception(f"ClassificationJob {job_id_str} failed: {e}")
            # Segments already saved stay visible; the user is not billed for
            # a job that did not finish.
            await session.rollback()
            if charged:
                await credit_service.refund_classification(session, user_id, job_uuid)
            await session.refresh(job)
            job.status = JobStatus.FAILED
            job.error_message = str(e)[:1000]
            job.completed_at = datetime.now(timezone.utc)
            await session.commit()
            progress.status(0, str(e))
        finally:
            await engine.dispose()

@celery_app.task(name="process_classification_job")
def process_classification_job(job_id_str: str):
    import asyncio
    return asyncio.run(_process_classification_job_async(job_id_str))
