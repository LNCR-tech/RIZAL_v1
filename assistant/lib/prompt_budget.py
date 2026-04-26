from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Optional


def estimate_tokens_from_text(text: str) -> int:
    """
    Very rough token estimator for OpenAI-compatible chat payloads.

    We intentionally avoid model-specific tokenizers because this assistant can be
    pointed at different providers/models. This is a conservative heuristic.
    """
    if not text:
        return 0
    # Common rough heuristic: ~4 characters per token for English-ish text/JSON.
    return max(1, len(text) // 4)


def estimate_tokens_from_messages(messages: List[Dict[str, Any]]) -> int:
    total = 0
    for msg in messages or []:
        # Per-message overhead (role separators, etc.). Keep small but non-zero.
        total += 6
        role = str(msg.get("role") or "")
        total += estimate_tokens_from_text(role)
        content = msg.get("content")
        if isinstance(content, str):
            total += estimate_tokens_from_text(content)
        elif isinstance(content, (dict, list)):
            total += estimate_tokens_from_text(json.dumps(content, ensure_ascii=False))
        elif content is not None:
            total += estimate_tokens_from_text(str(content))
    return total


def estimate_tokens_from_tools(tools: Optional[List[Dict[str, Any]]]) -> int:
    if not tools:
        return 0
    try:
        blob = json.dumps(tools, ensure_ascii=False)
    except Exception:
        blob = str(tools)
    # Tools are usually dense JSON; the 4-chars/token heuristic is reasonable.
    return estimate_tokens_from_text(blob)


def estimate_total_prompt_tokens(
    *,
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]] = None,
) -> int:
    return estimate_tokens_from_messages(messages) + estimate_tokens_from_tools(tools)

