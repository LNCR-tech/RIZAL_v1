import json
import logging
import os
import re
import uuid
import httpx
from typing import Any, Dict, List, Optional, AsyncGenerator

logger = logging.getLogger("uvicorn.error")

# --- AI Configuration (Verbatim from v1) ---
AI_PROVIDER = (os.getenv("AI_PROVIDER") or "").strip().lower()
AI_API_KEY = (
    os.getenv("AI_API_KEY")
    or os.getenv("OPENAI_API_KEY")
    or os.getenv("ANTHROPIC_API_KEY")
    or os.getenv("GEMINI_API_KEY")
)
AI_API_BASE = (
    os.getenv("AI_API_BASE")
    or os.getenv("OPENAI_API_BASE")
    or os.getenv("ANTHROPIC_API_BASE")
    or os.getenv("GEMINI_API_BASE")
    or ""
)
AI_MODEL = (
    os.getenv("AI_MODEL")
    or os.getenv("OPENAI_MODEL")
    or os.getenv("ANTHROPIC_MODEL")
    or os.getenv("GEMINI_MODEL")
    or "gpt-4o-mini"
)
try:
    AI_MAX_TOKENS = max(
        1,
        int(
            os.getenv("AI_MAX_TOKENS")
            or os.getenv("OPENAI_MAX_TOKENS")
            or os.getenv("ANTHROPIC_MAX_TOKENS")
            or os.getenv("GEMINI_MAX_TOKENS")
            or "1024"
        ),
    )
except (ValueError, TypeError):
    AI_MAX_TOKENS = 1024

AI_API_VERSION = (
    os.getenv("AI_API_VERSION")
    or os.getenv("ANTHROPIC_VERSION")
    or os.getenv("ANTHROPIC_API_VERSION")
    or "2023-06-01"
).strip()

def _infer_ai_provider() -> str:
    explicit = AI_PROVIDER.strip().lower()
    if explicit in {"openai", "openai_compatible", "openai-compatible", "compatible"}:
        return "openai"
    if explicit in {"anthropic", "claude"}:
        return "anthropic"
    if explicit in {"gemini", "google", "google_ai", "google-ai"}:
        return "gemini"

    base_url = AI_API_BASE.lower()
    model_name = AI_MODEL.lower()
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

def _normalize_base_url(value: str) -> str:
    return str(value or "").strip().rstrip("/")

def _effective_ai_base_url(provider: Optional[str] = None) -> str:
    resolved_provider = provider or _infer_ai_provider()
    configured_base = _normalize_base_url(AI_API_BASE)
    if configured_base:
        return configured_base
    return _default_ai_base_url(resolved_provider)

def _resolve_ai_endpoint(path: str) -> str:
    base = _effective_ai_base_url().rstrip("/")
    suffix = "/" + path.lstrip("/")
    if base.endswith(suffix):
        return base
    return f"{base}{suffix}"

def _resolve_gemini_endpoint() -> str:
    base = _effective_ai_base_url("gemini").rstrip("/")
    if ":generateContent" in base:
        return base
    if base.endswith("/models"):
        return f"{base}/{AI_MODEL}:generateContent"
    if "/models/" in base:
        return f"{base}:generateContent"
    return f"{base}/models/{AI_MODEL}:generateContent"

def _extract_text_content(content: Any) -> str:
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
        parts: List[str] = []
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

