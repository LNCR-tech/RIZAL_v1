classDiagram
direction BT
class ai_logs {
   integer user_id
   varchar(100) role
   text message
   varchar(100) tool_called
   boolean success
   timestamp timestamp
   integer id
}
class alembic_version {
   varchar(32) version_num
}
class anomaly_logs {
   integer event_id
   integer user_id
   varchar(64) anomaly_type
   varchar(16) severity
   double precision confidence
   json details
   timestamp detected_at
   boolean is_resolved
   integer id
}
class attendance_predictions {
   integer student_id
   integer event_id
   double precision attendance_probability
   double precision confidence
   varchar(16) risk_level
   varchar(64) model_version
   timestamp generated_at
   integer id
}
class attendances {
   integer student_id
   integer event_id
   timestamp time_in
   timestamp time_out
   varchar(50) method
   attendancestatus status
   integer verified_by
   varchar(500) notes
   integer id
}
class bulk_import_errors {
   varchar(36) job_id
   integer row_number
   text error_message
   json row_data
   timestamp created_at
   integer id
}
class bulk_import_jobs {
   integer created_by_user_id
   varchar(20) status
   varchar(255) original_filename
   varchar(1024) stored_file_path
   varchar(1024) failed_report_path
   integer total_rows
   integer processed_rows
   integer success_count
   integer failed_count
   integer eta_seconds
   text error_summary
   boolean is_rate_limited
   timestamp started_at
   timestamp completed_at
   timestamp created_at
   timestamp updated_at
   timestamp last_heartbeat
   integer target_school_id
   varchar(36) id
}
class data_governance_settings {
   integer attendance_retention_days
   integer audit_log_retention_days
   integer import_file_retention_days
   boolean auto_delete_enabled
   integer updated_by_user_id
   timestamp updated_at
   integer school_id
}
class data_requests {
   integer school_id
   integer requested_by_user_id
   integer target_user_id
   varchar(20) request_type
   varchar(50) scope
   varchar(20) status
   text reason
   json details_json
   varchar(1024) output_path
   integer handled_by_user_id
   timestamp created_at
   timestamp resolved_at
   integer id
}
class data_retention_run_logs {
   integer school_id
   boolean dry_run
   varchar(20) status
   text summary
   timestamp created_at
   integer id
}
class departments {
   varchar name
   integer id
}
class email_delivery_logs {
   varchar(36) job_id
   integer user_id
   varchar(255) email
   varchar(20) status
   text error_message
   integer retry_count
   timestamp created_at
   timestamp updated_at
   integer id
}
class event_consumption_logs {
   varchar(36) event_id
   varchar(120) event_type
   varchar(120) consumer_name
   varchar(24) status
   text error_message
   integer retry_count
   timestamp processed_at
   integer id
}
class event_department_association {
   integer event_id
   integer department_id
}
class event_flags {
   integer event_id
   varchar(255) reason
   timestamp flagged_at
   boolean active
   integer id
}
class event_predictions {
   integer event_id
   integer expected_attendance_count
   double precision expected_turnout_pct
   double precision underperform_probability
   varchar(16) risk_level
   varchar(64) model_version
   timestamp generated_at
   integer id
}
class event_program_association {
   integer event_id
   integer program_id
}
class event_ssg_association {
   integer event_id
   integer ssg_profile_id
}
class events {
   varchar(100) name
   varchar(200) location
   timestamp start_datetime
   timestamp end_datetime
   eventstatus status
   integer school_id
   integer id
}
class login_history {
   integer user_id
   integer school_id
   varchar(255) email_attempted
   boolean success
   varchar(30) auth_method
   varchar(255) failure_reason
   varchar(64) ip_address
   varchar(500) user_agent
   timestamp created_at
   integer id
}
class mfa_challenges {
   integer user_id
   varchar(255) code_hash
   varchar(20) channel
   integer attempts
   timestamp expires_at
   timestamp consumed_at
   varchar(64) ip_address
   varchar(500) user_agent
   timestamp created_at
   varchar(36) id
}
class model_metadata {
   varchar(120) model_name
   varchar(64) model_version
   timestamp trained_at
   json metrics
   json feature_schema
   text notes
   integer id
}
class notification_logs {
   integer school_id
   integer user_id
   varchar(50) category
   varchar(20) channel
   varchar(20) status
   varchar(255) subject
   text message
   text error_message
   json metadata_json
   timestamp created_at
   integer id
}
class notifications {
   integer user_id
   varchar(1000) message
   boolean is_read
   timestamp created_at
   integer id
}
class outbox_events {
   varchar(120) event_type
   varchar(120) source_service
   json payload
   varchar(24) status
   timestamp created_at
   timestamp published_at
   integer retry_count
   text last_error
   varchar(36) id
}
class password_reset_requests {
   integer user_id
   integer school_id
   varchar(255) requested_email
   varchar(20) status
   timestamp requested_at
   timestamp resolved_at
   integer reviewed_by_user_id
   integer id
}
class program_department_association {
   integer program_id
   integer department_id
}
class programs {
   varchar name
   integer id
}
class recommendation_cache {
   integer student_id
   json recommendations
   timestamp generated_at
   timestamp expires_at
   integer id
}
class roles {
   varchar(50) name
   integer id
}
class school_audit_logs {
   integer school_id
   integer actor_user_id
   varchar(100) action
   varchar(30) status
   text details
   timestamp created_at
   integer id
}
class school_settings {
   varchar(7) primary_color
   varchar(7) secondary_color
   varchar(7) accent_color
   timestamp updated_at
   integer updated_by_user_id
   integer school_id
}
class school_subscription_reminders {
   integer school_id
   varchar(40) reminder_type
   varchar(20) status
   timestamp due_at
   timestamp sent_at
   text error_message
   timestamp created_at
   integer id
}
class school_subscription_settings {
   varchar(50) plan_name
   integer user_limit
   integer event_limit_monthly
   integer import_limit_monthly
   date renewal_date
   boolean auto_renew
   integer reminder_days_before
   integer updated_by_user_id
   timestamp updated_at
   integer school_id
}
class schools {
   varchar(255) name
   varchar(500) address
   varchar(1000) logo_url
   varchar(100) subscription_plan
   date subscription_start
   date subscription_end
   timestamp created_at
   timestamp updated_at
   varchar(255) school_name
   varchar(50) school_code
   varchar(7) primary_color
   varchar(7) secondary_color
   varchar(30) subscription_status
   boolean active_status
   integer id
}
class security_alerts {
   integer anomaly_log_id
   integer event_id
   varchar(16) severity
   varchar(255) message
   timestamp created_at
   boolean acknowledged
   integer id
}
class ssg_profiles {
   integer user_id
   varchar(100) position
   integer id
}
class student_profiles {
   integer user_id
   varchar(50) student_id
   integer department_id
   integer program_id
   integer year_level
   bytea face_encoding
   boolean is_face_registered
   varchar(500) face_image_url
   boolean registration_complete
   varchar(50) section
   varchar(100) rfid_tag
   timestamp last_face_update
   integer school_id
   integer id
}
class student_risk_scores {
   integer student_id
   integer risk_score
   varchar(16) risk_level
   varchar(255) recommendation
   json factors
   timestamp generated_at
   timestamp updated_at
   integer id
}
class user_notification_preferences {
   boolean email_enabled
   boolean sms_enabled
   varchar(40) sms_number
   boolean notify_missed_events
   boolean notify_low_attendance
   boolean notify_account_security
   boolean notify_subscription
   timestamp updated_at
   integer user_id
}
class user_privacy_consents {
   integer user_id
   integer school_id
   varchar(50) consent_type
   boolean consent_granted
   varchar(20) consent_version
   varchar(50) source
   timestamp created_at
   integer id
}
class user_roles {
   integer user_id
   integer role_id
   integer id
}
class user_security_settings {
   boolean mfa_enabled
   integer trusted_device_days
   timestamp updated_at
   integer user_id
}
class user_sessions {
   integer user_id
   varchar(64) token_jti
   varchar(64) ip_address
   varchar(500) user_agent
   timestamp created_at
   timestamp last_seen_at
   timestamp revoked_at
   timestamp expires_at
   varchar(36) id
}
class users {
   varchar(255) email
   varchar(255) password_hash
   varchar(100) first_name
   varchar(100) middle_name
   varchar(100) last_name
   boolean is_active
   timestamp created_at
   varchar(30) approval_status
   varchar(200) requested_roles
   varchar(100) requested_ssg_position
   integer school_id
   boolean must_change_password
   integer id
}

