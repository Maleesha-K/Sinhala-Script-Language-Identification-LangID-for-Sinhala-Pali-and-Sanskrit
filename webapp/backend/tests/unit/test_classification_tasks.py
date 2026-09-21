import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from uuid import uuid4
from datetime import datetime, timezone

from app.workers.tasks.classification_tasks import _process_classification_job_async
from app.db.models.classification_job import ClassificationJob, JobStatus

def test_process_classification_job_not_found():
    """Verify that when a job is not found in DB, it logs an error and exits cleanly without throwing."""
    async def _run():
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        mock_session_maker = MagicMock()
        mock_session_maker.return_value.__aenter__.return_value = mock_session
        
        with patch("app.workers.tasks.classification_tasks.async_session_maker", mock_session_maker):
            # Should not raise exception
            await _process_classification_job_async(str(uuid4()))

    asyncio.run(_run())

def test_process_classification_job_success():
    """Verify complete classification workflow with mocked ML, DB, and Credit Service."""
    async def _run():
        job_id = uuid4()
        mock_job = ClassificationJob(
            id=job_id,
            user_id=uuid4(),
            input_text="නමෝ තස්ස භගවතෝ. මෙය සිංහල වාක්‍යයකි.",
            model_name="sklearn_langid",
            segmentation_strategy="sentence",
            status=JobStatus.QUEUED
        )
        
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_session.execute.return_value = mock_result
        
        mock_session_maker = MagicMock()
        mock_session_maker.return_value.__aenter__.return_value = mock_session
        
        mock_predictions = [
            {"language": "pali", "confidence": 0.99, "probabilities": {"pali": 0.99, "sinhala": 0.01}},
            {"language": "sinhala", "confidence": 0.98, "probabilities": {"sinhala": 0.98, "pali": 0.02}},
        ]
        
        with patch("app.workers.tasks.classification_tasks.async_session_maker", mock_session_maker), \
             patch("app.workers.tasks.classification_tasks.publish_job_event"), \
             patch("app.workers.tasks.classification_tasks.langid_classifier.predict_batch", return_value=mock_predictions), \
             patch("app.services.credit_service.credit_service.charge_classification", new_callable=AsyncMock, return_value=True), \
             patch("sqlalchemy.ext.asyncio.AsyncEngine.dispose", new_callable=AsyncMock):
             
            await _process_classification_job_async(str(job_id))
            
            assert mock_job.status == JobStatus.COMPLETED
            assert mock_job.completed_at is not None
            assert mock_job.total_tokens > 0
            assert mock_session.add.call_count == 2 # 2 classified segments added

    asyncio.run(_run())

def test_process_classification_job_empty_text_fails():
    """Verify that a job with empty text transitions to FAILED status."""
    async def _run():
        job_id = uuid4()
        mock_job = ClassificationJob(
            id=job_id,
            user_id=uuid4(),
            input_text="",
            model_name="sklearn_langid",
            segmentation_strategy="sentence",
            status=JobStatus.QUEUED
        )
        
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_session.execute.return_value = mock_result
        
        mock_session_maker = MagicMock()
        mock_session_maker.return_value.__aenter__.return_value = mock_session
        
        with patch("app.workers.tasks.classification_tasks.async_session_maker", mock_session_maker), \
             patch("app.workers.tasks.classification_tasks.publish_job_event"), \
             patch("sqlalchemy.ext.asyncio.AsyncEngine.dispose", new_callable=AsyncMock):
             
            await _process_classification_job_async(str(job_id))
            assert mock_job.status == JobStatus.FAILED

    asyncio.run(_run())
