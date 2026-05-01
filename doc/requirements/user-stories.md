# User Stories

[<- Back to doc index](../README.md)

> **Status:** MUST HAVE — IN PROGRESS
> **Last Updated:** 2026-04-22

---

## Authentication

- **US-001** As a **Campus Admin**, I want to log in securely so that my account is protected from unauthorized access.
- **US-002** As any **user**, I want to be forced to change my temporary password on first login so that my account remains secure.
- **US-003** As any **user**, I want to view and revoke my active sessions so that I can prevent unauthorized use.

## User Management

- **US-004** As a **Campus Admin**, I want to create student accounts individually or in bulk via Excel so that onboarding large cohorts is efficient.
- **US-005** As a **Campus Admin**, I want to see row-level validation errors during import so that I can fix issues before committing data.
- **US-006** As a **Campus Admin**, I want to assign and change user roles so that students and officers have the correct access.

## Event Management

- **US-007** As an **SSG Officer**, I want to create events scoped to departments or programs so that only relevant students see them.
- **US-008** As an **SSG/SG/ORG Officer**, I want to set custom attendance windows (early, late, grace) so that check-in timing is flexible for events I am assigned to organize.
- **US-009** As an **SSG Officer**, I want to extend the near-start attendance window on the fly so that latecomers can still check in as present.

## Attendance

- **US-010** As an **SSG Officer**, I want to record manual time-in and time-out so that attendance is captured even without biometric equipment.
- **US-011** As an **SSG Officer**, I want to use face-scan to mark attendance so that check-in is fast and accurate.
- **US-012** As a **Student**, I want to check in through face recognition so that my attendance is recorded quickly and accurately.
- **US-013** As a **Student**, I want to view my own attendance history so that I can monitor my standing.

## Governance

- **US-014** As an **SSG Officer**, I want to create and manage campus-wide events so that school activities are organized.
- **US-015** As an **SG Officer**, I want to manage attendance only for students in my department so that I have the right scope of authority.
- **US-016** As an **ORG Officer**, I want to create program-level announcements so that my org members are informed.

## Admin and Reporting

- **US-017** As a **Platform Admin**, I want to view all schools and their statuses so that I can manage the platform.
- **US-018** As a **Campus Admin**, I want to view audit logs so that I can trace who made changes and when.
- **US-019** As a **Campus Admin**, I want to see subscription usage metrics so that I know when plan limits are approaching.
- **US-020** As a **Student**, I want to submit a data export request so that I can exercise my data privacy rights.

## System Health

- **US-021** As a **DevOps engineer**, I want a health check endpoint so that I can monitor DB connectivity and pool status in production.
- **US-022** As a **Campus Admin**, I want to assign event organization responsibilities to specific SSG, SG, or ORG officers so that they can manage their respective events.

## AI Assistant

- **US-023** As any **authenticated user**, I want to ask the assistant questions about attendance and events in natural language so that I can get answers without manually navigating reports.
- **US-024** As a **Campus Admin**, I want the assistant to respect my school's data boundary so that it never returns data from other schools.
- **US-025** As an **SSG Officer**, I want the assistant to help me draft bulk student imports so that the process is faster and less error-prone.
