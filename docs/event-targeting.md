# Event Targeting System

Aura provides a flexible system for targeting events to specific student audiences based on metadata such as Year Level, Department, and Course.

## Overview
Targeting ensures that students only see and can sign into events relevant to them. It supports granular combinations (e.g., "3rd Year BSIT students only").

## How it Works
Targeting is defined by one or more **Target Rules** attached to an event.

### Target Rules
Each rule consists of:
- **Scope Type**: The category of targeting (e.g., `YEAR_LEVEL`, `COURSE_YEAR`).
- **Metadata**: The specific IDs or values (e.g., `year_level: 3`, `course_id: UUID`).

### Evaluation (OR Logic)
Rules are evaluated using **OR** logic. A student is eligible if they match **ANY** of the rules defined for the event.

## Supported Scopes
- `ALL`: Open to all active students in the school.
- `YEAR_LEVEL`: Open to students in a specific year level (1-5).
- `DEPARTMENT`: Open to students in a specific department.
- `COURSE`: Open to students in a specific program/course.
- `DEPARTMENT_YEAR`: Open to students in a specific department AND year level.
- `COURSE_YEAR`: Open to students in a specific course AND year level.

## Student Visibility
The **Student Dashboard** automatically filters the event list based on these rules. If a student is not eligible (wrong year, wrong course, or inactive status), the event will not appear on their timeline.

## Attendance Enforcement
During check-in (Manual, Bulk, or Scan), the system verifies the student's eligibility using the centralized `EventEligibilityService`. If a student matches no targets, they are rejected with an error code: `STUDENT_NOT_INCLUDED_IN_EVENT_SCOPE`.

## Notifications (Phase 9)
Event announcement notifications are scoped to eligible students only.

### Dispatch endpoint
```
POST /api/notifications/dispatch/event-announcement/{event_id}
```
Requires `campus_admin` or `admin` role. Returns a `NotificationDispatchSummary`.

### Eligibility rules applied
1. Student must belong to the **same school** as the event (`school_id` boundary).
2. Student `student_status` must be **ACTIVE**. GRADUATED, INACTIVE, TRANSFERRED, and ARCHIVED students are excluded.
3. Student must match **at least one** of the event's `event_targets` (OR logic across all target rules).
4. Fallback: if no `event_targets` exist, legacy `departments`/`programs` associations are used.

### Reminder notifications
`dispatch_event_reminder_notifications` (called via `POST /api/notifications/dispatch/event-reminders`) also enforces the same eligibility rules. The event query now eagerly loads `event_targets`, `programs`, and `departments` to avoid N+1 queries and ensure correct scope resolution.

## Target Scope Permissions (Phase 11)

Event target scopes are enforced server-side based on the actor's governance role. Frontend may mirror these rules for UX, but the backend is the authoritative gate.

### Rules

| Actor | Allowed scopes |
|---|---|
| Campus Admin / Admin | ALL, YEAR_LEVEL, DEPARTMENT, COURSE, DEPARTMENT_YEAR, COURSE_YEAR |
| SSG member with `manage_events` | ALL, YEAR_LEVEL |
| SG member with `manage_events` | DEPARTMENT (own dept), DEPARTMENT_YEAR (own dept + any year) |
| ORG member with `manage_events` | COURSE (own program), COURSE_YEAR (own program + any year) |

### Enforcement point
`validate_event_targets_for_actor` in `app/services/event_target_permissions.py` is called from both `create_event` and `update_event` in `app/routers/events/crud.py`. It raises HTTP 403 with a descriptive message when the actor's governance unit does not permit the requested scope.

### Multi-school boundary
School boundary is enforced by the existing `school_id` checks in the event CRUD layer. `validate_event_targets_for_actor` only validates the scope type and IDs against the actor's governance unit.

## Backward Compatibility
Existing events that use the legacy `department_ids` and `program_ids` fields are still supported. The system automatically migrates these to the new target rules format.

## Reporting & Analytics
The targeting system directly influences attendance reports:
- **Automatic "Expected" Calculation**: The system automatically calculates the number of expected students by counting `ACTIVE` students who fall within the event's targeted scope.
- **Precise Absentees**: Students who fall outside the scope are excluded from absentee counts, ensuring that report accuracy is maintained even for events with very narrow targets (e.g., a specific section or year level).
- **Targeted Filters**: Reports can be dynamically filtered by Year Level, Department, or Course to drill down into the attendance performance of specific sub-groups.
