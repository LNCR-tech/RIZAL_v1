# Reports Location Guide (Frontend + Backend)

## Scope

This guide maps where report-related functionality lives across the project, including:

- frontend report pages and navigation entry points
- frontend API callers used by report screens
- backend routers/functions serving report data
- report-related schemas/models/storage paths
- report-related tests and documentation

---

## Frontend: Report Locations

### 1) Route Entry Points

- `Frontend/src/App.tsx`
  - lazy imports:
    - `Reports` at `line 21`
    - `ReportsLab` at `line 22`
  - routes:
    - `/admin_reports` -> `Reports` (`line 110`)
    - `/campus_admin_reports` -> `Reports` (`line 170`)
    - `/dashboard/reports-lab` -> `ReportsLab` (`line 545`)
  - `ReportsLab` route is guarded by `ProtectedRoute` allowing roles `admin`, `campus_admin`, `student` (`lines 540-543`)

### 2) Main Report Pages

- `Frontend/src/pages/Reports.tsx`
  - legacy report UI for event attendance summaries
  - calls:
    - `fetchAllEvents` (event list/search)
    - `fetchEventAttendanceReport` (`GET /api/attendance/events/{event_id}/report`)
  - includes CSV/PDF export logic in browser

- `Frontend/src/pages/ReportsLab.tsx`
  - central "Reports Lab" runner page (`ReportsLab` component starts around `line 780`)
  - report catalog config:
    - `REPORTS` array around `line 169`
  - report executor switch:
    - `executeReport(...)` around `line 308`
  - helper HTTP wrappers inside page:
    - `apiGet`, `apiPost`, `apiPostForm` (`lines 268-291`)

### 3) Navigation That Links to Reports

- `Frontend/src/components/NavbarAdmin.tsx`
  - link to `/dashboard/reports-lab` (`line 115`)
- `Frontend/src/components/NavbarSchoolIT.tsx`
  - links to `/campus_admin_reports` (`line 72`) and `/dashboard/reports-lab` (`line 78`)
- `Frontend/src/components/NavbarStudent.tsx`
  - link to `/dashboard/reports-lab` (`line 140`)
- `Frontend/src/components/NavbarStudentSSG.tsx`
  - item path `/dashboard/reports-lab` (`line 80`)
- `Frontend/src/components/GovernanceSidebar.tsx`
  - item path `/dashboard/reports-lab` (`line 137`)
- `Frontend/src/dashboard/SchoolITDashboard.tsx`
  - report card link to `/campus_admin_reports` (`line 113`)

### 4) Frontend Files ReportsLab Depends On

- `Frontend/src/api/attendanceApi.ts`
  - `fetchStudentAttendanceOverview`
  - `fetchStudentAttendanceReport`
  - `fetchEventAttendanceReport`
- `Frontend/src/api/eventsApi.ts`
  - `fetchAllEvents`
  - `fetchEventAttendancesWithStudents`
- `Frontend/src/api/academicApi.ts`
  - `fetchAcademicCatalog`
- `Frontend/src/api/governanceHierarchyApi.ts`
  - `fetchGovernanceUnits`
  - `fetchMyGovernanceAccess`
  - `fetchGovernanceDashboardOverview`
- `Frontend/src/api/userApi.ts`
  - `fetchSchoolScopedUsers`
  - `fetchCurrentUserProfile`
- `Frontend/src/hooks/useGovernanceAccess.ts`
  - governance permission/scope loading cache hook used for report visibility/scope
- `Frontend/src/lib/api/client.ts`
  - low-level authenticated API request helpers used by ReportsLab
- `Frontend/src/lib/auth/storedUser.ts`
  - reads stored user/session metadata for role + school scope
- `Frontend/src/utils/roleUtils.ts`
  - role normalization (`admin`, `campus-admin`, `student`, etc.)
- `Frontend/src/components/ProtectedRoute.tsx`
  - route access guard used by report routes

### 5) Report UI Style Files

- `Frontend/src/css/Reports.css` exists as a report-style asset file
- `Reports.tsx` and `ReportsLab.tsx` currently rely mostly on inline styles + Bootstrap classes

---

## Backend: Report Locations

### 1) Router Registration / Mounting

- `Backend/app/main.py`
  - includes attendance router at `/api/attendance`
  - includes dedicated reports router at `/api/reports` via `include_api_router(reports.router)`
- `Backend/app/routers/attendance/__init__.py`
  - attendance router prefix `/attendance`
  - includes:
    - `reports_router`
    - `records_router`
    - `check_in_out_router`
    - `overrides_router`

### 2) Attendance Report Router (Legacy + Core)

