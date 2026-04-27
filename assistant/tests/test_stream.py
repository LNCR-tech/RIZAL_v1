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