ai_logs  -->  users : user_id:id
anomaly_logs  -->  events : event_id:id
anomaly_logs  -->  users : user_id:id
attendance_predictions  -->  events : event_id:id
attendance_predictions  -->  student_profiles : student_id:id
attendances  -->  events : event_id:id
attendances  -->  student_profiles : student_id:id
attendances  -->  users : verified_by:id
bulk_import_errors  -->  bulk_import_jobs : job_id:id
bulk_import_jobs  -->  schools : target_school_id:id
bulk_import_jobs  -->  users : created_by_user_id:id
data_governance_settings  -->  schools : school_id:id
data_governance_settings  -->  users : updated_by_user_id:id
data_requests  -->  schools : school_id:id
data_requests  -->  users : requested_by_user_id:id
data_requests  -->  users : handled_by_user_id:id
data_requests  -->  users : target_user_id:id
data_retention_run_logs  -->  schools : school_id:id
email_delivery_logs  -->  bulk_import_jobs : job_id:id
email_delivery_logs  -->  users : user_id:id
event_consumption_logs  -->  events : event_id:id
event_department_association  -->  departments : department_id:id
event_department_association  -->  events : event_id:id
event_flags  -->  events : event_id:id
event_predictions  -->  events : event_id:id
event_program_association  -->  events : event_id:id
event_program_association  -->  programs : program_id:id
event_ssg_association  -->  events : event_id:id
event_ssg_association  -->  ssg_profiles : ssg_profile_id:id
events  -->  schools : school_id:id
login_history  -->  schools : school_id:id
login_history  -->  users : user_id:id
mfa_challenges  -->  users : user_id:id
notification_logs  -->  schools : school_id:id
notification_logs  -->  users : user_id:id
notifications  -->  users : user_id:id
password_reset_requests  -->  schools : school_id:id
password_reset_requests  -->  users : user_id:id
password_reset_requests  -->  users : reviewed_by_user_id:id
program_department_association  -->  departments : department_id:id
program_department_association  -->  programs : program_id:id
recommendation_cache  -->  student_profiles : student_id:id
school_audit_logs  -->  schools : school_id:id
school_audit_logs  -->  users : actor_user_id:id
school_settings  -->  schools : school_id:id
school_settings  -->  users : updated_by_user_id:id
school_subscription_reminders  -->  schools : school_id:id
school_subscription_settings  -->  schools : school_id:id
school_subscription_settings  -->  users : updated_by_user_id:id
security_alerts  -->  anomaly_logs : anomaly_log_id:id
security_alerts  -->  events : event_id:id
ssg_profiles  -->  users : user_id:id
student_profiles  -->  departments : department_id:id
student_profiles  -->  programs : program_id:id
student_profiles  -->  schools : school_id:id
student_profiles  -->  users : user_id:id
student_risk_scores  -->  student_profiles : student_id:id
user_notification_preferences  -->  users : user_id:id
user_privacy_consents  -->  schools : school_id:id
user_privacy_consents  -->  users : user_id:id
user_roles  -->  roles : role_id:id
user_roles  -->  users : user_id:id
user_security_settings  -->  users : user_id:id
user_sessions  -->  users : user_id:id
users  -->  schools : school_id:id
