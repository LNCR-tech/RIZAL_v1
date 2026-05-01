# Database Overview

> **Status:** Maintained
> **Last Updated:** 2026-03-28
>
> **Source of truth:**
> - `Backend/app/models/`
> - `Backend/alembic/versions/`
> - `docs/technical/ERD/ERDv2.md`

---

## Purpose

This document defines how data is structured, related, and controlled in the active database schema.

It is written to prevent:

- outdated schema descriptions
- missing table definitions
- unclear foreign-key and uniqueness behavior
- untracked migration changes
- weak security and data-handling documentation

## Active Stack Reference

| Item | Value |
|---|---|
| Database engine | PostgreSQL 15 (`docker-compose.yml`, `docker-compose.prod.yml`) |
| ORM | SQLAlchemy |
| Migration tool | Alembic |
| Active Alembic head | `b1a2c3d4e5f6` |
| Active schema table objects | 38 (including 3 association tables) |

## Active Table Groups

### 1. Tenant, Identity, and Academic Scope

- `schools`
- `users`
- `roles`
- `user_roles`
- `student_profiles`
- `departments`
- `programs`
- `program_department_association`

### 2. Events and Attendance

- `events`
- `attendances`
- `event_department_association`
- `event_program_association`

### 3. Auth and Security

- `user_sessions`
- `login_history`
- `password_reset_requests`
- `user_face_profiles`

### 4. Governance Hierarchy

- `governance_units`
- `governance_members`
- `governance_permissions`
- `governance_unit_permissions`
- `governance_member_permissions`
- `governance_announcements`
- `governance_student_notes`

### 5. Import, Notifications, and Operations

- `bulk_import_jobs`
- `bulk_import_errors`
- `email_delivery_logs`
- `user_notification_preferences`
- `notification_logs`

### 6. Governance, Privacy, Subscription, and Audit

- `school_settings`
- `school_audit_logs`
- `school_subscription_settings`
- `school_subscription_reminders`
- `data_governance_settings`
- `user_privacy_consents`
- `data_requests`
- `data_retention_run_logs`

## Data Integrity Controls

| Control type | Active examples |
|---|---|
| Primary keys | Standard PKs on all main tables and composite PKs in association tables |
| Unique constraints | `uq_student_profiles_school_student_id`, `uq_departments_school_name`, `uq_programs_school_name`, `uq_governance_units_school_unit_code`, unique `token_jti` in `user_sessions`, unique role names |
| Foreign keys with cascades | School-scoped and user-scoped relationships use `CASCADE`, `SET NULL`, or `RESTRICT` depending on domain behavior |
| Domain enums | Attendance status and governance permission/unit enums are constrained through typed columns and migrations |
| Indexed lookups | Frequent filters are indexed (`school_id`, `user_id`, status, created timestamps) |

## Security and Data Handling Notes

| Area | Implementation detail |
|---|---|
| Password storage | Passwords are stored as hashes (`users.password_hash`), not plaintext. |
| Session control | Session records are persisted in `user_sessions` using `token_jti`, with revocation support. |
| Face data handling | Face embeddings are stored as binary data in `user_face_profiles` and `student_profiles.face_encoding`. |
| Auditability | Security and data operations are tracked through `login_history`, `notification_logs`, and `school_audit_logs`. |
| Data governance | Retention and privacy request records are maintained in `data_governance_settings`, `data_requests`, and `data_retention_run_logs`. |

## Legacy Table Cleanup Status

The active schema excludes multiple legacy analytics and role-artifact tables.

- Migration `9b3e1f2c4d5a` drops unused legacy analytics and event tables.
- Migration `c3d91e4ab2f6` removes legacy governance role artifacts, including `ssg_profiles` and `event_ssg_association`.

These removed tables should not be documented as active tables.

## Requirement Traceability

| Requirement area | Database coverage |
|---|---|
| FR-01 Authentication and Session Management | `users`, `user_sessions`, `login_history`, `password_reset_requests` |
| FR-02 User Management | `users`, `student_profiles`, `departments`, `programs`, `bulk_import_jobs`, `bulk_import_errors`, `email_delivery_logs` |
| FR-03 Event Management | `events`, `event_department_association`, `event_program_association` |
| FR-04 Attendance | `attendances`, `user_face_profiles`, `student_profiles` |
| FR-05 Governance Hierarchy | `governance_units`, `governance_members`, `governance_permissions`, `governance_*` permission and content tables |
| FR-06 Notifications | `user_notification_preferences`, `notification_logs` |
| FR-07 Reporting and Audit | `school_audit_logs`, `school_subscription_*`, `data_governance_settings`, `user_privacy_consents`, `data_requests`, `data_retention_run_logs` |

## Verification Commands

```bash
# Show current migration state
docker compose exec backend alembic current

# Show migration history
docker compose exec backend alembic history

# Apply latest schema state
docker compose exec backend alembic upgrade head
```

See also:

- [tables.md](./tables.md)
- [relationships.md](./relationships.md)
- [migrations.md](./migrations.md)
- [ERDv2.md](../ERD/ERDv2.md)
