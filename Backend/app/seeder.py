"""Use: Seeds backend tables with starter records.
Where to use: Use this from setup scripts or local development when you need sample app data.
Role: Data setup layer. It prepares initial records for the app.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import os

from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine
from app.models.base import Base
from app.models.governance_hierarchy import (
    GovernanceMember,
    GovernanceMemberPermission,
    GovernancePermission,
    GovernanceUnit,
    GovernanceUnitType,
    PERMISSION_DEFINITIONS,
)
from app.models.role import Role
from app.models.school import School, SchoolSetting
from app.models.user import StudentProfile, User, UserRole

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


def _apply_admin_defaults(user: User, admin_email: str) -> bool:
    updated = False

    if user.email != admin_email:
        user.email = admin_email
        updated = True
    if getattr(user, "school_id", None) is not None:
        user.school_id = None
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


def seed_admin_user(db: Session, school: School) -> User:
    """Create or repair the initial platform admin user."""
    del school

    admin_email = (os.getenv("ADMIN_EMAIL", "admin@university.edu") or "admin@university.edu").strip().lower()
    admin_password = os.getenv("ADMIN_PASSWORD", "AdminPass123!")
    reset_password = (
        os.getenv("SEED_ADMIN_RESET_PASSWORD", "false").strip().lower()
        in {"1", "true", "yes", "y"}
    )

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
        db.add(existing_admin)
        db.flush()
        created_admin = True

    updated = _apply_admin_defaults(existing_admin, admin_email)
    had_admin_role = "admin" in _role_names_for_user(existing_admin)

    if _ensure_user_role(db, existing_admin, "admin"):
        updated = True

    # Local/dev should be deterministic (optional), and legacy data can leave users without a valid admin role.
    if created_admin or reused_legacy_admin or not had_admin_role or reset_password:
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
    elif reused_legacy_admin:
        print(f"Legacy admin account repaired as: {admin_email}")
        print(f"Admin password: {admin_password}")
    else:
        if reset_password:
            print(f"Admin password reset to: {admin_password}")
        if removed_legacy_placeholder:
            print("Removed legacy placeholder admin account")
        print("Admin user already exists")

    return existing_admin


def _seed_governance_permissions(db: Session) -> None:
    existing_codes = {
        (row.permission_code.value if hasattr(row.permission_code, "value") else row.permission_code)
        for row in db.query(GovernancePermission).all()
    }
    for code, meta in PERMISSION_DEFINITIONS.items():
        code_value = code.value if hasattr(code, "value") else str(code)
        if code_value in existing_codes:
            continue
        db.add(
            GovernancePermission(
                permission_code=code,
                permission_name=meta.get("permission_name") or code_value,
                description=meta.get("description"),
            )
        )
    db.commit()


def _get_or_create_governance_unit(
    db: Session,
    *,
    school_id: int,
    unit_code: str,
    unit_name: str,
    unit_type: GovernanceUnitType,
    created_by_user_id: int | None,
    parent_unit_id: int | None = None,
) -> GovernanceUnit:
    unit = (
        db.query(GovernanceUnit)
        .filter(GovernanceUnit.school_id == school_id, GovernanceUnit.unit_code == unit_code)
        .first()
    )
    if unit:
        return unit
    unit = GovernanceUnit(
        unit_code=unit_code,
        unit_name=unit_name,
        unit_type=unit_type,
        school_id=school_id,
        parent_unit_id=parent_unit_id,
        created_by_user_id=created_by_user_id,
        is_active=True,
    )
    db.add(unit)
    db.flush()
    return unit


def _ensure_governance_member(
    db: Session,
    *,
    unit_id: int,
    user_id: int,
    assigned_by_user_id: int | None,
    position_title: str | None = None,
) -> GovernanceMember:
    member = (
        db.query(GovernanceMember)
        .filter(GovernanceMember.governance_unit_id == unit_id, GovernanceMember.user_id == user_id)
        .first()
    )
    if member:
        return member
    member = GovernanceMember(
        governance_unit_id=unit_id,
        user_id=user_id,
        assigned_by_user_id=assigned_by_user_id,
        position_title=position_title,
        is_active=True,
    )
    db.add(member)
    db.flush()
    return member


def _grant_member_permission(
    db: Session,
    *,
    governance_member_id: int,
    permission_code_value: str,
    granted_by_user_id: int | None,
) -> None:
    # permission_code is stored as a string-backed enum; normalize to the enum when possible.
    permission_code = permission_code_value
    try:
        from app.models.governance_hierarchy import PermissionCode

        permission_code = PermissionCode(permission_code_value)
    except Exception:
        permission_code = permission_code_value

    permission = db.query(GovernancePermission).filter(GovernancePermission.permission_code == permission_code).first()
    if permission is None:
        return
    exists = (
        db.query(GovernanceMemberPermission.id)
        .filter(
            GovernanceMemberPermission.governance_member_id == governance_member_id,
            GovernanceMemberPermission.permission_id == permission.id,
        )
        .first()
    )
    if exists:
        return
    db.add(
        GovernanceMemberPermission(
            governance_member_id=governance_member_id,
            permission_id=permission.id,
            granted_by_user_id=granted_by_user_id,
        )
    )


@dataclass(frozen=True)
class SeededUserTemplate:
    email: str
    password: str
    roles: tuple[str, ...]
    school_scoped: bool
    active: bool = True
    must_change_password: bool = False
    student_id: str | None = None
    governance_unit_code: str | None = None
    governance_title: str | None = None
    governance_permissions: tuple[str, ...] = ()


def _get_or_create_user_from_template(
    db: Session,
    *,
    template: SeededUserTemplate,
    school_id: int | None,
    reset_password: bool,
) -> User:
    user = _find_user_by_email(db, template.email)
    created = False
    if user is None:
        user = User(
            email=template.email.strip().lower(),
            school_id=school_id if template.school_scoped else None,
            first_name="Demo",
            middle_name=None,
            last_name="User",
            is_active=template.active,
            must_change_password=template.must_change_password,
            should_prompt_password_change=False,
        )
        user.set_password(template.password)
        db.add(user)
        db.flush()
        created = True
    else:
        updated = False
        desired_school_id = school_id if template.school_scoped else None
        if getattr(user, "school_id", None) != desired_school_id:
            user.school_id = desired_school_id
            updated = True
        if getattr(user, "is_active", True) != template.active:
            user.is_active = template.active
            updated = True
        if getattr(user, "must_change_password", False) != template.must_change_password:
            user.must_change_password = template.must_change_password
            updated = True
        if reset_password:
            user.set_password(template.password)
            updated = True
        if updated:
            db.flush()

    for role_name in template.roles:
        _ensure_user_role(db, user, role_name)

    if "student" in template.roles and template.school_scoped and template.student_id:
        profile = (
            db.query(StudentProfile)
            .filter(StudentProfile.user_id == user.id)
            .first()
        )
        if profile is None:
            db.add(
                StudentProfile(
                    user_id=user.id,
                    school_id=school_id,
                    student_id=template.student_id,
                    year_level=1,
                )
            )
        else:
            if getattr(profile, "school_id", None) != school_id:
                profile.school_id = school_id
            if getattr(profile, "student_id", None) != template.student_id:
                profile.student_id = template.student_id

    db.commit()
    if created:
        print(f"Created demo user: {template.email} roles={list(template.roles)}")
    return user


def seed_demo_users(db: Session, *, school: School, platform_admin: User) -> list[SeededUserTemplate]:
    """Seed a predictable set of demo users for local development."""
    enabled = (os.getenv("SEED_DEMO_USERS", "false").strip().lower() in {"1", "true", "yes", "y"})
    if not enabled:
        return []

    reset_password = (
        os.getenv("SEED_DEMO_RESET_PASSWORD", "false").strip().lower()
        in {"1", "true", "yes", "y"}
    )

    templates: list[SeededUserTemplate] = [
        SeededUserTemplate(
            email="campus_admin@demo.example.com",
            password="CampusAdmin123!",
            roles=("campus_admin",),
            school_scoped=True,
        ),
        SeededUserTemplate(
            email="student1@demo.example.com",
            password="Student123!",
            roles=("student",),
            school_scoped=True,
            student_id="S-0001",
        ),
        SeededUserTemplate(
            email="student2@demo.example.com",
            password="Student123!",
            roles=("student",),
            school_scoped=True,
            student_id="S-0002",
        ),
        SeededUserTemplate(
            email="student3@demo.example.com",
            password="Student123!",
            roles=("student",),
            school_scoped=True,
            student_id="S-0003",
        ),
        SeededUserTemplate(
            email="student_inactive@demo.example.com",
            password="Student123!",
            roles=("student",),
            school_scoped=True,
            active=False,
            student_id="S-0099",
        ),
        SeededUserTemplate(
            email="student_must_change@demo.example.com",
            password="TempPass123!",
            roles=("student",),
            school_scoped=True,
            must_change_password=True,
            student_id="S-0100",
        ),
        SeededUserTemplate(
            email="ssg_president@demo.example.com",
            password="GovPass123!",
            roles=("student",),
            school_scoped=True,
            student_id="S-1001",
            governance_unit_code="SSG",
            governance_title="SSG President",
            governance_permissions=("manage_events", "manage_announcements", "manage_members", "assign_permissions"),
        ),
        SeededUserTemplate(
            email="sg_officer@demo.example.com",
            password="GovPass123!",
            roles=("student",),
            school_scoped=True,
            student_id="S-1002",
            governance_unit_code="SG-1",
            governance_title="SG Officer",
            governance_permissions=("view_students", "manage_events"),
        ),
        SeededUserTemplate(
            email="org_manager@demo.example.com",
            password="GovPass123!",
            roles=("student",),
            school_scoped=True,
            student_id="S-1003",
            governance_unit_code="ORG-1",
            governance_title="ORG Manager",
            governance_permissions=("manage_announcements", "manage_events"),
        ),
    ]

    # Create/update users.
    resolved_users: dict[str, User] = {}
    for tpl in templates:
        resolved_users[tpl.email] = _get_or_create_user_from_template(
            db,
            template=tpl,
            school_id=school.id,
            reset_password=reset_password,
        )

    # Governance: permissions + units + memberships.
    _seed_governance_permissions(db)
    db.flush()

    campus_admin = resolved_users.get("campus_admin@demo.example.com")
    created_by_user_id = campus_admin.id if campus_admin else platform_admin.id

    ssg = _get_or_create_governance_unit(
        db,
        school_id=school.id,
        unit_code="SSG",
        unit_name=f"{school.school_name or school.name} SSG",
        unit_type=GovernanceUnitType.SSG,
        created_by_user_id=created_by_user_id,
        parent_unit_id=None,
    )
    sg = _get_or_create_governance_unit(
        db,
        school_id=school.id,
        unit_code="SG-1",
        unit_name="Student Government",
        unit_type=GovernanceUnitType.SG,
        created_by_user_id=created_by_user_id,
        parent_unit_id=ssg.id,
    )
    org = _get_or_create_governance_unit(
        db,
        school_id=school.id,
        unit_code="ORG-1",
        unit_name="Demo Organization",
        unit_type=GovernanceUnitType.ORG,
        created_by_user_id=created_by_user_id,
        parent_unit_id=sg.id,
    )
    db.commit()

    unit_by_code = {
        "SSG": ssg,
        "SG-1": sg,
        "ORG-1": org,
    }

    for tpl in templates:
        if not tpl.governance_unit_code:
            continue
        user = resolved_users.get(tpl.email)
        unit = unit_by_code.get(tpl.governance_unit_code)
        if not user or not unit:
            continue
        member = _ensure_governance_member(
            db,
            unit_id=unit.id,
            user_id=user.id,
            assigned_by_user_id=created_by_user_id,
            position_title=tpl.governance_title,
        )
        for perm_code in tpl.governance_permissions:
            _grant_member_permission(
                db,
                governance_member_id=member.id,
                permission_code_value=perm_code,
                granted_by_user_id=created_by_user_id,
            )
        db.commit()

    print("Demo users seeded")
    return templates


def print_dev_info(*, school: School, templates: list[SeededUserTemplate]) -> None:
    if not (os.getenv("SEED_PRINT_DEV_INFO", "false").strip().lower() in {"1", "true", "yes", "y"}):
        return

    admin_email = (os.getenv("ADMIN_EMAIL", "") or "").strip() or "admin@yourdomain.com"
    admin_password = os.getenv("ADMIN_PASSWORD", "") or "AdminPass123!"

    pgadmin_email = (os.getenv("PGADMIN_DEFAULT_EMAIL", "") or "").strip() or "admin@example.com"
    pgadmin_password = os.getenv("PGADMIN_DEFAULT_PASSWORD", "") or "admin123"

    print("")
    print("DEV URLS")
    print("Frontend: http://localhost:5173")
    print("Backend:  http://localhost:8000/docs")
    print(f"pgAdmin:  http://localhost:5050  ({pgadmin_email} / {pgadmin_password})")
    print("Mailpit:  http://localhost:8025")
    print("")
    print("SEEDED USERS")
    print(f"School: {school.school_name or school.name} (id={school.id})")
    print(f"- {admin_email} / {admin_password} roles=['admin'] scope=platform")
    for tpl in templates:
        scope = "school" if tpl.school_scoped else "platform"
        flags = []
        if not tpl.active:
            flags.append("inactive")
        if tpl.must_change_password:
            flags.append("must_change_password")
        flag_str = f" flags={flags}" if flags else ""
        governance = ""
        if tpl.governance_unit_code:
            governance = (
                f" governance_unit={tpl.governance_unit_code}"
                f" governance_title={tpl.governance_title}"
                f" governance_permissions={list(tpl.governance_permissions)}"
            )
        print(f"- {tpl.email} / {tpl.password} roles={list(tpl.roles)} scope={scope}{flag_str}{governance}")
    print("")


def run_seeder() -> None:
    """Main seeder function."""
    print("Starting database seeding...")
    db = SessionLocal()

    try:
        create_tables()
        seed_roles(db)
        school = seed_default_school(db)
        platform_admin = seed_admin_user(db, school)
        templates = seed_demo_users(db, school=school, platform_admin=platform_admin)
        print_dev_info(school=school, templates=templates)
        print("Database seeding completed successfully")
    except Exception as exc:
        print(f"Error during seeding: {exc}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seeder()
