# Backend Overview Guide

> **Status:** ACTIVE
> **Last Updated:** 2026-04-27

## Purpose

This document gives a fast but current orientation to the Aura backend as of the latest fetched `origin/integrate/pilot-merge` state.

Use it when you need to understand:

- what the backend owns
- where major behavior lives
- which recent backend changes matter most
- which supporting docs to open next

## What The Backend Owns

The backend is the source of truth for:

- authentication, password-change enforcement, session persistence, and privileged face MFA
- school-scoped users, student profiles, departments, programs, and school settings
- events, attendance, quick-attendance flows, and public face-scan attendance
- governance hierarchy, SG and SSG access, sanctions, and clearance workflows
- notifications, email transport, audit logging, and health diagnostics
- bulk student import, import preview, and background task execution
- user-level app preference persistence used by the frontend across devices

## Backend Stack

| Area | Technology |
|---|---|
| API framework | FastAPI |
| ORM | SQLAlchemy |
| Schema validation | Pydantic |
| Database | PostgreSQL |
| Migrations | Alembic |
| Background jobs | Celery |
| Queue / broker | Redis |
| Face and liveness runtime | InsightFace, ONNX Runtime |
| Container runtime | Docker Compose |

## High-Level Request Flow

1. The client hits a route under `Backend/app/routers/` or another registered router package.
2. The route resolves auth context, request payloads, and dependencies.
3. Domain logic runs inside `Backend/app/services/`.
4. Models in `Backend/app/models/` persist business state through SQLAlchemy.
5. Import-specific helpers may delegate to `Backend/app/repositories/`.
6. Async work such as imports, email, and event status sync runs through Celery workers.
7. The backend returns normalized response data for the frontend or assistant.

## Canonical Backend Structure

