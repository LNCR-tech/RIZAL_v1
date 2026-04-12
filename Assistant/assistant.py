"""Agentic assistant API (role-aware, streaming, conversation history).

Run:
  uvicorn assistant:app --reload

Environment variables:
  DATABASE_URL           PostgreSQL connection string
  JWT_SECRET             JWT HMAC secret (or set JWT_PUBLIC_KEY for RS256)
  JWT_ALGORITHM          Default: HS256
  JWT_PUBLIC_KEY         Optional PEM for RS256 verification
  OPENAI_API_KEY         Optional, used for LLM calls
  OPENAI_API_BASE        Optional, default: https://api.openai.com/v1
  OPENAI_MODEL           Optional, default: gpt-4o
  ASSISTANT_AUTO_MIGRATE Optional, default: true
  MCP_SCHEMA_URL         Optional, role-scoped schema service endpoint
  MCP_QUERY_URL          Optional, role-scoped query service endpoint
"""

from __future__ import annotations

import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Generator, List, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text, create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

MCP_DIR = os.path.join(os.path.dirname(__file__), "mcp")
if MCP_DIR not in sys.path:
    sys.path.insert(0, MCP_DIR)

from policy import (
    get_effective_policy,
    normalize_permission,
    normalize_role,
    summarize_scope_rules,
)

try:
    from jose import JWTError, jwt
except Exception:  # pragma: no cover - dependency may be missing in some setups
    jwt = None
    JWTError = Exception


APP_DATABASE_URL = os.getenv("APP_DATABASE_URL") or os.getenv("TENANT_DATABASE_URL") or os.getenv("DATABASE_URL")
ASSISTANT_DB_URL = os.getenv("ASSISTANT_DB_URL") or APP_DATABASE_URL
ASSISTANT_DB_SCHEMA = os.getenv("ASSISTANT_DB_SCHEMA", "public")
JWT_SECRETS = list(
    dict.fromkeys(
        secret
        for secret in (
            os.getenv("SECRET_KEY"),  # Backend token signer uses SECRET_KEY
            os.getenv("JWT_SECRET"),  # Legacy/alternate config key
        )
        if secret
    )
)
JWT_PUBLIC_KEY = os.getenv("JWT_PUBLIC_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
try:
    OPENAI_MAX_TOKENS = max(1, int(os.getenv("OPENAI_MAX_TOKENS", "1024")))
except ValueError:
    OPENAI_MAX_TOKENS = 1024
ASSISTANT_AUTO_MIGRATE = os.getenv("ASSISTANT_AUTO_MIGRATE", "true").lower() == "true"
MCP_SCHEMA_URL = os.getenv("MCP_SCHEMA_URL") or "http://127.0.0.1:8500/mcp/schema/schema"
MCP_QUERY_URL = os.getenv("MCP_QUERY_URL") or "http://127.0.0.1:8500/mcp/query/query"
MCP_SCHOOL_ADMIN_URL = os.getenv("MCP_SCHOOL_ADMIN_URL") or "http://127.0.0.1:8500/mcp/school-admin/action"
MCP_STUDENT_IMPORT_URL = os.getenv("MCP_STUDENT_IMPORT_URL") or "http://127.0.0.1:8500/mcp/student-import/action"
ASSISTANT_CONTEXT_MAX_MESSAGES = os.getenv("ASSISTANT_CONTEXT_MAX_MESSAGES")

if not ASSISTANT_DB_URL:
    raise RuntimeError("ASSISTANT_DB_URL is required for assistant storage.")

# Assistant storage engine (conversations, messages)
engine = create_engine(ASSISTANT_DB_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Tenant application engine (VALID8 data)
if APP_DATABASE_URL:
    app_engine = create_engine(APP_DATABASE_URL, pool_pre_ping=True)
    AppSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=app_engine)
else:
    app_engine = None
    AppSessionLocal = None

Base = declarative_base()


class Conversation(Base):
    __tablename__ = "assistant_conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(128), index=True, nullable=False)
    user_role = Column(String(64), nullable=False)
    title = Column(String(255), nullable=True)
    status = Column(String(32), nullable=False, server_default="active")
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Message(Base):
    __tablename__ = "assistant_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(
        String(36),
        ForeignKey("assistant_conversations.id"),
        index=True,
        nullable=False,
    )
    role = Column(String(32), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class DailyUsage(Base):
    __tablename__ = "assistant_daily_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(128), index=True, nullable=False)
    user_role = Column(String(64), index=True, nullable=False)
    usage_date = Column(Date, index=True, nullable=False)
    message_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class AssistantRequest(BaseModel):
    message: str = Field(..., min_length=1)
    user_id: Optional[str] = Field(default=None, min_length=1)
    user_role: Optional[str] = Field(default=None, min_length=1)
    user_name: Optional[str] = None
    user_school: Optional[str] = None
    user_school_id: Optional[int] = None
    user_timezone: Optional[str] = None
    conversation_id: Optional[str] = None


class ConversationSummary(BaseModel):
    conversation_id: str
    title: Optional[str]
    last_message: Optional[str]
    updated_at: datetime


class ConversationDetail(BaseModel):
    conversation_id: str
    title: Optional[str]
    messages: List[Dict[str, Any]]


class ConversationUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=80)


