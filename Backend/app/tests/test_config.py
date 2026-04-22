from pathlib import Path

from app.core import config as config_module
from app.core.app_settings import APP_SETTINGS
from app.core.config import get_settings


def test_get_env_candidate_paths_checks_backend_then_repo_root(tmp_path):
    config_file = tmp_path / "Backend" / "app" / "core" / "config.py"
    config_file.parent.mkdir(parents=True)
    config_file.touch()

    paths = config_module._get_env_candidate_paths(config_file)

    assert paths == [
        tmp_path / "Backend" / ".env",
        tmp_path / ".env",
    ]


def test_normalize_storage_path_resolves_relative_paths_from_repo_root(tmp_path):
    config_file = tmp_path / "Backend" / "app" / "core" / "config.py"
    config_file.parent.mkdir(parents=True)
    config_file.touch()

    resolved = config_module._normalize_storage_path("storage/imports", config_file)

    assert Path(resolved) == (tmp_path / "storage" / "imports").resolve()


def test_normalize_storage_path_preserves_absolute_paths(tmp_path):
    absolute_path = (tmp_path / "storage" / "imports").resolve()

    resolved = config_module._normalize_storage_path(str(absolute_path))

    assert Path(resolved) == absolute_path


def test_get_settings_exposes_mailjet_and_runtime_fields(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@db:5432/app")
    monkeypatch.setenv("DATABASE_ADMIN_URL", "postgresql://admin:pass@db:5432/postgres")
    monkeypatch.setenv("TENANT_DATABASE_PREFIX", "ignored-prefix")
    monkeypatch.setenv("EMAIL_TIMEOUT_SECONDS", "45")
    monkeypatch.setenv("EMAIL_TRANSPORT", "mailjet_api")
    monkeypatch.setenv("EMAIL_SENDER_EMAIL", "mailer@example.com")
    monkeypatch.setenv("EMAIL_SENDER_NAME", "Aura Notifications")
    monkeypatch.setenv("EMAIL_REPLY_TO", "reply@example.com")
    monkeypatch.setenv("MAILJET_API_KEY", "mailjet-key")
    monkeypatch.setenv("MAILJET_API_SECRET", "mailjet-secret")
    monkeypatch.setenv("LOGIN_URL", "https://valid8.example/login")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://valid8.example,https://admin.valid8.example")

    settings = get_settings()

    assert settings.database_url == "postgresql://user:pass@db:5432/app"
    assert settings.database_admin_url == "postgresql://admin:pass@db:5432/postgres"
    assert settings.tenant_database_prefix == APP_SETTINGS.tenant_database_prefix
    assert settings.email_transport == "mailjet_api"
    assert settings.email_timeout_seconds == APP_SETTINGS.email_timeout_seconds
    assert settings.email_sender_email == "mailer@example.com"
    assert settings.email_sender_name == "Aura Notifications"
    assert settings.email_reply_to == "reply@example.com"
    assert settings.mailjet_api_key == "mailjet-key"
    assert settings.mailjet_api_secret == "mailjet-secret"
    assert settings.login_url == "https://valid8.example/login"
    assert settings.cors_allowed_origins == [
        "https://valid8.example",
        "https://admin.valid8.example",
    ]


def test_get_settings_normalizes_relative_storage_paths(monkeypatch):
    monkeypatch.setenv("IMPORT_STORAGE_DIR", "/tmp/ignored-imports")
    monkeypatch.setenv("SCHOOL_LOGO_STORAGE_DIR", "/tmp/ignored-school-logos")

    settings = get_settings()
    repo_root = config_module._get_repo_root()

    assert Path(settings.import_storage_dir) == (
        repo_root / APP_SETTINGS.import_storage_dir
    ).resolve()
    assert Path(settings.school_logo_storage_dir) == (
        repo_root / APP_SETTINGS.school_logo_storage_dir
    ).resolve()


def test_get_settings_defaults_email_transport_to_disabled_when_unset(monkeypatch):
    monkeypatch.delenv("EMAIL_TRANSPORT", raising=False)

    settings = get_settings()

    assert settings.email_transport == "disabled"
    assert settings.mailjet_api_key == ""
    assert settings.mailjet_api_secret == ""
