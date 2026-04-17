"""Agentic assistant API (role-aware, streaming, conversation history).

Run:
  uvicorn assistant:app --reload

Environment variables:
  DATABASE_URL           PostgreSQL connection string
  JWT_SECRET             JWT HMAC secret (or set JWT_PUBLIC_KEY for RS256)
  JWT_ALGORITHM          Default: HS256
  JWT_PUBLIC_KEY         Optional PEM for RS256 verification
  AI_PROVIDER            Optional: openai, anthropic, gemini
  AI_API_KEY             Optional, used for LLM calls
  AI_API_BASE            Optional provider base URL
  AI_MODEL               Optional model name
  OPENAI_*               Backward-compatible aliases for OpenAI-compatible APIs
  ASSISTANT_AUTO_MIGRATE Optional, default: true
  MCP_SCHEMA_URL         Optional, role-scoped schema service endpoint
  MCP_QUERY_URL          Optional, role-scoped query service endpoint
  BACKEND_API_BASE_URL   Optional backend API origin for guarded backend actions/reports
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional
from urllib.parse import urlencode
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text, create_engine, func, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

ASSISTANT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ASSISTANT_DIR.parent
load_dotenv(ASSISTANT_DIR / ".env", override=False)
load_dotenv(PROJECT_ROOT / ".env", override=False)

MCP_DIR = os.path.join(os.path.dirname(__file__), "mcp")
if MCP_DIR not in sys.path:
    sys.path.insert(0, MCP_DIR)

ASSISTANT_DIR = os.path.dirname(__file__)
if ASSISTANT_DIR not in sys.path:
    # Ensure `import mcp.*` works when running via uvicorn from other working dirs.
    sys.path.insert(0, ASSISTANT_DIR)

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


logger = logging.getLogger("uvicorn.error")

LOADED_ENV_PATHS: list[str] = []


def _parse_env_file(path: Path) -> Dict[str, str]:
    """Minimal .env parser so local runs work even without python-dotenv.

    Supports:
      - blank lines / comments
      - KEY=VALUE
      - optional leading "export "
      - single/double-quoted values (no variable expansion)
    """
    values: Dict[str, str] = {}
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return values

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def _load_env_files() -> None:
    """Load .env files for local runs (uvicorn won't do this automatically)."""
    assistant_root = Path(__file__).resolve().parent
    repo_root = assistant_root.parent
    for env_path in (assistant_root / ".env", repo_root / ".env"):
        if env_path.exists():
            LOADED_ENV_PATHS.append(str(env_path))
            if load_dotenv is not None:
                load_dotenv(env_path, override=False)
            # If the shell has vars set but empty, python-dotenv won't override them by default.
            # Treat empty as "unset" for local developer ergonomics.
            for key, value in _parse_env_file(env_path).items():
                if os.environ.get(key, "") == "":
                    os.environ[key] = value


_load_env_files()

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
except ValueError:
    AI_MAX_TOKENS = 1024
AI_API_VERSION = (
    os.getenv("AI_API_VERSION")
    or os.getenv("ANTHROPIC_VERSION")
    or os.getenv("ANTHROPIC_API_VERSION")
    or "2023-06-01"
).strip()
ASSISTANT_AUTO_MIGRATE = os.getenv("ASSISTANT_AUTO_MIGRATE", "true").lower() == "true"
MCP_SCHEMA_URL = os.getenv("MCP_SCHEMA_URL") or "http://127.0.0.1:8500/mcp/schema/schema"
MCP_QUERY_URL = os.getenv("MCP_QUERY_URL") or "http://127.0.0.1:8500/mcp/query/query"
MCP_SCHOOL_ADMIN_URL = os.getenv("MCP_SCHOOL_ADMIN_URL") or "http://127.0.0.1:8500/mcp/school-admin/action"
MCP_STUDENT_IMPORT_URL = os.getenv("MCP_STUDENT_IMPORT_URL") or "http://127.0.0.1:8500/mcp/student-import/action"
ASSISTANT_CONTEXT_MAX_MESSAGES = os.getenv("ASSISTANT_CONTEXT_MAX_MESSAGES")
BACKEND_API_BASE_URL = (os.getenv("BACKEND_API_BASE_URL") or "").strip()
try:
    BACKEND_API_TIMEOUT_SECONDS = max(5, int(os.getenv("BACKEND_API_TIMEOUT_SECONDS", "30")))
except ValueError:
    BACKEND_API_TIMEOUT_SECONDS = 30
ASSISTANT_ALLOW_DELETE = os.getenv("ASSISTANT_ALLOW_DELETE", "false").strip().lower() == "true"

if not JWT_PUBLIC_KEY and not JWT_SECRETS:
    logger.warning(
        "Assistant JWT verification is not configured yet: set SECRET_KEY/JWT_SECRET or JWT_PUBLIC_KEY "
        "(check that your repo-root .env is being loaded for this process)."
    )
else:
    logger.info(
        "Assistant auth config loaded (algorithm=%s, hmac_secrets=%s, public_key=%s, env_files=%s).",
        JWT_ALGORITHM,
        len(JWT_SECRETS),
        bool(JWT_PUBLIC_KEY),
        LOADED_ENV_PATHS or [],
    )

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

# Integrated MCP sub-apps (Role-scoped tools).
#
# Note: There is a third-party PyPI package named `mcp`; importing `mcp.*` would
# resolve to that package instead of our local `Assistant/mcp/*.py`. We add
# `MCP_DIR` to `sys.path` above so we can import these modules directly.
from schema_server import app as schema_app
from query_server import app as query_app
from school_admin_server import app as school_admin_app
from student_import_server import app as student_import_app

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


@app.get("/debug/auth-config")
def debug_auth_config() -> Dict[str, Any]:
    """Dev-only helper: confirms what the running assistant process sees.

    Does not return secret values.
    """
    return {
        "jwt_algorithm": JWT_ALGORITHM,
        "has_jwt_public_key": bool(JWT_PUBLIC_KEY),
        "jwt_hmac_secrets_configured": len(JWT_SECRETS),
        "env_files_loaded": LOADED_ENV_PATHS,
        "env_present": {
            "SECRET_KEY": bool(os.getenv("SECRET_KEY")),
            "JWT_SECRET": bool(os.getenv("JWT_SECRET")),
            "JWT_PUBLIC_KEY": bool(os.getenv("JWT_PUBLIC_KEY")),
        },
    }


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


ROLE_FROM_UNIT_TYPE = {
    "ssg": "ssg",
    "sg": "sg",
    "org": "org",
}

BACKEND_SAFE_METHODS = {"GET", "POST", "PUT", "PATCH"}
BACKEND_ALLOWED_PREFIXES = (
    "/api/attendance",
    "/api/events",
    "/api/governance",
    "/api/sanctions",
    "/api/users",
    "/api/programs",
    "/api/departments",
    "/api/notifications",
    "/api/audit-logs",
    "/api/subscription",
    "/api/school",
    "/school-settings",
)
BACKEND_BLOCKED_PREFIXES = (
    "/token",
    "/login",
    "/auth",
    "/api/auth",
    "/api/security",
    "/api/face",
    "/public-attendance",
)
BACKEND_BLOCKED_PATTERNS = (
    re.compile(r"/password", re.IGNORECASE),
    re.compile(r"/face", re.IGNORECASE),
    re.compile(r"/security", re.IGNORECASE),
    re.compile(r"/token", re.IGNORECASE),
)


def _normalize_base_url(value: str) -> str:
    return str(value or "").strip().rstrip("/")


def _join_base_url(base_url: str, path: str) -> str:
    normalized_base = _normalize_base_url(base_url)
    normalized_path = "/" + str(path or "").strip().lstrip("/")
    return f"{normalized_base}{normalized_path}"


def _dedupe_strings(values: List[str]) -> List[str]:
    items: List[str] = []
    seen = set()
    for value in values:
        normalized = str(value or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        items.append(normalized)
    return items


def _candidate_backend_base_urls() -> List[str]:
    return _dedupe_strings(
        [
            BACKEND_API_BASE_URL,
            "http://127.0.0.1:8000",
            "http://localhost:8000",
            os.getenv("BACKEND_ORIGIN"),
            os.getenv("APP_BACKEND_URL"),
            "http://backend:8000",
        ]
    )


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


def _effective_ai_base_url(provider: Optional[str] = None) -> str:
    resolved_provider = provider or _infer_ai_provider()
    configured_base = _normalize_base_url(AI_API_BASE)
    if configured_base:
        return configured_base
    return _default_ai_base_url(resolved_provider)


def _configured_provider_name() -> str:
    provider = _infer_ai_provider()
    if provider == "anthropic":
        return "Anthropic"
    if provider == "gemini":
        return "Gemini"
    return "OpenAI-compatible"


def _provider_requires_api_key(provider: Optional[str] = None) -> bool:
    resolved_provider = provider or _infer_ai_provider()
    if resolved_provider != "openai":
        return True
    base_url = _effective_ai_base_url(resolved_provider).lower()
    return not any(host in base_url for host in ("localhost", "127.0.0.1", "host.docker.internal"))


def _sanitize_backend_path(path: str) -> str:
    normalized_path = "/" + str(path or "").strip().lstrip("/")
    if not normalized_path.startswith("/"):
        raise HTTPException(status_code=400, detail="backend path must start with '/'")
    if ".." in normalized_path:
        raise HTTPException(status_code=400, detail="backend path must not contain path traversal")
    return normalized_path


def _assert_backend_route_allowed(method: str, path: str) -> None:
    normalized_method = str(method or "").strip().upper()
    normalized_path = _sanitize_backend_path(path)
    if normalized_method == "DELETE" and not ASSISTANT_ALLOW_DELETE:
        raise HTTPException(
            status_code=403,
            detail="DELETE requests are blocked for assistant backend actions",
        )
    if normalized_method not in BACKEND_SAFE_METHODS and not (
        ASSISTANT_ALLOW_DELETE and normalized_method == "DELETE"
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported backend method: {normalized_method}",
        )
    if any(normalized_path.startswith(prefix) for prefix in BACKEND_BLOCKED_PREFIXES):
        raise HTTPException(
            status_code=403,
            detail="This backend route is blocked for assistant safety",
        )
    if any(pattern.search(normalized_path) for pattern in BACKEND_BLOCKED_PATTERNS):
        raise HTTPException(
            status_code=403,
            detail="This backend route is blocked for assistant safety",
        )
    if not any(normalized_path.startswith(prefix) for prefix in BACKEND_ALLOWED_PREFIXES):
        raise HTTPException(
            status_code=403,
            detail="This backend route is outside the assistant allowlist",
        )


def _serialize_backend_response(response: httpx.Response) -> Any:
    content_type = (response.headers.get("content-type") or "").lower()
    if "application/json" in content_type:
        try:
            return response.json()
        except ValueError:
            return {"raw": response.text}
    text_body = response.text
    if not text_body:
        return {"status_code": response.status_code}
    return {"text": text_body[:8000]}


def _normalize_governance_access(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return {"permission_codes": [], "roles": [], "units": [], "school_id": None}

    permission_codes = _dedupe_strings(
        [str(code).strip().lower() for code in (payload.get("permission_codes") or [])]
    )
    units: List[Dict[str, Any]] = []
    derived_roles: List[str] = []
    for unit in payload.get("units") or []:
        if not isinstance(unit, dict):
            continue
        unit_type = str(unit.get("unit_type") or "").strip().lower()
        role_name = ROLE_FROM_UNIT_TYPE.get(unit_type)
        if role_name:
            derived_roles.append(role_name)
        units.append(
            {
                "governance_unit_id": unit.get("governance_unit_id"),
                "unit_code": unit.get("unit_code"),
                "unit_name": unit.get("unit_name"),
                "unit_type": unit_type,
                "permission_codes": _dedupe_strings(
                    [str(code).strip().lower() for code in (unit.get("permission_codes") or [])]
                ),
            }
        )

    return {
        "permission_codes": permission_codes,
        "roles": _dedupe_strings(derived_roles),
        "units": units,
        "school_id": payload.get("school_id"),
    }


def _load_governance_access_from_db(user_id: str, school_id: Optional[int]) -> Dict[str, Any]:
    if AppSessionLocal is None:
        return {"permission_codes": [], "roles": [], "units": [], "school_id": school_id}

    try:
        normalized_user_id = int(str(user_id).strip())
    except (TypeError, ValueError):
        return {"permission_codes": [], "roles": [], "units": [], "school_id": school_id}

    query = """
        select
            gu.id as governance_unit_id,
            gu.unit_code,
            gu.unit_name,
            lower(cast(gu.unit_type as text)) as unit_type,
            gp.permission_code
        from governance_members gm
        join governance_units gu
          on gu.id = gm.governance_unit_id
        left join governance_member_permissions gmp
          on gmp.governance_member_id = gm.id
        left join governance_permissions gp
          on gp.id = gmp.permission_id
        where gm.user_id = :user_id
          and gm.is_active = true
          and gu.is_active = true
    """
    params: Dict[str, Any] = {"user_id": normalized_user_id}
    if school_id is not None:
        query += " and gu.school_id = :school_id"
        params["school_id"] = school_id
    query += " order by gu.id asc"

    try:
        with AppSessionLocal() as db_session:
            rows = db_session.execute(text(query), params).mappings().all()
    except Exception:
        return {"permission_codes": [], "roles": [], "units": [], "school_id": school_id}

    units_by_id: Dict[Any, Dict[str, Any]] = {}
    permission_codes: List[str] = []
    roles: List[str] = []

    for row in rows:
        unit_id = row.get("governance_unit_id")
        unit_type = str(row.get("unit_type") or "").strip().lower()
        if unit_id not in units_by_id:
            units_by_id[unit_id] = {
                "governance_unit_id": unit_id,
                "unit_code": row.get("unit_code"),
                "unit_name": row.get("unit_name"),
                "unit_type": unit_type,
                "permission_codes": [],
            }
        permission_code = str(row.get("permission_code") or "").strip().lower()
        if permission_code:
            units_by_id[unit_id]["permission_codes"].append(permission_code)
            permission_codes.append(permission_code)
        role_name = ROLE_FROM_UNIT_TYPE.get(unit_type)
        if role_name:
            roles.append(role_name)

    units = []
    for unit in units_by_id.values():
        unit["permission_codes"] = _dedupe_strings(unit.get("permission_codes") or [])
        units.append(unit)

    return {
        "permission_codes": _dedupe_strings(permission_codes),
        "roles": _dedupe_strings(roles),
        "units": units,
        "school_id": school_id,
    }


async def _request_backend(
    *,
    method: str,
    path: str,
    authorization: Optional[str],
    query: Optional[Dict[str, Any]] = None,
    body: Optional[Dict[str, Any]] = None,
    validate_path: bool = False,
) -> Dict[str, Any]:
    normalized_method = str(method or "").strip().upper()
    normalized_path = _sanitize_backend_path(path)
    if validate_path:
        _assert_backend_route_allowed(normalized_method, normalized_path)

    query_params = {k: v for k, v in (query or {}).items() if v is not None and v != ""}
    request_headers: Dict[str, str] = {}
    if authorization:
        request_headers["Authorization"] = authorization

    candidates = _candidate_backend_base_urls()
    if not candidates:
        return {"ok": False, "error": "backend origin is not configured"}

    last_error: Optional[str] = None
    last_failure: Optional[Dict[str, Any]] = None
    async with httpx.AsyncClient(timeout=BACKEND_API_TIMEOUT_SECONDS) as client:
        for base_url in candidates:
            url = _join_base_url(base_url, normalized_path)
            if query_params:
                url = f"{url}?{urlencode(query_params, doseq=True)}"
            try:
                response = await client.request(
                    normalized_method,
                    url,
                    headers=request_headers,
                    json=body if body is not None else None,
                )
            except httpx.HTTPError as exc:
                last_error = str(exc)
                continue

            data = _serialize_backend_response(response)
            result = {
                "ok": response.status_code < 400,
                "status_code": response.status_code,
                "data": data,
                "url": url,
            }
            if response.status_code < 400:
                return result

            last_failure = result
            if response.status_code in {401, 403, 405, 422}:
                return result
            if response.status_code != 404:
                return result

    if last_failure is not None:
        return last_failure
    return {
        "ok": False,
        "error": "backend unreachable",
        "detail": last_error or "No backend candidates responded",
    }


async def _resolve_runtime_governance_access(
    *,
    authorization: Optional[str],
    user_id: str,
    school_id: Optional[int],
) -> Dict[str, Any]:
    if authorization:
        backend_result = await _request_backend(
            method="GET",
            path="/api/governance/access/me",
            authorization=authorization,
            validate_path=False,
        )
        if backend_result.get("ok"):
            return _normalize_governance_access(backend_result.get("data"))
    return _load_governance_access_from_db(user_id=user_id, school_id=school_id)


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


def _get_roles_from_identity(
    identity: Dict[str, Any],
    body_role: Optional[str],
    extra_roles: Optional[List[str]] = None,
) -> tuple[str, list[str]]:
    raw_roles = identity.get("roles") or identity.get("role") or identity.get("user_role") or []
    if isinstance(raw_roles, str):
        raw_roles = [raw_roles]
    if extra_roles:
        raw_roles = [*raw_roles, *extra_roles]

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


def _get_permissions_from_identity(
    identity: Dict[str, Any],
    extra_permissions: Optional[List[str]] = None,
) -> list[str]:
    raw_permissions = (
        identity.get("permissions")
        or identity.get("permission_codes")
        or identity.get("governance_permissions")
        or []
    )
    if isinstance(raw_permissions, str):
        raw_permissions = [raw_permissions]
    if extra_permissions:
        raw_permissions = [*raw_permissions, *extra_permissions]

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
    def _summarize(values: List[str], *, limit: int, separator: str = ", ") -> str:
        items = [value for value in values if isinstance(value, str) and value.strip()]
        total = len(items)
        if not total:
            return "none"
        clipped = items[:limit]
        summary = separator.join(clipped)
        if total > len(clipped):
            summary += f"{separator}... (+{total - len(clipped)} more)"
        return summary

    policy = get_effective_policy(roles, permissions)
    readable_tables = _summarize(sorted(policy.allowed_tables), limit=18)
    writable_tables = _summarize(sorted(policy.allowed_write_tables), limit=14)
    scope_rules = _summarize(summarize_scope_rules(policy), limit=10, separator="; ")
    capability_notes = _summarize(list(policy.capability_notes), limit=6, separator="; ")
    non_capability_notes = _summarize(list(policy.non_capability_notes), limit=6, separator="; ")

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


def _ai_not_configured_message() -> str:
    return (
        "LLM is not configured. Set AI_PROVIDER/AI_API_KEY/AI_MODEL "
        "or the compatible OPENAI_* variables."
    )


def _extract_text_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
                continue
            if not isinstance(item, dict):
                continue
            text_value = item.get("text")
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


def _convert_tools_for_anthropic(tools: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    converted: List[Dict[str, Any]] = []
    for tool in tools or []:
        function_def = tool.get("function") or {}
        converted.append(
            {
                "name": function_def.get("name"),
                "description": function_def.get("description") or "",
                "input_schema": function_def.get("parameters") or {"type": "object", "properties": {}},
            }
        )
    return converted


def _convert_tools_for_gemini(tools: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    declarations: List[Dict[str, Any]] = []
    for tool in tools or []:
        function_def = tool.get("function") or {}
        declarations.append(
            {
                "name": function_def.get("name"),
                "description": function_def.get("description") or "",
                "parameters": function_def.get("parameters") or {"type": "object", "properties": {}},
            }
        )
    return [{"functionDeclarations": declarations}] if declarations else []


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


async def _call_openai(messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    provider = _infer_ai_provider()
    if _provider_requires_api_key(provider) and not AI_API_KEY:
        return {"content": _ai_not_configured_message()}
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            if provider == "anthropic":
                system_text, anthropic_messages = _convert_messages_for_anthropic(messages)
                payload: Dict[str, Any] = {
                    "model": AI_MODEL,
                    "messages": anthropic_messages,
                    "max_tokens": AI_MAX_TOKENS,
                }
                if system_text:
                    payload["system"] = system_text
                converted_tools = _convert_tools_for_anthropic(tools)
                if converted_tools:
                    payload["tools"] = converted_tools
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
                converted_tools = _convert_tools_for_gemini(tools)
                if converted_tools:
                    payload["tools"] = converted_tools
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

            headers = {"Content-Type": "application/json"}
            if AI_API_KEY:
                headers["Authorization"] = f"Bearer {AI_API_KEY}"
            payload = {"model": AI_MODEL, "messages": messages, "max_tokens": AI_MAX_TOKENS}
            if tools:
                payload["tools"] = tools
            endpoint = _resolve_ai_endpoint("chat/completions")
            resp = await client.post(endpoint, headers=headers, json=payload)
            if resp.status_code >= 400:
                retry_max_tokens = _suggest_retry_max_tokens(resp.text, AI_MAX_TOKENS)
                if retry_max_tokens and retry_max_tokens != AI_MAX_TOKENS:
                    retry_payload = dict(payload)
                    retry_payload["max_tokens"] = retry_max_tokens
                    resp = await client.post(endpoint, headers=headers, json=retry_payload)
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


async def _call_openai_json(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Best-effort JSON-mode call for validators (temperature=0, JSON object output)."""
    provider = _infer_ai_provider()
    if _provider_requires_api_key(provider) and not AI_API_KEY:
        return {"content": '{"error":"llm_not_configured"}'}
        return {"content": '{"error":"llm_not_configured"}'}
    if provider != "openai":
        result = await _call_openai(messages)
        content = _extract_text_content(result.get("content"))
        return {"content": content or '{"error":"llm_bad_shape"}'}

    headers = {"Content-Type": "application/json"}
    if AI_API_KEY:
        headers["Authorization"] = f"Bearer {AI_API_KEY}"
    base_payload: Dict[str, Any] = {
        "model": AI_MODEL,
        "messages": messages,
        "temperature": 0,
        "max_tokens": 200,
    }

    payload = dict(base_payload)
    payload["response_format"] = {"type": "json_object"}

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            endpoint = _resolve_ai_endpoint("chat/completions")
            resp = await client.post(endpoint, headers=headers, json=payload)
            if resp.status_code >= 400:
                payload = dict(base_payload)
                retry_max_tokens = _suggest_retry_max_tokens(resp.text, int(base_payload["max_tokens"]))
                if retry_max_tokens:
                    payload["max_tokens"] = retry_max_tokens
                resp = await client.post(endpoint, headers=headers, json=payload)
            if resp.status_code >= 400:
                body_preview = (resp.text or "").strip()
                if len(body_preview) > 600:
                    body_preview = body_preview[:600] + "…"
                logger.warning("LLM JSON-mode HTTP error (status=%s): %s", resp.status_code, body_preview)
                return {"content": '{"error":"llm_error"}'}
            data = resp.json()
    except httpx.HTTPError as exc:
        logger.warning("LLM JSON-mode transport error: %s", str(exc).strip() or repr(exc))
        return {"content": '{"error":"llm_request_failed"}'}
    except Exception as exc:
        logger.warning("LLM JSON-mode unexpected error: %s", str(exc).strip() or repr(exc))
        return {"content": '{"error":"llm_request_failed"}'}

    try:
        return data["choices"][0]["message"]
    except Exception:
        return {"content": '{"error":"llm_bad_shape"}'}


async def _summarize_title(messages: List[Dict[str, Any]]) -> Optional[str]:
    provider = _infer_ai_provider()
    if _provider_requires_api_key(provider) and not AI_API_KEY:
        return None
    prompt = [
        {
            "role": "system",
            "content": "Summarize this conversation in 3-6 words. Return only the title.",
        },
        {"role": "user", "content": json.dumps(messages, ensure_ascii=False)},
    ]
    result = await _call_openai(prompt)
    title = _extract_text_content(result.get("content")).strip().strip('"')
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
    {
        "type": "function",
        "function": {
            "name": "backend_action",
            "description": "Call an allowlisted backend API route with the current user's token for role-validated business actions. Guardrails block auth, password, security, face, public-attendance, and DELETE routes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "method": {
                        "type": "string",
                        "enum": ["GET", "POST", "PUT", "PATCH"],
                    },
                    "path": {"type": "string"},
                    "query": {"type": ["object", "null"]},
                    "body": {"type": ["object", "null"]},
                },
                "required": ["method", "path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "backend_report",
            "description": "Fetch existing backend report endpoints for attendance and governance analytics using the current user's role and scope.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "school_attendance_summary",
                            "student_overview",
                            "student_attendance_report",
                            "student_attendance_stats",
                            "student_attendance_records",
                            "my_attendance_records",
                            "event_attendance_report",
                            "event_attendees",
                            "event_attendances",
                            "governance_dashboard_overview",
                        ],
                    },
                    "event_id": {"type": ["integer", "null"]},
                    "student_id": {"type": ["integer", "string", "null"]},
                    "governance_unit_id": {"type": ["integer", "null"]},
                    "query": {"type": ["object", "null"]},
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

    if name == "backend_action":
        method = str(args.get("method") or "").strip().upper()
        path = str(args.get("path") or "").strip()
        if not method or not path:
            return json.dumps({"error": "method and path are required"})
        result = await _run_backend_action(
            method=method,
            path=path,
            query=args.get("query") if isinstance(args.get("query"), dict) else None,
            body=args.get("body") if isinstance(args.get("body"), dict) else None,
            authorization=authorization,
        )
        return json.dumps(result, default=str)

    if name == "backend_report":
        action = args.get("action")
        if not action:
            return json.dumps({"error": "action is required"})
        result = await _run_backend_report(
            action=str(action),
            event_id=args.get("event_id"),
            student_id=args.get("student_id"),
            governance_unit_id=args.get("governance_unit_id"),
            query=args.get("query") if isinstance(args.get("query"), dict) else None,
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


def _normalize_function_markup(text: str) -> str:
    # Some providers emit full-width separators in pseudo-markup tags.
    # Normalize them so one parser can handle both variants.
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
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        if lowered == "null":
            return None
        return value


def _extract_dsml_invoke_markup(text: str) -> Optional[Dict[str, Any]]:
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

    return _tool_call_message(function_name, json.dumps(args, ensure_ascii=False))


def _extract_function_markup(text: str) -> Optional[Dict[str, Any]]:
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
        return _tool_call_message(function_name, arguments)

    return _extract_dsml_invoke_markup(normalized)


def _looks_like_tool_markup(text: str) -> bool:
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
    if tool_name in {"backend_action", "backend_report"}:
        if "query" in cleaned and not isinstance(cleaned["query"], dict):
            cleaned["query"] = {}
    if tool_name == "backend_action":
        if "body" in cleaned and not isinstance(cleaned["body"], dict):
            cleaned["body"] = {}
        if "method" in cleaned:
            cleaned["method"] = str(cleaned["method"]).strip().upper()
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


def _tool_result_from_backend_response(result: Dict[str, Any]) -> Dict[str, Any]:
    if result.get("ok"):
        return {
            "status_code": result.get("status_code"),
            "data": result.get("data"),
        }
    return {
        "error": "backend request failed",
        "status_code": result.get("status_code"),
        "detail": result.get("data") or result.get("detail") or result.get("error"),
    }


async def _run_backend_action(
    *,
    method: str,
    path: str,
    query: Optional[Dict[str, Any]],
    body: Optional[Dict[str, Any]],
    authorization: Optional[str],
) -> Dict[str, Any]:
    try:
        result = await _request_backend(
            method=method,
            path=path,
            authorization=authorization,
            query=query,
            body=body,
            validate_path=True,
        )
    except HTTPException as exc:
        return {"error": exc.detail, "status_code": exc.status_code}
    return _tool_result_from_backend_response(result)


def _coerce_report_int(value: Any, field_name: str) -> tuple[Optional[int], Optional[Dict[str, Any]]]:
    if value in (None, ""):
        return None, None
    try:
        normalized = int(value)
    except (TypeError, ValueError):
        return None, {"error": f"{field_name} must be an integer"}
    if normalized <= 0:
        return None, {"error": f"{field_name} must be greater than zero"}
    return normalized, None


def _coerce_report_identifier(value: Any, field_name: str) -> tuple[Optional[str], Optional[Dict[str, Any]]]:
    normalized = str(value or "").strip()
    if not normalized:
        return None, {"error": f"{field_name} is required"}
    if "/" in normalized or ".." in normalized:
        return None, {"error": f"{field_name} contains an invalid path value"}
    return normalized, None


async def _run_backend_report(
    *,
    action: str,
    event_id: Any,
    student_id: Any,
    governance_unit_id: Any,
    query: Optional[Dict[str, Any]],
    authorization: Optional[str],
) -> Dict[str, Any]:
    action_name = str(action or "").strip().lower()
    query_params = dict(query or {})
    path: Optional[str] = None

    if action_name == "school_attendance_summary":
        path = "/api/attendance/summary"
    elif action_name == "student_overview":
        path = "/api/attendance/students/overview"
    elif action_name == "student_attendance_report":
        normalized_student_id, error = _coerce_report_int(student_id, "student_id")
        if error:
            return error
        path = f"/api/attendance/students/{normalized_student_id}/report"
    elif action_name == "student_attendance_stats":
        normalized_student_id, error = _coerce_report_int(student_id, "student_id")
        if error:
            return error
        path = f"/api/attendance/students/{normalized_student_id}/stats"
    elif action_name == "student_attendance_records":
        normalized_student_id, error = _coerce_report_identifier(student_id, "student_id")
        if error:
            return error
        path = f"/api/attendance/students/{normalized_student_id}/records"
    elif action_name == "my_attendance_records":
        path = "/api/attendance/me/records"
    elif action_name == "event_attendance_report":
        normalized_event_id, error = _coerce_report_int(event_id, "event_id")
        if error:
            return error
        path = f"/api/attendance/events/{normalized_event_id}/report"
    elif action_name == "event_attendees":
        normalized_event_id, error = _coerce_report_int(event_id, "event_id")
        if error:
            return error
        path = f"/api/attendance/events/{normalized_event_id}/attendees"
    elif action_name == "event_attendances":
        normalized_event_id, error = _coerce_report_int(event_id, "event_id")
        if error:
            return error
        path = f"/api/attendance/events/{normalized_event_id}/attendances"
    elif action_name == "governance_dashboard_overview":
        normalized_unit_id, error = _coerce_report_int(governance_unit_id, "governance_unit_id")
        if error:
            return error
        path = f"/api/governance/units/{normalized_unit_id}/dashboard-overview"
    else:
        return {"error": f"unsupported report action: {action_name}"}

    try:
        result = await _request_backend(
            method="GET",
            path=path,
            authorization=authorization,
            query=query_params,
            validate_path=True,
        )
    except HTTPException as exc:
        return {"error": exc.detail, "status_code": exc.status_code}
    return _tool_result_from_backend_response(result)


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
    authorization = request.headers.get("authorization")
    identity_school_id = (
        body.user_school_id
        if body.user_school_id is not None
        else identity.get("school_id")
    )
    runtime_governance_access = await _resolve_runtime_governance_access(
        authorization=authorization,
        user_id=request_user_id,
        school_id=identity_school_id,
    )
    effective_school_id = (
        body.user_school_id
        if body.user_school_id is not None
        else identity_school_id
        if identity_school_id is not None
        else runtime_governance_access.get("school_id")
    )
    primary_role, effective_roles = _get_roles_from_identity(
        identity,
        body.user_role,
        runtime_governance_access.get("roles") or [],
    )
    effective_permissions = _get_permissions_from_identity(
        identity,
        runtime_governance_access.get("permission_codes") or [],
    )
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
            content = _extract_text_content(response_msg.get("content"))
            if content.strip():
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
        content = _extract_text_content(response_msg.get("content"))
        if content.strip():
            final_assistant_text = content

    if final_assistant_text:
        assistant_text = final_assistant_text
    elif messages and messages[-1].get("role") == "tool":
        assistant_text = "I completed a data step but couldn't finish the reply cleanly. Ask again and I'll continue from there."
    else:
        last_content = _extract_text_content(messages[-1].get("content")) if messages else ""
        assistant_text = last_content if last_content.strip() else "No response generated."

    # Safety net: if a provider returns pseudo tool markup as plain text,
    # recover and execute it so raw internals never leak to end users.
    if isinstance(assistant_text, str) and assistant_text.strip() and _looks_like_tool_markup(assistant_text):
        recovered_tool_call = _extract_function_markup(assistant_text)
        if recovered_tool_call is not None:
            if messages and isinstance(messages[-1], dict) and not messages[-1].get("tool_calls"):
                messages[-1] = recovered_tool_call
            else:
                messages.append(recovered_tool_call)

            for tool_call in recovered_tool_call["tool_calls"]:
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

            follow_up = await _call_openai(messages, tools=None)
            messages.append(follow_up)
            follow_up_content = follow_up.get("content")
            if isinstance(follow_up_content, str) and follow_up_content.strip():
                assistant_text = follow_up_content
            else:
                assistant_text = (
                    "I hit a formatting issue while processing your request, "
                    "but I can continue if you ask me again."
                )
        else:
            assistant_text = (
                "I hit a formatting issue while processing your request, "
                "but I can continue if you ask me again."
            )

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