app = FastAPI(
    title="Agentic Assistant API",
    openapi_url="/__assistant__/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Integrated MCP sub-apps (Role-scoped tools)
from mcp.schema_server import app as schema_app
from mcp.query_server import app as query_app
from mcp.school_admin_server import app as school_admin_app
from mcp.student_import_server import app as student_import_app

app.mount("/mcp/schema", schema_app)
app.mount("/mcp/query", query_app)
app.mount("/mcp/school-admin", school_admin_app)
app.mount("/mcp/student-import", student_import_app)

# Dev-friendly CORS (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def init_db() -> None:
    if ASSISTANT_AUTO_MIGRATE:
        Base.metadata.create_all(bind=engine)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> Dict[str, str]:
    # Lightweight health endpoint for docker compose / probes.
    return {"status": "ok"}


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _decode_jwt(token: str) -> Dict[str, Any]:
    if not jwt:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="python-jose is required to verify JWTs.",
        )
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    last_error: Optional[Exception] = None

    # Prefer asymmetric verification when configured, but allow HMAC fallback for mixed deployments.
    if JWT_PUBLIC_KEY:
        try:
            return jwt.decode(token, JWT_PUBLIC_KEY, algorithms=[JWT_ALGORITHM])
        except JWTError as exc:
            last_error = exc

    if not JWT_SECRETS:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SECRET_KEY/JWT_SECRET or JWT_PUBLIC_KEY must be configured.",
        )

    for secret in JWT_SECRETS:
        try:
            return jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
        except JWTError as exc:
            last_error = exc

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from last_error


def get_current_identity(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Authorization header")
    token = authorization.split(" ", 1)[1].strip()
    payload = _decode_jwt(token)
    return payload


def _get_token_user_id(identity: Dict[str, Any]) -> str:
    # Prefer an explicit numeric/opaque `user_id` claim when present.
    # Many tenant apps use `sub` as an email, which breaks DB joins expecting an integer user_id.
    token_user_id = str(identity.get("user_id") or identity.get("sub") or "")
    if not token_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing user identity in token")
    return token_user_id


def _ensure_user_match(identity: Dict[str, Any], body: AssistantRequest) -> str:
    token_user_id = _get_token_user_id(identity)
    if body.user_id and token_user_id != str(body.user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="user_id mismatch")
    return token_user_id



ROLE_PRIORITY = ["admin", "campus_admin", "ssg", "sg", "org", "student"]


def _get_roles_from_identity(identity: Dict[str, Any], body_role: Optional[str]) -> tuple[str, list[str]]:
    raw_roles = identity.get("roles") or identity.get("role") or identity.get("user_role") or []
    if isinstance(raw_roles, str):
        raw_roles = [raw_roles]

    normalized_roles: list[str] = []
    seen = set()
    for role in raw_roles:
        normalized = normalize_role(role)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        normalized_roles.append(normalized)

    if not normalized_roles:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing user role in token")

    requested_role = normalize_role(body_role or "")
    if requested_role and requested_role not in seen:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="user_role mismatch")

    if requested_role:
        primary_role = requested_role
    else:
        primary_role = next((role for role in ROLE_PRIORITY if role in seen), normalized_roles[0])

    sorted_roles = [role for role in ROLE_PRIORITY if role in seen]
    for role in normalized_roles:
        if role not in sorted_roles:
            sorted_roles.append(role)

    return primary_role, sorted_roles


def _get_permissions_from_identity(identity: Dict[str, Any]) -> list[str]:
    raw_permissions = (
        identity.get("permissions")
        or identity.get("permission_codes")
        or identity.get("governance_permissions")
        or []
    )
    if isinstance(raw_permissions, str):
        raw_permissions = [raw_permissions]

    normalized_permissions: list[str] = []
    seen = set()
    for permission in raw_permissions:
        normalized = normalize_permission(permission)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        normalized_permissions.append(normalized)
    return normalized_permissions


def _create_conversation(db: Session, user_id: str, user_role: str, title: Optional[str]) -> Conversation:
    convo = Conversation(user_id=user_id, user_role=user_role, title=title)
    db.add(convo)
    db.commit()
    db.refresh(convo)
    return convo


def _get_owned_conversation(db: Session, conversation_id: str, user_id: str) -> Conversation:
    convo = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .first()
    )
    if not convo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return convo


