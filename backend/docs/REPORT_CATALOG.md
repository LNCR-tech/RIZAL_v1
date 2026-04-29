# Report Catalog

<!--nav-->
[Previous](compatibility-fixes-apr-2026.md) | [Next](runtime-behavior.md) | [Home](/README.md)

---
<!--/nav-->

This catalog lists practical reports for the attendance system.

Role labels used below:
- `Admin`
- `Campus Admin`
- `SSG`
- `SG`
- `ORG`
- `Student` (regular student account)

## Currently Available Reports

| Report Title | Purpose | Metric / Formula | Useful Filters | Role Visibility (Current Behavior) | Function / Endpoint | Source File | Primary Owner |
|---|---|---|---|---|---|---|---|
| Event Attendance Summary | Quick health check of one event | Attendance Rate = (Completed Present + Completed Late) / Total Participants | Event, Governance Context | Admin, Campus Admin, SSG/SG/ORG (with `manage_attendance`, scoped) | `get_event_attendance_report` (`GET /api/attendance/events/{event_id}/report`) | `Backend/app/routers/attendance/reports.py` | School IT |
| Event Program Breakdown | Compare outcomes across programs | Per program: Present, Late, Incomplete, Absent counts and rate | Event, Program | Admin, Campus Admin, SSG/SG/ORG (with `manage_attendance`, scoped) | `get_event_attendance_report` (`GET /api/attendance/events/{event_id}/report`) | `Backend/app/routers/attendance/reports.py` | School IT |
| Event Attendee Roster | Show who has attendance records in an event | Student-level attendance rows | Event, Status, Pagination | Admin, Campus Admin, SSG/SG/ORG (with `manage_attendance`, scoped) | `get_event_attendees` (`GET /api/attendance/events/{event_id}/attendees`), `get_attendances_with_students` (`GET /api/attendance/events/{event_id}/attendances-with-students`) | `Backend/app/routers/attendance/records.py` | School IT / SSG |
| Event Status Mix | See attendance quality distribution for an event | Status percentage per status = Count / Event Total | Event | Admin, Campus Admin, SSG/SG/ORG (with `manage_attendance`, scoped) | Derived from `get_event_attendance_report` (`GET /api/attendance/events/{event_id}/report`) | `Backend/app/routers/attendance/reports.py` | School IT |
| Event Late Burden | Measure tardiness in an event | Late Rate = Late / Total Participants | Event | Admin, Campus Admin, SSG/SG/ORG (with `manage_attendance`, scoped) | Derived from `get_event_attendance_report` (`GET /api/attendance/events/{event_id}/report`) | `Backend/app/routers/attendance/reports.py` | School IT |
| Event Incomplete Sign-Out Report | Detect sign-out process gaps | Incomplete Rate = Incomplete / Total Participants | Event | Admin, Campus Admin, SSG/SG/ORG (with `manage_attendance`, scoped) | Derived from `get_event_attendance_report` (`GET /api/attendance/events/{event_id}/report`) | `Backend/app/routers/attendance/reports.py` | School IT / SSG |
| Student Attendance Overview List | Scan all students quickly | Per student: Total Events, Attendance Rate, Last Attendance | Department, Program, Date Range, Search | Admin, Campus Admin, SSG/SG/ORG (with `manage_attendance`, scoped) | `get_students_attendance_overview` (`GET /api/attendance/students/overview`) | `Backend/app/routers/attendance/reports.py` | School IT |
| Student Attendance Performance Card | Full summary for one student | Attended, Late, Incomplete, Absent, Excused, Rate | Student, Date Range, Event Type | Admin, Campus Admin, SSG/SG/ORG (with `manage_attendance`, scoped), Student (own report only) | `get_student_attendance_report` (`GET /api/attendance/students/{student_id}/report`) | `Backend/app/routers/attendance/reports.py` | School IT / Advisers |
| Student Attendance Event Log | Auditable event-by-event history | Detailed rows with status and timestamps | Student, Date Range, Status | Admin, Campus Admin, SSG/SG/ORG (with `manage_attendance`, scoped), Student (own records only) | `get_student_attendance_report` (`GET /api/attendance/students/{student_id}/report`), `get_student_attendance_records` (`GET /api/attendance/students/{student_id}/records`) | `Backend/app/routers/attendance/reports.py`, `Backend/app/routers/attendance/records.py` | School IT |
| Student Monthly Attendance Trend | Monitor progress over time | Monthly status counts | Student, Date Range | Admin, Campus Admin, SSG/SG/ORG (with `manage_attendance`, scoped), Student (own report only) | `get_student_attendance_report` (`GET /api/attendance/students/{student_id}/report`) | `Backend/app/routers/attendance/reports.py` | School IT / SSG |
| Student Event-Type Attendance Mix | See behavior by event category | Count by event type | Student, Date Range | Admin, Campus Admin, SSG/SG/ORG (with `manage_attendance`, scoped), Student (own report only) | `get_student_attendance_report` and `get_student_attendance_stats` (`GET /api/attendance/students/{student_id}/report`, `GET /api/attendance/students/{student_id}/stats`) | `Backend/app/routers/attendance/reports.py` | School IT / SSG |
| Student Status Distribution | Snapshot of one student's status split | Present/Late/Absent/Excused counts | Student, Date Range | Admin, Campus Admin, SSG/SG/ORG (with `manage_attendance`, scoped), Student (own stats only) | `get_student_attendance_stats` (`GET /api/attendance/students/{student_id}/stats`) | `Backend/app/routers/attendance/reports.py` | School IT |
| Student Trend by Period | Time-series tracking | Trend count by day/week/month/year and status | Student, Group By, Date Range | Admin, Campus Admin, SSG/SG/ORG (with `manage_attendance`, scoped), Student (own stats only) | `get_student_attendance_stats` (`GET /api/attendance/students/{student_id}/stats`) | `Backend/app/routers/attendance/reports.py` | School IT |
| School Attendance Summary | Overall school attendance snapshot | Total records, status counts, attended count, attendance rate | Date Range, Department, Program | Admin, Campus Admin, SSG/SG/ORG (with `manage_attendance`, scoped) | `get_attendance_summary` (`GET /api/attendance/summary`) | `Backend/app/routers/attendance/reports.py` | School IT / Campus Admin |
| School Unique Student Participation | Measure student reach | Unique Students with attendance records | Date Range, Department, Program | Admin, Campus Admin, SSG/SG/ORG (with `manage_attendance`, scoped) | Derived from `get_attendance_summary` (`GET /api/attendance/summary`) | `Backend/app/routers/attendance/reports.py` | School IT |
| School Unique Event Coverage | Measure event coverage | Unique Events with attendance records | Date Range, Department, Program | Admin, Campus Admin, SSG/SG/ORG (with `manage_attendance`, scoped) | Derived from `get_attendance_summary` (`GET /api/attendance/summary`) | `Backend/app/routers/attendance/reports.py` | School IT |
| Department Attendance Slice | Department-level attendance quality | Status counts and rate for selected department | Department, Date Range | Admin, Campus Admin, SSG/SG/ORG (with `manage_attendance`, scoped) | `get_attendance_summary` (`GET /api/attendance/summary?department_id=...`) | `Backend/app/routers/attendance/reports.py` | School IT / Department Heads |
| Program Attendance Slice | Program-level attendance quality | Status counts and rate for selected program | Program, Date Range | Admin, Campus Admin, SSG/SG/ORG (with `manage_attendance`, scoped) | `get_attendance_summary` (`GET /api/attendance/summary?program_id=...`) | `Backend/app/routers/attendance/reports.py` | School IT / Program Chairs |
| Student Record Collection | Pull records for selected students | Grouped attendance rows by student | Student IDs, Event, Status | Admin, Campus Admin, SSG/SG/ORG (with `manage_attendance`, scoped) | `get_all_student_attendance_records` (`GET /api/attendance/students/records`) | `Backend/app/routers/attendance/records.py` | School IT |
| Personal Attendance History | Student self-service transparency | Own attendance records and statuses | Event, Status, Date Range | Student (own data only); also usable by SSG/SG/ORG users for their own student profile | `get_my_attendance_records` (`GET /api/attendance/me/records`) | `Backend/app/routers/attendance/records.py` | Student / SSG |
| Import Preview Quality Report | Validate import readiness before commit | Total Rows, Valid Rows, Invalid Rows, Can Commit | File, Preview Token | Admin, Campus Admin | `preview_import_students` (`POST /api/admin/import-students/preview`) | `Backend/app/routers/admin_import.py` | School IT |
| Import Job Progress Report | Track bulk import execution | Processed, Success, Failed, Percentage, ETA | Job ID | Admin, Campus Admin | `get_import_status` (`GET /api/admin/import-status/{job_id}`) | `Backend/app/routers/admin_import.py` | School IT |
| Import Failed Rows Report | Resolve failed imports | Failed row list with reasons | Job ID | Admin, Campus Admin | `download_import_errors` (`GET /api/admin/import-errors/{job_id}/download`) and `get_import_status` (`GET /api/admin/import-status/{job_id}`) | `Backend/app/routers/admin_import.py` | School IT |
| Audit Activity Report | Accountability and governance | Total actions and detailed logs | Date Range, Actor, Action, Status, Search | Admin, Campus Admin | `search_audit_logs` (`GET /api/audit-logs`) | `Backend/app/routers/audit_logs.py` | Campus Admin / School IT |
| Notification Log Report | Check delivery behavior | Notification entries by category/channel/status | Category, Status, User, Limit | Admin, Campus Admin | `list_notification_logs` (`GET /api/notifications/logs`) | `Backend/app/routers/notifications.py` | School IT |
| Notification Dispatch Outcome | Monitor campaign results | Processed, Sent, Failed, Skipped | Dispatch Type, School, Parameters | Admin, Campus Admin | `dispatch_missed_events_notifications`, `dispatch_low_attendance_alerts`, `dispatch_event_reminders` (`POST /api/notifications/dispatch/*`) | `Backend/app/routers/notifications.py` | School IT |
| Governance Unit Dashboard Overview | Unit-level governance monitoring | Published Announcements, Total Students, Recent Announcements, Child Units | Governance Unit | Admin, Campus Admin, SSG, SG, ORG (unit access required) | `get_governance_dashboard_overview` (`GET /api/governance/units/{governance_unit_id}/dashboard-overview`) | `Backend/app/routers/governance_hierarchy.py` | SSG / SG / Campus Admin |
| Data Retention Run Summary | Data compliance monitoring | Deleted Audit Logs, Import Logs, Notifications | School, Dry Run Flag | Admin, Campus Admin | `run_retention_cleanup` (`POST /api/governance/run-retention`) | `Backend/app/routers/governance.py` | Campus Admin |

