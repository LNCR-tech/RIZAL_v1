"""Use: Keeps old database imports working while the app uses the new core database setup.
Where to use: Use this only when older code still imports from `app.database`.
Role: Compatibility layer. It forwards database access to the current core modules.
"""

from app.core.database import Base, SessionLocal, engine
from app.core.dependencies import get_db

__all__ = ["Base", "SessionLocal", "engine", "get_db"]
