# Assistant Testing Guide

<!--nav-->
[Previous](../README.md) | [Next](../README.md) | [Home](/README.md)

---
<!--/nav-->


## Overview

The assistant has a pytest suite covering its three main endpoint groups: health, conversations, and the streaming chat endpoint. Tests run against an in-memory SQLite database â€” no Postgres, no Redis, no real LLM API calls required.

## Running Tests Locally

```powershell
cd assistant
pytest
```

Verbose output:

```powershell
pytest -v
```

Run a specific file:

```powershell
pytest tests/test_stream.py -v
```

### Prerequisites

No external services needed. The test suite self-configures via `conftest.py`:

- SQLite is used as the test database (`test_assistant.db`)
- LLM API calls are mocked â€” no real `AI_API_KEY` is used
- MCP tool calls are mocked â€” no MCP servers need to be running

The only requirement is the Python dependencies installed:

```powershell
pip install -r requirements.txt
```

## What Is Tested

| File | Coverage |
|---|---|
| `test_health.py` | `GET /health` â€” returns `{"status": "ok", "version": "v2-mcp"}` |
| `test_conversations.py` | List (empty + with data + auth guard), get by ID (success, 404, other user 404, auth guard), rename (success, 404, auth guard), delete (success, 404, auth guard) |
| `test_stream.py` | Auth guards (no token, expired token), invalid conversation ID, successful stream, tool call SSE events, daily quota exceeded (429) |

**Total: ~20 tests**

## What Is Not Tested

- **Real LLM responses** â€” `call_llm_stream` is mocked. Actual OpenAI/Gemini API calls, token budgeting, and tool-use loops are not exercised.
- **MCP tool execution** â€” `mcp_client.get_all_tools` and `mcp_client.call_tool` are mocked to return empty results. The MCP servers (`query_server`, `report_server`, etc.) are not started during tests.
- **Backend API integration** â€” `resolve_backend_user_id` and `resolve_runtime_governance_access` are mocked. The assistant does not make real calls to the backend during tests.

## How CI Works

GitHub Actions runs the assistant tests in the `assistant-tests` job using SQLite â€” no Postgres or Redis service containers are needed for this job.

The CI job:
1. Installs Python dependencies from `requirements.txt`
2. Runs `pytest` with test-only env vars set inline

Env vars used in CI:

```
SECRET_KEY: test-secret-key
ASSISTANT_DB_URL: sqlite:///./test_assistant.db
AI_API_KEY: test-key
AI_API_BASE: https://test.example.com/v1
AI_MODEL: test-model
BACKEND_API_BASE_URL: http://localhost:8000
```

## Test Architecture

- **SQLite in-process** â€” `conftest.py` sets `ASSISTANT_DB_URL=sqlite:///./test_assistant.db` and calls `Base.metadata.create_all()` before tests run. The schema is dropped after the session.
- **MCP mocking** â€” the `client` fixture patches `mcp_client.get_all_tools` and `mcp_client.call_tool` with `AsyncMock` so no MCP subprocess is spawned.
- **JWT auth** â€” the `auth_token` fixture mints a valid JWT signed with `test-secret-key`. The `expired_token` fixture mints one with a past expiry to test 401 rejection.
- **SSE parsing** â€” `test_stream.py` includes a `_collect_sse` helper that parses the `text/event-stream` response into a list of `{event, data}` dicts for assertion.
- **Per-test client** â€” unlike the backend, the assistant `client` fixture is function-scoped (not session-scoped), so each test gets a fresh client with clean mocks.

