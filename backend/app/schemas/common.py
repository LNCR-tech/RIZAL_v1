"""Use: Defines small shared API schemas used across routers.
Where to use: Import these for simple message and error responses.
Role: Schema layer. It keeps common response shapes explicit and reusable.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    message: str


class RateLimitErrorResponse(BaseModel):
    code: str = "rate_limit_exceeded"
    message: str
    limit: int = Field(gt=0)
    window_seconds: int = Field(gt=0)
    retry_after_seconds: int = Field(ge=0)
