# ERD Guide: How to Read the Project ERD

> **Status:** Maintained
> **Last Updated:** 2026-03-28
>
> **Scope:** Active database structure represented in `ERDv2.md`.

---

## Purpose

This guide explains how to read the ERD accurately and map it to real models, migrations, and system features.

Use this guide to avoid:

- interpreting legacy entities as active
- misreading cardinality and junction tables
- losing traceability between ERD and backend schema

## Start Here

1. Open [ERDv2.md](./ERDv2.md).
2. Focus first on `ERD-v2-main` (`aura_db.png`).
3. Use [tables.md](../database/tables.md) and [relationships.md](../database/relationships.md) for exact definitions.

## Diagram Labels and What They Mean

| Label | Meaning |
|---|---|
| `ERD-v2-main` | Authoritative current schema visual. |
| `ERD-v2-desktop-capture` | Supplemental snapshot of v2 diagram. |
| `ERD-legacy-analytics` | Historical-only view; not the active schema baseline. |

## Read the ERD in This Order

1. Tenant boundary:
   - `schools`
2. Identity and access:
   - `users`, `roles`, `user_roles`, `student_profiles`
3. Academic scope:
   - `departments`, `programs`, `program_department_association`
4. Events and attendance:
   - `events`, `event_department_association`, `event_program_association`, `attendances`
5. Security and auth operations:
   - `user_sessions`, `login_history`, `password_reset_requests`, `user_face_profiles`
6. Governance hierarchy:
   - `governance_units`, `governance_members`, `governance_permissions`, `governance_unit_permissions`, `governance_member_permissions`, `governance_announcements`, `governance_student_notes`
7. Operational and compliance data:
   - `bulk_import_jobs`, `bulk_import_errors`, `email_delivery_logs`, `notification_logs`, `user_notification_preferences`, `school_audit_logs`, `school_subscription_*`, `data_governance_settings`, `user_privacy_consents`, `data_requests`, `data_retention_run_logs`

## Relationship Symbols and Patterns

| Pattern | How to recognize it | Example |
|---|---|---|
| One-to-many | Parent key referenced by many child rows | `schools -> users` |
| One-to-one | Child row keyed uniquely per parent | `users -> student_profiles` |
| Many-to-many | Two entities connected through junction table | `events <-> departments` via `event_department_association` |
| Self-reference | Row links to another row in same table | `governance_units.parent_unit_id -> governance_units.id` |

## Critical Relationship Checks

When validating ERD changes, verify:

1. Tenant scope remains explicit (`school_id` where needed).
2. Junction tables match declared many-to-many links.
3. Unique constraints still enforce identity and permission rules.
4. Removed legacy tables are not documented as active entities.

## Legacy vs Active Clarification

Active schema is based on current models and migration head.

Historical entities like:

- `ssg_profiles`
- `event_ssg_association`
- `ai_logs`
- `anomaly_logs`
- `attendance_predictions`

should only appear in legacy context, not in active relationship explanations.

## Traceability to Code and Docs

Use these together:

1. [ERDv2.md](./ERDv2.md)
2. [database-overview.md](../database/database-overview.md)
3. [tables.md](../database/tables.md)
4. [relationships.md](../database/relationships.md)
5. [migrations.md](../database/migrations.md)
6. `Backend/app/models/`
7. `Backend/alembic/versions/`

## 30-Second ERD Explanation Script

"The ERD is school-scoped, with `schools` as the tenant root. Identity starts at `users` and roles, events are scoped through department and program junction tables, and `attendances` is the transactional core. Governance tables model SSG, SG, and ORG hierarchy with explicit permission mapping. Security, import, notification, and data-governance tables support operations and compliance. We treat legacy analytics diagrams as historical and validate active ERD content against current models and Alembic migrations."

## Update Rule

When database schema changes:

1. Update migrations and verify revision head.
2. Recheck ERD labels and visuals in [ERDv2.md](./ERDv2.md).
3. Update this guide if relationship interpretation changed.
4. Update database docs in the same change set.
