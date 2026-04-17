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


def _get_backend_root(config_file: Path | None = None) -> Path:
    resolved_config_file = config_file or Path(__file__).resolve()
    return resolved_config_file.parents[2]


def _get_repo_root(config_file: Path | None = None) -> Path:
    resolved_config_file = config_file or Path(__file__).resolve()
    return resolved_config_file.parents[3]


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


def _as_csv_list(value: str | None, default: list[str]) -> list[str]:
    if value is None:
        return default
    parsed = [item.strip() for item in value.split(",") if item.strip()]
    return parsed or default


def _as_scope_list(value: str | None, default: list[str]) -> list[str]:
    if value is None:
        return default
    normalized = value.replace(",", " ").replace("\n", " ")
    parsed = [item.strip() for item in normalized.split(" ") if item.strip()]
    return parsed or default


def _as_email_list(value: str | None, default: list[str]) -> list[str]:
    if value is None:
        return default
    parsed = [item.strip().lower() for item in value.replace(";", ",").split(",") if item.strip()]
    return parsed or default


def _get_first_env_value(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value is not None:
            return value
    return default


@dataclass(frozen=True)
class Settings:
    database_url: str
    database_admin_url: str | None
    db_pool_size: int
    db_max_overflow: int
    db_pool_timeout_seconds: int
    db_pool_recycle_seconds: int
    secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    face_scan_bypass_emails: list[str]
    face_threshold_single: float
    face_threshold_group: float
    face_threshold_mfa: float
    face_warmup_on_startup: bool
    face_embedding_dim: int
    face_embedding_dtype: str
    liveness_threshold: float
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
    celery_task_time_limit_seconds: int

    email_timeout_seconds: int
    email_sender_email: str
    email_from_email: str
    email_from_name: str
    email_reply_to: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_use_tls: bool
    smtp_use_starttls: bool
    email_google_account_type: str
    email_google_allow_custom_from: bool
    google_oauth_client_id: str
    google_oauth_client_secret: str
    google_oauth_refresh_token: str
    google_oauth_auth_url: str
    google_oauth_token_url: str
    google_oauth_scopes: list[str]
    google_gmail_api_base_url: str
    email_transport: str
    email_required_on_startup: bool
    email_verify_connection_on_startup: bool
    login_url: str

    school_logo_storage_dir: str
    school_logo_max_file_size_mb: int
    school_logo_public_prefix: str
    cors_allowed_origins: list[str]


def get_settings() -> Settings:
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    email_transport = (os.getenv("EMAIL_TRANSPORT") or "disabled").strip().lower()

    return Settings(
        database_url=os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/fastapi_db"),
        database_admin_url=(os.getenv("DATABASE_ADMIN_URL") or "").strip() or None,
        db_pool_size=max(1, int(os.getenv("DB_POOL_SIZE", "10"))),
        db_max_overflow=max(0, int(os.getenv("DB_MAX_OVERFLOW", "10"))),
        db_pool_timeout_seconds=max(1, int(os.getenv("DB_POOL_TIMEOUT_SECONDS", "15"))),
        db_pool_recycle_seconds=max(30, int(os.getenv("DB_POOL_RECYCLE_SECONDS", "1800"))),
        secret_key=os.getenv("SECRET_KEY", "change-this-secret-in-production"),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
        face_scan_bypass_emails=_as_email_list(
            os.getenv("FACE_SCAN_BYPASS_EMAILS"),
            [],
        ),
        face_threshold_single=float(os.getenv("FACE_THRESHOLD_SINGLE", "0.40")),
        face_threshold_group=float(os.getenv("FACE_THRESHOLD_GROUP", "0.40")),
        face_threshold_mfa=float(os.getenv("FACE_THRESHOLD_MFA", "0.35")),
        face_warmup_on_startup=_as_bool(os.getenv("FACE_WARMUP_ON_STARTUP"), True),
        face_embedding_dim=max(1, int(os.getenv("FACE_EMBEDDING_DIM", "512"))),
        face_embedding_dtype=(os.getenv("FACE_EMBEDDING_DTYPE", "float32").strip().lower() or "float32"),
        liveness_threshold=float(os.getenv("LIVENESS_THRESHOLD", "0.85")),
        allow_liveness_bypass_when_model_missing=_as_bool(
            os.getenv("ALLOW_LIVENESS_BYPASS_WHEN_MODEL_MISSING"),
            False,
        ),
        anti_spoof_scale=float(os.getenv("ANTI_SPOOF_SCALE", "2.7")),
        anti_spoof_model_path=os.getenv("ANTI_SPOOF_MODEL_PATH", "").strip(),
        geo_max_allowed_accuracy_m=float(os.getenv("GEO_MAX_ALLOWED_ACCURACY_M", "30")),
        geo_max_travel_speed_mps=float(os.getenv("GEO_MAX_TRAVEL_SPEED_MPS", "60")),
        event_status_sync_enabled=_as_bool(os.getenv("EVENT_STATUS_SYNC_ENABLED"), True),
        event_status_sync_interval_seconds=max(
            30,
            int(os.getenv("EVENT_STATUS_SYNC_INTERVAL_SECONDS", "60")),
        ),
        public_attendance_enabled=_as_bool(
            os.getenv("PUBLIC_ATTENDANCE_ENABLED"),
            True,
        ),
        public_attendance_max_faces_per_frame=max(
            1,
            int(os.getenv("PUBLIC_ATTENDANCE_MAX_FACES_PER_FRAME", "10")),
        ),
        public_attendance_scan_cooldown_seconds=max(
            1,
            int(os.getenv("PUBLIC_ATTENDANCE_SCAN_COOLDOWN_SECONDS", "8")),
        ),
        public_attendance_event_lookahead_hours=max(
            1,
            int(os.getenv("PUBLIC_ATTENDANCE_EVENT_LOOKAHEAD_HOURS", "12")),
        ),
        tenant_database_prefix=(os.getenv("TENANT_DATABASE_PREFIX") or "school").strip() or "school",
        import_max_file_size_mb=int(os.getenv("IMPORT_MAX_FILE_SIZE_MB", "50")),
        import_chunk_size=max(1, int(os.getenv("IMPORT_CHUNK_SIZE", "5000"))),
        import_storage_dir=_normalize_storage_path(
            os.getenv("IMPORT_STORAGE_DIR") or "/tmp/valid8_imports",
        ),
        import_rate_limit_count=max(1, int(os.getenv("IMPORT_RATE_LIMIT_COUNT", "3"))),
        import_rate_limit_window_seconds=max(1, int(os.getenv("IMPORT_RATE_LIMIT_WINDOW_SECONDS", "300"))),
        celery_broker_url=os.getenv("CELERY_BROKER_URL", redis_url),
        celery_result_backend=os.getenv("CELERY_RESULT_BACKEND", redis_url),
        celery_task_time_limit_seconds=max(60, int(os.getenv("CELERY_TASK_TIME_LIMIT_SECONDS", "10800"))),
        email_timeout_seconds=max(
            5,
            int(_get_first_env_value("EMAIL_TIMEOUT_SECONDS", "SMTP_TIMEOUT_SECONDS", default="20")),
        ),
        email_sender_email=_get_first_env_value("EMAIL_SENDER_EMAIL", "SMTP_USERNAME").strip(),
        email_from_email=_get_first_env_value("EMAIL_FROM_EMAIL", "SMTP_FROM_EMAIL").strip(),
        email_from_name=_get_first_env_value(
            "EMAIL_FROM_NAME",
            "SMTP_FROM_NAME",
            default="Aura Notifications",
        ).strip(),
        email_reply_to=_get_first_env_value("EMAIL_REPLY_TO", "SMTP_REPLY_TO").strip(),
        smtp_host=_get_first_env_value("SMTP_HOST", default="localhost").strip(),
        smtp_port=max(1, int(_get_first_env_value("SMTP_PORT", default="1025"))),
        smtp_username=_get_first_env_value("SMTP_USERNAME").strip(),
        smtp_password=_get_first_env_value("SMTP_PASSWORD").strip(),
        smtp_use_tls=_as_bool(_get_first_env_value("SMTP_USE_TLS"), False),
        smtp_use_starttls=_as_bool(_get_first_env_value("SMTP_USE_STARTTLS"), False),
        email_google_account_type=_get_first_env_value(
            "EMAIL_GOOGLE_ACCOUNT_TYPE",
            "SMTP_GOOGLE_ACCOUNT_TYPE",
            default="auto",
        ).strip().lower(),
        email_google_allow_custom_from=_as_bool(
            _get_first_env_value("EMAIL_GOOGLE_ALLOW_CUSTOM_FROM", "SMTP_GOOGLE_ALLOW_CUSTOM_FROM"),
            False,
        ),
        google_oauth_client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID", "").strip(),
        google_oauth_client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "").strip(),
        google_oauth_refresh_token=os.getenv("GOOGLE_OAUTH_REFRESH_TOKEN", "").strip(),
        google_oauth_auth_url=(
            os.getenv("GOOGLE_OAUTH_AUTH_URL", "https://accounts.google.com/o/oauth2/v2/auth").strip()
        ),
        google_oauth_token_url=(
            os.getenv("GOOGLE_OAUTH_TOKEN_URL", "https://oauth2.googleapis.com/token").strip()
        ),
        google_oauth_scopes=_as_scope_list(
            os.getenv("GOOGLE_OAUTH_SCOPES"),
            [
                "https://www.googleapis.com/auth/gmail.send",
                "https://www.googleapis.com/auth/gmail.settings.basic",
            ],
        ),
        google_gmail_api_base_url=(
            os.getenv("GOOGLE_GMAIL_API_BASE_URL", "https://gmail.googleapis.com/gmail/v1").strip()
        ),
        email_transport=email_transport,
        email_required_on_startup=_as_bool(
            os.getenv("EMAIL_REQUIRED_ON_STARTUP"),
            email_transport != "disabled",
        ),
        email_verify_connection_on_startup=_as_bool(
            os.getenv("EMAIL_VERIFY_CONNECTION_ON_STARTUP"),
            False,
        ),
        login_url=os.getenv("LOGIN_URL", "http://localhost:5173"),
        school_logo_storage_dir=_normalize_storage_path(
            os.getenv("SCHOOL_LOGO_STORAGE_DIR") or "/tmp/valid8_school_logos",
        ),
        school_logo_max_file_size_mb=max(1, int(os.getenv("SCHOOL_LOGO_MAX_FILE_SIZE_MB", "2"))),
        school_logo_public_prefix=os.getenv("SCHOOL_LOGO_PUBLIC_PREFIX", "/media/school-logos"),
        cors_allowed_origins=_as_csv_list(
            os.getenv("CORS_ALLOWED_ORIGINS"),
            ["http://localhost:5173", "http://127.0.0.1:5173"],
        ),
    )
