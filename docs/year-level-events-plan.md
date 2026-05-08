# Year Level Event Targeting Plan

Date: 2026-05-08
Status: Analysis only. No behavior changes implemented.

## Goal

Understand the current Aura backend and frontend event, attendance, report, import, and RBAC flows before implementing year-level event targeting.

## 1. Current Relevant Files

### Backend models

- `backend/app/models/event.py`
- `backend/app/models/user.py`
- `backend/app/models/attendance.py`
- `backend/app/models/associations.py`
- `backend/app/models/governance_hierarchy.py`

### Backend schemas

- `backend/app/schemas/event.py`
- `backend/app/schemas/user.py`
- `backend/app/schemas/attendance.py`
- `backend/app/schemas/public_attendance.py`

### Backend event routers and shared logic

- `backend/app/routers/events/crud.py`
- `backend/app/routers/events/queries.py`
- `backend/app/routers/events/workflow.py`
- `backend/app/routers/events/attendance_queries.py`
- `backend/app/routers/events/shared.py`

### Backend attendance routers and services

- `backend/app/routers/attendance/check_in_out.py`
- `backend/app/routers/attendance/shared.py`
- `backend/app/routers/public_attendance.py`
- `backend/app/services/attendance_face_scan.py`
- `backend/app/services/event_attendance_service.py`
- `backend/app/services/event_time_status.py`
- `backend/app/services/event_workflow_status.py`

### Backend reports

- `backend/app/reports/attendance/router.py`
- `backend/app/reports/attendance/service.py`
- `backend/app/reports/attendance/queries.py`
- `backend/app/reports/student/router.py`
- `backend/app/reports/student/service.py`
- `backend/app/reports/student/queries.py`
- `backend/app/reports/school/service.py`
- `backend/app/reports/school/queries.py`

### Backend import and RBAC

- `backend/app/routers/admin_import.py`
- `backend/app/services/student_import_service.py`
- `backend/app/services/import_validation_service.py`
- `backend/app/core/security.py`
- `backend/app/services/governance_hierarchy_service/shared.py`

### Backend migration setup

- `backend/alembic/env.py`
- `backend/alembic/schema.sql`
- `backend/alembic/versions/0001_baseline_normalized_schema.py`
- `backend/alembic/versions/0002_reports_user_demographics.py`

### Frontend event creation/editing

- `frontend-web/src/components/events/EventEditorSheet.vue`
- `frontend-web/src/services/eventEditor.js`
- `frontend-web/src/views/dashboard/GovernanceWorkspaceView.vue`
- `frontend-web/src/views/dashboard/SgEventsView.vue`
- `frontend-web/src/services/backendApi.js`

### Frontend student and scanner flows

- `frontend-web/src/views/dashboard/HomeView.vue`
- `frontend-web/src/views/dashboard/GatherAttendanceView.vue`
- `frontend-web/src/composables/useGatherAttendance.js`
- `frontend-web/src/views/auth/QuickAttendanceView.vue`
- `frontend-web/src/composables/useGatherKiosk.js`

### Frontend student management and import-adjacent screens

- `frontend-web/src/views/dashboard/SchoolItImportStudentsView.vue`
- `frontend-web/src/views/dashboard/SchoolItProgramStudentsView.vue`
- `frontend-web/src/views/dashboard/SchoolItUnassignedStudentsView.vue`
- `frontend-web/src/views/dashboard/SgStudentsView.vue`

### Existing tests

- `backend/tests/test_events.py`
- `backend/tests/test_events_extended.py`
- `backend/tests/test_events_workflow.py`
- `backend/tests/test_attendance.py`
- `backend/tests/test_attendance_extended.py`
- `backend/tests/test_public_attendance.py`
- `backend/tests/test_reports.py`
- `backend/tests/test_rbac_matrix.py`
- `backend/tests/test_bulk_import.py`
- `backend/tests/test_admin_import.py`
- `backend/tests/test_migrations.py`

## 2. Existing Event Model Structure

Current event scoping is department/program based only.

### Data model

`backend/app/models/event.py`

- `Event.id`
- `Event.school_id`
- `Event.event_type_id`
- `Event.created_by_user_id`
- `Event.name`
- `Event.location`
- geofence fields:
  - `geo_latitude`
  - `geo_longitude`
  - `geo_radius_m`
  - `geo_required`
  - `geo_max_accuracy_m`
- attendance timing fields:
  - `early_check_in_minutes`
  - `late_threshold_minutes`
  - `sign_out_grace_minutes`
  - `sign_out_open_delay_minutes`
  - `sign_out_override_until`
  - `present_until_override_at`
  - `late_until_override_at`
