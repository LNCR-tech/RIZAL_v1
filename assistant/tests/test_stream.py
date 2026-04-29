from unittest.mock import AsyncMock, patch
from main import mcp_client


def _collect_sse(response) -> list[dict]:
    """Parse SSE response text into a list of {event, data} dicts."""
    import json
    events = []
    current_event = {}
    for line in response.text.splitlines():
        if line.startswith("event:"):
            current_event["event"] = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            current_event["data"] = json.loads(line.split(":", 1)[1].strip())
        elif line == "" and current_event:
            events.append(current_event)
            current_event = {}
    return events


def test_stream_no_token(client):
    response = client.post("/assistant/stream", json={"message": "hello"})
    assert response.status_code == 401


def test_stream_expired_token(client, expired_token):
    response = client.post(
        "/assistant/stream",
        json={"message": "hello"},
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401


def test_stream_invalid_conversation_id(client, auth_headers):
    response = client.post(
        "/assistant/stream",
        json={"message": "hello", "conversation_id": "00000000-0000-0000-0000-000000000000"},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_stream_success(client, auth_headers):
    async def mock_stream(messages, tools=None):
        yield {"type": "chunk", "content": "Hello!"}
        yield {"role": "assistant", "content": "Hello!", "tool_calls": None}

    with patch("main.call_llm_stream", return_value=mock_stream([])), \
         patch("main.resolve_backend_user_id", new=AsyncMock(return_value=None)), \
         patch("main.resolve_runtime_governance_access", new=AsyncMock(return_value={"permission_codes": [], "roles": [], "school_id": 1})):

        response = client.post(
            "/assistant/stream",
            json={"message": "hello"},
            headers=auth_headers,
        )

    assert response.status_code == 200
    events = _collect_sse(response)
    event_types = [e["event"] for e in events]
    assert "message" in event_types
    assert "done" in event_types

    done_event = next(e for e in events if e["event"] == "done")
    assert done_event["data"]["finish_reason"] == "stop"
    assert "conversation_id" in done_event["data"]


def test_stream_tool_call_events(client, auth_headers):
    """Tool call flow emits tool_call and tool_done SSE events."""
    async def turn_one(messages, tools=None):
        yield {
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id": "call_1",
                "function": {"name": "query_attendance", "arguments": "{}"},
            }],
        }

    async def turn_two(messages, tools=None):
        yield {"type": "chunk", "content": "Done."}
        yield {"role": "assistant", "content": "Done.", "tool_calls": None}

    gen_one = turn_one(None)
    gen_two = turn_two(None)

    with patch("main.call_llm_stream", side_effect=[gen_one, gen_two]), \
         patch("main.resolve_backend_user_id", new=AsyncMock(return_value=None)), \
         patch("main.resolve_runtime_governance_access", new=AsyncMock(return_value={"permission_codes": [], "roles": [], "school_id": 1})):

        response = client.post(
            "/assistant/stream",
            json={"message": "show attendance"},
            headers=auth_headers,
        )

    assert response.status_code == 200
    events = _collect_sse(response)
    event_types = [e["event"] for e in events]
    assert "tool_call" in event_types
    assert "tool_done" in event_types
    assert "done" in event_types


def test_stream_daily_quota_exceeded(client, auth_headers):
    """Exceeding the daily message quota returns 429."""
    import datetime
    from lib.database import DailyUsage, SessionLocal

    db = SessionLocal()
    today = datetime.datetime.now(datetime.timezone.utc).date()
    # admin limit is 500 — insert a row already at the limit
    existing = db.query(DailyUsage).filter_by(
        user_id="test@aura.local", user_role="admin", usage_date=today
    ).first()
    if existing:
        existing.message_count = 500
    else:
        db.add(DailyUsage(user_id="test@aura.local", user_role="admin", usage_date=today, message_count=500))
    db.commit()
    db.close()

    with patch("main.resolve_backend_user_id", new=AsyncMock(return_value=None)), \
         patch("main.resolve_runtime_governance_access", new=AsyncMock(return_value={"permission_codes": [], "roles": ["admin"], "school_id": 1})):
        response = client.post(
            "/assistant/stream",
            json={"message": "hello"},
            headers=auth_headers,
        )

    assert response.status_code == 429
