import json
import logging
import os
import re
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger("uvicorn.error")

def parse_tool_arguments(arguments: Any) -> Dict[str, Any]:
    """
    Safely parses tool arguments from a string or returns the dictionary if already parsed.
    """
    if isinstance(arguments, dict):
        return arguments
    if not isinstance(arguments, str):
        return {}
    try:
        return json.loads(arguments)
    except json.JSONDecodeError:
        return {}

def _normalize_function_markup(text: str) -> str:
    return (text or "").replace("｜", "|")

def _parse_dsml_parameter_value(raw_value: str, force_string: bool) -> Any:
    value = (raw_value or "").strip()
    if force_string:
        return value
    if not value:
        return ""
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        lowered = value.lower()
        if lowered == "true": return True
        if lowered == "false": return False
        if lowered == "null": return None
        return value

def extract_dsml_invoke_markup(text: str) -> Optional[Dict[str, Any]]:
    normalized = _normalize_function_markup(text)
    invoke_match = re.search(
        r"<\|?DSML\|?invoke\s+name=\"([a-zA-Z0-9_]+)\"\s*>(.*?)</\|?DSML\|?invoke>",
        normalized,
        re.DOTALL | re.IGNORECASE,
    )
    if not invoke_match:
        return None

    function_name = invoke_match.group(1).strip()
    param_block = invoke_match.group(2) or ""

    args: Dict[str, Any] = {}
    for parameter_match in re.finditer(
        r"<\|?DSML\|?parameter\s+name=\"([^\"]+)\"(?:\s+string=\"(true|false)\")?\s*>(.*?)</\|?DSML\|?parameter>",
        param_block,
        re.DOTALL | re.IGNORECASE,
    ):
        key = (parameter_match.group(1) or "").strip()
        if not key:
            continue
        force_string = (parameter_match.group(2) or "").lower() == "true"
        raw_value = parameter_match.group(3) or ""
        args[key] = _parse_dsml_parameter_value(raw_value, force_string)

    return tool_call_message(function_name, json.dumps(args, ensure_ascii=False))

def extract_function_markup(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    normalized = _normalize_function_markup(text)

    match = re.search(
        r"<function=([a-zA-Z0-9_]+)\s*>?\s*(\{.*?\})\s*</function>",
        normalized,
        re.DOTALL,
    )
    if match:
        function_name = match.group(1).strip()
        arguments = match.group(2).strip()
        return tool_call_message(function_name, arguments)

    return extract_dsml_invoke_markup(normalized)

def tool_call_message(name: str, arguments: str) -> Dict[str, Any]:
    return {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "id": f"recovered_{uuid.uuid4().hex}",
                "type": "function",
                "function": {
                    "name": name,
                    "arguments": arguments,
                },
            }
        ],
    }

def looks_like_tool_markup(text: str) -> bool:
    normalized = _normalize_function_markup(text).lower()
    if not normalized:
        return False
    markers = (
        "<function=",
        "<function_calls",
        "<|dsml|function_calls>",
        "<|dsml|invoke ",
        "<tool_call",
    )
    return any(marker in normalized for marker in markers)

def recover_tool_call_from_error(error_text: str) -> Optional[Dict[str, Any]]:
    markup = extract_function_markup(error_text)
    if markup is not None:
        return markup
    try:
        payload = json.loads(error_text)
    except json.JSONDecodeError:
        return None
    
    if isinstance(payload, dict):
        failed_generation = payload.get("error", {}).get("failed_generation")
        if isinstance(failed_generation, str):
            try:
                maybe_calls = json.loads(failed_generation)
            except json.JSONDecodeError:
                maybe_calls = None
            recovered = _tool_calls_from_groq_list(maybe_calls)
            if recovered is not None:
                return recovered
    
    failed_generation = (
        payload.get("error", {}).get("failed_generation")
        if isinstance(payload, dict)
        else None
    )
    if not isinstance(failed_generation, str):
        return None
    return extract_function_markup(failed_generation)

def recover_tool_call_from_message(message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if message.get("tool_calls"):
        return None
    content = message.get("content")
    if not isinstance(content, str):
        return None
    return extract_function_markup(content)

def _tool_calls_from_groq_list(value: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(value, list) or not value:
        return None
    call = value[0]
    if not isinstance(call, dict):
        return None
    name = call.get("name")
    params = call.get("parameters")
    if not isinstance(name, str) or not isinstance(params, dict):
        return None
    sanitized = sanitize_tool_args(name, params)
    return tool_call_message(name, json.dumps(sanitized, ensure_ascii=False))

def sanitize_tool_args(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    cleaned: Dict[str, Any] = {}
    for k, v in (args or {}).items():
        if v is None:
            continue
        cleaned[k] = v
    
    if tool_name == "mcp_query" or tool_name == "aura-query":
        if "count_only" not in cleaned:
            cleaned["count_only"] = False
        if "limit" not in cleaned:
            cleaned["limit"] = 100
        if "params" in cleaned and not isinstance(cleaned["params"], dict):
            cleaned["params"] = {}
        if "filters" in cleaned and not isinstance(cleaned["filters"], dict):
            cleaned["filters"] = {}
            
    if tool_name in {"school_admin_action", "student_import_action"}:
        if "payload" in cleaned and cleaned["payload"] is None:
            cleaned["payload"] = {}
            
    if tool_name in {"backend_action", "backend_report"}:
        if "query" in cleaned and not isinstance(cleaned["query"], dict):
            cleaned["query"] = {}
            
    if tool_name == "backend_action":
        if "body" in cleaned and not isinstance(cleaned["body"], dict):
            cleaned["body"] = {}
        if "method" in cleaned:
            cleaned["method"] = str(cleaned["method"]).strip().upper()
    return cleaned

def convert_tools_for_anthropic(tools: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    converted: List[Dict[str, Any]] = []
    for tool in tools or []:
        # Standard MCP tool shape handle
        name = tool.get("name") # MCP format
        description = tool.get("description")
        input_schema = tool.get("input_schema") or tool.get("inputSchema")
        
        # Backward compatibility for v1 tool shape handle
        if not name and "function" in tool:
            name = tool["function"].get("name")
            description = tool["function"].get("description")
            input_schema = tool["function"].get("parameters")

        converted.append(
            {
                "name": name,
                "description": description or "",
                "input_schema": input_schema or {"type": "object", "properties": {}},
            }
        )
    return converted

def convert_tools_for_gemini(tools: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    declarations: List[Dict[str, Any]] = []
    for tool in tools or []:
        name = tool.get("name")
        description = tool.get("description")
        parameters = tool.get("input_schema") or tool.get("inputSchema")
        
        if not name and "function" in tool:
            name = tool["function"].get("name")
            description = tool["function"].get("description")
            parameters = tool["function"].get("parameters")

        declarations.append(
            {
                "name": name,
                "description": description or "",
                "parameters": parameters or {"type": "object", "properties": {}},
            }
        )
    return [{"functionDeclarations": declarations}] if declarations else []

def convert_tools_for_openai(tools: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    converted: List[Dict[str, Any]] = []
    for tool in tools or []:
        name = tool.get("name")
        description = tool.get("description")
        parameters = tool.get("input_schema") or tool.get("inputSchema")
        
        if not name and "function" in tool:
            name = tool["function"].get("name")
            description = tool["function"].get("description")
            parameters = tool["function"].get("parameters")

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