- schedule fields:
  - `start_at`
  - `end_at`
- workflow field:
  - `status`
- relationships:
  - `departments`
  - `programs`
  - `attendance_records`
  - `event_type`

### Association tables

`backend/app/models/associations.py`

- `event_departments(event_id, department_id)`
- `event_programs(event_id, program_id)`

There is no event-to-year-level association table yet.

### API schema shape

`backend/app/schemas/event.py`

- `EventCreate` accepts:
  - core event fields
  - `department_ids: List[int]`
  - `program_ids: List[int]`
- `EventUpdate` accepts optional:
  - core event fields
  - `department_ids: Optional[List[int]]`
  - `program_ids: Optional[List[int]]`
- `Event` response exposes:
  - nested `departments`
  - nested `programs`
  - computed `department_ids`
  - computed `program_ids`

There is no `year_level_ids`, `year_levels`, or equivalent event-targeting field in the schema today.

### Event create/update behavior

`backend/app/routers/events/crud.py`

- Create:
  - validates schedule and geofence
  - resolves governance scope
  - writes the event row
  - attaches departments/programs from payload or governance context
- Update:
  - reloads event with departments/programs
  - validates timing and geofence changes
  - replaces department/program associations if provided

Important: year-level targeting cannot be added only at read time. It must be threaded into event create/update persistence and event query responses.

## 3. Existing Student/User Model Structure

### User

`backend/app/models/user.py`

- `User` holds identity, auth, school, and role assignment.
- roles are attached through `UserRole`.

### Student profile

`backend/app/models/user.py`

- `StudentProfile.id`
- `StudentProfile.user_id`
- `StudentProfile.school_id`
- `StudentProfile.student_number`
- `StudentProfile.department_id`
- `StudentProfile.program_id`
- `StudentProfile.year_level`
- `StudentProfile.section`
- `StudentProfile.rfid_tag`

Key finding: `year_level` already exists and is required at the model/schema level for students.

### Student-facing schemas

`backend/app/schemas/user.py`

- student creation and profile schemas already include `year_level`
- user filters already expose optional `year_level`

### Existing student-scope logic

Current scope matching logic generally uses:

- department only
- program only
- department + program

It does not currently include year level in:

- event visibility checks
- event participant derivation
- event attendance eligibility
- public attendance face-scan audience matching
- governance event scope matching

## 4. Existing Attendance Flow

### Operator attendance flow

`backend/app/routers/attendance/check_in_out.py`

- Attendance is recorded against `student_profile.id` and `event.id`.
- Sign-in and sign-out share the same event and student lookup path.
- The router checks:
  - operator permission
  - event school scope
  - governance attendance scope
  - whether the student is inside event participant scope
  - whether current event time window allows sign-in or sign-out

### Event participant matching

`backend/app/routers/attendance/shared.py`

- `_ensure_student_is_event_participant(student, event)` currently checks:
  - event program scope
  - event department scope
- It does not check `student.year_level`.

### Participant list derivation

`backend/app/services/event_attendance_service.py`

- `get_event_participant_student_ids(db, event)` builds the event audience from school students.
- It filters by:
  - `StudentProfile.program_id`
  - `StudentProfile.department_id`
- It does not filter by `StudentProfile.year_level`.

This service is one of the main backend insertion points for year-level targeting.

### Public attendance / Gather / kiosk flow

`backend/app/routers/public_attendance.py`
`backend/app/services/attendance_face_scan.py`

- nearby events are listed for the public scanner
- the scanner submits a multi-face scan for one event
- face matching is intentionally scoped to valid students for the selected event
- event audience is resolved through `get_registered_face_candidates_for_event()`
- out-of-scope handling distinguishes:
  - in scope
  - out of scope
  - no match

Important detail:

- public face matching does not simply match against the whole school first
- it tries to resolve event-valid students and then reports `out_of_scope` when a school match exists outside the event audience

Any year-level targeting must be applied consistently to:

- participant derivation
- public attendance scope label
- public face candidate generation
- out-of-scope messaging

### Attendance finalization

`backend/app/services/event_attendance_service.py`

- `finalize_completed_event_attendance()` derives participant IDs from event scope
- creates absent rows for missing participants
- auto-closes incomplete rows

If participant scope changes, attendance finalization behavior also changes.

## 5. Existing Report Flow

### Event attendance report

`backend/app/reports/attendance/service.py`
`backend/app/reports/attendance/queries.py`

