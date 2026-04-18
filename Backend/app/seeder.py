"""Use: Seeds backend tables with starter records.
Where to use: Use this from setup scripts or local development when you need sample app data.
Role: Data setup layer. It prepares initial records for the app.
"""

from __future__ import annotations

from datetime import date
import csv
import os
from pathlib import Path
import random
import string

from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.utils.passwords import hash_password_bcrypt

from app.core.database import SessionLocal, engine
from app.models.base import Base
from app.models.department import Department
from app.models.governance_hierarchy import (
    GovernanceMember,
    GovernanceMemberPermission,
    GovernancePermission,
    GovernanceUnit,
    GovernanceUnitType,
    PERMISSION_DEFINITIONS,
    PermissionCode,
)
from app.models.program import Program
from app.models.role import Role
from app.models.school import School, SchoolSetting
from app.models.user import StudentProfile, User, UserRole
from app.models.sanctions import (
    EventSanctionConfig,
    SanctionRecord,
    SanctionItem,
    SanctionComplianceStatus,
    SanctionItemStatus,
    ClearanceDeadline,
    ClearanceDeadlineStatus,
)

load_dotenv()

LEGACY_PLACEHOLDER_ADMIN_EMAIL = "admin@yourdomain.com"
DEMO_SEED_RANDOM_SEED = 1337
DEFAULT_DEMO_EMAIL_DOMAIN = "demo.valid8.dev"

# Generated demo credentials are written to a local file (gitignored).
DEFAULT_DEMO_CREDENTIALS_PATH = Path(__file__).resolve().parents[1] / "storage" / "seed_credentials.csv"

# Realistic Name Matrix for production-level simulation
FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda", "David", "Elizabeth",
    "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Christopher", "Karen",
    "Charles", "Nancy", "Daniel", "Lisa", "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra",
    "Donald", "Ashley", "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
    "Kenneth", "Dorothy", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa", "Timothy", "Deborah",
    "Juan", "Maria", "Jose", "Concepcion", "Antonio", "Elena", "Ricardo", "Francisca", "Mateo", "Angela",
    "Kenji", "Yuki", "Hiroshi", "Sakura", "Wei", "Li", "Min", "Jun", "Arjun", "Ananya",
    "Cj", "Aura", "Rizal", "Crisostomo", "Ibarra", "Maria Clara", "Elias", "Basilio", "Crispin", "Simoun"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
    "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
    "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts",
    "Rizal", "Mercado", "Alonso", "Realonda", "Santos", "Reyes", "Cruz", "Bautista", "Ocampo", "Dela Cruz"
]


def create_tables() -> None:
    """Create all tables."""
    Base.metadata.create_all(bind=engine)
    print("Database tables created")


def seed_roles(db: Session) -> None:
    """Seed roles table with required roles."""
    # Note: Governance permissions are managed via governance tables; these are the auth roles
    # used for API access + login.
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


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _normalize_email(value: str) -> str:
    return (value or "").strip().lower()


def _ensure_permission_catalog(db: Session) -> None:
    existing = {row.permission_code for row in db.query(GovernancePermission).all()}
    created = 0
    for code, definition in PERMISSION_DEFINITIONS.items():
        if code in existing:
            continue
        db.add(
            GovernancePermission(
                permission_code=code,
                permission_name=definition.get("permission_name") or code.value,
                description=definition.get("description") or "",
            )
        )
        created += 1
    if created:
        db.flush()


def _get_permission(db: Session, code: PermissionCode) -> GovernancePermission:
    perm = db.query(GovernancePermission).filter(GovernancePermission.permission_code == code).first()
    if perm is None:
        raise RuntimeError(f"Missing governance permission in catalog: {code.value}")
    return perm


