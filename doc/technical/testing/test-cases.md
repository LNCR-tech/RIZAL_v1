# Test Cases — VALID8 Attendance Recognition System

> **Status:** ACTIVE — IN PROGRESS
> **Last Updated:** 2026-04-08
> **Author Role:** QA Engineer / Documentation Specialist
>
> See also: [test-plan.md](./test-plan.md) · [bug-reports.md](./bug-reports.md)

---

## Purpose

This file defines requirement-linked test cases for functional validation and regression checks.
Each test case is explicitly tied to a Functional Requirement ID so every behavior can be traced
from requirement → test → result → bug (if any).

---

## Test Case Rules

- Every test case **must** map to at least one requirement ID from `functional-requirements.md`.
- Every failed execution **must** reference a bug ID in [bug-reports.md](./bug-reports.md).
- Keep expected results explicit: status code, payload shape, and business rule outcome.
- Update `Last Run` date after every test execution.
- Use existing test file names as evidence sources wherever available.

---

## Test Case Template

```markdown
## TC-<AREA>-<NUMBER>: <Short Title>

| Field | Value |
|---|---|
| Requirement ID(s) | FR-XX.X |
| Endpoint / Area | e.g. POST /api/login |
| Test Type | Automated / Manual / Integration |
| Preconditions | Required setup and role |
| Steps | 1) ... 2) ... 3) ... |
| Expected Result | Exact response and behavior |
| Evidence Source | Test file or run log |
| Last Run | YYYY-MM-DD |
| Status | Passed / Failed / Blocked / In Progress |
| Linked Bug ID | BUG-XXX or N/A |
```

---

## FR-01: Authentication and Session Management

---

## TC-FR01-01: Login with valid credentials

| Field | Value |
|---|---|
| Requirement ID(s) | FR-01.1 |
| Endpoint / Area | `POST /login` |
| Test Type | Automated |
| Preconditions | Active user with valid password and role |
| Steps | 1) Submit email and password 2) Inspect response body |
| Expected Result | `200` and token payload includes identity and role context |
| Evidence Source | `Backend/app/tests/test_api.py` |
| Last Run | 2026-04-08 |
| Status | Passed |
| Linked Bug ID | N/A |

---

## TC-FR01-02: Login rejected for inactive school

| Field | Value |
|---|---|
| Requirement ID(s) | FR-01.6 |
| Endpoint / Area | `POST /login` |
| Test Type | Automated |
| Preconditions | User belongs to an inactive school |
| Steps | 1) Submit valid credentials for a user in an inactive school |
| Expected Result | Access is blocked with guardrail response — no session token granted |
| Evidence Source | `Backend/app/tests/test_api.py`, `Backend/app/tests/test_auth_session_login_guard.py` |
| Last Run | 2026-04-08 |
| Status | Passed |
| Linked Bug ID | N/A |

---

## TC-FR01-03: Force password change on first login

| Field | Value |
|---|---|
| Requirement ID(s) | FR-01.3 |
| Endpoint / Area | Frontend route guard → `/change-password` |
| Test Type | Manual |
| Preconditions | User account with `must_change_password = true` |
| Steps | 1) Log in with seeded demo student account 2) Observe redirect 3) Change password 4) Confirm dashboard access |
| Expected Result | User is redirected to `/change-password` and cannot access any protected route until password is changed |
| Evidence Source | `Frontend/src/router/index.js` navigation guard |
| Last Run | 2026-04-08 |
| Status | Passed |
| Linked Bug ID | N/A |

---

## TC-FR01-04: Login with wrong password (negative)

| Field | Value |
|---|---|
| Requirement ID(s) | FR-01.1 |
| Endpoint / Area | `POST /login` |
| Test Type | Automated |
| Preconditions | Valid user email, incorrect password |
| Steps | 1) Submit valid email with wrong password |
| Expected Result | `401` or `403` — no session token issued |
| Evidence Source | `Backend/app/tests/test_api.py` |
| Last Run | 2026-04-08 |
| Status | Passed |
| Linked Bug ID | N/A |

---

## TC-FR01-05: Face-enrollment gate prevents dashboard access

| Field | Value |
|---|---|
| Requirement ID(s) | FR-01.3, FR-04.2 |
| Endpoint / Area | Frontend route guard → `/face-registration` |
| Test Type | Manual |
| Preconditions | Authenticated student with no registered face profile |
| Steps | 1) Log in 2) Attempt to navigate to `/dashboard` |
| Expected Result | Router redirects user to `/face-registration` before allowing dashboard access |
| Evidence Source | `Frontend/src/router/index.js` (`sessionNeedsFaceRegistration`) |
| Last Run | 2026-04-08 |
| Status | Passed |
| Linked Bug ID | N/A |

