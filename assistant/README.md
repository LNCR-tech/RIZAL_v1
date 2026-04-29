# Assistant Service

<!--nav-->
[Previous](../README.md) | [Next](docs/TESTING.md) | [Home](/README.md)

---
<!--/nav-->

AI assistant service for Aura. Provides streaming LLM responses with MCP tool integration for querying live school data.

## Stack

- Python + FastAPI
- OpenAI-compatible API (Groq, SiliconFlow, Gemini, etc.)
- MCP (Model Context Protocol) for tool integration
- Postgres for conversation storage

## Setup

```bash
cd assistant
cp .env.example .env
# fill in AI_API_KEY, ASSISTANT_DB_URL, SECRET_KEY (same as backend)

pip install -r requirements.txt
uvicorn main:app --port 8500 --reload
```

## Docs

- [Assistant Testing Guide](docs/TESTING.md)
- API docs: `http://localhost:8500/docs`

## Key Directories

- `lib/` — core assistant logic, conversation storage, MCP integration
- `mcp_servers/` — MCP tool server definitions

## Prompt Budgeting

The assistant sends a system prompt + recent conversation history to the LLM on every message. To keep requests under a token cap, it supports server-side prompt budgeting — older context is summarized into a hidden `meta_summary` message, and only the most recent messages are sent verbatim.

Optional env overrides:

- `ASSISTANT_PROMPT_BUDGET_TOKENS` (default `25000`)
- `ASSISTANT_PROMPT_RESERVE_COMPLETION_TOKENS` (default `2000`)
- `ASSISTANT_CONTEXT_KEEP_LAST_MESSAGES` (default `8`)
- `ASSISTANT_CONTEXT_SUMMARY_MAX_CHARS` (default `3500`)
