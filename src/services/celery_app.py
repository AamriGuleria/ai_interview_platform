from celery import Celery
from core.config import config
from kombu import Exchange , Queue, Connection, Producer

interview_exchange = Exchange(
    "interview",
    type="direct",
    durable = True
)

dead_letter_exchange = Exchange(
    "interview.dlx",
    type="direct",
    durable=True
)

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
    task_queues = (
        Queue(
            "interview_tasks",
            exchange = interview_exchange,
            routing_key="interview.process",
            durable=True,
            queue_arguments={
                "x-dead-letter-exchange": "interview.dlx",
                "x-dead-letter-routing-key": "interview.failed",
            },
        ),
        Queue(
            "interview_tasks.dlq",
            exchange=dead_letter_exchange,
            routing_key="interview.failed",
            durable=True,
        )
    ),
    task_routes={
        "background_tasks.resume_text_extraction.extract_resume_context": {
            "queue": "interview_tasks",
            "routing_key": "interview.process",
        },
        "background_tasks.prepare_interview.prepare_interview": {
            "queue": "interview_tasks",
            "routing_key": "interview.process",
        },
    },
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
)
# Deletes result in 1 hr
celery_app.conf.result_expires = 3600 

def publish_to_dlq(task_name: str, task_id: str , args, kwargs, error: str):
    with Connection(config.rabbitmq_url) as connection:
        producer = Producer(connection)

        producer.publish(
            {
                "task_name": task_name,
                "task_id": task_id,
                "args": args,
                "kwargs": kwargs,
                "error": error,
            },
            exchange="interview.dlx",
            routing_key="interview.failed",
            serializer="json",
            declare=[dead_letter_exchange],
            delivery_mode=2
        )