"""Generate a large Misamis University seed dataset for local and staging databases."""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

from sqlalchemy import inspect, insert
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.core.database import SessionLocal, engine
from app.models.associations import program_department_association
from app.models.attendance import Attendance
from app.models.department import Department
from app.models.event import Event, EventStatus
from app.models.governance_hierarchy import (
    GovernanceMember,
    GovernanceMemberPermission,
    GovernancePermission,
    GovernanceUnit,
    GovernanceUnitPermission,
    GovernanceUnitType,
    PermissionCode,
)
from app.models.program import Program
from app.models.role import Role
from app.models.sanctions import (
    EventSanctionConfig,
    SanctionComplianceStatus,
    SanctionDelegation,
    SanctionDelegationScopeType,
    SanctionItem,
    SanctionItemStatus,
    SanctionRecord,
)
from app.models.school import School, SchoolSetting
from app.models.user import StudentProfile, User, UserRole
from app.seeder import seed_roles
from app.services.governance_hierarchy_service import ensure_permission_catalog
from app.utils.passwords import generate_secure_password, hash_password_bcrypt

SEED_SCHOOL_NAME = "Misamis University"
SEED_SCHOOL_CODE = "MU-SEED"
DEFAULT_ATTENDANCE_TARGET = 1_000_000
DEFAULT_STUDENT_COUNT = 15_000
DEFAULT_EVENT_COUNT = 33
SEED_EMAIL_DOMAIN = "misamisu.seed.edu.ph"
DEFAULT_PASSWORD_HASH_ROUNDS = 6
DEFAULT_USER_BATCH_SIZE = 500
DEFAULT_ATTENDANCE_BATCH_SIZE = 5_000
ABSENCE_MODULUS = 6

REQUIRED_TABLES = {
    "roles",
    "users",
    "user_roles",
    "schools",
    "school_settings",
    "departments",
    "programs",
    "program_department_association",
    "student_profiles",
    "governance_units",
    "governance_members",
    "governance_permissions",
    "governance_unit_permissions",
    "governance_member_permissions",
    "events",
    "attendances",
    "event_sanction_configs",
    "sanction_records",
    "sanction_items",
    "sanction_delegations",
}

DEPARTMENT_PROGRAMS = (
    ("College of Arts and Sciences", ("BS Biology", "BA English", "BS Psychology")),
    ("College of Business and Management", ("BS Accountancy", "BSBA Marketing", "BS Entrepreneurship")),
    ("College of Engineering", ("BS Civil Engineering", "BS Electrical Engineering", "BS Mechanical Engineering")),
    ("College of Education", ("BSEd English", "BSEd Mathematics", "BEEd")),
    ("College of Computing", ("BS Computer Science", "BS Information Technology", "BS Information Systems")),
)

FILIPINO_FIRST_NAMES = (
    "Aaron", "Aira", "Alden", "Alex", "Alyssa", "Andrea", "Angela", "Anthony", "Arvin", "Bea",
    "Ben", "Bianca", "Carla", "Carl", "Cedric", "Chloe", "Christian", "Christine", "Daniel", "Daphne",
    "David", "Denise", "Dianne", "Elaine", "Eli", "Erika", "Frances", "Gabriel", "Hannah", "Hazel",
    "Ian", "Isabel", "Janelle", "Jasmine", "Jay", "Jerome", "Joshua", "Joyce", "Karla", "Kevin",
    "Kim", "Kyle", "Lance", "Lara", "Leah", "Louise", "Mae", "Marco", "Maria", "Mark",
    "Marlon", "Mia", "Miguel", "Nadine", "Nico", "Noel", "Paolo", "Patricia", "Paula", "Ralph",
    "Raymond", "Rea", "Rico", "Samantha", "Sean", "Sophia", "Trisha", "Vanessa", "Victor", "Yna",
)

FILIPINO_MIDDLE_NAMES = ("Anne", "Claire", "Grace", "Joy", "Kate", "Mae", "Lou", "Marie", "Rose", "Jean")

FILIPINO_LAST_NAMES = (
    "Abad", "Aquino", "Bacalso", "Bautista", "Cabrera", "Castillo", "Cruz", "Dela Cruz", "Dizon", "Domingo",
    "Escobar", "Fernandez", "Flores", "Garcia", "Gonzales", "Hernandez", "Lopez", "Mendoza", "Navarro", "Pascual",
    "Ramos", "Reyes", "Rivera", "Rodriguez", "Salazar", "Santos", "Soriano", "Suarez", "Torres", "Valdez",
)

EVENT_THEMES = (
    "University Assembly",
    "Leadership Forum",
    "Academic Excellence Summit",
    "Student Wellness Fair",
    "Campus Unity Program",
    "Innovation Showcase",
    "Community Service Briefing",
    "Research Colloquium",
    "Career Readiness Day",
    "Student Affairs Town Hall",
    "Recognition Ceremony",
)

EVENT_LOCATIONS = (
    "MU Main Gymnasium",
    "MU Audio Visual Hall",
    "MU Engineering Auditorium",
    "MU Open Grounds",
    "MU Student Center",
    "MU Library Conference Hall",
)

SSG_PERMISSION_CODES = {
    PermissionCode.CREATE_SG,
    PermissionCode.MANAGE_STUDENTS,
    PermissionCode.VIEW_STUDENTS,
    PermissionCode.MANAGE_MEMBERS,
    PermissionCode.MANAGE_EVENTS,
    PermissionCode.MANAGE_ATTENDANCE,
    PermissionCode.MANAGE_ANNOUNCEMENTS,
    PermissionCode.ASSIGN_PERMISSIONS,
    PermissionCode.VIEW_SANCTIONED_STUDENTS_LIST,
    PermissionCode.VIEW_STUDENT_SANCTION_DETAIL,
    PermissionCode.APPROVE_SANCTION_COMPLIANCE,
    PermissionCode.CONFIGURE_EVENT_SANCTIONS,
    PermissionCode.EXPORT_SANCTIONED_STUDENTS,
    PermissionCode.VIEW_SANCTIONS_DASHBOARD,
}

