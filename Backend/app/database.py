"""Compatibility wrapper for legacy database imports.

Prefer importing from `app.core.database` and `app.core.dependencies` in new code.
"""

from app.core.database import Base, SessionLocal, engine
from app.core.dependencies import get_db

__all__ = ["Base", "SessionLocal", "engine", "get_db"]