def _get_or_create_school(
    db: Session,
    *,
    name: str,
    school_code: str,
    address: str,
    primary_color: str,
    secondary_color: str,
    accent_color: str,
) -> School:
    school_code = (school_code or "").strip() or None
    existing = None
    if school_code:
        existing = db.query(School).filter(School.school_code == school_code).first()
    if existing is None:
        existing = db.query(School).filter(School.school_name == name).first()
    if existing is not None:
        # Ensure settings row exists (older DBs).
        if not db.query(SchoolSetting).filter(SchoolSetting.school_id == existing.id).first():
            db.add(
                SchoolSetting(
                    school_id=existing.id,
                    primary_color=primary_color,
                    secondary_color=secondary_color,
                    accent_color=accent_color,
                )
            )
            db.flush()
        return existing

    school = School(
        name=name,
        school_name=name,
        address=address,
        school_code=school_code,
        subscription_status="trial",
        active_status=True,
        subscription_plan="free",
        subscription_start=date.today(),
        primary_color=primary_color,
        secondary_color=secondary_color,
    )
    db.add(school)
    db.flush()
    db.add(
        SchoolSetting(
            school_id=school.id,
            primary_color=primary_color,
            secondary_color=secondary_color,
            accent_color=accent_color,
        )
    )
    db.refresh(school)
    return school


def _get_or_create_department(db: Session, *, school_id: int, name: str) -> Department:
    existing = (
        db.query(Department)
        .filter(Department.school_id == school_id, Department.name == name)
        .first()
    )
    if existing is not None:
        return existing
    dept = Department(school_id=school_id, name=name)
    db.add(dept)
    db.flush()
    return dept


def _get_or_create_program(db: Session, *, school_id: int, name: str) -> Program:
    existing = (
        db.query(Program)
        .filter(Program.school_id == school_id, Program.name == name)
        .first()
    )
    if existing is not None:
        return existing
    prog = Program(school_id=school_id, name=name)
    db.add(prog)
    db.flush()
    return prog


def _get_or_create_governance_unit(
    db: Session,
    *,
    school_id: int,
    unit_code: str,
    unit_name: str,
    unit_type: GovernanceUnitType,
    parent_unit_id: int | None = None,
    department_id: int | None = None,
    program_id: int | None = None,
    created_by_user_id: int | None = None,
) -> GovernanceUnit:
    existing = (
        db.query(GovernanceUnit)
        .filter(
            GovernanceUnit.school_id == school_id,
            GovernanceUnit.unit_code == unit_code,
        )
        .first()
    )
    if existing is not None:
        return existing
    unit = GovernanceUnit(
        school_id=school_id,
        unit_code=unit_code,
        unit_name=unit_name,
        unit_type=unit_type,
        parent_unit_id=parent_unit_id,
        department_id=department_id,
        program_id=program_id,
        created_by_user_id=created_by_user_id,
        is_active=True,
    )
    db.add(unit)
    db.flush()
    return unit


def _get_or_create_user(
    db: Session,
    *,
    email: str,
    password: str,
    school_id: int | None,
    first_name: str,
    last_name: str,
    must_change_password: bool = False,
    reset_password: bool = False,
) -> User:
    normalized_email = _normalize_email(email)
    user = db.query(User).filter(User.email == normalized_email).first()
    if user is None:
        user = User(
            email=normalized_email,
            school_id=school_id,
            first_name=first_name,
            middle_name=None,
            last_name=last_name,
            is_active=True,
            must_change_password=must_change_password,
            should_prompt_password_change=False,
        )
        # `password_hash` is NOT NULL; set it before first flush/insert.
        user.set_password(password)
        db.add(user)
        db.flush()
        return user

    user.is_active = True
    if reset_password:
        user.set_password(password)
    return user


def _ensure_student_profile(
    db: Session,
    *,
    user: User,
    school_id: int,
    student_id: str,
    department_id: int | None,
    program_id: int | None,
    year_level: int,
    section: str,
) -> None:
    existing = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    if existing is not None:
        return
    profile = StudentProfile(
        user_id=user.id,
        school_id=school_id,
        student_id=student_id,
        department_id=department_id,
        program_id=program_id,
        year_level=year_level,
        section=section,
        is_face_registered=False,
        registration_complete=True,
    )
    db.add(profile)


