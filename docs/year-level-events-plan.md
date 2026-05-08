# Year Level Event Targeting Plan

## Phase 1: Student Metadata Stabilization (COMPLETED)
- [x] **Add `year_level` to `StudentProfile`** (1-5, default 1).
- [x] **Add `student_status` Enum to `StudentProfile`** (ACTIVE, GRADUATED, etc.).
- [x] **Add `promotion_locked` boolean** (default false).
- [x] **Update API Schemas** to include new fields.
- [x] **Update Student Management Routers** to handle persistence and validation.
- [x] **Update Serialization Helpers** to ensure API responses include new metadata.

## Phase 2: Student Bulk Import Update (COMPLETED)
- [x] **Add `Year Level` and `Status` columns** to import template.
- [x] **Implement row-level validation** for year level (1-5) and status (ACTIVE, etc.).
- [x] **Maintain backward compatibility** for legacy 7-column templates.
- [x] **Update Frontend Preview** to display new fields and validation tags.

## Phase 3: Event Targeting Infrastructure (COMPLETED)
- [x] **Database Migration:** Created `event_targets` table with scope-based targeting.
- [x] **Backend Models:** Implemented `EventTarget` and `EventTargetScope`.

## Phase 4: Event Targeting API Integration (COMPLETED)
- [x] **Backend Schemas:** Updated `EventCreate`, `EventUpdate`, and `Event` response to use `event_targets`.
- [x] **Backend CRUD:** Implemented transaction-safe create/update with backward compatibility for legacy IDs.
- [x] **Attendance Validation:** Updated participant check to enforce targeting rules (Year Level, Department, Course).
- [x] **Documentation:** Updated backend implementation guide.

## Phase 5: Centralized Eligibility Service (COMPLETED)
- [x] **Service Implementation:** Created `EventEligibilityService` to centralize student validation logic.
- [x] **Refactoring:** Updated attendance and event routers to use the centralized service.
- [x] **Standardized Errors:** Implemented rejection codes (`STUDENT_NOT_ACTIVE`, `STUDENT_NOT_INCLUDED_IN_EVENT_SCOPE`, etc.).
- [x] **Documentation:** Created `docs/attendance-eligibility.md`.

## Phase 6: Student Dashboard Filtering (COMPLETED)
- [x] **Backend Optimization:** Updated event queries to include `event_targets` via `joinedload`.
- [x] **Dashboard Enforcement:** Integrated the eligibility checker into the Student Dashboard event list.
- [x] **Frontend Polish:** Added "No upcoming events assigned to you" message in `EventsCard.vue`.

## Phase 7: Attendance Enforcement (COMPLETED)
- [x] **Backend Hardening:** Integrated `EventEligibilityService` into Face Scan, Manual Attendance, and Bulk Import routers.
- [x] **Strict Rejection:** Enforced HTTP 403 responses with code `STUDENT_NOT_INCLUDED_IN_EVENT_SCOPE`.
- [x] **Frontend Polish:** Updated scanner and kiosk UI to display user-friendly "Not included in this event" messages.

## Phase 8: Attendance Reports Update (COMPLETED)
- [x] **Logic Update:** Re-implemented expected/absent calculations based on `event_targets` and `ACTIVE` status.
- [x] **New Metrics:** Added "Signed-out" and "No sign-out" student tracking to event reports.
- [x] **Dynamic Filtering:** Added Year Level, Department, Course, and Status filters to all attendance report endpoints.
- [x] **Historical Integrity:** Ensured graduated/inactive students are excluded from expected lists but remain visible in actual attendance records.

## Phase 9: Event Announcement Notifications (COMPLETED)
- [x] **`dispatch_event_announcement_notifications`**: New service function in `notification_center_service.py`. Uses `get_event_participant_student_ids` to resolve eligible recipients — enforces `ACTIVE` status, `event_targets` scope, and school boundary.
- [x] **`POST /api/notifications/dispatch/event-announcement/{event_id}`**: New router endpoint. Requires `campus_admin` or `admin`. Enforces school boundary (404 if event belongs to a different school).
- [x] **`dispatch_event_reminder_notifications` fix**: Added `joinedload(Event.event_targets, Event.programs, Event.departments)` to the event query to prevent N+1 and ensure correct scope resolution.
- [x] **Tests**: `backend/tests/test_event_announcement_notifications.py` — 11 test cases covering YEAR_LEVEL, COURSE_YEAR, GRADUATED exclusion, INACTIVE exclusion, TRANSFERRED exclusion, out-of-scope exclusion, ALL scope, empty participant list, school boundary (HTTP 404), RBAC (HTTP 403), and auth guard (HTTP 401).
- [x] **Documentation**: Updated `docs/event-targeting.md` and `docs/year-level-events-plan.md`.

