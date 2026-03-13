# Backend Event Time Status Guide

## Purpose

This guide explains the dynamic event time-status layer that was added to the backend.

The goal is:

- keep the stored event workflow status (`upcoming`, `ongoing`, `completed`, `cancelled`) for organizers
- add a computed attendance-window status (`upcoming`, `open`, `late`, `closed`) for verification flows
- keep the attendance-window status computed while also syncing the stored workflow status safely on backend access

This keeps the feature safe for the current repo while making attendance decisions automatic.

## Logic Summary

For attendance verification, the backend now computes a separate event time status from:

- `start_datetime`
- `end_datetime`
- `late_threshold_minutes`
- current time in `Asia/Manila`

Computed rules:

1. before `start_datetime` -> `upcoming`
2. from `start_datetime` through `start_datetime + late_threshold_minutes` -> `open`
3. after the late threshold but before `end_datetime` -> `late`
4. at or after `end_datetime` -> `closed`

Attendance decision rules:

- `upcoming` -> reject attendance verification
- `open` -> allow and mark as `present`
- `late` -> allow and mark as `late`
- `closed` -> reject new attendance verification

Important behavior in this repo:

- this computed time status is still the source of truth for attendance decisions
- the stored event `status` is now auto-synced by Celery Beat and by relevant backend request paths
- student face sign-out is still allowed when an active attendance already exists

## Main Files

- `Backend/app/services/event_time_status.py`
- `Backend/app/services/event_workflow_status.py`
- `Backend/app/services/attendance_status.py`
- `Backend/app/routers/events.py`
- `Backend/app/routers/face_recognition.py`
- `Backend/app/routers/attendance.py`
- `Backend/app/worker/celery_app.py`
- `Backend/app/worker/tasks.py`
- `Backend/app/tests/test_event_time_status.py`
- `Backend/app/tests/test_event_workflow_status.py`
- `Backend/app/tests/test_attendance_status_support.py`

## Step-By-Step Implementation

## 1. Add the reusable time-status service

`Backend/app/services/event_time_status.py` now contains:

- `get_event_status()`
- `get_attendance_decision()`

Why this was added:

- the logic can now be reused by FastAPI routes, Flask views, Django views, Celery tasks, or plain service code
- there is no dependency on FastAPI request objects or database sessions

## 2. Normalize datetimes safely

The service treats event schedule datetimes as event-local datetimes in `Asia/Manila`.

If a datetime is already timezone-aware, it is converted safely.

If a datetime is naive:

- event schedule values are treated as `Asia/Manila`
- attendance timestamps recorded by the backend are normalized from UTC in `Backend/app/services/attendance_status.py`

This matches the repo's current pattern:

- events are created from local schedule times
- attendance timestamps are usually recorded from server time

## 3. Keep the attendance-window status computed and sync the workflow status safely

The computed attendance-window status is still not stored in the database.

Instead:

- the backend computes the time status every time it needs it
- that computed status now drives both periodic scheduler syncing and request-time syncing of the stored workflow status

Current workflow sync behavior:

- `upcoming` -> stored `upcoming`
- `open` / `late` -> stored `ongoing`
- `closed` -> stored `completed`

Safety rules:

- `cancelled` stays manual
- `completed` is treated as sticky during automatic sync so it is not reopened accidentally

## 4. Expose the computed status in routes

The backend now exposes:

- `GET /events/{event_id}/time-status`
- `POST /events/{event_id}/verify-location`

`POST /events/{event_id}/verify-location` now returns:

- geofence result
- computed event time status
- attendance decision

Related workflow auto-sync is now applied in the event, attendance, and face route helpers before those routes continue.

The same workflow sync logic is also called by the Celery Beat periodic task:

- `app.worker.tasks.sync_event_workflow_statuses`

## 5. Use the decision in attendance routes

The dynamic time decision is now used in:

- `POST /face/face-scan-with-recognition`
- `POST /attendance/face-scan`
- `POST /attendance/manual`
- `POST /attendance/bulk`

Current behavior:

- new check-ins are rejected when the event is still `upcoming`
- new check-ins are rejected when the event is already `closed`
- successful check-ins during `open` become `present`
- successful check-ins during `late` become `late`

