# Assistant Service

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

- [Assistant Guide](docs/)
- API docs: `http://localhost:8500/docs`

## Key Directories

- `lib/` — core assistant logic, conversation storage, MCP integration
- `mcp_servers/` — MCP tool server definitions
