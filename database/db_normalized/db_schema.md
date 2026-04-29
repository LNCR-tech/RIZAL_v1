# Aura Database Schema

<!--nav-->
[Previous](../README.md) | [Next](../README.md) | [Home](/README.md)

---
<!--/nav-->


The live schema has 66 application tables across 8 domains. The SQL definition is in `db_schema.sql`. The ERD is in `erd/`.

---

## Lookup / Reference Tables

Small, mostly static tables that other tables reference via FK instead of storing raw strings.

| Table | Purpose |
|---|---|
| `roles` | Platform roles: `admin`, `campus_admin`, `student` |
| `attendance_statuses` | `present`, `late`, `absent`, `excused` |
| `attendance_methods` | `manual`, `face`, `rfid`, `qr` |
| `subscription_plans` | Plan tiers with user/event/import limits |
| `privacy_consent_types` | Consent categories (e.g. `privacy_policy`, `biometric_processing`) |
| `notification_channels` | `email`, `sms` |
| `notification_topics` | `missed_events`, `low_attendance`, etc. |
| `delivery_statuses` | `queued`, `sent`, `failed` |

---

## School Domain

A school is the top-level tenant. All data is scoped to a school.

| Table | Purpose |
|---|---|
| `schools` | Core school identity (name, code, address) |
| `school_branding` | Logo, colors â€” separated so branding can change without touching the school row |
| `school_event_policies` | Default event timing settings per school |
| `school_subscriptions` | Active plan, dates, renewal settings |
| `school_subscription_reminders` | Scheduled reminder log for upcoming renewals |
| `school_audit_logs` | Append-only log of admin actions |

---

## Users & Identity

| Table | Purpose |
|---|---|
| `users` | Core user record â€” email, password hash, name, school, import password flag |
| `user_roles` | Many-to-many: users â†” roles |
| `user_sessions` | Active JWT sessions |
| `mfa_challenges` | One-time MFA codes |
| `login_history` | Audit log of login attempts (success and failure) |
| `user_app_preferences` | UI preferences (dark mode, font size) |
| `user_security_settings` | MFA enabled, trusted device days |
| `user_notification_preferences` | Legacy flat notification prefs |
| `user_notification_channel_settings` | Per-channel opt-in (4NF decomposition) |
| `user_notification_topic_settings` | Per-topic opt-in (4NF decomposition) |
| `user_privacy_consents` | Consent records per user per consent type |

---

## Academic Structure

| Table | Purpose |
|---|---|
| `departments` | Colleges/departments within a school |
| `programs` | Degree programs within a school |
| `program_departments` | Many-to-many: programs â†” departments |
| `academic_periods` | School years and semesters (e.g. `2024-2025 1st Semester`) |
| `student_profiles` | Student-specific data: student number, year level, section, RFID |
| `faculty_profiles` | Faculty-specific data: department and program assignment |
| `student_face_embeddings` | pgvector face embeddings for face recognition attendance |

---

## Events & Attendance

| Table | Purpose |
|---|---|
| `event_types` | Global or school-specific event categories |
| `events` | School events with timing, geo, and status |
| `event_departments` | Scopes an event to specific departments |
| `event_programs` | Scopes an event to specific programs |
| `attendance_records` | One row per student per event â€” method, status, geo, liveness |

---

## Governance

Student government hierarchy: SSG â†’ SG â†’ ORG.

| Table | Purpose |
|---|---|
| `governance_units` | SSG, SG, and ORG units with parent-child hierarchy |
| `governance_permissions` | Permission catalog (e.g. `MANAGE_EVENTS`, `VIEW_STUDENTS`) |
| `governance_unit_permissions` | Permissions granted to a unit |
| `governance_members` | Users assigned to a governance unit with a position title |
| `governance_member_permissions` | Per-member permission overrides |
| `governance_announcements` | Announcements published by a governance unit |
| `governance_student_notes` | Internal notes on students written by governance officers |
| `governance_student_note_tags` | Tags on student notes (extracted from JSON for queryability) |

---

## Sanctions

| Table | Purpose |
|---|---|
| `event_sanction_configs` | Whether sanctions are enabled for an event |
| `sanction_item_templates` | The sanction items defined for an event (e.g. Apology Letter, Fine) |
| `sanction_records` | One sanction record per absent student per event |
| `sanction_record_items` | Individual items within a sanction record |
| `sanction_item_attributes` | Flexible key-value metadata on sanction items |
| `sanction_delegations` | Delegates sanction management to a governance unit |
| `sanction_delegation_departments` | Scopes a delegation to specific departments |
| `sanction_delegation_programs` | Scopes a delegation to specific programs |
| `sanction_compliance_history` | Audit trail of compliance actions per item |
| `clearance_deadlines` | Deadlines declared for sanction clearance |

---

## Imports, Notifications & Data Governance

| Table | Purpose |
|---|---|
| `bulk_import_jobs` | Excel student import jobs with status and progress |
| `bulk_import_errors` | Row-level errors from a failed import |
| `bulk_import_error_cells` | Cell-level detail for each import error |
| `email_delivery_logs` | Email delivery attempts and outcomes |
| `notification_logs` | In-app and email notification records |
| `notification_log_attributes` | Flexible metadata on notification logs |
| `password_reset_requests` | Admin-approved password reset requests |
| `data_governance_settings` | Retention policies per school |
| `data_requests` | Export or deletion requests |
| `data_request_items` | Items within a data request |
| `data_retention_run_logs` | Audit log of data retention runs |

