"""Use: Defines request and response data shapes for department API data.
Where to use: Use this in routers and services when validating or returning department API data.
Role: Schema layer. It keeps API payloads clear and typed.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class DepartmentBase(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        examples=["Computer Science", "Engineering"],
        description="Official name of the department"
    )

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        examples=["Updated Department Name"],
        description="New name for the department"
    )

class Department(DepartmentBase):
    id: int = Field(..., description="Unique identifier of the department")
    school_id: Optional[int] = Field(default=None, description="Owning school/campus identifier")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "school_id": 1,
                "name": "Computer Science"
            }
        }
    )
