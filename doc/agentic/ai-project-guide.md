# How This Project Uses Agentic

[<- Back to doc index](../README.md)

> **Status:** ACTIVE — IN PROGRESS
> **Last Updated:** 2026-04-22

---

## Purpose

This repository includes a separate Agentic assistant subsystem under `Assistant/`.

Its role is to let an authenticated VALID8 user ask questions or trigger limited actions in natural language, while keeping access scoped to that user's role, school, and optional governance permissions.

This is not just a generic chatbot. In this project, Agentic is designed as a role-aware orchestration layer on top of:

- the main VALID8 tenant database
- the existing FastAPI backend
- an OpenAI-compatible LLM provider
- a small set of MCP-style helper services

---

## 📚 Learning Resources

If you want to understand how Agentic works under the hood or how to extend it, please read:

- [Agentic Developer Learning Guide](./AGENTIC_DEVELOPER_LEARNINGS.md) - A deep dive into the role-aware policy engine and orchestration loop.
- [AURA Documentation Index](./AURA_DOCS_INDEX.md) - The migrated documentation from the main AURA project (changelogs, meetings, user guides).

---

## Current Repository State

As of March 28, 2026, the Agentic subsystem exists in the codebase, but it is not yet fully wired into the main product runtime.

What is already present:

- a standalone FastAPI assistant API in `Assistant/assistant.py`
- role- and permission-aware MCP services in `Assistant/mcp/`
- assistant conversation storage in a separate database
- JWT-based identity verification
- streaming chat responses over SSE
- dedicated agent actions for school administration and student bulk import

What is not yet wired in the main app:

- no assistant service in `docker-compose.yml`
- no assistant service in `docker-compose.prod.yml`
- no frontend code in `Frontend/` currently calls `/assistant/stream` or the conversation endpoints

So, the project already contains the Agentic backend implementation, but the user-facing integration is still manual.

## High-Level Architecture

