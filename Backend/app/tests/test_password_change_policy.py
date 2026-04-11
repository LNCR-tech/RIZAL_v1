from app.services.password_change_policy import issue_new_account_password


def test_issue_new_account_password_prefers_configured_default(monkeypatch):
    monkeypatch.setenv("NEW_ACCOUNT_DEFAULT_PASSWORD", "password")

    generated = issue_new_account_password(
        generator=lambda min_length=10, max_length=14: "RandomPass123",
    )

    assert generated == "password"


def test_issue_new_account_password_uses_generator_when_default_is_unset(monkeypatch):
    monkeypatch.delenv("NEW_ACCOUNT_DEFAULT_PASSWORD", raising=False)

    generated = issue_new_account_password(
        generator=lambda min_length=10, max_length=14: "RandomPass123",
    )

    assert generated == "RandomPass123"
