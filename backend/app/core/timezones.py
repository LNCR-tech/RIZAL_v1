"""Shared timezone helpers for backend timestamps and API responses."""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

PHILIPPINE_TIMEZONE = ZoneInfo("Asia/Manila")


def utc_now() -> datetime:
    """Return an aware UTC timestamp for persistence and response helpers."""
    return datetime.now(timezone.utc)


def ensure_utc(value: datetime | None) -> datetime | None:
    """Normalize a datetime to an aware UTC datetime.

    SQLAlchemy drivers or legacy schemas may yield naive datetimes even when the
    ORM column is declared as timezone-aware. Treat naive values as UTC.
    """
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def to_philippine_time(value: datetime | None) -> datetime | None:
    """Normalize UTC-stored timestamps into Asia/Manila for API responses."""
    if value is None:
        return None
    return ensure_utc(value).astimezone(PHILIPPINE_TIMEZONE)