```text
Backend/app/
|-- main.py
|-- core/
|-- models/
|-- repositories/
|-- routers/
|-- schemas/
|-- services/
|-- utils/
|-- workers/
`-- tests/
```

## Main Layers

| Layer | Responsibility | Main examples |
|---|---|---|
| `main.py` | app boot, router registration, CORS, middleware | `Backend/app/main.py` |
| `core/` | config, DB engine, security helpers, shared dependencies | `config.py`, `database.py`, `dependencies.py`, `security.py` |
| `routers/` | HTTP endpoints and route-level access control | `auth.py`, `users.py`, `events.py`, `attendance.py`, `sanctions.py` |
| `services/` | business rules and reusable workflows | `auth_session.py`, `attendance_face_scan.py`, `user_preference_service.py` |
| `models/` | SQLAlchemy entities and relationships | `user.py`, `event.py`, `attendance.py`, `sanctions.py` |
| `schemas/` | request and response contracts | auth, event, sanctions, import, user schemas |
| `repositories/` | focused persistence helpers | `import_repository.py` |
| `workers/` | async tasks and scheduled jobs | `celery_app.py`, `tasks.py` |
| `tests/` | automated verification | `test_api.py`, `test_public_attendance.py`, `test_governance_hierarchy_api.py` |

## Main Backend Domains

### 1. Authentication, Sessions, and Security

Main files:

- `Backend/app/routers/auth.py`
- `Backend/app/routers/security_center.py`
- `Backend/app/services/auth_session.py`
- `Backend/app/services/security_service.py`
- `Backend/app/services/user_preference_service.py`

This domain now covers:

- password login
- forced password change flow
- `remember_me` session duration support
- privileged face MFA for `admin` and `campus_admin`
- face-pending tokens that upgrade into full sessions only after verification
- account-level UI preferences stored in `user_app_preferences`

See also:

- `user-preferences-and-auth-session.md`

### 2. Users, Schools, Departments, and Programs

Main files:

- `Backend/app/routers/users.py`
- `Backend/app/routers/school.py`
- `Backend/app/routers/departments.py`
- `Backend/app/routers/programs.py`
- `Backend/app/routers/school_settings.py`

This domain manages:

- user CRUD
- student profile lifecycle
- school settings and branding
- department and program hierarchy
- school-scoped and platform-scoped access boundaries

### 3. Events, Attendance, and Face Scanning

Main files:

- `Backend/app/routers/events.py`
- `Backend/app/routers/attendance.py`
- `Backend/app/routers/public_attendance.py`
- `Backend/app/services/event_time_status.py`
- `Backend/app/services/event_workflow_status.py`
- `Backend/app/services/attendance_face_scan.py`

This domain manages:

- event CRUD and status transitions
- sign-in and sign-out timing windows
- quick attendance and public attendance
- InsightFace-based recognition
- liveness, geolocation, and scan timeout handling

### 4. Governance and Sanctions

Main files:

- `Backend/app/routers/governance.py`
- `Backend/app/routers/governance_hierarchy.py`
- `Backend/app/routers/sanctions.py`
- `Backend/app/services/governance_hierarchy_service.py`

This domain manages:

- SSG, SG, and ORG hierarchy
- governance membership and permissions
- sanctions dashboard access
- sanction delegation, approval, and student sanction detail flows
- platform-admin fallback access when school scope is incomplete

### 5. Import, Notifications, Audit, and Health

Main files:

- `Backend/app/routers/admin_import.py`
- `Backend/app/routers/notifications.py`
- `Backend/app/routers/audit_logs.py`
- `Backend/app/routers/health.py`
- `Backend/app/services/student_import_service.py`

This domain manages:

- preview-first bulk import
- onboarding and notification delivery
- audit visibility
- health and runtime diagnostics
- Gmail API transport by default plus optional Mailpit local SMTP testing

See also:

- `email-local-testing.md`
- `migration-guide-import-email.md`

## Main Route Groups

The backend currently exposes a mix of `/api/*` and legacy direct prefixes. The frontend compensates for that inconsistency in its API client.

| Route area | Purpose |
|---|---|
| `/token`, `/login`, `/auth/*` | authentication, password change, security flows |
| `/api/users/*`, `/users/*` | current-user, user CRUD, student profiles, user preferences |
| `/api/events/*`, `/events/*` | event CRUD, detail, time status, location verification |
| `/api/attendance/*`, `/attendance/*` | attendance records, reports, summary, face timeout |
| `/api/governance/*` | governance access, units, setup, dashboards |
| `/api/sanctions/*` | sanctions dashboards, delegation, config, detail, export |
| `/api/face/*`, `/face/*` | face registration and scan attendance |
| `/api/auth/security/*`, `/auth/security/*` | face status, face reference, face verify |
| `/api/admin/*` | import preview, import execution, import status, template download |
| `/health` | health diagnostics |

## Important Data Models

Core entities visible across current backend behavior:

- `User`, `Role`, `UserRole`, `StudentProfile`
- `UserSession`, `LoginHistory`, `UserSecuritySetting`
- `UserAppPreference`
- `School`, `SchoolSetting`, `SchoolAuditLog`
- `Department`, `Program`
- `Event`, `Attendance`
- `GovernanceUnit`, `GovernanceMember`, `GovernancePermission`
- sanction-related event and student records
- `BulkImportJob`, `BulkImportError`, `EmailDeliveryLog`

## Background Jobs

Important worker responsibilities:

- student import processing
- scheduled event status synchronization
- onboarding email dispatch
- login and security notification dispatch

Workers matter because:

- imports are long-running
- email should not block request latency
- event status sync needs recurring execution

## Configuration Areas

The active config source is `Backend/app/core/config.py`.

Important categories:

- database and connection pool settings
- JWT and session expiration settings
- face thresholds for single, group, and MFA verification
- liveness and anti-spoof controls
- geolocation limits
- import size and rate limits
- Celery broker and result backend
- runtime startup orchestration flags for web, migrations, seeding, worker, and beat
- SMTP and Gmail API transport settings
- login URL, CORS, logo storage, and runtime file paths

## Current Backend Change Highlights

Recent backend changes reflected in this combined docs tree:

- `2026-04-27`: normalized-schema rollout was stabilized with non-destructive/idempotent migration fixes, merged Alembic heads, and hardened path resolution in `backend/alembic/env.py`.
- `2026-04-27`: backend startup and auth regressions after schema alignment were fixed across core routers/services/models.
- `2026-04-27`: `assistant-v2/` was renamed to `assistant/` and deployment references were synchronized in compose and workflow paths.
- `2026-04-26`: pgvector-backed face embedding support was added for attendance matching, including migration and runtime integration paths.
- `2026-04-26`: CI/deployment paths were hardened with explicit migration-first workflow coverage and stronger deploy branch gates.
- `2026-04-25`: backend face attendance/verification error handling was normalized and compose/runtime reliability was improved for health checks and persistent storage mounts.

## Useful Reading Order

If you need the fastest orientation:

1. `backend/app/main.py`
2. `backend/app/routers/`
3. `backend/app/services/`
4. `backend/app/models/`
5. `backend/app/workers/tasks.py`
6. `backend/app/tests/`

Feature-first debug entry points:

- auth and session: `auth.py`, `auth_session.py`, `security_center.py`
- user preferences: `users.py`, `user_preference_service.py`
- event timing: `events.py`, `event_time_status.py`, `event_workflow_status.py`
- attendance and face scan: `attendance.py`, `public_attendance.py`, `attendance_face_scan.py`
- governance and sanctions: `governance.py`, `governance_hierarchy.py`, `sanctions.py`
- import and email: `admin_import.py`, `student_import_service.py`, email service modules

## Supporting Backend Docs

Detailed backend references already exist in `Backend/docs/`, and the combined docs tree now mirrors the most important recent ones here:

- `user-preferences-and-auth-session.md`
- `email-local-testing.md`
- `migration-guide-import-email.md`

## Summary

The backend remains the strongest and most structured layer of the repository.

If you are trying to understand a change quickly, start by asking:

`Is this auth/session, user/school, events/attendance, governance/sanctions, or import/notification behavior?`

That question will usually point you to the correct router, service, model, and test file immediately.