- file: `Backend/app/routers/attendance/reports.py`
- key endpoints/functions:
  - `GET /api/attendance/events/{event_id}/report` -> `get_event_attendance_report`
  - `GET /api/attendance/students/overview` -> `get_students_attendance_overview`
  - `GET /api/attendance/students/{student_id}/report` -> `get_student_attendance_report`
  - `GET /api/attendance/students/{student_id}/stats` -> `get_student_attendance_stats`
  - `GET /api/attendance/summary` -> `get_attendance_summary`

### 3) Dedicated Reports Router (`/api/reports`)

- file: `Backend/app/routers/reports.py`
- router prefix: `/reports` (mounted under `/api`)
- endpoints/functions:
  - `GET /api/reports/attendance/at-risk` -> `get_at_risk_attendance_report`
  - `GET /api/reports/attendance/top-absentees` -> `get_top_absentees_report`
  - `GET /api/reports/attendance/top-late` -> `get_top_late_students_report`
  - `GET /api/reports/attendance/leaderboard` -> `get_attendance_leaderboard_report`
  - `GET /api/reports/attendance/recovery` -> `get_attendance_recovery_report`
  - `GET /api/reports/attendance/decline-alerts` -> `get_attendance_decline_report`
  - `GET /api/reports/events/no-show` -> `get_no_show_event_report`
  - `GET /api/reports/events/execution-quality` -> `get_event_execution_quality_report`
  - `GET /api/reports/events/completion-vs-cancellation` -> `get_event_completion_vs_cancellation_report`
  - `GET /api/reports/attendance/by-day-of-week` -> `get_attendance_by_day_of_week_report`
  - `GET /api/reports/attendance/by-time-block` -> `get_attendance_by_time_block_report`
  - `GET /api/reports/attendance/year-level-distribution` -> `get_year_level_attendance_distribution_report`
  - `GET /api/reports/attendance/repeat-participation` -> `get_repeat_participation_report`
  - `GET /api/reports/events/first-time-vs-repeat` -> `get_first_time_vs_repeat_attendee_report`
  - `GET /api/reports/school/kpi-dashboard` -> `get_school_kpi_dashboard_report`

### 4) Supporting Backend Endpoints Used by ReportsLab

- `Backend/app/routers/attendance/records.py`
  - `GET /api/attendance/events/{event_id}/attendances-with-students` -> `get_attendances_with_students`
  - `GET /api/attendance/students/records` -> `get_all_student_attendance_records`
  - `GET /api/attendance/me/records` -> `get_my_attendance_records`

- `Backend/app/routers/admin_import.py` (prefix `/api/admin`)
  - `POST /api/admin/import-students/preview` -> `preview_import_students`
  - `GET /api/admin/import-status/{job_id}` -> `get_import_status`
  - `GET /api/admin/import-errors/{job_id}/download` -> `download_import_errors`
  - `GET /api/admin/import-preview-errors/{preview_token}/download` -> `download_preview_errors`

- `Backend/app/routers/audit_logs.py` (prefix `/api/audit-logs`)
  - `GET /api/audit-logs` -> `search_audit_logs`

- `Backend/app/routers/notifications.py` (prefix `/api/notifications`)
  - `GET /api/notifications/logs` -> `list_notification_logs`
  - `POST /api/notifications/dispatch/missed-events` -> `dispatch_missed_events_notifications`
  - `POST /api/notifications/dispatch/low-attendance` -> `dispatch_low_attendance_alerts`
  - `POST /api/notifications/dispatch/event-reminders` -> `dispatch_event_reminders`

- `Backend/app/routers/governance_hierarchy.py` (prefix `/api/governance`)
  - `GET /api/governance/units/{governance_unit_id}/dashboard-overview` -> `get_governance_dashboard_overview`
  - `GET /api/governance/access/me` -> `get_my_governance_access`
  - `GET /api/governance/units` -> `list_governance_units`

- `Backend/app/routers/governance.py` (prefix `/api/governance`)
  - `POST /api/governance/run-retention` -> `run_retention_cleanup`

- selector/scope feeders used by ReportsLab forms:
  - `Backend/app/routers/events/queries.py` -> `GET /api/events/` (`read_events`)
  - `Backend/app/routers/departments.py` -> `GET /api/departments/` (`read_departments`)
  - `Backend/app/routers/programs.py` -> `GET /api/programs/` (`read_programs`)
  - `Backend/app/routers/users/accounts.py` -> `GET /api/users/` (`get_all_users`), `GET /api/users/me/` (`get_current_user_profile`)

### 5) Shared Backend Scope/Status Helpers Used by Reports

