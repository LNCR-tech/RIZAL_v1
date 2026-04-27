# Normalized Schema Workspace (`db_normalized/`)

This folder is a **playground** for proposing and iterating on a more-normalized database design for the current website schema.

- Current production-style schema dump: `db_schema.sql` (repo root)
- Human-readable snapshot: `db_schema_readable.md` (repo root)
- Proposed normalized target (playground): `db_normalized/new_db_schema.sql`

## What The Proposed Design Solves

The current schema is already fairly relational (many FK relationships + association tables), but it has a few consistent normalization/integrity pain points. The proposed target schema in `db_normalized/new_db_schema.sql` focuses on:

1. Reducing duplicated attributes (example: school branding + subscription state duplicated across multiple tables).
2. Replacing repeating-group JSON blobs with relational tables where the app needs to query/index/validate at the DB layer.
3. Reducing transitive redundancy (`school_id` stored on child tables where it is derivable through an FK chain) when safe.
4. Tightening link-table integrity (preventing duplicate rows in join tables via composite keys / unique constraints).
5. Pushing toward 4NF where a single table mixed independent multi-valued facts (example: notification channels vs notification topics).

## Current -> Target Mapping (High Level)

- `schools` -> `schools` + `school_branding` + `school_event_policies` + `school_subscriptions`
- `school_settings` -> `school_branding` + `school_event_policies`
- `school_subscription_settings` -> `school_subscriptions`
- `user_roles` -> same table name but normalized key design
- `attendances` -> `attendance_records` + lookup FKs (`attendance_statuses`, `attendance_methods`)
- `event_sanction_configs` -> split JSON definitions into `sanction_item_templates`
- `sanction_items` -> `sanction_record_items` + `sanction_item_attributes`
- `governance_student_notes` -> `governance_student_notes` + `governance_student_note_tags`
- `bulk_import_errors` -> `bulk_import_errors` + `bulk_import_error_cells`
- `notification_logs` -> `notification_logs` + `notification_log_attributes`
- `user_notification_preferences` -> keep legacy table for compatibility; optionally add `user_notification_channel_settings` + `user_notification_topic_settings` for 4NF decomposition
- `data_requests` -> `data_requests` + `data_request_items`

## Legacy Tables Intentionally Not Carried Forward

The `ssg_*` legacy tables are intentionally excluded from this normalized target because governance is already modeled in the modern `governance_*` tables.

## Notes for Future Migration Work

If we migrate from current production schema to this design, do it in phases:

1. Create new normalized tables side-by-side.
2. Backfill from legacy columns/JSON.
3. Add application dual-write for transition period.
4. Switch reads to normalized tables.
5. Remove old columns/tables after validation.

## Frontend Compatibility Constraint

This normalization work should **not** require frontend changes. The expected approach is:

- Keep REST endpoints, request bodies, and response shapes stable.
- Apply DB changes behind the API (backend service + model layer), or introduce DB-level compatibility views for transitional periods.

## ERD

Use `erd/index.html` to inspect the normalized table groups and relationships visually.
