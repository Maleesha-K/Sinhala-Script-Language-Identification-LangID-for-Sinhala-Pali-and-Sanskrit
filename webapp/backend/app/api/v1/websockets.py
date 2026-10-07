import asyncio
import json
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.redis_client import async_redis_client
from app.dependencies import get_ws_current_user, get_db
from app.db.models.classification_job import ClassificationJob, JobStatus

router = APIRouter(prefix="/ws", tags=["websockets"])

TERMINAL_STATUSES = {JobStatus.COMPLETED.value, JobStatus.FAILED.value}

@router.websocket("/jobs/{job_id}")
async def job_updates_websocket(
    websocket: WebSocket, 
    job_id: str,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    await websocket.accept()
    
    try:
        # Authenticate
        user = await get_ws_current_user(token, db)
    except ValueError as e:
        await websocket.close(code=1008, reason=str(e))
        return

    # Only the job's owner may follow it.
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        await websocket.close(code=1008, reason="Invalid job id")
        return
    result = await db.execute(
        select(ClassificationJob.status).where(
            ClassificationJob.id == job_uuid, ClassificationJob.user_id == user.id
        )
    )
    status = result.scalar_one_or_none()
    if status is None:
        await websocket.close(code=1008, reason="Job not found")
        return

    # Subscribe to Redis
    channel_name = f"job_updates:{job_id}"
    pubsub = async_redis_client.pubsub()
    await pubsub.subscribe(channel_name)

    try:
        # The job may have finished before the client connected, in which case
        # no further event will ever be published.
        db.expire_all()
        refreshed = await db.execute(select(ClassificationJob.status).where(ClassificationJob.id == job_uuid))
        current = refreshed.scalar_one().value
        if current in TERMINAL_STATUSES:
            await websocket.send_text(json.dumps({"status": current, "progress": 100 if current == "completed" else 0, "message": ""}))
            return

        while True:
            # Wait for message from redis
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message:
                await websocket.send_text(message["data"])
                try:
                    if json.loads(message["data"]).get("status") in TERMINAL_STATUSES:
                        return
                except (ValueError, AttributeError):
                    pass
            else:
                await asyncio.sleep(0.1)
                
    except WebSocketDisconnect:
        # Client disconnected normally
        pass
    except Exception:
        pass
    finally:
        await pubsub.unsubscribe(channel_name)
        await pubsub.close()
        try:
            await websocket.close()
        except Exception:
            pass
