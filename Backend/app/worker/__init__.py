"""Use: Keeps the old `app.worker` package path available.
Where to use: Use this only when older imports still point to `app.worker`.
Role: Compatibility layer. It helps old worker imports keep working during refactors.
"""

from app.workers.celery_app import celery_app

__all__ = ["celery_app"]
