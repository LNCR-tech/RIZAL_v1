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

## Phase 5: Frontend Integration (NEXT)
- [ ] **Frontend Updates:**
    - Update the API client schemas and state stores.
    - Add a UI control in the Event Creation and Edit forms to select targeted Year Levels (1-5).
- [ ] **Testing & Validation:**
    - Verify that students from non-targeted year levels are rejected during check-in.
