from celery import Celery
from core.config import config

celery_app = Celery(
    "celery_worker",
    broker=config.rabbitmq_url,
    backend=config.redis_url,
    include=[
        "background_tasks.resume_text_extraction",
        "background_tasks.prepare_interview",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
)
# Deletes result in 1 hr
celery_app.conf.result_expires = 3600 
