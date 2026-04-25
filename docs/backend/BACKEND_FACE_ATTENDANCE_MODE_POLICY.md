# Face Attendance Mode Policy

<!--nav-->
[← Email Guide](BACKEND_EMAIL_LOCAL_TESTING_GUIDE.md) | [🏠 Home](/README.md) | [Face Engine Migration →](BACKEND_FACE_ENGINE_MIGRATION_GUIDE.md)

---
<!--/nav-->

## Purpose

Define and document the expected behavior for event face attendance by mode:

- student self-scan (account-bound)
- Gather / kiosk scan (multi-person)

This prevents cross-account attendance recording while preserving fast group scanning flows.

## Effective Behavior

### 1) Student self-scan endpoint (account-bound)

Endpoint: `POST /api/face/face-scan-with-recognition`

Rules:

- only signed-in student accounts can use this endpoint
- signed-in student must be inside the event scope
- face matching is done against the signed-in student's own stored embedding
- if face does not match the signed-in student, the request is rejected and no attendance is created
- non-student operator accounts (including governance/admin-style accounts) are rejected from this endpoint

Expected error messages:

- `Student self-scan access is required for this endpoint. Use Gather public attendance endpoints for multi-person scans.`
- `The signed-in student is outside this event scope.`
- `The live face does not match the currently signed-in student account.`

### 2) Gather / kiosk endpoint (multi-person)

Endpoint: `POST /public-attendance/events/{event_id}/multi-face-scan`

Rules:

- designed for multi-face scans in one capture
- not account-locked to the signed-in dashboard user
- returns per-face outcomes plus aggregate result counts

This is the correct mode for "scan many people, record many people."

## Frontend Mapping

### Student event self-scan

- uses `POST /api/face/face-scan-with-recognition`
- behavior is strictly self-only / account-bound

### Gather attendance view

- now submits scans through `submitPublicAttendanceScan(...)`
- calls `POST /public-attendance/events/{event_id}/multi-face-scan`
- uses event window stage to determine check-in/check-out availability
- displays aggregate scan summary (detected vs recorded)

## Security Intent

The same logged-in account must not be able to record another student's attendance in self-scan mode.  
Gather mode is intentionally the opposite: it is allowed to process many students in one scan.

## Regression Tests Added

File: `backend/app/tests/test_routes_face.py`

- `test_face_scan_with_recognition_rejects_student_outside_event_scope`
- `test_face_scan_with_recognition_rejects_non_student_operator_accounts`
- `test_face_scan_with_recognition_never_records_other_student_for_self_scan`

## Notes

- This policy does not disable Gather behavior.
- Governance/admin users should use Gather/public attendance flows for multi-person scanning, not the student self-scan endpoint.
- `PRIVILEGED_FACE_VERIFICATION_ENABLED` is related to privileged verification flows and does not replace this mode separation policy.
