# Backend Attendance Status Guide

## Purpose

This document records how attendance statuses work in the backend and how the `late` status was merged into the live `RIZAL_v1` backend safely.

## Current Valid Attendance Statuses

- `present`
- `late`
- `absent`
- `excused`

## Event Late Threshold

Events now support `late_threshold_minutes`.

Meaning:

- the threshold is stored on the event
- the value is measured from the event start time
- if a valid sign-in happens after `start_datetime + late_threshold_minutes`, the final attendance status becomes `late`

Example:

- event starts at `9:00 AM`
- late threshold is `10`
- sign-in at `9:10 AM` is still `present`
- sign-in at `9:11 AM` becomes `late`

## Business Rule In This Repo

`late` is now a valid attendance status across the backend and database.

For reporting and attendance-rate calculations in this repo:

- `present` counts as attended
- `late` also counts as attended
- `absent` does not count as attended
- `excused` does not count as attended

## Automatic Absent On Event Completion

When an event is marked `completed`, the backend now finalizes attendance for the event scope.

Current behavior:

- students with no attendance record for the completed event are automatically given an `absent` record
- students with an active attendance record but no `time_out` are automatically marked `absent`

The participant scope follows the event assignment rules already used by the repo:

- all students in the school if no department or program filters are set
- otherwise the students matching the event's department and program scope

## Automatic Time Window Behavior

The backend now computes a separate attendance-window status from the event schedule.

Computed event time statuses:

- `upcoming`
- `open`
- `late`
- `closed`

Current behavior:

- `upcoming` rejects new attendance verification
- `open` allows verification and marks the new check-in as `present`
- `late` allows verification and marks the new check-in as `late`
- `closed` rejects new attendance verification

The reusable implementation lives in:

- `Backend/app/services/event_time_status.py`

Important limit:

- this computed time status does not replace the stored organizer event workflow status
- organizer event management still uses the event model's saved `status` field

## Main Files

- `Backend/app/models/attendance.py`
- `Backend/app/schemas/attendance.py`
- `Backend/app/services/attendance_status.py`
- `Backend/app/services/event_time_status.py`
- `Backend/app/routers/attendance.py`
- `Backend/app/services/notification_center_service.py`
- `Backend/alembic/versions/a12b34c56d78_add_late_to_attendance_status_enum.py`

## What Changed

### Models

The SQLAlchemy attendance enum now includes `late`.

The event model now also includes `late_threshold_minutes`.

### Schemas

The FastAPI and Pydantic attendance enum now includes `late`.

The event create and update schemas now accept `late_threshold_minutes`.

Additional response models now expose late-aware fields where needed:

- `ProgramBreakdownItem.late`
- `AttendanceReportResponse.late_attendees`
- `StudentAttendanceSummary.late_events`

### Migration

The PostgreSQL enum is updated with:

```sql
ALTER TYPE attendancestatus ADD VALUE IF NOT EXISTS 'late'
```

### Reports and summaries

Attendance summaries now treat `late` as attended for:

- event attendance report totals
- student overview attendance rate
- student attendance report totals
- attendance summary dashboard counts
- low-attendance notification calculations

Monthly chart dictionaries now also include a `late` key by default to avoid missing-key errors.

## Main Backend Touchpoints For This Feature

- `Backend/app/models/event.py`
- `Backend/app/schemas/event.py`
- `Backend/app/services/attendance_status.py`
- `Backend/app/services/event_attendance_service.py`
- `Backend/app/routers/events.py`
- `Backend/app/routers/attendance.py`
- `Backend/app/routers/face_recognition.py`

## Testing

Recommended checks:

1. Run the Alembic migration to head.
2. Run the focused attendance status tests.
3. Create or edit an event with `late_threshold_minutes`.
4. Sign in after the threshold and confirm the final status becomes `late`.
5. Mark an event `completed` and confirm students without attendance are materialized as `absent`.
6. Verify a summary endpoint returns `late` without validation or key errors.
7. Call `GET /events/{event_id}/time-status` and confirm the computed status changes from `upcoming` to `open`, `late`, and `closed`.