- Event report reloads the event with departments/programs.
- It builds a participant subquery from school students.
- Participant filtering currently uses only:
  - `program_ids`
  - `department_ids`
- Report totals, absentees, and breakdowns depend on that participant set.

Impact:

- year-level targeting is not just a display concern
- it directly changes total participants, absentees, attendance rate, and program breakdown

### Student overview and student report

`backend/app/reports/student/service.py`
`backend/app/reports/student/queries.py`

- student rows already expose `year_level`
- attendance overview supports filtering by department/program today
- reports consume allowed event IDs from attendance governance scope

Current gap:

- student reports know the student year level
- event-level audience building does not use year level yet

### School summary

`backend/app/reports/school/service.py`

- school attendance summary supports department/program filters
- student login rows already return `year_level`

Potential future extension:

- school summary filters may eventually need optional year-level filters too
- that is separate from event targeting, but related enough to plan for

## 6. Existing Frontend Event Form Flow

### Shared event editor UI

`frontend-web/src/components/events/EventEditorSheet.vue`
`frontend-web/src/services/eventEditor.js`

- shared sheet edits:
  - name
  - schedule
  - geofence
  - attendance timing
- draft builder and payload builder do not expose any audience-targeting fields
- no department/program/year-level picker exists in the reusable editor

### Governance event creation/editing

`frontend-web/src/views/dashboard/GovernanceWorkspaceView.vue`

- create uses shared `EventEditorSheet`
- screen injects scope through `buildScopedEventPayload(payload)`
- current injected scope:
  - `department_ids`
  - `program_ids`
- edit uses `updateEvent(...)` with governance context params
- create uses `createGovernanceEvent(...)`

### Governance fallback resolver

`frontend-web/src/views/dashboard/SgEventsView.vue`

- builds candidate create attempts across governance contexts
- injects department/program scope depending on resolved governance unit detail
- does not include year-level scope in payload construction

### Student dashboard visibility

`frontend-web/src/views/dashboard/HomeView.vue`

- student home consumes already-filtered event data
- frontend search includes event names, location, departments, programs
- frontend is not applying year-level event visibility itself
- student visibility is primarily backend-driven

### Gather / scanner UI

`frontend-web/src/views/dashboard/GatherAttendanceView.vue`
`frontend-web/src/composables/useGatherAttendance.js`
`frontend-web/src/composables/useGatherKiosk.js`

- scanner chooses from available candidate events
- selected event shows `scope_label`
- event submit flow depends on backend event eligibility and public-attendance response

Frontend implication:

- once backend returns a year-level-aware scope label, Gather can display it
- if product wants year level visible before scanning, normalizers and selection card copy will need to expose it

## 7. Event Approval Logic

There is no separate event approval workflow in the inspected current implementation.

Current event workflow covers:

- event create/update/delete
- status transitions
- time-based workflow sync
- early sign-out opening

`backend/app/routers/events/workflow.py` handles status changes, but there is no dedicated approval state or approval router for events at this time.

If year-level targeting is introduced, no approval-specific backend branch currently needs to be updated unless an approval workflow is added later.

## 8. Student Bulk Import Logic

### Import API

`backend/app/routers/admin_import.py`

- preview file
- validate rows
- store approved preview manifest
- queue import
- retry failed rows

### Import service

`backend/app/services/student_import_service.py`

- processes rows in chunks
- builds validation context from school departments/programs
- inserts students in bulk

### Important data dependency

Student records already carry `year_level`, so year-level event targeting can rely on existing imported data.

Main risk:

- if year-level values are inconsistent, null, or poorly normalized across older imported records, event targeting may exclude intended students

Implementation note:

- before rollout, audit real student data quality for `student_profiles.year_level`
- if needed, add validation/backfill work separately from event-targeting delivery

## 9. RBAC / Permissions Logic

### Core auth roles

`backend/app/core/security.py`

- role checks are centralized with normalized role names
- event and attendance APIs rely on:
  - `admin`
  - `campus_admin`
  - governance roles
  - `student`

### Governance permissions

`backend/app/routers/events/shared.py`
`backend/app/routers/attendance/shared.py`

- event management uses `PermissionCode.MANAGE_EVENTS`
- attendance management uses `PermissionCode.MANAGE_ATTENDANCE`
- governance scope matching is currently department/program based

Important risk:

- year-level event targeting is not the same as governance scope
- do not accidentally blend governance-unit permissions with event audience targeting unless product explicitly wants year-level governance scopes too

Safe assumption for now:

- governance write permissions stay as they are
- year level is an event audience filter, not a governance-unit permission dimension

## 10. Alembic Migration Setup

### Current setup

`backend/alembic/env.py`

- Alembic loads app metadata
- metadata comes from the app model base
- migrations read `DATABASE_URL` or configured settings

### Current migration shape

- `0001_baseline_normalized_schema.py` replays `backend/alembic/schema.sql`
- `0002_reports_user_demographics.py` adds reporting/demographic tables and user age/gender

Key risk:

- baseline is SQL-file driven, while later changes are standard Alembic operations
- a year-level event-targeting migration should be created as a normal forward migration
- do not edit baseline or schema snapshot for an incremental feature

Likely migration need:

- a new association table for event-to-year-level mapping, or
- an alternative event target structure if product prefers a different schema

## 11. Existing Tests

### What exists now

- event CRUD and workflow tests
- attendance tests
- public attendance tests
- reports tests
- migration head test
- RBAC matrix tests
- import tests

### What current tests do not appear to cover well

- department/program audience edge cases in deep combinations
- public attendance out-of-scope behavior with multiple audience dimensions
- event report totals under mixed audience filters
- create/edit frontend audience-targeting inputs

Year-level targeting will need fresh coverage in those areas.

## 12. Recommended Implementation Order

### Phase 1: backend data model and schema

1. Add persistent event year-level targeting structure.
2. Extend SQLAlchemy models and event schemas.
3. Add migration for the new storage.

### Phase 2: backend event write/read paths

1. Update event create/update routers to persist year-level targeting.
2. Update event query responses to expose year-level targeting.
3. Add any scope-label helpers needed for frontend display.

### Phase 3: backend participant and attendance logic

1. Update `get_event_participant_student_ids()`.
2. Update `_ensure_student_is_event_participant()`.
3. Update public attendance face candidate scoping and out-of-scope behavior.
4. Verify completed-event finalization still produces correct absent rows.

### Phase 4: backend reports

1. Update event attendance report participant subquery.
2. Recheck student and school report assumptions.
3. Decide whether report filters should also expose year-level filtering now or later.

### Phase 5: frontend event forms

1. Extend shared event editor draft/payload support.
2. Add year-level target UI to create/edit flows.
3. Thread values through governance create/edit wrappers.

### Phase 6: frontend display surfaces

1. Update event detail/scope label rendering if needed.
2. Update student dashboard/event cards if audience metadata should be visible.
3. Update Gather/public-attendance labels if product wants year-level scope shown.

### Phase 7: tests

1. Add migration coverage.
2. Add event CRUD coverage for year-level targets.
3. Add attendance and public-attendance scope tests.
4. Add report participant-total tests.
5. Add frontend unit/integration coverage where available.

## 13. Risks and Files That Must Be Edited Carefully

### Highest-risk backend files

- `backend/app/services/event_attendance_service.py`
  - drives participants, absentees, and completed-event finalization
- `backend/app/services/attendance_face_scan.py`
  - drives public face-scan eligibility and out-of-scope detection
- `backend/app/routers/attendance/shared.py`
  - operator attendance guardrails depend on event participant checks
- `backend/app/reports/attendance/queries.py`
  - event report totals depend on participant subquery accuracy
- `backend/app/routers/events/crud.py`
  - create/update persistence must stay compatible with governance scoping

### Highest-risk frontend files

- `frontend-web/src/components/events/EventEditorSheet.vue`
  - shared event editor used by multiple flows
- `frontend-web/src/services/eventEditor.js`
  - central payload builder for create/edit form state
- `frontend-web/src/views/dashboard/GovernanceWorkspaceView.vue`
  - active governance event creation/edit flow
- `frontend-web/src/views/dashboard/SgEventsView.vue`
  - governance fallback scope resolution is easy to break if payload shape changes
- `frontend-web/src/composables/useGatherAttendance.js`
  - scanner event selection and UX copy depend on backend event scope

### Data and rollout risks

- legacy student data quality for `year_level`
- mixing governance scope rules with event audience rules
- changing participant counts will affect:
  - absentees
  - attendance rates
  - sanctions
  - public scan out-of-scope responses
- incomplete migration strategy could leave old events without a clear default audience interpretation

## 14. Recommended Implementation Direction

Recommended direction:

- keep current department/program event targeting behavior intact
- add year-level as an additional optional audience filter
- treat empty year-level targeting as “all year levels inside the existing department/program scope”
- centralize participant resolution in one backend service and reuse that everywhere

This keeps the rollout safer because it extends the current model instead of replacing event scope behavior.

