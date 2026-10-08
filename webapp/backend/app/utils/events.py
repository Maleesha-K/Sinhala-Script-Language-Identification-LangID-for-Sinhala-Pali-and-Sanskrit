"""Live progress events, published by the Celery workers to Redis pub/sub and
relayed to browsers by the WebSockets in app/api/v1/websockets.py.

Every event is a JSON object with a "type":

  job_updates:{job_id}
    status     {status, progress, message, done, total}  job status / progress
               (cancel_requested: true while a cancel is pending)
    segments   {segments, done, total}                   newly classified segments

  document_updates:{document_id}
    document       {status, message}                     document status (cancel_requested
                                                         while a cancel is pending)
    page           {page}                                 a page was created or changed
    page_job       {page_number, job}                     a page's classification job changed
    page_segments  {page_number, job_id, segments}        newly classified segments of a page

Events only carry what changed, so clients merge them into the state they load
over REST (the REST endpoints serialize with the same helpers). A WebSocket
sends {"type": "subscribed"} once it listens, and clients load the REST state
after that, so nothing published in between is missed.
"""

import json

from app.utils.redis_client import sync_redis_client


def job_channel(job_id) -> str:
    return f"job_updates:{job_id}"


def document_channel(document_id) -> str:
    return f"document_updates:{document_id}"


def publish(channel: str, payload: dict) -> None:
    sync_redis_client.publish(channel, json.dumps(payload, default=str))


def segment_payload(segment) -> dict:
    return {
        "id": str(segment.id),
        "segment_index": segment.segment_index,
        "text": segment.text,
        "predicted_language": segment.predicted_language,
        "confidence": float(segment.confidence),
        "probabilities": segment.probabilities,
        "start_char_offset": segment.start_char_offset,
        "end_char_offset": segment.end_char_offset,
    }


def page_payload(page) -> dict:
    return {
        "id": str(page.id),
        "document_id": str(page.document_id),
        "page_number": page.page_number,
        "extracted_text": page.extracted_text,
        "extraction_method": page.extraction_method.value if page.extraction_method else None,
        "ocr_model": page.ocr_model,
        "status": page.status.value,
    }


def job_payload(job, done: int | None = None, total: int | None = None) -> dict:
    return {
        "id": str(job.id),
        "status": job.status.value,
        "model_name": job.model_name,
        "error_message": job.error_message,
        "cancel_requested": job.cancel_requested,
        "done": done,
        "total": total,
    }
