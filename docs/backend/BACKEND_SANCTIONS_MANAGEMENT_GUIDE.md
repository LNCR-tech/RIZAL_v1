[<- Back to docs index](../../README.md)

# Backend Sanctions Management Guide

## Purpose

This guide documents the sanctions data-model baseline introduced for sanctions management in Aura.

## Schema Overview

Migration: `Backend/alembic/versions/d1a2b3c4d5e6_add_sanctions_management_tables.py`

Added tables:

- `event_sanction_configs`
  - Per-event sanctions toggle and sanction item definitions (`item_definitions_json`)
  - One config per event (`uq_event_sanction_configs_event_id`)
- `sanction_records`
  - One sanction record per absent student per event
  - Unique per `(event_id, student_profile_id)` (`uq_sanction_records_event_student`)
  - Tracks overall sanction status (`pending` or `complied`)
- `sanction_items`
  - Child sanction items under a sanction record
  - Unique per `(sanction_record_id, item_code)` (`uq_sanction_items_record_item_code`)
  - Tracks per-item status (`pending` or `complied`)
- `sanction_delegations`
  - Event-level sanction delegation to governance units
  - Unique per `(event_id, delegated_to_governance_unit_id)` (`uq_sanction_delegations_event_governance_unit`)
  - Tracks delegation scope and active/revoked state
- `sanction_compliance_history`
  - Permanent compliance log with school year, semester, event context, and compliance date
- `clearance_deadlines`
  - SSG-declared sanctions clearance deadlines with delivery state fields for warning channels

Added enum types:

- `sanction_compliance_status` -> `pending`, `complied`
- `sanction_item_status` -> `pending`, `complied`
- `sanction_delegation_scope_type` -> `unit`, `department`, `program`, `school`
- `clearance_deadline_status` -> `active`, `closed`, `expired`

## ORM Models

Model file: `Backend/app/models/sanctions.py`

Added model classes:

- `EventSanctionConfig`
- `SanctionRecord`
- `SanctionItem`
- `SanctionDelegation`
- `SanctionComplianceHistory`
- `ClearanceDeadline`

Model registration updates:

- `Backend/app/models/__init__.py` now exports the sanctions models.
- `Backend/alembic/env.py` imports sanctions models so metadata resolution includes sanctions tables.

## Validation and Test Coverage

Test file: `Backend/app/tests/test_sanctions_models.py`

Covered checks:

- sanctions tables are registered in SQLAlchemy metadata
- event sanction config uniqueness per event
- sanction record uniqueness per event and student
- sanction item uniqueness per record and item code
- sanction delegation uniqueness per event and delegated governance unit
- clearance deadline default status is `active`

Run:

1. `python -m pytest -q Backend/app/tests/test_sanctions_models.py`

Step 8 behavior test file: `Backend/tests/test_sanctions.py`

Covered checks:

- sanction record auto-generation after event completion workflow transition
- scope enforcement:
  - `SSG` sees all records for accessible events
  - `SG` sees only scoped/delegated records
  - `ORG` sees only scoped/delegated records
- delegation grant changes access for sanctions list endpoints
- approve action creates compliance history rows and remains idempotent on repeated approve calls
- student personal sanctions view isolation (`/api/sanctions/students/me`)

Run:

1. `python -m pytest -q Backend/tests/test_sanctions.py`

## Routes and Service

Router: `Backend/app/routers/sanctions.py`  
Service: `Backend/app/services/sanctions_service.py`

Mounted path:

- `/api/sanctions/*` (mounted in `Backend/app/main.py`)

Implemented endpoints:

- `GET /api/sanctions/events/{event_id}/config`
- `PUT /api/sanctions/events/{event_id}/config`
- `GET /api/sanctions/events/{event_id}/students`
- `POST /api/sanctions/events/{event_id}/students/{user_id}/approve`
- `GET /api/sanctions/events/{event_id}/delegation`
- `PUT /api/sanctions/events/{event_id}/delegation`
- `GET /api/sanctions/dashboard`
- `GET /api/sanctions/students/me`
- `GET /api/sanctions/students/{user_id}`
- `POST /api/sanctions/clearance-deadline`
- `GET /api/sanctions/clearance-deadline`
- `GET /api/sanctions/events/{event_id}/export`

All sanctions business logic is implemented in `sanctions_service.py`; router handlers only delegate calls.

## Governance Permission Group

Permission system updates:

- Added governance permission group constant in `Backend/app/services/governance_hierarchy_service/shared.py`:
  - `SANCTIONS_MANAGEMENT_PERMISSION_GROUP = "sanctions_management"`
  - `SANCTIONS_MANAGEMENT_PERMISSION_CODES`
- Added new `PermissionCode` values in `Backend/app/models/governance_hierarchy.py`:
  - `view_sanctioned_students_list`
  - `view_student_sanction_detail`
  - `approve_sanction_compliance`
  - `configure_event_sanctions`
  - `export_sanctioned_students`
  - `view_sanctions_dashboard`
- Added definitions for these codes in `PERMISSION_DEFINITIONS`.
- Expanded `UNIT_MEMBER_PERMISSION_WHITELIST` for `SSG`, `SG`, and `ORG` to include sanctions permissions.
- Added migration:
  - `Backend/alembic/versions/e2f7a1c9d4b6_add_sanctions_governance_permissions.py`
  - Seeds the six new governance permission rows.

