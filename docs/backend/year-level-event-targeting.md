# Year Level Event Targeting - Backend Implementation

This document describes the backend changes implemented for the Year Level Event Targeting feature.

## Overview
Aura now supports targeting events to specific student audiences based on:
- Year Level (1-5)
- Student Status (ACTIVE, GRADUATED, etc.)
- Academic Scope (Department, Course, or both)

## Data Models

### StudentProfile
Added fields:
- `year_level`: Integer (1-5), optional.
- `student_status`: Enum (ACTIVE, GRADUATED, INACTIVE, TRANSFERRED, ARCHIVED). Defaults to ACTIVE.

### EventTarget
A new dedicated table for flexible event targeting:
- `scope_type`: Enum (ALL, YEAR_LEVEL, DEPARTMENT, COURSE, DEPARTMENT_YEAR, COURSE_YEAR).
- `year_level`: Optional integer.
- `department_id`: Optional FK to departments.
- `course_id`: Optional FK to programs.

## API Changes

### Event CRUD (`/v1/events`)
- `EventCreate` and `EventUpdate` schemas now accept an `event_targets` list.
- If `event_targets` is provided, the system enforces the new targeting logic during attendance.
- **Backward Compatibility:** Legacy `department_ids` and `program_ids` are still supported. If `event_targets` is missing but legacy IDs are provided, the system automatically generates corresponding `event_targets`.
- **Default Behavior:** If no targeting info is provided at all, the event defaults to an `ALL` scope.

### Student Import (`/v1/admin-import/students`)
- Supports `Year Level` and `Status` columns.
- Validates year level (1-5) and status values.
- Defaults status to `ACTIVE` if missing.

## Attendance Validation
The `_ensure_student_is_event_participant` helper now:
1. Checks `event.event_targets`.
2. If targets exist, it verifies if the student matches at least one target (OR logic).
3. If no targets exist, it falls back to checking the legacy department/program associations.

## Notification and Reporting Behavior
- `dispatch_event_announcement_notifications` resolves recipients from the same event-target eligibility rules used by attendance.
- Only `ACTIVE` students from the same school are eligible.
- Eligible recipients are de-duplicated by user before notification logs are created.
- Event announcement dispatch is idempotent per `user_id + event_id + category`; rerunning the dispatcher will not create a second announcement log for the same user and event.
- Event attendance reports no longer assume `AttendanceRecord` exposes a `completion_state` column. Completion is derived from the existing attendance completion helper, which treats records with `time_out` as completed and open records as incomplete.

## Testing
To test the new targeting logic:
1. Create an event with a specific target (e.g., `scope_type: "YEAR_LEVEL", year_level: 3`).
2. Attempt to sign in a student with `year_level: 3` (should succeed).
3. Attempt to sign in a student with `year_level: 2` (should fail with 400).
4. Dispatch an event announcement twice for the same event and confirm each eligible student receives only one `event_announcement` log entry.
5. Run the attendance event report for a mix of signed-in-only and signed-out records and confirm open records count under `no_sign_out_attendees` while signed-out records count under `signed_out_attendees`.
