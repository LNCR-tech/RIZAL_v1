"""Use: Marks `workers` as the main background-job package.
Where to use: Used automatically when the backend imports worker modules from `app.workers`.
Role: Package layer. It groups the current Celery worker files together.
"""

from app.workers.celery_app import celery_app

__all__ = ["celery_app"]
