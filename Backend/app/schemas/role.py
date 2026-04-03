"""Use: Defines request and response data shapes for role API data.
Where to use: Use this in routers and services when validating or returning role API data.
Role: Schema layer. It keeps API payloads clear and typed.
"""

from pydantic import BaseModel, ConfigDict

class Role(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)
