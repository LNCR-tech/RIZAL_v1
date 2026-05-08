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
- `EventCreate` and `EventUpdate` schemas now accept a `targets` list.
- If `targets` is provided, the system enforces the new targeting logic during attendance.
- Legacy `department_ids` and `program_ids` are still supported for backward compatibility.

### Student Import (`/v1/admin-import/students`)
- Supports `Year Level` and `Status` columns.
- Validates year level (1-5) and status values.
- Defaults status to `ACTIVE` if missing.

## Attendance Validation
The `_ensure_student_is_event_participant` helper now:
1. Checks `event.targets`.
2. If targets exist, it verifies if the student matches at least one target (OR logic).
3. If no targets exist, it falls back to checking the legacy department/program associations.

## Testing
To test the new targeting logic:
1. Create an event with a specific target (e.g., `scope_type: "YEAR_LEVEL", year_level: 3`).
2. Attempt to sign in a student with `year_level: 3` (should succeed).
3. Attempt to sign in a student with `year_level: 2` (should fail with 400).