SG_PERMISSION_CODES = {
    PermissionCode.CREATE_ORG,
    PermissionCode.MANAGE_STUDENTS,
    PermissionCode.VIEW_STUDENTS,
    PermissionCode.MANAGE_MEMBERS,
    PermissionCode.MANAGE_EVENTS,
    PermissionCode.MANAGE_ATTENDANCE,
    PermissionCode.MANAGE_ANNOUNCEMENTS,
    PermissionCode.ASSIGN_PERMISSIONS,
    PermissionCode.VIEW_SANCTIONED_STUDENTS_LIST,
    PermissionCode.VIEW_STUDENT_SANCTION_DETAIL,
    PermissionCode.APPROVE_SANCTION_COMPLIANCE,
    PermissionCode.CONFIGURE_EVENT_SANCTIONS,
    PermissionCode.EXPORT_SANCTIONED_STUDENTS,
    PermissionCode.VIEW_SANCTIONS_DASHBOARD,
}

ORG_PERMISSION_CODES = {
    PermissionCode.MANAGE_STUDENTS,
    PermissionCode.VIEW_STUDENTS,
    PermissionCode.MANAGE_MEMBERS,
    PermissionCode.MANAGE_EVENTS,
    PermissionCode.MANAGE_ATTENDANCE,
    PermissionCode.MANAGE_ANNOUNCEMENTS,
    PermissionCode.ASSIGN_PERMISSIONS,
    PermissionCode.VIEW_SANCTIONED_STUDENTS_LIST,
    PermissionCode.VIEW_STUDENT_SANCTION_DETAIL,
    PermissionCode.APPROVE_SANCTION_COMPLIANCE,
    PermissionCode.CONFIGURE_EVENT_SANCTIONS,
    PermissionCode.EXPORT_SANCTIONED_STUDENTS,
    PermissionCode.VIEW_SANCTIONS_DASHBOARD,
}


@dataclass(slots=True)
class SeedConfig:
    student_count: int = DEFAULT_STUDENT_COUNT
    event_count: int = DEFAULT_EVENT_COUNT
    attendance_target: int = DEFAULT_ATTENDANCE_TARGET
    user_batch_size: int = DEFAULT_USER_BATCH_SIZE
    attendance_batch_size: int = DEFAULT_ATTENDANCE_BATCH_SIZE
    password_hash_rounds: int = DEFAULT_PASSWORD_HASH_ROUNDS
    password_hash_workers: int = 0
    random_seed: int = 20260418
    school_name: str = SEED_SCHOOL_NAME
    school_code: str = SEED_SCHOOL_CODE
    replace_existing: bool = False
    dry_run: bool = False
    credentials_output_path: Path | None = None
    summary_output_path: Path | None = None


@dataclass(slots=True)
class SeedPlan:
    core_attendance_rows: int
    extra_attendance_rows: int
    attendance_rows_per_event: list[int]
    absent_core_rows: int
    sanction_record_rows: int
    sanction_item_rows: int


@dataclass(slots=True)
class StudentSeedSpec:
    ordinal: int
    email: str
    password: str
    first_name: str
    middle_name: str | None
    last_name: str
    student_code: str
    department_id: int
    department_name: str
    program_id: int
    program_name: str
    year_level: int
    user_id: int | None = None
    student_profile_id: int | None = None
    governance_role_name: str | None = None
    governance_unit_code: str | None = None
    governance_position_title: str | None = None

    @property
    def role_names(self) -> list[str]:
        roles = ["student"]
        if self.governance_role_name:
            roles.append(self.governance_role_name)
        return roles


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_output_paths() -> tuple[Path, Path]:
    output_dir = _repo_root() / "storage" / "seed_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    return (
        output_dir / "misamis_university_credentials.csv",
        output_dir / "misamis_university_seed_summary.json",
    )


def _chunked(items: Sequence[object], chunk_size: int) -> list[Sequence[object]]:
    return [items[index : index + chunk_size] for index in range(0, len(items), chunk_size)]


def _resolve_worker_count(config: SeedConfig) -> int:
    if config.password_hash_workers > 0:
        return config.password_hash_workers
    return min(8, os.cpu_count() or 4)


def _hash_passwords(passwords: list[str], *, rounds: int, workers: int) -> list[str]:
    if workers <= 1:
        return [hash_password_bcrypt(password, rounds=rounds) for password in passwords]

    with ThreadPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(lambda value: hash_password_bcrypt(value, rounds=rounds), passwords))


def _is_absent(student_index: int, event_index: int) -> bool:
    return (student_index + event_index) % ABSENCE_MODULUS == 0


