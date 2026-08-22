import redis.asyncio as aioredis
import redis
from app.config import settings

# Async client for FastAPI WebSockets
async_redis_client = aioredis.from_url(
    f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
    decode_responses=True
)

# Sync client for Celery tasks
sync_redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True
)

def publish_job_event(job_id: str, status: str, progress: int = 0, message: str = ""):
    """Publish a progress event to the job's pub/sub channel"""
    import json
    channel = f"job_updates:{job_id}"
    payload = json.dumps({
        "status": status,
        "progress": progress,
        "message": message
    })
    sync_redis_client.publish(channel, payload)
