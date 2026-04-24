"""Use: Defines request and response data shapes for per-user app preference API data.
Where to use: Use this in routers when validating or returning user app preference payloads.
Role: Schema layer. It keeps API payloads clear and typed.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserAppPreferenceResponse(BaseModel):
    user_id: int
    dark_mode_enabled: bool
    font_size_percent: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserAppPreferenceUpdate(BaseModel):
    dark_mode_enabled: bool | None = None
    font_size_percent: int | None = Field(default=None, ge=80, le=130)
