"""Use: Defines shared FastAPI dependencies such as the database session.
Where to use: Use this in routers when a route needs common injected objects.
Role: Core wiring layer. It keeps shared dependency code in one place.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.core.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


__all__ = ["get_db"]
