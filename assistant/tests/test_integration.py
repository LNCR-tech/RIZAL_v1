"""
Integration tests — in-process, no live servers required.

Both the backend and assistant apps run via FastAPI TestClient in the same
pytest process. The assistant's HTTP calls to the backend are intercepted and
routed through the backend TestClient directly.

Run with:
    pytest -v -m integration tests/test_integration.py
"""

import asyncio
import json
import os
import sys
import datetime
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

# ---------------------------------------------------------------------------
# Environment — must be set before any app import
# ---------------------------------------------------------------------------

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ASSISTANT_DB_URL", "sqlite:///./test_assistant_integration.db")
os.environ.setdefault("AI_API_KEY", "test-key")
os.environ.setdefault("AI_API_BASE", "https://test.example.com/v1")
os.environ.setdefault("AI_MODEL", "test-model")
os.environ.setdefault("BACKEND_API_BASE_URL", "http://localhost:8000")
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:cmpjdatabase@127.0.0.1:5432/fastapi_db")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("FACE_SCAN_BYPASS_ALL", "true")
os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "true")
os.environ.setdefault("EMAIL_TRANSPORT", "disabled")

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from fastapi.testclient import TestClient

# Put the backend on sys.path so its modules are importable from the assistant dir
_BACKEND_DIR = str(Path(__file__).resolve().parent.parent.parent / "backend")
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

# Backend app
from app.main import app as backend_app
from app.core.database import SessionLocal as BackendSessionLocal
from app.core.dependencies import get_db as backend_get_db

# Assistant app
from lib.database import Base as AssistantBase, engine as assistant_engine, SessionLocal as AssistantSessionLocal
from lib.database import get_db as assistant_get_db
from main import app as assistant_app, mcp_client

# MCP tool functions (called in-process)
LIB_DIR = str(Path(__file__).resolve().parent.parent / "lib")
MCP_DIR = str(Path(__file__).resolve().parent.parent / "mcp_servers")
for _d in (LIB_DIR, MCP_DIR):
    if _d not in sys.path:
        sys.path.insert(0, _d)

from query_server import mcp_query
from admin_server import list_departments, list_programs, list_schools

# ---------------------------------------------------------------------------
# Session-scoped DB setup
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def setup_assistant_db():
    AssistantBase.metadata.create_all(bind=assistant_engine)
    yield
    AssistantBase.metadata.drop_all(bind=assistant_engine)


@pytest.fixture(scope="session")
def backend_db():
    import importlib.util
    db = BackendSessionLocal()
    spec = importlib.util.spec_from_file_location(
        "backend_conftest",
        str(Path(_BACKEND_DIR) / "tests" / "conftest.py")
    )
    backend_conftest = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(backend_conftest)
    backend_conftest._seed(db)
    db.commit()
    yield db
    db.close()


# ---------------------------------------------------------------------------
# Backend TestClient + real token
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def backend_client(backend_db):
    def override_get_db():
        yield backend_db

    backend_app.dependency_overrides[backend_get_db] = override_get_db
    with TestClient(backend_app) as c:
        yield c
    backend_app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def admin_token(backend_client):
    r = backend_client.post("/login", json={"email": "admin@test.com", "password": "TestPass123!"})
    assert r.status_code == 200, f"Admin login failed: {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def campus_admin_token(backend_client):
    r = backend_client.post("/login", json={"email": "campus_admin@test.com", "password": "TestPass123!"})
    assert r.status_code == 200, f"Campus admin login failed: {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def student_token(backend_client):
    r = backend_client.post("/login", json={"email": "student@test.com", "password": "TestPass123!"})
    assert r.status_code == 200, f"Student login failed: {r.text}"
    return r.json()["access_token"]


# ---------------------------------------------------------------------------
# Assistant TestClient wired to backend TestClient
# ---------------------------------------------------------------------------

def _make_backend_proxy(backend_client: TestClient):
    """
    Returns a coroutine that mimics lib.auth.request_backend but routes
    calls through the in-process backend TestClient instead of real HTTP.
    """
    async def _proxy(method: str, path: str, authorization=None, query=None, body=None):
        headers = {"Authorization": authorization} if authorization else {}
        resp = backend_client.request(method, f"/{path.lstrip('/')}", headers=headers, params=query, json=body)
        ok = resp.status_code < 400
        try:
            data = resp.json()
        except Exception:
            data = resp.text
        return {"ok": ok, "status_code": resp.status_code, "data": data}

    return _proxy


@pytest.fixture(scope="session")
def assistant_db_session():
    db = AssistantSessionLocal()
    yield db
    db.close()


@pytest.fixture()
def assistant_client(backend_client, assistant_db_session):
    def override_assistant_db():
        yield assistant_db_session

    assistant_app.dependency_overrides[assistant_get_db] = override_assistant_db

    proxy = _make_backend_proxy(backend_client)

    with patch("lib.auth.request_backend", side_effect=proxy), \
         patch.object(mcp_client, "get_all_tools", new=AsyncMock(return_value=[])), \
         patch.object(mcp_client, "call_tool", new=AsyncMock(return_value="{}")):
        with TestClient(assistant_app) as c:
            yield c

    assistant_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# SSE helper
