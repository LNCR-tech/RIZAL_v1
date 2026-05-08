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

## Backward Compatibility
Existing events that use the legacy `department_ids` and `program_ids` fields are still supported. The system automatically migrates these to the new target rules format.

## Reporting & Analytics
The targeting system directly influences attendance reports:
- **Automatic "Expected" Calculation**: The system automatically calculates the number of expected students by counting `ACTIVE` students who fall within the event's targeted scope.
- **Precise Absentees**: Students who fall outside the scope are excluded from absentee counts, ensuring that report accuracy is maintained even for events with very narrow targets (e.g., a specific section or year level).
- **Targeted Filters**: Reports can be dynamically filtered by Year Level, Department, or Course to drill down into the attendance performance of specific sub-groups.
