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


def _as_csv_list(value: str | None, default: list[str]) -> list[str]:
    if value is None:
        return default
    parsed = [item.strip() for item in value.split(",") if item.strip()]
    return parsed or default


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
    face_scan_bypass_all: bool
    face_scan_bypass_emails: list[str]
    face_threshold_single: float
    face_threshold_group: float
    face_threshold_mfa: float
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
    celery_task_time_limit_seconds: int

    email_timeout_seconds: int
    email_sender_email: str
    email_sender_name: str
    email_reply_to: str
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


def get_settings() -> Settings:
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    email_transport = (os.getenv("EMAIL_TRANSPORT") or "disabled").strip().lower()

    return Settings(
        database_url=os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/fastapi_db"),
        database_admin_url=(os.getenv("DATABASE_ADMIN_URL") or "").strip() or None,
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
        celery_task_time_limit_seconds=APP_SETTINGS.celery_task_time_limit_seconds,
        email_timeout_seconds=APP_SETTINGS.email_timeout_seconds,
        email_sender_email=os.getenv("EMAIL_SENDER_EMAIL", "").strip(),
        email_sender_name=os.getenv("EMAIL_SENDER_NAME", "Aura Notifications").strip(),
        email_reply_to=os.getenv("EMAIL_REPLY_TO", "").strip(),
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
    )
