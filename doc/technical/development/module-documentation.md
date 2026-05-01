# Module Documentation

> **Status:** Maintained
> **Last Updated:** 2026-03-28
>
> **Source of truth:**
> - `Backend/app/`
> - `Frontend/src/`
> - `docs/technical/architecture/`

---

## Purpose

This file maps project modules to their responsibilities so developers can quickly understand where logic belongs and how modules connect.

## Backend Module Map

### Entry and Core

| Module | Responsibility |
|---|---|
| `Backend/app/main.py` | FastAPI app startup, middleware setup, router registration, static mount setup. |
| `Backend/app/core/config.py` | Environment variable loading and runtime settings resolution. |
| `Backend/app/core/database.py` | Engine, session factory, and pool diagnostics. |
| `Backend/app/core/dependencies.py` | Shared dependency injection helpers (`get_db`, auth dependencies). |
| `Backend/app/core/security.py` | Token auth helpers, role checks, and auth utility functions. |
| `Backend/app/core/event_defaults.py` | Default attendance window constants and cascade helpers. |

### Router Layer (`Backend/app/routers/`)

| Router | Prefix | Responsibility |
|---|---|---|
| `auth.py` | explicit route paths (no global prefix) | Login, change-password, forgot-password workflow. |
| `users.py` | `/users` | User CRUD, role assignment, profile operations, password resets. |
| `events.py` | `/events` | Event CRUD, status, time windows, and location checks. |
| `attendance.py` | `/attendance` | Attendance records, reports, manual and face-scan flows, absent or excused updates. |
| `face_recognition.py` | `/face` | Face registration, verification, and recognition-based scan endpoints. |
| `public_attendance.py` | `/public-attendance` | Public event face-scan attendance flow. |
| `departments.py` | `/departments` | Department CRUD and scoped academic setup. |
| `programs.py` | `/programs` | Program CRUD and scoped academic setup. |
| `school.py` | `/api/school` | School admin management, school IT account operations, school update endpoints. |
| `school_settings.py` | `/school-settings` | Branding settings, audit logs, import template and import handling. |
| `admin_import.py` | `/api/admin` | Student import preview, queueing, status, and retry/download endpoints. |
| `governance.py` | `/api/governance` | Data governance settings, consent handling, data request flow, retention runs. |
| `governance_hierarchy.py` | `/api/governance` | Governance unit, members, permissions, announcements, and scoped student access endpoints. |
| `security_center.py` | `/auth/security` | Session control, login-history and face-security operations. |
| `notifications.py` | `/api/notifications` | Notification preferences, logs, and dispatch actions. |
| `subscription.py` | `/api/subscription` | Subscription settings and reminder operations. |
| `audit_logs.py` | `/api/audit-logs` | School audit-log querying endpoints. |
| `health.py` | explicit route paths (no global prefix) | Health checks and database pool status endpoint (`/health`). |

### Services and Domain Logic (`Backend/app/services/`)

| Area | Representative modules | Responsibility |
|---|---|---|
| Auth and security | `security_service.py`, `auth_session.py`, `password_change_policy.py` | Session policy, login-security behavior, auth session context. |
| Attendance and events | `event_attendance_service.py`, `attendance_status.py`, `event_time_status.py`, `event_workflow_status.py` | Attendance decisions, event phase logic, event workflow sync. |
| Face and geolocation | `face_recognition.py`, `event_geolocation.py`, `geolocation.py`, `attendance_face_scan.py` | Face verification and geofence-aware attendance behavior. |
| Import and validation | `student_import_service.py`, `import_validation_service.py` | Student import lifecycle and validation rules. |
| Notifications and email | `notification_center_service.py`, `email_service.py`, `auth_task_dispatcher.py` | Delivery orchestration for security and operational notifications. |
| Governance | `governance_hierarchy_service.py` | Governance units, memberships, permission logic, scoped operations. |
| Academic setup | `department_service.py`, `program_service.py` | Department and program domain logic. |

### Data and Worker Modules

| Module area | Responsibility |
|---|---|
| `Backend/app/models/` | SQLAlchemy model definitions and DB relationships. |
| `Backend/app/schemas/` | Request and response schema contracts. |
| `Backend/app/repositories/` | Data access helper abstractions for selected domains. |
| `Backend/app/workers/` | Active Celery app and tasks runtime (`celery_app.py`, `tasks.py`). |
| `Backend/app/worker/` | Compatibility wrappers forwarding to `app.workers`. |

## Frontend Module Map

### Root and Routing (`Frontend/src/`)

| Module | Responsibility |
|---|---|
| `main.tsx` | Application bootstrap and root render. |
| `App.tsx` | Route map, lazy loading, error boundary, and protected-route enforcement. |
| `authFlow.ts` | Auth-flow helper behavior for login and route handling. |

### Feature Layers

| Path | Responsibility |
|---|---|
| `api/` | Backend API client modules (`authApi.ts`, `eventsApi.ts`, `recordsApi.ts`, `publicAttendanceApi.ts`, and others). |
| `components/` | Shared reusable UI and route-shell components (`ProtectedRoute`, navbars, camera/map utilities). |
| `dashboard/` | Role dashboard entry views (`AdminDashboard`, `SchoolITDashboard`, `StudentDashboard`, `SSGDashboard`, `SgDashboard`, `OrgDashboard`). |
| `pages/` | Feature pages for events, attendance, reports, governance, imports, profile, and security flows. |
| `context/` | Shared application context (`UserContext`). |
| `hooks/`, `types/`, `utils/` | Reusable hooks, type definitions, and helper utilities. |
| `css/`, `assets/` | Styling and static assets. |

## Module Dependency Flow

```text
Frontend route/page
-> frontend API module
-> backend router
-> backend service
-> models or repositories
-> database
```

Background flow:

```text
backend router or service
-> Celery task in app/workers
-> Redis broker
-> worker execution
-> DB and notification side effects
```

## Module Documentation Rule

When a module is added, removed, renamed, or significantly repurposed:

1. Update this file.
2. Update related architecture docs:
   - `docs/technical/architecture/backend-structure.md`
   - `docs/technical/architecture/frontend-structure.md`
3. Update API or database docs when routes or schema behavior changed.
4. For backend logic changes, update `Backend/docs/BACKEND_CHANGELOG.md` per `AGENTS.md`.