def _assign_governance_membership(
    db: Session,
    *,
    user: User,
    governance_unit: GovernanceUnit,
    assigned_by_user_id: int | None,
    permission_codes: list[PermissionCode],
) -> None:
    existing = (
        db.query(GovernanceMember)
        .filter(
            GovernanceMember.governance_unit_id == governance_unit.id,
            GovernanceMember.user_id == user.id,
        )
        .first()
    )
    if existing is None:
        existing = GovernanceMember(
            governance_unit_id=governance_unit.id,
            user_id=user.id,
            position_title="Officer",
            assigned_by_user_id=assigned_by_user_id,
            is_active=True,
        )
        db.add(existing)
        db.flush()
    else:
        existing.is_active = True

    existing_codes = {
        mp.permission.permission_code
        for mp in getattr(existing, "member_permissions", [])
        if getattr(mp, "permission", None) is not None
    }
    for code in permission_codes:
        if code in existing_codes:
            continue
        perm = _get_permission(db, code)
        db.add(
            GovernanceMemberPermission(
                governance_member_id=existing.id,
                permission_id=perm.id,
                granted_by_user_id=assigned_by_user_id,
            )
        )


def seed_demo_data(
    db: Session,
    *,
    schools_target: int = 5,
    users_target: int = 100,
    credentials_path: Path = DEFAULT_DEMO_CREDENTIALS_PATH,
) -> None:
    """Seed a multi-school demo dataset for manual UI + assistant testing."""
    rng = random.Random(DEMO_SEED_RANDOM_SEED)
    demo_email_domain = (os.getenv("SEED_DEMO_EMAIL_DOMAIN") or DEFAULT_DEMO_EMAIL_DOMAIN).strip().lstrip("@").lower()

    # Older demo datasets used `@demo.local` which fails strict email validation. Repair in-place so
    # existing foreign keys stay valid and users can still log in.
    legacy_domain = "demo.local"
    if demo_email_domain and demo_email_domain != legacy_domain:
        legacy_users = db.query(User).filter(User.email.like(f"%@{legacy_domain}")).all()
        for user in legacy_users:
            local_part = (user.email or "").split("@", 1)[0]
            if not local_part:
                continue
            candidate = f"{local_part}@{demo_email_domain}"
            collision = db.query(User).filter(User.email == candidate, User.id != user.id).first()
            if collision is None:
                user.email = candidate
        db.flush()

    demo_schools = [
        ("Aurora State University", "ASU", "1 Aurora Ave", "#162F65", "#2C5F9E", "#4A90E2"),
        ("Bayview Polytechnic Institute", "BPI", "22 Bayview Rd", "#0B3D2E", "#1E6F5C", "#5BC0BE"),
        ("Cedar Ridge College", "CRC", "7 Cedar Ridge", "#3B1F2B", "#B76E79", "#F2C14E"),
        ("Delta City University", "DCU", "99 Delta Blvd", "#1D3557", "#457B9D", "#E63946"),
        ("Evergreen Arts & Tech", "EAT", "14 Evergreen St", "#2D1E2F", "#6D597A", "#B56576"),
    ]
    demo_schools = demo_schools[: max(1, schools_target)]

    _ensure_permission_catalog(db)

    schools: list[School] = []
    for name, code, address, p, s, a in demo_schools:
        schools.append(
            _get_or_create_school(
                db,
                name=name,
                school_code=code,
                address=address,
                primary_color=p,
                secondary_color=s,
                accent_color=a,
            )
        )

    # Create departments/programs and governance units per school.
    school_context: dict[int, dict[str, object]] = {}
    for school in schools:
        dept_names = [
            "College of Engineering",
            "College of Business",
            "College of Arts",
            "College of Computing",
        ]
        prog_names = [
            "BS Computer Science",
            "BS Information Technology",
            "BS Civil Engineering",
            "BS Accountancy",
            "BA Communication",
            "BS Data Science",
        ]
        departments = [_get_or_create_department(db, school_id=school.id, name=n) for n in dept_names]
        programs = [_get_or_create_program(db, school_id=school.id, name=n) for n in prog_names]

        # Associate programs with departments (many-to-many).
        for program in programs:
            # Link each program to 1-2 departments deterministically.
            chosen = rng.sample(departments, k=2 if rng.random() < 0.35 else 1)
            for dept in chosen:
                if dept not in program.departments:
                    program.departments.append(dept)

        ssg = _get_or_create_governance_unit(
            db,
            school_id=school.id,
            unit_code="SSG",
            unit_name="Supreme Students Government",
            unit_type=GovernanceUnitType.SSG,
        )

        sg_units: list[GovernanceUnit] = []
        for dept in departments[:2]:
            sg_units.append(
                _get_or_create_governance_unit(
                    db,
                    school_id=school.id,
                    unit_code=f"SG-{dept.id}",
                    unit_name=f"Student Government ({dept.name})",
                    unit_type=GovernanceUnitType.SG,
                    parent_unit_id=ssg.id,
                    department_id=dept.id,
                )
            )

        org_units: list[GovernanceUnit] = []
        for idx, program in enumerate(programs[:3]):
            parent_sg = sg_units[idx % len(sg_units)] if sg_units else ssg
            org_units.append(
                _get_or_create_governance_unit(
                    db,
                    school_id=school.id,
                    unit_code=f"ORG-{program.id}",
                    unit_name=f"Org ({program.name})",
                    unit_type=GovernanceUnitType.ORG,
                    parent_unit_id=parent_sg.id,
                    program_id=program.id,
                )
            )

        school_context[school.id] = {
            "departments": departments,
            "programs": programs,
            "ssg": ssg,
            "sg_units": sg_units,
            "org_units": org_units,
        }

    # Make sure we have roles to assign.
    _get_or_create_role(db, "student")
    _get_or_create_role(db, "campus_admin")
    _get_or_create_role(db, "admin")
    db.flush()

    # Build demo users.
    credentials_path.parent.mkdir(parents=True, exist_ok=True)
    created_credentials: list[dict[str, str]] = []

    def _record_cred(*, email: str, password: str, roles: list[str], permissions: list[str], school: School | None):
        created_credentials.append(
            {
                "email": email,
                "password": password,
                "school_code": school.school_code if school else "",
                "school_id": str(school.id) if school else "",
                "roles": ",".join(roles),
                "permissions": ",".join(permissions),
            }
        )

    # 3 platform admins (no school scope).
    platform_admin_password = "AdminPass123!"
    for i in range(1, 4):
        email = f"platform.admin{i}@{demo_email_domain}"
        user = _get_or_create_user(
            db,
            email=email,
            password=platform_admin_password,
            school_id=None,
            first_name="Platform",
            last_name=f"Admin{i}",
            must_change_password=False,
            reset_password=True,
        )
        _ensure_user_role(db, user, "admin")
        _record_cred(email=user.email, password=platform_admin_password, roles=["admin"], permissions=[], school=None)

    # One campus admin per school.
    campus_admin_password = "CampusPass123!"
    campus_admin_users_by_school: dict[int, User] = {}
    for school in schools:
        email = f"campus.admin+{(school.school_code or str(school.id)).lower()}@{demo_email_domain}"
        user = _get_or_create_user(
            db,
            email=email,
            password=campus_admin_password,
            school_id=school.id,
            first_name="Campus",
            last_name=f"Admin{school.school_code or school.id}",
            must_change_password=False,
            reset_password=True,
        )
        _ensure_user_role(db, user, "campus_admin")
        campus_admin_users_by_school[school.id] = user
        _record_cred(
            email=user.email,
            password=campus_admin_password,
            roles=["campus_admin"],
            permissions=[],
            school=school,
        )

    # Remaining users: mostly students with varied governance permissions.
    remaining = max(0, users_target - (3 + len(schools)))
    # Mix: 70% plain students, 30% governance officers.
    if remaining == 0:
        officer_count = 0
        student_count = 0
    else:
        officer_count = max(1, int(remaining * 0.30))
        student_count = remaining - officer_count

    def _create_student_user(*, school: School, index: int, is_officer: bool) -> tuple[User, str]:
        password = f"UserPass{index:03d}!"
        email = f"user{index:03d}+{(school.school_code or school.id).lower()}@{demo_email_domain}"
        user = _get_or_create_user(
            db,
            email=email,
            password=password,
            school_id=school.id,
            first_name="Demo",
            last_name=f"User{index:03d}",
            must_change_password=False,
            reset_password=True,
        )
        _ensure_user_role(db, user, "student")

        ctx = school_context[school.id]
        departments: list[Department] = ctx["departments"]  # type: ignore[assignment]
        programs: list[Program] = ctx["programs"]  # type: ignore[assignment]
        dept = rng.choice(departments)
        prog = rng.choice(programs)
        _ensure_student_profile(
            db,
            user=user,
            school_id=school.id,
            student_id=f"{school.school_code or 'SCH'}-{index:04d}",
            department_id=dept.id,
            program_id=prog.id,
            year_level=1 + (index % 4),
            section=f"SEC-{1 + (index % 3)}",
        )
        return user, password

    # Create plain students.
    index_base = 1
    current_index = 1
    for _ in range(student_count):
        school = rng.choice(schools)
        user, password = _create_student_user(school=school, index=current_index, is_officer=False)
        _record_cred(email=user.email, password=password, roles=["student"], permissions=[], school=school)
        current_index += 1

    # Create officers with varied permissions and unit types.
    officer_permission_sets: list[list[PermissionCode]] = [
        [PermissionCode.VIEW_STUDENTS],
        [PermissionCode.VIEW_STUDENTS, PermissionCode.MANAGE_STUDENTS],
        [PermissionCode.MANAGE_EVENTS, PermissionCode.MANAGE_ATTENDANCE],
        [PermissionCode.MANAGE_ANNOUNCEMENTS],
        [PermissionCode.ASSIGN_PERMISSIONS, PermissionCode.MANAGE_MEMBERS],
        [PermissionCode.VIEW_SANCTIONED_STUDENTS_LIST, PermissionCode.VIEW_SANCTIONS_DASHBOARD],
    ]

    for j in range(officer_count):
        school = schools[j % len(schools)]
        user, password = _create_student_user(school=school, index=current_index, is_officer=True)
        ctx = school_context[school.id]
        ssg: GovernanceUnit = ctx["ssg"]  # type: ignore[assignment]
        sg_units: list[GovernanceUnit] = ctx["sg_units"]  # type: ignore[assignment]
        org_units: list[GovernanceUnit] = ctx["org_units"]  # type: ignore[assignment]

        unit_choice_pool = [ssg, *sg_units, *org_units]
        chosen_unit = unit_choice_pool[(current_index + j) % len(unit_choice_pool)]
        assigned_by = campus_admin_users_by_school[school.id].id
        perms = officer_permission_sets[(current_index + j) % len(officer_permission_sets)]
        _assign_governance_membership(
            db,
            user=user,
            governance_unit=chosen_unit,
            assigned_by_user_id=assigned_by,
            permission_codes=perms,
        )

        # Assistant derives governance roles/permissions from JWT; backend will include these in token.
        derived_role = chosen_unit.unit_type.value.lower()
        _record_cred(
            email=user.email,
            password=password,
            roles=["student", derived_role],
            permissions=[p.value for p in perms],
            school=school,
        )
        current_index += 1

    db.commit()

    # Write credentials CSV (overwrite so it's always accurate for the current seed run).
    fieldnames = ["email", "password", "school_code", "school_id", "roles", "permissions"]
    with credentials_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in created_credentials:
            writer.writerow(row)

    print(f"Demo seed credentials written to: {credentials_path}")