## Python Implementation

Core usage:

```python
from datetime import datetime
from app.services.event_time_status import get_event_status, get_attendance_decision

time_status = get_event_status(
    start_time=event.start_datetime,
    end_time=event.end_datetime,
    late_threshold_minutes=event.late_threshold_minutes,
)

decision = get_attendance_decision(
    start_time=event.start_datetime,
    end_time=event.end_datetime,
    late_threshold_minutes=event.late_threshold_minutes,
)
```

Returned fields from `get_event_status()`:

- `event_status`
- `current_time`
- `start_time`
- `end_time`
- `late_threshold_time`
- `timezone_name`

Returned fields from `get_attendance_decision()`:

- `event_status`
- `attendance_allowed`
- `attendance_status`
- `reason_code`
- `message`
- `current_time`
- `start_time`
- `end_time`
- `late_threshold_time`
- `timezone_name`

## Example FastAPI Integration

Example pattern used in this repo:

```python
from fastapi import HTTPException
from app.services.event_time_status import get_attendance_decision

decision = get_attendance_decision(
    start_time=event.start_datetime,
    end_time=event.end_datetime,
    late_threshold_minutes=event.late_threshold_minutes,
)

if not decision.attendance_allowed:
    raise HTTPException(
        status_code=403,
        detail={
            "code": decision.reason_code,
            "message": decision.message,
            "event_status": decision.event_status,
        },
    )

attendance_status = decision.attendance_status
```

This same service can be reused in Flask or Django because it is plain Python.

## Example API Flow

1. User sends GPS coordinates.
2. Backend checks the geofence.
3. Backend computes the dynamic event time status.
4. Backend decides whether attendance is allowed.
5. Backend returns the result.

## Example JSON Request

`POST /events/12/verify-location`

```json
{
  "latitude": 8.1575,
  "longitude": 123.8431,
  "accuracy_m": 20
}
```

## Example JSON Response

```json
{
  "ok": true,
  "reason": null,
  "distance_m": 11.284,
  "effective_distance_m": 31.284,
  "radius_m": 100.0,
  "accuracy_m": 20.0,
  "time_status": {
    "event_status": "late",
    "current_time": "2026-03-11T09:23:00+08:00",
    "start_time": "2026-03-11T09:00:00+08:00",
    "end_time": "2026-03-11T11:00:00+08:00",
    "late_threshold_time": "2026-03-11T09:10:00+08:00",
    "timezone_name": "Asia/Manila"
  },
  "attendance_decision": {
    "event_status": "late",
    "attendance_allowed": true,
    "attendance_status": "late",
    "reason_code": null,
    "message": "Attendance is still allowed, but it will be marked late.",
    "current_time": "2026-03-11T09:23:00+08:00",
    "start_time": "2026-03-11T09:00:00+08:00",
    "end_time": "2026-03-11T11:00:00+08:00",
    "late_threshold_time": "2026-03-11T09:10:00+08:00",
    "timezone_name": "Asia/Manila"
  }
}
```

## Suggested Production Improvements

- automatic attendance closing
  - run a worker task after `end_datetime` to finalize incomplete attendances without waiting for a manual event-status change

- timezone-safe scheduling
  - store event datetimes in UTC internally and convert at the edges
  - add an explicit event timezone field if schools may span multiple zones

- background validation
  - Celery Beat now calls the workflow sync service automatically; if you later move to managed cloud scheduling, reuse the same task/service logic

- preventing early or late check-ins
  - keep using `get_attendance_decision()` for every new attendance creation path
  - optionally add a configurable grace period before `start_datetime`

- handling server time drift
  - sync servers with NTP
  - centralize time reads in one helper
  - log the computed current time and timezone in attendance audit trails

- automatic attendance closing
  - extend the worker to mark lingering no-timeout attendances as `absent` after the event ends if business rules require it

## Test Files

- `Backend/app/tests/test_event_time_status.py`
- `Backend/app/tests/test_attendance_status_support.py`

These tests cover:

- status transitions across `upcoming`, `open`, `late`, and `closed`
- attendance decision mapping
- invalid schedule handling
- timezone normalization for late-threshold checks