---

## FR-02: User Management and Import

---

## TC-FR02-01: Import preview reports conflicts

| Field | Value |
|---|---|
| Requirement ID(s) | FR-02.3 |
| Endpoint / Area | `POST /api/admin/import-students/preview` |
| Test Type | Automated integration |
| Preconditions | Campus Admin token, Excel file with duplicate or conflicting records |
| Steps | 1) Upload Excel file 2) Read preview summary and error report |
| Expected Result | Preview returns conflict details; invalid rows are explicitly flagged |
| Evidence Source | `Backend/app/tests/test_admin_import_preview_flow.py` |
| Last Run | 2026-04-08 |
| Status | Passed |
| Linked Bug ID | N/A |

---

## TC-FR02-02: Import requires approved preview token

| Field | Value |
|---|---|
| Requirement ID(s) | FR-02.3 |
| Endpoint / Area | `POST /api/admin/import-students` |
| Test Type | Automated integration |
| Preconditions | Import request submitted without a valid preview token |
| Steps | 1) Call the import endpoint directly without completing preview |
| Expected Result | Request is rejected — import cannot proceed without an approved preview |
| Evidence Source | `Backend/app/tests/test_admin_import_preview_flow.py` |
| Last Run | 2026-04-08 |
| Status | Passed |
| Linked Bug ID | N/A |

---

## TC-FR02-03: Onboarding email sent after import

| Field | Value |
|---|---|
| Requirement ID(s) | FR-02.3, FR-06.1 |
| Endpoint / Area | `POST /api/admin/import-students` → Celery task → Gmail API |
| Test Type | Automated + Manual |
| Preconditions | Import batch with valid rows; Gmail API configured |
| Steps | 1) Complete preview and approve import 2) Check `email_delivery_logs` table for imported users |
| Expected Result | Logs record `status=sent` with credentials-style email content (email, temp password, login URL) |
| Evidence Source | `Backend/app/tests/test_student_import_email_delivery.py` |
| Last Run | 2026-04-08 |
| Status | Passed |
| Linked Bug ID | N/A |

---

## TC-FR02-04: Import with empty Excel file (edge case)

| Field | Value |
|---|---|
| Requirement ID(s) | FR-02.3 |
| Endpoint / Area | `POST /api/admin/import-students/preview` |
| Test Type | Manual |
| Preconditions | Campus Admin token, empty Excel file |
| Steps | 1) Upload an empty Excel file 2) Observe API response |
| Expected Result | Preview returns a clear error — no rows were found or processed |
| Evidence Source | Manual exploratory — no automated test yet |
| Last Run | NOT RUN |
| Status | In Progress |
| Linked Bug ID | N/A |

---

## FR-03: Event Management

---

## TC-FR03-01: Event creation applies default attendance windows

| Field | Value |
|---|---|
| Requirement ID(s) | FR-03.1, FR-03.3 |
| Endpoint / Area | `POST /api/events/` |
| Test Type | Automated |
| Preconditions | Authorized event creator with valid schedule payload |
| Steps | 1) Create event without overriding window fields 2) Check stored values |
| Expected Result | Event is created with configured default attendance window settings |
| Evidence Source | `Backend/app/tests/test_api.py` |
| Last Run | 2026-04-08 |
| Status | Passed |
| Linked Bug ID | N/A |

---

## TC-FR03-02: Event workflow status auto-syncs

| Field | Value |
|---|---|
| Requirement ID(s) | FR-03.5 |
| Endpoint / Area | Background scheduler → event status fields |
| Test Type | Automated |
| Preconditions | Scheduled event with known start and end times |
| Steps | 1) Create event with a past start time 2) Check returned event status |
| Expected Result | Status transitions correctly (upcoming → ongoing → completed) |
| Evidence Source | `Backend/app/tests/test_event_workflow_status.py`, `test_event_time_status.py` |
| Last Run | 2026-04-08 |
| Status | Passed |
| Linked Bug ID | N/A |

---

## TC-FR03-03: Sign-out delay blocks sign-out before window opens (edge case)

| Field | Value |
|---|---|
| Requirement ID(s) | FR-03.3, FR-04.4 |
| Endpoint / Area | `POST /public-attendance/events/{event_id}/multi-face-scan` |
| Test Type | Automated |
| Preconditions | Event with `sign_out_open_delay_minutes > 0` configured |
| Steps | 1) Sign in during check-in window 2) Attempt sign-out before delay expiry |
| Expected Result | Sign-out is rejected with `sign_out_pending` state |
| Evidence Source | `Backend/app/tests/test_event_time_status.py` |
| Last Run | 2026-04-08 |
| Status | Passed |
| Linked Bug ID | N/A |

