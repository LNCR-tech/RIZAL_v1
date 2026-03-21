"""Use: Keeps old Celery app imports working.
Where to use: Use this only when older code or commands still import `app.worker.celery_app`.
Role: Compatibility layer. It forwards old worker imports to the current worker package.
"""

from app.workers.celery_app import celery_app

__all__ = ["celery_app"]
