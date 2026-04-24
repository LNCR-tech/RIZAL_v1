"""Schemas for event type API and nested event payloads."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EventTypeSummary(BaseModel):
    id: int
    school_id: int | None = None
    name: str
    code: str | None = None
    description: str | None = None
    is_active: bool
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class EventTypeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=1000)
    is_active: bool = True
    sort_order: int = Field(default=0, ge=0, le=100000)


class EventTypeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    code: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=1000)
    is_active: bool | None = None
    sort_order: int | None = Field(default=None, ge=0, le=100000)


class EventType(EventTypeSummary):
    created_at: datetime
    updated_at: datetime

