# Backend Attendance Status Guide

## Purpose

This guide documents how attendance status is now recorded in the backend with explicit sign-in and sign-out audit fields.

The backend now separates:

- `check_in_status`: what the sign-in window decided
- `check_out_status`: whether sign-out completed inside an allowed sign-out window
- `status`: the final attendance status used by reports and dashboards

## Valid Final Statuses

- `present`
- `late`
- `absent`
- `excused`

## New Attendance Audit Fields

Stored on `attendances`:

- `check_in_status: "present" | "late" | "absent" | null`
- `check_out_status: "present" | "absent" | null`

Exposed from:

- `Backend/app/models/attendance.py`
- `Backend/app/schemas/attendance.py`

Added by migration:

- `Backend/alembic/versions/e4b7c1d9f6a2_add_event_attendance_window_controls.py`

Historical rows may still have `null` audit fields.

## Check-In Status Rules

Check-in status is derived from the event timing window:

- before start, inside the early window -> `present`
- from exact start through the late threshold cutoff -> `late`
- after the late threshold cutoff while check-in is still open -> `absent`

Important rule:

- exact start time is treated as `late`

The reusable helpers live in:

- `Backend/app/services/event_time_status.py`
- `Backend/app/services/attendance_status.py`

## Sign-Out Rules

Sign-out is allowed only when:

- the event has reached `end_datetime`, or
- an active early sign-out override is open

If the student signs out during an allowed sign-out window:

- `check_out_status = "present"`

If sign-out is missing or finalized after the effective close:

- `check_out_status = "absent"`

## Final Status Matrix

The backend finalizes `status` with this matrix:

| check_in_status | check_out_status | final status |
| --- | --- | --- |
| `present` | `present` | `present` |
| `late` | `present` | `late` |
| `absent` | `present` | `absent` |
| any value | not `present` | `absent` |
| unknown check-in | `present` | `absent` |

Implementation:

- `Backend/app/services/attendance_status.py`

## Route Behavior

### Manual and operator face-scan attendance

These routes now branch in this order:

1. find the student and current event
2. if there is an active attendance with no `time_out`, treat the request as sign-out
3. otherwise evaluate the check-in window and create a new attendance

That behavior is important so sign-out override works correctly.

Routes:

- `POST /attendance/manual`
- `POST /attendance/face-scan`

### Student face attendance

Student self-scan already follows the same sign-out-first behavior:

- `POST /face/face-scan-with-recognition`

## Automatic Finalization

When an event reaches the effective sign-out close, the backend finalizes remaining attendance:

- open attendances with no `time_out` become:
  - `check_out_status = "absent"`
  - final `status = "absent"`
- students in scope with no attendance row receive an auto-created absent record

Finalization now waits for the effective sign-out close, not the raw `end_datetime`.

Implementation:

- `Backend/app/services/event_attendance_service.py`
- `Backend/app/services/event_workflow_status.py`

## Reporting Behavior

For reporting and attendance-rate calculations:

- `present` counts as attended
- `late` counts as attended
- `absent` does not count as attended
- `excused` does not count as attended

Existing report models already expose late-aware summary fields such as:

- `ProgramBreakdownItem.late`
- `StudentAttendanceSummary.late_events`

## Main Backend Touchpoints

- `Backend/app/models/attendance.py`
- `Backend/app/models/event.py`
- `Backend/app/schemas/attendance.py`
- `Backend/app/schemas/attendance_requests.py`
- `Backend/app/schemas/event.py`
- `Backend/app/services/attendance_status.py`
- `Backend/app/services/event_time_status.py`
- `Backend/app/services/event_attendance_service.py`
- `Backend/app/routers/attendance.py`
- `Backend/app/routers/face_recognition.py`

## Testing

Recommended checks:

1. Run `Backend\.venv\Scripts\python.exe -m pytest -q Backend/app/tests/test_attendance_status_support.py Backend/app/tests/test_governance_hierarchy_api.py -k "attendance or override"`.
2. Create an event with:
   - `early_check_in_minutes`
   - `late_threshold_minutes`
   - `sign_out_grace_minutes`
3. Record check-in before start and confirm `check_in_status = "present"`.
4. Record check-in at exact start or inside the threshold and confirm `check_in_status = "late"`.
5. Record check-in after the threshold and confirm `check_in_status = "absent"`.
6. Try to sign out before sign-out opens and confirm the backend rejects it.
7. Open `POST /events/{event_id}/sign-out-override/open` and confirm the same active attendance can sign out successfully.
8. Confirm final rows include `check_in_status`, `check_out_status`, and the correct final `status`.
