from celery import Celery
from core.config import config

celery_app = Celery(
    "celery_worker",
    broker=config.rabbitmq_url,
    backend=config.redis_url,
    include=["src.background_tasks"],
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