"""Use: Request schemas for Google OAuth login.
Where to use: The /auth/google endpoint.
Role: Schema layer.
"""

from pydantic import BaseModel, Field


class GoogleLoginRequest(BaseModel):
    id_token: str = Field(..., min_length=1, description="Google ID token from the client.")
