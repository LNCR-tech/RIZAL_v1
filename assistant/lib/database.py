import os
import logging
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text, create_engine, func, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Generator
from dotenv import load_dotenv
from pathlib import Path

# Setup logging
logger = logging.getLogger("assistant.db")

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
Base = declarative_base()

# --- Models ---

class Conversation(Base):
    __tablename__ = "assistant_conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(128), index=True, nullable=False)
    user_role = Column(String(64), nullable=False)
    title = Column(String(255), nullable=True)
    status = Column(String(32), nullable=False, server_default="active")
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class Message(Base):
    __tablename__ = "assistant_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(
        String(36),
        ForeignKey("assistant_conversations.id"),
        index=True,
        nullable=False,
    )
    role = Column(String(32), nullable=False)
    content = Column(Text, nullable=False)
    visual_data = Column(Text, nullable=True)  # JSON string for visualization data
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class DailyUsage(Base):
    __tablename__ = "assistant_daily_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(128), index=True, nullable=False)
    user_role = Column(String(64), index=True, nullable=False)
    usage_date = Column(Date, index=True, nullable=False)
    message_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

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

def init_db():
    Base.metadata.create_all(bind=engine)

def get_app_db() -> Generator[Session, None, None]:
    """Dependency for getting the application/tenant database session."""
    if not AppSessionLocal:
        raise RuntimeError("Application database is not configured.")
    db = AppSessionLocal()
    try:
        yield db
    finally:
        db.close()
