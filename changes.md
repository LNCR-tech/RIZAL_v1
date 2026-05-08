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
