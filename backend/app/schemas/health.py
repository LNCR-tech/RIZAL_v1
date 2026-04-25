"""Use: Defines health-check response shapes.
Where to use: Use this for health/readiness route response validation.
Role: Schema layer. It keeps runtime status payloads explicit.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthDatabaseStatus(BaseModel):
    ok: bool
    detail: str | None = None


class HealthReadinessStatus(BaseModel):
    ready: bool
    database_ready: bool
    face_runtime_ready: bool


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    database: HealthDatabaseStatus
    face_runtime: dict[str, Any] = Field(default_factory=dict)
    readiness: HealthReadinessStatus
    pool: dict[str, Any] = Field(default_factory=dict)


class ReadinessResponse(BaseModel):
    status: str
    timestamp: str
    database: HealthDatabaseStatus
    face_runtime: dict[str, Any] = Field(default_factory=dict)
