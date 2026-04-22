-- Aura v3 Database Schema (PostgreSQL)
-- Verified accurate count: 45 tables (plus alembic_version if managed by migrations)


CREATE TABLE governance_permissions (
	id SERIAL NOT NULL, 
	permission_code VARCHAR(29) NOT NULL, 
	permission_name VARCHAR(100) NOT NULL, 
	description TEXT, 
	PRIMARY KEY (id)
);


CREATE TABLE roles (
	id SERIAL NOT NULL, 
	name VARCHAR(50) NOT NULL, 
	PRIMARY KEY (id)
);


CREATE TABLE schools (
	id SERIAL NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	school_name VARCHAR(255) NOT NULL, 
	school_code VARCHAR(50), 
	address VARCHAR(500) NOT NULL, 
	logo_url VARCHAR(1000), 
	primary_color VARCHAR(7) NOT NULL, 
	secondary_color VARCHAR(7), 
	subscription_status VARCHAR(30) NOT NULL, 
	active_status BOOLEAN NOT NULL, 
	subscription_plan VARCHAR(100) NOT NULL, 
	subscription_start DATE NOT NULL, 
	subscription_end DATE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);


CREATE TABLE data_retention_run_logs (
	id SERIAL NOT NULL, 
	school_id INTEGER NOT NULL, 
	dry_run BOOLEAN NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	summary TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(school_id) REFERENCES schools (id) ON DELETE CASCADE
);


CREATE TABLE departments (
	id SERIAL NOT NULL, 
	school_id INTEGER, 
	name VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_departments_school_name UNIQUE (school_id, name), 
	FOREIGN KEY(school_id) REFERENCES schools (id) ON DELETE CASCADE
);


CREATE TABLE events (
	id SERIAL NOT NULL, 
	school_id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	location VARCHAR(200), 
	geo_latitude FLOAT, 
	geo_longitude FLOAT, 
	geo_radius_m FLOAT, 
	geo_required BOOLEAN NOT NULL, 
	geo_max_accuracy_m FLOAT, 
	early_check_in_minutes INTEGER NOT NULL, 
	late_threshold_minutes INTEGER NOT NULL, 
	sign_out_grace_minutes INTEGER NOT NULL, 
	sign_out_open_delay_minutes INTEGER NOT NULL, 
	sign_out_override_until TIMESTAMP WITHOUT TIME ZONE, 
	present_until_override_at TIMESTAMP WITHOUT TIME ZONE, 
	late_until_override_at TIMESTAMP WITHOUT TIME ZONE, 
	start_datetime TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	end_datetime TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	status eventstatus NOT NULL, 
	event_type VARCHAR(50) DEFAULT 'Regular Event' NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(school_id) REFERENCES schools (id) ON DELETE CASCADE
);


CREATE TABLE programs (
	id SERIAL NOT NULL, 
	school_id INTEGER, 
	name VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_programs_school_name UNIQUE (school_id, name), 
	FOREIGN KEY(school_id) REFERENCES schools (id) ON DELETE CASCADE
);


CREATE TABLE school_subscription_reminders (
	id SERIAL NOT NULL, 
	school_id INTEGER NOT NULL, 
	reminder_type VARCHAR(40) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	due_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	sent_at TIMESTAMP WITHOUT TIME ZONE, 
	error_message TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(school_id) REFERENCES schools (id) ON DELETE CASCADE
);


CREATE TABLE users (
	id SERIAL NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	school_id INTEGER, 
	password_hash VARCHAR(255) NOT NULL, 
	first_name VARCHAR(100), 
	middle_name VARCHAR(100), 
	last_name VARCHAR(100), 
	is_active BOOLEAN, 
	must_change_password BOOLEAN NOT NULL, 
	should_prompt_password_change BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(school_id) REFERENCES schools (id) ON DELETE CASCADE
);


CREATE TABLE bulk_import_jobs (
	id VARCHAR(36) NOT NULL, 
	created_by_user_id INTEGER, 
	target_school_id INTEGER NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	original_filename VARCHAR(255) NOT NULL, 
	stored_file_path VARCHAR(1024) NOT NULL, 
	failed_report_path VARCHAR(1024), 
	total_rows INTEGER NOT NULL, 
	processed_rows INTEGER NOT NULL, 
	success_count INTEGER NOT NULL, 
	failed_count INTEGER NOT NULL, 
	eta_seconds INTEGER, 
	error_summary TEXT, 
	is_rate_limited BOOLEAN NOT NULL, 
	started_at TIMESTAMP WITHOUT TIME ZONE, 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	last_heartbeat TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(created_by_user_id) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(target_school_id) REFERENCES schools (id) ON DELETE CASCADE
);


