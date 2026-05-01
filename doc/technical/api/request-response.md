# Request and Response Reference

> **Status:** STANDARDIZED
> **Last Updated:** 2026-03-28

---

## Purpose

This document defines the common request and response rules used across the API so frontend, backend, and QA interpret payloads consistently.

## Request Standards

### Common Headers

| Header | Value | Required |
|---|---|---|
| `Authorization` | `Bearer <jwt_token>` | Required for protected endpoints |
| `Content-Type` | `application/json` | Required for JSON POST, PUT, and PATCH |
| `Content-Type` | `multipart/form-data` | Required for file upload endpoints such as face upload registration |

### Common Query Parameters

| Parameter | Type | Meaning |
|---|---|---|
| `skip` | int | Offset for list pagination |
| `limit` | int | Maximum number of items to return |
| `status` | string | Status filter for endpoint-specific states |
| `start_date` | datetime | Lower bound date filter |
| `end_date` | datetime | Upper bound date filter |
| `search` | string | Free-text search filter |

### Datetime Format

All datetimes should be treated as ISO 8601 values.

Examples:

```text
2026-03-28T10:30:00
2026-03-28T10:30:00Z
```

### Field Naming

- JSON fields use `snake_case`
- Path parameters use route placeholders such as `{event_id}`
- Query parameters should be documented explicitly when used

## Response Standards

### Success Response Patterns

There is not a single success envelope for every endpoint. Clients should rely on the documented response model for each route.

Common patterns include:

1. Single object response
2. Array response
3. Result-summary object for write actions
4. Token payload for login flows

### Example: Token Response

```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "email": "admin@school.edu",
  "roles": ["admin"],
  "user_id": 1,
  "school_id": 1,
  "must_change_password": false,
  "session_id": "uuid"
}
```

### Example: Face Registration Response

```json
{
  "message": "Face registered successfully.",
  "student_id": "2024-0001",
  "liveness": {
    "passed": true,
    "score": 0.98
  }
}
```

## Error Standards

The API currently uses `detail` as the main error field, but `detail` is not always the same type.

### Error Pattern 1: Simple String Detail

```json
{
  "detail": "Incorrect email or password"
}
```

### Error Pattern 2: Validation Detail Array

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

### Error Pattern 3: Structured Detail Object

```json
{
  "detail": {
    "code": "public_scan_throttled",
    "message": "The kiosk is already processing a recent scan. Please wait briefly.",
    "retry_after_seconds": 0.75
  }
}
```

Client rule:

- Always inspect `detail`
- Do not assume `detail` is always a string
- Handle string, array, and object forms safely

## Common Status Codes

| Status | Meaning | Common Context |
|---|---|---|
| `200` | Success | Standard read and update success |
| `201` | Created | Resource created successfully |
| `400` | Bad request | Invalid business rule or bad user input |
| `401` | Unauthorized | Invalid credentials or missing valid token |
| `403` | Forbidden | Authenticated but not allowed |
| `404` | Not found | Missing user, event, route target, or disabled feature |
| `409` | Conflict | State conflict such as invalid attendance phase or cancelled event |
| `422` | Validation error | Schema or field validation failed |
| `429` | Too many requests | Public kiosk throttling or rate limiting |
| `500` | Internal server error | Unexpected backend failure |
| `502` | Bad gateway or dependency failure | Downstream email dispatch failure |

## Documentation Consistency Rule

For every endpoint contract added to this folder, document:

1. request body or parameters
2. success response shape
3. common error codes
4. auth requirement
5. related requirement or feature
6. source router or schema

## Traceability Rule

When request or response behavior changes:

- update [endpoints.md](./endpoints.md)
- update [authentication.md](./authentication.md) if auth is affected
- update [backend-changelog.md](../../changelog/backend-changelog.md)
- confirm the affected requirement still matches the API behavior
