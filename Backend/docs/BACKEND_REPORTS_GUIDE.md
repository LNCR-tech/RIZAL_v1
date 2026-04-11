# Backend Reports Guide

## Purpose

This guide documents the dedicated reports router that serves recommended reports listed in `REPORT_CATALOG.md`.

## Router

- file: `Backend/app/routers/reports.py`
- base path: `/api/reports`
- auth: same JWT auth used by the rest of the API
- scope model:
  - `admin` and `campus_admin`: school-scoped access
  - governance members (`SSG` / `SG` / `ORG`): must have `manage_attendance`, data is scope-limited by governance unit
  - student: leaderboard endpoint only

## Endpoints

### Attendance reports

- `GET /api/reports/attendance/at-risk`
- `GET /api/reports/attendance/top-absentees`
- `GET /api/reports/attendance/top-late`
- `GET /api/reports/attendance/leaderboard`
- `GET /api/reports/attendance/recovery`
- `GET /api/reports/attendance/decline-alerts`
- `GET /api/reports/attendance/by-day-of-week`
- `GET /api/reports/attendance/by-time-block`
- `GET /api/reports/attendance/year-level-distribution`
- `GET /api/reports/attendance/repeat-participation`

### Event reports

- `GET /api/reports/events/no-show`
- `GET /api/reports/events/execution-quality`
- `GET /api/reports/events/completion-vs-cancellation`
- `GET /api/reports/events/first-time-vs-repeat`

### School KPI

- `GET /api/reports/school/kpi-dashboard`

## Common Query Parameters

- `governance_context=SSG|SG|ORG` for governance-scoped views
- `start_date`, `end_date`
- `department_id`, `program_id`
- report-specific controls such as:
  - `threshold`, `min_events`, `limit`
  - period compare fields:
    - `current_start_date`, `current_end_date`
    - `previous_start_date`, `previous_end_date`

## Runtime Notes

- attendance calculations use latest attendance record per `(student_id, event_id)` pair
- valid attendance follows existing attendance display/validity rules (`present` and `late` only after completion)
- no new database tables or migrations are introduced

## How To Test

1. Ensure backend is running and seeded with sample users/events/attendance.
2. Call:
   - `GET /api/reports/attendance/at-risk`
   - `GET /api/reports/events/no-show`
   - `GET /api/reports/school/kpi-dashboard`
3. Repeat calls with `governance_context=SSG`, `SG`, and `ORG` using matching governance users.
4. Verify student accounts can open leaderboard but receive `403` on manage-attendance-only reports.
