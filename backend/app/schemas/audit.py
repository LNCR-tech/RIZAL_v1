"""Use: Defines request and response data shapes for audit log API data.
Where to use: Use this in routers and services when validating or returning audit log API data.
Role: Schema layer. It keeps API payloads clear and typed.
"""

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, field_validator


def _ensure_datetime_has_timezone(value):
    """Keep API response offsets intact while treating naive DB values as UTC."""
    if not isinstance(value, datetime):
        return value
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


class SchoolAuditLogSearchItem(BaseModel):
    id: int
    school_id: int
    actor_user_id: Optional[int] = None
    action: str
    status: str
    details: Optional[str] = None
    details_json: Optional[dict[str, Any]] = None
    created_at: datetime

    @field_validator("created_at", mode="before")
    @classmethod
    def normalize_created_at_timezone(cls, value):
        return _ensure_datetime_has_timezone(value)

    model_config = ConfigDict(from_attributes=True)


class SchoolAuditLogSearchResponse(BaseModel):
    total: int
    items: list[SchoolAuditLogSearchItem]
