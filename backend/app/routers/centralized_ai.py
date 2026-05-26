"""Backend-owned centralized AI routes."""

from __future__ import annotations

from typing import Annotated
import json

from fastapi import APIRouter, Header, HTTPException, status
from fastapi.responses import StreamingResponse

from app.core.config import get_settings
from app.schemas.centralized_ai import (
    CentralizedAIChatRequest,
    CentralizedAIChatResponse,
    CentralizedAICompletionRequest,
    CentralizedAICompletionResponse,
)
from app.services.centralized_ai_service import complete_chat, extract_text_content, stream_chat

router = APIRouter(prefix="/centralized-ai", tags=["centralized-ai"])


def _authorize_centralized_ai(
    *,
    x_centralized_ai_key: str | None,
    authorization: str | None,
) -> None:
    expected_key = get_settings().centralized_ai_api_key
    if not expected_key:
        return
    bearer_value = ""
    if authorization and authorization.lower().startswith("bearer "):
        bearer_value = authorization.split(" ", 1)[1].strip()
    if x_centralized_ai_key == expected_key or bearer_value == expected_key:
        return
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid centralized AI service key",
    )


def _sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


@router.post("/chat", response_model=CentralizedAIChatResponse)
async def centralized_chat(
    body: CentralizedAIChatRequest,
    x_centralized_ai_key: Annotated[str | None, Header()] = None,
    authorization: Annotated[str | None, Header()] = None,
):
    _authorize_centralized_ai(
        x_centralized_ai_key=x_centralized_ai_key,
        authorization=authorization,
    )
    message = await complete_chat([{"role": "user", "content": body.prompt}])
    return {"response": extract_text_content(message.get("content"))}


@router.post("/chat/completions", response_model=CentralizedAICompletionResponse)
async def centralized_chat_completion(
    body: CentralizedAICompletionRequest,
    x_centralized_ai_key: Annotated[str | None, Header()] = None,
    authorization: Annotated[str | None, Header()] = None,
):
    _authorize_centralized_ai(
        x_centralized_ai_key=x_centralized_ai_key,
        authorization=authorization,
    )
    message = await complete_chat(
        body.messages,
        tools=body.tools,
        max_tokens=body.max_tokens,
    )
    return {
        "message": message,
        "response": extract_text_content(message.get("content")),
    }


@router.post("/chat/stream")
async def centralized_chat_stream(
    body: CentralizedAICompletionRequest,
    x_centralized_ai_key: Annotated[str | None, Header()] = None,
    authorization: Annotated[str | None, Header()] = None,
):
    _authorize_centralized_ai(
        x_centralized_ai_key=x_centralized_ai_key,
        authorization=authorization,
    )

    async def _generator():
        async for chunk in stream_chat(
            body.messages,
            tools=body.tools,
            max_tokens=body.max_tokens,
        ):
            yield _sse_event("chunk", chunk)
        yield _sse_event("done", {"status": "ok"})

    return StreamingResponse(
        _generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
