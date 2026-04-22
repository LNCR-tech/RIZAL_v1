[<- Back to docs index](../../README.md)

# Assistant Database Schema (Proposed)

This schema stores assistant conversations, messages, and tool calls separately from the main app database.

## Tables

### 1) `assistant_conversations`
Tracks a user's conversation threads.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | UUID (PK) | Conversation id |
| `user_id` | TEXT | User identifier from main app |
| `user_role` | TEXT | Role at time of creation |
| `title` | TEXT | Optional title |
| `status` | TEXT | e.g. `active`, `archived`, `deleted` |
| `created_at` | TIMESTAMPTZ | Default `now()` |
| `updated_at` | TIMESTAMPTZ | Default `now()` |
| `last_message_at` | TIMESTAMPTZ | For sorting list |

Indexes:
- `(user_id, updated_at desc)`
- `(user_id, status)`

### 2) `assistant_messages`
Stores user/assistant/system messages in a conversation.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | UUID (PK) | Message id |
| `conversation_id` | UUID (FK) | References `assistant_conversations.id` |
| `role` | TEXT | `user`, `assistant`, `system`, `tool` |
| `content` | TEXT | Message body |
| `metadata` | JSONB | Optional extra data |
| `created_at` | TIMESTAMPTZ | Default `now()` |

Indexes:
- `(conversation_id, created_at asc)`

### 3) `assistant_tool_calls`
Stores tool executions (MCP queries, etc).

| Column | Type | Notes |
| --- | --- | --- |
| `id` | UUID (PK) | Tool call id |
| `message_id` | UUID (FK) | Message that triggered the tool call |
| `tool_name` | TEXT | e.g. `mcp_schema`, `mcp_query` |
| `input` | JSONB | Tool input payload |
| `output` | JSONB | Tool output payload |
| `created_at` | TIMESTAMPTZ | Default `now()` |

Indexes:
- `(message_id)`

## SQL DDL (PostgreSQL)

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE assistant_conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    user_role TEXT NOT NULL,
    title TEXT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_message_at TIMESTAMPTZ NULL
);

CREATE INDEX idx_assistant_conversations_user_updated
    ON assistant_conversations (user_id, updated_at DESC);

CREATE INDEX idx_assistant_conversations_user_status
    ON assistant_conversations (user_id, status);

CREATE TABLE assistant_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES assistant_conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_assistant_messages_conversation_created
    ON assistant_messages (conversation_id, created_at ASC);

CREATE TABLE assistant_tool_calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id UUID NOT NULL REFERENCES assistant_messages(id) ON DELETE CASCADE,
    tool_name TEXT NOT NULL,
    input JSONB NULL,
    output JSONB NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_assistant_tool_calls_message
    ON assistant_tool_calls (message_id);
```


