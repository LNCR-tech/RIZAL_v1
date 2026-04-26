-- aura_v4_normalized.sql
-- Purpose: Target normalized schema for Aura (PostgreSQL).
-- Notes:
-- 1) This is a forward-looking design in db_normalized/ playground.
-- 2) Legacy duplicated and denormalized tables are intentionally omitted.
-- 3) Uses generated identities and explicit FK/UK constraints.

BEGIN;

CREATE SCHEMA IF NOT EXISTS aura_norm;
SET search_path TO aura_norm, public;

-- ---------------------------------------------------------------------------
-- Extensions
-- ---------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS citext;

-- ---------------------------------------------------------------------------
-- Lookup / reference tables
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS subscription_plans (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  code TEXT NOT NULL UNIQUE,
  display_name TEXT NOT NULL,
  user_limit INTEGER NOT NULL CHECK (user_limit > 0),
  event_limit_monthly INTEGER NOT NULL CHECK (event_limit_monthly >= 0),
  import_limit_monthly INTEGER NOT NULL CHECK (import_limit_monthly >= 0),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS roles (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  code TEXT NOT NULL UNIQUE,
  display_name TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS attendance_statuses (
  code TEXT PRIMARY KEY,
  display_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS attendance_methods (
  code TEXT PRIMARY KEY,
  display_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS privacy_consent_types (
  code TEXT PRIMARY KEY,
  description TEXT NOT NULL,
  current_version TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notification_channels (
  code TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  supports_address BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS notification_topics (
  code TEXT PRIMARY KEY,
  display_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS delivery_statuses (
  code TEXT PRIMARY KEY,
  display_name TEXT NOT NULL
);

INSERT INTO attendance_statuses (code, display_name) VALUES
  ('present', 'Present'),
  ('late', 'Late'),
  ('absent', 'Absent'),
  ('excused', 'Excused')
ON CONFLICT (code) DO NOTHING;

INSERT INTO attendance_methods (code, display_name) VALUES
  ('face_scan', 'Face Scan'),
  ('manual', 'Manual'),
  ('rfid', 'RFID')
ON CONFLICT (code) DO NOTHING;

INSERT INTO privacy_consent_types (code, description, current_version) VALUES
  ('privacy_policy', 'Privacy policy consent', 'v1'),
  ('biometric_processing', 'Biometric data processing consent', 'v1')
ON CONFLICT (code) DO NOTHING;

INSERT INTO notification_channels (code, display_name, supports_address) VALUES
  ('email', 'Email', FALSE),
  ('sms', 'SMS', TRUE)
ON CONFLICT (code) DO NOTHING;

INSERT INTO notification_topics (code, display_name) VALUES
  ('missed_events', 'Missed events'),
  ('low_attendance', 'Low attendance'),
  ('account_security', 'Account security'),
  ('subscription', 'Subscription')
ON CONFLICT (code) DO NOTHING;

INSERT INTO delivery_statuses (code, display_name) VALUES
  ('queued', 'Queued'),
  ('sent', 'Sent'),
  ('failed', 'Failed')
ON CONFLICT (code) DO NOTHING;

-- ---------------------------------------------------------------------------
-- School domain
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS schools (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  school_code TEXT UNIQUE,
  legal_name TEXT NOT NULL,
  display_name TEXT NOT NULL,
  address TEXT NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS school_branding (
  school_id BIGINT PRIMARY KEY REFERENCES schools(id) ON DELETE CASCADE,
  logo_url TEXT,
  primary_color CHAR(7) NOT NULL,
  secondary_color CHAR(7),
  accent_color CHAR(7),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_by_user_id BIGINT
);

CREATE TABLE IF NOT EXISTS school_event_policies (
  school_id BIGINT PRIMARY KEY REFERENCES schools(id) ON DELETE CASCADE,
  default_early_check_in_minutes INTEGER NOT NULL CHECK (default_early_check_in_minutes >= 0),
  default_late_threshold_minutes INTEGER NOT NULL CHECK (default_late_threshold_minutes >= 0),
  default_sign_out_grace_minutes INTEGER NOT NULL CHECK (default_sign_out_grace_minutes >= 0),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_by_user_id BIGINT
);

CREATE TABLE IF NOT EXISTS school_subscriptions (
  school_id BIGINT PRIMARY KEY REFERENCES schools(id) ON DELETE CASCADE,
  plan_id BIGINT NOT NULL REFERENCES subscription_plans(id) ON DELETE RESTRICT,
  status TEXT NOT NULL CHECK (status IN ('trial', 'active', 'past_due', 'canceled')),
  starts_on DATE NOT NULL,
  ends_on DATE,
  renewal_date DATE,
  auto_renew BOOLEAN NOT NULL DEFAULT FALSE,
  reminder_days_before INTEGER NOT NULL DEFAULT 14 CHECK (reminder_days_before >= 0),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_by_user_id BIGINT
);

CREATE TABLE IF NOT EXISTS school_subscription_reminders (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  school_id BIGINT NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
  reminder_type TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('pending', 'sent', 'failed')),
  due_at TIMESTAMPTZ NOT NULL,
  sent_at TIMESTAMPTZ,
  error_message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_school_subscription_reminders_school_due
  ON school_subscription_reminders (school_id, due_at);

-- ---------------------------------------------------------------------------
-- Identity & user domain
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  school_id BIGINT REFERENCES schools(id) ON DELETE CASCADE,
  email CITEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  prefix TEXT,
  first_name TEXT,
  middle_name TEXT,
  last_name TEXT,
  suffix TEXT,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  must_change_password BOOLEAN NOT NULL DEFAULT TRUE,
  should_prompt_password_change BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE school_branding
  ADD CONSTRAINT fk_school_branding_updated_by_user
  FOREIGN KEY (updated_by_user_id) REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE school_event_policies
  ADD CONSTRAINT fk_school_event_policies_updated_by_user
  FOREIGN KEY (updated_by_user_id) REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE school_subscriptions
  ADD CONSTRAINT fk_school_subscriptions_updated_by_user
  FOREIGN KEY (updated_by_user_id) REFERENCES users(id) ON DELETE SET NULL;

CREATE TABLE IF NOT EXISTS user_roles (
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role_id BIGINT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
  assigned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  assigned_by_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
  PRIMARY KEY (user_id, role_id)
);

-- Legacy-compatible shape (kept so the backend can ignore any newer normalization work here).
CREATE TABLE IF NOT EXISTS user_notification_preferences (
  user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  email_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  sms_enabled BOOLEAN NOT NULL DEFAULT FALSE,
  sms_number TEXT,
  notify_missed_events BOOLEAN NOT NULL DEFAULT TRUE,
  notify_low_attendance BOOLEAN NOT NULL DEFAULT TRUE,
  notify_account_security BOOLEAN NOT NULL DEFAULT TRUE,
  notify_subscription BOOLEAN NOT NULL DEFAULT TRUE,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Optional 4NF decomposition (future use). Safe to ignore without breaking the legacy table above.
CREATE TABLE IF NOT EXISTS user_notification_channel_settings (
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  channel_code TEXT NOT NULL REFERENCES notification_channels(code) ON DELETE RESTRICT,
  enabled BOOLEAN NOT NULL,
  address_value TEXT,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, channel_code)
);

CREATE TABLE IF NOT EXISTS user_notification_topic_settings (
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  topic_code TEXT NOT NULL REFERENCES notification_topics(code) ON DELETE RESTRICT,
  enabled BOOLEAN NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, topic_code)
);

CREATE TABLE IF NOT EXISTS user_app_preferences (
  user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  dark_mode_enabled BOOLEAN NOT NULL DEFAULT FALSE,
  font_size_percent INTEGER NOT NULL DEFAULT 100 CHECK (font_size_percent BETWEEN 80 AND 200),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_security_settings (
  user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE,
  trusted_device_days INTEGER NOT NULL DEFAULT 14 CHECK (trusted_device_days BETWEEN 0 AND 365),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_face_profiles (
  user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  face_encoding BYTEA NOT NULL,
  provider TEXT NOT NULL,
  embedding_dtype TEXT,
  embedding_dimension INTEGER,
  embedding_normalized BOOLEAN NOT NULL DEFAULT TRUE,
  reference_image_sha256 CHAR(64),
  last_verified_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_sessions (
  id UUID PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_jti CHAR(64) NOT NULL UNIQUE,
  ip_address TEXT,
  user_agent TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  revoked_at TIMESTAMPTZ,
  expires_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS mfa_challenges (
  id UUID PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  code_hash TEXT NOT NULL,
  channel TEXT NOT NULL CHECK (channel IN ('email', 'sms')),
  attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0),
  expires_at TIMESTAMPTZ NOT NULL,
  consumed_at TIMESTAMPTZ,
  ip_address TEXT,
  user_agent TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS login_history (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
  school_id BIGINT REFERENCES schools(id) ON DELETE SET NULL,
  email_attempted CITEXT NOT NULL,
  success BOOLEAN NOT NULL DEFAULT FALSE,
  auth_method TEXT NOT NULL DEFAULT 'password',
  failure_reason TEXT,
  ip_address TEXT,
  user_agent TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_privacy_consents (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  school_id BIGINT NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
  consent_type_code TEXT NOT NULL REFERENCES privacy_consent_types(code) ON DELETE RESTRICT,
  consent_granted BOOLEAN NOT NULL,
  consent_version TEXT NOT NULL,
  source TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, consent_type_code, consent_version, created_at)
);

-- ---------------------------------------------------------------------------
-- Academic structure
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS departments (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  school_id BIGINT NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  UNIQUE (school_id, name)
);

CREATE TABLE IF NOT EXISTS programs (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  school_id BIGINT NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  UNIQUE (school_id, name)
);

-- Academic periods are normalized as a dimension table (avoids free-text drift in history tables).
CREATE TABLE IF NOT EXISTS academic_periods (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  school_id BIGINT NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
  school_year TEXT NOT NULL,
  semester TEXT NOT NULL,
  label TEXT NOT NULL,
  starts_on DATE,
  ends_on DATE,
  UNIQUE (school_id, school_year, semester)
);

CREATE TABLE IF NOT EXISTS program_departments (
  program_id BIGINT NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
  department_id BIGINT NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
  PRIMARY KEY (program_id, department_id)
);

CREATE TABLE IF NOT EXISTS student_profiles (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id BIGINT UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  school_id BIGINT NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
  student_number TEXT NOT NULL,
  department_id BIGINT REFERENCES departments(id) ON DELETE RESTRICT,
  program_id BIGINT REFERENCES programs(id) ON DELETE RESTRICT,
  year_level INTEGER NOT NULL CHECK (year_level BETWEEN 1 AND 10),
  section TEXT,
  rfid_tag TEXT UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (school_id, student_number)
);

CREATE TABLE IF NOT EXISTS faculty_profiles (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id BIGINT NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  department_id BIGINT REFERENCES departments(id) ON DELETE SET NULL,
  program_id BIGINT REFERENCES programs(id) ON DELETE SET NULL
);

-- ---------------------------------------------------------------------------
-- Events and attendance
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS event_types (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  school_id BIGINT REFERENCES schools(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  code TEXT,
  description TEXT,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  sort_order INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (school_id, name)
);

CREATE TABLE IF NOT EXISTS events (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  school_id BIGINT NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
  event_type_id BIGINT REFERENCES event_types(id) ON DELETE SET NULL,
  created_by_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
  create_idempotency_key TEXT,
  name TEXT NOT NULL,
  location TEXT,
  geo_latitude DOUBLE PRECISION,
  geo_longitude DOUBLE PRECISION,
  geo_radius_m DOUBLE PRECISION,
  geo_required BOOLEAN NOT NULL DEFAULT FALSE,
  geo_max_accuracy_m DOUBLE PRECISION,
  early_check_in_minutes INTEGER NOT NULL CHECK (early_check_in_minutes >= 0),
  late_threshold_minutes INTEGER NOT NULL CHECK (late_threshold_minutes >= 0),
  sign_out_grace_minutes INTEGER NOT NULL CHECK (sign_out_grace_minutes >= 0),
  sign_out_open_delay_minutes INTEGER NOT NULL DEFAULT 0 CHECK (sign_out_open_delay_minutes >= 0),
  sign_out_override_until TIMESTAMPTZ,
  present_until_override_at TIMESTAMPTZ,
  late_until_override_at TIMESTAMPTZ,
  start_at TIMESTAMPTZ NOT NULL,
  end_at TIMESTAMPTZ NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('upcoming', 'ongoing', 'completed', 'cancelled')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (created_by_user_id, create_idempotency_key),
  CHECK (end_at >= start_at)
);

CREATE TABLE IF NOT EXISTS event_departments (
  event_id BIGINT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  department_id BIGINT NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
  PRIMARY KEY (event_id, department_id)
);

CREATE TABLE IF NOT EXISTS event_programs (
  event_id BIGINT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  program_id BIGINT NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
  PRIMARY KEY (event_id, program_id)
);

CREATE TABLE IF NOT EXISTS attendance_records (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  student_profile_id BIGINT NOT NULL REFERENCES student_profiles(id) ON DELETE CASCADE,
  event_id BIGINT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  time_in TIMESTAMPTZ NOT NULL DEFAULT now(),
  time_out TIMESTAMPTZ,
  method_code TEXT NOT NULL REFERENCES attendance_methods(code) ON DELETE RESTRICT,
  status_code TEXT NOT NULL REFERENCES attendance_statuses(code) ON DELETE RESTRICT,
  check_in_status TEXT,
  check_out_status TEXT,
  verified_by_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
  notes TEXT,
  geo_distance_m DOUBLE PRECISION,
  geo_effective_distance_m DOUBLE PRECISION,
  geo_latitude DOUBLE PRECISION,
  geo_longitude DOUBLE PRECISION,
  geo_accuracy_m DOUBLE PRECISION,
  liveness_label TEXT,
  liveness_score DOUBLE PRECISION,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (student_profile_id, event_id)
);

CREATE INDEX IF NOT EXISTS idx_attendance_records_event_status
  ON attendance_records (event_id, status_code);

-- ---------------------------------------------------------------------------
-- Governance
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS governance_units (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  school_id BIGINT NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
  parent_unit_id BIGINT REFERENCES governance_units(id) ON DELETE SET NULL,
  unit_code TEXT NOT NULL,
  unit_name TEXT NOT NULL,
  description TEXT,
  unit_type TEXT NOT NULL CHECK (unit_type IN ('SSG', 'SG', 'ORG')),
  department_id BIGINT REFERENCES departments(id) ON DELETE SET NULL,
  program_id BIGINT REFERENCES programs(id) ON DELETE SET NULL,
  created_by_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  event_default_early_check_in_minutes INTEGER,
  event_default_late_threshold_minutes INTEGER,
  event_default_sign_out_grace_minutes INTEGER,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (school_id, unit_code)
);

CREATE TABLE IF NOT EXISTS governance_permissions (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  permission_code TEXT NOT NULL UNIQUE,
  permission_name TEXT NOT NULL,
  description TEXT
);

CREATE TABLE IF NOT EXISTS governance_members (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  governance_unit_id BIGINT NOT NULL REFERENCES governance_units(id) ON DELETE CASCADE,
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  position_title TEXT,
  assigned_by_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
  assigned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  UNIQUE (governance_unit_id, user_id)
);

CREATE TABLE IF NOT EXISTS governance_unit_permissions (
  governance_unit_id BIGINT NOT NULL REFERENCES governance_units(id) ON DELETE CASCADE,
  permission_id BIGINT NOT NULL REFERENCES governance_permissions(id) ON DELETE CASCADE,
  granted_by_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
  granted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (governance_unit_id, permission_id)
);

CREATE TABLE IF NOT EXISTS governance_member_permissions (
  governance_member_id BIGINT NOT NULL REFERENCES governance_members(id) ON DELETE CASCADE,
  permission_id BIGINT NOT NULL REFERENCES governance_permissions(id) ON DELETE CASCADE,
  granted_by_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
  granted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (governance_member_id, permission_id)
);

CREATE TABLE IF NOT EXISTS governance_announcements (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  governance_unit_id BIGINT NOT NULL REFERENCES governance_units(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('draft', 'published', 'archived')),
  created_by_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
  updated_by_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS governance_student_notes (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  governance_unit_id BIGINT NOT NULL REFERENCES governance_units(id) ON DELETE CASCADE,
  student_profile_id BIGINT NOT NULL REFERENCES student_profiles(id) ON DELETE CASCADE,
  notes TEXT NOT NULL DEFAULT '',
  created_by_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
  updated_by_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (governance_unit_id, student_profile_id)
);

CREATE TABLE IF NOT EXISTS governance_student_note_tags (
  note_id BIGINT NOT NULL REFERENCES governance_student_notes(id) ON DELETE CASCADE,
  tag TEXT NOT NULL,
  PRIMARY KEY (note_id, tag)
);

-- ---------------------------------------------------------------------------
-- Sanctions
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS event_sanction_configs (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  event_id BIGINT NOT NULL UNIQUE REFERENCES events(id) ON DELETE CASCADE,
  sanctions_enabled BOOLEAN NOT NULL DEFAULT FALSE,
  created_by_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
  updated_by_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sanction_item_templates (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  sanction_config_id BIGINT NOT NULL REFERENCES event_sanction_configs(id) ON DELETE CASCADE,
  item_code TEXT NOT NULL,
  item_name TEXT NOT NULL,
  item_description TEXT,
  sort_order INTEGER NOT NULL DEFAULT 0,
  is_required BOOLEAN NOT NULL DEFAULT TRUE,
  UNIQUE (sanction_config_id, item_code)
);

CREATE TABLE IF NOT EXISTS sanction_records (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  event_id BIGINT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  student_profile_id BIGINT NOT NULL REFERENCES student_profiles(id) ON DELETE CASCADE,
  sanction_config_id BIGINT REFERENCES event_sanction_configs(id) ON DELETE SET NULL,
  attendance_id BIGINT REFERENCES attendance_records(id) ON DELETE SET NULL,
  delegated_governance_unit_id BIGINT REFERENCES governance_units(id) ON DELETE SET NULL,
  status TEXT NOT NULL CHECK (status IN ('pending', 'complied')),
  assigned_by_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
  complied_at TIMESTAMPTZ,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (event_id, student_profile_id)
);

CREATE TABLE IF NOT EXISTS sanction_record_items (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  sanction_record_id BIGINT NOT NULL REFERENCES sanction_records(id) ON DELETE CASCADE,
  template_id BIGINT REFERENCES sanction_item_templates(id) ON DELETE SET NULL,
  item_code TEXT,
  item_name TEXT NOT NULL,
  item_description TEXT,
  status TEXT NOT NULL CHECK (status IN ('pending', 'complied')),
  complied_at TIMESTAMPTZ,
  compliance_notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (sanction_record_id, item_code)
);

CREATE TABLE IF NOT EXISTS sanction_item_attributes (
  sanction_record_item_id BIGINT NOT NULL REFERENCES sanction_record_items(id) ON DELETE CASCADE,
  attribute_key TEXT NOT NULL,
  attribute_value TEXT,
  PRIMARY KEY (sanction_record_item_id, attribute_key)
);

CREATE TABLE IF NOT EXISTS sanction_delegations (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  event_id BIGINT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  sanction_config_id BIGINT REFERENCES event_sanction_configs(id) ON DELETE SET NULL,
  delegated_by_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
  delegated_to_governance_unit_id BIGINT NOT NULL REFERENCES governance_units(id) ON DELETE CASCADE,
  scope_type TEXT NOT NULL CHECK (scope_type IN ('unit', 'department', 'program', 'school')),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  revoked_at TIMESTAMPTZ,
  revoked_by_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (event_id, delegated_to_governance_unit_id)
);

CREATE TABLE IF NOT EXISTS sanction_delegation_departments (
  delegation_id BIGINT NOT NULL REFERENCES sanction_delegations(id) ON DELETE CASCADE,
  department_id BIGINT NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
  PRIMARY KEY (delegation_id, department_id)
);

CREATE TABLE IF NOT EXISTS sanction_delegation_programs (
  delegation_id BIGINT NOT NULL REFERENCES sanction_delegations(id) ON DELETE CASCADE,
  program_id BIGINT NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
  PRIMARY KEY (delegation_id, program_id)
);

CREATE TABLE IF NOT EXISTS sanction_compliance_history (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  sanction_record_id BIGINT REFERENCES sanction_records(id) ON DELETE SET NULL,
  sanction_record_item_id BIGINT REFERENCES sanction_record_items(id) ON DELETE SET NULL,
  complied_by_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
  compliance_term_label TEXT NOT NULL,
  academic_period_id BIGINT REFERENCES academic_periods(id) ON DELETE RESTRICT,
  complied_on DATE NOT NULL,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS clearance_deadlines (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  event_id BIGINT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  declared_by_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
  target_governance_unit_id BIGINT REFERENCES governance_units(id) ON DELETE SET NULL,
  deadline_at TIMESTAMPTZ NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('active', 'closed', 'expired')),
  warning_email_sent_at TIMESTAMPTZ,
  warning_popup_sent_at TIMESTAMPTZ,
  message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Imports, notifications, and audit
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bulk_import_jobs (
  id UUID PRIMARY KEY,
  created_by_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
  target_school_id BIGINT NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
  status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'failed', 'completed')),
  original_filename TEXT NOT NULL,
  stored_file_path TEXT NOT NULL,
  failed_report_path TEXT,
  total_rows INTEGER NOT NULL DEFAULT 0 CHECK (total_rows >= 0),
  processed_rows INTEGER NOT NULL DEFAULT 0 CHECK (processed_rows >= 0),
  success_count INTEGER NOT NULL DEFAULT 0 CHECK (success_count >= 0),
  failed_count INTEGER NOT NULL DEFAULT 0 CHECK (failed_count >= 0),
  eta_seconds INTEGER,
  error_summary TEXT,
  is_rate_limited BOOLEAN NOT NULL DEFAULT FALSE,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  last_heartbeat TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS bulk_import_errors (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  job_id UUID NOT NULL REFERENCES bulk_import_jobs(id) ON DELETE CASCADE,
  row_number INTEGER NOT NULL CHECK (row_number > 0),
  error_message TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS bulk_import_error_cells (
  error_id BIGINT NOT NULL REFERENCES bulk_import_errors(id) ON DELETE CASCADE,
  column_name TEXT NOT NULL,
  raw_value TEXT,
  PRIMARY KEY (error_id, column_name)
);

CREATE TABLE IF NOT EXISTS email_delivery_logs (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  job_id UUID REFERENCES bulk_import_jobs(id) ON DELETE SET NULL,
  user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
  email CITEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('queued', 'sent', 'failed')),
  error_message TEXT,
  retry_count INTEGER NOT NULL DEFAULT 0 CHECK (retry_count >= 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS notification_logs (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  school_id BIGINT REFERENCES schools(id) ON DELETE CASCADE,
  user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
  category TEXT NOT NULL,
  channel TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('queued', 'sent', 'failed')),
  subject TEXT NOT NULL,
  message TEXT NOT NULL,
  error_message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS notification_log_attributes (
  notification_log_id BIGINT NOT NULL REFERENCES notification_logs(id) ON DELETE CASCADE,
  attribute_key TEXT NOT NULL,
  attribute_value TEXT,
  PRIMARY KEY (notification_log_id, attribute_key)
);

CREATE TABLE IF NOT EXISTS school_audit_logs (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  school_id BIGINT NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
  actor_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
  action TEXT NOT NULL,
  status TEXT NOT NULL,
  details TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS password_reset_requests (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  school_id BIGINT NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
  requested_email CITEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('pending', 'approved', 'denied', 'completed')),
  requested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at TIMESTAMPTZ,
  reviewed_by_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS data_governance_settings (
  school_id BIGINT PRIMARY KEY REFERENCES schools(id) ON DELETE CASCADE,
  attendance_retention_days INTEGER NOT NULL CHECK (attendance_retention_days > 0),
  audit_log_retention_days INTEGER NOT NULL CHECK (audit_log_retention_days > 0),
  import_file_retention_days INTEGER NOT NULL CHECK (import_file_retention_days > 0),
  auto_delete_enabled BOOLEAN NOT NULL DEFAULT FALSE,
  updated_by_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS data_requests (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  school_id BIGINT NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
  requested_by_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
  target_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
  request_type TEXT NOT NULL CHECK (request_type IN ('export', 'delete')),
  scope TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('pending', 'approved', 'rejected', 'completed')),
  reason TEXT,
  output_path TEXT,
  handled_by_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS data_request_items (
  data_request_id BIGINT NOT NULL REFERENCES data_requests(id) ON DELETE CASCADE,
  item_key TEXT NOT NULL,
  item_value TEXT,
  PRIMARY KEY (data_request_id, item_key)
);

CREATE TABLE IF NOT EXISTS data_retention_run_logs (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  school_id BIGINT NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
  dry_run BOOLEAN NOT NULL DEFAULT TRUE,
  status TEXT NOT NULL,
  summary TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Operational indexes
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_users_school_id ON users (school_id);
CREATE INDEX IF NOT EXISTS idx_student_profiles_school_program ON student_profiles (school_id, program_id);
CREATE INDEX IF NOT EXISTS idx_events_school_start ON events (school_id, start_at);
CREATE INDEX IF NOT EXISTS idx_sanction_records_event_status ON sanction_records (event_id, status);
CREATE INDEX IF NOT EXISTS idx_bulk_import_jobs_school_status ON bulk_import_jobs (target_school_id, status);
CREATE INDEX IF NOT EXISTS idx_notification_logs_user_created ON notification_logs (user_id, created_at);

COMMIT;