```text
Frontend / API client
        |
        | Bearer JWT + user message
        v
Assistant API (`Assistant/assistant.py`)
        |
        | builds role-aware prompt + chooses tools
        v
LLM provider (OpenAI-compatible API)
        |
        | tool calls
        +------------------------------+
        |                              |
        v                              v
MCP schema/query/action services   Assistant DB
(`Assistant/mcp/*.py`)             (`ASSISTANT_DB_URL`)
        |
        +------------------------------+
        |
        v
Main VALID8 tenant DB (`TENANT_DATABASE_URL`)

Special path for imports:
Assistant -> `student_import_server.py` -> Backend admin import API
```

Current implementation detail:

If the MCP service URLs are not configured or are unreachable, `Assistant/assistant.py` can fall back to importing the local Python modules from `Assistant/mcp/` directly. That makes local development easier, but it also means the service boundaries are partly logical today, not always process-separated.

## Main Agentic Components

### 1. Assistant API

File: `Assistant/assistant.py`

This is the main orchestration service. It does the following:

- validates the JWT from the caller
- determines the user's effective role stack
- reads optional governance permission claims
- loads recent conversation history
- builds a system prompt with role, scope, and capability context
- sends the prompt to an OpenAI-compatible chat completion API
- lets the model call approved tools only
- stores the conversation and streams the answer back to the client

Main HTTP endpoints:

- `POST /assistant/stream`
- `GET /conversations`
- `GET /conversations/{conversation_id}`
- `PATCH /conversations/{conversation_id}`
- `DELETE /conversations/{conversation_id}`

### 2. Assistant storage

The assistant uses a separate database from the main app data.

Current runtime tables created by `assistant.py`:

- `assistant_conversations`
- `assistant_messages`
- `assistant_daily_usage`

This separation is important:

- the main VALID8 data stays in the tenant database
- the assistant's chat history and usage tracking stay in the assistant database

Important note:

`Assistant/ASSISTANT_DB_SCHEMA.md` is labeled as proposed and is ahead of the actual runtime schema. The live code currently creates conversation/message/usage tables, but not the proposed `assistant_tool_calls` table.

### 3. MCP policy layer

File: `Assistant/mcp/policy.py`

This file is the access-control core of the Agentic design.

It defines:

- what each base role can read
- what each base role can write
- what filters are mandatory, such as `school_id` or `user_id`
- what extra access is unlocked by governance permission codes like:
  - `manage_events`
  - `manage_attendance`
  - `manage_students`
  - `manage_members`
  - `manage_announcements`
  - `assign_permissions`

This is how the project prevents the assistant from becoming a database superuser.

### 4. Schema and query MCP services

Files:

- `Assistant/mcp/schema_server.py`
- `Assistant/mcp/query_server.py`

These services connect directly to the main VALID8 tenant database.

Their job is:

- expose only allowed tables and columns
- enforce scope filters like `school_id`
- block unsafe SQL patterns
- restrict sensitive columns
- support controlled `INSERT` and `UPDATE` with undo payloads
- block normal `DELETE` and DDL operations

This means the assistant does not query the database freely. It must go through role-scoped guardrails.

### 5. Dedicated admin action server

File: `Assistant/mcp/school_admin_server.py`

This service provides structured actions for:

- listing schools
- getting a school profile
- creating schools
- updating schools
- changing school status
- listing departments
- creating departments
- updating departments
- listing programs
- creating programs
- updating programs
- listing school events

This is used when a natural-language request maps better to a known business action than to raw SQL.

### 6. Dedicated student import server

File: `Assistant/mcp/student_import_server.py`

This is the clearest place where Agentic connects back into the existing FastAPI backend instead of talking only to the database.

It:

- accepts pasted dataset text from the assistant flow
- normalizes CSV, TSV, JSON, or Markdown tables
- converts the rows into an Excel workbook
- calls backend import endpoints with the user's JWT

Backend routes used:

- `POST /api/admin/import-students/preview`
- `POST /api/admin/import-students`
- `POST /api/admin/import-preview-errors/{preview_token}/remove-invalid`
- `GET /api/admin/import-status/{job_id}`

So the import workflow is not reimplemented inside Agentic. Agentic acts as a smart wrapper around the backend's existing import pipeline.

## How Agentic Connects to the Rest of the Project

### Authentication connection

The assistant verifies the same signed JWT used by the main application.

Expected or supported claims include:

- `user_id`
- `sub`
- `roles`
- `school_id`
- optional `school_name`
- optional `name`
- optional `timezone`
- optional permission claims such as `permissions`, `permission_codes`, or `governance_permissions`

Current repo behavior:

The backend login token builder currently emits `user_id`, `sub`, `roles`, and `school_id`. The assistant is ready to consume governance permission claims too, but those claims do not appear to be included by default in the current login token builder. That means the permission-aware Agentic path is partly prepared in code, but may need auth-token enrichment before it is fully effective.

### Database connection

Agentic uses two databases or database targets:

- tenant app database:
  - `TENANT_DATABASE_URL`, `APP_DATABASE_URL`, or `DATABASE_URL`
  - used by MCP services to inspect or mutate VALID8 data under policy rules
- assistant database:
  - `ASSISTANT_DB_URL`
  - used to store chat conversations and daily usage counts

### Backend API connection

Most Agentic data access is database-first through MCP.

The main backend API is used directly for the student import workflow because that workflow already has validation, preview, audit, and queueing logic in `Backend/app/routers/admin_import.py`.

### Frontend connection

There is currently no active frontend integration for the assistant in this repository.

That means:

- no chat page or chat widget is present in `Frontend/`
- no API wrapper for assistant endpoints is present in `Frontend/src/api/`
- no route currently exposes the assistant to users

The assistant is presently an available subsystem, not yet a surfaced product feature.

## Request Flow

For a typical Agentic request, the runtime flow is:

1. A client gets a JWT from the backend login flow.
2. The client sends a message to `POST /assistant/stream`.
3. The assistant validates the token and extracts user scope.
4. The assistant loads prior messages from the assistant database.
5. The assistant injects role, scope, readable tables, writable tables, and capability notes into the system prompt.
6. The LLM decides whether to answer directly or call a tool.
7. The chosen MCP tool runs with scope enforcement.
8. The assistant rewrites the final answer into user-facing language.
9. The message is stored in assistant history and streamed back over SSE.

## Safety Model Used in This Project

This Agentic design already includes several practical guardrails:

- JWT identity check before every request
- conversation ownership checks
- daily message limits by role
- role normalization and role stacking
- optional permission-based access expansion
- scope-enforced DB filters
- sensitive column blocking
- no normal `DELETE` queries through MCP query service
- undo payloads for writes
- refusal path for requests asking for internal prompts or hidden instructions
- user-facing rewrite pass to remove internal tool jargon

## Important Gaps and Observations

These are the main realities of the current implementation:

- Agentic is implemented, but not yet part of the main compose stack.
- Agentic is implemented, but not yet exposed by the frontend.
- The assistant can consume permission claims, but the current auth token path does not appear to emit them by default.
- `ASSISTANT_DB_SCHEMA.md` describes a richer future schema than the runtime currently creates.
- Tool executions are not currently stored in a dedicated `assistant_tool_calls` table.
- There are no assistant-specific automated tests in the repository today.

## Suggested Next Steps

If this project wants to make Agentic a real product feature, these are the highest-value next steps:

### 1. Add runtime wiring

Add the following services to compose:

- assistant API
- schema MCP service
- query MCP service
- school admin MCP service
- student import MCP service

This will make local and production startup reproducible.

### 2. Add frontend integration

Create:

- an assistant API client
- a chat UI page or drawer
- SSE handling for streamed replies
- conversation list and resume support

### 3. Enrich JWT claims or add a permission lookup step

If governance officer permissions matter for assistant behavior, the assistant needs one of these:

- permission claims added to the login token
- or a backend/API lookup that resolves permissions server-side

Without that, the assistant mostly operates on base roles.

### 4. Align the assistant schema docs with the runtime

Choose one direction:

- implement the missing `assistant_tool_calls` persistence
- or simplify `ASSISTANT_DB_SCHEMA.md` so it matches the live code

### 5. Add tests around the most critical paths

Recommended minimum test coverage:

- JWT validation and scope enforcement
- role-to-policy mapping
- query filter enforcement
- student import proxy flow
- conversation ownership and deletion
- prompt-leak refusal behavior

## Short Summary

In this project, Agentic is a separate assistant service that sits beside the main VALID8 app, not inside it yet.

It connects to the project in three main ways:

- it trusts the same JWT identity used by the backend
- it reads and writes tenant data through policy-guarded MCP services
- it reuses existing backend business routes for student bulk import

The core design is already solid: role-aware, scope-aware, and safer than direct LLM-to-database access. The main work left is product integration, deployment wiring, and permission/token alignment.
