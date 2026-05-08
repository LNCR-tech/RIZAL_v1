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

## Phase 8: Event Creation UI Controls (NEXT)
- [ ] **Frontend Updates:**
    - Add UI controls to the Event Creation/Edit forms to select targeted Year Levels, Departments, and Courses.
    - Implement validation to ensure at least one target is selected (or default to ALL).
- [ ] **Testing & Validation:**
    - Verify the end-to-end flow from event creation with specific targets to student rejection at the scanner.
