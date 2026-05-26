"""Schemas for the backend-owned centralized AI API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CentralizedAIChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1)


class CentralizedAIChatResponse(BaseModel):
    response: str


class CentralizedAICompletionRequest(BaseModel):
    messages: list[dict[str, Any]] = Field(..., min_length=1)
    tools: list[dict[str, Any]] | None = None
    max_tokens: int | None = Field(default=None, ge=1)


class CentralizedAICompletionResponse(BaseModel):
    message: dict[str, Any]
    response: str
