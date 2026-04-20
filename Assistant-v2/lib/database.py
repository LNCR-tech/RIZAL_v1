import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from dotenv import load_dotenv
from pathlib import Path

# Setup logging
logger = logging.getLogger("assistant-v2.db")

# Load environment variables
assistant_v2_root = Path(__file__).resolve().parent.parent
project_root = assistant_v2_root.parent
load_dotenv(assistant_v2_root / ".env")
load_dotenv(project_root / ".env")

# Database URLs
APP_DATABASE_URL = os.getenv("APP_DATABASE_URL") or os.getenv("TENANT_DATABASE_URL") or os.getenv("DATABASE_URL")
ASSISTANT_DB_URL = os.getenv("ASSISTANT_DB_URL") or APP_DATABASE_URL

if not ASSISTANT_DB_URL:
    raise RuntimeError("ASSISTANT_DB_URL is required for assistant storage.")

# Assistant storage engine (conversations, messages)
engine = create_engine(ASSISTANT_DB_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Tenant application engine (The data Aura actually queries)
app_engine = None
AppSessionLocal = None
if APP_DATABASE_URL:
    app_engine = create_engine(APP_DATABASE_URL, pool_pre_ping=True)
    AppSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=app_engine)

def get_db() -> Generator[Session, None, None]:
    """Dependency for getting the assistant's own database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_app_db() -> Generator[Session, None, None]:
    """Dependency for getting the application/tenant database session."""
    if not AppSessionLocal:
        raise RuntimeError("Application database is not configured.")
    db = AppSessionLocal()
    try:
        yield db
    finally:
        db.close()