def _build_seed_plan(config: SeedConfig) -> SeedPlan:
    if config.student_count < len(DEPARTMENT_PROGRAMS) + sum(len(programs) for _, programs in DEPARTMENT_PROGRAMS) + 1:
        raise ValueError("student_count is too small for the required SSG, SG, and ORG memberships")
    if config.event_count <= 0:
        raise ValueError("event_count must be greater than 0")
    if config.user_batch_size <= 0 or config.attendance_batch_size <= 0:
        raise ValueError("batch sizes must be greater than 0")

    core_attendance_rows = config.student_count * config.event_count
    if config.attendance_target < core_attendance_rows:
        raise ValueError(
            "attendance_target must be at least student_count * event_count "
            f"({core_attendance_rows:,})"
        )

    extra_attendance_rows = config.attendance_target - core_attendance_rows
    attendance_rows_per_event = [
        extra_attendance_rows // config.event_count + (1 if index < (extra_attendance_rows % config.event_count) else 0)
        for index in range(config.event_count)
    ]
    absent_core_rows = sum(
        1
        for event_index in range(config.event_count)
        for student_index in range(config.student_count)
        if _is_absent(student_index, event_index)
    )
    return SeedPlan(
        core_attendance_rows=core_attendance_rows,
        extra_attendance_rows=extra_attendance_rows,
        attendance_rows_per_event=attendance_rows_per_event,
        absent_core_rows=absent_core_rows,
        sanction_record_rows=absent_core_rows,
        sanction_item_rows=absent_core_rows * 2,
    )


def _assert_schema_ready() -> None:
    inspector = inspect(engine)
    missing_tables = sorted(table_name for table_name in REQUIRED_TABLES if not inspector.has_table(table_name))
    if missing_tables:
        raise RuntimeError(
            "Database schema is incomplete. Run migrations before this seed script. "
            f"Missing tables: {', '.join(missing_tables)}"
        )


def _print_plan(config: SeedConfig, plan: SeedPlan) -> None:
    print("Seed plan")
    print(f"- school: {config.school_name} ({config.school_code})")
    print(f"- students: {config.student_count:,}")
    print(f"- events: {config.event_count:,}")
    print(f"- attendance rows: {config.attendance_target:,}")
    print(f"- core attendance rows: {plan.core_attendance_rows:,}")
    print(f"- duplicate attendance rows: {plan.extra_attendance_rows:,}")
    print(f"- sanction records: {plan.sanction_record_rows:,}")
    print(f"- sanction items: {plan.sanction_item_rows:,}")
    print(f"- password hash rounds: {config.password_hash_rounds}")


def _ensure_unique_email(db: Session, email: str) -> None:
    existing_user = db.query(User.id).filter(User.email == email).first()
    if existing_user is not None:
        raise RuntimeError(f"User email already exists: {email}")


def _create_or_replace_school(db: Session, config: SeedConfig) -> School:
    existing_school = (
        db.query(School)
        .filter(
            (School.school_code == config.school_code)
            | (School.school_name == config.school_name)
        )
        .first()
    )
    if existing_school is not None:
        if not config.replace_existing:
            raise RuntimeError(
                f"School '{config.school_name}' already exists. Use --replace-existing to recreate it."
            )
        db.delete(existing_school)
        db.commit()

    school = School(
        name=config.school_name,
        school_name=config.school_name,
        school_code=config.school_code,
        address="H.T. Feliciano Street, Ozamiz City, Misamis Occidental, Philippines",
        primary_color="#143C77",
        secondary_color="#D9A404",
        subscription_status="active",
        active_status=True,
        subscription_plan="enterprise-demo",
        subscription_start=date.today() - timedelta(days=90),
    )
    db.add(school)
    db.flush()
    return school


def _create_campus_admin(
    db: Session,
    school: School,
    *,
    password_hash_rounds: int,
) -> tuple[User, dict[str, str]]:
    admin_email = f"campus.admin@{SEED_EMAIL_DOMAIN}"
    _ensure_unique_email(db, admin_email)

    admin_password = generate_secure_password()
    admin_user = User(
        email=admin_email,
        school_id=school.id,
        first_name="Marian",
        middle_name="Joy",
        last_name="Torres",
        password_hash=hash_password_bcrypt(admin_password, rounds=password_hash_rounds),
        is_active=True,
        must_change_password=False,
        should_prompt_password_change=False,
    )
    db.add(admin_user)
    db.flush()

    db.add(
        SchoolSetting(
            school_id=school.id,
            primary_color=school.primary_color,
            secondary_color=school.secondary_color or "#D9A404",
            accent_color="#F2C94C",
            updated_by_user_id=admin_user.id,
        )
    )
    db.flush()

    return admin_user, {
        "account_type": "campus_admin",
        "email": admin_email,
        "password": admin_password,
        "student_id": "",
        "roles": "campus_admin",
        "first_name": admin_user.first_name or "",
        "last_name": admin_user.last_name or "",
        "department": "",
        "program": "",
        "year_level": "",
        "governance_unit": "",
    }


def _create_departments_and_programs(db: Session, school: School) -> tuple[list[Department], list[Program]]:
    departments: list[Department] = []
    programs: list[Program] = []

    for department_name, program_names in DEPARTMENT_PROGRAMS:
        department = Department(school_id=school.id, name=department_name)
        db.add(department)
        db.flush()
        departments.append(department)

        for program_name in program_names:
            program = Program(school_id=school.id, name=program_name)
            db.add(program)
            db.flush()
            db.execute(
                program_department_association.insert().values(
                    program_id=program.id,
                    department_id=department.id,
                )
            )
            programs.append(program)

    db.flush()
    return departments, programs


