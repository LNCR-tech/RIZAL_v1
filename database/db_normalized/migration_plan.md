# Database Normalization Analysis & Migration Plan

Source: `db_schema_readable.md` (repo root)

This document describes the *current* schema issues and a safe migration approach toward the proposed target schema in `db_normalized/new_db_schema.sql`.

## Current Schema: How Normalized Is It?

Overall: **mostly 3NF-ish for core entities** (schools/users/events/programs/departments/governance) due to:
- clear entity tables (`schools`, `users`, `events`, `departments`, `programs`, …)
- proper association tables for many-to-many (`event_program_association`, `event_department_association`, `program_department_association`, …)
- widespread FK usage and reasonable indexing

Main gaps are **(a) redundancy** and **(b) 1NF violations via JSON repeating groups** in a few important tables.

## Issues & Proposed Fixes

### Issue 1 — Duplicate school fields (redundancy)
**Tables:** `schools`, `school_settings`, `school_subscription_settings`
- Duplicate “name” concept: `schools.name` vs `schools.school_name`.
- Duplicate branding colors: `schools.primary_color/secondary_color` vs `school_settings.primary_color/secondary_color`.
- Subscription fields split/overlapping between `schools` and `school_subscription_settings`.

**Fix direction:** make one canonical source for each concept (name, branding, subscription state).

### Issue 2 — Face embedding stored twice (entity integrity + redundancy)
**Tables:** `student_profiles`, `user_face_profiles`
- Both contain face embedding bytes/provider-ish metadata.

**Fix direction:** single source of truth for embeddings (prefer `user_face_profiles`), keep only student-specific flags/URLs/timestamps on `student_profiles`.

### Issue 3 — `school_id` duplicated down the FK chain (redundancy; 3NF-style concern)
**Examples:** `event_sanction_configs.school_id`, `sanction_records.school_id`, `clearance_deadlines.school_id`, `governance_student_notes.school_id`, …
- In many cases it is derivable (`event_id -> events.school_id`, `governance_unit_id -> governance_units.school_id`).

**Fix direction:** either remove the redundant column, or explicitly treat it as controlled denormalization (kept for performance/tenant filtering + enforced via trigger/constraint strategy).

### Issue 4 — Sanction item definitions stored as JSON (1NF)
**Table:** `event_sanction_configs`
- `item_definitions_json` is a repeating group (array) inside a column.

**Fix direction:** relational child table (templates/definitions) keyed by config/event.

### Issue 5 — Governance note tags stored as JSON (1NF)
**Table:** `governance_student_notes`
- `tags` is a repeating group (array) inside a column.

**Fix direction:** `governance_student_note_tags(note_id, tag)`.

### Issue 6 — Delegation scope stored as JSON (1NF)
**Table:** `sanction_delegations`
- `scope_json` hides structured scope IDs and prevents FK enforcement.

**Fix direction:** explicit relational scope tables or FK columns for common scope types + optional “extra” JSON for uncommon cases.

### Issue 7 — Academic period stored as free-text (domain integrity)
**Table:** `sanction_compliance_history`
- `school_year` and `semester` free-text strings allow inconsistent values.

**Fix direction:** `academic_periods` lookup + FK.

### Issue 8 — Legacy `ssg_*` duplicates modern governance model (entity duplication)
**Tables:** `ssg_events`, `ssg_announcements`, `ssg_roles`, `ssg_user_roles`, `ssg_permissions`, `ssg_role_permissions`

**Fix direction:** migrate active usage into `governance_*` and remove legacy tables (or keep read-only if still required).

**Note:** governance “unit types” are application-defined (hardcoded) categories (e.g. `SSG`, `SG`, `ORG`). This is separate from auth roles like `admin`, `campus_admin`, `student`, `faculty`, etc. which are data-driven via the `roles` table.

### Issue 9 — Missing uniqueness constraints in link tables (integrity)
**Examples:** `user_roles`, `attendances`
- `user_roles` has no unique constraint on `(user_id, role_id)` so duplicates are possible.
- `attendances` has no uniqueness constraint for “one attendance per student per event” (if that is the intended rule).

**Fix direction:** add composite uniqueness (or composite PK) aligned with actual business rules.

### Issue 10 — Notification preferences mix independent multi-valued facts (4NF)
**Table:** `user_notification_preferences` (current schema)
- Channel settings (email vs sms + optional sms_number) are independent from topic settings (missed events, low attendance, etc.).
- Storing both sets in a single wide row is workable, but it’s not 4NF-friendly and makes extension harder.

**Fix direction:** decompose into:
- `user_notification_channel_settings(user_id, channel_code, enabled, address_value)`
- `user_notification_topic_settings(user_id, topic_code, enabled)`

(Keep the legacy `user_notification_preferences` table for compatibility; treat the decomposed tables as optional until the backend is updated to use them.)

## Compatibility Constraint (No Frontend Changes)

This plan assumes **no frontend changes**:
- REST routes, request bodies, and response shapes stay the same.
- Any schema change is isolated behind the backend (service/query + serialization), and/or via transitional DB compatibility views.

## Suggested Execution Order (If Migrating Production)

1. Create new normalized tables side-by-side (no drops).
2. Backfill from legacy columns/JSON into the new tables.
3. Add dual-write (backend writes both legacy + new for a transition window).
4. Switch reads to normalized tables (backend-only change).
5. Drop legacy columns/tables only after validation + metrics confirm parity.
