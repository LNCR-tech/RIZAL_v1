# Year Level Event Targeting Plan

## Phase 1: Student Metadata Stabilization (COMPLETED)
- [x] **Add `year_level` to `StudentProfile`** (1-5, default 1).
- [x] **Add `student_status` Enum to `StudentProfile`** (ACTIVE, GRADUATED, etc.).
- [x] **Add `promotion_locked` boolean** (default false).
- [x] **Update API Schemas** to include new fields.
- [x] **Update Student Management Routers** to handle persistence and validation.
- [x] **Update Serialization Helpers** to ensure API responses include new metadata.
- [x] **Stabilize Test Suite** by disabling email delivery and fixing volume permissions in test environment.

## Phase 2: Event Targeting Implementation (NEXT)
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
   - Generate an Alembic migration for `event_year_levels`.

## Phase 3: Frontend Integration
1. **Frontend Updates:**
   - Update the API client schemas and state stores.
   - Add a UI control in the Event Creation and Edit forms to select targeted Year Levels (1-5).
2. **Testing & Validation:**
   - Verify that students from non-targeted year levels are rejected during check-in.
