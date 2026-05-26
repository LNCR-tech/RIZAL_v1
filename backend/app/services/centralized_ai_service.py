"""Provider adapter for backend-owned AI requests."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any
import json
import logging
import re
import uuid

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _normalize_base_url(value: str) -> str:
    return str(value or "").strip().rstrip("/")


def _infer_ai_provider() -> str:
    settings = get_settings()
    explicit = settings.ai_provider.strip().lower()
    if explicit in {"openai", "openai_compatible", "openai-compatible", "compatible"}:
        return "openai"
    if explicit in {"anthropic", "claude"}:
        return "anthropic"
    if explicit in {"gemini", "google", "google_ai", "google-ai"}:
        return "gemini"

    base_url = settings.ai_api_base.lower()
    model_name = settings.ai_model.lower()
    if "anthropic" in base_url or model_name.startswith("claude"):
        return "anthropic"
    if "generativelanguage.googleapis.com" in base_url or model_name.startswith("gemini"):
        return "gemini"
    return "openai"


def _default_ai_base_url(provider: str) -> str:
    if provider == "anthropic":
        return "https://api.anthropic.com/v1"
    if provider == "gemini":
        return "https://generativelanguage.googleapis.com/v1beta"
    return "https://api.openai.com/v1"


def _effective_ai_base_url(provider: str | None = None) -> str:
    settings = get_settings()
    resolved_provider = provider or _infer_ai_provider()
    configured_base = _normalize_base_url(settings.ai_api_base)
    return configured_base or _default_ai_base_url(resolved_provider)


def _resolve_ai_endpoint(path: str) -> str:
    base = _effective_ai_base_url().rstrip("/")
    suffix = "/" + path.lstrip("/")
    if base.endswith(suffix):
        return base
    return f"{base}{suffix}"


def extract_text_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        main_text = str(content.get("content") or "").strip()
        reasoning = str(content.get("reasoning_content") or "").strip()
        if reasoning and not main_text:
            return reasoning
        if reasoning and main_text:
            return f"<thought>\n{reasoning}\n</thought>\n{main_text}"
        return main_text
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
                continue
            if not isinstance(item, dict):
                continue
            text_value = item.get("text") or item.get("content") or item.get("reasoning_content")
            if isinstance(text_value, str):
                parts.append(text_value)
        return "\n".join(part for part in parts if part).strip()
    return ""


def _safe_json_load(value: Any, default: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    if not isinstance(value, str):
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def _suggest_retry_max_tokens(error_text: str, current_max_tokens: int) -> int | None:
    text_value = str(error_text or "")
    max_allowed_match = re.search(
        r"max_tokens` must be less than or equal to `(\d+)`",
        text_value,
        re.IGNORECASE,
    )
    if not max_allowed_match:
        max_allowed_match = re.search(
            r"maximum value for `max_tokens` is\s+`?(\d+)`?",
            text_value,
            re.IGNORECASE,
        )
    if max_allowed_match:
        try:
            max_allowed = int(max_allowed_match.group(1))
        except ValueError:
            max_allowed = 0
        if 0 < max_allowed < current_max_tokens:
            return max(64, max_allowed)
    affordable_match = re.search(r"can only afford (\d+)", text_value, re.IGNORECASE)
    if affordable_match:
        try:
            affordable_tokens = int(affordable_match.group(1))
        except ValueError:
            affordable_tokens = 0
        if 0 < affordable_tokens < current_max_tokens:
            return max(64, affordable_tokens)
    if "fewer max_tokens" in text_value.lower() and current_max_tokens > 128:
        return max(64, current_max_tokens // 2)
    return None


def _convert_tools_for_openai(tools: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    converted: list[dict[str, Any]] = []
    for tool in tools or []:
        name = tool.get("name")
        description = tool.get("description")
        parameters = tool.get("input_schema") or tool.get("inputSchema")

        if not name and "function" in tool:
            function = tool.get("function") or {}
            name = function.get("name")
            description = function.get("description")
            parameters = function.get("parameters")

        if not name:
            continue
        converted.append(
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description or "",
                    "parameters": parameters or {"type": "object", "properties": {}},
                },
            }
        )
    return converted


def _convert_tools_for_anthropic(tools: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    converted: list[dict[str, Any]] = []
    for tool in tools or []:
        name = tool.get("name")
        description = tool.get("description")
        input_schema = tool.get("input_schema") or tool.get("inputSchema")
        if not name and "function" in tool:
            function = tool.get("function") or {}
            name = function.get("name")
            description = function.get("description")
            input_schema = function.get("parameters")
        if not name:
            continue
        converted.append(
            {
                "name": name,
                "description": description or "",
                "input_schema": input_schema or {"type": "object", "properties": {}},
            }
        )
    return converted


def _convert_messages_for_anthropic(
    messages: list[dict[str, Any]],
) -> tuple[str, list[dict[str, Any]]]:
    system_parts: list[str] = []
    converted: list[dict[str, Any]] = []
    for message in messages:
        role = message.get("role")
        if role == "system":
            content = extract_text_content(message.get("content"))
            if content:
                system_parts.append(content)
            continue
        if role == "assistant":
            assistant_parts: list[dict[str, Any]] = []
            content = extract_text_content(message.get("content"))
            if content:
                assistant_parts.append({"type": "text", "text": content})
            for tool_call in message.get("tool_calls") or []:
                tool_function = tool_call.get("function") or {}
                assistant_parts.append(
                    {
                        "type": "tool_use",
                        "id": tool_call.get("id") or f"tool_{uuid.uuid4().hex}",
                        "name": tool_function.get("name") or "tool",
                        "input": _safe_json_load(tool_function.get("arguments"), {}),
                    }
                )
            converted.append({"role": "assistant", "content": assistant_parts or [{"type": "text", "text": ""}]})
            continue
        if role == "tool":
            tool_content = message.get("content")
            tool_content_text = (
                json.dumps(tool_content, ensure_ascii=False)
                if isinstance(tool_content, (dict, list))
                else str(tool_content or "")
            )
            converted.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": message.get("tool_call_id") or f"tool_{uuid.uuid4().hex}",
                            "content": tool_content_text,
                        }
                    ],
                }
            )
            continue
        converted.append({"role": "user", "content": extract_text_content(message.get("content")) or ""})
    return "\n\n".join(part for part in system_parts if part).strip(), converted


def _normalize_anthropic_response(data: dict[str, Any]) -> dict[str, Any]:
    content_blocks = data.get("content") or []
    text_parts: list[str] = []
    tool_calls: list[dict[str, Any]] = []
    for block in content_blocks:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text" and isinstance(block.get("text"), str):
            text_parts.append(block.get("text") or "")
        if block.get("type") == "tool_use":
            tool_calls.append(
                {
                    "id": block.get("id") or f"tool_{uuid.uuid4().hex}",
                    "type": "function",
                    "function": {
                        "name": block.get("name") or "tool",
                        "arguments": json.dumps(block.get("input") or {}, ensure_ascii=False),
                    },
                }
            )
    message: dict[str, Any] = {"role": "assistant", "content": "\n".join(text_parts).strip()}
    if tool_calls:
        message["tool_calls"] = tool_calls
    return message


async def complete_chat(
    messages: list[dict[str, Any]],
    *,
    tools: list[dict[str, Any]] | None = None,
    max_tokens: int | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    provider = _infer_ai_provider()
    effective_max_tokens = max_tokens or settings.ai_max_tokens
    try:
        async with httpx.AsyncClient(timeout=settings.ai_request_timeout_seconds) as client:
            if provider == "anthropic":
                system_text, anthropic_messages = _convert_messages_for_anthropic(messages)
                payload: dict[str, Any] = {
                    "model": settings.ai_model,
                    "messages": anthropic_messages,
                    "max_tokens": effective_max_tokens,
                }
                if system_text:
                    payload["system"] = system_text
                if tools:
                    payload["tools"] = _convert_tools_for_anthropic(tools)
                resp = await client.post(
                    _resolve_ai_endpoint("messages"),
                    headers={
                        "x-api-key": settings.ai_api_key,
                        "anthropic-version": settings.ai_api_version,
                        "content-type": "application/json",
                    },
                    json=payload,
                )
                if resp.status_code >= 400:
                    return {"role": "assistant", "content": f"LLM error {resp.status_code}: {resp.text}"}
                return _normalize_anthropic_response(resp.json())

            headers = {"Content-Type": "application/json"}
            if settings.ai_api_key:
                headers["Authorization"] = f"Bearer {settings.ai_api_key}"
            payload = {
                "model": settings.ai_model,
                "messages": messages,
                "max_tokens": effective_max_tokens,
            }
            if tools:
                payload["tools"] = _convert_tools_for_openai(tools)
            endpoint = _resolve_ai_endpoint("chat/completions")
            resp = await client.post(endpoint, headers=headers, json=payload)
            if resp.status_code >= 400:
                retry_max_tokens = _suggest_retry_max_tokens(resp.text, effective_max_tokens)
                if retry_max_tokens and retry_max_tokens != effective_max_tokens:
                    retry_payload = dict(payload)
                    retry_payload["max_tokens"] = retry_max_tokens
                    resp = await client.post(endpoint, headers=headers, json=retry_payload)
            if resp.status_code >= 400:
                return {"role": "assistant", "content": f"LLM error {resp.status_code}: {resp.text}"}
            data = resp.json()
    except Exception as exc:
        return {"role": "assistant", "content": f"LLM request failed: {exc}"}

    try:
        return data["choices"][0]["message"]
    except Exception as exc:
        return {"role": "assistant", "content": f"LLM returned an unexpected response shape: {exc}"}


async def stream_chat(
    messages: list[dict[str, Any]],
    *,
    tools: list[dict[str, Any]] | None = None,
    max_tokens: int | None = None,
) -> AsyncGenerator[dict[str, Any], None]:
    settings = get_settings()
    provider = _infer_ai_provider()
    if provider != "openai":
        yield await complete_chat(messages, tools=tools, max_tokens=max_tokens)
        return

    headers = {"Content-Type": "application/json"}
    if settings.ai_api_key:
        headers["Authorization"] = f"Bearer {settings.ai_api_key}"
    payload: dict[str, Any] = {
        "model": settings.ai_model,
        "messages": messages,
        "max_tokens": max_tokens or settings.ai_max_tokens,
        "stream": True,
    }
    if tools:
        payload["tools"] = _convert_tools_for_openai(tools)

    endpoint = _resolve_ai_endpoint("chat/completions")
    full_content = ""
    full_tool_calls: dict[int, dict[str, Any]] = {}

    async def _stream_response(response: httpx.Response) -> AsyncGenerator[dict[str, Any], None]:
        nonlocal full_content
        async for line in response.aiter_lines():
            if not line.startswith("data: "):
                continue
            data_str = line[6:].strip()
            if data_str == "[DONE]":
                break
            try:
                chunk = json.loads(data_str)
                delta = chunk["choices"][0].get("delta", {})
                content = delta.get("content")
                if content:
                    full_content += content
                    yield {"role": "assistant", "content": content, "type": "chunk"}
                for tool_call in delta.get("tool_calls") or []:
                    index = tool_call.get("index", 0)
                    if index not in full_tool_calls:
                        full_tool_calls[index] = {
                            "id": tool_call.get("id"),
                            "type": "function",
                            "function": {"name": "", "arguments": ""},
                        }
                    function_delta = tool_call.get("function", {})
                    if function_delta.get("name"):
                        full_tool_calls[index]["function"]["name"] += function_delta["name"]
                    if function_delta.get("arguments"):
                        full_tool_calls[index]["function"]["arguments"] += function_delta["arguments"]
            except Exception:
                logger.exception("Error parsing centralized AI stream chunk.")

    try:
        async with httpx.AsyncClient(timeout=settings.ai_request_timeout_seconds) as client:
            async with client.stream("POST", endpoint, headers=headers, json=payload) as response:
                if response.status_code >= 400:
                    err_body = await response.aread()
                    err_text = err_body.decode(errors="replace")
                    retry_max_tokens = _suggest_retry_max_tokens(
                        err_text,
                        int(payload.get("max_tokens") or settings.ai_max_tokens),
                    )
                    if retry_max_tokens and retry_max_tokens != payload.get("max_tokens"):
                        retry_payload = dict(payload)
                        retry_payload["max_tokens"] = retry_max_tokens
                        async with client.stream("POST", endpoint, headers=headers, json=retry_payload) as response2:
                            if response2.status_code >= 400:
                                err_body2 = await response2.aread()
                                yield {
                                    "role": "assistant",
                                    "content": f"LLM error {response2.status_code}: {err_body2.decode(errors='replace')}",
                                }
                                return
                            async for chunk in _stream_response(response2):
                                yield chunk
                    else:
                        yield {"role": "assistant", "content": f"LLM error {response.status_code}: {err_text}"}
                        return
                else:
                    async for chunk in _stream_response(response):
                        yield chunk

        final_msg: dict[str, Any] = {"role": "assistant", "content": full_content}
        if full_tool_calls:
            final_msg["tool_calls"] = [tc for _, tc in sorted(full_tool_calls.items())]
        yield final_msg
    except Exception as exc:
        yield {"role": "assistant", "content": f"Streaming failed: {exc}"}
