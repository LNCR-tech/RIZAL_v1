# Database Schema (Readable)

Source: db_schema.sql
Generated: 2026-04-26 18:12:31 +08:00

- Tables: 54
- Enums: 3

## Enums

### attendancestatus
Values: present, absent, excused, late

### eventstatus
Values: UPCOMING, ONGOING, COMPLETED, CANCELLED

### ssg_event_status
Values: pending, approved, rejected

## Tables

### alembic_version

| Column | Type | Nullable | Default |
|---|---|---|---|
| version_num | character varying(32) | NO |  |

Primary key: version_num
Unique constraints: none
Foreign keys: none
Indexes: none

### attendances

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| student_id | integer | YES |  |
| event_id | integer | YES |  |
| time_in | timestamp with time zone | NO |  |
| time_out | timestamp with time zone | YES |  |
| method | character varying(50) | YES |  |
| status | attendancestatus | NO |  |
| verified_by | integer | YES |  |
| notes | character varying(500) | YES |  |
| geo_distance_m | double precision | YES |  |
| geo_effective_distance_m | double precision | YES |  |
| geo_latitude | double precision | YES |  |
| geo_longitude | double precision | YES |  |
| geo_accuracy_m | double precision | YES |  |
| liveness_label | character varying(32) | YES |  |
| liveness_score | double precision | YES |  |
| check_in_status | character varying(16) | YES |  |
| check_out_status | character varying(16) | YES |  |

Primary key: id
Unique constraints: none
Foreign keys:
- event_id -> events(id) (ON DELETE CASCADE)
- student_id -> student_profiles(id) (ON DELETE CASCADE)
- verified_by -> users(id) (ON DELETE SET NULL)
Indexes:
- ix_attendances_event_id: event_id
- ix_attendances_id: id
- ix_attendances_student_id: student_id

### bulk_import_errors

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| job_id | character varying(36) | NO |  |
| row_number | integer | NO |  |
| error_message | text | NO |  |
| row_data | json | YES |  |
| created_at | timestamp with time zone | NO | now() |

Primary key: id
Unique constraints: none
Foreign keys:
- job_id -> bulk_import_jobs(id) (ON DELETE CASCADE)
Indexes:
- ix_bulk_import_errors_job_id: job_id
- ix_bulk_import_errors_job_row: job_id, row_number

### bulk_import_jobs

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | character varying(36) | NO |  |
| created_by_user_id | integer | YES |  |
| status | character varying(20) | NO | 'pending'::character varying |
| original_filename | character varying(255) | NO |  |
| stored_file_path | character varying(1024) | NO |  |
| failed_report_path | character varying(1024) | YES |  |
| total_rows | integer | NO | 0 |
| processed_rows | integer | NO | 0 |
| success_count | integer | NO | 0 |
| failed_count | integer | NO | 0 |
| eta_seconds | integer | YES |  |
| error_summary | text | YES |  |
| is_rate_limited | boolean | NO | false |
| started_at | timestamp with time zone | YES |  |
| completed_at | timestamp with time zone | YES |  |
| created_at | timestamp with time zone | NO | now() |
| updated_at | timestamp with time zone | NO | now() |
| last_heartbeat | timestamp with time zone | YES |  |
| target_school_id | integer | NO |  |

Primary key: id
Unique constraints: none
Foreign keys:
- created_by_user_id -> users(id) (ON DELETE SET NULL)
- target_school_id -> schools(id) (ON DELETE CASCADE)
Indexes:
- ix_bulk_import_jobs_created_at: created_at
- ix_bulk_import_jobs_created_by_user_id: created_by_user_id
- ix_bulk_import_jobs_status: status
- ix_bulk_import_jobs_target_school_id: target_school_id

### clearance_deadlines

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| school_id | integer | NO |  |
| event_id | integer | NO |  |
| declared_by_user_id | integer | YES |  |
| target_governance_unit_id | integer | YES |  |
| deadline_at | timestamp with time zone | NO |  |
| status | character varying(7) | NO | 'active'::character varying |
| warning_email_sent_at | timestamp with time zone | YES |  |
| warning_popup_sent_at | timestamp with time zone | YES |  |
| message | text | YES |  |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |

Primary key: id
Unique constraints: none
Foreign keys:
- declared_by_user_id -> users(id) (ON DELETE SET NULL)
- event_id -> events(id) (ON DELETE CASCADE)
- school_id -> schools(id) (ON DELETE CASCADE)
- target_governance_unit_id -> governance_units(id) (ON DELETE SET NULL)
Indexes:
- ix_clearance_deadlines_created_at: created_at
- ix_clearance_deadlines_deadline_at: deadline_at
- ix_clearance_deadlines_declared_by_user_id: declared_by_user_id
- ix_clearance_deadlines_event_id: event_id
- ix_clearance_deadlines_id: id
- ix_clearance_deadlines_school_id: school_id
- ix_clearance_deadlines_status: status
- ix_clearance_deadlines_target_governance_unit_id: target_governance_unit_id

### data_governance_settings

| Column | Type | Nullable | Default |
|---|---|---|---|
| school_id | integer | NO |  |
| attendance_retention_days | integer | NO | 1095 |
| audit_log_retention_days | integer | NO | 3650 |
| import_file_retention_days | integer | NO | 180 |
| auto_delete_enabled | boolean | NO | false |
| updated_by_user_id | integer | YES |  |
| updated_at | timestamp with time zone | NO | now() |

