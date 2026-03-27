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


def test_get_settings_exposes_tenant_database_fields(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@db:5432/app")
    monkeypatch.setenv("DATABASE_ADMIN_URL", "postgresql://admin:pass@db:5432/postgres")
    monkeypatch.setenv("TENANT_DATABASE_PREFIX", "valid8")
    monkeypatch.setenv("EMAIL_TRANSPORT", "gmail_api")
    monkeypatch.setenv("EMAIL_TIMEOUT_SECONDS", "45")
    monkeypatch.setenv("EMAIL_SENDER_EMAIL", "mailer@example.com")
    monkeypatch.setenv("EMAIL_FROM_NAME", "VALID8 Notifications")

    settings = get_settings()

    assert settings.database_url == "postgresql://user:pass@db:5432/app"
    assert settings.database_admin_url == "postgresql://admin:pass@db:5432/postgres"
    assert settings.tenant_database_prefix == "valid8"
    assert settings.email_transport == "gmail_api"
    assert settings.email_timeout_seconds == 45
    assert settings.email_sender_email == "mailer@example.com"
    assert settings.email_from_name == "VALID8 Notifications"

def test_get_settings_defaults_email_transport_to_disabled_when_unset(monkeypatch):
    monkeypatch.delenv("EMAIL_TRANSPORT", raising=False)

    settings = get_settings()

    assert settings.email_transport == "disabled"
    assert settings.email_required_on_startup is False
