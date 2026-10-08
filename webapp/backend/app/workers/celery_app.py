from celery import Celery
from app.config import settings

celery_app = Celery(
    "langid_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
    # Each OCR engine has its own worker (see webapp/docker-compose.yml), so a
    # long OCR run never blocks the classification of the pages it has already
    # read, which go to the default queue. Surya holds ~5 GB of models in RAM
    # per process, so its worker runs a single process.
    task_routes={
        "process_document_ocr": {"queue": "ocr"},
        "process_document_ocr_surya": {"queue": "surya"},
    },
)

# Auto-discover tasks in all submodules
celery_app.autodiscover_tasks(
    ['app.workers.tasks.ocr_tasks', 'app.workers.tasks.classification_tasks'],
    force=True
)
