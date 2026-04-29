from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.dependencies import get_db
from app.core.rate_limit import reset_rate_limit_state
from app.models import Base
from app.models.role import Role
from app.models.school import School
from app.models.user import User, UserRole
from app.routers import auth as auth_router
from app.services import google_auth_service


@pytest.fixture()
def app_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, expire_on_commit=False, bind=engine,
    )

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(auth_router.router)
    app.dependency_overrides[get_db] = override_get_db
    reset_rate_limit_state()

    db = TestingSessionLocal()
    school = School(name="Test", school_name="Test", school_code="TST", address="123 Test St")
    db.add(school)
    db.flush()
    role = Role(name="student")
    db.add(role)
    db.flush()
    user = User(
        email="user@example.com",
        first_name="U",
        last_name="L",
        is_active=True,
        school_id=school.id,
    )
    user.set_password("StrongP@ssword1!")
    db.add(user)
    db.flush()
    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()
    db.close()

    with TestClient(app) as client:
        yield client, TestingSessionLocal

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def _patch_verify(payload):
    return patch("app.routers.auth.verify_google_id_token", return_value=payload)


def _no_rate_limit():
    return patch("app.routers.auth.enforce_rate_limit", lambda *args, **kwargs: None)


def test_google_login_succeeds_for_existing_user(app_client):
    client, _ = app_client
    payload = {"email": "user@example.com", "email_verified": True, "sub": "1"}
    with _no_rate_limit(), _patch_verify(payload):
        response = client.post("/auth/google", json={"id_token": "fake"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["access_token"]
    assert body["email"] == "user@example.com"


def test_google_login_rejects_unregistered_email(app_client):
    client, _ = app_client
    payload = {"email": "stranger@example.com", "email_verified": True, "sub": "2"}
    with _no_rate_limit(), _patch_verify(payload):
        response = client.post("/auth/google", json={"id_token": "fake"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Google account is not registered."


def test_google_login_rejects_unverified_email(app_client):
    client, _ = app_client
    with _no_rate_limit(), patch(
        "app.routers.auth.verify_google_id_token",
        side_effect=google_auth_service.GoogleEmailNotVerifiedError("nope"),
    ):
        response = client.post("/auth/google", json={"id_token": "fake"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Google email is not verified."


def test_google_login_returns_403_when_disabled(app_client):
    client, _ = app_client
    with _no_rate_limit(), patch(
        "app.routers.auth.verify_google_id_token",
        side_effect=google_auth_service.GoogleAuthDisabledError("off"),
    ):
        response = client.post("/auth/google", json={"id_token": "fake"})
    assert response.status_code == 403
    assert response.json()["detail"] == "Google login is disabled."


def test_google_login_returns_401_for_invalid_token(app_client):
    client, _ = app_client
    with _no_rate_limit(), patch(
        "app.routers.auth.verify_google_id_token",
        side_effect=google_auth_service.GoogleAuthInvalidTokenError("bad"),
    ):
        response = client.post("/auth/google", json={"id_token": "fake"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Google token."
