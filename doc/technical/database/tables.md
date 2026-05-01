# Tables Reference

> **Status:** Maintained
> **Last Updated:** 2026-03-28
>
> **Scope:** Active tables from `Backend/app/models/` plus active association tables.

---

## Purpose

This page provides a table-level dictionary for the current schema so table ownership, key fields, and constraints are explicit.

## Full Active Table Catalog

| Table | Primary key | Key foreign keys | Primary purpose |
|---|---|---|---|
| `schools` | `id` | - | Tenant root record for school-scoped data. |
| `school_settings` | `school_id` | `school_id -> schools.id`, `updated_by_user_id -> users.id` | Branding and default event settings per school. |
| `school_audit_logs` | `id` | `school_id -> schools.id`, `actor_user_id -> users.id` | Immutable school-level audit history. |
| `users` | `id` | `school_id -> schools.id` | User identity, auth flags, and account state. |
| `roles` | `id` | - | Role definitions for RBAC. |
| `user_roles` | `id` | `user_id -> users.id`, `role_id -> roles.id` | User-to-role assignments. |
| `student_profiles` | `id` | `user_id -> users.id`, `school_id -> schools.id`, `department_id -> departments.id`, `program_id -> programs.id` | Student academic profile and face-registration metadata. |
| `departments` | `id` | `school_id -> schools.id` | School-scoped departments. |
| `programs` | `id` | `school_id -> schools.id` | School-scoped programs. |
| `program_department_association` | (`program_id`, `department_id`) | `program_id -> programs.id`, `department_id -> departments.id` | Many-to-many link between programs and departments. |
| `events` | `id` | `school_id -> schools.id` | Event definitions, status, windows, and geofence fields. |
| `event_department_association` | (`event_id`, `department_id`) | `event_id -> events.id`, `department_id -> departments.id` | Event scope by department. |
| `event_program_association` | (`event_id`, `program_id`) | `event_id -> events.id`, `program_id -> programs.id` | Event scope by program. |
| `attendances` | `id` | `student_id -> student_profiles.id`, `event_id -> events.id`, `verified_by -> users.id` | Attendance records with method, status, and geolocation details. |
| `user_face_profiles` | `user_id` | `user_id -> users.id` | Canonical face embedding per user for recognition flows. |
| `user_sessions` | `id` | `user_id -> users.id` | Session tracking with revocation and expiry. |
| `login_history` | `id` | `user_id -> users.id`, `school_id -> schools.id` | Login attempt history, including failed attempts. |
| `password_reset_requests` | `id` | `user_id -> users.id`, `school_id -> schools.id`, `reviewed_by_user_id -> users.id` | Password reset request workflow state. |
| `bulk_import_jobs` | `id` | `created_by_user_id -> users.id`, `target_school_id -> schools.id` | Student import job execution metadata. |
| `bulk_import_errors` | `id` | `job_id -> bulk_import_jobs.id` | Row-level import validation and processing errors. |
| `email_delivery_logs` | `id` | `job_id -> bulk_import_jobs.id`, `user_id -> users.id` | Email delivery status and retry audit logs. |
| `user_notification_preferences` | `user_id` | `user_id -> users.id` | User notification channel and topic preferences. |
| `notification_logs` | `id` | `school_id -> schools.id`, `user_id -> users.id` | Notification delivery history and failure details. |
| `school_subscription_settings` | `school_id` | `school_id -> schools.id`, `updated_by_user_id -> users.id` | School subscription limits and billing settings. |
| `school_subscription_reminders` | `id` | `school_id -> schools.id` | Reminder queue for subscription lifecycle events. |
| `data_governance_settings` | `school_id` | `school_id -> schools.id`, `updated_by_user_id -> users.id` | School-level retention and auto-delete policy settings. |
| `user_privacy_consents` | `id` | `user_id -> users.id`, `school_id -> schools.id` | User consent records and consent version tracking. |
| `data_requests` | `id` | `school_id -> schools.id`, `requested_by_user_id -> users.id`, `target_user_id -> users.id`, `handled_by_user_id -> users.id` | Data export/delete request lifecycle tracking. |
| `data_retention_run_logs` | `id` | `school_id -> schools.id` | Retention run execution history. |
| `governance_units` | `id` | `school_id -> schools.id`, `parent_unit_id -> governance_units.id`, `department_id -> departments.id`, `program_id -> programs.id`, `created_by_user_id -> users.id` | Governance tree structure (SSG, SG, ORG). |
| `governance_members` | `id` | `governance_unit_id -> governance_units.id`, `user_id -> users.id`, `assigned_by_user_id -> users.id` | Membership assignments in governance units. |
| `governance_permissions` | `id` | - | Permission definitions used by governance access control. |
| `governance_unit_permissions` | `id` | `governance_unit_id -> governance_units.id`, `permission_id -> governance_permissions.id`, `granted_by_user_id -> users.id` | Permission assignments at unit level. |
| `governance_member_permissions` | `id` | `governance_member_id -> governance_members.id`, `permission_id -> governance_permissions.id`, `granted_by_user_id -> users.id` | Permission assignments at individual-member level. |
| `governance_announcements` | `id` | `governance_unit_id -> governance_units.id`, `school_id -> schools.id`, `created_by_user_id -> users.id`, `updated_by_user_id -> users.id` | Governance-scoped announcements with publication status. |
| `governance_student_notes` | `id` | `governance_unit_id -> governance_units.id`, `student_profile_id -> student_profiles.id`, `school_id -> schools.id`, `created_by_user_id -> users.id`, `updated_by_user_id -> users.id` | Governance-scoped student notes and tags. |

## Key Constraints to Know

| Constraint | Where it applies | Why it matters |
|---|---|---|
| Unique school student identity | `uq_student_profiles_school_student_id` | Prevents duplicate student IDs within the same school while allowing cross-school reuse. |
| Unique department name per school | `uq_departments_school_name` | Avoids duplicate department records inside one tenant. |
| Unique program name per school | `uq_programs_school_name` | Avoids duplicate program records inside one tenant. |
| Unique governance unit code per school | `uq_governance_units_school_unit_code` | Prevents conflicting governance unit codes in one school. |
| Unique governance member per unit | `uq_governance_members_unit_user` | Stops duplicate membership rows for the same user and governance unit. |
| Unique unit-permission pair | `uq_governance_unit_permissions_unit_permission` | Stops duplicate unit permission grants. |
| Unique member-permission pair | `uq_governance_member_permissions_member_permission` | Stops duplicate member permission grants. |
| Unique user session token ID | `user_sessions.token_jti` unique index | Supports secure session lookup and revocation by token identifier. |

## Legacy Table Note

The following legacy tables are intentionally not listed as active tables because cleanup migrations remove them in current schema state:

- `ssg_profiles`
- `event_ssg_association`
- `ai_logs`
- `anomaly_logs`
- `attendance_predictions`
- `event_predictions`
- `event_flags`
- `notifications`

See [migrations.md](./migrations.md) for the exact cleanup revisions.

See also:

- [database-overview.md](./database-overview.md)
- [relationships.md](./relationships.md)
- [migrations.md](./migrations.md)
