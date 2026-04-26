"""Production bootstrap helpers for the backend database."""

from __future__ import annotations

from dataclasses import dataclass

from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app.core.app_settings import APP_SETTINGS
from app.core.database import SessionLocal, engine
from app.models.base import Base
from app.models.event_type import EventType
from app.models.role import Role
from app.models.user import User, UserRole

load_dotenv()

LEGACY_PLACEHOLDER_ADMIN_EMAIL = "admin@yourdomain.com"

DEFAULT_ROLES: list[dict] = [
    {"name": "admin", "display_name": "Administrator"},
    {"name": "campus_admin", "display_name": "Campus Administrator"},
    {"name": "student", "display_name": "Student"},
]

DEFAULT_EVENT_TYPE_DEFINITIONS = [
    {"name": "Regular Event", "code": "regular-event", "sort_order": 0},
    {"name": "Assembly", "code": "assembly", "sort_order": 10},
    {"name": "Seminar", "code": "seminar", "sort_order": 20},
    {"name": "Workshop", "code": "workshop", "sort_order": 30},
    {"name": "Conference", "code": "conference", "sort_order": 40},
    {"name": "Meeting", "code": "meeting", "sort_order": 50},
]


@dataclass(frozen=True)
class BootstrapSeedOptions:
    admin_email: str = APP_SETTINGS.default_admin_email
    admin_password: str = APP_SETTINGS.default_admin_password


def create_tables() -> None:
    """Create all tables."""
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    print("Database tables created")


def seed_roles(db: Session, role_names: list[str] | None = None) -> None:
    """Seed required roles."""
    roles_to_seed = DEFAULT_ROLES
    if role_names is not None:
        name_set = set(role_names)
        roles_to_seed = [r for r in DEFAULT_ROLES if r["name"] in name_set]
        # Also handle any extra names not in DEFAULT_ROLES
        known_names = {r["name"] for r in DEFAULT_ROLES}
        for extra in role_names:
            if extra not in known_names:
                roles_to_seed.append({"name": extra, "display_name": extra.replace("_", " ").title()})

    existing_role_codes = {role.code for role in db.query(Role).all()}

    for role_def in roles_to_seed:
        if role_def["name"] not in existing_role_codes:
            db.add(Role(code=role_def["name"], display_name=role_def["display_name"]))

    db.commit()
    print("Roles seeded")


def seed_event_types(db: Session) -> None:
    existing_global_names = {
        event_type.name
        for event_type in db.query(EventType).filter(EventType.school_id.is_(None)).all()
    }

    for definition in DEFAULT_EVENT_TYPE_DEFINITIONS:
        if definition["name"] in existing_global_names:
            continue
        db.add(
            EventType(
                school_id=None,
                name=definition["name"],
                code=definition["code"],
                description=None,
                is_active=True,
                sort_order=definition["sort_order"],
            )
        )

    db.commit()
    print("Event types seeded")


def _get_or_create_role(db: Session, role_name: str) -> Role:
    role = db.query(Role).filter(Role.code == role_name).first()
    if role is None:
        # Look up display_name from defaults, fall back to title-cased name
        display_name = next(
            (r["display_name"] for r in DEFAULT_ROLES if r["name"] == role_name),
            role_name.replace("_", " ").title(),
        )
        role = Role(code=role_name, display_name=display_name)
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


def _apply_admin_defaults(user: User, admin_email: str) -> bool:
    updated = False
    normalized_email = (admin_email or "").strip().lower()

    if user.email != normalized_email:
        user.email = normalized_email
        updated = True
    if user.school_id is not None:
        user.school_id = None
        updated = True
    if not user.first_name:
        user.first_name = "System"
        updated = True
    if not user.last_name:
        user.last_name = "Administrator"
        updated = True
    if not user.is_active:
        user.is_active = True
        updated = True
    if user.must_change_password:
        user.must_change_password = False
        updated = True
    if user.should_prompt_password_change:
        user.should_prompt_password_change = False
        updated = True

    return updated


def seed_admin_user(
    db: Session,
    *,
    options: BootstrapSeedOptions | None = None,
) -> None:
    """Create or repair the platform admin account."""
    resolved_options = options or BootstrapSeedOptions()
    admin_email = (resolved_options.admin_email or APP_SETTINGS.default_admin_email).strip().lower()
    admin_password = resolved_options.admin_password or APP_SETTINGS.default_admin_password

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
            school_id=None,
            first_name="System",
            middle_name=None,
            last_name="Administrator",
            is_active=True,
            must_change_password=False,
            should_prompt_password_change=False,
        )
        existing_admin.set_password(admin_password)
        db.add(existing_admin)
        db.flush()
        created_admin = True

    updated = _apply_admin_defaults(existing_admin, admin_email)
    had_admin_role = "admin" in _role_names_for_user(existing_admin)

    if _ensure_user_role(db, existing_admin, "admin"):
        updated = True

    if reused_legacy_admin or not had_admin_role:
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


def bootstrap_database(
    db: Session,
    *,
    options: BootstrapSeedOptions | None = None,
) -> None:
    """Seed only the production baseline required for a fresh deployment."""
    resolved_options = options or BootstrapSeedOptions()
    seed_roles(db)
    seed_event_types(db)
    seed_admin_user(db, options=resolved_options)


def run_production_bootstrap(
    options: BootstrapSeedOptions | None = None,
) -> None:
    """Create the minimal production data set without demo or sample records."""
    print("Starting production bootstrap...")
    db = SessionLocal()

    try:
        create_tables()
        bootstrap_database(db, options=options)
        print("Production bootstrap completed successfully")
    except Exception as exc:
        print(f"Error during production bootstrap: {exc}")
        db.rollback()
        raise
    finally:
        db.close()
