# Agentic Developer Learning Guide

[<- Back to doc index](../README.md)

> **Status:** ACTIVE — IN PROGRESS
> **Last Updated:** 2026-04-22

---

This guide helps you understand the AURA v3.2 Agentic assistant subsystem by walking through its code mechanics and design patterns.

---

## 1. The Core Architecture

The Agentic subsystem is a **role-aware LLM orchestration layer**. It does not just pass user messages to an AI — it wraps them in a strict security and capability context before any tool call is made.

### The Orchestrator: `Assistant/assistant.py`

This is the heart of the system. It handles:

- **Authentication** — Verifies the JWT and extracts user roles and school metadata.
- **Context Building** — Dynamically constructs a system prompt that tells the LLM exactly what it can and cannot do based on the user's role.
- **Tool Selection** — Uses OpenAI-compatible tool calling to interact with the database or backend.
- **Memory** — Manages conversation history in a dedicated assistant database.

---

## 2. The Policy Engine

The most critical part of the Agentic design is the **Policy Engine** in `Assistant/mcp/policy.py`.

### How It Works

The policy engine defines `AccessPolicy` objects that specify:

- `allowed_tables` — Which tables the role can read.
- `allowed_columns` — Which specific columns are safe (e.g., hiding password hashes).
- `required_filters` — Mandatory `WHERE` clauses (e.g., `school_id = :user_school_id`).
- `allowed_write_tables` — Which tables can be updated or inserted into.
- `capability_notes` — Plain-English descriptions of what the role can do.

### Role Stacking

The system supports **Base Roles** (admin, campus_admin, student) and **Officer Permissions** (manage_events, manage_attendance).

- If a user is a `student` but also has `manage_events` permission, the policies are **merged** using `merge_policies()`.
- This ensures that a student leader gets the combined access of a student plus event management tools.

---

## 3. The Tooling Flow (MCP)

"MCP" stands for Model Context Protocol style services. In this project, they are implemented as local Python servers or modules.

### The Request Lifecycle

1. **User asks:** "List all events in my school."
2. **Assistant** sees the user is a `campus_admin` for `school_id: 12`.
3. **Assistant** calls the `query_server` tool.
4. **Query Server** checks `policy.py`:
   - Is `events` table allowed? **Yes.**
   - Is there a required filter? **Yes: `school_id`.**
5. **Query Server** executes: `SELECT ... FROM events WHERE school_id = 12`.
6. **LLM** receives the data and formats the answer for the user.

### Important Guardrails

- **No DELETE** — `query_server.py` explicitly blocks `DELETE` and `DROP` commands.
- **Undo Logic** — For `UPDATE` or `INSERT`, the system generates an undo payload so changes can be reverted if the assistant makes a mistake.

---

## 4. How to Extend Agentic

To add a new capability to the assistant, follow these steps:

### Step 1: Update the Policy

Add the new table or permission to `Assistant/mcp/policy.py`.

```python
"manage_inventory": AccessPolicy(
    allowed_tables={"inventory_items", "categories"},
    allowed_write_tables={"inventory_items"},
    required_filters={"inventory_items": {"school_id"}},
    capability_notes=("Can manage school inventory items.",)
)
```

### Step 2: Add a Tool

If the capability is more complex than a simple database query, add it as a new tool in `Assistant/assistant.py` or a dedicated server in `Assistant/mcp/`.

### Step 3: Update the System Prompt

The text in `Assistant/system_prompt.txt` guides the LLM on how to use the tools. If you add a complex business logic tool, describe its purpose there.

---

## 5. Local Learning Sandbox

Since the assistant is not yet wired into `docker-compose.yml`, you can run it manually for development and testing:

1. **Setup env** — Copy `Assistant/.env.example` to `Assistant/.env` and add your `OPENAI_API_KEY`.
2. **Install deps** — `pip install -r Assistant/requirements.txt`
3. **Run assistant** — `python Assistant/assistant.py`
4. **Test MCP servers individually:**
   - `python Assistant/mcp/schema_server.py`
   - `python Assistant/mcp/query_server.py`

---

## Key Files to Study

| File | Purpose |
|---|---|
| `Assistant/assistant.py` | Main orchestration logic |
| `Assistant/mcp/policy.py` | Security and access rules |
| `Assistant/mcp/query_server.py` | Scoped database query tool |
| `Assistant/mcp/schema_server.py` | Allowed table and column registry |
| `Assistant/mcp/school_admin_server.py` | Structured admin actions (school, department, program) |
| `Assistant/mcp/student_import_server.py` | Smart wrapper that calls the main backend import API |

---

For the full architectural overview, see [ai-project-guide.md](./ai-project-guide.md).
