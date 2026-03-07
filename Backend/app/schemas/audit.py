from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class SchoolAuditLogSearchItem(BaseModel):
    id: int
    school_id: int
    actor_user_id: Optional[int] = None
    action: str
    status: str
    details: Optional[str] = None
    details_json: Optional[dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SchoolAuditLogSearchResponse(BaseModel):
    total: int
    items: list[SchoolAuditLogSearchItem]
