"""initial_baseline

Revision ID: e79235331d71
Revises:
Create Date: 2026-04-18 16:46:41.989921

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'e79235331d71'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # Create native PostgreSQL ENUM types
    result = bind.execute(sa.text("SELECT typname FROM pg_type WHERE typtype = 'e'"))
    existing_enums = {row[0] for row in result}

    if 'attendancestatus' not in existing_enums:
        postgresql.ENUM(
            'present', 'late', 'absent', 'excused',
            name='attendancestatus',
        ).create(bind)

    if 'eventstatus' not in existing_enums:
        postgresql.ENUM(
            'upcoming', 'ongoing', 'completed', 'cancelled',
            name='eventstatus',
        ).create(bind)

    # ------------------------------------------------------------------ roles
    if 'roles' not in existing_tables:
        op.create_table(
            'roles',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(50), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name'),
        )
        op.create_index('ix_roles_name', 'roles', ['name'], unique=True)

    # ----------------------------------------------------------------- schools
    if 'schools' not in existing_tables:
        op.create_table(
            'schools',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('school_name', sa.String(255), nullable=False),
            sa.Column('school_code', sa.String(50), nullable=True),
            sa.Column('address', sa.String(500), nullable=False),
            sa.Column('logo_url', sa.String(1000), nullable=True),
            sa.Column('primary_color', sa.String(7), nullable=False, server_default='#162F65'),
            sa.Column('secondary_color', sa.String(7), nullable=True),
            sa.Column('subscription_status', sa.String(30), nullable=False, server_default='trial'),
            sa.Column('active_status', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('subscription_plan', sa.String(100), nullable=False, server_default='free'),
            sa.Column('subscription_start', sa.Date(), nullable=False),
            sa.Column('subscription_end', sa.Date(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('school_code'),
        )
        op.create_index('ix_schools_id', 'schools', ['id'], unique=False)
        op.create_index('ix_schools_school_name', 'schools', ['school_name'], unique=False)
        op.create_index('ix_schools_school_code', 'schools', ['school_code'], unique=True)

    # ------------------------------------------------------------------ users
    if 'users' not in existing_tables:
        op.create_table(
            'users',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('email', sa.String(255), nullable=False),
            sa.Column('school_id', sa.Integer(), nullable=True),
            sa.Column('password_hash', sa.String(255), nullable=False),
            sa.Column('first_name', sa.String(100), nullable=True),
            sa.Column('middle_name', sa.String(100), nullable=True),
            sa.Column('last_name', sa.String(100), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('must_change_password', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('should_prompt_password_change', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('email'),
        )
        op.create_index('ix_users_id', 'users', ['id'], unique=False)
        op.create_index('ix_users_email', 'users', ['email'], unique=True)
        op.create_index('ix_users_school_id', 'users', ['school_id'], unique=False)
        op.create_index('ix_users_is_active', 'users', ['is_active'], unique=False)
        op.create_index('ix_users_must_change_password', 'users', ['must_change_password'], unique=False)

    # -------------------------------------------------------------- user_roles
    if 'user_roles' not in existing_tables:
        op.create_table(
            'user_roles',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('role_id', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_user_roles_user_id', 'user_roles', ['user_id'], unique=False)
        op.create_index('ix_user_roles_role_id', 'user_roles', ['role_id'], unique=False)

    # --------------------------------------------------------- school_settings
    if 'school_settings' not in existing_tables:
        op.create_table(
            'school_settings',
            sa.Column('school_id', sa.Integer(), nullable=False),
            sa.Column('primary_color', sa.String(7), nullable=False, server_default='#162F65'),
            sa.Column('secondary_color', sa.String(7), nullable=False, server_default='#2C5F9E'),
            sa.Column('accent_color', sa.String(7), nullable=False, server_default='#4A90E2'),
            sa.Column('event_default_early_check_in_minutes', sa.Integer(), nullable=False),
            sa.Column('event_default_late_threshold_minutes', sa.Integer(), nullable=False),
            sa.Column('event_default_sign_out_grace_minutes', sa.Integer(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('updated_by_user_id', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['updated_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('school_id'),
        )

    # ------------------------------------------------------- school_audit_logs
    if 'school_audit_logs' not in existing_tables:
        op.create_table(
            'school_audit_logs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('school_id', sa.Integer(), nullable=False),
            sa.Column('actor_user_id', sa.Integer(), nullable=True),
            sa.Column('action', sa.String(100), nullable=False),
            sa.Column('status', sa.String(30), nullable=False, server_default='success'),
            sa.Column('details', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_school_audit_logs_id', 'school_audit_logs', ['id'], unique=False)
        op.create_index('ix_school_audit_logs_school_id', 'school_audit_logs', ['school_id'], unique=False)
        op.create_index('ix_school_audit_logs_actor_user_id', 'school_audit_logs', ['actor_user_id'], unique=False)
        op.create_index('ix_school_audit_logs_created_at', 'school_audit_logs', ['created_at'], unique=False)

    # ------------------------------------------------------------- departments
    if 'departments' not in existing_tables:
        op.create_table(
            'departments',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('school_id', sa.Integer(), nullable=True),
            sa.Column('name', sa.String(), nullable=False),
            sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('school_id', 'name', name='uq_departments_school_name'),
        )
        op.create_index('ix_departments_id', 'departments', ['id'], unique=False)
        op.create_index('ix_departments_school_id', 'departments', ['school_id'], unique=False)

    # --------------------------------------------------------------- programs
    if 'programs' not in existing_tables:
        op.create_table(
            'programs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('school_id', sa.Integer(), nullable=True),
            sa.Column('name', sa.String(), nullable=False),
            sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('school_id', 'name', name='uq_programs_school_name'),
        )
        op.create_index('ix_programs_id', 'programs', ['id'], unique=False)
        op.create_index('ix_programs_school_id', 'programs', ['school_id'], unique=False)

    # --------------------------------------- program_department_association
    if 'program_department_association' not in existing_tables:
        op.create_table(
            'program_department_association',
            sa.Column('program_id', sa.Integer(), nullable=False),
            sa.Column('department_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('program_id', 'department_id'),
        )

    # ------------------------------------------------------------------ events
    # NOTE: created with event_type (String) column — no event_type_id yet,
    # no created_by_user_id / create_idempotency_key (added by later migrations).
    if 'events' not in existing_tables:
        op.create_table(
            'events',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('school_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('location', sa.String(200), nullable=True),
            sa.Column('geo_latitude', sa.Float(), nullable=True),
            sa.Column('geo_longitude', sa.Float(), nullable=True),
            sa.Column('geo_radius_m', sa.Float(), nullable=True),
            sa.Column('geo_required', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('geo_max_accuracy_m', sa.Float(), nullable=True),
            sa.Column('early_check_in_minutes', sa.Integer(), nullable=False),
            sa.Column('late_threshold_minutes', sa.Integer(), nullable=False),
            sa.Column('sign_out_grace_minutes', sa.Integer(), nullable=False),
            sa.Column('sign_out_open_delay_minutes', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('sign_out_override_until', sa.DateTime(), nullable=True),
            sa.Column('present_until_override_at', sa.DateTime(), nullable=True),
            sa.Column('late_until_override_at', sa.DateTime(), nullable=True),
            sa.Column('start_datetime', sa.DateTime(), nullable=False),
            sa.Column('end_datetime', sa.DateTime(), nullable=False),
            sa.Column(
                'status',
                postgresql.ENUM(
                    'upcoming', 'ongoing', 'completed', 'cancelled',
                    name='eventstatus', create_type=False,
                ),
                nullable=False,
            ),
            sa.Column('event_type', sa.String(100), nullable=True),
            sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_events_id', 'events', ['id'], unique=False)
        op.create_index('ix_events_school_id', 'events', ['school_id'], unique=False)

    # --------------------------------------- event_department_association
    if 'event_department_association' not in existing_tables:
        op.create_table(
            'event_department_association',
            sa.Column('event_id', sa.Integer(), nullable=False),
            sa.Column('department_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('event_id', 'department_id'),
        )

    # ----------------------------------------- event_program_association
    if 'event_program_association' not in existing_tables:
        op.create_table(
            'event_program_association',
            sa.Column('event_id', sa.Integer(), nullable=False),
            sa.Column('program_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('event_id', 'program_id'),
        )

    # --------------------------------------------------------- student_profiles
    if 'student_profiles' not in existing_tables:
        op.create_table(
            'student_profiles',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('school_id', sa.Integer(), nullable=False),
            sa.Column('student_id', sa.String(50), nullable=True),
            sa.Column('department_id', sa.Integer(), nullable=True),
            sa.Column('program_id', sa.Integer(), nullable=True),
            sa.Column('year_level', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('face_encoding', sa.LargeBinary(), nullable=True),
            sa.Column('embedding_provider', sa.String(32), nullable=True),
            sa.Column('embedding_dtype', sa.String(16), nullable=True),
            sa.Column('embedding_dimension', sa.Integer(), nullable=True),
            sa.Column('embedding_normalized', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('is_face_registered', sa.Boolean(), nullable=True),
            sa.Column('face_image_url', sa.String(500), nullable=True),
            sa.Column('registration_complete', sa.Boolean(), nullable=True),
            sa.Column('section', sa.String(50), nullable=True),
            sa.Column('rfid_tag', sa.String(100), nullable=True),
            sa.Column('last_face_update', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='RESTRICT'),
            sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ondelete='RESTRICT'),
            sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id'),
            sa.UniqueConstraint('rfid_tag'),
            sa.UniqueConstraint('school_id', 'student_id', name='uq_student_profiles_school_student_id'),
        )
        op.create_index('ix_student_profiles_id', 'student_profiles', ['id'], unique=False)
        op.create_index('ix_student_profiles_user_id', 'student_profiles', ['user_id'], unique=True)
        op.create_index('ix_student_profiles_school_id', 'student_profiles', ['school_id'], unique=False)
        op.create_index('ix_student_profiles_student_id', 'student_profiles', ['student_id'], unique=False)
        op.create_index('ix_student_profiles_department_id', 'student_profiles', ['department_id'], unique=False)
        op.create_index('ix_student_profiles_program_id', 'student_profiles', ['program_id'], unique=False)
        op.create_index('ix_student_profiles_is_face_registered', 'student_profiles', ['is_face_registered'], unique=False)
        op.create_index('ix_student_profiles_registration_complete', 'student_profiles', ['registration_complete'], unique=False)
        op.create_index('ix_student_profiles_section', 'student_profiles', ['section'], unique=False)

    # --------------------------------------------------------------- attendances
    # NOTE: time_in / time_out are TIMESTAMP WITHOUT TIME ZONE here;
    # migration c4d5e6f7a8b9 converts them to WITH TIME ZONE.
    if 'attendances' not in existing_tables:
        op.create_table(
            'attendances',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('student_id', sa.Integer(), nullable=True),
            sa.Column('event_id', sa.Integer(), nullable=True),
            sa.Column('time_in', sa.DateTime(), nullable=False),
            sa.Column('time_out', sa.DateTime(), nullable=True),
            sa.Column('method', sa.String(50), nullable=True),
            sa.Column(
                'status',
                postgresql.ENUM(
                    'present', 'late', 'absent', 'excused',
                    name='attendancestatus', create_type=False,
                ),
                nullable=False,
                server_default='present',
            ),
            sa.Column('check_in_status', sa.String(16), nullable=True),
            sa.Column('check_out_status', sa.String(16), nullable=True),
            sa.Column('verified_by', sa.Integer(), nullable=True),
            sa.Column('notes', sa.String(500), nullable=True),
            sa.Column('geo_distance_m', sa.Float(), nullable=True),
            sa.Column('geo_effective_distance_m', sa.Float(), nullable=True),
            sa.Column('geo_latitude', sa.Float(), nullable=True),
            sa.Column('geo_longitude', sa.Float(), nullable=True),
            sa.Column('geo_accuracy_m', sa.Float(), nullable=True),
            sa.Column('liveness_label', sa.String(32), nullable=True),
            sa.Column('liveness_score', sa.Float(), nullable=True),
            sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['verified_by'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_attendances_id', 'attendances', ['id'], unique=False)
        op.create_index('ix_attendances_student_id', 'attendances', ['student_id'], unique=False)
        op.create_index('ix_attendances_event_id', 'attendances', ['event_id'], unique=False)

    # --------------------------------------- user_notification_preferences
    if 'user_notification_preferences' not in existing_tables:
        op.create_table(
            'user_notification_preferences',
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('email_enabled', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('sms_enabled', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('sms_number', sa.String(40), nullable=True),
            sa.Column('notify_missed_events', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('notify_low_attendance', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('notify_account_security', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('notify_subscription', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('user_id'),
        )

    # -------------------------------------------------- user_app_preferences
    if 'user_app_preferences' not in existing_tables:
        op.create_table(
            'user_app_preferences',
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('dark_mode_enabled', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('font_size_percent', sa.Integer(), nullable=False, server_default='100'),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('user_id'),
        )

    # --------------------------------------------------------- notification_logs
    if 'notification_logs' not in existing_tables:
        op.create_table(
            'notification_logs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('school_id', sa.Integer(), nullable=True),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('category', sa.String(50), nullable=False),
            sa.Column('channel', sa.String(20), nullable=False, server_default='email'),
            sa.Column('status', sa.String(20), nullable=False, server_default='queued'),
            sa.Column('subject', sa.String(255), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('metadata_json', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_notification_logs_id', 'notification_logs', ['id'], unique=False)
        op.create_index('ix_notification_logs_school_id', 'notification_logs', ['school_id'], unique=False)
        op.create_index('ix_notification_logs_user_id', 'notification_logs', ['user_id'], unique=False)
        op.create_index('ix_notification_logs_category', 'notification_logs', ['category'], unique=False)
        op.create_index('ix_notification_logs_status', 'notification_logs', ['status'], unique=False)
        op.create_index('ix_notification_logs_created_at', 'notification_logs', ['created_at'], unique=False)

    # ------------------------------------------------------ user_security_settings
    if 'user_security_settings' not in existing_tables:
        op.create_table(
            'user_security_settings',
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('mfa_enabled', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('trusted_device_days', sa.Integer(), nullable=False, server_default='14'),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('user_id'),
        )

    # -------------------------------------------------------- user_face_profiles
    if 'user_face_profiles' not in existing_tables:
        op.create_table(
            'user_face_profiles',
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('face_encoding', sa.LargeBinary(), nullable=False),
            sa.Column('provider', sa.String(50), nullable=False, server_default='arcface'),
            sa.Column('reference_image_sha256', sa.String(64), nullable=True),
            sa.Column('last_verified_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('user_id'),
        )

    # ----------------------------------------------------------- mfa_challenges
    if 'mfa_challenges' not in existing_tables:
        op.create_table(
            'mfa_challenges',
            sa.Column('id', sa.String(36), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('code_hash', sa.String(255), nullable=False),
            sa.Column('channel', sa.String(20), nullable=False, server_default='email'),
            sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('consumed_at', sa.DateTime(), nullable=True),
            sa.Column('ip_address', sa.String(64), nullable=True),
            sa.Column('user_agent', sa.String(500), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_mfa_challenges_user_id', 'mfa_challenges', ['user_id'], unique=False)
        op.create_index('ix_mfa_challenges_expires_at', 'mfa_challenges', ['expires_at'], unique=False)
        op.create_index('ix_mfa_challenges_created_at', 'mfa_challenges', ['created_at'], unique=False)

    # ----------------------------------------------------------- user_sessions
    if 'user_sessions' not in existing_tables:
        op.create_table(
            'user_sessions',
            sa.Column('id', sa.String(36), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('token_jti', sa.String(64), nullable=False),
            sa.Column('ip_address', sa.String(64), nullable=True),
            sa.Column('user_agent', sa.String(500), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('last_seen_at', sa.DateTime(), nullable=False),
            sa.Column('revoked_at', sa.DateTime(), nullable=True),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('token_jti'),
        )
        op.create_index('ix_user_sessions_user_id', 'user_sessions', ['user_id'], unique=False)
        op.create_index('ix_user_sessions_token_jti', 'user_sessions', ['token_jti'], unique=True)
        op.create_index('ix_user_sessions_created_at', 'user_sessions', ['created_at'], unique=False)
        op.create_index('ix_user_sessions_expires_at', 'user_sessions', ['expires_at'], unique=False)

    # ----------------------------------------------------------- login_history
    if 'login_history' not in existing_tables:
        op.create_table(
            'login_history',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('school_id', sa.Integer(), nullable=True),
            sa.Column('email_attempted', sa.String(255), nullable=False),
            sa.Column('success', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('auth_method', sa.String(30), nullable=False, server_default='password'),
            sa.Column('failure_reason', sa.String(255), nullable=True),
            sa.Column('ip_address', sa.String(64), nullable=True),
            sa.Column('user_agent', sa.String(500), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_login_history_id', 'login_history', ['id'], unique=False)
        op.create_index('ix_login_history_user_id', 'login_history', ['user_id'], unique=False)
        op.create_index('ix_login_history_school_id', 'login_history', ['school_id'], unique=False)
        op.create_index('ix_login_history_email_attempted', 'login_history', ['email_attempted'], unique=False)
        op.create_index('ix_login_history_success', 'login_history', ['success'], unique=False)
        op.create_index('ix_login_history_created_at', 'login_history', ['created_at'], unique=False)

    # ---------------------------------------- school_subscription_settings
    if 'school_subscription_settings' not in existing_tables:
        op.create_table(
            'school_subscription_settings',
            sa.Column('school_id', sa.Integer(), nullable=False),
            sa.Column('plan_name', sa.String(50), nullable=False, server_default='free'),
            sa.Column('user_limit', sa.Integer(), nullable=False, server_default='500'),
            sa.Column('event_limit_monthly', sa.Integer(), nullable=False, server_default='100'),
            sa.Column('import_limit_monthly', sa.Integer(), nullable=False, server_default='10'),
            sa.Column('renewal_date', sa.Date(), nullable=True),
            sa.Column('auto_renew', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('reminder_days_before', sa.Integer(), nullable=False, server_default='14'),
            sa.Column('updated_by_user_id', sa.Integer(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['updated_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('school_id'),
        )

    # --------------------------------------- school_subscription_reminders
    if 'school_subscription_reminders' not in existing_tables:
        op.create_table(
            'school_subscription_reminders',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('school_id', sa.Integer(), nullable=False),
            sa.Column('reminder_type', sa.String(40), nullable=False, server_default='renewal_warning'),
            sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
            sa.Column('due_at', sa.DateTime(), nullable=False),
            sa.Column('sent_at', sa.DateTime(), nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_school_subscription_reminders_id', 'school_subscription_reminders', ['id'], unique=False)
        op.create_index('ix_school_subscription_reminders_school_id', 'school_subscription_reminders', ['school_id'], unique=False)
        op.create_index('ix_school_subscription_reminders_status', 'school_subscription_reminders', ['status'], unique=False)
        op.create_index('ix_school_subscription_reminders_due_at', 'school_subscription_reminders', ['due_at'], unique=False)
        op.create_index('ix_school_subscription_reminders_created_at', 'school_subscription_reminders', ['created_at'], unique=False)

    # ----------------------------------------- data_governance_settings
    if 'data_governance_settings' not in existing_tables:
        op.create_table(
            'data_governance_settings',
            sa.Column('school_id', sa.Integer(), nullable=False),
            sa.Column('attendance_retention_days', sa.Integer(), nullable=False, server_default='1095'),
            sa.Column('audit_log_retention_days', sa.Integer(), nullable=False, server_default='3650'),
            sa.Column('import_file_retention_days', sa.Integer(), nullable=False, server_default='180'),
            sa.Column('auto_delete_enabled', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('updated_by_user_id', sa.Integer(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['updated_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('school_id'),
        )

    # ------------------------------------------------------ user_privacy_consents
    if 'user_privacy_consents' not in existing_tables:
        op.create_table(
            'user_privacy_consents',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('school_id', sa.Integer(), nullable=False),
            sa.Column('consent_type', sa.String(50), nullable=False),
            sa.Column('consent_granted', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('consent_version', sa.String(20), nullable=False, server_default='v1'),
            sa.Column('source', sa.String(50), nullable=False, server_default='web'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_user_privacy_consents_id', 'user_privacy_consents', ['id'], unique=False)
        op.create_index('ix_user_privacy_consents_user_id', 'user_privacy_consents', ['user_id'], unique=False)
        op.create_index('ix_user_privacy_consents_school_id', 'user_privacy_consents', ['school_id'], unique=False)
        op.create_index('ix_user_privacy_consents_consent_type', 'user_privacy_consents', ['consent_type'], unique=False)
        op.create_index('ix_user_privacy_consents_created_at', 'user_privacy_consents', ['created_at'], unique=False)

    # -------------------------------------------------------------- data_requests
    if 'data_requests' not in existing_tables:
        op.create_table(
            'data_requests',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('school_id', sa.Integer(), nullable=False),
            sa.Column('requested_by_user_id', sa.Integer(), nullable=True),
            sa.Column('target_user_id', sa.Integer(), nullable=True),
            sa.Column('request_type', sa.String(20), nullable=False),
            sa.Column('scope', sa.String(50), nullable=False, server_default='user_data'),
            sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
            sa.Column('reason', sa.Text(), nullable=True),
            sa.Column('details_json', sa.JSON(), nullable=True),
            sa.Column('output_path', sa.String(1024), nullable=True),
            sa.Column('handled_by_user_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('resolved_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['handled_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['requested_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['target_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_data_requests_id', 'data_requests', ['id'], unique=False)
        op.create_index('ix_data_requests_school_id', 'data_requests', ['school_id'], unique=False)
        op.create_index('ix_data_requests_requested_by_user_id', 'data_requests', ['requested_by_user_id'], unique=False)
        op.create_index('ix_data_requests_target_user_id', 'data_requests', ['target_user_id'], unique=False)
        op.create_index('ix_data_requests_request_type', 'data_requests', ['request_type'], unique=False)
        op.create_index('ix_data_requests_status', 'data_requests', ['status'], unique=False)
        op.create_index('ix_data_requests_created_at', 'data_requests', ['created_at'], unique=False)

    # -------------------------------------------------- data_retention_run_logs
    if 'data_retention_run_logs' not in existing_tables:
        op.create_table(
            'data_retention_run_logs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('school_id', sa.Integer(), nullable=False),
            sa.Column('dry_run', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('status', sa.String(20), nullable=False, server_default='completed'),
            sa.Column('summary', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_data_retention_run_logs_id', 'data_retention_run_logs', ['id'], unique=False)
        op.create_index('ix_data_retention_run_logs_school_id', 'data_retention_run_logs', ['school_id'], unique=False)
        op.create_index('ix_data_retention_run_logs_created_at', 'data_retention_run_logs', ['created_at'], unique=False)

    # --------------------------------------------------------- bulk_import_jobs
    if 'bulk_import_jobs' not in existing_tables:
        op.create_table(
            'bulk_import_jobs',
            sa.Column('id', sa.String(36), nullable=False),
            sa.Column('created_by_user_id', sa.Integer(), nullable=True),
            sa.Column('target_school_id', sa.Integer(), nullable=False),
            sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
            sa.Column('original_filename', sa.String(255), nullable=False),
            sa.Column('stored_file_path', sa.String(1024), nullable=False),
            sa.Column('failed_report_path', sa.String(1024), nullable=True),
            sa.Column('total_rows', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('processed_rows', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('success_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('failed_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('eta_seconds', sa.Integer(), nullable=True),
            sa.Column('error_summary', sa.Text(), nullable=True),
            sa.Column('is_rate_limited', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('started_at', sa.DateTime(), nullable=True),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('last_heartbeat', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['target_school_id'], ['schools.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_bulk_import_jobs_created_by_user_id', 'bulk_import_jobs', ['created_by_user_id'], unique=False)
        op.create_index('ix_bulk_import_jobs_target_school_id', 'bulk_import_jobs', ['target_school_id'], unique=False)
        op.create_index('ix_bulk_import_jobs_status', 'bulk_import_jobs', ['status'], unique=False)
        op.create_index('ix_bulk_import_jobs_created_at', 'bulk_import_jobs', ['created_at'], unique=False)

    # ------------------------------------------------------- bulk_import_errors
    if 'bulk_import_errors' not in existing_tables:
        op.create_table(
            'bulk_import_errors',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('job_id', sa.String(36), nullable=False),
            sa.Column('row_number', sa.Integer(), nullable=False),
            sa.Column('error_message', sa.Text(), nullable=False),
            sa.Column('row_data', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['job_id'], ['bulk_import_jobs.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_bulk_import_errors_job_id', 'bulk_import_errors', ['job_id'], unique=False)
        op.create_index('ix_bulk_import_errors_created_at', 'bulk_import_errors', ['created_at'], unique=False)

    # ----------------------------------------------------- email_delivery_logs
    if 'email_delivery_logs' not in existing_tables:
        op.create_table(
            'email_delivery_logs',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('job_id', sa.String(36), nullable=True),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('email', sa.String(255), nullable=False),
            sa.Column('status', sa.String(20), nullable=False),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['job_id'], ['bulk_import_jobs.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_email_delivery_logs_job_id', 'email_delivery_logs', ['job_id'], unique=False)
        op.create_index('ix_email_delivery_logs_user_id', 'email_delivery_logs', ['user_id'], unique=False)
        op.create_index('ix_email_delivery_logs_email', 'email_delivery_logs', ['email'], unique=False)
        op.create_index('ix_email_delivery_logs_status', 'email_delivery_logs', ['status'], unique=False)

    # -------------------------------------------------- password_reset_requests
    if 'password_reset_requests' not in existing_tables:
        op.create_table(
            'password_reset_requests',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('school_id', sa.Integer(), nullable=False),
            sa.Column('requested_email', sa.String(255), nullable=False),
            sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
            sa.Column('requested_at', sa.DateTime(), nullable=False),
            sa.Column('resolved_at', sa.DateTime(), nullable=True),
            sa.Column('reviewed_by_user_id', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['reviewed_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_password_reset_requests_user_id', 'password_reset_requests', ['user_id'], unique=False)
        op.create_index('ix_password_reset_requests_school_id', 'password_reset_requests', ['school_id'], unique=False)
        op.create_index('ix_password_reset_requests_requested_email', 'password_reset_requests', ['requested_email'], unique=False)
        op.create_index('ix_password_reset_requests_status', 'password_reset_requests', ['status'], unique=False)
        op.create_index('ix_password_reset_requests_requested_at', 'password_reset_requests', ['requested_at'], unique=False)

    # --------------------------------------------------------- governance_units
    if 'governance_units' not in existing_tables:
        op.create_table(
            'governance_units',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('unit_code', sa.String(50), nullable=False),
            sa.Column('unit_name', sa.String(255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('unit_type', sa.String(50), nullable=False),
            sa.Column('parent_unit_id', sa.Integer(), nullable=True),
            sa.Column('school_id', sa.Integer(), nullable=False),
            sa.Column('department_id', sa.Integer(), nullable=True),
            sa.Column('program_id', sa.Integer(), nullable=True),
            sa.Column('created_by_user_id', sa.Integer(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('event_default_early_check_in_minutes', sa.Integer(), nullable=True),
            sa.Column('event_default_late_threshold_minutes', sa.Integer(), nullable=True),
            sa.Column('event_default_sign_out_grace_minutes', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['parent_unit_id'], ['governance_units.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('school_id', 'unit_code', name='uq_governance_units_school_unit_code'),
        )
        op.create_index('ix_governance_units_id', 'governance_units', ['id'], unique=False)
        op.create_index('ix_governance_units_unit_code', 'governance_units', ['unit_code'], unique=False)
        op.create_index('ix_governance_units_unit_type', 'governance_units', ['unit_type'], unique=False)
        op.create_index('ix_governance_units_parent_unit_id', 'governance_units', ['parent_unit_id'], unique=False)
        op.create_index('ix_governance_units_school_id', 'governance_units', ['school_id'], unique=False)
        op.create_index('ix_governance_units_department_id', 'governance_units', ['department_id'], unique=False)
        op.create_index('ix_governance_units_program_id', 'governance_units', ['program_id'], unique=False)
        op.create_index('ix_governance_units_created_by_user_id', 'governance_units', ['created_by_user_id'], unique=False)
        op.create_index('ix_governance_units_is_active', 'governance_units', ['is_active'], unique=False)

    # ------------------------------------------------------- governance_members
    if 'governance_members' not in existing_tables:
        op.create_table(
            'governance_members',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('governance_unit_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('position_title', sa.String(100), nullable=True),
            sa.Column('assigned_by_user_id', sa.Integer(), nullable=True),
            sa.Column('assigned_at', sa.DateTime(), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.ForeignKeyConstraint(['assigned_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['governance_unit_id'], ['governance_units.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('governance_unit_id', 'user_id', name='uq_governance_members_unit_user'),
        )
        op.create_index('ix_governance_members_id', 'governance_members', ['id'], unique=False)
        op.create_index('ix_governance_members_governance_unit_id', 'governance_members', ['governance_unit_id'], unique=False)
        op.create_index('ix_governance_members_user_id', 'governance_members', ['user_id'], unique=False)
        op.create_index('ix_governance_members_assigned_by_user_id', 'governance_members', ['assigned_by_user_id'], unique=False)
        op.create_index('ix_governance_members_is_active', 'governance_members', ['is_active'], unique=False)

    # --------------------------------------------------- governance_permissions
    if 'governance_permissions' not in existing_tables:
        op.create_table(
            'governance_permissions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('permission_code', sa.String(100), nullable=False),
            sa.Column('permission_name', sa.String(100), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('permission_code'),
        )
        op.create_index('ix_governance_permissions_id', 'governance_permissions', ['id'], unique=False)
        op.create_index('ix_governance_permissions_permission_code', 'governance_permissions', ['permission_code'], unique=True)

    # ----------------------------------------------- governance_unit_permissions
    if 'governance_unit_permissions' not in existing_tables:
        op.create_table(
            'governance_unit_permissions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('governance_unit_id', sa.Integer(), nullable=False),
            sa.Column('permission_id', sa.Integer(), nullable=False),
            sa.Column('granted_by_user_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['governance_unit_id'], ['governance_units.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['granted_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['permission_id'], ['governance_permissions.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('governance_unit_id', 'permission_id', name='uq_governance_unit_permissions_unit_permission'),
        )
        op.create_index('ix_governance_unit_permissions_id', 'governance_unit_permissions', ['id'], unique=False)
        op.create_index('ix_governance_unit_permissions_governance_unit_id', 'governance_unit_permissions', ['governance_unit_id'], unique=False)
        op.create_index('ix_governance_unit_permissions_permission_id', 'governance_unit_permissions', ['permission_id'], unique=False)
        op.create_index('ix_governance_unit_permissions_granted_by_user_id', 'governance_unit_permissions', ['granted_by_user_id'], unique=False)

    # --------------------------------------------- governance_member_permissions
    if 'governance_member_permissions' not in existing_tables:
        op.create_table(
            'governance_member_permissions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('governance_member_id', sa.Integer(), nullable=False),
            sa.Column('permission_id', sa.Integer(), nullable=False),
            sa.Column('granted_by_user_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['governance_member_id'], ['governance_members.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['granted_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['permission_id'], ['governance_permissions.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('governance_member_id', 'permission_id', name='uq_governance_member_permissions_member_permission'),
        )
        op.create_index('ix_governance_member_permissions_id', 'governance_member_permissions', ['id'], unique=False)
        op.create_index('ix_governance_member_permissions_governance_member_id', 'governance_member_permissions', ['governance_member_id'], unique=False)
        op.create_index('ix_governance_member_permissions_permission_id', 'governance_member_permissions', ['permission_id'], unique=False)
        op.create_index('ix_governance_member_permissions_granted_by_user_id', 'governance_member_permissions', ['granted_by_user_id'], unique=False)

    # ------------------------------------------------- governance_announcements
    if 'governance_announcements' not in existing_tables:
        op.create_table(
            'governance_announcements',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('governance_unit_id', sa.Integer(), nullable=False),
            sa.Column('school_id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(255), nullable=False),
            sa.Column('body', sa.Text(), nullable=False),
            sa.Column('status', sa.String(50), nullable=False),
            sa.Column('created_by_user_id', sa.Integer(), nullable=True),
            sa.Column('updated_by_user_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['governance_unit_id'], ['governance_units.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['updated_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_governance_announcements_id', 'governance_announcements', ['id'], unique=False)
        op.create_index('ix_governance_announcements_governance_unit_id', 'governance_announcements', ['governance_unit_id'], unique=False)
        op.create_index('ix_governance_announcements_school_id', 'governance_announcements', ['school_id'], unique=False)
        op.create_index('ix_governance_announcements_status', 'governance_announcements', ['status'], unique=False)
        op.create_index('ix_governance_announcements_created_by_user_id', 'governance_announcements', ['created_by_user_id'], unique=False)
        op.create_index('ix_governance_announcements_updated_by_user_id', 'governance_announcements', ['updated_by_user_id'], unique=False)

    # ------------------------------------------------ governance_student_notes
    if 'governance_student_notes' not in existing_tables:
        op.create_table(
            'governance_student_notes',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('governance_unit_id', sa.Integer(), nullable=False),
            sa.Column('student_profile_id', sa.Integer(), nullable=False),
            sa.Column('school_id', sa.Integer(), nullable=False),
            sa.Column('tags', sa.JSON(), nullable=False),
            sa.Column('notes', sa.Text(), nullable=False),
            sa.Column('created_by_user_id', sa.Integer(), nullable=True),
            sa.Column('updated_by_user_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['governance_unit_id'], ['governance_units.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['student_profile_id'], ['student_profiles.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['updated_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('governance_unit_id', 'student_profile_id', name='uq_governance_student_notes_unit_student'),
        )
        op.create_index('ix_governance_student_notes_id', 'governance_student_notes', ['id'], unique=False)
        op.create_index('ix_governance_student_notes_governance_unit_id', 'governance_student_notes', ['governance_unit_id'], unique=False)
        op.create_index('ix_governance_student_notes_student_profile_id', 'governance_student_notes', ['student_profile_id'], unique=False)
        op.create_index('ix_governance_student_notes_school_id', 'governance_student_notes', ['school_id'], unique=False)
        op.create_index('ix_governance_student_notes_created_by_user_id', 'governance_student_notes', ['created_by_user_id'], unique=False)
        op.create_index('ix_governance_student_notes_updated_by_user_id', 'governance_student_notes', ['updated_by_user_id'], unique=False)

    # ------------------------------------------------- event_sanction_configs
    if 'event_sanction_configs' not in existing_tables:
        op.create_table(
            'event_sanction_configs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('school_id', sa.Integer(), nullable=False),
            sa.Column('event_id', sa.Integer(), nullable=False),
            sa.Column('sanctions_enabled', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('item_definitions_json', sa.JSON(), nullable=False),
            sa.Column('created_by_user_id', sa.Integer(), nullable=True),
            sa.Column('updated_by_user_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['updated_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('event_id', name='uq_event_sanction_configs_event_id'),
        )
        op.create_index('ix_event_sanction_configs_id', 'event_sanction_configs', ['id'], unique=False)
        op.create_index('ix_event_sanction_configs_school_id', 'event_sanction_configs', ['school_id'], unique=False)
        op.create_index('ix_event_sanction_configs_event_id', 'event_sanction_configs', ['event_id'], unique=False)
        op.create_index('ix_event_sanction_configs_sanctions_enabled', 'event_sanction_configs', ['sanctions_enabled'], unique=False)
        op.create_index('ix_event_sanction_configs_created_by_user_id', 'event_sanction_configs', ['created_by_user_id'], unique=False)
        op.create_index('ix_event_sanction_configs_updated_by_user_id', 'event_sanction_configs', ['updated_by_user_id'], unique=False)
        op.create_index('ix_event_sanction_configs_created_at', 'event_sanction_configs', ['created_at'], unique=False)

    # ------------------------------------------------------ sanction_records
    if 'sanction_records' not in existing_tables:
        op.create_table(
            'sanction_records',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('school_id', sa.Integer(), nullable=False),
            sa.Column('event_id', sa.Integer(), nullable=False),
            sa.Column('sanction_config_id', sa.Integer(), nullable=True),
            sa.Column('student_profile_id', sa.Integer(), nullable=False),
            sa.Column('attendance_id', sa.Integer(), nullable=True),
            sa.Column('delegated_governance_unit_id', sa.Integer(), nullable=True),
            sa.Column('status', sa.String(50), nullable=False),
            sa.Column('assigned_by_user_id', sa.Integer(), nullable=True),
            sa.Column('complied_at', sa.DateTime(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['assigned_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['attendance_id'], ['attendances.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['delegated_governance_unit_id'], ['governance_units.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['sanction_config_id'], ['event_sanction_configs.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['student_profile_id'], ['student_profiles.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('event_id', 'student_profile_id', name='uq_sanction_records_event_student'),
        )
        op.create_index('ix_sanction_records_id', 'sanction_records', ['id'], unique=False)
        op.create_index('ix_sanction_records_school_id', 'sanction_records', ['school_id'], unique=False)
        op.create_index('ix_sanction_records_event_id', 'sanction_records', ['event_id'], unique=False)
        op.create_index('ix_sanction_records_sanction_config_id', 'sanction_records', ['sanction_config_id'], unique=False)
        op.create_index('ix_sanction_records_student_profile_id', 'sanction_records', ['student_profile_id'], unique=False)
        op.create_index('ix_sanction_records_attendance_id', 'sanction_records', ['attendance_id'], unique=False)
        op.create_index('ix_sanction_records_delegated_governance_unit_id', 'sanction_records', ['delegated_governance_unit_id'], unique=False)
        op.create_index('ix_sanction_records_status', 'sanction_records', ['status'], unique=False)
        op.create_index('ix_sanction_records_assigned_by_user_id', 'sanction_records', ['assigned_by_user_id'], unique=False)
        op.create_index('ix_sanction_records_complied_at', 'sanction_records', ['complied_at'], unique=False)
        op.create_index('ix_sanction_records_created_at', 'sanction_records', ['created_at'], unique=False)

    # ------------------------------------------------------- sanction_items
    if 'sanction_items' not in existing_tables:
        op.create_table(
            'sanction_items',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('sanction_record_id', sa.Integer(), nullable=False),
            sa.Column('item_code', sa.String(64), nullable=True),
            sa.Column('item_name', sa.String(255), nullable=False),
            sa.Column('item_description', sa.Text(), nullable=True),
            sa.Column('status', sa.String(50), nullable=False),
            sa.Column('complied_at', sa.DateTime(), nullable=True),
            sa.Column('compliance_notes', sa.Text(), nullable=True),
            sa.Column('metadata_json', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['sanction_record_id'], ['sanction_records.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('sanction_record_id', 'item_code', name='uq_sanction_items_record_item_code'),
        )
        op.create_index('ix_sanction_items_id', 'sanction_items', ['id'], unique=False)
        op.create_index('ix_sanction_items_sanction_record_id', 'sanction_items', ['sanction_record_id'], unique=False)
        op.create_index('ix_sanction_items_item_code', 'sanction_items', ['item_code'], unique=False)
        op.create_index('ix_sanction_items_status', 'sanction_items', ['status'], unique=False)
        op.create_index('ix_sanction_items_complied_at', 'sanction_items', ['complied_at'], unique=False)
        op.create_index('ix_sanction_items_created_at', 'sanction_items', ['created_at'], unique=False)

    # -------------------------------------------------- sanction_delegations
    if 'sanction_delegations' not in existing_tables:
        op.create_table(
            'sanction_delegations',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('school_id', sa.Integer(), nullable=False),
            sa.Column('event_id', sa.Integer(), nullable=False),
            sa.Column('sanction_config_id', sa.Integer(), nullable=True),
            sa.Column('delegated_by_user_id', sa.Integer(), nullable=True),
            sa.Column('delegated_to_governance_unit_id', sa.Integer(), nullable=False),
            sa.Column('scope_type', sa.String(50), nullable=False),
            sa.Column('scope_json', sa.JSON(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('revoked_at', sa.DateTime(), nullable=True),
            sa.Column('revoked_by_user_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['delegated_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['delegated_to_governance_unit_id'], ['governance_units.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['revoked_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['sanction_config_id'], ['event_sanction_configs.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('event_id', 'delegated_to_governance_unit_id', name='uq_sanction_delegations_event_governance_unit'),
        )
        op.create_index('ix_sanction_delegations_id', 'sanction_delegations', ['id'], unique=False)
        op.create_index('ix_sanction_delegations_school_id', 'sanction_delegations', ['school_id'], unique=False)
        op.create_index('ix_sanction_delegations_event_id', 'sanction_delegations', ['event_id'], unique=False)
        op.create_index('ix_sanction_delegations_sanction_config_id', 'sanction_delegations', ['sanction_config_id'], unique=False)
        op.create_index('ix_sanction_delegations_delegated_by_user_id', 'sanction_delegations', ['delegated_by_user_id'], unique=False)
        op.create_index('ix_sanction_delegations_delegated_to_governance_unit_id', 'sanction_delegations', ['delegated_to_governance_unit_id'], unique=False)
        op.create_index('ix_sanction_delegations_scope_type', 'sanction_delegations', ['scope_type'], unique=False)
        op.create_index('ix_sanction_delegations_is_active', 'sanction_delegations', ['is_active'], unique=False)
        op.create_index('ix_sanction_delegations_revoked_by_user_id', 'sanction_delegations', ['revoked_by_user_id'], unique=False)
        op.create_index('ix_sanction_delegations_created_at', 'sanction_delegations', ['created_at'], unique=False)

    # -------------------------------------------- sanction_compliance_history
    if 'sanction_compliance_history' not in existing_tables:
        op.create_table(
            'sanction_compliance_history',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('school_id', sa.Integer(), nullable=False),
            sa.Column('event_id', sa.Integer(), nullable=True),
            sa.Column('sanction_record_id', sa.Integer(), nullable=True),
            sa.Column('sanction_item_id', sa.Integer(), nullable=True),
            sa.Column('student_profile_id', sa.Integer(), nullable=True),
            sa.Column('complied_on', sa.Date(), nullable=False),
            sa.Column('school_year', sa.String(20), nullable=False),
            sa.Column('semester', sa.String(20), nullable=False),
            sa.Column('complied_by_user_id', sa.Integer(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['complied_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['sanction_item_id'], ['sanction_items.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['sanction_record_id'], ['sanction_records.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['student_profile_id'], ['student_profiles.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_sanction_compliance_history_id', 'sanction_compliance_history', ['id'], unique=False)
        op.create_index('ix_sanction_compliance_history_school_id', 'sanction_compliance_history', ['school_id'], unique=False)
        op.create_index('ix_sanction_compliance_history_event_id', 'sanction_compliance_history', ['event_id'], unique=False)
        op.create_index('ix_sanction_compliance_history_sanction_record_id', 'sanction_compliance_history', ['sanction_record_id'], unique=False)
        op.create_index('ix_sanction_compliance_history_sanction_item_id', 'sanction_compliance_history', ['sanction_item_id'], unique=False)
        op.create_index('ix_sanction_compliance_history_student_profile_id', 'sanction_compliance_history', ['student_profile_id'], unique=False)
        op.create_index('ix_sanction_compliance_history_complied_on', 'sanction_compliance_history', ['complied_on'], unique=False)
        op.create_index('ix_sanction_compliance_history_school_year', 'sanction_compliance_history', ['school_year'], unique=False)
        op.create_index('ix_sanction_compliance_history_semester', 'sanction_compliance_history', ['semester'], unique=False)
        op.create_index('ix_sanction_compliance_history_complied_by_user_id', 'sanction_compliance_history', ['complied_by_user_id'], unique=False)
        op.create_index('ix_sanction_compliance_history_created_at', 'sanction_compliance_history', ['created_at'], unique=False)

    # ---------------------------------------------------- clearance_deadlines
    if 'clearance_deadlines' not in existing_tables:
        op.create_table(
            'clearance_deadlines',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('school_id', sa.Integer(), nullable=False),
            sa.Column('event_id', sa.Integer(), nullable=False),
            sa.Column('declared_by_user_id', sa.Integer(), nullable=True),
            sa.Column('target_governance_unit_id', sa.Integer(), nullable=True),
            sa.Column('deadline_at', sa.DateTime(), nullable=False),
            sa.Column('status', sa.String(50), nullable=False),
            sa.Column('warning_email_sent_at', sa.DateTime(), nullable=True),
            sa.Column('warning_popup_sent_at', sa.DateTime(), nullable=True),
            sa.Column('message', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['declared_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['target_governance_unit_id'], ['governance_units.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_clearance_deadlines_id', 'clearance_deadlines', ['id'], unique=False)
        op.create_index('ix_clearance_deadlines_school_id', 'clearance_deadlines', ['school_id'], unique=False)
        op.create_index('ix_clearance_deadlines_event_id', 'clearance_deadlines', ['event_id'], unique=False)
        op.create_index('ix_clearance_deadlines_declared_by_user_id', 'clearance_deadlines', ['declared_by_user_id'], unique=False)
        op.create_index('ix_clearance_deadlines_target_governance_unit_id', 'clearance_deadlines', ['target_governance_unit_id'], unique=False)
        op.create_index('ix_clearance_deadlines_deadline_at', 'clearance_deadlines', ['deadline_at'], unique=False)
        op.create_index('ix_clearance_deadlines_status', 'clearance_deadlines', ['status'], unique=False)
        op.create_index('ix_clearance_deadlines_warning_email_sent_at', 'clearance_deadlines', ['warning_email_sent_at'], unique=False)
        op.create_index('ix_clearance_deadlines_warning_popup_sent_at', 'clearance_deadlines', ['warning_popup_sent_at'], unique=False)
        op.create_index('ix_clearance_deadlines_created_at', 'clearance_deadlines', ['created_at'], unique=False)


def downgrade() -> None:
    pass
