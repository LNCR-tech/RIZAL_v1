"""Use: Creates the main Celery app for backend background jobs.
Where to use: Use this when starting Celery workers or beat with the current worker package path.
Role: Worker setup layer. It configures background task execution.
"""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "aura_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_time_limit=settings.celery_task_time_limit_seconds,
    broker_connection_retry_on_startup=True,
)

if settings.event_status_sync_enabled:
    celery_app.conf.beat_schedule = {
        "sync-event-workflow-statuses": {
            "task": "app.workers.tasks.sync_event_workflow_statuses",
            "schedule": settings.event_status_sync_interval_seconds,
        }
    }
else:
    celery_app.conf.beat_schedule = {}

celery_app.autodiscover_tasks(["app.workers"])
