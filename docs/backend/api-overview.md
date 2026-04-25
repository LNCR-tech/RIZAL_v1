# Backend API Overview

<!--nav-->
[← Backend Docs](README.md) | [🏠 Home](/README.md) | [Runtime Behavior →](runtime-behavior.md)

---
<!--/nav-->

## Base Paths

- Public root: `/` (lists major endpoints)
- Private API prefix: `/api`
- OpenAPI docs: `/docs`

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

