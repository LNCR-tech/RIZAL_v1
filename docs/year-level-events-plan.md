# Year Level Event Targeting Plan

## 1. Current Relevant Files
- **Backend Models:** `app/models/event.py`, `app/models/user.py`, `app/models/associations.py`
- **Backend Schemas:** `app/schemas/event.py`
- **Backend Routers:** `app/routers/events/crud.py`, `app/routers/attendance/check_in_out.py`, `app/routers/attendance/shared.py`
- **Frontend Components:** `src/components/events/EventEditorSheet.vue`, potentially `src/components/events/EventTargetingPicker.vue` (if it exists) or wherever `department_ids` and `program_ids` are handled.
- **Database Migrations:** `alembic/versions/`

## 2. Existing Event Model Structure
- The `Event` model (`events` table) contains base fields like name, time, location, and attendance config.
- Targeting is currently handled via many-to-many associations to `departments` (`event_departments`) and `programs` (`event_programs`).
- There is currently no field or association table for `year_levels`.

## 3. Existing Student/User Model Structure
- The `StudentProfile` model (`student_profiles` table) contains a `year_level` integer column (typically 1-5).
- It also references `department_id` and `program_id`.

## 4. Existing Attendance Flow
- When a student checks in (e.g., via `/scan`, `/manual`, or `/bulk` in `app/routers/attendance/check_in_out.py`), the system verifies they belong to the event.
- It uses a shared function (like `_ensure_student_is_event_participant` in `app/routers/attendance/shared.py`) to validate if the student's department/program matches the event's scoped departments/programs.

## 5. Existing Report Flow
- Reports in `app/reports/attendance` aggregate data based on the attendees. If attendance targeting becomes more specific (by year level), the reports should still function properly, but the total expected attendees calculation must factor in the year level filter.

## 6. Existing Frontend Event Form Flow
- `EventEditorSheet.vue` currently collects basic event details, scheduling, attendance windows, and geolocation constraints.
- Targeting (departments, programs) might be handled either in the same sheet or a separate setup step. Year levels will need a multi-select input (e.g., Checkboxes for Year 1, 2, 3, 4, 5) added to the event creation/edit payload.

## 7. Recommended Implementation Order
1. **Database Schema & Models:**
   - Create a new association table `event_year_levels` `(event_id, year_level)` in `app/models/associations.py`.
   - Add a `year_levels` relationship to the `Event` model.
2. **Backend Schemas:**
   - Update `EventCreate` and `EventUpdate` in `app/schemas/event.py` to accept `year_levels: Optional[List[int]] = None`.
   - Update `Event` schema to include `year_levels` (or `target_year_levels`).
3. **Backend CRUD:**
   - Update `app/routers/events/crud.py` to handle inserting and updating `event_year_levels` when an event is created or edited.
4. **Attendance Validation Logic:**
   - Update `_ensure_student_is_event_participant` in `app/routers/attendance/shared.py`. If the event has specific `year_levels` configured, assert that `student.year_level` is in that list. If empty, assume all year levels are allowed.
5. **Database Migration:**
   - Generate an Alembic migration (`alembic revision --autogenerate -m "Add event year levels"`) to apply the schema change.
6. **Frontend Updates:**
   - Update the API client schemas and state stores.
   - Add a UI control in the Event Creation and Edit forms to select targeted Year Levels.
7. **Testing:**
   - Run existing tests and add new tests verifying that a student from a non-targeted year level is rejected during sign-in.

## 8. Risks or Files That Must Be Edited Carefully
- **`app/routers/attendance/shared.py`**: Modifying the attendance participation logic is high-risk. A bug here could prevent legitimate students from signing in or allow unauthorized ones.
- **`app/routers/events/crud.py`**: Event updates must cleanly overwrite existing year level targets without causing duplicate key errors.
- **Expected Attendees Calculation**: If the system displays a "Total Expected" count anywhere based on the event's scope, the query must be updated to filter by `student_profiles.year_level` in addition to department/program.