def _get_daily_limit(roles: List[str]) -> int:
    role_set = set(roles)
    if "admin" in role_set:
        return 500
    if "campus_admin" in role_set:
        return 200
    if role_set.intersection({"ssg", "sg"}):
        return 120
    return 50


def _enforce_daily_limit(db: Session, user_id: str, user_role: str, effective_roles: List[str]) -> None:
    today = datetime.now(timezone.utc).date()
    row = (
        db.query(DailyUsage)
        .filter(
            DailyUsage.user_id == user_id,
            DailyUsage.user_role == user_role,
            DailyUsage.usage_date == today,
        )
        .first()
    )
    if row is None:
        row = DailyUsage(
            user_id=user_id,
            user_role=user_role,
            usage_date=today,
            message_count=0,
        )
        db.add(row)
        db.commit()
        db.refresh(row)

    limit = _get_daily_limit(effective_roles)
    if row.message_count >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily limit reached ({limit} messages).",
        )

    row.message_count += 1
    row.updated_at = datetime.now(timezone.utc)
    db.commit()


def _load_system_prompt() -> str:
    prompt_path = os.path.join(os.path.dirname(__file__), "system_prompt.txt")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return "You are a helpful assistant for the VALID8 system. Use tools when necessary to answer user questions about data."


def _render_system_prompt(
    template: str,
    *,
    user_id: str,
    user_role: str,
    effective_roles: str,
    effective_permissions: str,
    user_name: Optional[str],
    user_school: Optional[str],
    user_school_id: Optional[int],
    user_timezone: str,
    readable_tables: str,
    writable_tables: str,
    scope_rules: str,
    capability_notes: str,
    non_capability_notes: str,
) -> str:
    utc_now = datetime.now(timezone.utc)
    local_now = utc_now
    try:
        local_now = utc_now.astimezone(ZoneInfo(user_timezone))
    except ZoneInfoNotFoundError:
        user_timezone = "UTC"
    now_iso = local_now.isoformat()
    safe_name = user_name or "User"
    safe_school = user_school or "Unknown"
    safe_school_id = str(user_school_id) if user_school_id is not None else "Unknown"
    return (
        template.replace("{datetime}", now_iso)
        .replace("{user_id}", user_id)
        .replace("{user_role}", user_role)
        .replace("{effective_roles}", effective_roles)
        .replace("{effective_permissions}", effective_permissions)
        .replace("{user_name}", safe_name)
        .replace("{user_school}", safe_school)
        .replace("{user_school_id}", safe_school_id)
        .replace("{user_timezone}", user_timezone)
        .replace("{readable_tables}", readable_tables)
        .replace("{writable_tables}", writable_tables)
        .replace("{scope_rules}", scope_rules)
        .replace("{capability_notes}", capability_notes)
        .replace("{non_capability_notes}", non_capability_notes)
    )


def _get_effective_timezone(identity: Dict[str, Any], body: AssistantRequest) -> str:
    raw_timezone = (
        body.user_timezone
        or identity.get("timezone")
        or identity.get("user_timezone")
        or identity.get("tenant_timezone")
        or identity.get("school_timezone")
        or "UTC"
    )
    timezone_name = str(raw_timezone).strip() or "UTC"
    try:
        ZoneInfo(timezone_name)
        return timezone_name
    except ZoneInfoNotFoundError as exc:
        if body.user_timezone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported user_timezone: {body.user_timezone}",
            ) from exc
        return "UTC"


def _render_role_capabilities(roles: List[str], permissions: List[str]) -> tuple[str, str, str, str, str]:
    policy = get_effective_policy(roles, permissions)
    readable_tables = ", ".join(sorted(policy.allowed_tables)) or "none"
    writable_tables = ", ".join(sorted(policy.allowed_write_tables)) or "none"
    scope_rules = "; ".join(summarize_scope_rules(policy)) or "none"
    capability_notes = "; ".join(policy.capability_notes) or "none"
    non_capability_notes = "; ".join(policy.non_capability_notes) or "none"

    return readable_tables, writable_tables, scope_rules, capability_notes, non_capability_notes


def _append_message(db: Session, conversation_id: str, role: str, content: str) -> Message:
    msg = Message(conversation_id=conversation_id, role=role, content=content)
    db.add(msg)
    convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if convo:
        now = datetime.now(timezone.utc)
        convo.last_message_at = now
        convo.updated_at = now
    db.commit()
    db.refresh(msg)
    return msg