## Recommended Additional Reports

| Report Title | Purpose | Metric / Formula | Useful Filters | Recommended Role Visibility | Primary Owner |
|---|---|---|---|---|---|
| At-Risk Attendance List | Identify students needing intervention | At Risk if Attendance Rate < threshold and minimum events met | Department, Program, Date Range, Threshold | Admin, Campus Admin, SSG/SG/ORG (with `manage_attendance`, scoped) | School IT / Advisers |
| Top Absentees | Prioritize follow-up | Ranked by Absent Count | Date Range, Department, Program | Admin, Campus Admin, SSG/SG/ORG (with `manage_attendance`, scoped) | SSG / Advisers |
| Top Late Students | Improve punctuality | Ranked by Late Count or Late Rate | Date Range, Department, Program | Admin, Campus Admin, SSG/SG/ORG (with `manage_attendance`, scoped) | SSG / Advisers |
| Attendance Leaderboard | Recognize high performers | Ranked by Attendance Rate with minimum event count | Date Range, Department, Program | Admin, Campus Admin, SSG/SG/ORG (with `manage_attendance`, scoped), Student (view-only) | SSG |
| Attendance Recovery Report | Track improvement | Rate Change = Current Period Rate - Previous Period Rate | Compare Period A vs B | Admin, Campus Admin, SSG/SG/ORG (with `manage_attendance`, scoped) | School IT / Advisers |
| Attendance Decline Alert | Early warning of drop-offs | Negative Rate Change beyond threshold | Compare Period A vs B | Admin, Campus Admin, SSG/SG/ORG (with `manage_attendance`, scoped) | School IT / Advisers |
| No-Show Event Report | Flag weak event attendance | No-Show Rate = Absent / Total Participants | Event, Date Range, Program/Department | Admin, Campus Admin, SSG/SG/ORG (with `manage_attendance`, scoped) | School IT / Event Leads |
| Event Execution Quality Report | Detect attendance flow problems | Incomplete Rate and late sign-out pattern | Event, Date Range | Admin, Campus Admin, SSG/SG/ORG (with `manage_attendance`, scoped) | School IT |
| Event Completion vs Cancellation Report | Track event outcomes at a glance | Completed Count, Cancelled Count, Completion Rate = Completed / (Completed + Cancelled), Cancellation Rate = Cancelled / (Completed + Cancelled) | Date Range, Governance Context, Department, Program, Event Type | Admin, Campus Admin, SSG/SG/ORG (scoped) | School IT / SSG |
| Attendance by Day of Week | Find low-attendance weekdays | Status counts and attendance rate by weekday | Date Range, Department, Program | Admin, Campus Admin, SSG/SG/ORG (with `manage_attendance`, scoped) | School IT / Planners |
| Attendance by Time Block | Understand late check-in patterns | Late frequency by time block | Date Range, Event Type | Admin, Campus Admin, SSG/SG/ORG (with `manage_attendance`, scoped) | School IT |
| Year Level Attendance Distribution | Compare year cohorts | Attendance rate and status counts by year level | Date Range, Department, Program | Admin, Campus Admin, SSG/SG/ORG (with `manage_attendance`, scoped) | School IT / Advisers |
| Repeat Participation Report | Measure engagement depth | Events per student distribution | Date Range, Department, Program | Admin, Campus Admin, SSG/SG/ORG (with `manage_attendance`, scoped) | SSG / School IT |
| First-Time vs Repeat Attendee Report | Measure new engagement | First-time attendee count vs repeat attendee count | Event, Date Range | Admin, Campus Admin, SSG/SG/ORG (with `manage_attendance`, scoped) | SSG / Event Leads |
| School KPI Dashboard Report | Executive overview | Attendance Rate, Late Rate, Absent Rate, Incomplete Rate, Participation Reach | Date Range, Department, Program | Admin, Campus Admin, SSG (school-wide visibility), SG/ORG (scoped view) | Campus Admin |

## Access Notes

- `SSG`, `SG`, and `ORG` report access is governance-permission-based, not just role name. They need `manage_attendance` for attendance management reports.
- Governance report scope is restricted by unit scope:
  - `SSG`: school-wide
  - `SG`: department-scoped
  - `ORG`: organization/program-scoped
- `Student` access is mostly own-data only.
- Multiple roles can see the same report, with different scope limits.



