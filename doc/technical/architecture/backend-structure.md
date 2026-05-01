# Backend Structure

> **Status:** Maintained
> **Last Updated:** 2026-03-28
>
> **Source of truth:**
> - `Backend/app/`
> - `Backend/app/main.py`
> - `Backend/app/core/`
> - `Backend/app/workers/`

---

## Purpose

This page explains how the FastAPI backend is organized, what each layer owns, and how the backend structure maps to requirements and runtime behavior.

See also:
- [system-architecture.md](./system-architecture.md)
- [api-overview.md](../api/api-overview.md)
- [database-overview.md](../database/database-overview.md)
- [functional-requirements.md](../../requirements/functional-requirements.md)

## Active Module Layout

```text
Backend/app/
|-- main.py
|-- database.py
|-- seeder.py
|-- core/
|-- models/
|-- repositories/
|-- routers/
|-- schemas/
|-- services/
|-- utils/
|-- worker/
`-- workers/
```

## Layer Responsibilities

| Path | Responsibility |
|---|---|
| `Backend/app/main.py` | FastAPI entry point. Registers routers, CORS middleware, and static logo storage. |
| `Backend/app/core/` | Shared runtime setup such as environment settings, DB session factory, dependency injection, security helpers, and event default logic. |
| `Backend/app/routers/` | HTTP endpoints grouped by feature domain. |
| `Backend/app/schemas/` | Request and response contracts used by the API layer. |
| `Backend/app/services/` | Business rules, orchestration, attendance decisions, imports, notifications, and face-processing logic. |
| `Backend/app/repositories/` | Persistence helpers for domains that need repository-style DB operations. |
| `Backend/app/models/` | SQLAlchemy models for the database schema. |
| `Backend/app/workers/` | Active Celery runtime package for background jobs and scheduled tasks. |
| `Backend/app/worker/` | Compatibility wrapper for older Celery import paths. Runtime commands use `app.workers`, not this legacy path. |
| `Backend/app/database.py` | Compatibility import path that forwards to `app.core.database`. |
| `Backend/app/utils/` | Shared helper functions. |

## Router Domains

| Router area | Main responsibility | Requirement link |
|---|---|---|
| `auth.py` | Login, password change, password reset, and session-related auth flows. | FR-01 |
| `users.py`, `school.py`, `departments.py`, `programs.py` | User, school, department, and program management. | FR-02 |
| `admin_import.py` | Student import preview, queueing, retry, and import status tracking. | FR-02.3 |
| `events.py` | Event creation, editing, scheduling, and governance-scoped event flows. | FR-03 |
| `attendance.py` | Manual attendance, records, and attendance reporting endpoints. | FR-04 |
| `face_recognition.py` | Face enrollment, verification, and face-based attendance processing. | FR-04.2, FR-04.4 |
| `public_attendance.py` | Public-facing event check-in flows used by kiosk-style attendance pages. In project docs, this is treated as face-recognition attendance support, not a separate QR-based flow. | FR-04 |
| `governance.py`, `governance_hierarchy.py` | Governance units, permissions, retention, consent, and scoped access rules. | FR-05, FR-07.4 |
| `notifications.py`, `security_center.py`, `audit_logs.py`, `subscription.py`, `health.py` | Operational features such as notifications, security insights, audit trail, subscription data, and health checks. | FR-06, FR-07 |

## Service and Worker Responsibilities

| Module area | Main responsibility |
|---|---|
| `services/face_recognition.py` | Biometric encoding, matching, and face-verification support. |
| `services/event_attendance_service.py`, `services/attendance_status.py`, `services/event_time_status.py` | Attendance state decisions and event attendance rules. |
| `services/event_workflow_status.py` | Automatic event status transitions and finalization logic. |
| `services/student_import_service.py`, `services/import_validation_service.py` | Validation and processing of Excel-based user import jobs. |
| `services/email_service.py`, `services/auth_task_dispatcher.py`, `services/notification_center_service.py` | Email delivery, notification dispatch, and auth-related background task handoff. |
| `services/security_service.py` | Session, password, and security-event logic. |
| `services/governance_hierarchy_service.py` | Governance hierarchy rules and permission-aware operations. |
| `workers/celery_app.py` | Celery app configuration and beat schedule registration. |
| `workers/tasks.py` | Student import processing, login security notifications, and scheduled event workflow sync. |

## Request Lifecycle

```text
Frontend API call
-> FastAPI router in `Backend/app/routers/`
-> auth and scope dependencies in `Backend/app/core/`
-> business logic in `Backend/app/services/`
-> repository/model access through `Backend/app/repositories/`, `Backend/app/models/`, and `Backend/app/core/database.py`
-> schema serialization in `Backend/app/schemas/`
-> HTTP response
```

## Background Job Lifecycle

```text
Route or service schedules work
-> Celery task in `Backend/app/workers/tasks.py`
-> Redis broker
-> Celery worker or beat
-> DB update, email delivery, or event workflow sync
-> frontend reads the updated result through normal API endpoints
```

## Requirement Traceability

| Requirement area | Backend modules that cover it |
|---|---|
| FR-01 Authentication and Session Management | `routers/auth.py`, `schemas/auth.py`, `services/security_service.py`, `core/security.py` |
| FR-02 User Management | `routers/users.py`, `routers/school.py`, `routers/admin_import.py`, `services/student_import_service.py` |
| FR-03 Event Management | `routers/events.py`, `services/event_time_status.py`, `services/event_workflow_status.py` |
| FR-04 Attendance | `routers/attendance.py`, `routers/face_recognition.py`, `routers/public_attendance.py`, `services/event_attendance_service.py` |
| FR-05 Governance Hierarchy | `routers/governance.py`, `routers/governance_hierarchy.py`, `services/governance_hierarchy_service.py` |
| FR-06 Notifications | `routers/notifications.py`, `services/notification_center_service.py`, `services/email_service.py` |
| FR-07 Reporting and Audit | `routers/audit_logs.py`, `routers/subscription.py`, `routers/health.py` |

## Documentation Controls

- Update this page when router, service, or worker module names change.
- Verify worker-path references against `docker-compose.yml` and `docker-compose.prod.yml`. The active runtime path is `app.workers`.
- Keep router summaries aligned with [endpoints.md](../api/endpoints.md) and schema changes aligned with [database-overview.md](../database/database-overview.md).
