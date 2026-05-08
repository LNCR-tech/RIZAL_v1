# Changes

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
