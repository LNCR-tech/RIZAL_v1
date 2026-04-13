# Backend Reports Module Guide

## Purpose

This guide documents the reports refactor that consolidates report-related logic into a modular `app/reports` package while preserving existing API contracts.

## New Module Structure

Added:

- `Backend/app/reports/attendance/`
  - `router.py`
  - `service.py`
  - `queries.py`
- `Backend/app/reports/student/`
  - `router.py`
  - `service.py`
  - `queries.py`
- `Backend/app/reports/school/`
  - `router.py`
  - `service.py`
  - `queries.py`
- `Backend/app/reports/system/`
  - `router.py`
  - `service.py`
  - `queries.py`

## Architecture Rule Applied

Refactored report endpoints now follow:

- `router -> service -> queries -> database`

### Responsibilities

- Router layer:
  - request parsing
  - dependency injection
  - response model enforcement
- Service layer:
  - permissions and orchestration
  - business rules and computed report fields
- Query layer:
  - SQLAlchemy query construction
  - data fetch primitives

## Endpoint Contract Preservation

No report endpoint paths were changed.

The following report endpoints remain available with the same public behavior:

- Attendance reports/analytics:
  - `GET /api/attendance/events/{event_id}/report`
  - `GET /api/attendance/students/overview`
  - `GET /api/attendance/students/{student_id}/report`
  - `GET /api/attendance/students/{student_id}/stats`
  - `GET /api/attendance/summary`
  - `GET /api/attendance/events/{event_id}/attendees`
  - `GET /api/attendance/events/{event_id}/attendances`
  - `GET /api/attendance/events/{event_id}/attendances/{status}`
  - `GET /api/attendance/events/{event_id}/attendances-with-students`
  - `GET /api/attendance/students/records`
  - `GET /api/attendance/students/{student_id}/records`
  - `GET /api/attendance/me/records`
- System report/log endpoints:
  - `GET /api/admin/import-preview-errors/{preview_token}/download`
  - `GET /api/admin/import-preview-errors/{preview_token}/retry-download`
  - `GET /api/admin/import-status/{job_id}`
  - `GET /api/admin/import-errors/{job_id}/download`
  - `GET /api/audit-logs`
  - `GET /api/notifications/logs`
  - `GET /api/governance/units/{governance_unit_id}/dashboard-overview`

## Legacy Router Wiring

Legacy router files were reduced to thin composition/wrapper behavior:

- `Backend/app/main.py`
  - now registers reports through `include_api_router(reports_router)` using `Backend/app/reports/router.py`
- `Backend/app/routers/attendance/__init__.py`
  - now keeps only operational attendance routes (check-in/out + overrides)
  - report routes were removed from attendance package-level includes to prevent duplicate registrations
- `Backend/app/routers/attendance/reports.py`
  - retained as compatibility shim; report endpoints are now mounted via `app.reports.router` registration in main
- `Backend/app/routers/attendance/records.py`
  - retained as an empty compatibility router to preserve attendance package include wiring
- `Backend/app/routers/admin_import.py`
- `Backend/app/routers/audit_logs.py`
- `Backend/app/routers/notifications.py`
- `Backend/app/routers/governance_hierarchy.py`
  - targeted report endpoints now delegate to `app.reports.system`
  - duplicate, unused report-file helper functions were removed from `admin_import.py`
    because equivalent implementations are centralized in `app.reports.system.queries`
  - preview manifest path/read helpers in `admin_import.py` now reuse
    `app.reports.system.queries.preview_manifest_path` and
    `app.reports.system.queries.load_preview_manifest`

## Schema, Migration, and Config Impact

- No request/response schema contracts were renamed.
- No database migrations were added.
- No environment variable or runtime config key changes were introduced.
- Import preview validation now tolerates trailing blank header columns in Excel uploads while still enforcing the expected header names and order.

## How To Test

1. Run compile checks:
   - `python -m compileall Backend/app/reports Backend/app/routers/attendance/reports.py Backend/app/routers/attendance/records.py Backend/app/routers/admin_import.py Backend/app/routers/audit_logs.py Backend/app/routers/notifications.py Backend/app/routers/governance_hierarchy.py`
2. Run backend API regression tests for touched domains:
   - `python -m pytest -q Backend/app/tests/test_admin_import_preview_flow.py Backend/app/tests/test_governance_hierarchy_api.py Backend/app/tests/test_public_attendance.py`
3. Run full backend regression after integration:
   - `python -m pytest -q Backend/app/tests`
4. Optional manual API smoke:
   - call each report endpoint listed above with an authenticated account and verify response shape/HTTP status parity with pre-refactor behavior.
5. Import preview regression:
   - upload an `.xlsx` file whose header row matches the template plus trailing blank columns and verify `POST /api/admin/import-students/preview` returns a successful preview when row data is valid.
