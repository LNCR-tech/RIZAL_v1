# Aura Assistant v1 vs. v2: Architectural Comparison

This document provides a comprehensive side-by-side comparison of the legacy **Assistant-v1** and the newly refactored **Assistant-v2**. The migration focuses on transforming a monolithic architecture into a clean, modular, properly decoupled structure using the official Model Context Protocol (MCP) standards.

---

## 1. High-Level Architecture Overview

### Assistant-v1: The Monolith
- **Structure:** Heavily monolithic. The core logic is concentrated entirely within a massive `assistant.py` file (~109KB, 2,863 lines).
- **Concerns:** Routing, database models, database connections, authentication (`jwt` decoding), governance policy evaluation, LLM prompting, system prompt generation, and streaming logic are all tightly coupled in one single script.
- **Routing:** Complex nested functions and localized `httpx` client instantiations for direct internal bridging.

### Assistant-v2: Clean & Modular
- **Structure:** Highly modular. `main.py` serves strictly as an API Gateway/Entrypoint and is extremely lightweight (~17KB, ~400 lines).
- **Separation of Concerns:** Core business logic is strictly decoupled into distinct domain modules under the `lib/` directory:
  - `auth.py`: JWT token verification and identity parsing.
  - `database.py`: SQLAlchemy models, engines, and CRUD session logic.
  - `llm.py`: Provider-agnostic LLM interaction streams handling (OpenAI/Gemini).
  - `policy.py`: Governance rules and role limitations.
  - `tools_logic.py`: Argument parsing, payload sanitization, and fallback markup recovery.
  - `mcp_client.py`: The `MultiMCPClient` infrastructure that dynamically scales tools.

> [!TIP]
> **Why it matters:** In v2, debugging an auth issue no longer requires navigating a 2,000-line routing file. This strict separation dramatically lowers the cognitive load required to maintain and extend the assistant.

---

## 2. Model Context Protocol (MCP) Implementation

### Assistant-v1: Embedded Sub-Apps
- **Integration:** MCP tooling is "embedded". Tools like `schema_server.py`, `query_server.py`, and `school_admin_server.py` are attached as sub-applications directly to the root FastAPI app via `app.mount()`.
- **Execution:** Runs in the exact same application context/event loop.
- **Config:** Sub-app endpoints are hardcoded throughout the router environments.

### Assistant-v2: Standardized Stdio Servers
- **Integration:** Adopts the **true MCP architectural pattern**. The servers located in `mcp_servers/` act as independent, isolated processes.
- **Execution:** Governed by `mcp_config.json`. The assistant spawns native MCP external shell processes via `MultiMCPClient` communicating over robust `stdio` streams (the industry standard for standard MCP connection).
- **Extensibility:** Adding a new tool server to v2 requires *zero* changes to `main.py`—you simply plug the new entry point into `mcp_config.json`.

---

## 3. Tool Calling and LLM Pipeline

### Assistant-v1: HTTP Fallbacks
- **Pipeline:** Relies heavily on custom internal `httpx` calls chaining between the mounted FastMCP routes.
- **Fallbacks:** Often struggles with reliable tool serialization, leading to custom fallback regex patterns directly intertwined with core SSE streaming loops.

### Assistant-v2: The Recursive Loop Engine
- **Pipeline:** Features a beautifully abstracted recursive reasoning loop (`call_llm_stream`).
- **Tool Dispatch:** When the LLM decides to use a tool, `mcp_client.call_tool` delegates the work to isolated servers cleanly, yielding event triggers like `tool_call` and `tool_done` transparently to the front-end SSE stream.
- **Context Injection:** Trust Headers (User ID, Roles, Permissions, Auth tokens) are surgical injected into the tool arguments reliably before passing them into the secure `mcp_client` boundary.

---

## 4. Dependencies & Environments

| Feature | Assistant-v1 | Assistant-v2 |
| :--- | :--- | :--- |
| **Frameworks** | `fastapi==0.110.0` | `fastapi==0.129.2`, `mcp==1.26.0`, `fastmcp==2.14.5` |
| **LLM SDKs** | Raw HTTP requests | Standardized `openai==2.28.0`, `google-genai==1.66.0` |
| **Validation** | Pydantic v2 (mixed usage) | Strict `pydantic==2.12.5`, `pydantic-settings` |
| **Entry Point** | `uvicorn assistant:app` | `uvicorn main:app` |

---

## Summary of the Upgrade

The transition to Assistant-v2 was a major **architectural maturation**. 
By adopting true stdio-based MCP patterns and strictly segmenting domain operations into a `lib/` core, the application has moved from a fragile "scripted monolith" to a highly robust "framework-agnostic orchestrator". 

This ensures that future work on prompts, new tool integrations, or transitioning LLM providers can be executed surgically without risk of cascading bugs into authentication or runtime governance logic.