def _build_student_specs(
    config: SeedConfig,
    departments: list[Department],
    programs: list[Program],
) -> list[StudentSeedSpec]:
    rng = random.Random(config.random_seed)
    department_by_id = {department.id: department for department in departments}
    program_department_id = {program.id: program.departments[0].id for program in programs}
    shuffled_programs = programs[:]
    rng.shuffle(shuffled_programs)
    student_numbers = rng.sample(range(100000, 999999), config.student_count)

    specs: list[StudentSeedSpec] = []
    for index in range(config.student_count):
        program = shuffled_programs[index % len(shuffled_programs)]
        department = department_by_id[program_department_id[program.id]]
        specs.append(
            StudentSeedSpec(
                ordinal=index,
                email=f"student.{index + 1:05d}@{SEED_EMAIL_DOMAIN}",
                password=generate_secure_password(),
                first_name=rng.choice(FILIPINO_FIRST_NAMES),
                middle_name=rng.choice(FILIPINO_MIDDLE_NAMES) if rng.random() < 0.45 else None,
                last_name=rng.choice(FILIPINO_LAST_NAMES),
                student_code=f"MU{student_numbers[index]}",
                department_id=department.id,
                department_name=department.name,
                program_id=program.id,
                program_name=program.name,
                year_level=(index % 4) + 1,
            )
        )

    return specs


def _insert_student_users(
    db: Session,
    config: SeedConfig,
    school: School,
    student_specs: list[StudentSeedSpec],
) -> None:
    workers = _resolve_worker_count(config)
    for chunk in _chunked(student_specs, config.user_batch_size):
        passwords = [spec.password for spec in chunk]
        password_hashes = _hash_passwords(
            passwords,
            rounds=config.password_hash_rounds,
            workers=workers,
        )
        db.execute(
            insert(User),
            [
                {
                    "email": spec.email,
                    "school_id": school.id,
                    "password_hash": password_hash,
                    "first_name": spec.first_name,
                    "middle_name": spec.middle_name,
                    "last_name": spec.last_name,
                    "is_active": True,
                    "must_change_password": False,
                    "should_prompt_password_change": False,
                    "created_at": datetime.utcnow(),
                }
                for spec, password_hash in zip(chunk, password_hashes)
            ],
        )
        db.commit()


def _assign_user_ids(db: Session, student_specs: list[StudentSeedSpec]) -> None:
    email_to_id: dict[str, int] = {}
    for chunk in _chunked([spec.email for spec in student_specs], 1000):
        rows = db.query(User.id, User.email).filter(User.email.in_(chunk)).all()
        for user_id, email in rows:
            email_to_id[email] = user_id

    missing = [spec.email for spec in student_specs if spec.email not in email_to_id]
    if missing:
        raise RuntimeError(f"Failed to resolve {len(missing)} seeded student users after insert.")

    for spec in student_specs:
        spec.user_id = email_to_id[spec.email]


def _insert_student_roles_and_profiles(
    db: Session,
    school: School,
    student_specs: list[StudentSeedSpec],
    student_role_id: int,
) -> None:
    db.execute(
        insert(UserRole),
        [
            {
                "user_id": spec.user_id,
                "role_id": student_role_id,
            }
            for spec in student_specs
            if spec.user_id is not None
        ],
    )
    db.execute(
        insert(StudentProfile),
        [
            {
                "user_id": spec.user_id,
                "school_id": school.id,
                "student_id": spec.student_code,
                "department_id": spec.department_id,
                "program_id": spec.program_id,
                "year_level": spec.year_level,
                "is_face_registered": False,
                "registration_complete": False,
            }
            for spec in student_specs
            if spec.user_id is not None
        ],
    )
    db.commit()


def _assign_student_profile_ids(db: Session, student_specs: list[StudentSeedSpec]) -> None:
    user_id_to_profile_id: dict[int, int] = {}
    for chunk in _chunked([spec.user_id for spec in student_specs if spec.user_id is not None], 1000):
        rows = db.query(StudentProfile.id, StudentProfile.user_id).filter(StudentProfile.user_id.in_(chunk)).all()
        for profile_id, user_id in rows:
            if user_id is not None:
                user_id_to_profile_id[user_id] = profile_id

    missing = [spec.email for spec in student_specs if spec.user_id not in user_id_to_profile_id]
    if missing:
        raise RuntimeError(f"Failed to resolve {len(missing)} student profile rows after insert.")

    for spec in student_specs:
        if spec.user_id is not None:
            spec.student_profile_id = user_id_to_profile_id[spec.user_id]


def _select_unique_student(
    student_specs: list[StudentSeedSpec],
    *,
    taken_ordinals: set[int],
    department_id: int | None = None,
    program_id: int | None = None,
) -> StudentSeedSpec:
    for spec in student_specs:
        if spec.ordinal in taken_ordinals:
            continue
        if department_id is not None and spec.department_id != department_id:
            continue
        if program_id is not None and spec.program_id != program_id:
            continue
        taken_ordinals.add(spec.ordinal)
        return spec
    raise RuntimeError("Unable to select a unique seeded student for governance membership.")