- `Backend/app/routers/attendance/shared.py`
  - `_get_attendance_governance_units`
  - `_apply_student_scope_filters`
  - `_get_event_ids_in_attendance_scope`
  - `_attendance_display_status_value`
  - `_attendance_is_valid_value`
  - `_ensure_event_report_access`
  - `_ensure_attendance_report_access`

---

## Schemas, Models, and Storage Used by Reports

### 1) Report Response Schemas

- `Backend/app/schemas/attendance.py`
  - `AttendanceReportResponse`
  - `StudentAttendanceSummary`
  - `StudentAttendanceReport`
  - `StudentListItem`
  - `ProgramBreakdownItem`

- `Backend/app/schemas/import_job.py`
  - `ImportJobStatusResponse.failed_report_download_url`

### 2) Core Models Used by Report Queries

- `Backend/app/models/attendance.py`
  - `AttendanceStatus`, `Attendance`
- `Backend/app/models/event.py`
  - `EventStatus`, `Event`
- `Backend/app/models/user.py`
  - `User`, `StudentProfile`
- `Backend/app/models/import_job.py`
  - `BulkImportJob.failed_report_path` (file path for failed-row report workbook)

### 3) Import Failed-Report Generation Path

- `Backend/app/services/student_import_service.py`
  - builds/saves failed-row workbook under `Path(settings.import_storage_dir) / "reports"`
  - returns report file path to job status updates
- `Backend/app/repositories/import_repository.py`
  - persists `failed_report_path` via `mark_completed(job_id, failed_report_path=...)`

---

## Data Flow Maps

### Flow A: Legacy Event Reports Page (`/admin_reports`, `/campus_admin_reports`)

1. User opens `Reports.tsx`
2. Page loads events via `fetchAllEvents` (`/api/events/`)
3. Selecting an event runs `fetchEventAttendanceReport` (`/api/attendance/events/{event_id}/report`)
4. Backend serves from `get_event_attendance_report` in `attendance/reports.py`
5. UI renders summary + charts, then client-side CSV/PDF export

### Flow B: Reports Lab (`/dashboard/reports-lab`)

1. User opens `ReportsLab.tsx`
2. Page loads selector data:
   - departments/programs (`/api/departments/`, `/api/programs/`)
   - events (`/api/events/`)
   - governance units/access (`/api/governance/units`, `/api/governance/access/me`)
   - school users (`/api/users/`)
3. User picks a report from `REPORTS` config
4. `executeReport(...)` maps selected runner -> endpoint call
5. Backend responds from one of:
   - `attendance/reports.py`
   - `reports.py`
   - `attendance/records.py`
   - admin/audit/notification/governance routers
6. Raw JSON + table are rendered in Report Output panel

### Flow C: Import Failed Rows Report

1. ReportsLab calls `/api/admin/import-status/{job_id}`
2. Backend returns status with `failed_report_download_url` when available
3. URL points to `/api/admin/import-errors/{job_id}/download`
4. File served from `BulkImportJob.failed_report_path` generated by `student_import_service.py`

---

## Tests Related to Reports

### Backend tests

- `Backend/app/tests/test_attendance_status_support.py`
  - validates report-related status/schema behavior (`test_report_models_accept_late_fields`)
- `Backend/app/tests/test_governance_hierarchy_api.py`
  - validates attendance-overview permission gating (`/api/attendance/students/overview`)
- `Backend/app/tests/test_admin_import_preview_flow.py`
  - validates preview error report and retry workbook endpoints

### Frontend tests

- no project-level frontend test files were found under `Frontend/src` for `Reports.tsx` or `ReportsLab.tsx`

### Coverage gap to note

- no dedicated backend tests were found for new `/api/reports/*` endpoints in `Backend/app/routers/reports.py`

---

## Existing Report Documentation

- `REPORT_CATALOG.md` (root)
  - functional catalog of current + recommended reports
- `Backend/docs/BACKEND_REPORTS_GUIDE.md`
  - dedicated backend reports router guide
- `Backend/docs/BACKEND_CHANGELOG.md`
  - changelog entries for reports router and related report behavior
- `Backend/docs/BACKEND_ATTENDANCE_STATUS_GUIDE.md`
  - attendance status semantics used by report calculations
- `Backend/docs/BACKEND_BULK_IMPORT_GUIDE.md`
  - import preview/error report behavior
- `Backend/docs/BACKEND_GOVERNANCE_HIERARCHY_GUIDE.md`
  - governance scope and permissions affecting report access
- `Backend/docs/BACKEND_PROJECT_STRUCTURE_GUIDE.md`
  - structural pointers to report router locations

