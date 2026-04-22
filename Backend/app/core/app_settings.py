"""Backend non-secret runtime defaults.

This module is the source of truth for backend, worker, and beat behavior that
should not require environment edits between local, staging, and production
deployments.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BackendAppSettings:
    db_pool_size: int = 10
    db_max_overflow: int = 10
    db_pool_timeout_seconds: int = 15
    db_pool_recycle_seconds: int = 1800
    access_token_expire_minutes: int = 30

    face_scan_bypass_all: bool = False
    face_scan_bypass_emails: tuple[str, ...] = ()
    face_threshold_single: float = 0.40
    face_threshold_group: float = 0.40
    face_threshold_mfa: float = 0.35
    face_warmup_on_startup: bool = True
    face_embedding_dim: int = 512
    face_embedding_dtype: str = "float32"
    liveness_threshold: float = 0.85
    allow_liveness_bypass_when_model_missing: bool = False
    anti_spoof_scale: float = 2.7
    anti_spoof_model_path: str = ""
    geo_max_allowed_accuracy_m: float = 30.0
    geo_max_travel_speed_mps: float = 60.0

    event_status_sync_enabled: bool = True
    event_status_sync_interval_seconds: int = 60
    public_attendance_enabled: bool = True
    public_attendance_max_faces_per_frame: int = 10
    public_attendance_scan_cooldown_seconds: int = 8
    public_attendance_event_lookahead_hours: int = 12
    tenant_database_prefix: str = "school"

    import_max_file_size_mb: int = 50
    import_chunk_size: int = 5000
    import_storage_dir: str = "storage/imports"
    import_rate_limit_count: int = 3
    import_rate_limit_window_seconds: int = 300

    celery_task_time_limit_seconds: int = 10800

    email_timeout_seconds: int = 20
    email_verify_connection_on_startup: bool = True
    mailjet_api_base_url: str = "https://api.mailjet.com/v3.1/send"

    school_logo_storage_dir: str = "storage/school_logos"
    school_logo_max_file_size_mb: int = 2
    school_logo_public_prefix: str = "/media/school-logos"

    default_school_name: str = "Default School"
    default_school_code: str = "DS-001"
    default_school_address: str = "Default Address"
    default_school_logo_url: str = ""
    default_school_primary_color: str = "#162F65"
    default_school_secondary_color: str = "#2C5F9E"
    default_subscription_status: str = "trial"
    default_subscription_plan: str = "free"
    default_admin_email: str = "admin@university.edu"
    default_admin_password: str = "AdminPass123!"

    demo_seed_email_domain: str = "demo.aura.dev"
    demo_seed_schools: int = 5
    demo_seed_users: int = 100
    demo_massive_students: int = 5000
    demo_massive_records: int = 1000000


APP_SETTINGS = BackendAppSettings()
