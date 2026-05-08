# Changes

## 2026-05-08 (Phase 7: Attendance Enforcement)
4: 
5: ### Backend Changes
6: - **Attendance Routers:** Hardened `record_face_scan_attendance` in `app/routers/attendance/check_in_out.py` to enforce event eligibility using the centralized service.
7: - **Status Codes:** Updated `_ensure_student_is_event_participant` in `app/routers/attendance/shared.py` to return HTTP 403 (Forbidden) instead of 400, specifically for student targeting violations.
8: - **Standardized Messaging:** Standardized the rejection message to "Student is not included in this event scope." in `EventEligibilityService`.
9: 
10: ### Frontend Changes
11: - **Public Attendance Service:** Updated `describePublicAttendanceError` and `normalizeOutcome` in `src/services/publicAttendance.js` to translate the backend error code into user-friendly messages:
12:     - Top-level: "You are not included in this event."
13:     - Scan outcomes: "Not included in this event."
14: 
15: ### Documentation
16: - Updated `docs/year-level-events-plan.md` to reflect Phase 7 completion.
17: - Updated `docs/attendance-eligibility.md` to reflect the 403 status code change.
18: 

## 2026-05-08 (Phase 6: Student Dashboard Filtering)

### Backend Changes
- **Queries:** Updated event listing routes in `app/routers/events/queries.py` to proactively load `event_targets`, ensuring the eligibility service has the necessary data for filtering.
- **Filtering:** Dashboard events are now strictly filtered using the centralized `EventEligibilityService`, ensuring students only see events matching their Year Level, Department, or Course.

### Frontend Changes
- **Components:** Updated `EventsCard.vue` to display a personalized "No upcoming events assigned to you" message when no eligible events are found for the current student.

### Documentation
- Created `docs/event-targeting.md` as a consolidated reference for the whole targeting system.
- Updated `docs/year-level-events-plan.md` to reflect Phase 6 completion.

## 2026-05-08 (Phase 5: Centralized Eligibility Service)

### Backend Changes
- **Services:**
    - Created `app/services/event_eligibility_service.py` to centralize student eligibility checks.
    - Implemented rules for School matching, Student Status (must be ACTIVE), and Targeting Scopes.
    - Added standardized rejection codes (`STUDENT_NOT_ACTIVE`, `STUDENT_NOT_INCLUDED_IN_EVENT_SCOPE`, etc.).
- **Routers:**
    - Refactored `app/routers/attendance/shared.py` to use the new eligibility service for check-in validation.
    - Refactored `app/routers/events/shared.py` to use the new eligibility service for filtering the student dashboard.

### Documentation
- Created `docs/attendance-eligibility.md` defining the core eligibility rules.
- Updated `docs/year-level-events-plan.md` to reflect Phase 5 completion.

## 2026-05-08 (Phase 4: Event Targeting API Integration)

### Backend Changes
- **Schemas:**
    - Renamed `targets` to `event_targets` in `app/schemas/event.py` for clarity and Phase 4 alignment.
    - Updated `EventCreate` and `EventUpdate` to accept `event_targets` list.
- **Routers:**
    - **CRUD:** Updated `app/routers/events/crud.py` with transaction-safe targeting logic.
    - **Backward Compatibility:** Implemented automatic migration of legacy `department_ids`/`program_ids` to `event_targets` if the new field is absent.
- **Models:**
    - Renamed `targets` relationship to `event_targets` in `Event` model.

## 2026-05-08 (Phase 3: Event Targeting Infrastructure)

### Backend Changes
- **Models:**
    - Created `EventTarget` model in `app/models/event.py` for scope-based targeting.
- **Database:**
    - Created and applied Alembic migration `b033a6f7e275` for the `event_targets` table.

## 2026-05-08 (Phase 2: Student Bulk Import Update)

### Backend Changes
- **Services:** Updated `app/services/import_validation_service.py` to support new columns: `School_ID`, `Year Level`, and `Status`.

### Frontend Changes
- **Views:** Updated `SchoolItImportStudentsView.vue` and the import preview list to display `Year Level` and `Status` tags.

## 2026-05-08 (Phase 1: Student Profile Stabilization)

### Backend Changes
- **Models:** Updated `StudentProfile` in `app/models/user.py` to include `student_status` (Enum) and `promotion_locked` (Boolean).
- **Database:** Created Alembic migration `0003_add_student_status`.
