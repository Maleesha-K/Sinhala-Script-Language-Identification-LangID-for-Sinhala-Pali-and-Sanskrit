"""Live progress for classification jobs and documents (see app/utils/events.py).

Both sockets send {"type": "subscribed"} once they listen on Redis; clients load
the current state over REST after that and merge the relayed events into it.
A socket closes itself once there is nothing left to wait for.
"""

import asyncio
import json
import uuid
from typing import Awaitable, Callable

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.events import document_channel, job_channel
from app.utils.redis_client import async_redis_client
from app.dependencies import get_ws_current_user, get_db
from app.db.models.classification_job import ClassificationJob, JobStatus
from app.db.models.document import Document, UploadStatus
from app.services.job_control import ACTIVE_JOB_STATUSES

router = APIRouter(prefix="/ws", tags=["websockets"])

TERMINAL_STATUSES = {JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.CANCELLED.value}


async def _authenticate(websocket: WebSocket, token: str, db: AsyncSession, object_id: str):
    """The user and the parsed id, or None after closing the socket."""
    try:
        user = await get_ws_current_user(token, db)
    except ValueError as e:
        await websocket.close(code=1008, reason=str(e))
        return None, None
    try:
        return user, uuid.UUID(object_id)
    except ValueError:
        await websocket.close(code=1008, reason="Invalid id")
        return None, None


async def _relay(
    websocket: WebSocket,
    channel: str,
    on_subscribed: Callable[[], Awaitable[bool]],
    on_event: Callable[[dict], Awaitable[bool]],
):
    """Forward the channel's events until a callback returns True (done)."""
    pubsub = async_redis_client.pubsub()
    await pubsub.subscribe(channel)
    try:
        await websocket.send_text(json.dumps({"type": "subscribed"}))
        if await on_subscribed():
            return
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if not message:
                await asyncio.sleep(0.1)
                continue
            await websocket.send_text(message["data"])
            try:
                event = json.loads(message["data"])
            except ValueError:
                continue
            if isinstance(event, dict) and await on_event(event):
                return
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()
        try:
            await websocket.close()
        except Exception:
            pass


@router.websocket("/jobs/{job_id}")
async def job_updates_websocket(
    websocket: WebSocket,
    job_id: str,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    await websocket.accept()
    user, job_uuid = await _authenticate(websocket, token, db, job_id)
    if user is None:
        return

    # Only the job's owner may follow it.
    status_query = select(ClassificationJob.status).where(
        ClassificationJob.id == job_uuid, ClassificationJob.user_id == user.id
    )
    if (await db.execute(status_query)).scalar_one_or_none() is None:
        await websocket.close(code=1008, reason="Job not found")
        return
    await db.rollback()  # do not hold a transaction open for the socket's lifetime

    async def on_subscribed() -> bool:
        # The job may have finished before we subscribed, in which case no
        # further event will ever be published.
        current = (await db.execute(status_query)).scalar_one().value
        await db.rollback()
        if current in TERMINAL_STATUSES:
            await websocket.send_text(json.dumps({
                "type": "status", "status": current,
                "progress": 100 if current == "completed" else 0, "message": "",
            }))
            return True
        return False

    async def on_event(event: dict) -> bool:
        return event.get("type") == "status" and event.get("status") in TERMINAL_STATUSES

    await _relay(websocket, job_channel(job_id), on_subscribed, on_event)


@router.websocket("/documents/{document_id}")
async def document_updates_websocket(
    websocket: WebSocket,
    document_id: str,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    await websocket.accept()
    user, doc_uuid = await _authenticate(websocket, token, db, document_id)
    if user is None:
        return

    owned = await db.execute(
        select(Document.id).where(Document.id == doc_uuid, Document.user_id == user.id)
    )
    if owned.scalar_one_or_none() is None:
        await websocket.close(code=1008, reason="Document not found")
        return
    await db.rollback()

    async def settled() -> bool:
        """OCR has finished and no page is still waiting for classification."""
        status = (await db.execute(select(Document.upload_status).where(Document.id == doc_uuid))).scalar_one_or_none()
        pending = (await db.execute(select(exists().where(
            ClassificationJob.document_id == doc_uuid,
            ClassificationJob.status.in_(ACTIVE_JOB_STATUSES),
        )))).scalar()
        await db.rollback()
        if status is None or (status != UploadStatus.UPLOADING and not pending):
            await websocket.send_text(json.dumps({"type": "settled"}))
            return True
        return False

    async def on_event(event: dict) -> bool:
        kind = event.get("type")
        if kind == "document" and event.get("status") != UploadStatus.UPLOADING.value:
            return await settled()
        if kind == "page_job" and (event.get("job") or {}).get("status") in TERMINAL_STATUSES:
            return await settled()
        return False

    await _relay(websocket, document_channel(document_id), settled, on_event)