Primary key: school_id
Unique constraints: none
Foreign keys:
- school_id -> schools(id) (ON DELETE CASCADE)
- updated_by_user_id -> users(id) (ON DELETE SET NULL)
Indexes: none

### data_requests

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| school_id | integer | NO |  |
| requested_by_user_id | integer | YES |  |
| target_user_id | integer | YES |  |
| request_type | character varying(20) | NO |  |
| scope | character varying(50) | NO | 'user_data'::character varying |
| status | character varying(20) | NO | 'pending'::character varying |
| reason | text | YES |  |
| details_json | json | YES |  |
| output_path | character varying(1024) | YES |  |
| handled_by_user_id | integer | YES |  |
| created_at | timestamp with time zone | NO | now() |
| resolved_at | timestamp with time zone | YES |  |

Primary key: id
Unique constraints: none
Foreign keys:
- handled_by_user_id -> users(id) (ON DELETE SET NULL)
- requested_by_user_id -> users(id) (ON DELETE SET NULL)
- school_id -> schools(id) (ON DELETE CASCADE)
- target_user_id -> users(id) (ON DELETE SET NULL)
Indexes:
- ix_data_requests_created_at: created_at
- ix_data_requests_request_type: request_type
- ix_data_requests_requested_by_user_id: requested_by_user_id
- ix_data_requests_school_id: school_id
- ix_data_requests_status: status
- ix_data_requests_target_user_id: target_user_id

### data_retention_run_logs

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| school_id | integer | NO |  |
| dry_run | boolean | NO | true |
| status | character varying(20) | NO | 'completed'::character varying |
| summary | text | YES |  |
| created_at | timestamp with time zone | NO | now() |

Primary key: id
Unique constraints: none
Foreign keys:
- school_id -> schools(id) (ON DELETE CASCADE)
Indexes:
- ix_data_retention_run_logs_created_at: created_at
- ix_data_retention_run_logs_school_id: school_id

### departments

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| name | character varying | NO |  |
| school_id | integer | YES |  |

Primary key: id
Unique constraints: school_id, name
Foreign keys:
- school_id -> schools(id) (ON DELETE CASCADE)
Indexes:
- ix_departments_id: id
- ix_departments_school_id: school_id

### email_delivery_logs

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| job_id | character varying(36) | YES |  |
| user_id | integer | YES |  |
| email | character varying(255) | NO |  |
| status | character varying(20) | NO |  |
| error_message | text | YES |  |
| retry_count | integer | NO | 0 |
| created_at | timestamp with time zone | NO | now() |
| updated_at | timestamp with time zone | NO | now() |

Primary key: id
Unique constraints: none
Foreign keys:
- job_id -> bulk_import_jobs(id) (ON DELETE SET NULL)
- user_id -> users(id) (ON DELETE SET NULL)
Indexes:
- ix_email_delivery_logs_email: email
- ix_email_delivery_logs_job_id: job_id
- ix_email_delivery_logs_status: status
- ix_email_delivery_logs_user_id: user_id

### event_department_association

| Column | Type | Nullable | Default |
|---|---|---|---|
| event_id | integer | NO |  |
| department_id | integer | NO |  |

Primary key: event_id, department_id
Unique constraints: none
Foreign keys:
- department_id -> departments(id) (ON DELETE CASCADE)
- event_id -> events(id) (ON DELETE CASCADE)
Indexes: none

### event_program_association

| Column | Type | Nullable | Default |
|---|---|---|---|
| event_id | integer | NO |  |
| program_id | integer | NO |  |

Primary key: event_id, program_id
Unique constraints: none
Foreign keys:
- event_id -> events(id) (ON DELETE CASCADE)
- program_id -> programs(id) (ON DELETE CASCADE)
Indexes: none

### event_sanction_configs

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| school_id | integer | NO |  |
| event_id | integer | NO |  |
| sanctions_enabled | boolean | NO | false |
| item_definitions_json | json | NO |  |
| created_by_user_id | integer | YES |  |
| updated_by_user_id | integer | YES |  |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |

Primary key: id
Unique constraints: event_id
Foreign keys:
- created_by_user_id -> users(id) (ON DELETE SET NULL)
- event_id -> events(id) (ON DELETE CASCADE)
- school_id -> schools(id) (ON DELETE CASCADE)
- updated_by_user_id -> users(id) (ON DELETE SET NULL)
Indexes:
- ix_event_sanction_configs_created_at: created_at
- ix_event_sanction_configs_created_by_user_id: created_by_user_id
- ix_event_sanction_configs_event_id: event_id
- ix_event_sanction_configs_id: id
- ix_event_sanction_configs_sanctions_enabled: sanctions_enabled
- ix_event_sanction_configs_school_id: school_id
- ix_event_sanction_configs_updated_by_user_id: updated_by_user_id

### event_types

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| school_id | integer | YES |  |
| name | character varying(100) | NO |  |
| code | character varying(50) | YES |  |
| description | text | YES |  |
| is_active | boolean | NO |  |
| sort_order | integer | NO |  |
| created_at | timestamp with time zone | NO |  |
| updated_at | timestamp with time zone | NO |  |

Primary key: id
Unique constraints: school_id, name
Foreign keys:
- school_id -> schools(id) (ON DELETE CASCADE)
Indexes:
- ix_event_types_id: id
- ix_event_types_school_id: school_id