async def _call_openai(messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    if not OPENAI_API_KEY:
        return {"content": "LLM is not configured. Set OPENAI_API_KEY."}
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": OPENAI_MODEL, "messages": messages, "max_tokens": OPENAI_MAX_TOKENS}
    if tools:
        payload["tools"] = tools

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(f"{OPENAI_API_BASE}/chat/completions", headers=headers, json=payload)
            if resp.status_code >= 400:
                recovered_tool_call = _recover_tool_call_from_error(resp.text)
                if recovered_tool_call is not None:
                    return recovered_tool_call
                return {"content": f"LLM error {resp.status_code}: {resp.text}"}
            data = resp.json()
    except httpx.HTTPError as exc:
        return {"content": f"LLM request failed: {exc}"}
    except ValueError as exc:
        return {"content": f"LLM returned invalid JSON: {exc}"}

    try:
        message = data["choices"][0]["message"]
        recovered_tool_call = _recover_tool_call_from_message(message)
        if recovered_tool_call is not None:
            return recovered_tool_call
        return message
    except (KeyError, IndexError, TypeError) as exc:
        return {"content": f"LLM returned an unexpected response shape: {exc}"}


async def _call_openai_json(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """Best-effort JSON-mode call for validators (temperature=0, JSON object output)."""
    if not OPENAI_API_KEY:
        return {"content": '{"error":"llm_not_configured"}'}

    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    base_payload: Dict[str, Any] = {
        "model": OPENAI_MODEL,
        "messages": messages,
        "temperature": 0,
        "max_tokens": 200,
    }

    # Some providers support response_format; some reject it. We'll try and fall back.
    payload = dict(base_payload)
    payload["response_format"] = {"type": "json_object"}

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(f"{OPENAI_API_BASE}/chat/completions", headers=headers, json=payload)
            if resp.status_code >= 400:
                payload = dict(base_payload)
                resp = await client.post(f"{OPENAI_API_BASE}/chat/completions", headers=headers, json=payload)
            if resp.status_code >= 400:
                return {"content": '{"error":"llm_error"}'}
            data = resp.json()
    except Exception:
        return {"content": '{"error":"llm_request_failed"}'}

    try:
        return data["choices"][0]["message"]
    except Exception:
        return {"content": '{"error":"llm_bad_shape"}'}


async def _summarize_title(messages: List[Dict[str, str]]) -> Optional[str]:
    if not OPENAI_API_KEY:
        return None
    prompt = [
        {
            "role": "system",
            "content": "Summarize this conversation in 3-6 words. Return only the title.",
        },
        {"role": "user", "content": json.dumps(messages, ensure_ascii=False)},
    ]
    result = await _call_openai(prompt)
    title = (result.get("content") or "").strip().strip('"')
    if not title:
        return None
    return title[:80]


def _get_conversation_messages(
    db: Session,
    conversation_id: str,
    limit: Optional[int] = None,
) -> List[Dict[str, str]]:
    if limit:
        rows = (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .all()
        )
        rows.reverse()
    else:
        rows = (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .all()
        )
    return [{"role": r.role, "content": r.content} for r in rows]


async def _update_conversation_title(db: Session, conversation_id: str) -> None:
    messages = _get_conversation_messages(db, conversation_id, limit=10)
    title = await _summarize_title(messages)
    if not title:
        return
    convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not convo:
        return
    convo.title = title
    convo.updated_at = datetime.now(timezone.utc)
    db.commit()


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "mcp_schema",
            "description": "Get the role- and permission-scoped database schema from MCP.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mcp_query",
            "description": "Run a capability-scoped query via MCP. Prefer structured reads with table, columns, filters, limit, and count_only. Use raw sql only when structured reads are not enough. DELETE is not allowed; INSERT/UPDATE include undo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {"type": ["string", "null"]},
                    "params": {"type": ["object", "null"]},
                    "table": {"type": ["string", "null"]},
                    "columns": {
                        "type": ["array", "null"],
                        "items": {"type": "string"},
                    },
                    "filters": {"type": ["object", "null"]},
                    "limit": {"type": ["integer", "null"]},
                    "count_only": {"type": ["boolean", "null"]},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mcp_undo",
            "description": "Apply undo steps returned by MCP write queries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "steps": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "sql": {"type": "string"},
                                "params": {"type": "object"},
                            },
                            "required": ["sql"],
                        },
                    }
                },
                "required": ["steps"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "school_admin_action",
            "description": "Manage schools, departments, and programs through dedicated role-aware actions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "list_schools",
                            "get_school",
                            "create_school",
                            "update_school",
                            "update_school_status",
                            "list_events",
                            "list_departments",
                            "create_department",
                            "update_department",
                            "list_programs",
                            "create_program",
                            "update_program",
                        ],
                    },
                    "payload": {"type": ["object", "null"]},
                },
                "required": ["action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "student_import_action",
            "description": "Preview, clean, commit, and track bulk student imports using the dedicated import workflow.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "expected_headers",
                            "preview_import",
                            "clean_preview",
                            "commit_import",
                            "import_status",
                        ],
                    },
                    "dataset_text": {"type": ["string", "null"]},
                    "dataset_format": {
                        "type": ["string", "null"],
                        "enum": ["auto", "csv", "tsv", "json", "markdown"],
                    },
                    "preview_token": {"type": ["string", "null"]},
                    "job_id": {"type": ["string", "null"]},
                },
                "required": ["action"],
            },
        },
    },
]


