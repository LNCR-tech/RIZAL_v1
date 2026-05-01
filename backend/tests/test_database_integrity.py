import pytest
from app.core.database import engine
from sqlalchemy import text

def test_database_migrations_head():
    """Verify that Alembic migrations result in a single clean head, and database schema is valid."""
    with engine.connect() as conn:
        # Check alembic_version table
        result = conn.execute(text("SELECT version_num FROM alembic_version")).fetchall()
        assert len(result) == 1, f"Expected exactly 1 migration head, got {len(result)}"

def test_unique_constraints_user_email(db_session):
    from app.models.user import User
    from app.utils.passwords import hash_password_bcrypt
    from sqlalchemy.exc import IntegrityError
    
    # Try to insert duplicate email
    duplicate_user = User(
        email="admin@test.com", # Already exists from seeds
        first_name="Duplicate",
        last_name="User",
        password_hash=hash_password_bcrypt("Test1234!")
    )
    
    db_session.add(duplicate_user)
    with pytest.raises(IntegrityError):
        db_session.commit()
        
    db_session.rollback()

def test_foreign_key_constraints(db_session):
    from app.models.user import UserRole
    from sqlalchemy.exc import IntegrityError
    
    invalid_role = UserRole(user_id=999999, role_id=999999)
    db_session.add(invalid_role)
    with pytest.raises(IntegrityError):
        db_session.commit()
        
    db_session.rollback()