def _suggest_retry_max_tokens(error_text: str, current_max_tokens: int) -> Optional[int]:
    text_value = str(error_text or "")
    affordable_match = re.search(r"can only afford (\d+)", text_value, re.IGNORECASE)
    if affordable_match:
        try:
            affordable_tokens = int(affordable_match.group(1))
        except ValueError:
            affordable_tokens = 0
        if affordable_tokens > 0 and affordable_tokens < current_max_tokens:
            return max(64, affordable_tokens)
    if "fewer max_tokens" in text_value.lower() and current_max_tokens > 128:
        return max(64, current_max_tokens // 2)
    return None

def _convert_messages_for_anthropic(messages: List[Dict[str, Any]]) -> tuple[str, List[Dict[str, Any]]]:
    system_parts: List[str] = []
    converted: List[Dict[str, Any]] = []
    for message in messages:
        role = message.get("role")
        if role == "system":
            content = _extract_text_content(message.get("content"))
            if content:
                system_parts.append(content)
            continue
        if role == "assistant":
            assistant_parts: List[Dict[str, Any]] = []
            content = _extract_text_content(message.get("content"))
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
            if isinstance(tool_content, (dict, list)):
                tool_content_text = json.dumps(tool_content, ensure_ascii=False)
            else:
                tool_content_text = str(tool_content or "")
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
        converted.append({"role": "user", "content": _extract_text_content(message.get("content")) or ""})
    return "\n\n".join(part for part in system_parts if part).strip(), converted

def _convert_messages_for_gemini(messages: List[Dict[str, Any]]) -> tuple[str, List[Dict[str, Any]]]:
    system_parts: List[str] = []
    converted: List[Dict[str, Any]] = []
    for message in messages:
        role = message.get("role")
        if role == "system":
            content = _extract_text_content(message.get("content"))
            if content:
                system_parts.append(content)
            continue
        if role == "assistant":
            parts: List[Dict[str, Any]] = []
            content = _extract_text_content(message.get("content"))
            if content:
                parts.append({"text": content})
            for tool_call in message.get("tool_calls") or []:
                tool_function = tool_call.get("function") or {}
                parts.append(
                    {
                        "functionCall": {
                            "name": tool_function.get("name") or "tool",
                            "args": _safe_json_load(tool_function.get("arguments"), {}),
                        }
                    }
                )
            converted.append({"role": "model", "parts": parts or [{"text": ""}]})
            continue
        if role == "tool":
            tool_content = message.get("content")
            parsed_tool_content = _safe_json_load(tool_content, {"content": str(tool_content or "")})
            if not isinstance(parsed_tool_content, dict):
                parsed_tool_content = {"content": parsed_tool_content}
            converted.append(
                {
                    "role": "user",
                    "parts": [
                        {
                            "functionResponse": {
                                "name": message.get("name") or "tool",
                                "response": parsed_tool_content,
                            }
                        }
                    ],
                }
            )
            continue
        converted.append(
            {
                "role": "user",
                "parts": [{"text": _extract_text_content(message.get("content")) or ""}],
            }
        )
    return "\n\n".join(part for part in system_parts if part).strip(), converted

def _normalize_anthropic_response(data: Dict[str, Any]) -> Dict[str, Any]:
    content_blocks = data.get("content") or []
    text_parts: List[str] = []
    tool_calls: List[Dict[str, Any]] = []
    for block in content_blocks:
        if not isinstance(block, dict):
            continue
        block_type = block.get("type")
        if block_type == "text" and isinstance(block.get("text"), str):
            text_parts.append(block.get("text") or "")
        if block_type == "tool_use":
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
    message: Dict[str, Any] = {
        "role": "assistant",
        "content": "\n".join(part for part in text_parts if part).strip(),
    }
    if tool_calls:
        message["tool_calls"] = tool_calls
    return message

def _normalize_gemini_response(data: Dict[str, Any]) -> Dict[str, Any]:
    candidates = data.get("candidates") or []
    if not candidates:
        return {"content": "LLM returned no candidates."}
    parts = ((candidates[0] or {}).get("content") or {}).get("parts") or []
    text_parts: List[str] = []
    tool_calls: List[Dict[str, Any]] = []
    for part in parts:
        if not isinstance(part, dict):
            continue
        if isinstance(part.get("text"), str):
            text_parts.append(part.get("text") or "")
        function_call = part.get("functionCall")
        if isinstance(function_call, dict):
            tool_calls.append(
                {
                    "id": function_call.get("id") or f"tool_{uuid.uuid4().hex}",
                    "type": "function",
                    "function": {
                        "name": function_call.get("name") or "tool",
                        "arguments": json.dumps(function_call.get("args") or {}, ensure_ascii=False),
                    },
                }
            )
    message: Dict[str, Any] = {
        "role": "assistant",
        "content": "\n".join(part for part in text_parts if part).strip(),
    }
    if tool_calls:
        message["tool_calls"] = tool_calls
    return message

async def call_openai(messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    provider = _infer_ai_provider()
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            if provider == "anthropic":
                try:
                    from .tools_logic import convert_tools_for_anthropic
                except ImportError:
                    return {"content": "Anthropic SDK dependencies are missing. Please install 'anthropic'."}

                system_text, anthropic_messages = _convert_messages_for_anthropic(messages)
                payload: Dict[str, Any] = {
                    "model": AI_MODEL,
                    "messages": anthropic_messages,
                    "max_tokens": AI_MAX_TOKENS,
                }
                if system_text:
                    payload["system"] = system_text
                if tools:
                    payload["tools"] = convert_tools_for_anthropic(tools)
                
                resp = await client.post(
                    _resolve_ai_endpoint("messages"),
                    headers={
                        "x-api-key": AI_API_KEY,
                        "anthropic-version": AI_API_VERSION,
                        "content-type": "application/json",
                    },
                    json=payload,
                )
                if resp.status_code >= 400:
                    return {"content": f"LLM error {resp.status_code}: {resp.text}"}
                data = resp.json()
                return _normalize_anthropic_response(data)

            if provider == "gemini":
                system_text, gemini_messages = _convert_messages_for_gemini(messages)
                payload = {
                    "contents": gemini_messages,
                    "generationConfig": {
                        "maxOutputTokens": AI_MAX_TOKENS,
                    },
                }
                if tools:
                    from .tools_logic import convert_tools_for_gemini
                    payload["tools"] = convert_tools_for_gemini(tools)
                if system_text:
                    payload["systemInstruction"] = {"parts": [{"text": system_text}]}
                
                url = _resolve_gemini_endpoint()
                headers = {"content-type": "application/json"}
                if "generativelanguage.googleapis.com" in url:
                    separator = "&" if "?" in url else "?"
                    url = f"{url}{separator}key={AI_API_KEY}"
                else:
                    headers["Authorization"] = f"Bearer {AI_API_KEY}"
                
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code >= 400:
                    return {"content": f"LLM error {resp.status_code}: {resp.text}"}
                data = resp.json()
                return _normalize_gemini_response(data)

            # OpenAI Default
            headers = {"Content-Type": "application/json"}
            if AI_API_KEY:
                headers["Authorization"] = f"Bearer {AI_API_KEY}"
            payload = {"model": AI_MODEL, "messages": messages, "max_tokens": AI_MAX_TOKENS}
            if tools:
                from .tools_logic import convert_tools_for_openai
                payload["tools"] = convert_tools_for_openai(tools)
            
            endpoint = _resolve_ai_endpoint("chat/completions")
            resp = await client.post(endpoint, headers=headers, json=payload)
            if resp.status_code >= 400:
                retry_max_tokens = _suggest_retry_max_tokens(resp.text, AI_MAX_TOKENS)
                if retry_max_tokens and retry_max_tokens != AI_MAX_TOKENS:
                    retry_payload = dict(payload)
                    retry_payload["max_tokens"] = retry_max_tokens
                    resp = await client.post(endpoint, headers=headers, json=retry_payload)
            
            if resp.status_code >= 400:
                from .tools_logic import recover_tool_call_from_error
                recovered_tool_call = recover_tool_call_from_error(resp.text)
                if recovered_tool_call is not None:
                    return recovered_tool_call
                return {"content": f"LLM error {resp.status_code}: {resp.text}"}
            data = resp.json()
    except Exception as exc:
        return {"content": f"LLM request failed: {exc}"}

    try:
        message = data["choices"][0]["message"]
        from .tools_logic import recover_tool_call_from_message
        recovered_tool_call = recover_tool_call_from_message(message)
        if recovered_tool_call is not None:
            return recovered_tool_call
        return message
    except Exception as exc:
        return {"content": f"LLM returned an unexpected response shape: {exc}"}

async def call_llm_stream(messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Generic SSE streaming generator for LLM providers.
    Yields intermediate text chunks and a final message object.
    """
    provider = _infer_ai_provider()
    if provider != "openai":
        # Fallback to non-streaming for now for Anthropic/Gemini to keep it simple, 
        # but yield as a single 'final' event.
        res = await call_openai(messages, tools=tools)
        yield res
        return

    # OpenAI-Compatible Streaming
    headers = {"Content-Type": "application/json"}
    if AI_API_KEY:
        headers["Authorization"] = f"Bearer {AI_API_KEY}"
    
    payload = {
        "model": AI_MODEL, 
        "messages": messages, 
        "max_tokens": AI_MAX_TOKENS, 
        "stream": True
    }
    if tools:
        from .tools_logic import convert_tools_for_openai
        payload["tools"] = convert_tools_for_openai(tools)
    
    endpoint = _resolve_ai_endpoint("chat/completions")
    
    full_content = ""
    full_tool_calls: Dict[int, Dict[str, Any]] = {}

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream("POST", endpoint, headers=headers, json=payload) as response:
                if response.status_code >= 400:
                    err_body = await response.aread()
                    yield {"role": "assistant", "content": f"LLM error {response.status_code}: {err_body.decode()}"}
                    return

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break
                    
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk["choices"][0].get("delta", {})
                        
                        # Handle Text Content
                        content = delta.get("content")
                        if content:
                            full_content += content
                            yield {"role": "assistant", "content": content, "type": "chunk"}
                        
                        # Handle Tool Calls (Accumulate)
                        tool_calls = delta.get("tool_calls")
                        if tool_calls:
                            for tc in tool_calls:
                                index = tc.get("index", 0)
                                if index not in full_tool_calls:
                                    full_tool_calls[index] = {
                                        "id": tc.get("id"),
                                        "type": "function",
                                        "function": {"name": "", "arguments": ""}
                                    }
                                
                                func_delta = tc.get("function", {})
                                if func_delta.get("name"):
                                    full_tool_calls[index]["function"]["name"] += func_delta["name"]
                                if func_delta.get("arguments"):
                                    full_tool_calls[index]["function"]["arguments"] += func_delta["arguments"]
                                    
                    except Exception as e:
                        logger.error(f"Error parsing SSE chunk: {e}")

        # Final Yield: The complete message for the recursive logic to process
        final_msg = {"role": "assistant", "content": full_content}
        if full_tool_calls:
            final_msg["tool_calls"] = [tc for i, tc in sorted(full_tool_calls.items())]
        
        yield final_msg

    except Exception as e:
        yield {"role": "assistant", "content": f"Streaming failed: {e}"}