### events

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| name | character varying(100) | NO |  |
| location | character varying(200) | YES |  |
| start_datetime | timestamp without time zone | NO |  |
| end_datetime | timestamp without time zone | NO |  |
| status | eventstatus | NO |  |
| school_id | integer | NO |  |
| late_threshold_minutes | integer | NO | 10 |
| geo_latitude | double precision | YES |  |
| geo_longitude | double precision | YES |  |
| geo_radius_m | double precision | YES |  |
| geo_required | boolean | NO | false |
| geo_max_accuracy_m | double precision | YES |  |
| early_check_in_minutes | integer | NO |  |
| sign_out_grace_minutes | integer | NO |  |
| sign_out_override_until | timestamp without time zone | YES |  |
| present_until_override_at | timestamp without time zone | YES |  |
| late_until_override_at | timestamp without time zone | YES |  |
| sign_out_open_delay_minutes | integer | NO |  |
| event_type_id | integer | YES |  |
| created_by_user_id | integer | YES |  |
| create_idempotency_key | character varying(128) | YES |  |

Primary key: id
Unique constraints: created_by_user_id, create_idempotency_key
Foreign keys:
- created_by_user_id -> users(id) (ON DELETE SET NULL)
- event_type_id -> event_types(id) (ON DELETE SET NULL)
- school_id -> schools(id) (ON DELETE CASCADE)
Indexes:
- ix_events_created_by_user_id: created_by_user_id
- ix_events_event_type_id: event_type_id
- ix_events_id: id
- ix_events_school_id: school_id

### faculty_profiles

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| user_id | integer | NO |  |
| department_id | integer | YES |  |
| program_id | integer | YES |  |

Primary key: id
Unique constraints: user_id
Foreign keys:
- department_id -> departments(id) (ON DELETE SET NULL)
- program_id -> programs(id) (ON DELETE SET NULL)
- user_id -> users(id) (ON DELETE CASCADE)
Indexes:
- ix_faculty_profiles_department_id: department_id
- ix_faculty_profiles_id: id
- ix_faculty_profiles_program_id: program_id
- ix_faculty_profiles_user_id: user_id

### governance_announcements

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| governance_unit_id | integer | NO |  |
| school_id | integer | NO |  |
| title | character varying(255) | NO |  |
| body | text | NO |  |
| status | character varying(9) | NO | 'draft'::character varying |
| created_by_user_id | integer | YES |  |
| updated_by_user_id | integer | YES |  |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |

Primary key: id
Unique constraints: none
Foreign keys:
- created_by_user_id -> users(id) (ON DELETE SET NULL)
- governance_unit_id -> governance_units(id) (ON DELETE CASCADE)
- school_id -> schools(id) (ON DELETE CASCADE)
- updated_by_user_id -> users(id) (ON DELETE SET NULL)
Indexes:
- ix_governance_announcements_governance_unit_id: governance_unit_id
- ix_governance_announcements_school_id: school_id
- ix_governance_announcements_status: status

### governance_member_permissions

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| governance_member_id | integer | NO |  |
| permission_id | integer | NO |  |
| granted_by_user_id | integer | YES |  |
| created_at | timestamp with time zone | NO | now() |

Primary key: id
Unique constraints: governance_member_id, permission_id
Foreign keys:
- governance_member_id -> governance_members(id) (ON DELETE CASCADE)
- granted_by_user_id -> users(id) (ON DELETE SET NULL)
- permission_id -> governance_permissions(id) (ON DELETE CASCADE)
Indexes:
- ix_governance_member_permissions_created_at: created_at
- ix_governance_member_permissions_governance_member_id: governance_member_id
- ix_governance_member_permissions_granted_by_user_id: granted_by_user_id
- ix_governance_member_permissions_id: id
- ix_governance_member_permissions_permission_id: permission_id

### governance_members

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| governance_unit_id | integer | NO |  |
| user_id | integer | NO |  |
| position_title | character varying(100) | YES |  |
| assigned_by_user_id | integer | YES |  |
| assigned_at | timestamp with time zone | NO | now() |
| is_active | boolean | NO | true |

Primary key: id
Unique constraints: governance_unit_id, user_id
Foreign keys:
- assigned_by_user_id -> users(id) (ON DELETE SET NULL)
- governance_unit_id -> governance_units(id) (ON DELETE CASCADE)
- user_id -> users(id) (ON DELETE CASCADE)
Indexes:
- ix_governance_members_assigned_by_user_id: assigned_by_user_id
- ix_governance_members_governance_unit_id: governance_unit_id
- ix_governance_members_id: id
- ix_governance_members_is_active: is_active
- ix_governance_members_user_id: user_id

### governance_permissions

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| permission_code | character varying(29) | NO |  |
| permission_name | character varying(100) | NO |  |
| description | text | YES |  |

Primary key: id
Unique constraints: none
Foreign keys: none
Indexes:
- ix_governance_permissions_id: id
- UNIQUE ix_governance_permissions_permission_code: permission_code

### governance_student_notes

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| governance_unit_id | integer | NO |  |
| student_profile_id | integer | NO |  |
| school_id | integer | NO |  |
| tags | json | NO |  |
| notes | text | NO | ''::text |
| created_by_user_id | integer | YES |  |
| updated_by_user_id | integer | YES |  |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |

Primary key: id
Unique constraints: governance_unit_id, student_profile_id
Foreign keys:
- created_by_user_id -> users(id) (ON DELETE SET NULL)
- governance_unit_id -> governance_units(id) (ON DELETE CASCADE)
- school_id -> schools(id) (ON DELETE CASCADE)
- student_profile_id -> student_profiles(id) (ON DELETE CASCADE)
- updated_by_user_id -> users(id) (ON DELETE SET NULL)
Indexes:
- ix_governance_student_notes_governance_unit_id: governance_unit_id
- ix_governance_student_notes_school_id: school_id
- ix_governance_student_notes_student_profile_id: student_profile_id

### governance_unit_permissions

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| governance_unit_id | integer | NO |  |
| permission_id | integer | NO |  |
| granted_by_user_id | integer | YES |  |
| created_at | timestamp with time zone | NO | now() |

Primary key: id
Unique constraints: governance_unit_id, permission_id
Foreign keys:
- governance_unit_id -> governance_units(id) (ON DELETE CASCADE)
- granted_by_user_id -> users(id) (ON DELETE SET NULL)
- permission_id -> governance_permissions(id) (ON DELETE CASCADE)
Indexes:
- ix_governance_unit_permissions_created_at: created_at
- ix_governance_unit_permissions_governance_unit_id: governance_unit_id
- ix_governance_unit_permissions_granted_by_user_id: granted_by_user_id
- ix_governance_unit_permissions_id: id
- ix_governance_unit_permissions_permission_id: permission_id

### governance_units

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| unit_code | character varying(50) | NO |  |
| unit_name | character varying(255) | NO |  |
| unit_type | character varying(3) | NO |  |
| parent_unit_id | integer | YES |  |
| school_id | integer | NO |  |
| department_id | integer | YES |  |
| program_id | integer | YES |  |
| created_by_user_id | integer | YES |  |
| is_active | boolean | NO | true |
| created_at | timestamp with time zone | NO | now() |
| updated_at | timestamp with time zone | NO | now() |
| description | text | YES |  |
| event_default_early_check_in_minutes | integer | YES |  |
| event_default_late_threshold_minutes | integer | YES |  |
| event_default_sign_out_grace_minutes | integer | YES |  |

