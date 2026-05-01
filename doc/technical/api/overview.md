# API Overview

> **Status:** STANDARDIZED
> **Last Updated:** 2026-04-18

---

## Purpose

This folder documents how the frontend and backend interact through HTTP endpoints, authentication, and data exchange.

The main documentation risks in this area are:

- outdated or inaccurate endpoint notes
- missing request or response details
- unclear authentication flow
- inconsistent payload expectations
- weak error-handling guidance
- missing links to requirements and system features

This folder addresses those risks by using one documentation standard for endpoint purpose, authentication, request shape, response shape, error behavior, and traceability.

## Verification Sources

This API folder is the curated integration guide. Verification should always be done against:

1. Runtime contract: `http://localhost:8000/docs` and `http://localhost:8000/redoc`
2. Source routers: `Backend/app/routers/*.py`
3. Source schemas: `Backend/app/schemas/*.py`

If the runtime contract and these docs conflict, the runtime contract and router code win until the docs are corrected.

## Base Information

| Item | Value |
|---|---|
| Base URL | `http://localhost:8000` |
| Swagger UI | `http://localhost:8000/docs` |
| ReDoc | `http://localhost:8000/redoc` |
| Default Auth Type | Bearer Token (JWT) |
| Primary Content Type | `application/json` |
| Secondary Content Type | `multipart/form-data` for file upload endpoints |

## Required Endpoint Documentation Standard

Every documented endpoint in this folder should include:

| Field | Requirement |
|---|---|
| Method and path | Exact HTTP method and route |
| Purpose | What the endpoint does in system terms |
| Authentication | None, Bearer JWT, or role-scoped |
| Request | Body, query, path, and required headers |
| Success response | Main response shape and status code |
| Errors | Common failure codes and meanings |
| Source router | Router file that owns the endpoint |
| Traceability | Related requirement or feature area |

## API Domains

| Domain | Prefix | Source Router | Primary Use | Traceability |
|---|---|---|---|---|
| Authentication | `/token`, `/login`, `/auth/*` | `Backend/app/routers/auth.py` | Login, password flows | [functional-requirements.md](../../requirements/functional-requirements.md) `FR-01` |
| Security Center | `/auth/security/*` | `Backend/app/routers/security_center.py` | Session control, login history, face security checks | [functional-requirements.md](../../requirements/functional-requirements.md) `FR-01` |
| Users | `/users/*` | `Backend/app/routers/users.py` | User CRUD, profile management, role assignment | [functional-requirements.md](../../requirements/functional-requirements.md) `FR-02` |
| Events | `/events/*` | `Backend/app/routers/events.py` | Event creation, lifecycle, attendance timing, reporting | [functional-requirements.md](../../requirements/functional-requirements.md) `FR-03` |
| Attendance | `/attendance/*` | `Backend/app/routers/attendance.py` | Manual attendance, face-scan attendance, reports, staff actions | [functional-requirements.md](../../requirements/functional-requirements.md) `FR-04` |
| Face Recognition | `/face/*` | `Backend/app/routers/face_recognition.py` | Face registration, verification, recognition-based attendance | [functional-requirements.md](../../requirements/functional-requirements.md) `FR-04` |
| Public Face Attendance Kiosk | `/public-attendance/*` | `Backend/app/routers/public_attendance.py` | Nearby-event lookup and multi-face public kiosk scans | [use-cases.md](../../requirements/use-cases.md) `UC-04` |
| School Management | `/api/school/*`, `/school-settings/*` | `school.py`, `school_settings.py` | School administration and defaults | [functional-requirements.md](../../requirements/functional-requirements.md) `FR-02`, `FR-03` |
| Import Center | `/api/admin/*` | `Backend/app/routers/admin_import.py` | Bulk student import preview, queue, retry, status | [functional-requirements.md](../../requirements/functional-requirements.md) `FR-02` |
| Notifications | `/api/notifications/*` | `Backend/app/routers/notifications.py` | Preferences, notification dispatch, logs | [functional-requirements.md](../../requirements/functional-requirements.md) `FR-06` |
| Governance | `/api/governance/*`, `/api/governance-hierarchy/*` | `governance.py`, `governance_hierarchy.py` | Consents, retention, hierarchy, permissions, notes | [functional-requirements.md](../../requirements/functional-requirements.md) `FR-05`, `FR-07` |
| Departments and Programs | `/departments/*`, `/programs/*` | `departments.py`, `programs.py` | Academic structure CRUD | [functional-requirements.md](../../requirements/functional-requirements.md) `FR-02`, `FR-03` |
| Audit Logs | `/api/audit-logs` | `Backend/app/routers/audit_logs.py` | School-scoped audit trail | [functional-requirements.md](../../requirements/functional-requirements.md) `FR-07` |
| Subscription | `/api/subscription/*` | `Backend/app/routers/subscription.py` | Plan limits and usage metrics | [functional-requirements.md](../../requirements/functional-requirements.md) `FR-07` |
| Health | `/health` | `Backend/app/routers/health.py` | API and DB reachability checks | [user-stories.md](../../requirements/user-stories.md) `US-021` |

## Authentication Summary

- Frontend login should use `POST /login`
- Swagger UI and OAuth2 flow use `POST /token`
- Protected endpoints require `Authorization: Bearer <token>`
- Role checks are enforced server-side before handler execution

See [authentication.md](./authentication.md) for the full flow.

## Shared Error Contract

For MVP frontend behavior, use the shared runtime error contract in:

- [error-contract.md](./error-contract.md)

That page defines the expected HTTP status plus `error_code` pairs the frontend should use for routing, validation, retries, and error messaging.

## Versioning and Change Control

- The API is currently unversioned. There is no `/v1/` prefix yet.
- Changes affecting routes, auth, schemas, or response behavior must update this folder.
- Backend delivery history should be logged in [backend-changelog.md](../../changelog/backend-changelog.md).
- Branch-level raw updates should be logged in [branch-updates.md](../../changelog/branch-updates.md).

## Traceability Rule

When documenting or reviewing an endpoint, always be able to answer:

1. Which router owns it?
2. Which request and response schema define it?
3. Which requirement or use case depends on it?
4. Which changelog entry records the behavior change?
