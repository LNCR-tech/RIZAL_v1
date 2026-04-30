from unittest.mock import patch

import pytest

from app.services import google_auth_service


def _patch_verify(payload):
    return patch("app.routers.auth.verify_google_id_token", return_value=payload)


def _no_rate_limit():
    return patch("app.routers.auth.enforce_rate_limit", lambda *args, **kwargs: None)


def test_google_login_succeeds_for_existing_user(client, campus_admin_token):
    """Google login returns a token for a user that exists in the DB."""
    payload = {"email": "campus_admin@test.com", "email_verified": True, "sub": "1"}
    with _no_rate_limit(), _patch_verify(payload):
        response = client.post("/auth/google", json={"id_token": "fake"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["access_token"]
    assert body["email"] == "campus_admin@test.com"


def test_google_login_rejects_unregistered_email(client):
    payload = {"email": "nobody@example.com", "email_verified": True, "sub": "2"}
    with _no_rate_limit(), _patch_verify(payload):
        response = client.post("/auth/google", json={"id_token": "fake"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Google account is not registered."


def test_google_login_rejects_unverified_email(client):
    with _no_rate_limit(), patch(
        "app.routers.auth.verify_google_id_token",
        side_effect=google_auth_service.GoogleEmailNotVerifiedError("nope"),
    ):
        response = client.post("/auth/google", json={"id_token": "fake"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Google email is not verified."


def test_google_login_returns_403_when_disabled(client):
    with _no_rate_limit(), patch(
        "app.routers.auth.verify_google_id_token",
        side_effect=google_auth_service.GoogleAuthDisabledError("off"),
    ):
        response = client.post("/auth/google", json={"id_token": "fake"})
    assert response.status_code == 403
    assert response.json()["detail"] == "Google login is disabled."


def test_google_login_returns_401_for_invalid_token(client):
    with _no_rate_limit(), patch(
        "app.routers.auth.verify_google_id_token",
        side_effect=google_auth_service.GoogleAuthInvalidTokenError("bad"),
    ):
        response = client.post("/auth/google", json={"id_token": "fake"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Google token."