def _apply_admin_defaults(user: User, admin_email: str) -> bool:
    updated = False

    if user.email != admin_email:
        user.email = admin_email
        updated = True
    # Platform admin should not be assigned to a school
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


def wipe_database_records(db: Session) -> None:
    """Clear all records from application tables without dropping schemas."""
    from app.models.attendance import Attendance
    from app.models.event import Event
    from app.models.governance_hierarchy import GovernanceMember, GovernanceMemberPermission, GovernanceUnit
    from app.models.user import StudentProfile, User, UserRole
    from app.models.program import Program
    from app.models.department import Department
    from app.models.school import School, SchoolSetting
    from app.models.role import Role

    print("Cleaning existing database records (Safe Wipe)...")
    # Order matters for foreign keys
    db.query(Attendance).delete()
    db.query(GovernanceMemberPermission).delete()
    db.query(GovernanceMember).delete()
    db.query(GovernanceUnit).delete()
    db.query(StudentProfile).delete()
    db.query(UserRole).delete()
    db.query(User).filter(User.email != os.getenv("ADMIN_EMAIL", "admin@university.edu")).delete()
    db.query(Event).delete()
    db.query(Program).delete()
    db.query(Department).delete()
    db.query(SchoolSetting).delete()
    db.query(School).delete()
    db.query(Role).delete()
    db.commit()
    print("Database records cleaned.")


