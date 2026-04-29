# Backend API Overview

<!--nav-->
[← Backend Docs](README.md) | [🏠 Home](/README.md) | [Runtime Behavior →](runtime-behavior.md)

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

## Paginated List Responses

Paginated list endpoints use the shared `PaginatedResponse` envelope:

```json
{
  "data": [],
  "page": 1,
  "total": 0,
  "total_pages": 0,
  "limit": 100,
  "next": null,
  "prev": null
}
```

Updated endpoints:

- `GET /api/events/`
- `GET /api/events/ongoing`
- `GET /api/users/`
- `GET /api/users/by-role/{role_name}`
- `GET /api/governance/students`

Clients should request `page` and `limit` instead of loading all records and slicing locally.

Event read endpoints compute their response from current database state and do not commit workflow sync side effects during GET requests.

## Auth Password Defaults

- Student accounts created by bulk import or the Campus Admin student form use the lowercased last name as their default password.
- `POST /auth/forgot-password` accepts `{ "email": "student@example.com" }` and auto-resets eligible student accounts to that default password without sending email.
- The default password is accepted case-insensitively only while the account is marked as using the default import password; after the student changes password, normal case-sensitive password checks apply.

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

## Attendance Display Status

Attendance display status is finalized from both stored status and timestamps. Rows with `time_in` but no `time_out` count as `absent`; `present` and `late` require both sign-in and sign-out. Event stats, event attendee filters, and student attendance serializers use the same rule.

