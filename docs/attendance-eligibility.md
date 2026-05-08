# Attendance Eligibility Logic

This document defines the centralized rules for determining if a student is eligible to participate in (and sign into) an event.

## Core Rules

A student is eligible for an event ONLY if all the following conditions are met:

1.  **School Matching**: The student must belong to the same school as the event.
2.  **Active Status**: The student's `student_status` must be `ACTIVE`. Students with status `GRADUATED`, `INACTIVE`, `TRANSFERRED`, or `ARCHIVED` are rejected.
3.  **Audience Matching**: The student must match at least one targeting rule configured for the event.

## Targeting Scopes (`event_targets`)

Targeting rules are evaluated using **OR** logic. If a student matches any one rule, they satisfy the audience requirement.

| Scope Type | Logic |
| :--- | :--- |
| `ALL` | Matches all ACTIVE students in the same school. |
| `YEAR_LEVEL` | Matches the student's `year_level`. |
| `DEPARTMENT` | Matches the student's `department_id`. |
| `COURSE` | Matches the student's `course_id` (Program ID). |
| `DEPARTMENT_YEAR`| Matches both `department_id` AND `year_level`. |
| `COURSE_YEAR` | Matches both `course_id` AND `year_level`. |

## Error Codes

When eligibility is denied, the system returns specific error codes:

*   `STUDENT_SCHOOL_MISMATCH`: Student is from a different campus/school.
*   `STUDENT_NOT_ACTIVE`: Student is not currently ACTIVE.
*   `STUDENT_NOT_INCLUDED_IN_EVENT_SCOPE`: Student does not match any targeted year levels, departments, or courses.
*   `EVENT_HAS_NO_TARGETS`: The event has no targeted audience configuration (critical error).

## Implementation

The centralized checker is implemented in `backend/app/services/event_eligibility_service.py` and is used by:
- Attendance routers (to block check-ins).
- Event routers (to filter visible events on the student dashboard).
