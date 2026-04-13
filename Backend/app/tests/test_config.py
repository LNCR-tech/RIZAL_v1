from pathlib import Path

from app.core import config as config_module
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


def test_get_settings_exposes_tenant_database_fields(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@db:5432/app")
    monkeypatch.setenv("DATABASE_ADMIN_URL", "postgresql://admin:pass@db:5432/postgres")
    monkeypatch.setenv("TENANT_DATABASE_PREFIX", "valid8")
    monkeypatch.setenv("EMAIL_TRANSPORT", "gmail_api")
    monkeypatch.setenv("EMAIL_TIMEOUT_SECONDS", "45")
    monkeypatch.setenv("EMAIL_SENDER_EMAIL", "mailer@example.com")
    monkeypatch.setenv("EMAIL_FROM_NAME", "VALID8 Notifications")
    monkeypatch.setenv("SMTP_HOST", "mailpit")
    monkeypatch.setenv("SMTP_PORT", "1025")
    monkeypatch.setenv("SMTP_USE_TLS", "false")
    monkeypatch.setenv("SMTP_USE_STARTTLS", "false")

    settings = get_settings()

    assert settings.database_url == "postgresql://user:pass@db:5432/app"
    assert settings.database_admin_url == "postgresql://admin:pass@db:5432/postgres"
    assert settings.tenant_database_prefix == "valid8"
    assert settings.email_transport == "gmail_api"
    assert settings.email_timeout_seconds == 45
    assert settings.email_sender_email == "mailer@example.com"
    assert settings.email_from_name == "VALID8 Notifications"
    assert settings.smtp_host == "mailpit"
    assert settings.smtp_port == 1025
    assert settings.smtp_use_tls is False
    assert settings.smtp_use_starttls is False


def test_get_settings_normalizes_relative_storage_paths(monkeypatch):
    monkeypatch.setenv("IMPORT_STORAGE_DIR", "storage/imports")
    monkeypatch.setenv("SCHOOL_LOGO_STORAGE_DIR", "storage/school_logos")

    settings = get_settings()
    repo_root = config_module._get_repo_root()

    assert Path(settings.import_storage_dir) == (repo_root / "storage" / "imports").resolve()
    assert Path(settings.school_logo_storage_dir) == (repo_root / "storage" / "school_logos").resolve()


def test_get_settings_defaults_email_transport_to_disabled_when_unset(monkeypatch):
    monkeypatch.delenv("EMAIL_TRANSPORT", raising=False)

    settings = get_settings()

    assert settings.email_transport == "disabled"
    assert settings.email_required_on_startup is False