## Phase 10: Event Creation UI Controls (COMPLETED)
- [x] **`eventEditor.js`**: Added `AUDIENCE_SCOPE_OPTIONS`, `YEAR_LEVEL_OPTIONS`, `scopeNeedsYearLevel`, `scopeNeedsDepartment`, `scopeNeedsCourse`, `buildEventTargetsFromDraft`, and `audienceDraftFromEventTargets`. Updated `createEventEditorDraft` to hydrate audience fields from `event.event_targets`. Updated `buildEventUpdatePayloadFromDraft` to include `event_targets` in the payload.
- [x] **`EventEditorSheet.vue`**: Added `departments` and `programs` props. Added Audience section with scope selector and conditional year-level, department, and course dropdowns. Imported `Users` icon and audience helpers from `eventEditor.js`.
- [x] **`SgEventsView.vue`**: Added `cachedDepartments` and `cachedPrograms` state. Loads departments and programs on `loadEvents` (best-effort, non-blocking). Passes them to `EventEditorSheet`. Added audience fields to `form` ref and `resetEventForm`. Wires `buildEventTargetsFromDraft` into `buildCreateEventPayload`.
- [x] **Tests**: `frontend-web/tests/unit/services/eventEditor.spec.js` — 30 test cases covering scope predicates, option arrays, `buildEventTargetsFromDraft` for all six scopes (valid + invalid), and `createEventEditorDraft` audience hydration.

## Phase 11: Target Scope RBAC Enforcement (COMPLETED)
- [x] **`app/services/event_target_permissions.py`** (new): `validate_event_targets_for_actor` — enforces which `EventTargetScope` values each governance role may use. Campus Admin/Admin: unrestricted. SSG: ALL + YEAR_LEVEL. SG: DEPARTMENT + DEPARTMENT_YEAR (own dept only). ORG: COURSE + COURSE_YEAR (own program only). Returns HTTP 403 with a descriptive message on violation.
- [x] **`app/routers/events/crud.py`**: `create_event` calls `validate_event_targets_for_actor` after `_ensure_event_manager`, before any DB writes. `update_event` calls it when `event_targets` is explicitly provided in the patch payload.
- [x] **`app/routers/events/shared.py`**: Added `validate_event_targets_for_actor` import.
- [x] **Tests**: `backend/tests/test_event_target_permissions.py` — 28 test cases: pure unit tests for all role/scope combinations (SSG, SG, ORG, campus_admin, empty targets, no units) + HTTP integration tests (campus_admin ALL/YEAR_LEVEL create, student 403, unauthenticated 401, campus_admin update targets).
- [x] **Documentation**: Updated `docs/event-targeting.md` and `docs/year-level-events-plan.md`.

## Phase 12: Rejected Scan Audit Logging (COMPLETED)
- [x] **Architecture decision**: Used the existing `SchoolAuditLog` table (`school_audit_logs`) — no new table, no migration, zero schema risk.
- [x] **`app/routers/attendance/shared.py`**: Added `_log_rejected_scan_attempt` (writes a `SchoolAuditLog` row; DB errors are caught and logged as warnings, never propagated). Added `_ensure_student_is_event_participant_with_audit` (calls eligibility check, logs on rejection, re-raises HTTP 403 unchanged).
- [x] **`app/routers/attendance/check_in_out.py`**: `record_face_scan_attendance` now calls `_ensure_student_is_event_participant_with_audit` with `attempt_type="SIGN_IN"`. `record_manual_attendance` calls it with `attempt_type="MANUAL"`.
- [x] **Tests**: `backend/tests/test_scan_audit_log.py` — 10 test cases: audit row written on rejection, correct fields in details JSON, DB error does not propagate, rejected scan creates no attendance record, rejected scan not in report, accepted scan creates attendance record and no rejection row.
- [x] **Documentation**: Updated `docs/attendance-eligibility.md` with Phase 12 audit logging section.

## Phase 13: (NEXT)
- [ ] TBD.

---

## Codebase Analysis (Pre-Phase 9)

### 1. Current Relevant Files