Route-level permission guards enforce sanctions actions in `Backend/app/routers/sanctions.py`:

- `GET /events/{event_id}/config` -> `configure_event_sanctions` (fallback: `manage_events`)
- `PUT /events/{event_id}/config` -> `configure_event_sanctions` (fallback: `manage_events`)
- `GET /events/{event_id}/students` -> `view_sanctioned_students_list`
- `POST /events/{event_id}/students/{user_id}/approve` -> `approve_sanction_compliance`
- `GET /events/{event_id}/delegation` -> `configure_event_sanctions` (fallback: `manage_events`)
- `PUT /events/{event_id}/delegation` -> `configure_event_sanctions` (fallback: `manage_events`)
- `GET /dashboard` -> `view_sanctions_dashboard` (fallback: `configure_event_sanctions` or `manage_events`)
- `GET /students/{user_id}` -> `view_student_sanction_detail`
- `POST /clearance-deadline` -> `configure_event_sanctions`
- `GET /events/{event_id}/export` -> `export_sanctioned_students`

Role fallback guardrails for governance sanctions routes:

- role fallback now uses active governance membership first (`SSG`/`SG`/`ORG` unit types), then legacy role aliases (`student_council`, `student council`) as compatibility fallback
- when fallback mode is enabled on a route, governance users can access sanctions features without explicit sanctions permission grants
- governance-role fallback is enabled on:
  - `GET /events/{event_id}/config`
  - `PUT /events/{event_id}/config`
  - `GET /events/{event_id}/students`
  - `POST /events/{event_id}/students/{user_id}/approve`
  - `GET /events/{event_id}/delegation`
  - `PUT /events/{event_id}/delegation`
  - `GET /dashboard`
  - `GET /students/{user_id}`
  - `POST /clearance-deadline`
  - `GET /events/{event_id}/export`
- service helpers (`_require_event_access`, `_evaluate_event_access`) remain the source of truth for event scope, write access, and delegation boundaries.

Not guarded by governance permission (by design):

- `GET /students/me` (student-only endpoint)
- `GET /clearance-deadline` (supports student warning/popup flow and governance visibility filtering in service)

## Access and Delegation Rules

Service-level enforcement implemented in `_evaluate_event_access` and related helpers:

- `Admin` (platform admin with `school_id = NULL`)
  - sanctions service resolves a default school context (lowest `School.id`) when a school-scoped sanctions query needs `school_id`
  - route-level admin bypass remains in place for sanctions permission checks
- `SSG`
  - full sanctions read across governance levels
  - sanctions write restricted to SSG-owned events
- `SG`
  - sanctions access on SG-owned events
  - sanctions access on SSG-owned events only when delegated per-event
- `ORG`
  - sanctions access on ORG-owned events
  - sanctions access on SG-owned events only when delegated per-event
- `Students`
  - only own sanctions through `/api/sanctions/students/me`

Delegation behavior:

- delegations are checked per event from `sanction_delegations`
- delegation updates are restricted to event-owner governance level (`creator-level` behavior)
- SSG-owned events can delegate to SG units
- SG-owned events can delegate to ORG units
- ORG-owned events cannot delegate further

## Event Completion Auto-generation

Hook location:

- `Backend/app/services/event_workflow_status.py`

Completion behavior:

1. Attendance finalization runs when event reaches `completed`.
2. `generate_sanctions_for_completed_event` executes after attendance finalization.
3. If sanctions are enabled for the event:
   - absent students receive `sanction_records`
   - configured sanction items are materialized into `sanction_items`
   - sanction notification emails are queued asynchronously

Sync summary includes sanctions counters:

- `sanction_records_created`
- `sanction_notification_emails_queued`

## Async Email Tasks

Worker file: `Backend/app/workers/tasks.py`

Added tasks:

- `app.workers.tasks.send_sanction_notification_email`
- `app.workers.tasks.send_clearance_deadline_warning_email`
- `app.workers.tasks.send_sanction_compliance_confirmation_email`

Dispatch behavior:

- sanctions service dispatches these through Celery task `.apply_async(...)`
- email senders use existing email transport via `send_plain_email`

## End-to-end Test Commands

1. `python -m pytest -q Backend/app/tests/test_sanctions_models.py`
2. `python -m pytest -q Backend/app/tests/test_sanctions_api.py`
3. `python -m pytest -q Backend/app/tests/test_auth_task_dispatcher.py`
4. `python -m pytest -q Backend/app/tests/test_event_workflow_status.py`
5. `python -m pytest -q Backend/app/tests/test_governance_hierarchy_api.py`
6. `python -m pytest -q Backend/tests/test_sanctions.py`

Sanctions role-fallback verification:

1. Login as `SSG`, `SG`, and `ORG` users that each have active governance membership, without granting explicit sanctions member permissions.
2. Open a matching owned event (`SSG` campus-wide, `SG` department-scoped, `ORG` program-scoped).
3. Confirm scoped endpoints return `200` (for example config, students list, dashboard, and export for their owned event scope).
4. Confirm cross-scope access without delegation still returns `404` (for example `SG` reading an `SSG`-owned event sanctions list).
5. Login as platform `admin` with `school_id = NULL`, call `GET /api/sanctions/dashboard`, and confirm `200`.