def _seed_governance_units_and_members(
    db: Session,
    school: School,
    campus_admin: User,
    student_specs: list[StudentSeedSpec],
    departments: list[Department],
    programs: list[Program],
    role_lookup: dict[str, Role],
) -> tuple[GovernanceUnit, dict[int, GovernanceUnit], dict[int, GovernanceUnit], list[dict[str, str]]]:
    permission_lookup = {
        permission.permission_code: permission
        for permission in db.query(GovernancePermission).all()
    }

    ssg_unit = GovernanceUnit(
        unit_code="SSG",
        unit_name="Supreme Students Government",
        description="Campus-wide student governance for Misamis University seed data.",
        unit_type=GovernanceUnitType.SSG,
        school_id=school.id,
        created_by_user_id=campus_admin.id,
        is_active=True,
    )
    db.add(ssg_unit)
    db.flush()

    sg_units_by_department_id: dict[int, GovernanceUnit] = {}
    org_units_by_program_id: dict[int, GovernanceUnit] = {}

    for department in departments:
        sg_unit = GovernanceUnit(
            unit_code=f"SG-{department.id}",
            unit_name=f"{department.name} Student Government",
            description=f"Department-level governance unit for {department.name}.",
            unit_type=GovernanceUnitType.SG,
            parent_unit_id=ssg_unit.id,
            school_id=school.id,
            department_id=department.id,
            created_by_user_id=campus_admin.id,
            is_active=True,
        )
        db.add(sg_unit)
        db.flush()
        sg_units_by_department_id[department.id] = sg_unit

    for program in programs:
        department_id = program.departments[0].id
        org_unit = GovernanceUnit(
            unit_code=f"ORG-{program.id}",
            unit_name=f"{program.name} Organization",
            description=f"Program-level governance unit for {program.name}.",
            unit_type=GovernanceUnitType.ORG,
            parent_unit_id=sg_units_by_department_id[department_id].id,
            school_id=school.id,
            department_id=department_id,
            program_id=program.id,
            created_by_user_id=campus_admin.id,
            is_active=True,
        )
        db.add(org_unit)
        db.flush()
        org_units_by_program_id[program.id] = org_unit

    taken_ordinals: set[int] = set()
    ssg_spec = _select_unique_student(student_specs, taken_ordinals=taken_ordinals)
    ssg_spec.governance_role_name = "ssg"
    ssg_spec.governance_unit_code = ssg_unit.unit_code
    ssg_spec.governance_position_title = "SSG President"

    sg_specs_by_unit_id: dict[int, StudentSeedSpec] = {}
    for department in departments:
        sg_spec = _select_unique_student(
            student_specs,
            taken_ordinals=taken_ordinals,
            department_id=department.id,
        )
        sg_spec.governance_role_name = "sg"
        sg_spec.governance_unit_code = sg_units_by_department_id[department.id].unit_code
        sg_spec.governance_position_title = "SG Chairperson"
        sg_specs_by_unit_id[sg_units_by_department_id[department.id].id] = sg_spec

    org_specs_by_unit_id: dict[int, StudentSeedSpec] = {}
    for program in programs:
        org_spec = _select_unique_student(
            student_specs,
            taken_ordinals=taken_ordinals,
            program_id=program.id,
        )
        org_spec.governance_role_name = "org"
        org_spec.governance_unit_code = org_units_by_program_id[program.id].unit_code
        org_spec.governance_position_title = "ORG President"
        org_specs_by_unit_id[org_units_by_program_id[program.id].id] = org_spec

    db.execute(
        insert(UserRole),
        [
            {
                "user_id": spec.user_id,
                "role_id": role_lookup[spec.governance_role_name].id,
            }
            for spec in student_specs
            if spec.governance_role_name and spec.user_id is not None
        ],
    )

    unit_permission_rows = []

    def register_unit_permissions(unit: GovernanceUnit, permission_codes: set[PermissionCode]) -> None:
        for permission_code in permission_codes:
            unit_permission_rows.append(
                {
                    "governance_unit_id": unit.id,
                    "permission_id": permission_lookup[permission_code].id,
                    "granted_by_user_id": campus_admin.id,
                    "created_at": datetime.utcnow(),
                }
            )

    register_unit_permissions(ssg_unit, SSG_PERMISSION_CODES)
    for sg_unit in sg_units_by_department_id.values():
        register_unit_permissions(sg_unit, SG_PERMISSION_CODES)
    for org_unit in org_units_by_program_id.values():
        register_unit_permissions(org_unit, ORG_PERMISSION_CODES)

    member_records: list[tuple[GovernanceMember, set[PermissionCode], StudentSeedSpec]] = []

    ssg_member = GovernanceMember(
        governance_unit_id=ssg_unit.id,
        user_id=ssg_spec.user_id,
        position_title=ssg_spec.governance_position_title,
        assigned_by_user_id=campus_admin.id,
        is_active=True,
    )
    db.add(ssg_member)
    db.flush()
    member_records.append((ssg_member, SSG_PERMISSION_CODES, ssg_spec))

    for unit_id, sg_spec in sg_specs_by_unit_id.items():
        sg_member = GovernanceMember(
            governance_unit_id=unit_id,
            user_id=sg_spec.user_id,
            position_title=sg_spec.governance_position_title,
            assigned_by_user_id=campus_admin.id,
            is_active=True,
        )
        db.add(sg_member)
        db.flush()
        member_records.append((sg_member, SG_PERMISSION_CODES, sg_spec))

    for unit_id, org_spec in org_specs_by_unit_id.items():
        org_member = GovernanceMember(
            governance_unit_id=unit_id,
            user_id=org_spec.user_id,
            position_title=org_spec.governance_position_title,
            assigned_by_user_id=campus_admin.id,
            is_active=True,
        )
        db.add(org_member)
        db.flush()
        member_records.append((org_member, ORG_PERMISSION_CODES, org_spec))

    db.execute(insert(GovernanceUnitPermission), unit_permission_rows)
    db.execute(
        insert(GovernanceMemberPermission),
        [
            {
                "governance_member_id": member.id,
                "permission_id": permission_lookup[permission_code].id,
                "granted_by_user_id": campus_admin.id,
                "created_at": datetime.utcnow(),
            }
            for member, permission_codes, _spec in member_records
            for permission_code in permission_codes
        ],
    )
    db.commit()

    privileged_rows = [
        {
            "account_type": "student_governance",
            "email": spec.email,
            "password": spec.password,
            "student_id": spec.student_code,
            "roles": "|".join(spec.role_names),
            "first_name": spec.first_name,
            "last_name": spec.last_name,
            "department": spec.department_name,
            "program": spec.program_name,
            "year_level": str(spec.year_level),
            "governance_unit": spec.governance_unit_code or "",
        }
        for spec in student_specs
        if spec.governance_role_name
    ]

    return ssg_unit, sg_units_by_department_id, org_units_by_program_id, privileged_rows