#### Backend
| File | Role |
|---|---|
| `backend/app/models/event.py` | `Event`, `EventTarget`, `EventTargetScope` ORM models |
| `backend/app/models/user.py` | `User`, `StudentProfile` (has `year_level`, `department_id`, `program_id`) |
| `backend/app/models/attendance.py` | `AttendanceRecord` ORM model |
| `backend/app/schemas/event.py` | `EventCreate`, `EventUpdate`, `Event`, `EventTarget`, `EventTargetScope` Pydantic schemas |
| `backend/app/routers/events/crud.py` | Create/update/delete event routes; handles `event_targets` persistence |
| `backend/app/routers/events/workflow.py` | Status transitions, early sign-out |
| `backend/app/routers/events/shared.py` | Shared helpers: RBAC guards, governance scope resolution, student filtering |
| `backend/app/routers/attendance/check_in_out.py` | Face-scan, manual, bulk sign-in/sign-out routes |
| `backend/app/routers/attendance/shared.py` | `_ensure_student_is_event_participant` calls eligibility service |
| `backend/app/services/event_eligibility_service.py` | `is_student_eligible_for_event` — single source of truth for eligibility |
| `backend/app/services/event_attendance_service.py` | `get_event_participant_student_ids`, `finalize_completed_event_attendance` |
| `backend/app/services/student_import_service.py` | Bulk import pipeline; reads `year_level` and `student_status` from rows |
| `backend/app/services/import_validation_service.py` | Row validation; validates `Year Level` (1-5) and `Status` columns |
| `backend/app/reports/attendance/service.py` | Event attendance report logic; uses `build_participant_subquery` |
| `backend/app/reports/attendance/queries.py` | `build_participant_subquery` — applies `event_targets` to filter expected students |
| `backend/alembic/versions/b033a6f7e275_create_event_targets_table.py` | Migration that created `event_targets` table |

#### Frontend
| File | Role |
|---|---|
| `frontend-web/src/components/events/EventEditorSheet.vue` | Create/Edit event bottom sheet — **missing target audience controls** |
| `frontend-web/src/services/eventEditor.js` | Draft model + payload builder — **missing `event_targets` field** |
| `frontend-web/src/views/dashboard/HomeView.vue` | Student dashboard; shows filtered events |
| `frontend-web/src/views/dashboard/GatherAttendanceView.vue` | Scanner/Gather page; delegates to `useGatherAttendance` composable |

#### Tests
| File | Coverage |
|---|---|
| `backend/tests/test_events.py` | Basic CRUD, datetime normalization |
| `backend/tests/test_events_extended.py` | Ongoing events, attendees, stats, time-status, auth guards |
| `backend/tests/test_events_workflow.py` | Status transitions, sign-out workflow |
| `backend/tests/test_attendance.py` | Core attendance sign-in/sign-out |
| `backend/tests/test_attendance_logic.py` | Attendance timing logic |
| `backend/tests/test_rbac_matrix.py` | Role-based access control matrix |

---

### 2. Existing Event Model Structure

```
Event (events table)
├── id, school_id, event_type_id, created_by_user_id
├── name, location, geo_*, early_check_in_minutes, late_threshold_minutes
├── sign_out_grace_minutes, sign_out_open_delay_minutes
├── start_at / start_datetime (synonym), end_at / end_datetime (synonym)
├── status (upcoming | ongoing | completed | cancelled)
├── departments  ← M2M via event_departments (legacy)
├── programs     ← M2M via event_programs (legacy)
└── event_targets ← one-to-many EventTarget rows (Phase 3+)

EventTarget (event_targets table)
├── id, event_id, school_id
├── scope_type: ALL | YEAR_LEVEL | DEPARTMENT | COURSE | DEPARTMENT_YEAR | COURSE_YEAR
├── year_level (nullable int)
├── department_id (nullable FK → departments)
└── course_id (nullable FK → programs)
```

**Scope validation rules** (enforced in `EventTargetBase.validate_scope_combinations`):
- `ALL` → no other fields
- `YEAR_LEVEL` → `year_level` required, no dept/course
- `DEPARTMENT` → `department_id` required, no year/course
- `COURSE` → `course_id` required, no year/dept
- `DEPARTMENT_YEAR` → both `department_id` + `year_level`, no course
- `COURSE_YEAR` → both `course_id` + `year_level`, no dept

**Default behavior**: If no `event_targets` and no legacy `department_ids`/`program_ids` are provided on create, a single `ALL` target is auto-created.

---

### 3. Existing Student/User Model Structure

```
User (users table)
├── id, school_id, email, password_hash
├── first_name, last_name, middle_name, prefix, suffix
└── student_profile → StudentProfile (one-to-one)

StudentProfile (student_profiles table)
├── id, user_id, school_id
├── student_number (indexed)
├── department_id (FK → departments)
├── program_id (FK → programs)
├── year_level (BigInteger, default 1)   ← key targeting field
├── student_status (Text, default ACTIVE) ← eligibility gate
├── promotion_locked (Boolean)
├── section (Text, nullable)
└── rfid_tag (Text, unique, nullable)
```