# ---------------------------------------------------------------------------

def _parse_sse(text: str) -> list[dict]:
    events, current = [], {}
    for line in text.splitlines():
        if line.startswith("event:"):
            current["event"] = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            try:
                current["data"] = json.loads(line.split(":", 1)[1].strip())
            except json.JSONDecodeError:
                current["data"] = line.split(":", 1)[1].strip()
        elif line == "" and current:
            events.append(current)
            current = {}
    return events


# ---------------------------------------------------------------------------
# Group 1: Assistant ↔ Backend (auth contract)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_backend_issues_valid_jwt(backend_client):
    """Backend /login returns a JWT for valid credentials."""
    r = backend_client.post("/login", json={"email": "admin@test.com", "password": "TestPass123!"})
    assert r.status_code == 200
    assert "access_token" in r.json()


@pytest.mark.integration
def test_backend_rejects_wrong_password(backend_client):
    r = backend_client.post("/login", json={"email": "admin@test.com", "password": "wrong"})
    assert r.status_code in (400, 401, 403)


@pytest.mark.integration
def test_assistant_accepts_backend_jwt(assistant_client, admin_token):
    """Assistant /assistant/stream accepts a JWT issued by the backend."""
    async def mock_stream(messages, tools=None):
        yield {"type": "chunk", "content": "ok"}
        yield {"role": "assistant", "content": "ok", "tool_calls": None}

    with patch("main.call_llm_stream", return_value=mock_stream([])):
        r = assistant_client.post(
            "/assistant/stream",
            json={"message": "hello"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
    assert r.status_code == 200


@pytest.mark.integration
def test_assistant_rejects_tampered_jwt(assistant_client, admin_token):
    """Assistant must reject a tampered backend JWT with 401."""
    tampered = admin_token[:-5] + "XXXXX"
    r = assistant_client.post(
        "/assistant/stream",
        json={"message": "hello"},
        headers={"Authorization": f"Bearer {tampered}"},
    )
    assert r.status_code == 401


@pytest.mark.integration
def test_assistant_rejects_missing_auth(assistant_client):
    r = assistant_client.post("/assistant/stream", json={"message": "hello"})
    assert r.status_code == 401


@pytest.mark.integration
def test_backend_me_endpoint_returns_user(backend_client, admin_token):
    """The /api/users/me/ endpoint the assistant calls returns a valid user object."""
    r = backend_client.get("/api/users/me/", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    data = r.json()
    assert "id" in data
    assert "email" in data


@pytest.mark.integration
def test_backend_governance_access_endpoint(backend_client, campus_admin_token):
    """The /api/governance/access/me endpoint the assistant calls is reachable."""
    r = backend_client.get("/api/governance/access/me", headers={"Authorization": f"Bearer {campus_admin_token}"})
    assert r.status_code in (200, 404)


@pytest.mark.integration
def test_backend_rejects_invalid_token_on_me(backend_client):
    """Backend correctly rejects a bad token — assistant must handle this gracefully."""
    r = backend_client.get("/api/users/me/", headers={"Authorization": "Bearer bad.token.here"})
    assert r.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Group 2: MCP Tools ↔ Backend DB (in-process)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_mcp_query_events_as_admin():
    """mcp_query fetches events from the real DB with admin role."""
    result = asyncio.run(
        mcp_query(roles=["admin"], user_id="1", school_id=1, table="events", limit=5)
    )
    assert "error" not in result, result.get("error")
    assert "rows" in result
    assert isinstance(result["rows"], list)


@pytest.mark.integration
def test_mcp_query_blocks_sensitive_columns():
    """mcp_query rejects queries targeting password_hash."""
    result = asyncio.run(
        mcp_query(
            roles=["admin"], user_id="1", school_id=1,
            sql="select password_hash from users where school_id = :school_id",
            params={"school_id": 1},
        )
    )
    assert "error" in result
    assert "sensitive" in result["error"].lower()


@pytest.mark.integration
def test_mcp_query_blocks_ddl():
    """mcp_query rejects DROP/DELETE statements."""
    result = asyncio.run(
        mcp_query(roles=["admin"], user_id="1", school_id=1, sql="drop table events")
    )
    assert "error" in result


@pytest.mark.integration
def test_mcp_query_student_cannot_access_users_table():
    """Student role must not query the users table."""
    result = asyncio.run(
        mcp_query(roles=["student"], user_id="1", school_id=1, table="users", limit=5)
    )
    assert "error" in result
    assert "not allowed" in result["error"].lower()


@pytest.mark.integration
def test_mcp_query_count_only():
    """mcp_query count_only returns a count row."""
    result = asyncio.run(
        mcp_query(roles=["admin"], user_id="1", school_id=1, table="events", count_only=True)
    )
    assert "error" not in result, result.get("error")
    assert result["rows"][0].get("count") is not None


@pytest.mark.integration
def test_mcp_list_departments():
    """list_departments returns departments for school 1."""
    result = asyncio.run(
        list_departments(roles=["campus_admin"], school_id=1)
    )
    assert "error" not in result, result.get("error")
    assert "departments" in result
    assert isinstance(result["departments"], list)


@pytest.mark.integration
def test_mcp_list_programs():
    """list_programs returns programs for school 1."""
    result = asyncio.run(
        list_programs(roles=["campus_admin"], school_id=1)
    )
    assert "error" not in result, result.get("error")
    assert "programs" in result


@pytest.mark.integration
def test_mcp_list_schools_as_admin():
    """list_schools returns at least one school for admin."""
    result = asyncio.run(
        list_schools(roles=["admin"])
    )
    assert "error" not in result, result.get("error")
    assert result["count"] >= 1


# ---------------------------------------------------------------------------
# Group 3: Full Flow — Frontend → Assistant → Backend
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_stream_returns_valid_sse_shape(assistant_client, admin_token):
    """Full stream flow returns well-formed SSE events with conversation_id."""
    async def mock_stream(messages, tools=None):
        yield {"type": "chunk", "content": "Hello!"}
        yield {"role": "assistant", "content": "Hello!", "tool_calls": None}

    with patch("main.call_llm_stream", return_value=mock_stream([])):
        r = assistant_client.post(
            "/assistant/stream",
            json={"message": "hello"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

    assert r.status_code == 200
    events = _parse_sse(r.text)
    event_types = [e["event"] for e in events]
    assert "message" in event_types
    assert "done" in event_types

    done = next(e for e in events if e["event"] == "done")
    assert "conversation_id" in done["data"]
    assert done["data"]["finish_reason"] == "stop"


@pytest.mark.integration
def test_stream_tool_call_flow(assistant_client, admin_token):
    """Tool call flow emits tool_call and tool_done SSE events."""
    async def turn_one(messages, tools=None):
        yield {
            "role": "assistant",
            "content": None,
            "tool_calls": [{"id": "call_1", "function": {"name": "mcp_query", "arguments": "{}"}}],
        }

    async def turn_two(messages, tools=None):
        yield {"type": "chunk", "content": "Done."}
        yield {"role": "assistant", "content": "Done.", "tool_calls": None}

    with patch("main.call_llm_stream", side_effect=[turn_one(None), turn_two(None)]):
        r = assistant_client.post(
            "/assistant/stream",
            json={"message": "show events"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

    assert r.status_code == 200
    events = _parse_sse(r.text)
    event_types = [e["event"] for e in events]
    assert "tool_call" in event_types
    assert "tool_done" in event_types
    assert "done" in event_types


@pytest.mark.integration
def test_conversation_persists_after_stream(assistant_client, admin_token):
    """Conversation created during stream is retrievable via /conversations/{id}."""
    async def mock_stream(messages, tools=None):
        yield {"type": "chunk", "content": "Saved."}
        yield {"role": "assistant", "content": "Saved.", "tool_calls": None}

    with patch("main.call_llm_stream", return_value=mock_stream([])):
        r = assistant_client.post(
            "/assistant/stream",
            json={"message": "remember this"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

    assert r.status_code == 200
    events = _parse_sse(r.text)
    done = next(e for e in events if e["event"] == "done")
    conversation_id = done["data"]["conversation_id"]

    r2 = assistant_client.get(
        f"/conversations/{conversation_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r2.status_code == 200
    data = r2.json()
    assert data["conversation_id"] == conversation_id
    assert any(m["role"] == "user" for m in data["messages"])
    assert any(m["role"] == "assistant" for m in data["messages"])


@pytest.mark.integration
def test_conversation_isolated_between_users(assistant_client, admin_token, campus_admin_token):
    """A conversation owned by one user is not accessible by another."""
    async def mock_stream(messages, tools=None):
        yield {"type": "chunk", "content": "Private."}
        yield {"role": "assistant", "content": "Private.", "tool_calls": None}

    with patch("main.call_llm_stream", return_value=mock_stream([])):
        r = assistant_client.post(
            "/assistant/stream",
            json={"message": "private"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

    assert r.status_code == 200
    done = next(e for e in _parse_sse(r.text) if e["event"] == "done")
    conversation_id = done["data"]["conversation_id"]

    r2 = assistant_client.get(
        f"/conversations/{conversation_id}",
        headers={"Authorization": f"Bearer {campus_admin_token}"},
    )
    assert r2.status_code == 404


@pytest.mark.integration
def test_student_role_stream_accepted(assistant_client, student_token):
    """Student JWT is accepted by the assistant stream endpoint."""
    async def mock_stream(messages, tools=None):
        yield {"type": "chunk", "content": "Hi student."}
        yield {"role": "assistant", "content": "Hi student.", "tool_calls": None}

    with patch("main.call_llm_stream", return_value=mock_stream([])):
        r = assistant_client.post(
            "/assistant/stream",
            json={"message": "hello"},
            headers={"Authorization": f"Bearer {student_token}"},
        )
    assert r.status_code == 200
