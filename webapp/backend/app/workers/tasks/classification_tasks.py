from uuid import UUID
import re
from datetime import datetime, timezone
import asyncio

from sqlalchemy import select
from app.workers.celery_app import celery_app
from app.db.session import async_session_maker
from app.db.models.classification_job import ClassificationJob, JobStatus
from app.db.models.classified_segment import ClassifiedSegment
from app.ml.sklearn_langid import langid_classifier
from app.utils.redis_client import publish_job_event
import logging

logger = logging.getLogger(__name__)

def _segment_text(text: str, strategy: str) -> list[dict]:
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
            segment_text = match.group(0).strip()
            if segment_text:
                segments.append({
                    "text": segment_text,
                    "start": match.start(),
                    "end": match.end()
                })
        return segments
        
    elif strategy == "sentence":
        # Split by typical sentence boundaries: ., !, ?, ।, 
        segments = []
        for match in re.finditer(r'[^.!?।]+(?:[.!?।]+|$)', text):
            segment_text = match.group(0).strip()
            if segment_text:
                segments.append({
                    "text": segment_text,
                    "start": match.start(),
                    "end": match.end()
                })
        return segments
        
    return [{"text": text, "start": 0, "end": len(text)}]

async def _process_classification_job_async(job_id_str: str):
    job_uuid = UUID(job_id_str)
    
    async with async_session_maker() as session:
        result = await session.execute(select(ClassificationJob).where(ClassificationJob.id == job_uuid))
        job = result.scalar_one_or_none()
        
        if not job:
            logger.error(f"ClassificationJob {job_id_str} not found")
            return
            
        try:
            job.status = JobStatus.PROCESSING
            await session.commit()
            publish_job_event(job_id_str, "processing", 10, "Starting segmentation...")
            
            # Use input_text if present, else fallback (not implemented fully)
            text_to_process = job.input_text or ""
            if not text_to_process:
                raise ValueError("No text provided for classification.")
            
            # 1. Segmentation
            segments_info = _segment_text(text_to_process, job.segmentation_strategy)
            
            # 2. Batch Classification
            texts = [s["text"] for s in segments_info]
            predictions = langid_classifier.predict_batch(texts)
            
            # 3. Create ClassifiedSegment records
            for i, (seg_info, pred) in enumerate(zip(segments_info, predictions)):
                segment_record = ClassifiedSegment(
                    job_id=job.id,
                    segment_index=i,
                    text=seg_info["text"],
                    predicted_language=pred["language"],
                    confidence=pred["confidence"],
                    probabilities=pred["probabilities"],
                    start_char_offset=seg_info["start"],
                    end_char_offset=seg_info["end"]
                )
                session.add(segment_record)
                
            # 4. Finalize Job
            # A rough estimate for tokens if needed
            job.total_tokens = sum(len(t.split()) for t in texts)
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc)
            
            await session.commit()
            logger.info(f"ClassificationJob {job_id_str} completed successfully.")
            publish_job_event(job_id_str, "completed", 100, "Job finished successfully.")
            
        except Exception as e:
            logger.exception(f"ClassificationJob {job_id_str} failed: {e}")
            job.status = JobStatus.FAILED
            await session.commit()
            publish_job_event(job_id_str, "failed", 0, str(e))

@celery_app.task(name="process_classification_job")
def process_classification_job(job_id_str: str):
    return asyncio.run(_process_classification_job_async(job_id_str))