`year_level` is stored as `BigInteger` in the DB but validated as `int` (1–5) in the import pipeline. The eligibility service compares `student.year_level == target.year_level` directly.

---

### 4. Existing Attendance Flow

```
Student scan/manual entry
  → check_in_out.py router
  → _get_event_in_school_or_404()       # loads event with event_targets joinedload
  → _ensure_student_is_event_participant()
      → is_student_eligible_for_event() # school check → status check → target match
  → _get_event_attendance_decision()    # timing window check
  → AttendanceRecord INSERT (time_in, method, status)

Sign-out
  → same router, finds open AttendanceRecord
  → _get_event_sign_out_decision()
  → _complete_attendance_sign_out()     # sets time_out, finalizes status

Event completion (auto or manual)
  → finalize_completed_event_attendance()
      → get_event_participant_student_ids()  # uses event_targets
      → auto-creates absent rows for no-shows
      → auto-closes open sign-ins
  → generate_sanctions_for_completed_event()
```

**Key**: `_get_event_in_school_or_404` already does `joinedload(Event.event_targets)`, so eligibility checks always have target data.

---

### 5. Existing Report Flow

```
GET /api/attendance/events/{event_id}/report
  → get_event_attendance_report() in reports/attendance/service.py
  → build_participant_subquery()        # applies event_targets OR legacy dept/prog filters
  → count_participants_from_subquery()  # total expected
  → list_event_attendance_rows_for_event_report()  # actual records
  → computes: attendees, late, absent, signed_out, no_sign_out
  → program_breakdown[]
  → AttendanceReportResponse
```

Filters supported: `year_level`, `department_id`, `program_id`, `status`. These are applied on top of the event's own targeting scope.

---

### 6. Existing Frontend Event Form Flow

```
EventEditorSheet.vue (create + edit, same component)
  ├── Props: isOpen, event (null = create mode), createDefaults
  ├── draft = createEventEditorDraft(event)   ← from eventEditor.js
  ├── On submit → buildEventUpdatePayloadFromDraft(draft)
  └── Emits 'save' with payload

eventEditor.js
  ├── createEventEditorDraft(event)
  │     Maps: name, location, startTime, endTime, status,
  │           geoRequired, latitude, longitude, radiusM, maxAccuracyM,
  │           earlyCheckInMinutes, lateThresholdMinutes,
  │           signOutGraceMinutes, signOutOpenDelayMinutes
  │     MISSING: event_targets
  └── buildEventUpdatePayloadFromDraft(draft)
        Builds API payload from draft fields
        MISSING: event_targets
```

The form currently has **no UI for target audience**. The backend defaults to `ALL` when no targets are sent.

---

### 7. Recommended Implementation Order (Phase 9)

1. **`eventEditor.js`** — Add `eventTargets` to draft model and payload builder. This is pure JS with no side effects.
2. **`EventEditorSheet.vue`** — Add "Target Audience" section with scope selector + conditional year/dept/course pickers. Needs department/program list from API.
3. **Backend tests** — Add test cases for `YEAR_LEVEL`, `DEPARTMENT_YEAR`, `COURSE_YEAR` scope creation and eligibility rejection.
4. **E2E smoke** — Verify student filtered out at scanner after year-level-targeted event creation.

---

### 8. Risks and Files That Must Be Edited Carefully

| File | Risk |
|---|---|
| `backend/app/routers/events/crud.py` | Large file; `create_event` and `update_event` both handle `event_targets`. Any change here must preserve the backward-compat migration path (legacy `department_ids` → targets). |
| `backend/app/services/event_eligibility_service.py` | Single source of truth for all eligibility. A logic error here silently breaks scanner, dashboard, and reports simultaneously. |
| `backend/app/services/event_attendance_service.py` | `get_event_participant_student_ids` drives absent auto-creation and sanction generation. Wrong participant set = wrong sanctions. |
| `backend/app/reports/attendance/queries.py` | `build_participant_subquery` is used by multiple report endpoints. Changing the filter logic affects all report counts. |
| `frontend-web/src/services/eventEditor.js` | `buildEventUpdatePayloadFromDraft` is the single payload builder for both create and edit. Adding `event_targets` here must not break existing events that have no targets set in the UI (should omit the field or send `[]` which triggers the ALL default). |
| `frontend-web/src/components/events/EventEditorSheet.vue` | Used for both create and edit. Must handle pre-populating existing `event_targets` from the event prop on edit. |
| `backend/alembic/versions/` | The `event_targets` table already exists. No new migration needed for Phase 9. Do not create a duplicate migration. |