Primary key: id
Unique constraints: school_id, unit_code
Foreign keys:
- created_by_user_id -> users(id) (ON DELETE SET NULL)
- department_id -> departments(id) (ON DELETE SET NULL)
- parent_unit_id -> governance_units(id) (ON DELETE SET NULL)
- program_id -> programs(id) (ON DELETE SET NULL)
- school_id -> schools(id) (ON DELETE CASCADE)
Indexes:
- ix_governance_units_created_by_user_id: created_by_user_id
- ix_governance_units_department_id: department_id
- ix_governance_units_id: id
- ix_governance_units_is_active: is_active
- ix_governance_units_parent_unit_id: parent_unit_id
- ix_governance_units_program_id: program_id
- ix_governance_units_school_id: school_id
- ix_governance_units_unit_code: unit_code
- ix_governance_units_unit_type: unit_type
- UNIQUE uq_governance_units_single_ssg_per_school: school_id) WHERE ((unit_type)::text = 'SSG'::text

### login_history

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| user_id | integer | YES |  |
| school_id | integer | YES |  |
| email_attempted | character varying(255) | NO |  |
| success | boolean | NO | false |
| auth_method | character varying(30) | NO | 'password'::character varying |
| failure_reason | character varying(255) | YES |  |
| ip_address | character varying(64) | YES |  |
| user_agent | character varying(500) | YES |  |
| created_at | timestamp with time zone | NO | now() |

Primary key: id
Unique constraints: none
Foreign keys:
- school_id -> schools(id) (ON DELETE SET NULL)
- user_id -> users(id) (ON DELETE SET NULL)
Indexes:
- ix_login_history_created_at: created_at
- ix_login_history_email_attempted: email_attempted
- ix_login_history_school_id: school_id
- ix_login_history_success: success
- ix_login_history_user_id: user_id

### mfa_challenges

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | character varying(36) | NO |  |
| user_id | integer | NO |  |
| code_hash | character varying(255) | NO |  |
| channel | character varying(20) | NO | 'email'::character varying |
| attempts | integer | NO | 0 |
| expires_at | timestamp with time zone | NO |  |
| consumed_at | timestamp with time zone | YES |  |
| ip_address | character varying(64) | YES |  |
| user_agent | character varying(500) | YES |  |
| created_at | timestamp with time zone | NO | now() |

Primary key: id
Unique constraints: none
Foreign keys:
- user_id -> users(id) (ON DELETE CASCADE)
Indexes:
- ix_mfa_challenges_created_at: created_at
- ix_mfa_challenges_expires_at: expires_at
- ix_mfa_challenges_user_id: user_id

### notification_logs

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| school_id | integer | YES |  |
| user_id | integer | YES |  |
| category | character varying(50) | NO |  |
| channel | character varying(20) | NO | 'email'::character varying |
| status | character varying(20) | NO | 'queued'::character varying |
| subject | character varying(255) | NO |  |
| message | text | NO |  |
| error_message | text | YES |  |
| metadata_json | json | YES |  |
| created_at | timestamp with time zone | NO | now() |

Primary key: id
Unique constraints: none
Foreign keys:
- school_id -> schools(id) (ON DELETE CASCADE)
- user_id -> users(id) (ON DELETE SET NULL)
Indexes:
- ix_notification_logs_category: category
- ix_notification_logs_created_at: created_at
- ix_notification_logs_school_id: school_id
- ix_notification_logs_status: status
- ix_notification_logs_user_id: user_id

### password_reset_requests

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| user_id | integer | NO |  |
| school_id | integer | NO |  |
| requested_email | character varying(255) | NO |  |
| status | character varying(20) | NO | 'pending'::character varying |
| requested_at | timestamp with time zone | NO | now() |
| resolved_at | timestamp with time zone | YES |  |
| reviewed_by_user_id | integer | YES |  |

Primary key: id
Unique constraints: none
Foreign keys:
- reviewed_by_user_id -> users(id) (ON DELETE SET NULL)
- school_id -> schools(id) (ON DELETE CASCADE)
- user_id -> users(id) (ON DELETE CASCADE)
Indexes:
- ix_password_reset_requests_id: id
- ix_password_reset_requests_requested_at: requested_at
- ix_password_reset_requests_requested_email: requested_email
- ix_password_reset_requests_reviewed_by_user_id: reviewed_by_user_id
- ix_password_reset_requests_school_id: school_id
- ix_password_reset_requests_status: status
- ix_password_reset_requests_user_id: user_id

### program_department_association

| Column | Type | Nullable | Default |
|---|---|---|---|
| program_id | integer | NO |  |
| department_id | integer | NO |  |

Primary key: program_id, department_id
Unique constraints: none
Foreign keys:
- department_id -> departments(id) (ON DELETE CASCADE)
- program_id -> programs(id) (ON DELETE CASCADE)
Indexes: none

### programs

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| name | character varying | NO |  |
| school_id | integer | YES |  |

Primary key: id
Unique constraints: school_id, name
Foreign keys:
- school_id -> schools(id) (ON DELETE CASCADE)
Indexes:
- ix_programs_id: id
- ix_programs_school_id: school_id

### roles

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| name | character varying(50) | NO |  |

Primary key: id
Unique constraints: none
Foreign keys: none
Indexes:
- UNIQUE ix_roles_name: name

### sanction_compliance_history

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| school_id | integer | NO |  |
| event_id | integer | YES |  |
| sanction_record_id | integer | YES |  |
| sanction_item_id | integer | YES |  |
| student_profile_id | integer | YES |  |
| complied_on | date | NO | CURRENT_DATE |
| school_year | character varying(20) | NO |  |
| semester | character varying(20) | NO |  |
| complied_by_user_id | integer | YES |  |
| notes | text | YES |  |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |

Primary key: id
Unique constraints: none
Foreign keys:
- complied_by_user_id -> users(id) (ON DELETE SET NULL)
- event_id -> events(id) (ON DELETE SET NULL)
- sanction_item_id -> sanction_items(id) (ON DELETE SET NULL)
- sanction_record_id -> sanction_records(id) (ON DELETE SET NULL)
- school_id -> schools(id) (ON DELETE CASCADE)
- student_profile_id -> student_profiles(id) (ON DELETE SET NULL)
Indexes:
- ix_sanction_compliance_history_complied_by_user_id: complied_by_user_id
- ix_sanction_compliance_history_complied_on: complied_on
- ix_sanction_compliance_history_created_at: created_at
- ix_sanction_compliance_history_event_id: event_id
- ix_sanction_compliance_history_id: id
- ix_sanction_compliance_history_sanction_item_id: sanction_item_id
- ix_sanction_compliance_history_sanction_record_id: sanction_record_id
- ix_sanction_compliance_history_school_id: school_id
- ix_sanction_compliance_history_school_year: school_year
- ix_sanction_compliance_history_semester: semester
- ix_sanction_compliance_history_student_profile_id: student_profile_id

### sanction_delegations

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| school_id | integer | NO |  |
| event_id | integer | NO |  |
| sanction_config_id | integer | YES |  |
| delegated_by_user_id | integer | YES |  |
| delegated_to_governance_unit_id | integer | NO |  |
| scope_type | character varying(10) | NO | 'unit'::character varying |
| scope_json | json | YES |  |
| is_active | boolean | NO | true |
| revoked_at | timestamp with time zone | YES |  |
| revoked_by_user_id | integer | YES |  |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |

Primary key: id
Unique constraints: event_id, delegated_to_governance_unit_id
Foreign keys:
- delegated_by_user_id -> users(id) (ON DELETE SET NULL)
- delegated_to_governance_unit_id -> governance_units(id) (ON DELETE CASCADE)
- event_id -> events(id) (ON DELETE CASCADE)
- revoked_by_user_id -> users(id) (ON DELETE SET NULL)
- sanction_config_id -> event_sanction_configs(id) (ON DELETE SET NULL)
- school_id -> schools(id) (ON DELETE CASCADE)
Indexes:
- ix_sanction_delegations_created_at: created_at
- ix_sanction_delegations_delegated_by_user_id: delegated_by_user_id
- ix_sanction_delegations_delegated_to_governance_unit_id: delegated_to_governance_unit_id
- ix_sanction_delegations_event_id: event_id
- ix_sanction_delegations_id: id
- ix_sanction_delegations_is_active: is_active
- ix_sanction_delegations_revoked_by_user_id: revoked_by_user_id
- ix_sanction_delegations_sanction_config_id: sanction_config_id
- ix_sanction_delegations_school_id: school_id
- ix_sanction_delegations_scope_type: scope_type

### sanction_items

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| sanction_record_id | integer | NO |  |
| item_code | character varying(64) | YES |  |
| item_name | character varying(255) | NO |  |
| item_description | text | YES |  |
| status | character varying(8) | NO | 'pending'::character varying |
| complied_at | timestamp with time zone | YES |  |
| compliance_notes | text | YES |  |
| metadata_json | json | YES |  |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |

Primary key: id
Unique constraints: sanction_record_id, item_code
Foreign keys:
- sanction_record_id -> sanction_records(id) (ON DELETE CASCADE)
Indexes:
- ix_sanction_items_complied_at: complied_at
- ix_sanction_items_created_at: created_at
- ix_sanction_items_id: id
- ix_sanction_items_item_code: item_code
- ix_sanction_items_sanction_record_id: sanction_record_id
- ix_sanction_items_status: status

### sanction_records

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| school_id | integer | NO |  |
| event_id | integer | NO |  |
| sanction_config_id | integer | YES |  |
| student_profile_id | integer | NO |  |
| attendance_id | integer | YES |  |
| delegated_governance_unit_id | integer | YES |  |
| status | character varying(8) | NO | 'pending'::character varying |
| assigned_by_user_id | integer | YES |  |
| complied_at | timestamp with time zone | YES |  |
| notes | text | YES |  |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |

Primary key: id
Unique constraints: event_id, student_profile_id
Foreign keys:
- assigned_by_user_id -> users(id) (ON DELETE SET NULL)
- attendance_id -> attendances(id) (ON DELETE SET NULL)
- delegated_governance_unit_id -> governance_units(id) (ON DELETE SET NULL)
- event_id -> events(id) (ON DELETE CASCADE)
- sanction_config_id -> event_sanction_configs(id) (ON DELETE SET NULL)
- school_id -> schools(id) (ON DELETE CASCADE)
- student_profile_id -> student_profiles(id) (ON DELETE CASCADE)
Indexes:
- ix_sanction_records_assigned_by_user_id: assigned_by_user_id
- ix_sanction_records_attendance_id: attendance_id
- ix_sanction_records_complied_at: complied_at
- ix_sanction_records_created_at: created_at
- ix_sanction_records_delegated_governance_unit_id: delegated_governance_unit_id
- ix_sanction_records_event_id: event_id
- ix_sanction_records_id: id
- ix_sanction_records_sanction_config_id: sanction_config_id
- ix_sanction_records_school_id: school_id
- ix_sanction_records_status: status
- ix_sanction_records_student_profile_id: student_profile_id

### school_audit_logs

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| school_id | integer | NO |  |
| actor_user_id | integer | YES |  |
| action | character varying(100) | NO |  |
| status | character varying(30) | NO | 'success'::character varying |
| details | text | YES |  |
| created_at | timestamp with time zone | NO | now() |

Primary key: id
Unique constraints: none
Foreign keys:
- actor_user_id -> users(id) (ON DELETE SET NULL)
- school_id -> schools(id) (ON DELETE CASCADE)
Indexes:
- ix_school_audit_logs_actor_user_id: actor_user_id
- ix_school_audit_logs_created_at: created_at
- ix_school_audit_logs_school_id: school_id

### school_settings

| Column | Type | Nullable | Default |
|---|---|---|---|
| school_id | integer | NO |  |
| primary_color | character varying(7) | NO | '#162F65'::character varying |
| secondary_color | character varying(7) | NO | '#2C5F9E'::character varying |
| accent_color | character varying(7) | NO | '#4A90E2'::character varying |
| updated_at | timestamp with time zone | NO | now() |
| updated_by_user_id | integer | YES |  |
| event_default_early_check_in_minutes | integer | NO |  |
| event_default_late_threshold_minutes | integer | NO |  |
| event_default_sign_out_grace_minutes | integer | NO |  |

Primary key: school_id
Unique constraints: none
Foreign keys:
- school_id -> schools(id) (ON DELETE CASCADE)
- updated_by_user_id -> users(id) (ON DELETE SET NULL)
Indexes: none

### school_subscription_reminders

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| school_id | integer | NO |  |
| reminder_type | character varying(40) | NO | 'renewal_warning'::character varying |
| status | character varying(20) | NO | 'pending'::character varying |
| due_at | timestamp with time zone | NO |  |
| sent_at | timestamp with time zone | YES |  |
| error_message | text | YES |  |
| created_at | timestamp with time zone | NO | now() |

Primary key: id
Unique constraints: none
Foreign keys:
- school_id -> schools(id) (ON DELETE CASCADE)
Indexes:
- ix_school_subscription_reminders_due_at: due_at
- ix_school_subscription_reminders_school_id: school_id
- ix_school_subscription_reminders_status: status

### school_subscription_settings

| Column | Type | Nullable | Default |
|---|---|---|---|
| school_id | integer | NO |  |
| plan_name | character varying(50) | NO | 'free'::character varying |
| user_limit | integer | NO | 500 |
| event_limit_monthly | integer | NO | 100 |
| import_limit_monthly | integer | NO | 10 |
| renewal_date | date | YES |  |
| auto_renew | boolean | NO | false |
| reminder_days_before | integer | NO | 14 |
| updated_by_user_id | integer | YES |  |
| updated_at | timestamp with time zone | NO | now() |

Primary key: school_id
Unique constraints: none
Foreign keys:
- school_id -> schools(id) (ON DELETE CASCADE)
- updated_by_user_id -> users(id) (ON DELETE SET NULL)
Indexes: none

### schools

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| name | character varying(255) | NO |  |
| address | character varying(500) | NO |  |
| logo_url | character varying(1000) | YES |  |
| subscription_plan | character varying(100) | NO | 'free'::character varying |
| subscription_start | date | NO | CURRENT_DATE |
| subscription_end | date | YES |  |
| created_at | timestamp with time zone | NO | now() |
| updated_at | timestamp with time zone | NO | now() |
| school_name | character varying(255) | NO |  |
| school_code | character varying(50) | YES |  |
| primary_color | character varying(7) | NO | '#162F65'::character varying |
| secondary_color | character varying(7) | YES |  |
| subscription_status | character varying(30) | NO | 'trial'::character varying |
| active_status | boolean | NO | true |

Primary key: id
Unique constraints: none
Foreign keys: none
Indexes:
- UNIQUE ix_schools_school_code: school_code
- ix_schools_school_name: school_name

### ssg_announcements

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| school_id | integer | NO |  |
| title | character varying(150) | NO |  |
| message | text | NO |  |
| created_by | integer | YES |  |
| created_at | timestamp without time zone | NO | now() |

Primary key: id
Unique constraints: none
Foreign keys:
- created_by -> users(id) (ON DELETE SET NULL)
- school_id -> schools(id) (ON DELETE CASCADE)
Indexes:
- ix_ssg_announcements_school_id: school_id

### ssg_events

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| school_id | integer | NO |  |
| title | character varying(150) | NO |  |
| description | text | YES |  |
| event_date | timestamp without time zone | NO |  |
| created_by | integer | YES |  |
| status | ssg_event_status | NO | 'pending'::public.ssg_event_status |
| approved_by | integer | YES |  |
| created_at | timestamp without time zone | NO | now() |
| approved_at | timestamp without time zone | YES |  |
| location | character varying(200) | YES |  |
| notification_sent | boolean | NO | false |
| start_time | timestamp without time zone | NO | now() |
| end_time | timestamp without time zone | NO | now() |
| late_threshold_minutes | integer | NO | 10 |

Primary key: id
Unique constraints: none
Foreign keys:
- approved_by -> users(id) (ON DELETE SET NULL)
- created_by -> users(id) (ON DELETE SET NULL)
- school_id -> schools(id) (ON DELETE CASCADE)
Indexes:
- ix_ssg_events_event_date: event_date
- ix_ssg_events_school_id: school_id
- ix_ssg_events_status: status

### ssg_permissions

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| permission_name | character varying(100) | NO |  |
| created_at | timestamp without time zone | NO | now() |

Primary key: id
Unique constraints: none
Foreign keys: none
Indexes:
- UNIQUE ix_ssg_permissions_permission_name: permission_name

### ssg_role_permissions

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| role_id | integer | NO |  |
| permission_id | integer | NO |  |

Primary key: id
Unique constraints: role_id, permission_id
Foreign keys:
- permission_id -> ssg_permissions(id) (ON DELETE CASCADE)
- role_id -> ssg_roles(id) (ON DELETE CASCADE)
Indexes:
- ix_ssg_role_permissions_permission_id: permission_id
- ix_ssg_role_permissions_role_id: role_id

### ssg_roles

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| school_id | integer | NO |  |
| role_name | character varying(100) | NO |  |
| max_members | integer | YES |  |
| created_at | timestamp without time zone | NO | now() |

Primary key: id
Unique constraints: school_id, role_name
Foreign keys:
- school_id -> schools(id) (ON DELETE CASCADE)
Indexes:
- ix_ssg_roles_school_id: school_id

### ssg_user_roles

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| user_id | integer | NO |  |
| role_id | integer | NO |  |
| school_year | character varying(20) | NO |  |
| assigned_at | timestamp without time zone | NO | now() |

Primary key: id
Unique constraints: user_id, role_id, school_year
Foreign keys:
- role_id -> ssg_roles(id) (ON DELETE CASCADE)
- user_id -> users(id) (ON DELETE CASCADE)
Indexes:
- ix_ssg_user_roles_role_id: role_id
- ix_ssg_user_roles_school_year: school_year
- ix_ssg_user_roles_user_id: user_id

### student_profiles

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| user_id | integer | YES |  |
| student_id | character varying(50) | YES |  |
| department_id | integer | YES |  |
| program_id | integer | YES |  |
| year_level | integer | NO |  |
| face_encoding | bytea | YES |  |
| is_face_registered | boolean | YES |  |
| face_image_url | character varying(500) | YES |  |
| registration_complete | boolean | YES |  |
| section | character varying(50) | YES |  |
| rfid_tag | character varying(100) | YES |  |
| last_face_update | timestamp with time zone | YES |  |
| school_id | integer | NO |  |
| embedding_provider | character varying(32) | YES |  |
| embedding_dtype | character varying(16) | YES |  |
| embedding_dimension | integer | YES |  |
| embedding_normalized | boolean | NO |  |

Primary key: id
Unique constraints: rfid_tag, school_id, student_id
Foreign keys:
- school_id -> schools(id) (ON DELETE CASCADE)
- department_id -> departments(id) (ON DELETE RESTRICT)
- program_id -> programs(id) (ON DELETE RESTRICT)
- user_id -> users(id) (ON DELETE CASCADE)
Indexes:
- ix_student_profiles_department_id: department_id
- ix_student_profiles_is_face_registered: is_face_registered
- ix_student_profiles_program_id: program_id
- ix_student_profiles_registration_complete: registration_complete
- ix_student_profiles_school_id: school_id
- ix_student_profiles_school_student_id: school_id, student_id
- ix_student_profiles_section: section
- ix_student_profiles_student_id: student_id
- UNIQUE ix_student_profiles_user_id: user_id

### user_app_preferences

| Column | Type | Nullable | Default |
|---|---|---|---|
| user_id | integer | NO |  |
| dark_mode_enabled | boolean | NO | false |
| font_size_percent | integer | NO | 100 |
| updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |

Primary key: user_id
Unique constraints: none
Foreign keys:
- user_id -> users(id) (ON DELETE CASCADE)
Indexes: none

### user_roles

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| user_id | integer | YES |  |
| role_id | integer | YES |  |

Primary key: id
Unique constraints: none
Foreign keys:
- role_id -> roles(id) (ON DELETE CASCADE)
- user_id -> users(id) (ON DELETE CASCADE)
Indexes:
- ix_user_roles_role_id: role_id
- ix_user_roles_user_id: user_id

### users

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| email | character varying(255) | NO |  |
| password_hash | character varying(255) | NO |  |
| first_name | character varying(100) | YES |  |
| middle_name | character varying(100) | YES |  |
| last_name | character varying(100) | YES |  |
| is_active | boolean | YES |  |
| created_at | timestamp with time zone | NO |  |
| school_id | integer | YES |  |
| must_change_password | boolean | NO | true |
| should_prompt_password_change | boolean | NO |  |
| prefix | character varying(20) | YES |  |
| suffix | character varying(20) | YES |  |

Primary key: id
Unique constraints: none
Foreign keys:
- school_id -> schools(id) (ON DELETE CASCADE)
Indexes:
- UNIQUE ix_users_email: email
- ix_users_id: id
- ix_users_is_active: is_active
- ix_users_school_id: school_id

### user_face_profiles

| Column | Type | Nullable | Default |
|---|---|---|---|
| user_id | integer | NO |  |
| face_encoding | bytea | NO |  |
| provider | character varying(50) | NO | 'face_recognition'::character varying |
| reference_image_sha256 | character varying(64) | YES |  |
| last_verified_at | timestamp with time zone | YES |  |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |

Primary key: user_id
Unique constraints: none
Foreign keys:
- user_id -> users(id) (ON DELETE CASCADE)
Indexes: none

### user_notification_preferences

| Column | Type | Nullable | Default |
|---|---|---|---|
| user_id | integer | NO |  |
| email_enabled | boolean | NO | true |
| sms_enabled | boolean | NO | false |
| sms_number | character varying(40) | YES |  |
| notify_missed_events | boolean | NO | true |
| notify_low_attendance | boolean | NO | true |
| notify_account_security | boolean | NO | true |
| notify_subscription | boolean | NO | true |
| updated_at | timestamp with time zone | NO | now() |

Primary key: user_id
Unique constraints: none
Foreign keys:
- user_id -> users(id) (ON DELETE CASCADE)
Indexes: none

### user_privacy_consents

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | integer | NO |  |
| user_id | integer | NO |  |
| school_id | integer | NO |  |
| consent_type | character varying(50) | NO |  |
| consent_granted | boolean | NO | true |
| consent_version | character varying(20) | NO | 'v1'::character varying |
| source | character varying(50) | NO | 'web'::character varying |
| created_at | timestamp with time zone | NO | now() |

Primary key: id
Unique constraints: none
Foreign keys:
- school_id -> schools(id) (ON DELETE CASCADE)
- user_id -> users(id) (ON DELETE CASCADE)
Indexes:
- ix_user_privacy_consents_consent_type: consent_type
- ix_user_privacy_consents_created_at: created_at
- ix_user_privacy_consents_school_id: school_id
- ix_user_privacy_consents_user_id: user_id

### user_security_settings

| Column | Type | Nullable | Default |
|---|---|---|---|
| user_id | integer | NO |  |
| mfa_enabled | boolean | NO | false |
| trusted_device_days | integer | NO | 14 |
| updated_at | timestamp with time zone | NO | now() |

Primary key: user_id
Unique constraints: none
Foreign keys:
- user_id -> users(id) (ON DELETE CASCADE)
Indexes: none

### user_sessions

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | character varying(36) | NO |  |
| user_id | integer | NO |  |
| token_jti | character varying(64) | NO |  |
| ip_address | character varying(64) | YES |  |
| user_agent | character varying(500) | YES |  |
| created_at | timestamp with time zone | NO | now() |
| last_seen_at | timestamp with time zone | NO | now() |
| revoked_at | timestamp with time zone | YES |  |
| expires_at | timestamp with time zone | NO |  |

Primary key: id
Unique constraints: none
Foreign keys:
- user_id -> users(id) (ON DELETE CASCADE)
Indexes:
- ix_user_sessions_created_at: created_at
- ix_user_sessions_expires_at: expires_at
- UNIQUE ix_user_sessions_token_jti: token_jti
- ix_user_sessions_user_id: user_id


