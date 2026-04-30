"""Use: Loads backend settings and environment values.
Where to use: Use this anywhere the app needs config like database URLs, limits, or feature settings.
Role: Core setup layer. It keeps runtime configuration in one place.
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional in runtime envs
    load_dotenv = None

from dataclasses import dataclass

from app.core.app_settings import APP_SETTINGS


def _get_backend_root(config_file: Path | None = None) -> Path:
    resolved_config_file = config_file or Path(__file__).resolve()
    return resolved_config_file.parents[2]


def _get_repo_root(config_file: Path | None = None) -> Path:
    resolved_config_file = config_file or Path(__file__).resolve()
    backend_root = _get_backend_root(resolved_config_file)
    if backend_root.name.lower() == "backend":
        return backend_root.parent
    return backend_root


def _get_env_candidate_paths(config_file: Path | None = None) -> list[Path]:
    backend_root = _get_backend_root(config_file)
    repo_root = _get_repo_root(config_file)
    return [
        backend_root / ".env",
        repo_root / ".env",
    ]


def _normalize_storage_path(value: str, config_file: Path | None = None) -> str:
    normalized_value = value.strip()
    path_value = Path(normalized_value).expanduser()
    if path_value.is_absolute():
        return str(path_value.resolve())
    return str((_get_repo_root(config_file) / path_value).resolve())


def _load_env_files() -> None:
    if load_dotenv is None:
        return

    seen_paths: set[Path] = set()
    for env_path in _get_env_candidate_paths():
        resolved_env_path = env_path.resolve()
        if resolved_env_path in seen_paths or not resolved_env_path.exists():
            continue
        load_dotenv(resolved_env_path, override=False)
        seen_paths.add(resolved_env_path)


_load_env_files()


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_int(value: str | None, default: int, field_name: str) -> int:
    if value is None or not value.strip():
        return default
    try:
        return int(value.strip())
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid integer.") from exc


def _as_csv_list(value: str | None, default: list[str]) -> list[str]:
    if value is None:
        return default
    parsed = [item.strip() for item in value.split(",") if item.strip()]
    return parsed or default


@dataclass(frozen=True)
class Settings:
    database_url: str
    db_pool_size: int
    db_max_overflow: int
    db_pool_timeout_seconds: int
    db_pool_recycle_seconds: int
    secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    face_scan_bypass_all: bool
    face_scan_bypass_emails: list[str]
    face_threshold_single: float
    face_threshold_group: float
    face_threshold_mfa: float
    privileged_face_verification_enabled: bool
    face_warmup_on_startup: bool
    face_embedding_dim: int
    face_embedding_dtype: str
    liveness_threshold: float
    public_attendance_liveness_threshold: float
    allow_liveness_bypass_when_model_missing: bool
    anti_spoof_scale: float
    anti_spoof_model_path: str
    geo_max_allowed_accuracy_m: float
    geo_max_travel_speed_mps: float
    event_status_sync_enabled: bool
    event_status_sync_interval_seconds: int
    public_attendance_enabled: bool
    public_attendance_max_faces_per_frame: int
    public_attendance_scan_cooldown_seconds: int
    public_attendance_event_lookahead_hours: int
    tenant_database_prefix: str

    import_max_file_size_mb: int
    import_chunk_size: int
    import_storage_dir: str
    import_rate_limit_count: int
    import_rate_limit_window_seconds: int

    celery_broker_url: str
    celery_result_backend: str
    redis_url: str
    celery_task_time_limit_seconds: int

    rate_limit_enabled: bool
    rate_limit_fail_open: bool
    rate_limit_login_count: int
    rate_limit_login_window_seconds: int
    rate_limit_forgot_password_count: int
    rate_limit_forgot_password_window_seconds: int
    rate_limit_authenticated_mutation_count: int
    rate_limit_authenticated_mutation_window_seconds: int
    rate_limit_face_count: int
    rate_limit_face_window_seconds: int
    rate_limit_public_count: int
    rate_limit_public_window_seconds: int
    max_request_body_size_mb: int
    face_image_max_size_mb: int
    api_docs_enabled: bool
    trusted_hosts: list[str]

    email_timeout_seconds: int
    email_sender_email: str
    email_sender_name: str
    email_reply_to: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_use_tls: bool
    smtp_use_starttls: bool
    mailjet_api_key: str
    mailjet_api_secret: str
    mailjet_api_base_url: str
    email_transport: str
    email_verify_connection_on_startup: bool
    login_url: str

    school_logo_storage_dir: str
    school_logo_max_file_size_mb: int
    school_logo_public_prefix: str
    cors_allowed_origins: list[str]
    default_admin_email: str
    default_admin_password: str

    google_login_enabled: bool
    google_web_client_id: str
    google_android_client_id: str


def get_settings() -> Settings:
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    email_transport = (os.getenv("EMAIL_TRANSPORT") or "disabled").strip().lower()

    return Settings(
        database_url=os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/fastapi_db"),
        db_pool_size=APP_SETTINGS.db_pool_size,
        db_max_overflow=APP_SETTINGS.db_max_overflow,
        db_pool_timeout_seconds=APP_SETTINGS.db_pool_timeout_seconds,
        db_pool_recycle_seconds=APP_SETTINGS.db_pool_recycle_seconds,
        secret_key=os.getenv("SECRET_KEY", "change-this-secret-in-production"),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        access_token_expire_minutes=APP_SETTINGS.access_token_expire_minutes,
        face_scan_bypass_all=APP_SETTINGS.face_scan_bypass_all,
        face_scan_bypass_emails=list(APP_SETTINGS.face_scan_bypass_emails),
        face_threshold_single=APP_SETTINGS.face_threshold_single,
        face_threshold_group=APP_SETTINGS.face_threshold_group,
        face_threshold_mfa=APP_SETTINGS.face_threshold_mfa,
        privileged_face_verification_enabled=_as_bool(
            os.getenv("PRIVILEGED_FACE_VERIFICATION_ENABLED"),
            APP_SETTINGS.privileged_face_verification_enabled,
        ),
        face_warmup_on_startup=APP_SETTINGS.face_warmup_on_startup,
        face_embedding_dim=APP_SETTINGS.face_embedding_dim,
        face_embedding_dtype=APP_SETTINGS.face_embedding_dtype,
        liveness_threshold=APP_SETTINGS.liveness_threshold,
        public_attendance_liveness_threshold=APP_SETTINGS.public_attendance_liveness_threshold,
        allow_liveness_bypass_when_model_missing=APP_SETTINGS.allow_liveness_bypass_when_model_missing,
        anti_spoof_scale=APP_SETTINGS.anti_spoof_scale,
        anti_spoof_model_path=APP_SETTINGS.anti_spoof_model_path,
        geo_max_allowed_accuracy_m=APP_SETTINGS.geo_max_allowed_accuracy_m,
        geo_max_travel_speed_mps=APP_SETTINGS.geo_max_travel_speed_mps,
        event_status_sync_enabled=APP_SETTINGS.event_status_sync_enabled,
        event_status_sync_interval_seconds=APP_SETTINGS.event_status_sync_interval_seconds,
        public_attendance_enabled=APP_SETTINGS.public_attendance_enabled,
        public_attendance_max_faces_per_frame=APP_SETTINGS.public_attendance_max_faces_per_frame,
        public_attendance_scan_cooldown_seconds=APP_SETTINGS.public_attendance_scan_cooldown_seconds,
        public_attendance_event_lookahead_hours=APP_SETTINGS.public_attendance_event_lookahead_hours,
        tenant_database_prefix=APP_SETTINGS.tenant_database_prefix,
        import_max_file_size_mb=APP_SETTINGS.import_max_file_size_mb,
        import_chunk_size=APP_SETTINGS.import_chunk_size,
        import_storage_dir=_normalize_storage_path(
            APP_SETTINGS.import_storage_dir,
        ),
        import_rate_limit_count=APP_SETTINGS.import_rate_limit_count,
        import_rate_limit_window_seconds=APP_SETTINGS.import_rate_limit_window_seconds,
        celery_broker_url=os.getenv("CELERY_BROKER_URL", redis_url),
        celery_result_backend=os.getenv("CELERY_RESULT_BACKEND", redis_url),
        redis_url=redis_url,
        celery_task_time_limit_seconds=APP_SETTINGS.celery_task_time_limit_seconds,
        rate_limit_enabled=_as_bool(
            os.getenv("RATE_LIMIT_ENABLED"),
            APP_SETTINGS.rate_limit_enabled,
        ),
        rate_limit_fail_open=_as_bool(
            os.getenv("RATE_LIMIT_FAIL_OPEN"),
            APP_SETTINGS.rate_limit_fail_open,
        ),
        rate_limit_login_count=_as_int(
            os.getenv("RATE_LIMIT_LOGIN_COUNT"),
            APP_SETTINGS.rate_limit_login_count,
            "RATE_LIMIT_LOGIN_COUNT",
        ),
        rate_limit_login_window_seconds=_as_int(
            os.getenv("RATE_LIMIT_LOGIN_WINDOW_SECONDS"),
            APP_SETTINGS.rate_limit_login_window_seconds,
            "RATE_LIMIT_LOGIN_WINDOW_SECONDS",
        ),
        rate_limit_forgot_password_count=_as_int(
            os.getenv("RATE_LIMIT_FORGOT_PASSWORD_COUNT"),
            APP_SETTINGS.rate_limit_forgot_password_count,
            "RATE_LIMIT_FORGOT_PASSWORD_COUNT",
        ),
        rate_limit_forgot_password_window_seconds=_as_int(
            os.getenv("RATE_LIMIT_FORGOT_PASSWORD_WINDOW_SECONDS"),
            APP_SETTINGS.rate_limit_forgot_password_window_seconds,
            "RATE_LIMIT_FORGOT_PASSWORD_WINDOW_SECONDS",
        ),
        rate_limit_authenticated_mutation_count=_as_int(
            os.getenv("RATE_LIMIT_AUTHENTICATED_MUTATION_COUNT"),
            APP_SETTINGS.rate_limit_authenticated_mutation_count,
            "RATE_LIMIT_AUTHENTICATED_MUTATION_COUNT",
        ),
        rate_limit_authenticated_mutation_window_seconds=_as_int(
            os.getenv("RATE_LIMIT_AUTHENTICATED_MUTATION_WINDOW_SECONDS"),
            APP_SETTINGS.rate_limit_authenticated_mutation_window_seconds,
            "RATE_LIMIT_AUTHENTICATED_MUTATION_WINDOW_SECONDS",
        ),
        rate_limit_face_count=_as_int(
            os.getenv("RATE_LIMIT_FACE_COUNT"),
            APP_SETTINGS.rate_limit_face_count,
            "RATE_LIMIT_FACE_COUNT",
        ),
        rate_limit_face_window_seconds=_as_int(
            os.getenv("RATE_LIMIT_FACE_WINDOW_SECONDS"),
            APP_SETTINGS.rate_limit_face_window_seconds,
            "RATE_LIMIT_FACE_WINDOW_SECONDS",
        ),
        rate_limit_public_count=_as_int(
            os.getenv("RATE_LIMIT_PUBLIC_COUNT"),
            APP_SETTINGS.rate_limit_public_count,
            "RATE_LIMIT_PUBLIC_COUNT",
        ),
        rate_limit_public_window_seconds=_as_int(
            os.getenv("RATE_LIMIT_PUBLIC_WINDOW_SECONDS"),
            APP_SETTINGS.rate_limit_public_window_seconds,
            "RATE_LIMIT_PUBLIC_WINDOW_SECONDS",
        ),
        max_request_body_size_mb=_as_int(
            os.getenv("MAX_REQUEST_BODY_SIZE_MB"),
            APP_SETTINGS.max_request_body_size_mb,
            "MAX_REQUEST_BODY_SIZE_MB",
        ),
        face_image_max_size_mb=_as_int(
            os.getenv("FACE_IMAGE_MAX_SIZE_MB"),
            APP_SETTINGS.face_image_max_size_mb,
            "FACE_IMAGE_MAX_SIZE_MB",
        ),
        api_docs_enabled=_as_bool(
            os.getenv("API_DOCS_ENABLED"),
            APP_SETTINGS.api_docs_enabled,
        ),
        trusted_hosts=_as_csv_list(
            os.getenv("TRUSTED_HOSTS"),
            list(APP_SETTINGS.trusted_hosts),
        ),
        email_timeout_seconds=APP_SETTINGS.email_timeout_seconds,
        email_sender_email=os.getenv("EMAIL_SENDER_EMAIL", "").strip(),
        email_sender_name=os.getenv("EMAIL_SENDER_NAME", "Aura Notifications").strip(),
        email_reply_to=os.getenv("EMAIL_REPLY_TO", "").strip(),
        smtp_host=os.getenv("SMTP_HOST", "").strip(),
        smtp_port=_as_int(os.getenv("SMTP_PORT"), 587, "SMTP_PORT"),
        smtp_username=os.getenv("SMTP_USERNAME", "").strip(),
        smtp_password=os.getenv("SMTP_PASSWORD", "").strip(),
        smtp_use_tls=_as_bool(os.getenv("SMTP_USE_TLS"), False),
        smtp_use_starttls=_as_bool(os.getenv("SMTP_USE_STARTTLS"), False),
        mailjet_api_key=os.getenv("MAILJET_API_KEY", "").strip(),
        mailjet_api_secret=os.getenv("MAILJET_API_SECRET", "").strip(),
        mailjet_api_base_url=APP_SETTINGS.mailjet_api_base_url,
        email_transport=email_transport,
        email_verify_connection_on_startup=APP_SETTINGS.email_verify_connection_on_startup,
        login_url=os.getenv("LOGIN_URL", "http://localhost:5173"),
        school_logo_storage_dir=_normalize_storage_path(
            APP_SETTINGS.school_logo_storage_dir,
        ),
        school_logo_max_file_size_mb=APP_SETTINGS.school_logo_max_file_size_mb,
        school_logo_public_prefix=APP_SETTINGS.school_logo_public_prefix,
        cors_allowed_origins=_as_csv_list(
            os.getenv("CORS_ALLOWED_ORIGINS"),
            ["http://localhost:5173", "http://127.0.0.1:5173"],
        ),
        default_admin_email=os.getenv("DEFAULT_ADMIN_EMAIL", APP_SETTINGS.default_admin_email).strip(),
        default_admin_password=os.getenv("DEFAULT_ADMIN_PASSWORD", APP_SETTINGS.default_admin_password),
        google_login_enabled=_as_bool(os.getenv("GOOGLE_LOGIN_ENABLED"), True),
        google_web_client_id=os.getenv("GOOGLE_WEB_CLIENT_ID", "").strip(),
        google_android_client_id=os.getenv("GOOGLE_ANDROID_CLIENT_ID", "").strip(),
    )
