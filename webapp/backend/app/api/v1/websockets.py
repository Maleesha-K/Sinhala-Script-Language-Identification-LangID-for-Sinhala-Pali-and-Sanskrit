import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional
from app.utils.redis_client import async_redis_client
from app.dependencies import get_ws_current_user, get_db
from app.db.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/ws", tags=["websockets"])

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

    # Subscribe to Redis
    channel_name = f"job_updates:{job_id}"
    pubsub = async_redis_client.pubsub()
    await pubsub.subscribe(channel_name)
    
    try:
        while True:
            # Wait for message from redis
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message:
                await websocket.send_text(message["data"])
            else:
                # To detect if client disconnected, we could optionally ping or wait on websocket.receive
                # A simple timeout allows us to check client connection
                await asyncio.sleep(0.1)
                
    except WebSocketDisconnect:
        # Client disconnected normally
        pass
    except Exception as e:
        pass
    finally:
        await pubsub.unsubscribe(channel_name)
        await pubsub.close()
