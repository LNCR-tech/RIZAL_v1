"""Use: Keeps old task imports working.
Where to use: Use this only when older code or commands still import `app.worker.tasks`.
Role: Compatibility layer. It forwards old task imports to the current worker package.
"""

from app.workers.tasks import *  # noqa: F401,F403
