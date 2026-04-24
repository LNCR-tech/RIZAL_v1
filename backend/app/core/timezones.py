"""Shared timezone helpers for backend API responses."""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

PHILIPPINE_TIMEZONE = ZoneInfo("Asia/Manila")


def to_philippine_time(value: datetime | None) -> datetime | None:
    """Normalize UTC-stored timestamps into Asia/Manila for API responses."""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(PHILIPPINE_TIMEZONE)
