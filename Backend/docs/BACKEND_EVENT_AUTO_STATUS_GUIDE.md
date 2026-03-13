# Backend Event Auto Status Guide

## Purpose

This guide explains the automatic event workflow-status sync that was added on top of the existing event time-status system.

The goal is:

- keep attendance decisions time-based
- automatically keep the stored event `status` aligned with the event schedule
- preserve existing `cancelled` and manual completion behavior
- finalize attendance automatically when an event closes through time-based sync

## Status Layers

The backend now uses two related status layers:

1. Attendance window status from `Backend/app/services/event_time_status.py`
   - `upcoming`
   - `open`
   - `late`
   - `closed`

2. Stored workflow status on `events.status`
   - `upcoming`
   - `ongoing`
   - `completed`
   - `cancelled`

Mapping rule:

- `upcoming` time status -> `upcoming` workflow status
- `open` time status -> `ongoing` workflow status
- `late` time status -> `ongoing` workflow status
- `closed` time status -> `completed` workflow status

## Main Files

- `Backend/app/services/event_workflow_status.py`
- `Backend/app/services/event_time_status.py`
- `Backend/app/services/event_attendance_service.py`
- `Backend/app/routers/events.py`
- `Backend/app/routers/attendance.py`
- `Backend/app/routers/face_recognition.py`
- `Backend/app/worker/celery_app.py`
- `Backend/app/worker/tasks.py`
- `Backend/app/tests/test_event_workflow_status.py`
- `Backend/docs/BACKEND_EVENT_TIME_STATUS_GUIDE.md`

## Step-By-Step Logic

## 1. Compute the time-based status

The backend still computes the dynamic attendance-window state from:

- `start_datetime`
- `end_datetime`
- `late_threshold_minutes`
- current time in `Asia/Manila`

That logic remains in:

- `Backend/app/services/event_time_status.py`

## 2. Convert that time status into the stored workflow status

The new service in:

- `Backend/app/services/event_workflow_status.py`

maps the time status into the stored event workflow status:

- before start -> `upcoming`
- during open or late window -> `ongoing`
- after end -> `completed`

## 3. Preserve terminal manual states safely

Two safety rules were added:

- `cancelled` stays manual and is never auto-overridden by time
- `completed` is treated as sticky during automatic sync so an already completed event is not reopened by accident

This keeps the change safe with the repo's current event-management workflow.

## 4. Finalize attendance when auto-sync closes the event

When the auto-sync moves an event into `completed`, the backend also runs:

- `finalize_completed_event_attendance()`

from:

- `Backend/app/services/event_attendance_service.py`

That means the system automatically:

- creates `absent` records for scoped students who never signed in
- marks no-timeout active attendances as `absent`

## 5. Trigger the sync automatically in the background

The repo now runs a periodic scheduler through Celery Beat.

Background flow:

- Celery Beat publishes `app.worker.tasks.sync_event_workflow_statuses`
- the worker scans `upcoming` and `ongoing` events
- matching events are moved to `ongoing` or `completed`
- completed events trigger automatic attendance finalization

Default interval:

- every `60` seconds

Configuration:

- `EVENT_STATUS_SYNC_ENABLED=true`
- `EVENT_STATUS_SYNC_INTERVAL_SECONDS=60`

The repo also keeps request-driven sync in the route helpers as a fallback, so normal app requests still correct stale statuses even if the scheduler was temporarily down.

## Routes and Logic Touchpoints

Updated routes and helpers:

- `GET /events/`
- `GET /events/ongoing`
- `GET /events/{event_id}`
- `GET /events/{event_id}/time-status`
- `POST /events/{event_id}/verify-location`
- `GET /events/{event_id}/attendees`
- `GET /events/{event_id}/stats`
- `PATCH /events/{event_id}`
- `PATCH /events/{event_id}/status`
- attendance helper `_get_event_in_school_or_404()`
- face helper `_get_school_event_or_404()`
- periodic task `app.worker.tasks.sync_event_workflow_statuses`

## Important Behavior Notes

- the dynamic attendance window status is still computed on demand and is still the source of truth for attendance decisions
- the stored event `status` is auto-synced both by Celery Beat and by request-time fallbacks
- the `beat` service should run as a single instance in deployment
- `cancelled` remains a manual organizer action
- manual `completed` still works and still finalizes attendance

## Example Flow

1. An event starts in the future with stored status `upcoming`.
2. Celery Beat fires the periodic sync task after the start time.
3. The backend sync service recalculates the event time window.
4. The stored `events.status` is updated to `ongoing`.
5. After the end time, the next scheduler run moves it to `completed`.
6. Attendance finalization runs automatically.

## No Migration Impact

This change does not add or alter database columns.

It changes backend behavior only.

## Deployment Notes

For container or VPS deployments, this setup is practical as long as:

- Redis is available
- one worker is running
- one beat instance is running

For managed cloud platforms, you can keep this design or replace Beat later with a provider cron job that calls the same sync logic.
