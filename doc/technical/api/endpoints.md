# Endpoints Reference

> **Status:** STANDARDIZED
> **Last Updated:** 2026-03-28

---

## Purpose

This document gives a verified integration-level view of the API surface. It focuses on the routes most likely to affect frontend integration, QA, and system behavior.

Verification source:

- Swagger UI: `http://localhost:8000/docs`
- Routers under `Backend/app/routers/`

## Endpoint Documentation Standard

Every endpoint entry should state:

- method and path
- authentication requirement
- request body or parameters
- success response contract
- common error cases
- source router
- related requirement or use case

## Primary Integration Endpoints

| Method | Path | Auth | Request | Success Response | Common Errors | Source Router | Traceability |
|---|---|---|---|---|---|---|---|
| POST | `/login` | None | `LoginRequest` with `email` and `password` | `Token` response | `401`, `422` | `auth.py` | `FR-01`, `UC-01` |
| POST | `/users/` | Admin or Campus Admin | `UserCreate` body | `UserCreateResponse` | `400`, `403`, `500` | `users.py` | `FR-02`, `US-004` |
| GET | `/users/me/` | Bearer JWT | No body | Current user profile object | `401`, `403` | `users.py` | `FR-02` |
| POST | `/events/` | Event-capable staff role | `EventCreate` body | `EventWithRelations` with `201 Created` | `400`, `403`, `404`, `409` | `events.py` | `FR-03`, `US-007` |
| GET | `/events/` | Bearer JWT | Query filters such as `skip`, `limit`, `status` | Event list | `401`, `403`, `422` | `events.py` | `FR-03` |
| POST | `/attendance/manual` | Attendance operator role | `ManualAttendanceRequest` body | Manual attendance result payload | `403`, `404`, `409`, `422` | `attendance.py` | `FR-04`, `UC-03` |
| POST | `/attendance/face-scan` | Attendance operator role | `event_id`, `student_id` parameters | Face-scan attendance result payload | `403`, `404`, `409` | `attendance.py` | `FR-04`, `UC-03` |
| POST | `/attendance/events/{event_id}/mark-excused` | Attendance operator role | `student_ids`, `reason` plus path parameter | Confirmation payload | `403`, `404`, `422` | `attendance.py` | `FR-04` |
| POST | `/face/register` | Student bearer token | `Base64ImageRequest` with `image_base64` | `FaceRegistrationResponse` | `403`, `422` | `face_recognition.py` | `FR-04` |
| POST | `/face/verify` | Bearer JWT | `Base64ImageRequest` with `image_base64` | `FaceVerificationResponse` | `404`, `422`, `500` | `face_recognition.py` | `FR-04` |
| POST | `/face/face-scan-with-recognition` | Student or authorized operator | `FaceAttendanceScanRequest` body | `FaceAttendanceScanResponse` | `403`, `404`, `409`, `422` | `face_recognition.py` | `FR-04`, `UC-04` |
| POST | `/public-attendance/events/nearby` | None | `PublicAttendanceNearbyEventsRequest` with location data | `PublicAttendanceNearbyEventsResponse` | `404`, `422` | `public_attendance.py` | `UC-04` |
| POST | `/public-attendance/events/{event_id}/multi-face-scan` | None | `PublicAttendanceMultiFaceScanRequest` with location and image | `PublicAttendanceMultiFaceScanResponse` | `404`, `409`, `422`, `429` | `public_attendance.py` | `UC-04` |
| GET | `/auth/security/sessions` | Bearer JWT | No body | `UserSessionItem[]` | `401`, `403` | `security_center.py` | `FR-01` |
| POST | `/auth/security/sessions/{session_id}/revoke` | Bearer JWT | Path parameter only | `RevokeSessionResponse` | `401`, `403`, `404` | `security_center.py` | `FR-01` |
| GET | `/health` | None | No body | Health status object | `500` when dependencies fail | `health.py` | `US-021` |

## Module Inventory

| Router File | Prefix | Notes |
|---|---|---|
| `auth.py` | `/token`, `/login`, `/auth/*` | Login, password reset, password change |
| `security_center.py` | `/auth/security/*` | Security and session management |
| `users.py` | `/users/*` | User and profile management |
| `events.py` | `/events/*` | Event lifecycle and event-scoped behavior |
| `attendance.py` | `/attendance/*` | Operator attendance flows and reports |
| `face_recognition.py` | `/face/*` | Face registration, verification, recognition-based attendance |
| `public_attendance.py` | `/public-attendance/*` | Public kiosk face scan flows |
| `admin_import.py` | `/api/admin/*` | Bulk import preview, queue, retry, error download |
| `school.py` | `/api/school/*` | School administration |
| `school_settings.py` | `/school-settings/*` | Branding, template, event defaults |
| `departments.py` | `/departments/*` | Department CRUD |
| `programs.py` | `/programs/*` | Program CRUD |
| `notifications.py` | `/api/notifications/*` | Notification preferences and dispatch |
| `governance.py` | `/api/governance/*` | Data governance and consent APIs |
| `governance_hierarchy.py` | `/api/governance-hierarchy/*` | Unit, member, permission, announcement, and student-note APIs |
| `subscription.py` | `/api/subscription/*` | Subscription settings and reminders |
| `audit_logs.py` | `/api/audit-logs` | Searchable audit logs |
| `health.py` | `/health` | Service health check |

## Review Rule

If a route is added, removed, renamed, re-authenticated, or given a new request or response shape, this file must be updated with the changed contract or module inventory entry.