def seed_massive_attendance_data(db: Session, target_school: School) -> None:
    """Generate 1M attendance records using high-performance bulk insertion."""
    import random
    import csv
    from datetime import datetime, timedelta, timezone
    from app.models.attendance import Attendance
    from app.models.event import Event, EventStatus
    from app.models.user import StudentProfile, User

    students_target = int(os.getenv("SEED_MASSIVE_STUDENTS", "5000"))
    records_target = int(os.getenv("SEED_MASSIVE_RECORDS", "1000000"))
    events_count = 500

    print(f"--- MASSIVE SEED START ---")
    print(f"Target: {students_target} students, {events_count} events, {records_target} attendances.")

    # 1. Create Colleges/Departments and Programs
    colleges = [
        ("College of Engineering", ["BS Civil Engineering", "BS Computer Engineering", "BS Electrical Engineering"]),
        ("College of Science", ["BS Biology", "BS Mathematics", "BS Physics", "BS Computer Science"]),
        ("College of Business", ["BS Accountancy", "BS Business Administration", "BS Marketing"]),
        ("College of Arts & Letters", ["BA Communication", "BA Psychology", "BA Philosophy"]),
        ("College of Education", ["BSEd Mathematics", "BSEd English"])
    ]

    all_programs_with_depts = []
    for dept_name, progs in colleges:
        dept = _get_or_create_department(db, school_id=target_school.id, name=dept_name)
        for p_name in progs:
            prog = _get_or_create_program(db, school_id=target_school.id, name=p_name)
            # Link them if not already linked (Many-to-Many)
            if dept not in prog.departments:
                prog.departments.append(dept)
            all_programs_with_depts.append((prog, dept.id))
    db.commit()

    # 2. Create Students
    print(f"Generating {students_target} realistic students (Password Hashing Optimized)...")
    student_profiles = []
    created_creds = []
    
    # PRE-CALCULATE HASH ONCE: This eliminates 4,999 expensive Bcrypt operations.
    common_password = "MassivePass123!"
    template_hash = hash_password_bcrypt(common_password)
    
    for i in range(1, students_target + 1):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        email = f"student.{i:05d}@massive.{DEFAULT_DEMO_EMAIL_DOMAIN}"
        
        user = User(
            email=email,
            school_id=target_school.id,
            first_name=first,
            last_name=last,
            password_hash=template_hash, # Direct assignment
            is_active=True,
            must_change_password=False
        )
        db.add(user)
        db.flush()
        
        _ensure_user_role(db, user, "student")
        
        prog, dept_id = random.choice(all_programs_with_depts)
        profile = StudentProfile(
            user_id=user.id,
            school_id=target_school.id,
            student_id=f"2024-{i:05d}",
            department_id=dept_id,
            program_id=prog.id,
            year_level=random.randint(1, 4),
            section=f"Section-{random.randint(1, 10)}",
            is_face_registered=random.random() > 0.2
        )
        db.add(profile)
        student_profiles.append(profile)
        
        created_creds.append({
            "email": email,
            "password": common_password,
            "school_code": target_school.school_code or "",
            "school_id": str(target_school.id),
            "roles": "student",
            "permissions": ""
        })
        
        if i % 1000 == 0:
            db.commit()
            print(f"  Created {i} students...")

    db.commit()

    # 3. Create Events
    print(f"Generating {events_count} historical events...")
    events_list = []
    start_date = datetime.now(timezone.utc) - timedelta(days=730)
    
    for i in range(events_count):
        e_date = start_date + timedelta(days=random.randint(0, 720), hours=random.randint(7, 18))
        event = Event(
            school_id=target_school.id,
            name=f"Standard Check-in: {e_date.strftime('%B %d, %Y')}",
            location="University Campus - Hall " + str(random.randint(1, 10)),
            start_datetime=e_date,
            end_datetime=e_date + timedelta(hours=2),
            status=EventStatus.COMPLETED if e_date < datetime.now(timezone.utc) else EventStatus.UPCOMING
        )
        db.add(event)
        events_list.append(event)
        if i % 100 == 0:
            db.flush()
    db.commit()

    # 4. Generate 1M Attendance Records (Optimized Bulk)
    print(f"Generating {records_target} attendance records (Bulk Insert Mode)...")
    student_ids = [p.id for p in student_profiles]
    event_ids = [e.id for e in events_list]
    
    batch_size = 50000
    statuses = ["present", "present", "present", "present", "late", "absent", "excused"]
    
    for start_idx in range(0, records_target, batch_size):
        batch = []
        current_batch_end = min(start_idx + batch_size, records_target)
        
        for _ in range(start_idx, current_batch_end):
            batch.append({
                "student_id": random.choice(student_ids),
                "event_id": random.choice(event_ids),
                "time_in": datetime.now(timezone.utc) - timedelta(days=random.randint(0, 700)),
                "status": random.choice(statuses),
                "method": random.choice(["face_scan", "rfid", "manual"]),
                "check_in_status": "verified"
            })
        
        db.bulk_insert_mappings(Attendance, batch)
        db.commit()
        print(f"  Inserted {current_batch_end} / {records_target} records...")

    # Write credentials to storage
    fieldnames = ["email", "password", "school_code", "school_id", "roles", "permissions"]
    # If wiping, overwrite the file to ensure sync. Otherwise append.
    mode = "w" if _as_bool(os.getenv("SEED_WIPE_EXISTING"), False) else "a"
    with DEFAULT_DEMO_CREDENTIALS_PATH.open(mode, newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        if mode == "w":
            writer.writeheader()
        for row in created_creds:
            writer.writerow(row)

    print(f"Massive seeding completed. {records_target} records added.")

    # 5. Sanction Universe
    seed_massive_sanctions(db, target_school=target_school, students=student_profiles, events=events_list)


def seed_massive_sanctions(db: Session, target_school: School, students: list[StudentProfile], events: list[Event]) -> None:
    """Generate high-volume sanction records for absentees of major events."""
    import random
    from datetime import datetime, timedelta, timezone

    print(f"--- SANCTION UNIVERSE START ---")
    
    # 1. Select 'Major Assemblies' to trigger sanctions (approx 10% of events)
    major_events = random.sample(events, k=max(1, len(events) // 10))
    print(f"Assigning sanction rules to {len(major_events)} major events...")

    sanction_configs = []
    for event in major_events:
        config = EventSanctionConfig(
            school_id=target_school.id,
            event_id=event.id,
            sanctions_enabled=True,
            item_definitions_json=[
                {"code": "WARN", "name": "Written Warning", "description": "Formal warning for absence"},
                {"code": "COMM", "name": "Community Service (4hrs)", "description": "Campus cleaning/maintenance"},
                {"code": "FINE", "name": "Clearance Fine", "description": "PHP 50.00 administrative fee"}
            ]
        )
        db.add(config)
        sanction_configs.append(config)
    db.commit()

    # 2. Generate Sanction Records for absentees
    # To keep it efficient, we'll pick a subset of students who were 'absent'
    # In our massive seed, we didn't explicitly track 'attendance' objects for all 5k students per event,
    # so we'll just simulate the absentees for these major events.
    print(f"Generating sanction records for absentees...")
    sanction_records = []
    
    for config in sanction_configs:
        # Assume 15% of students were absent from major events
        absentees = random.sample(students, k=int(len(students) * 0.15))
        
        batch = []
        for student in absentees:
            is_complied = random.random() > 0.6
            record = {
                "school_id": target_school.id,
                "event_id": config.event_id,
                "sanction_config_id": config.id,
                "student_profile_id": student.id,
                "status": SanctionComplianceStatus.COMPLIED if is_complied else SanctionComplianceStatus.PENDING,
                "complied_at": datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30)) if is_complied else None,
                "notes": "Automatically generated for non-attendance."
            }
            batch.append(record)
        
        # Batch insert for performance
        db.bulk_insert_mappings(SanctionRecord, batch)
        db.commit()
        
        # We need the IDs for the SanctionItems, so we'll fetch them back in chunks
        # This is a bit slower but necessary for the foreign keys
        records = db.query(SanctionRecord).filter(SanctionRecord.event_id == config.event_id).all()
        sanction_records.extend(records)

    # 3. Generate Sanction Items
    print(f"Building {len(sanction_records) * 2} sanction items...")
    item_batch = []
    for record in sanction_records:
        # Every sanction gets a Warning
        item_batch.append({
            "sanction_record_id": record.id,
            "item_code": "WARN",
            "item_name": "Written Warning",
            "status": SanctionItemStatus.COMPLIED if record.status == SanctionComplianceStatus.COMPLIED else SanctionItemStatus.PENDING
        })
        # 50% also get Community Service
        if random.random() > 0.5:
            item_batch.append({
                "sanction_record_id": record.id,
                "item_code": "COMM",
                "item_name": "Community Service (4hrs)",
                "status": SanctionItemStatus.COMPLIED if record.status == SanctionComplianceStatus.COMPLIED else SanctionItemStatus.PENDING
            })

    # Massive bulk insert for items
    chunk_size = 10000
    for i in range(0, len(item_batch), chunk_size):
        chunk = item_batch[i:i+chunk_size]
        db.bulk_insert_mappings(SanctionItem, chunk)
        db.commit()

    # 4. Add Clearance Deadlines
    print(f"Setting semester clearance deadlines...")
    deadlines = [
        ("End of Semester 1", datetime.now(timezone.utc) + timedelta(days=30)),
        ("Midterm Clearance", datetime.now(timezone.utc) - timedelta(days=15))
    ]
    
    for name, dt in deadlines:
        deadline = ClearanceDeadline(
            school_id=target_school.id,
            event_id=random.choice(major_events).id,
            deadline_at=dt,
            status=ClearanceDeadlineStatus.ACTIVE if dt > datetime.now(timezone.utc) else ClearanceDeadlineStatus.EXPIRED,
            message=f"Please settle all pending sanctions for {name}."
        )
        db.add(deadline)
    
    db.commit()
    print(f"Sanction Universe seeded successfully.")



def run_seeder() -> None:
    """Main seeder function."""
    print("Starting database seeding...")
    db = SessionLocal()

    try:
        create_tables()

        if _as_bool(os.getenv("SEED_WIPE_EXISTING"), False):
            wipe_database_records(db)

        # Basic infra always seeded
        seed_roles(db)
        school = seed_default_school(db)
        seed_admin_user(db, school)
        
        # Check both SEED_DATABASE (Cj's preferred) and SEED_DEMO_DATA (legacy)
        should_seed = os.getenv("SEED_DATABASE")
        if should_seed is None:
            should_seed = os.getenv("SEED_DEMO_DATA")

        if _as_bool(should_seed, True):
            if _as_bool(os.getenv("SEED_MASSIVE_ATTENDANCE"), False):
                seed_massive_attendance_data(db, target_school=school)
            else:
                schools_target = max(1, int(os.getenv("SEED_DEMO_SCHOOLS", "5")))
                users_target = max(1, int(os.getenv("SEED_DEMO_USERS", "100")))
                seed_demo_data(db, schools_target=schools_target, users_target=users_target)

        print("Database seeding completed successfully")
    except Exception as exc:
        print(f"Error during seeding: {exc}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seeder()
