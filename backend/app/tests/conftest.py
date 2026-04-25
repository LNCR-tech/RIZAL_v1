"""Use: Tests shared pytest fixtures and test app setup.
Where to use: Use this when running `pytest` to check that this backend behavior still works.
Role: Test layer. It protects the app from regressions.
"""

from collections.abc import Generator
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.dependencies import get_db
from app.main import app
from app.models import Base, Role, User, UserRole


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture(scope="session")
def test_session_factory(test_engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def test_db(test_engine, test_session_factory) -> Generator[Session, None, None]:
    db = test_session_factory()
    try:
        yield db
    finally:
        db.rollback()
        db.close()
        with test_engine.begin() as connection:
            for table in reversed(Base.metadata.sorted_tables):
                connection.execute(table.delete())


@pytest.fixture(scope="function")
def client(test_session_factory) -> Generator[TestClient, None, None]:
    def override_get_db():
        db = test_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    original_email_transport = os.environ.get("EMAIL_TRANSPORT")
    original_rate_limit_enabled = os.environ.get("RATE_LIMIT_ENABLED")
    original_privileged_face_verification = os.environ.get("PRIVILEGED_FACE_VERIFICATION_ENABLED")
    os.environ["EMAIL_TRANSPORT"] = "disabled"
    os.environ["RATE_LIMIT_ENABLED"] = "false"
    os.environ["PRIVILEGED_FACE_VERIFICATION_ENABLED"] = "true"
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)
        if original_email_transport is None:
            os.environ.pop("EMAIL_TRANSPORT", None)
        else:
            os.environ["EMAIL_TRANSPORT"] = original_email_transport
        if original_rate_limit_enabled is None:
            os.environ.pop("RATE_LIMIT_ENABLED", None)
        else:
            os.environ["RATE_LIMIT_ENABLED"] = original_rate_limit_enabled
        if original_privileged_face_verification is None:
            os.environ.pop("PRIVILEGED_FACE_VERIFICATION_ENABLED", None)
        else:
            os.environ["PRIVILEGED_FACE_VERIFICATION_ENABLED"] = original_privileged_face_verification


@pytest.fixture
def test_user(test_db):
    role = Role(name="admin")
    test_db.add(role)
    test_db.commit()

    user = User(
        email="test@example.com",
        first_name="Test",
        last_name="User",
    )
    user.set_password("password123")
    test_db.add(user)
    test_db.commit()

    user_role = UserRole(user_id=user.id, role_id=role.id)
    test_db.add(user_role)
    test_db.commit()

    return user
