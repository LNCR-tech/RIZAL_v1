# Backend Event Time Status Guide

## Purpose

This guide documents the computed attendance-window logic that now drives event check-in, sign-out, and workflow auto-sync.

The backend keeps two related concepts:

- stored workflow status on `events.status`: `upcoming`, `ongoing`, `completed`, `cancelled`
- computed time-window status used for attendance decisions

The computed layer is the source of truth for attendance behavior.

## Event Timing Fields

Per-event timing is now configured with:

- `start_datetime`
- `end_datetime`
- `early_check_in_minutes`
- `late_threshold_minutes`
- `sign_out_grace_minutes`
- `sign_out_override_until`

Default values for newly created events:

- `early_check_in_minutes = 30`
- `late_threshold_minutes = 10`
- `sign_out_grace_minutes = 20`

Existing events keep whatever values are already stored.

## Default Source For New Events

New event requests can now omit the three attendance-window values and let the backend fill them from settings.

Resolution order:

1. explicit per-event request values
2. `ORG` override defaults on the matching `governance_unit`
3. `SG` override defaults on the matching `governance_unit`
4. school defaults on `school_settings`
5. hard fallback `30 / 10 / 20`

Stored default-setting fields:

- school-wide:
  - `school_settings.event_default_early_check_in_minutes`
  - `school_settings.event_default_late_threshold_minutes`
  - `school_settings.event_default_sign_out_grace_minutes`
- SG/ORG override:
  - `governance_units.event_default_early_check_in_minutes`
  - `governance_units.event_default_late_threshold_minutes`
  - `governance_units.event_default_sign_out_grace_minutes`

Important rules:

- `SSG` does not store its own override layer
- `SSG` event creation uses the school default
- `SG` and `ORG` event creation can use a unit override when the route resolves that governance scope
- resetting an SG/ORG override to `null` returns future events to school-default behavior

Stored on:

- `Backend/app/models/event.py`
- `Backend/app/schemas/event.py`
- migration `Backend/alembic/versions/e4b7c1d9f6a2_add_event_attendance_window_controls.py`
- migration `Backend/alembic/versions/f5d2c8a1b4e9_add_school_and_governance_event_defaults.py`

## Computed Time Statuses

The service in `Backend/app/services/event_time_status.py` computes one of these states:

- `before_check_in`
- `early_check_in`
- `late_check_in`
- `absent_check_in`
- `sign_out_open`
- `closed`

### Window rules

Given:

- `check_in_opens_at = start_datetime - early_check_in_minutes`
- `late_threshold_time = start_datetime + late_threshold_minutes`
- `normal_sign_out_closes_at = end_datetime + sign_out_grace_minutes`
- `effective_sign_out_closes_at = max(normal_sign_out_closes_at, sign_out_override_until)`

The computed status is:

1. before `check_in_opens_at` -> `before_check_in`
2. during an active override -> `sign_out_open`
3. from `check_in_opens_at` until just before `start_datetime` -> `early_check_in`
4. from exact `start_datetime` through `late_threshold_time` -> `late_check_in`
5. after `late_threshold_time` until `end_datetime` -> `absent_check_in`
6. from `end_datetime` through `effective_sign_out_closes_at` -> `sign_out_open`
7. after `effective_sign_out_closes_at` -> `closed`

Important business rule:

- exact event start is already `late`

## Attendance Decisions

### Check-in

`get_attendance_decision()` returns:

- `before_check_in` -> reject
- `early_check_in` -> allow, mark `present`
- `late_check_in` -> allow, mark `late`
- `absent_check_in` -> allow, mark `absent`
- `sign_out_open` -> reject new check-in
- `closed` -> reject

### Sign-out

`get_sign_out_decision()` returns:

- allow only during:
  - the normal sign-out window
  - an active early sign-out override
- reject before sign-out opens
- reject after the effective sign-out close

## Early Sign-Out Override

The backend exposes:

- `POST /events/{event_id}/sign-out-override/open`

Behavior:

- permission requirement matches event attendance management access
- the event must already have started
- cancelled events cannot open sign-out
- completed events cannot reopen sign-out
- the request body now requires `override_minutes`
- opening the override sets `sign_out_override_until = now + override_minutes`
- while override is active, new check-ins are blocked and open attendances may sign out
- if the override expires before the scheduled end, sign-out closes again until the normal sign-out window opens
- if the override overlaps the normal sign-out window, sign-out stays open until the later close time

Example request body:

```json
{
  "override_minutes": 12
}
```

Implementation:

- `Backend/app/routers/events.py`

## Workflow Auto-Sync Mapping

The workflow sync service maps computed time status to stored event status like this:

- `before_check_in` -> `upcoming`
- `early_check_in` -> `upcoming`
- `late_check_in` -> `ongoing`
- `absent_check_in` -> `ongoing`
- `sign_out_open` -> `ongoing`
- `closed` -> `completed`

So an event stays `ongoing` until all sign-out availability has ended.

Main file:

- `Backend/app/services/event_workflow_status.py`

## Routes That Use The Computed Decision

- `GET /events/{event_id}/time-status`
- `POST /events/{event_id}/verify-location`
- `POST /events/{event_id}/sign-out-override/open`
- `POST /attendance/manual`
- `POST /attendance/face-scan`
- `POST /attendance/{attendance_id}/time-out`
- `POST /attendance/face-scan-timeout`
- `POST /face/face-scan-with-recognition`

The manual and operator face-scan attendance routes now branch in this order:

1. if the student already has an active attendance with no `time_out`, treat the request as sign-out
2. otherwise evaluate the check-in window

That ordering is required so early sign-out override works correctly.

## Response Fields

`get_event_status()` and the public route serializers now include:

- `event_status`
- `current_time`
- `check_in_opens_at`
- `start_time`
- `end_time`
- `late_threshold_time`
- `sign_out_opens_at`
- `normal_sign_out_closes_at`
- `effective_sign_out_closes_at`
- `sign_out_override_until`
- `sign_out_override_active`
- `timezone_name`

## Example

If an event is:

- start: `1:00 PM`
- end: `2:00 PM`
- early check-in: `10`
- late threshold: `10`
- sign-out grace: `10`

then:

- `12:50 PM` to `12:59 PM` -> early check-in, status `present`
- `1:00 PM` to `1:10 PM` -> late check-in, status `late`
- `1:11 PM` to `1:59 PM` -> absent check-in, status `absent`
- `2:00 PM` to `2:10 PM` -> sign-out open
- after `2:10 PM` -> closed

## Testing

Recommended checks:

1. Run `Backend\.venv\Scripts\python.exe -m pytest -q Backend/app/tests/test_event_time_status.py Backend/app/tests/test_event_workflow_status.py`.
2. As Campus Admin, update the school defaults and then create a new event without sending attendance-window fields.
3. As SG or ORG with `manage_events`, save a unit override and create a new event without sending attendance-window fields.
4. Confirm the created event stores the effective resolved values before checking time-status behavior.
5. Call `GET /events/{event_id}/time-status` before check-in opens, during early check-in, during late check-in, during absent check-in, during sign-out, and after close.
6. Call `POST /events/{event_id}/sign-out-override/open` with `{"override_minutes": 12}` after the event has started and confirm `sign_out_override_until` is returned.
7. Verify that `POST /events/{event_id}/verify-location` includes the new time-window metadata.
8. Confirm the stored event `status` stays `ongoing` during sign-out and only becomes `completed` after the effective sign-out close.
