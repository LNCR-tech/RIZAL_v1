"""Use: Request schemas for Google OAuth login.
Where to use: The /auth/google endpoint.
Role: Schema layer.
"""

from pydantic import BaseModel, Field, model_validator
from typing import Optional


class GoogleLoginRequest(BaseModel):
    id_token: Optional[str] = Field(None, min_length=1, description="Google ID token (native / Android).")
    access_token: Optional[str] = Field(None, min_length=1, description="Google OAuth2 access token (web implicit flow).")

    @model_validator(mode="after")
    def _require_one(self) -> "GoogleLoginRequest":
        if not self.id_token and not self.access_token:
            raise ValueError("Either id_token or access_token must be provided.")
        return self
