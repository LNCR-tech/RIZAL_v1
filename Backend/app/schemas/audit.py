"""Use: Defines request and response data shapes for audit log API data.
Where to use: Use this in routers and services when validating or returning audit log API data.
Role: Schema layer. It keeps API payloads clear and typed.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class SchoolAuditLogSearchItem(BaseModel):
    id: int
    school_id: int
    actor_user_id: Optional[int] = None
    action: str
    status: str
    details: Optional[str] = None
    details_json: Optional[dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SchoolAuditLogSearchResponse(BaseModel):
    total: int
    items: list[SchoolAuditLogSearchItem]