---

## FR-04: Attendance

---

## TC-FR04-01: Manual attendance blocks duplicate record

| Field | Value |
|---|---|
| Requirement ID(s) | FR-04.1 |
| Endpoint / Area | `POST /api/attendance/manual` |
| Test Type | Automated integration |
| Preconditions | Existing attendance row for the same event and student |
| Steps | 1) Submit duplicate manual attendance record |
| Expected Result | Duplicate submission is rejected; existing record is preserved |
| Evidence Source | `Backend/app/tests/test_governance_hierarchy_api.py` |
| Last Run | 2026-04-08 |
| Status | Passed |
| Linked Bug ID | N/A |

---

## TC-FR04-02: Public face scan follows sign-in and sign-out phases

| Field | Value |
|---|---|
| Requirement ID(s) | FR-04.2, FR-04.4 |
| Endpoint / Area | `POST /public-attendance/events/{event_id}/multi-face-scan` |
| Test Type | Automated integration |
| Preconditions | Event with valid phase windows and face-recognition setup |
| Steps | 1) Scan during sign-in window 2) Scan again during sign-out window |
| Expected Result | Outcomes follow event phase rules; attendance status transitions correctly |
| Evidence Source | `Backend/app/tests/test_public_attendance.py` |
| Last Run | 2026-04-08 |
| Status | Passed |
| Linked Bug ID | N/A |

---

## TC-FR04-03: Incomplete attendance shows `display_status = incomplete`

| Field | Value |
|---|---|
| Requirement ID(s) | FR-04.2, FR-04.4 |
| Endpoint / Area | Attendance record response after sign-in |
| Test Type | Automated |
| Preconditions | Student signed in but has not yet signed out |
| Steps | 1) Sign in to event 2) Read attendance record |
| Expected Result | Record returns `display_status = incomplete`; `is_valid_attendance = false` |
| Evidence Source | `Backend/app/tests/test_attendance_status_support.py` |
| Last Run | 2026-04-08 |
| Status | Passed |
| Linked Bug ID | N/A |

---

## TC-FR04-04: Student with null `student_id` can still register face (edge case)

| Field | Value |
|---|---|
| Requirement ID(s) | FR-04.2 |
| Endpoint / Area | `POST /api/face/register` |
| Test Type | Automated |
| Preconditions | Student account whose `student_profile.student_id` is null |
| Steps | 1) Sign in as student with null student ID 2) Call face registration endpoint |
| Expected Result | `200` with `student_id: null` in response — no 500 error |
| Evidence Source | `Backend/app/tests/test_face_recognition_schemas.py` |
| Last Run | 2026-04-08 |
| Status | Passed |
| Linked Bug ID | N/A |

---

## TC-FR04-05: Face scan geofence rejects out-of-range student (edge case)

| Field | Value |
|---|---|
| Requirement ID(s) | FR-04.2 |
| Endpoint / Area | `POST /public-attendance/events/{event_id}/multi-face-scan` |
| Test Type | Automated |
| Preconditions | Event with geofence enabled; student coordinates outside radius |
| Steps | 1) Submit face scan with coordinates outside event geofence |
| Expected Result | Attendance is rejected with geofence violation response |
| Evidence Source | `Backend/app/tests/test_geolocation.py`, `test_event_geolocation_service.py` |
| Last Run | 2026-04-08 |
| Status | Passed |
| Linked Bug ID | N/A |

---

## FR-05: Governance Hierarchy

---

## TC-FR05-01: Governance scope prevents out-of-scope attendance actions

| Field | Value |
|---|---|
| Requirement ID(s) | FR-05.3 |
| Endpoint / Area | `POST /api/attendance/manual?governance_context=SG` |
| Test Type | Automated integration |
| Preconditions | SG actor attempting attendance action outside their department |
| Steps | 1) Submit attendance for an out-of-scope student 2) Verify denial |
| Expected Result | Request is denied; no out-of-scope attendance record is written |
| Evidence Source | `Backend/app/tests/test_governance_hierarchy_api.py` |
| Last Run | 2026-04-08 |
| Status | Passed |
| Linked Bug ID | N/A |

---

## TC-FR05-02: Upcoming events visible to all school students regardless of scope