CREATE TABLE data_governance_settings (
	school_id INTEGER NOT NULL, 
	attendance_retention_days INTEGER NOT NULL, 
	audit_log_retention_days INTEGER NOT NULL, 
	import_file_retention_days INTEGER NOT NULL, 
	auto_delete_enabled BOOLEAN NOT NULL, 
	updated_by_user_id INTEGER, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (school_id), 
	FOREIGN KEY(school_id) REFERENCES schools (id) ON DELETE CASCADE, 
	FOREIGN KEY(updated_by_user_id) REFERENCES users (id) ON DELETE SET NULL
);


CREATE TABLE data_requests (
	id SERIAL NOT NULL, 
	school_id INTEGER NOT NULL, 
	requested_by_user_id INTEGER, 
	target_user_id INTEGER, 
	request_type VARCHAR(20) NOT NULL, 
	scope VARCHAR(50) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	reason TEXT, 
	details_json JSON, 
	output_path VARCHAR(1024), 
	handled_by_user_id INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	resolved_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(school_id) REFERENCES schools (id) ON DELETE CASCADE, 
	FOREIGN KEY(requested_by_user_id) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(target_user_id) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(handled_by_user_id) REFERENCES users (id) ON DELETE SET NULL
);


CREATE TABLE event_department_association (
	event_id INTEGER NOT NULL, 
	department_id INTEGER NOT NULL, 
	PRIMARY KEY (event_id, department_id), 
	FOREIGN KEY(event_id) REFERENCES events (id) ON DELETE CASCADE, 
	FOREIGN KEY(department_id) REFERENCES departments (id) ON DELETE CASCADE
);


CREATE TABLE event_program_association (
	event_id INTEGER NOT NULL, 
	program_id INTEGER NOT NULL, 
	PRIMARY KEY (event_id, program_id), 
	FOREIGN KEY(event_id) REFERENCES events (id) ON DELETE CASCADE, 
	FOREIGN KEY(program_id) REFERENCES programs (id) ON DELETE CASCADE
);


CREATE TABLE event_sanction_configs (
	id SERIAL NOT NULL, 
	school_id INTEGER NOT NULL, 
	event_id INTEGER NOT NULL, 
	sanctions_enabled BOOLEAN NOT NULL, 
	item_definitions_json JSON NOT NULL, 
	created_by_user_id INTEGER, 
	updated_by_user_id INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_event_sanction_configs_event_id UNIQUE (event_id), 
	FOREIGN KEY(school_id) REFERENCES schools (id) ON DELETE CASCADE, 
	FOREIGN KEY(event_id) REFERENCES events (id) ON DELETE CASCADE, 
	FOREIGN KEY(created_by_user_id) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(updated_by_user_id) REFERENCES users (id) ON DELETE SET NULL
);


CREATE TABLE governance_units (
	id SERIAL NOT NULL, 
	unit_code VARCHAR(50) NOT NULL, 
	unit_name VARCHAR(255) NOT NULL, 
	description TEXT, 
	unit_type VARCHAR(3) NOT NULL, 
	parent_unit_id INTEGER, 
	school_id INTEGER NOT NULL, 
	department_id INTEGER, 
	program_id INTEGER, 
	created_by_user_id INTEGER, 
	is_active BOOLEAN NOT NULL, 
	event_default_early_check_in_minutes INTEGER, 
	event_default_late_threshold_minutes INTEGER, 
	event_default_sign_out_grace_minutes INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_governance_units_school_unit_code UNIQUE (school_id, unit_code), 
	FOREIGN KEY(parent_unit_id) REFERENCES governance_units (id) ON DELETE SET NULL, 
	FOREIGN KEY(school_id) REFERENCES schools (id) ON DELETE CASCADE, 
	FOREIGN KEY(department_id) REFERENCES departments (id) ON DELETE SET NULL, 
	FOREIGN KEY(program_id) REFERENCES programs (id) ON DELETE SET NULL, 
	FOREIGN KEY(created_by_user_id) REFERENCES users (id) ON DELETE SET NULL
);


