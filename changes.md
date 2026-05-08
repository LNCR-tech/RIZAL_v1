# Changes

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
    - Added `EventTargetScope` and `EventTargetCreate` to standard exports.
- **Routers:**
    - **CRUD:** Updated `app/routers/events/crud.py` with transaction-safe targeting logic.
    - **Backward Compatibility:** Implemented automatic migration of legacy `department_ids`/`program_ids` to `event_targets` if the new field is absent.
    - **Validation:** Added enforcement of non-empty targeting and school-scoped foreign key checks for departments/courses.
    - **Attendance:** Updated participant check to enforce the new multi-scope targeting rules (Year Level, Department, Course, etc.).
- **Models:**
    - Renamed `targets` relationship to `event_targets` in `Event` model.

### Documentation
- Updated `docs/backend/year-level-event-targeting.md` with Phase 4 API details.
- Updated `docs/year-level-events-plan.md` to reflect completion of Phase 3 and 4.

## 2026-05-08 (Phase 3: Event Targeting Infrastructure)

### Backend Changes
- **Models:**
    - Created `EventTarget` model in `app/models/event.py` for scope-based targeting.
    - Added `EventTargetScope` Enum (ALL, YEAR_LEVEL, DEPARTMENT, COURSE, etc.).
- **Infrastructure:**
    - Shortened long unique constraint names in `GovernanceStudentNote` and `SanctionDelegation` to comply with PostgreSQL 63-character limits.
    - Fixed Alembic `env.py` and model registration to prevent `NoReferencedTableError` during migration generation.

### Database
- Created and applied Alembic migration `b033a6f7e275` for the `event_targets` table.

## 2026-05-08 (Phase 2: Student Bulk Import Update)

### Backend Changes
- **Services:**
    - Updated `app/services/import_validation_service.py` to support new columns: `School_ID`, `Year Level`, and `Status`.
    - Implemented dual-format support in `validate_headers` (Legacy 7-column vs Extended 10-column).
    - Added row-level validation for `Year Level` (1-5) and `Status` (Enum) in `validate_and_transform_row`.
    - Added conditional requirement for `Year Level` (mandatory for `ACTIVE` students in the new format).
- **Repositories:**
    - Updated `ImportRepository.bulk_insert_students` to persist `year_level` and `student_status` from import data.

### Frontend Changes
- **Views:**
    - Updated `SchoolItImportStudentsView.vue` to include new headers in the sidebar and template instructions.
    - Updated the import preview list to display `Year Level` and `Status` tags for each row.
    - Added CSS for compact metadata tags in the preview row.
- **Services:**
    - Updated `frontend-web/src/services/studentImport.js` to extract `yearLevel` and `studentStatus` from API responses.

### Documentation
- Created `docs/student-import-format.md` detailing the new and legacy header structures.
- Updated `docs/year-level-events-plan.md` to reflect progress on Phase 2.

## 2026-05-08 (Phase 1: Student Profile Stabilization)

### Backend Changes
- **Models:** Updated `StudentProfile` in `app/models/user.py` to include `student_status` (Enum) and `promotion_locked` (Boolean).
- **Schemas:** 
    - Added `StudentStatus` Enum to `app/schemas/user.py`.
    - Updated `StudentProfileBase` and `StudentAccountCreate` to include `year_level`, `student_status`, and `promotion_locked`.
    - Made `event_location` optional in `StudentAttendanceDetail` (`app/schemas/attendance.py`) to fix existing test regressions.
- **Routers:**
    - Updated `app/routers/users/students.py` to correctly handle `student_number` (internal name) vs `student_id` (external name) and persist new metadata.
    - Improved email error handling in student creation to avoid 502 errors when email delivery is disabled.
    - Updated `_serialize_user` in `app/routers/users/shared.py` to include new student metadata in API responses.
- **Core:**
    - Modified `app/core/config.py` to allow environment variable overrides (using `override=False` in `load_dotenv`), enabling cleaner test configurations.

### Database
- Created Alembic migration `0003_add_student_status` to apply schema updates.

### Testing
- Created `tests/test_students_extended.py` to verify Phase 1 requirements.
- Updated `tests/conftest.py` to explicitly disable email delivery and delivery mode during test execution.
- Resolved permission issues and environment clobbering that were causing bulk import and user management tests to fail.
- Verified all core student and import tests pass in the container environment.
