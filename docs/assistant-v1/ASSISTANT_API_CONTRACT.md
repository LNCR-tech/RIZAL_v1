[<- Back to docs index](../../README.md)

# Assistant API JSON Contract

This document shows the JSON payloads exchanged between the client and the `assistant.py` API.

## Authentication

Send JWT in the header, not in the JSON body:

```http
Authorization: Bearer <jwt>
```

Recommended JWT claims for capability-aware access:

```json
{
  "user_id": "12345",
  "sub": "user@example.com",
  "roles": ["student", "ssg"],
  "permissions": ["manage_events", "manage_attendance", "view_students"],
  "school_id": 1,
  "school_name": "Aurora University",
  "name": "CJ",
  "timezone": "Asia/Manila"
}
```

Notes:
- The assistant prefers `user_id` as the stable user identifier. If your `sub` claim is an email, include `user_id`.
- `roles` can be stacked.
- Governance feature access is driven by `permissions`.
- `school_id` is used for scope enforcement.
- `timezone` is optional and can provide a tenant or user default when the request body does not send `user_timezone`.
- `admin` tokens can omit `school_id` and `school_name` because they are system-wide.
- `campus_admin` uses base-role access and typically remains school-scoped even if `permissions` is empty.

## Start or Continue Conversation (Streaming)

**Request**

`POST /assistant/stream`

**Request JSON**

```json
{
  "message": "How do I reset my password?",
  "user_name": "CJ",
  "user_school": "Aurora University",
  "user_school_id": 1,
  "user_timezone": "Asia/Manila",
  "conversation_id": "c_9a2f1d3b"
}
```

Notes:
- `conversation_id` is optional; omit it to start a new chat.
- `user_id` and `user_role` are deprecated in the request body.
- The API derives the actual user identity and role stack from the JWT.
- `user_name`, `user_school`, and `user_school_id` are optional overrides.
- `user_timezone` is an optional override; the frontend should usually send the browser timezone.

**Streaming response (SSE)**

The response is `text/event-stream`. Each event includes an `event:` line and a `data:` line containing JSON.

Example `message` event:

```text
event: message
data: {"conversation_id":"c_9a2f1d3b","content":"To reset your password, go to Settings..."}
```

Final `done` event:

```text
event: done
data: {"conversation_id":"c_9a2f1d3b","message_id":"m_7812","finish_reason":"stop"}
```

## Health

**Request**

`GET /health`

**Response JSON**

```json
{
  "status": "ok"
}
```

## List Conversations

**Request**

`GET /conversations`

**Response JSON**

```json
[
  {
    "conversation_id": "c_9a2f1d3b",
    "title": "Password reset",
    "last_message": "Then click Change Password.",
    "updated_at": "2026-03-27T04:12:03Z"
  }
]
```

## Get One Conversation

**Request**

`GET /conversations/{conversation_id}`

**Response JSON**

```json
{
  "conversation_id": "c_9a2f1d3b",
  "title": "Password reset",
  "messages": [
    {
      "id": "m_001",
      "role": "user",
      "content": "How do I reset my password?",
      "created_at": "2026-03-27T04:11:00Z"
    },
    {
      "id": "m_002",
      "role": "assistant",
      "content": "Go to Settings and click Change Password.",
      "created_at": "2026-03-27T04:11:05Z"
    }
  ]
}
```

## Delete Conversation

**Request**

`DELETE /conversations/{conversation_id}`

**Response JSON**

```json
{
  "status": "deleted"
}
```

## Rename Conversation

**Request**

`PATCH /conversations/{conversation_id}`

```json
{
  "title": "Attendance for March"
}
```

**Response JSON**

```json
{
  "status": "updated",
  "conversation_id": "c_9a2f1d3b",
  "title": "Attendance for March"
}
```