| Field | Value |
|---|---|
| Requirement ID(s) | FR-05.3, FR-03.2 |
| Endpoint / Area | `GET /api/events/` |
| Test Type | Automated |
| Preconditions | School has upcoming events scoped to specific departments |
| Steps | 1) Log in as student outside the event's department scope 2) Request event list |
| Expected Result | All school-wide upcoming events are visible; in-progress out-of-scope events remain hidden |
| Evidence Source | `Backend/app/tests/test_governance_hierarchy_api.py` (`upcoming_events`) |
| Last Run | 2026-04-08 |
| Status | Passed |
| Linked Bug ID | N/A |

---

## FR-06: Notifications

---

## TC-FR06-01: Email sent after manual user creation

| Field | Value |
|---|---|
| Requirement ID(s) | FR-06.1 |
| Endpoint / Area | `POST /api/users/students/` → Gmail API |
| Test Type | Automated |
| Preconditions | Campus Admin token; Gmail API transport configured |
| Steps | 1) Create a new student account 2) Check that welcome email is queued/sent |
| Expected Result | Email dispatched with temporary credentials and frontend login URL |
| Evidence Source | `Backend/app/tests/test_email_service.py` |
| Last Run | 2026-04-08 |
| Status | Passed |
| Linked Bug ID | N/A |

---

## TC-FR06-02: Celery failure triggers inline email fallback

| Field | Value |
|---|---|
| Requirement ID(s) | FR-06.1 |
| Endpoint / Area | Import → Celery task → inline fallback |
| Test Type | Automated |
| Preconditions | Celery broker unavailable during import |
| Steps | 1) Run import with Celery stopped 2) Inspect `email_delivery_logs` |
| Expected Result | Inline fallback sends email; log records `status=sent` |
| Evidence Source | `Backend/app/tests/test_admin_import_preview_flow.py` (`falls_back_to_in_process_job_when_celery_dispatch_fails`) |
| Last Run | 2026-04-08 |
| Status | Passed |
| Linked Bug ID | N/A |

---

## FR-07: Reporting and Audit

---

## TC-FR07-01: Health endpoint reports service and pool status

| Field | Value |
|---|---|
| Requirement ID(s) | FR-07.2 |
| Endpoint / Area | `GET /health` |
| Test Type | Automated |
| Preconditions | Backend service is running |
| Steps | 1) Call health endpoint 2) Validate response structure |
| Expected Result | `200` with service status and database pool visibility fields |
| Evidence Source | `Backend/app/tests/test_api.py` |
| Last Run | 2026-04-08 |
| Status | Passed |
| Linked Bug ID | N/A |

---

## TC-FR07-02: Student attendance record returns null `student_id` safely (edge case)

| Field | Value |
|---|---|
| Requirement ID(s) | FR-07.1, FR-04.3 |
| Endpoint / Area | `GET /api/attendance/me/records` |
| Test Type | Automated |
| Preconditions | Authenticated student with `student_profile.student_id = null` |
| Steps | 1) Log in as student with null student ID 2) Call attendance records endpoint |
| Expected Result | `200` with `student_id: null` in JSON — no 500 or Pydantic validation error |
| Evidence Source | `Backend/app/tests/test_attendance_schemas.py` |
| Last Run | 2026-04-08 |
| Status | Passed |
| Linked Bug ID | N/A |

---

## Negative / Edge Case Summary

| TC ID | Area | Type | Risk |
|---|---|---|---|
| TC-FR01-04 | Login | Negative | Wrong password must not grant access |
| TC-FR02-04 | Import | Edge Case | Empty file must not crash import preview |
| TC-FR03-03 | Attendance timing | Edge Case | Sign-out delay window must reject early sign-out |
| TC-FR04-04 | Face registration | Edge Case | Null student ID must not break face registration |
| TC-FR04-05 | Geofence | Edge Case | Out-of-range scan must be rejected |
| TC-FR05-02 | Event visibility | Edge Case | Upcoming events must be visible school-wide |
| TC-FR07-02 | Attendance records | Edge Case | Null student ID in response must not cause 500 |

---

## Tests Still Needed (Gap Analysis)

| Gap | Priority | Suggested Test ID |
|---|---|---|
| Empty import file handling | Medium | TC-FR02-04 (created above) |
| Subscription metrics endpoint response validation | Medium | TC-FR07-03 |
| Data governance retention and consent requests | Low | TC-FR07-04 |
| Notification preferences CRUD | Low | TC-FR06-03 |
| Admin workspace multi-section route isolation | Medium | TC-UI-01 |
| Cross-role redirection guard (SG trying student dashboard) | High | TC-UI-02 |
| MFA email delivery fallback | Medium | TC-FR01-06 |