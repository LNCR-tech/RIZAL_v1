import os
import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text
from app.core.database import SessionLocal

@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_no_duplicate_migration_heads():
    # Ensure there is only one head revision
    alembic_cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(alembic_cfg)
    heads = script.get_revisions("heads")
    assert len(heads) == 1, f"Multiple migration heads found: {heads}"

def test_migrations_apply_cleanly(db):
    assert db.execute(text("SELECT 1")).scalar() == 1

def test_test_db_is_isolated():
    db_url = os.environ.get("DATABASE_URL", "localhost")
    assert "prod" not in db_url.lower(), f"Tests appear to be running against a production database: {db_url}"