CREATE TABLE login_history (
	id SERIAL NOT NULL, 
	user_id INTEGER, 
	school_id INTEGER, 
	email_attempted VARCHAR(255) NOT NULL, 
	success BOOLEAN NOT NULL, 
	auth_method VARCHAR(30) NOT NULL, 
	failure_reason VARCHAR(255), 
	ip_address VARCHAR(64), 
	user_agent VARCHAR(500), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(school_id) REFERENCES schools (id) ON DELETE SET NULL
);


CREATE TABLE mfa_challenges (
	id VARCHAR(36) NOT NULL, 
	user_id INTEGER NOT NULL, 
	code_hash VARCHAR(255) NOT NULL, 
	channel VARCHAR(20) NOT NULL, 
	attempts INTEGER NOT NULL, 
	expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	consumed_at TIMESTAMP WITHOUT TIME ZONE, 
	ip_address VARCHAR(64), 
	user_agent VARCHAR(500), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);


CREATE TABLE notification_logs (
	id SERIAL NOT NULL, 
	school_id INTEGER, 
	user_id INTEGER, 
	category VARCHAR(50) NOT NULL, 
	channel VARCHAR(20) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	subject VARCHAR(255) NOT NULL, 
	message TEXT NOT NULL, 
	error_message TEXT, 
	metadata_json JSON, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(school_id) REFERENCES schools (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE SET NULL
);


CREATE TABLE password_reset_requests (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	school_id INTEGER NOT NULL, 
	requested_email VARCHAR(255) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	requested_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	resolved_at TIMESTAMP WITHOUT TIME ZONE, 
	reviewed_by_user_id INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(school_id) REFERENCES schools (id) ON DELETE CASCADE, 
	FOREIGN KEY(reviewed_by_user_id) REFERENCES users (id) ON DELETE SET NULL
);


CREATE TABLE program_department_association (
	program_id INTEGER NOT NULL, 
	department_id INTEGER NOT NULL, 
	PRIMARY KEY (program_id, department_id), 
	FOREIGN KEY(program_id) REFERENCES programs (id) ON DELETE CASCADE, 
	FOREIGN KEY(department_id) REFERENCES departments (id) ON DELETE CASCADE
);


CREATE TABLE school_audit_logs (
	id SERIAL NOT NULL, 
	school_id INTEGER NOT NULL, 
	actor_user_id INTEGER, 
	action VARCHAR(100) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	details TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(school_id) REFERENCES schools (id) ON DELETE CASCADE, 
	FOREIGN KEY(actor_user_id) REFERENCES users (id) ON DELETE SET NULL
);


CREATE TABLE school_settings (
	school_id INTEGER NOT NULL, 
	primary_color VARCHAR(7) NOT NULL, 
	secondary_color VARCHAR(7) NOT NULL, 
	accent_color VARCHAR(7) NOT NULL, 
	event_default_early_check_in_minutes INTEGER NOT NULL, 
	event_default_late_threshold_minutes INTEGER NOT NULL, 
	event_default_sign_out_grace_minutes INTEGER NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_by_user_id INTEGER, 
	PRIMARY KEY (school_id), 
	FOREIGN KEY(school_id) REFERENCES schools (id) ON DELETE CASCADE, 
	FOREIGN KEY(updated_by_user_id) REFERENCES users (id) ON DELETE SET NULL
);


CREATE TABLE school_subscription_settings (
	school_id INTEGER NOT NULL, 
	plan_name VARCHAR(50) NOT NULL, 
	user_limit INTEGER NOT NULL, 
	event_limit_monthly INTEGER NOT NULL, 
	import_limit_monthly INTEGER NOT NULL, 
	renewal_date DATE, 
	auto_renew BOOLEAN NOT NULL, 
	reminder_days_before INTEGER NOT NULL, 
	updated_by_user_id INTEGER, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (school_id), 
	FOREIGN KEY(school_id) REFERENCES schools (id) ON DELETE CASCADE, 
	FOREIGN KEY(updated_by_user_id) REFERENCES users (id) ON DELETE SET NULL
);


CREATE TABLE student_profiles (
	id SERIAL NOT NULL, 
	user_id INTEGER, 
	school_id INTEGER NOT NULL, 
	student_id VARCHAR(50), 
	department_id INTEGER, 
	program_id INTEGER, 
	year_level INTEGER NOT NULL, 
	face_encoding BYTEA, 
	embedding_provider VARCHAR(32), 
	embedding_dtype VARCHAR(16), 
	embedding_dimension INTEGER, 
	embedding_normalized BOOLEAN NOT NULL, 
	is_face_registered BOOLEAN, 
	face_image_url VARCHAR(500), 
	registration_complete BOOLEAN, 
	section VARCHAR(50), 
	rfid_tag VARCHAR(100), 
	last_face_update TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_student_profiles_school_student_id UNIQUE (school_id, student_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(school_id) REFERENCES schools (id) ON DELETE CASCADE, 
	FOREIGN KEY(department_id) REFERENCES departments (id) ON DELETE RESTRICT, 
	FOREIGN KEY(program_id) REFERENCES programs (id) ON DELETE RESTRICT, 
	UNIQUE (rfid_tag)
);


CREATE TABLE user_app_preferences (
	user_id INTEGER NOT NULL, 
	dark_mode_enabled BOOLEAN NOT NULL, 
	font_size_percent INTEGER NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);


CREATE TABLE user_face_profiles (
	user_id INTEGER NOT NULL, 
	face_encoding BYTEA NOT NULL, 
	provider VARCHAR(50) NOT NULL, 
	reference_image_sha256 VARCHAR(64), 
	last_verified_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);


CREATE TABLE user_notification_preferences (
	user_id INTEGER NOT NULL, 
	email_enabled BOOLEAN NOT NULL, 
	sms_enabled BOOLEAN NOT NULL, 
	sms_number VARCHAR(40), 
	notify_missed_events BOOLEAN NOT NULL, 
	notify_low_attendance BOOLEAN NOT NULL, 
	notify_account_security BOOLEAN NOT NULL, 
	notify_subscription BOOLEAN NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);


CREATE TABLE user_privacy_consents (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	school_id INTEGER NOT NULL, 
	consent_type VARCHAR(50) NOT NULL, 
	consent_granted BOOLEAN NOT NULL, 
	consent_version VARCHAR(20) NOT NULL, 
	source VARCHAR(50) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(school_id) REFERENCES schools (id) ON DELETE CASCADE
);


CREATE TABLE user_roles (
	id SERIAL NOT NULL, 
	user_id INTEGER, 
	role_id INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(role_id) REFERENCES roles (id) ON DELETE CASCADE
);


CREATE TABLE user_security_settings (
	user_id INTEGER NOT NULL, 
	mfa_enabled BOOLEAN NOT NULL, 
	trusted_device_days INTEGER NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);


CREATE TABLE user_sessions (
	id VARCHAR(36) NOT NULL, 
	user_id INTEGER NOT NULL, 
	token_jti VARCHAR(64) NOT NULL, 
	ip_address VARCHAR(64), 
	user_agent VARCHAR(500), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	last_seen_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	revoked_at TIMESTAMP WITHOUT TIME ZONE, 
	expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);


CREATE TABLE attendances (
	id SERIAL NOT NULL, 
	student_id INTEGER, 
	event_id INTEGER, 
	time_in TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	time_out TIMESTAMP WITHOUT TIME ZONE, 
	method VARCHAR(50), 
	status attendancestatus NOT NULL, 
	check_in_status VARCHAR(16), 
	check_out_status VARCHAR(16), 
	verified_by INTEGER, 
	notes VARCHAR(500), 
	geo_distance_m FLOAT, 
	geo_effective_distance_m FLOAT, 
	geo_latitude FLOAT, 
	geo_longitude FLOAT, 
	geo_accuracy_m FLOAT, 
	liveness_label VARCHAR(32), 
	liveness_score FLOAT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(student_id) REFERENCES student_profiles (id) ON DELETE CASCADE, 
	FOREIGN KEY(event_id) REFERENCES events (id) ON DELETE CASCADE, 
	FOREIGN KEY(verified_by) REFERENCES users (id) ON DELETE SET NULL
);


CREATE TABLE bulk_import_errors (
	id SERIAL NOT NULL, 
	job_id VARCHAR(36) NOT NULL, 
	row_number INTEGER NOT NULL, 
	error_message TEXT NOT NULL, 
	row_data JSON, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(job_id) REFERENCES bulk_import_jobs (id) ON DELETE CASCADE
);


CREATE TABLE clearance_deadlines (
	id SERIAL NOT NULL, 
	school_id INTEGER NOT NULL, 
	event_id INTEGER NOT NULL, 
	declared_by_user_id INTEGER, 
	target_governance_unit_id INTEGER, 
	deadline_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	status VARCHAR(7) NOT NULL, 
	warning_email_sent_at TIMESTAMP WITHOUT TIME ZONE, 
	warning_popup_sent_at TIMESTAMP WITHOUT TIME ZONE, 
	message TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(school_id) REFERENCES schools (id) ON DELETE CASCADE, 
	FOREIGN KEY(event_id) REFERENCES events (id) ON DELETE CASCADE, 
	FOREIGN KEY(declared_by_user_id) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(target_governance_unit_id) REFERENCES governance_units (id) ON DELETE SET NULL
);


CREATE TABLE email_delivery_logs (
	id SERIAL NOT NULL, 
	job_id VARCHAR(36), 
	user_id INTEGER, 
	email VARCHAR(255) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	error_message TEXT, 
	retry_count INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(job_id) REFERENCES bulk_import_jobs (id) ON DELETE SET NULL, 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE SET NULL
);


CREATE TABLE governance_announcements (
	id SERIAL NOT NULL, 
	governance_unit_id INTEGER NOT NULL, 
	school_id INTEGER NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	body TEXT NOT NULL, 
	status VARCHAR(9) NOT NULL, 
	created_by_user_id INTEGER, 
	updated_by_user_id INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(governance_unit_id) REFERENCES governance_units (id) ON DELETE CASCADE, 
	FOREIGN KEY(school_id) REFERENCES schools (id) ON DELETE CASCADE, 
	FOREIGN KEY(created_by_user_id) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(updated_by_user_id) REFERENCES users (id) ON DELETE SET NULL
);


CREATE TABLE governance_members (
	id SERIAL NOT NULL, 
	governance_unit_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	position_title VARCHAR(100), 
	assigned_by_user_id INTEGER, 
	assigned_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_governance_members_unit_user UNIQUE (governance_unit_id, user_id), 
	FOREIGN KEY(governance_unit_id) REFERENCES governance_units (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(assigned_by_user_id) REFERENCES users (id) ON DELETE SET NULL
);


CREATE TABLE governance_student_notes (
	id SERIAL NOT NULL, 
	governance_unit_id INTEGER NOT NULL, 
	student_profile_id INTEGER NOT NULL, 
	school_id INTEGER NOT NULL, 
	tags JSON NOT NULL, 
	notes TEXT NOT NULL, 
	created_by_user_id INTEGER, 
	updated_by_user_id INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_governance_student_notes_unit_student UNIQUE (governance_unit_id, student_profile_id), 
	FOREIGN KEY(governance_unit_id) REFERENCES governance_units (id) ON DELETE CASCADE, 
	FOREIGN KEY(student_profile_id) REFERENCES student_profiles (id) ON DELETE CASCADE, 
	FOREIGN KEY(school_id) REFERENCES schools (id) ON DELETE CASCADE, 
	FOREIGN KEY(created_by_user_id) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(updated_by_user_id) REFERENCES users (id) ON DELETE SET NULL
);


CREATE TABLE governance_unit_permissions (
	id SERIAL NOT NULL, 
	governance_unit_id INTEGER NOT NULL, 
	permission_id INTEGER NOT NULL, 
	granted_by_user_id INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_governance_unit_permissions_unit_permission UNIQUE (governance_unit_id, permission_id), 
	FOREIGN KEY(governance_unit_id) REFERENCES governance_units (id) ON DELETE CASCADE, 
	FOREIGN KEY(permission_id) REFERENCES governance_permissions (id) ON DELETE CASCADE, 
	FOREIGN KEY(granted_by_user_id) REFERENCES users (id) ON DELETE SET NULL
);


CREATE TABLE sanction_delegations (
	id SERIAL NOT NULL, 
	school_id INTEGER NOT NULL, 
	event_id INTEGER NOT NULL, 
	sanction_config_id INTEGER, 
	delegated_by_user_id INTEGER, 
	delegated_to_governance_unit_id INTEGER NOT NULL, 
	scope_type VARCHAR(10) NOT NULL, 
	scope_json JSON, 
	is_active BOOLEAN NOT NULL, 
	revoked_at TIMESTAMP WITHOUT TIME ZONE, 
	revoked_by_user_id INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_sanction_delegations_event_governance_unit UNIQUE (event_id, delegated_to_governance_unit_id), 
	FOREIGN KEY(school_id) REFERENCES schools (id) ON DELETE CASCADE, 
	FOREIGN KEY(event_id) REFERENCES events (id) ON DELETE CASCADE, 
	FOREIGN KEY(sanction_config_id) REFERENCES event_sanction_configs (id) ON DELETE SET NULL, 
	FOREIGN KEY(delegated_by_user_id) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(delegated_to_governance_unit_id) REFERENCES governance_units (id) ON DELETE CASCADE, 
	FOREIGN KEY(revoked_by_user_id) REFERENCES users (id) ON DELETE SET NULL
);


CREATE TABLE governance_member_permissions (
	id SERIAL NOT NULL, 
	governance_member_id INTEGER NOT NULL, 
	permission_id INTEGER NOT NULL, 
	granted_by_user_id INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_governance_member_permissions_member_permission UNIQUE (governance_member_id, permission_id), 
	FOREIGN KEY(governance_member_id) REFERENCES governance_members (id) ON DELETE CASCADE, 
	FOREIGN KEY(permission_id) REFERENCES governance_permissions (id) ON DELETE CASCADE, 
	FOREIGN KEY(granted_by_user_id) REFERENCES users (id) ON DELETE SET NULL
);


CREATE TABLE sanction_records (
	id SERIAL NOT NULL, 
	school_id INTEGER NOT NULL, 
	event_id INTEGER NOT NULL, 
	sanction_config_id INTEGER, 
	student_profile_id INTEGER NOT NULL, 
	attendance_id INTEGER, 
	delegated_governance_unit_id INTEGER, 
	status VARCHAR(8) NOT NULL, 
	assigned_by_user_id INTEGER, 
	complied_at TIMESTAMP WITHOUT TIME ZONE, 
	notes TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_sanction_records_event_student UNIQUE (event_id, student_profile_id), 
	FOREIGN KEY(school_id) REFERENCES schools (id) ON DELETE CASCADE, 
	FOREIGN KEY(event_id) REFERENCES events (id) ON DELETE CASCADE, 
	FOREIGN KEY(sanction_config_id) REFERENCES event_sanction_configs (id) ON DELETE SET NULL, 
	FOREIGN KEY(student_profile_id) REFERENCES student_profiles (id) ON DELETE CASCADE, 
	FOREIGN KEY(attendance_id) REFERENCES attendances (id) ON DELETE SET NULL, 
	FOREIGN KEY(delegated_governance_unit_id) REFERENCES governance_units (id) ON DELETE SET NULL, 
	FOREIGN KEY(assigned_by_user_id) REFERENCES users (id) ON DELETE SET NULL
);


CREATE TABLE sanction_items (
	id SERIAL NOT NULL, 
	sanction_record_id INTEGER NOT NULL, 
	item_code VARCHAR(64), 
	item_name VARCHAR(255) NOT NULL, 
	item_description TEXT, 
	status VARCHAR(8) NOT NULL, 
	complied_at TIMESTAMP WITHOUT TIME ZONE, 
	compliance_notes TEXT, 
	metadata_json JSON, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_sanction_items_record_item_code UNIQUE (sanction_record_id, item_code), 
	FOREIGN KEY(sanction_record_id) REFERENCES sanction_records (id) ON DELETE CASCADE
);


CREATE TABLE sanction_compliance_history (
	id SERIAL NOT NULL, 
	school_id INTEGER NOT NULL, 
	event_id INTEGER, 
	sanction_record_id INTEGER, 
	sanction_item_id INTEGER, 
	student_profile_id INTEGER, 
	complied_on DATE NOT NULL, 
	school_year VARCHAR(20) NOT NULL, 
	semester VARCHAR(20) NOT NULL, 
	complied_by_user_id INTEGER, 
	notes TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(school_id) REFERENCES schools (id) ON DELETE CASCADE, 
	FOREIGN KEY(event_id) REFERENCES events (id) ON DELETE SET NULL, 
	FOREIGN KEY(sanction_record_id) REFERENCES sanction_records (id) ON DELETE SET NULL, 
	FOREIGN KEY(sanction_item_id) REFERENCES sanction_items (id) ON DELETE SET NULL, 
	FOREIGN KEY(student_profile_id) REFERENCES student_profiles (id) ON DELETE SET NULL, 
	FOREIGN KEY(complied_by_user_id) REFERENCES users (id) ON DELETE SET NULL
);

