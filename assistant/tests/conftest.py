import os
import datetime
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from jose import jwt

# Set env vars before importing the app
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ASSISTANT_DB_URL", "sqlite:///./test_assistant.db")
os.environ.setdefault("AI_API_KEY", "test-key")
os.environ.setdefault("AI_API_BASE", "https://test.example.com/v1")
os.environ.setdefault("AI_MODEL", "test-model")
os.environ.setdefault("BACKEND_API_BASE_URL", "http://localhost:8000")

from lib.database import Base, engine, SessionLocal
from main import app, mcp_client


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client():
    with patch.object(mcp_client, "get_all_tools", new=AsyncMock(return_value=[])), \
         patch.object(mcp_client, "call_tool", new=AsyncMock(return_value="{}")):
        with TestClient(app) as c:
            yield c


@pytest.fixture()
def auth_token():
    payload = {
        "sub": "test@aura.local",
        "school_id": 1,
        "roles": ["admin"],
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1),
    }
    return jwt.encode(payload, os.environ["SECRET_KEY"], algorithm="HS256")


@pytest.fixture()
def expired_token():
    payload = {
        "sub": "test@aura.local",
        "school_id": 1,
        "roles": ["admin"],
        "exp": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1),
    }
    return jwt.encode(payload, os.environ["SECRET_KEY"], algorithm="HS256")


@pytest.fixture()
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}