TOOL_BY_NAME = {tool["function"]["name"]: tool for tool in TOOLS}


async def execute_tool(
    name: str,
    args: Dict[str, Any],
    *,
    roles: List[str],
    permissions: List[str],
    user_id: str,
    school_id: Optional[int],
    authorization: Optional[str],
) -> str:
    if name == "mcp_schema":
        result = await _fetch_schema(roles=roles, permissions=permissions, db_schema="public")
        return json.dumps(result, default=str)

    if name == "mcp_query":
        sql = args.get("sql")
        params = args.get("params") or {}
        table = args.get("table")
        columns = args.get("columns")
        filters = args.get("filters") or {}
        limit = args.get("limit")
        count_only = bool(args.get("count_only", False))
        if not sql and not table:
            return json.dumps({"error": "sql or table is required"})
        result = await _run_query(
            roles=roles,
            permissions=permissions,
            user_id=user_id,
            school_id=school_id,
            sql=sql,
            params=params,
            table=table,
            columns=columns,
            filters=filters,
            limit=limit,
            count_only=count_only,
        )
        return json.dumps(result, default=str)

    if name == "mcp_undo":
        if not MCP_QUERY_URL:
            return json.dumps({"error": "query service not configured"})
        steps = args.get("steps") or []
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(MCP_QUERY_URL.replace("/query", "/undo"), json={"steps": steps})
                if resp.status_code >= 400:
                    return json.dumps({"error": f"undo error {resp.status_code}", "detail": resp.text})
                return json.dumps(resp.json(), default=str)
        except httpx.HTTPError as exc:
            return json.dumps({"error": "undo service unreachable", "detail": str(exc)})

    if name == "school_admin_action":
        action = args.get("action")
        if not action:
            return json.dumps({"error": "action is required"})
        payload = args.get("payload") or {}
        result = await _run_school_admin_action(
            roles=roles,
            permissions=permissions,
            school_id=school_id,
            action=action,
            payload=payload,
        )
        return json.dumps(result, default=str)

    if name == "student_import_action":
        action = args.get("action")
        if not action:
            return json.dumps({"error": "action is required"})
        result = await _run_student_import_action(
            roles=roles,
            action=action,
            dataset_text=args.get("dataset_text"),
            dataset_format=args.get("dataset_format") or "auto",
            preview_token=args.get("preview_token"),
            job_id=args.get("job_id"),
            authorization=authorization,
        )
        return json.dumps(result, default=str)

    return json.dumps({"error": "Tool not found"})


def _parse_tool_arguments(arguments: str) -> Dict[str, Any]:
    try:
        parsed = json.loads(arguments or "{}")
    except json.JSONDecodeError as exc:
        return {"__parse_error__": f"Invalid tool arguments JSON: {exc}"}
    if not isinstance(parsed, dict):
        return {"__parse_error__": "Tool arguments must be a JSON object"}
    return parsed


def _tool_call_message(name: str, arguments: str) -> Dict[str, Any]:
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


