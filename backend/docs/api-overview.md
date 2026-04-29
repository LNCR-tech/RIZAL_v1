# Backend API Overview

<!--nav-->
[Previous](../README.md) | [Next](BACKEND_CHANGELOG.md) | [Home](/README.md)

---
<!--/nav-->

## Base Paths

- Public root: `/` (lists major endpoints)
- Private API prefix: `/api`
- OpenAPI docs: `/docs` when `API_DOCS_ENABLED=true`

Routers are registered in `backend/app/main.py`. In practice, what matters to clients is the final path. Some routers include `/api` in their own router prefix, even if they are included without the `/api` helper.

## Router Map (major entrypoints)

Private API (`/api/...`):

- Users: `/api/users`
- Events: `/api/events`
- Programs: `/api/programs`
- Departments: `/api/departments`
- Attendance: `/api/attendance`
- Reports: `/api/reports` (see [Reports Module Guide](./BACKEND_REPORTS_MODULE_GUIDE.md))
- Admin import: `/api/admin/...`
- School: `/api/school/...`
- Audit logs: `/api/audit-logs/...`
- Notifications: `/api/notifications/...`
- Subscription: `/api/subscription/...`
- Governance: `/api/governance/...`
- Governance hierarchy: `/api/governance/units/...`
- Security center: `/api/auth/security`
- Face recognition: `/api/face`
- Sanctions: `/api/sanctions` (see [Sanctions Management Guide](./BACKEND_SANCTIONS_MANAGEMENT_GUIDE.md))

Non-`/api` routes:

- Auth: `/auth/...` (login/session endpoints)
- School settings: `/school-settings/...`
- Public attendance: `/public-attendance/...`
- Health: `/health/...`

If you are unsure about the exact request/response schema, use the live OpenAPI docs at `/docs`.

## Anti-Abuse Responses

Routes protected by the shared limiter return `429 Too Many Requests` with this detail shape:

```json
{
  "detail": {
    "code": "rate_limit_exceeded",
    "message": "Too many requests. Please wait before trying again.",
    "limit": 10,
    "window_seconds": 300,
    "retry_after_seconds": 60
  }
}
```

The response also includes a `Retry-After` header when the backend can calculate the remaining window.

## Hardened Request Shapes

The attendance write routes now support explicit JSON request models while keeping existing query-style clients compatible for face-scan timeout and event status updates:

- `POST /api/attendance/face-scan`: `{ "event_id": 1, "student_id": "..." }`
- `POST /api/attendance/face-scan-timeout`: `{ "event_id": 1, "student_id": "..." }`
- `POST /api/attendance/mark-absent-no-timeout`: `{ "event_id": 1 }`
- `PATCH /api/events/{event_id}/status`: `{ "status": "ongoing" }`

Face image payloads are bounded. Base64 image bodies are limited by schema validation, and multipart face uploads must be non-empty image content under `FACE_IMAGE_MAX_SIZE_MB`.


