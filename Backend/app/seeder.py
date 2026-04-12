"""Use: Seeds backend tables with starter records.
Where to use: Use this from setup scripts or local development when you need sample app data.
Role: Data setup layer. It prepares initial records for the app.
"""

from datetime import date
import os

from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine
from app.models.base import Base
from app.models.role import Role
from app.models.school import School, SchoolSetting
from app.models.user import User, UserRole

load_dotenv()

LEGACY_PLACEHOLDER_ADMIN_EMAIL = "admin@yourdomain.com"


def create_tables() -> None:
    """Create all tables."""
    Base.metadata.create_all(bind=engine)
    print("Database tables created")


def seed_roles(db: Session) -> None:
    """Seed roles table with required roles."""
    role_names = ["student", "campus_admin", "admin"]
    existing_role_names = {role.name for role in db.query(Role).all()}

    for role_name in role_names:
        if role_name not in existing_role_names:
            db.add(Role(name=role_name))

    db.commit()
    print("Roles seeded")


def _get_or_create_role(db: Session, role_name: str) -> Role:
    role = db.query(Role).filter(Role.name == role_name).first()
    if role is None:
        role = Role(name=role_name)
        db.add(role)
        db.flush()
    return role


def _role_names_for_user(user: User) -> set[str]:
    return {
        assignment.role.name
        for assignment in getattr(user, "roles", [])
        if getattr(assignment, "role", None) is not None and getattr(assignment.role, "name", None)
    }


def _ensure_user_role(db: Session, user: User, role_name: str) -> bool:
    role = _get_or_create_role(db, role_name)
    if role_name in _role_names_for_user(user):
        return False
    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.flush()
    return True


def _find_user_by_email(db: Session, email: str) -> User | None:
    normalized_email = (email or "").strip().lower()
    return db.query(User).filter(User.email == normalized_email).first()


def seed_default_school(db: Session) -> School:
    """Create a default school/settings record if none exists."""
    school = db.query(School).order_by(School.id.asc()).first()
    if school:
        if not getattr(school, "school_name", None):
            school.school_name = school.name
            db.commit()
        if not db.query(SchoolSetting).filter(SchoolSetting.school_id == school.id).first():
            db.add(SchoolSetting(school_id=school.id))
            db.commit()
        print(f"School already exists: {school.name}")
        return school

    school = School(
        name=os.getenv("DEFAULT_SCHOOL_NAME", "Default School"),
        school_name=os.getenv("DEFAULT_SCHOOL_NAME", "Default School"),
        address=os.getenv("DEFAULT_SCHOOL_ADDRESS", "Default Address"),
        logo_url=os.getenv("DEFAULT_SCHOOL_LOGO_URL"),
        primary_color=os.getenv("DEFAULT_SCHOOL_PRIMARY_COLOR", "#162F65"),
        secondary_color=os.getenv("DEFAULT_SCHOOL_SECONDARY_COLOR", "#2C5F9E"),
        school_code=os.getenv("DEFAULT_SCHOOL_CODE"),
        subscription_status=os.getenv("DEFAULT_SUBSCRIPTION_STATUS", "trial"),
        active_status=True,
        subscription_plan=os.getenv("DEFAULT_SUBSCRIPTION_PLAN", "free"),
        subscription_start=date.today(),
    )

    db.add(school)
    db.flush()

    db.add(SchoolSetting(school_id=school.id))
    db.commit()
    db.refresh(school)

    print(f"Default school created: {school.name}")
    return school


def _apply_admin_defaults(user: User, admin_email: str, default_school_id: int) -> bool:
    updated = False

    if user.email != admin_email:
        user.email = admin_email
        updated = True
    # Assign admin to default school so they can access school settings during onboarding
    if getattr(user, "school_id", None) != default_school_id:
        user.school_id = default_school_id
        updated = True
    if not getattr(user, "is_active", True):
        user.is_active = True
        updated = True
    if getattr(user, "must_change_password", False):
        user.must_change_password = False
        updated = True
    if getattr(user, "should_prompt_password_change", False):
        user.should_prompt_password_change = False
        updated = True
    if getattr(user, "first_name", None) != "System":
        user.first_name = "System"
        updated = True
    if getattr(user, "middle_name", None) is not None:
        user.middle_name = None
        updated = True
    if getattr(user, "last_name", None) != "Administrator":
        user.last_name = "Administrator"
        updated = True

    return updated


def seed_admin_user(db: Session, school: School) -> None:
    """Create or repair the initial platform admin user."""
    admin_email = (os.getenv("ADMIN_EMAIL", "admin@university.edu") or "admin@university.edu").strip().lower()
    admin_password = os.getenv("ADMIN_PASSWORD", "AdminPass123!")

    existing_admin = _find_user_by_email(db, admin_email)
    legacy_admin = None
    reused_legacy_admin = False
    created_admin = False

    if existing_admin is None and admin_email != LEGACY_PLACEHOLDER_ADMIN_EMAIL:
        legacy_admin = _find_user_by_email(db, LEGACY_PLACEHOLDER_ADMIN_EMAIL)
        if legacy_admin is not None:
            existing_admin = legacy_admin
            reused_legacy_admin = True

    if existing_admin is None:
        existing_admin = User(
            email=admin_email,
            school_id=school.id,
            first_name="System",
            middle_name=None,
            last_name="Administrator",
            is_active=True,
            must_change_password=False,
            should_prompt_password_change=False,
        )
        db.add(existing_admin)
        db.flush()
        created_admin = True

    updated = _apply_admin_defaults(existing_admin, admin_email, school.id)
    had_admin_role = "admin" in _role_names_for_user(existing_admin)

    if _ensure_user_role(db, existing_admin, "admin"):
        updated = True

    if created_admin or reused_legacy_admin or not had_admin_role:
        existing_admin.set_password(admin_password)
        updated = True

    removed_legacy_placeholder = False
    if admin_email != LEGACY_PLACEHOLDER_ADMIN_EMAIL:
        legacy_admin = legacy_admin or _find_user_by_email(db, LEGACY_PLACEHOLDER_ADMIN_EMAIL)
        if legacy_admin is not None and legacy_admin.id != existing_admin.id and not _role_names_for_user(legacy_admin):
            db.delete(legacy_admin)
            removed_legacy_placeholder = True
            updated = True

    if updated:
        db.commit()

    if created_admin:
        print(f"Admin user created: {admin_email}")
        print(f"Admin password: {admin_password}")
        return

    if reused_legacy_admin:
        print(f"Legacy admin account repaired as: {admin_email}")
        print(f"Admin password: {admin_password}")
        return

    if removed_legacy_placeholder:
        print("Removed legacy placeholder admin account")
    print("Admin user already exists")


def run_seeder() -> None:
    """Main seeder function."""
    print("Starting database seeding...")
    db = SessionLocal()

    try:
        create_tables()
        seed_roles(db)
        school = seed_default_school(db)
        seed_admin_user(db, school)
        print("Database seeding completed successfully")
    except Exception as exc:
        print(f"Error during seeding: {exc}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seeder()