def _extract_function_markup(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    match = re.search(
        r"<function=([a-zA-Z0-9_]+)\s*>?\s*(\{.*?\})\s*</function>",
        text,
        re.DOTALL,
    )
    if not match:
        return None
    function_name = match.group(1).strip()
    arguments = match.group(2).strip()
    return _tool_call_message(function_name, arguments)


def _recover_tool_call_from_error(error_text: str) -> Optional[Dict[str, Any]]:
    markup = _extract_function_markup(error_text)
    if markup is not None:
        return markup
    try:
        payload = json.loads(error_text)
    except json.JSONDecodeError:
        return None
    # Groq sometimes returns tool_use_failed with failed_generation as a JSON string
    # representing a list of {"name": ..., "parameters": {...}} objects.
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
    return _extract_function_markup(failed_generation)


def _recover_tool_call_from_message(message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if message.get("tool_calls"):
        return None
    content = message.get("content")
    if not isinstance(content, str):
        return None
    return _extract_function_markup(content)


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
    sanitized = _sanitize_tool_args(name, params)
    return _tool_call_message(name, json.dumps(sanitized, ensure_ascii=False))


def _sanitize_tool_args(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    # Providers sometimes emit explicit nulls for optional fields; remove them.
    cleaned: Dict[str, Any] = {}
    for k, v in (args or {}).items():
        if v is None:
            continue
        cleaned[k] = v
    # Tool-specific defaults for common cases.
    if tool_name == "mcp_query":
        # Accept either structured or raw; if both missing, let execute_tool reject.
        if "count_only" not in cleaned:
            # Avoid provider-side nulls turning into false positives.
            cleaned["count_only"] = False
        # Default limit only matters for structured reads.
        if "limit" not in cleaned:
            cleaned["limit"] = 100
        # Ensure params/filters are objects when present.
        if "params" in cleaned and not isinstance(cleaned["params"], dict):
            cleaned["params"] = {}
        if "filters" in cleaned and not isinstance(cleaned["filters"], dict):
            cleaned["filters"] = {}
    if tool_name in {"school_admin_action", "student_import_action"}:
        # Normalize absent payloads to {} instead of null.
        if "payload" in cleaned and cleaned["payload"] is None:
            cleaned["payload"] = {}
    return cleaned


async def _fetch_schema(roles: List[str], permissions: List[str], db_schema: str = "public") -> Optional[Dict[str, Any]]:
    def _fallback() -> Dict[str, Any]:
        import schema_server

        return schema_server.get_schema(
            schema_server.SchemaRequest(
                roles=roles,
                permissions=permissions,
                db_schema=db_schema,
            )
        )

    if not MCP_SCHEMA_URL:
        try:
            return _fallback()
        except Exception as exc:
            return {"error": "schema service unavailable", "detail": str(exc)}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                MCP_SCHEMA_URL,
                json={"roles": roles, "permissions": permissions, "db_schema": db_schema},
            )
            if resp.status_code >= 400:
                return {"error": f"schema service error {resp.status_code}", "detail": resp.text}
            return resp.json()
    except httpx.HTTPError as exc:
        try:
            return _fallback()
        except Exception as fallback_exc:
            return {
                "error": "schema service unreachable",
                "detail": f"{exc}; fallback failed: {fallback_exc}",
            }


async def _run_query(
    roles: List[str],
    permissions: List[str],
    user_id: str,
    school_id: Optional[int],
    sql: Optional[str],
    params: Optional[Dict[str, Any]] = None,
    table: Optional[str] = None,
    columns: Optional[List[str]] = None,
    filters: Optional[Dict[str, Any]] = None,
    limit: Optional[int] = None,
    count_only: bool = False,
) -> Dict[str, Any]:
    trusted_params = dict(params or {})
    if school_id is not None:
        trusted_params["school_id"] = school_id
    if user_id:
        trusted_params["user_id"] = user_id

    def _fallback() -> Dict[str, Any]:
        import query_server

        return query_server.run_query(
            query_server.QueryRequest(
                roles=roles,
                permissions=permissions,
                user_id=user_id,
                school_id=school_id,
                sql=sql,
                params=trusted_params,
                table=table,
                columns=columns,
                filters=filters or {},
                limit=limit or 100,
                count_only=count_only,
            )
        )

    if not MCP_QUERY_URL:
        try:
            return _fallback()
        except Exception as exc:
            return {"error": "query service unavailable", "detail": str(exc)}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                MCP_QUERY_URL,
                json={
                    "roles": roles,
                    "permissions": permissions,
                    "user_id": user_id,
                    "school_id": school_id,
                    "sql": sql,
                    "params": trusted_params,
                    "table": table,
                    "columns": columns,
                    "filters": filters or {},
                    "limit": limit or 100,
                    "count_only": count_only,
                },
            )
            if resp.status_code >= 400:
                return {"error": f"query service error {resp.status_code}", "detail": resp.text}
            return resp.json()
    except httpx.HTTPError as exc:
        try:
            return _fallback()
        except Exception as fallback_exc:
            return {
                "error": "query service unreachable",
                "detail": f"{exc}; fallback failed: {fallback_exc}",
            }


async def _run_school_admin_action(
    *,
    roles: List[str],
    permissions: List[str],
    school_id: Optional[int],
    action: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    request_body = {
        "roles": roles,
        "permissions": permissions,
        "school_id": school_id,
        "action": action,
        "payload": payload,
    }

    def _fallback() -> Dict[str, Any]:
        import school_admin_server

        return school_admin_server.run_action(
            school_admin_server.ActionRequest(**request_body)
        )

    if not MCP_SCHOOL_ADMIN_URL:
        try:
            return _fallback()
        except Exception as exc:
            return {"error": "school admin service unavailable", "detail": str(exc)}

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(MCP_SCHOOL_ADMIN_URL, json=request_body)
            if resp.status_code >= 400:
                return {"error": f"school admin service error {resp.status_code}", "detail": resp.text}
            return resp.json()
    except httpx.HTTPError as exc:
        try:
            return _fallback()
        except Exception as fallback_exc:
            return {
                "error": "school admin service unreachable",
                "detail": f"{exc}; fallback failed: {fallback_exc}",
            }


async def _run_student_import_action(
    *,
    roles: List[str],
    action: str,
    dataset_text: Optional[str],
    dataset_format: str,
    preview_token: Optional[str],
    job_id: Optional[str],
    authorization: Optional[str],
) -> Dict[str, Any]:
    request_body = {
        "roles": roles,
        "action": action,
        "dataset_text": dataset_text,
        "dataset_format": dataset_format,
        "preview_token": preview_token,
        "job_id": job_id,
    }
    headers = {}
    if authorization:
        headers["Authorization"] = authorization

    def _fallback() -> Dict[str, Any]:
        import student_import_server

        return student_import_server

    if not MCP_STUDENT_IMPORT_URL:
        try:
            module = _fallback()
            return await module._run_action_internal(
                module.ActionRequest(**request_body),
                authorization,
            )
        except Exception as exc:
            return {"error": "student import service unavailable", "detail": str(exc)}

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(MCP_STUDENT_IMPORT_URL, json=request_body, headers=headers)
            if resp.status_code >= 400:
                return {"error": f"student import service error {resp.status_code}", "detail": resp.text}
            return resp.json()
    except httpx.HTTPError as exc:
        try:
            module = _fallback()
            return await module._run_action_internal(
                module.ActionRequest(**request_body),
                authorization,
            )
        except Exception as fallback_exc:
            return {
                "error": "student import service unreachable",
                "detail": f"{exc}; fallback failed: {fallback_exc}",
            }


def _sse_event(event: str, data: Dict[str, Any]) -> str:
    payload = json.dumps(data, default=str)
    return f"event: {event}\ndata: {payload}\n\n"


def _stream_text_as_sse(conversation_id: str, text: str) -> StreamingResponse:
    """Stream plain assistant text as SSE `message` events, ending with a `done` event."""

    def _gen() -> Generator[str, None, None]:
        chunk_size = 180
        for i in range(0, len(text), chunk_size):
            yield _sse_event("message", {"conversation_id": conversation_id, "content": text[i : i + chunk_size]})
        yield _sse_event(
            "done",
            {"conversation_id": conversation_id, "message_id": str(uuid.uuid4()), "finish_reason": "stop"},
        )

    return StreamingResponse(_gen(), media_type="text/event-stream")


def _truncate_list(values: List[str], *, limit: int = 60) -> tuple[List[str], int]:
    items = [v for v in values if isinstance(v, str) and v.strip()]
    total = len(items)
    if total <= limit:
        return items, total
    return items[:limit], total



@app.post("/assistant/stream")
async def assistant_stream(
    request: Request,
    body: AssistantRequest,
    identity: Dict[str, Any] = Depends(get_current_identity),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    request_user_id = _ensure_user_match(identity, body)
    primary_role, effective_roles = _get_roles_from_identity(identity, body.user_role)
    effective_permissions = _get_permissions_from_identity(identity)
    authorization = request.headers.get("authorization")
    _enforce_daily_limit(db, user_id=request_user_id, user_role=primary_role, effective_roles=effective_roles)

    conversation_id = body.conversation_id
    if not conversation_id:
        convo = _create_conversation(db, user_id=request_user_id, user_role=primary_role, title=None)
        conversation_id = convo.id
    else:
        _get_owned_conversation(db, conversation_id, request_user_id)

    # Load the conversation before appending the new user message.
    max_messages = None
    if ASSISTANT_CONTEXT_MAX_MESSAGES:
        try:
            max_messages = int(ASSISTANT_CONTEXT_MAX_MESSAGES)
        except ValueError:
            max_messages = None

    history = _get_conversation_messages(db, conversation_id, limit=max_messages)
    _append_message(db, conversation_id, "user", body.message)

    system_prompt = _load_system_prompt()
    identity_name = identity.get("name") or identity.get("user_name")
    effective_name = body.user_name or identity_name
    identity_school = identity.get("school_name") or identity.get("school")
    effective_school = body.user_school or identity_school
    identity_school_id = identity.get("school_id")
    effective_school_id = body.user_school_id or identity_school_id
    effective_timezone = _get_effective_timezone(identity, body)
    readable_tables, writable_tables, scope_rules, capability_notes, non_capability_notes = _render_role_capabilities(
        effective_roles,
        effective_permissions,
    )
    system_prompt = _render_system_prompt(
        system_prompt,
        user_id=request_user_id,
        user_role=primary_role,
        effective_roles=", ".join(effective_roles) or "none",
        effective_permissions=", ".join(effective_permissions) or "none",
        user_name=effective_name,
        user_school=effective_school,
        user_school_id=effective_school_id,
        user_timezone=effective_timezone,
        readable_tables=readable_tables,
        writable_tables=writable_tables,
        scope_rules=scope_rules,
        capability_notes=capability_notes,
        non_capability_notes=non_capability_notes,
    )
    messages = [
        {"role": "system", "content": system_prompt},
        *history,
        {"role": "user", "content": body.message},
    ]

    # Handle multiple rounds of tool calls if necessary
    final_assistant_text: Optional[str] = None
    tools_used = False
    for _ in range(3):
        response_msg = await _call_openai(messages, tools=TOOLS)
        messages.append(response_msg)
        
        if not response_msg.get("tool_calls"):
            content = response_msg.get("content")
            if isinstance(content, str) and content.strip():
                final_assistant_text = content
            break

        for tool_call in response_msg["tool_calls"]:
            tools_used = True
            fname = tool_call["function"]["name"]
            fargs = _parse_tool_arguments(tool_call["function"].get("arguments", "{}"))
            if "__parse_error__" in fargs:
                result = json.dumps({"error": fargs["__parse_error__"]})
            else:
                fargs = _sanitize_tool_args(fname, fargs)
                result = await execute_tool(
                    fname,
                    fargs,
                    roles=effective_roles,
                    permissions=effective_permissions,
                    user_id=request_user_id,
                    school_id=effective_school_id,
                    authorization=authorization,
                )
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "name": fname,
                "content": result,
            })



    # If we ended on a tool message (provider oddities / max tool rounds), force one final
    # non-tool completion so users don't see "I couldn't finish the reply cleanly."
    if final_assistant_text is None and messages and messages[-1].get("role") == "tool":
        response_msg = await _call_openai(messages, tools=None)
        messages.append(response_msg)
        content = response_msg.get("content")
        if isinstance(content, str) and content.strip():
            final_assistant_text = content

    if final_assistant_text:
        assistant_text = final_assistant_text
    elif messages and messages[-1].get("role") == "tool":
        assistant_text = "I completed a data step but couldn't finish the reply cleanly. Ask again and I'll continue from there."
    else:
        last_content = messages[-1].get("content") if messages else None
        assistant_text = last_content if isinstance(last_content, str) and last_content.strip() else "No response generated."

    _append_message(db, conversation_id, "assistant", assistant_text)
    await _update_conversation_title(db, conversation_id)

    def stream() -> Generator[str, None, None]:
        chunk_size = 160
        for i in range(0, len(assistant_text), chunk_size):
            chunk = assistant_text[i : i + chunk_size]
            yield _sse_event(
                "message",
                {
                    "conversation_id": conversation_id,
                    "content": chunk,
                },
            )
        yield _sse_event(
            "done",
            {
                "conversation_id": conversation_id,
                "message_id": str(uuid.uuid4()),
                "finish_reason": "stop",
            },
        )

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/conversations", response_model=List[ConversationSummary])
def list_conversations(
    identity: Dict[str, Any] = Depends(get_current_identity),
    db: Session = Depends(get_db),
) -> List[ConversationSummary]:
    user_id = _get_token_user_id(identity)

    rows = (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )

    results: List[ConversationSummary] = []
    for convo in rows:
        last_msg = (
            db.query(Message)
            .filter(Message.conversation_id == convo.id)
            .order_by(Message.created_at.desc())
            .first()
        )
        results.append(
            ConversationSummary(
                conversation_id=convo.id,
                title=convo.title,
                last_message=last_msg.content if last_msg else None,
                updated_at=convo.updated_at.replace(tzinfo=timezone.utc)
                if convo.updated_at
                else datetime.now(tz=timezone.utc),
            )
        )
    return results


@app.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: str,
    identity: Dict[str, Any] = Depends(get_current_identity),
    db: Session = Depends(get_db),
) -> ConversationDetail:
    user_id = _get_token_user_id(identity)
    convo = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .first()
    )
    if not convo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    return ConversationDetail(
        conversation_id=convo.id,
        title=convo.title,
        messages=[
            {"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at}
            for m in messages
        ],
    )


@app.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    identity: Dict[str, Any] = Depends(get_current_identity),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    user_id = _get_token_user_id(identity)
    convo = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .first()
    )
    if not convo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    db.query(Message).filter(Message.conversation_id == conversation_id).delete()
    db.delete(convo)
    db.commit()
    return {"status": "deleted"}


@app.patch("/conversations/{conversation_id}")
def update_conversation_title(
    conversation_id: str,
    body: ConversationUpdate,
    identity: Dict[str, Any] = Depends(get_current_identity),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    user_id = _get_token_user_id(identity)
    convo = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .first()
    )
    if not convo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    convo.title = body.title.strip()
    convo.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "updated", "conversation_id": conversation_id, "title": convo.title}