def _create_events_and_configs(
    db: Session,
    config: SeedConfig,
    school: School,
    campus_admin: User,
    sg_units_by_department_id: dict[int, GovernanceUnit],
) -> tuple[list[Event], dict[int, EventSanctionConfig]]:
    start_anchor = datetime.utcnow() - timedelta(days=config.event_count * 7)
    events: list[Event] = []
    for index in range(config.event_count):
        event = Event(
            school_id=school.id,
            name=f"{config.school_name} {EVENT_THEMES[index % len(EVENT_THEMES)]} {index + 1:02d}",
            location=EVENT_LOCATIONS[index % len(EVENT_LOCATIONS)],
            start_datetime=start_anchor + timedelta(days=index * 5),
            end_datetime=start_anchor + timedelta(days=index * 5, hours=3),
            status=EventStatus.COMPLETED,
        )
        db.add(event)
        events.append(event)
    db.flush()

    sanction_configs: dict[int, EventSanctionConfig] = {}
    for event in events:
        sanction_config = EventSanctionConfig(
            school_id=school.id,
            event_id=event.id,
            sanctions_enabled=True,
            item_definitions_json=[
                {
                    "item_code": "reflection-letter",
                    "item_name": "Reflection Letter",
                    "item_description": "Submit a reflection letter explaining the absence.",
                },
                {
                    "item_code": "community-service",
                    "item_name": "Community Service",
                    "item_description": "Complete the assigned community service requirement.",
                },
            ],
            created_by_user_id=campus_admin.id,
            updated_by_user_id=campus_admin.id,
        )
        db.add(sanction_config)
        db.flush()
        sanction_configs[event.id] = sanction_config

    delegation_rows = []
    for event in events[: min(10, len(events))]:
        for department_id, sg_unit in sg_units_by_department_id.items():
            delegation_rows.append(
                {
                    "school_id": school.id,
                    "event_id": event.id,
                    "sanction_config_id": sanction_configs[event.id].id,
                    "delegated_by_user_id": campus_admin.id,
                    "delegated_to_governance_unit_id": sg_unit.id,
                    "scope_type": SanctionDelegationScopeType.DEPARTMENT,
                    "scope_json": {"department_ids": [department_id]},
                    "is_active": True,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            )
    if delegation_rows:
        db.execute(insert(SanctionDelegation), delegation_rows)
    db.commit()
    return events, sanction_configs


def _build_attendance_payload(
    *,
    student_profile_id: int,
    event: Event,
    status_value: str,
    duplicate_rank: int,
    core_row: bool,
    verified_by_user_id: int,
) -> dict[str, object]:
    status_is_absent = status_value == "absent"
    shift_minutes = 0 if core_row else duplicate_rank * 4
    time_in = event.start_datetime + timedelta(minutes=0 if status_is_absent else 12 + shift_minutes)
    time_out = event.end_datetime if status_is_absent else event.end_datetime - timedelta(minutes=shift_minutes)

    return {
        "student_id": student_profile_id,
        "event_id": event.id,
        "time_in": time_in,
        "time_out": time_out,
        "method": "manual",
        "status": status_value,
        "check_in_status": None if status_is_absent else "present",
        "check_out_status": "absent" if status_is_absent else "present",
        "verified_by": verified_by_user_id,
        "notes": (
            "Seeded absent attendance with sanction coverage."
            if status_is_absent
            else "Seeded present attendance."
        ),
    }


def _build_attendance_batches(
    *,
    event_index: int,
    event: Event,
    student_specs: list[StudentSeedSpec],
    extra_row_count: int,
    verified_by_user_id: int,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[StudentSeedSpec]]:
    extra_rows: list[dict[str, object]] = []
    core_rows: list[dict[str, object]] = []
    absent_specs: list[StudentSeedSpec] = []
    student_count = len(student_specs)
    rotation_offset = (event_index * 997) % student_count

    for extra_index in range(extra_row_count):
        student_index = (rotation_offset + extra_index) % student_count
        duplicate_rank = (extra_index // student_count) + 1
        spec = student_specs[student_index]
        status_value = "absent" if _is_absent(student_index, event_index) else "present"
        extra_rows.append(
            _build_attendance_payload(
                student_profile_id=spec.student_profile_id or 0,
                event=event,
                status_value=status_value,
                duplicate_rank=duplicate_rank,
                core_row=False,
                verified_by_user_id=verified_by_user_id,
            )
        )

    for student_index, spec in enumerate(student_specs):
        status_value = "absent" if _is_absent(student_index, event_index) else "present"
        if status_value == "absent":
            absent_specs.append(spec)
        core_rows.append(
            _build_attendance_payload(
                student_profile_id=spec.student_profile_id or 0,
                event=event,
                status_value=status_value,
                duplicate_rank=0,
                core_row=True,
                verified_by_user_id=verified_by_user_id,
            )
        )

    return extra_rows, core_rows, absent_specs


def _insert_attendance_rows(db: Session, rows: list[dict[str, object]], batch_size: int) -> None:
    for chunk in _chunked(rows, batch_size):
        db.execute(insert(Attendance), list(chunk))


def _seed_attendance_and_sanctions(
    db: Session,
    config: SeedConfig,
    plan: SeedPlan,
    events: list[Event],
    sanction_configs: dict[int, EventSanctionConfig],
    student_specs: list[StudentSeedSpec],
    campus_admin: User,
    sg_units_by_department_id: dict[int, GovernanceUnit],
) -> None:
    for event_index, event in enumerate(events):
        extra_rows, core_rows, absent_specs = _build_attendance_batches(
            event_index=event_index,
            event=event,
            student_specs=student_specs,
            extra_row_count=plan.attendance_rows_per_event[event_index],
            verified_by_user_id=campus_admin.id,
        )
        _insert_attendance_rows(db, extra_rows, config.attendance_batch_size)
        _insert_attendance_rows(db, core_rows, config.attendance_batch_size)
        db.commit()

        absent_profile_ids = [spec.student_profile_id for spec in absent_specs if spec.student_profile_id is not None]
        latest_absent_rows = (
            db.query(Attendance.id, Attendance.student_id)
            .filter(
                Attendance.event_id == event.id,
                Attendance.student_id.in_(absent_profile_ids),
                Attendance.status == "absent",
            )
            .order_by(
                Attendance.student_id.asc(),
                Attendance.time_in.desc(),
                Attendance.id.desc(),
            )
            .all()
        )

        attendance_id_by_student_profile_id: dict[int, int] = {}
        for attendance_id, student_profile_id in latest_absent_rows:
            if student_profile_id is None or student_profile_id in attendance_id_by_student_profile_id:
                continue
            attendance_id_by_student_profile_id[student_profile_id] = attendance_id

        sanction_records: list[tuple[SanctionRecord, bool]] = []
        for spec in absent_specs:
            if spec.student_profile_id is None:
                continue
            attendance_id = attendance_id_by_student_profile_id.get(spec.student_profile_id)
            if attendance_id is None:
                raise RuntimeError(
                    f"Unable to resolve latest absent attendance for student profile {spec.student_profile_id} on event {event.id}."
                )
            complied = ((spec.ordinal + event_index) % 5) == 0
            sanction_record = SanctionRecord(
                school_id=event.school_id,
                event_id=event.id,
                sanction_config_id=sanction_configs[event.id].id,
                student_profile_id=spec.student_profile_id,
                attendance_id=attendance_id,
                delegated_governance_unit_id=sg_units_by_department_id[spec.department_id].id,
                status=SanctionComplianceStatus.COMPLIED if complied else SanctionComplianceStatus.PENDING,
                assigned_by_user_id=campus_admin.id,
                complied_at=(event.end_datetime + timedelta(days=10)) if complied else None,
                notes="Seeded sanction generated from an absent attendance row.",
            )
            db.add(sanction_record)
            sanction_records.append((sanction_record, complied))

        db.flush()

        for sanction_record, complied in sanction_records:
            db.add_all(
                [
                    SanctionItem(
                        sanction_record_id=sanction_record.id,
                        item_code="reflection-letter",
                        item_name="Reflection Letter",
                        item_description="Seeded follow-up requirement.",
                        status=SanctionItemStatus.COMPLIED if complied else SanctionItemStatus.PENDING,
                        complied_at=sanction_record.complied_at if complied else None,
                    ),
                    SanctionItem(
                        sanction_record_id=sanction_record.id,
                        item_code="community-service",
                        item_name="Community Service",
                        item_description="Seeded sanctions task.",
                        status=SanctionItemStatus.COMPLIED,
                        complied_at=sanction_record.complied_at or (event.end_datetime + timedelta(days=5)),
                    ),
                ]
            )

        db.commit()
        print(
            f"Seeded event {event_index + 1}/{len(events)}: "
            f"{len(extra_rows) + len(core_rows):,} attendance rows, "
            f"{len(absent_specs):,} sanctions"
        )


def _write_credentials_manifest(
    config: SeedConfig,
    campus_admin_row: dict[str, str],
    student_specs: list[StudentSeedSpec],
    privileged_rows: list[dict[str, str]],
) -> None:
    if config.credentials_output_path is None:
        return

    rows = [campus_admin_row]
    rows.extend(
        {
            "account_type": "student",
            "email": spec.email,
            "password": spec.password,
            "student_id": spec.student_code,
            "roles": "|".join(spec.role_names),
            "first_name": spec.first_name,
            "last_name": spec.last_name,
            "department": spec.department_name,
            "program": spec.program_name,
            "year_level": str(spec.year_level),
            "governance_unit": spec.governance_unit_code or "",
        }
        for spec in student_specs
    )

    fieldnames = [
        "account_type",
        "email",
        "password",
        "student_id",
        "roles",
        "first_name",
        "last_name",
        "department",
        "program",
        "year_level",
        "governance_unit",
    ]
    with config.credentials_output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    privileged_path = config.credentials_output_path.with_name("misamis_university_privileged_credentials.csv")
    with privileged_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(campus_admin_row)
        writer.writerows(privileged_rows)


def _write_summary(
    config: SeedConfig,
    plan: SeedPlan,
    school: School,
    campus_admin_row: dict[str, str],
    student_specs: list[StudentSeedSpec],
) -> None:
    if config.summary_output_path is None:
        return

    governance_counts = {"ssg": 0, "sg": 0, "org": 0}
    for spec in student_specs:
        if spec.governance_role_name:
            governance_counts[spec.governance_role_name] += 1

    payload = {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds"),
        "school": {
            "id": school.id,
            "name": school.school_name,
            "code": school.school_code,
        },
        "counts": {
            "students": len(student_specs),
            "events": len(plan.attendance_rows_per_event),
            "attendance_rows": config.attendance_target,
            "core_attendance_rows": plan.core_attendance_rows,
            "duplicate_attendance_rows": plan.extra_attendance_rows,
            "sanction_records": plan.sanction_record_rows,
            "sanction_items": plan.sanction_item_rows,
            "governance_members": governance_counts,
        },
        "campus_admin": campus_admin_row,
        "artifacts": {
            "credentials_csv": str(config.credentials_output_path) if config.credentials_output_path else None,
            "summary_json": str(config.summary_output_path) if config.summary_output_path else None,
        },
        "notes": [
            "The 1,000,000 attendance target is implemented as total attendance rows across all seeded students.",
            "Each student still receives one core attendance row per event; additional duplicate history rows are added to reach the requested total volume.",
            "Sanctions are created for every core absent attendance row.",
        ],
    }
    config.summary_output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run_misamis_university_seed(config: SeedConfig) -> None:
    plan = _build_seed_plan(config)
    _print_plan(config, plan)
    if config.dry_run:
        return

    _assert_schema_ready()
    db = SessionLocal()

    try:
        seed_roles(db)
        ensure_permission_catalog(db)
        db.commit()

        school = _create_or_replace_school(db, config)
        campus_admin, campus_admin_row = _create_campus_admin(
            db,
            school,
            password_hash_rounds=config.password_hash_rounds,
        )
        campus_admin_role = db.query(Role).filter(Role.name == "campus_admin").one()
        db.add(UserRole(user_id=campus_admin.id, role_id=campus_admin_role.id))

        departments, programs = _create_departments_and_programs(db, school)
        db.commit()

        departments = db.query(Department).filter(Department.school_id == school.id).order_by(Department.id.asc()).all()
        programs = db.query(Program).filter(Program.school_id == school.id).order_by(Program.id.asc()).all()
        for program in programs:
            program.departments  # noqa: B018

        role_lookup = {
            role.name: role
            for role in db.query(Role).filter(Role.name.in_(["student", "ssg", "sg", "org"])).all()
        }

        student_specs = _build_student_specs(config, departments, programs)
        print(f"Creating {len(student_specs):,} student users...")
        _insert_student_users(db, config, school, student_specs)
        _assign_user_ids(db, student_specs)
        _insert_student_roles_and_profiles(db, school, student_specs, role_lookup["student"].id)
        _assign_student_profile_ids(db, student_specs)

        ssg_unit, sg_units_by_department_id, org_units_by_program_id, privileged_rows = _seed_governance_units_and_members(
            db,
            school,
            campus_admin,
            student_specs,
            departments,
            programs,
            role_lookup,
        )
        print(
            "Governance units created: "
            f"1 SSG, {len(sg_units_by_department_id)} SG, {len(org_units_by_program_id)} ORG"
        )

        events, sanction_configs = _create_events_and_configs(
            db,
            config,
            school,
            campus_admin,
            sg_units_by_department_id,
        )
        print(f"Created {len(events):,} completed events with sanction configs")

        _seed_attendance_and_sanctions(
            db,
            config,
            plan,
            events,
            sanction_configs,
            student_specs,
            campus_admin,
            sg_units_by_department_id,
        )

        _write_credentials_manifest(config, campus_admin_row, student_specs, privileged_rows)
        _write_summary(config, plan, school, campus_admin_row, student_specs)

        print("Large seed completed successfully")
        print(f"- school id: {school.id}")
        print(f"- campus admin email: {campus_admin_row['email']}")
        print(f"- campus admin password: {campus_admin_row['password']}")
        print(f"- credentials file: {config.credentials_output_path}")
        print(f"- summary file: {config.summary_output_path}")
        print(f"- SSG unit code: {ssg_unit.unit_code}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Seed one Misamis University school with 15,000 students, 33 events, and 1,000,000 attendance rows.",
    )
    parser.add_argument("--student-count", type=int, default=DEFAULT_STUDENT_COUNT)
    parser.add_argument("--event-count", type=int, default=DEFAULT_EVENT_COUNT)
    parser.add_argument("--attendance-target", type=int, default=DEFAULT_ATTENDANCE_TARGET)
    parser.add_argument("--user-batch-size", type=int, default=DEFAULT_USER_BATCH_SIZE)
    parser.add_argument("--attendance-batch-size", type=int, default=DEFAULT_ATTENDANCE_BATCH_SIZE)
    parser.add_argument("--password-hash-rounds", type=int, default=DEFAULT_PASSWORD_HASH_ROUNDS)
    parser.add_argument("--password-hash-workers", type=int, default=0)
    parser.add_argument("--random-seed", type=int, default=20260418)
    parser.add_argument("--school-code", default=SEED_SCHOOL_CODE)
    parser.add_argument("--replace-existing", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--credentials-output", type=Path, default=None)
    parser.add_argument("--summary-output", type=Path, default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_cli_parser()
    args = parser.parse_args(argv)
    default_credentials_output, default_summary_output = _default_output_paths()
    config = SeedConfig(
        student_count=args.student_count,
        event_count=args.event_count,
        attendance_target=args.attendance_target,
        user_batch_size=args.user_batch_size,
        attendance_batch_size=args.attendance_batch_size,
        password_hash_rounds=args.password_hash_rounds,
        password_hash_workers=args.password_hash_workers,
        random_seed=args.random_seed,
        school_code=args.school_code,
        replace_existing=args.replace_existing,
        dry_run=args.dry_run,
        credentials_output_path=(args.credentials_output or default_credentials_output),
        summary_output_path=(args.summary_output or default_summary_output),
    )
    run_misamis_university_seed(config)
    return 0


__all__ = ["SeedConfig", "main", "run_misamis_university_seed"]
