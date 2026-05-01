# Relationships

> **Status:** Maintained
> **Last Updated:** 2026-03-28
>
> **Scope:** Active relationships from `Backend/app/models/` and current migration head.

---

## Relationship Rules

- All tenant-scoped data should be traceable to `schools.id` directly or through a parent entity.
- Junction tables (`event_department_association`, `event_program_association`, `program_department_association`) implement many-to-many mappings with composite primary keys.
- `CASCADE`, `SET NULL`, and `RESTRICT` are used intentionally and should be preserved unless business logic changes.

## Core Relationships by Domain

### Tenant and Identity

| Parent | Child | Type | Notes |
|---|---|---|---|
| `schools` | `users` | one-to-many | User tenant scope. |
| `users` | `user_roles` | one-to-many | RBAC assignments. |
| `roles` | `user_roles` | one-to-many | RBAC role side. |
| `users` | `student_profiles` | one-to-one | One academic profile per user. |
| `schools` | `student_profiles` | one-to-many | Student tenant scope. |
| `departments` | `student_profiles` | one-to-many | Academic department mapping. |
| `programs` | `student_profiles` | one-to-many | Academic program mapping. |

### Academic and Event Scope

| Parent | Child | Type | Notes |
|---|---|---|---|
| `schools` | `departments` | one-to-many | Department tenant scope. |
| `schools` | `programs` | one-to-many | Program tenant scope. |
| `programs` | `program_department_association` | one-to-many | Program side of many-to-many. |
| `departments` | `program_department_association` | one-to-many | Department side of many-to-many. |
| `schools` | `events` | one-to-many | Event tenant scope. |
| `events` | `event_department_association` | one-to-many | Event scope by department. |
| `departments` | `event_department_association` | one-to-many | Department side of event mapping. |
| `events` | `event_program_association` | one-to-many | Event scope by program. |
| `programs` | `event_program_association` | one-to-many | Program side of event mapping. |

### Attendance and Face Recognition

| Parent | Child | Type | Notes |
|---|---|---|---|
| `events` | `attendances` | one-to-many | Attendance belongs to a specific event. |
| `student_profiles` | `attendances` | one-to-many | Attendance belongs to a specific student profile. |
| `users` | `attendances` (`verified_by`) | one-to-many (nullable) | Verifier reference uses `SET NULL` behavior. |
| `users` | `user_face_profiles` | one-to-one | Canonical per-user face embedding. |

### Security and Auth Operations

| Parent | Child | Type | Notes |
|---|---|---|---|
| `users` | `user_sessions` | one-to-many | Active and revoked session tracking. |
| `users` | `login_history` | one-to-many (nullable) | User link may be null for unknown attempts. |
| `schools` | `login_history` | one-to-many (nullable) | School link may be null for unknown scope. |
| `users` | `password_reset_requests` | one-to-many | Password reset targets and reviewers. |
| `schools` | `password_reset_requests` | one-to-many | School-scoped reset workflow. |

### Governance Hierarchy

| Parent | Child | Type | Notes |
|---|---|---|---|
| `schools` | `governance_units` | one-to-many | Governance unit tenant scope. |
| `governance_units` | `governance_units` (`parent_unit_id`) | one-to-many self-reference | Parent-child hierarchy (SSG -> SG -> ORG). |
| `governance_units` | `governance_members` | one-to-many | Unit memberships. |
| `users` | `governance_members` | one-to-many | Membership user reference. |
| `governance_units` | `governance_unit_permissions` | one-to-many | Unit-level permission assignments. |
| `governance_permissions` | `governance_unit_permissions` | one-to-many | Permission definition side. |
| `governance_members` | `governance_member_permissions` | one-to-many | Member-level permission assignments. |
| `governance_permissions` | `governance_member_permissions` | one-to-many | Permission definition side. |
| `governance_units` | `governance_announcements` | one-to-many | Unit-scoped announcements. |
| `governance_units` | `governance_student_notes` | one-to-many | Unit-scoped student notes. |
| `student_profiles` | `governance_student_notes` | one-to-many | Student note target. |

### Import, Notification, and Governance Operations

| Parent | Child | Type | Notes |
|---|---|---|---|
| `schools` | `bulk_import_jobs` | one-to-many | Import jobs scoped to target school. |
| `users` | `bulk_import_jobs` | one-to-many (nullable) | Job initiator may be null after user removal. |
| `bulk_import_jobs` | `bulk_import_errors` | one-to-many | Row errors per job. |
| `bulk_import_jobs` | `email_delivery_logs` | one-to-many (nullable link) | Email logs may persist even if job link is null. |
| `users` | `email_delivery_logs` | one-to-many (nullable) | Delivery target user link. |
| `users` | `user_notification_preferences` | one-to-one | Notification preference profile. |
| `schools` | `notification_logs` | one-to-many (nullable) | Notification tenant scope. |
| `users` | `notification_logs` | one-to-many (nullable) | User notification history. |

### Subscription, Privacy, and Audit

| Parent | Child | Type | Notes |
|---|---|---|---|
| `schools` | `school_settings` | one-to-one | Per-school branding and defaults. |
| `schools` | `school_audit_logs` | one-to-many | Audit trail records. |
| `schools` | `school_subscription_settings` | one-to-one | Subscription settings per school. |
| `schools` | `school_subscription_reminders` | one-to-many | Subscription reminder queue. |
| `schools` | `data_governance_settings` | one-to-one | Data retention settings per school. |
| `users` | `user_privacy_consents` | one-to-many | Consent history per user. |
| `schools` | `user_privacy_consents` | one-to-many | Consent tenant scope. |
| `schools` | `data_requests` | one-to-many | Privacy request lifecycle scope. |
| `users` | `data_requests` | one-to-many (nullable refs) | Requester, target, and handler references. |
| `schools` | `data_retention_run_logs` | one-to-many | Retention run execution history. |

## Critical Constraints and Relationship Integrity

| Rule | Why it matters |
|---|---|
| `student_profiles` must be unique by (`school_id`, `student_id`) | Prevents duplicate student identities in the same tenant. |
| `governance_members` unique on (`governance_unit_id`, `user_id`) | Prevents duplicate membership assignments. |
| Governance permission junctions enforce uniqueness | Prevents duplicate permission grants at both unit and member levels. |
| `user_sessions.token_jti` is unique | Enables reliable token revocation and replay protection checks. |
| Department and program names are unique per school | Keeps academic scoping deterministic for event and student assignment. |

## Legacy Relationship Note

The following legacy relationship pairs are not part of the active schema at current head and should not be documented as active:

- `events <-> ssg_profiles` via `event_ssg_association`
- Analytics legacy tables removed by `9b3e1f2c4d5a`

See also:

- [tables.md](./tables.md)
- [database-overview.md](./database-overview.md)
- [migrations.md](./migrations.md)
- [ERDv2.md](../ERD/ERDv2.md)
- [ERDGuide.md](../ERD/ERDGuide.md)
