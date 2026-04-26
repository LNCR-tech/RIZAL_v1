"""Seed the production database with 10,000 demo students across 5 schools.

Usage (inside the backend container):
    python seed_demo.py

Or via docker compose:
    docker compose --profile seed -f docker-compose.prod.yml run --rm seed
"""

from __future__ import annotations

import math
import os
import random
import struct
import sys
import time
from datetime import date, datetime, timedelta, timezone

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Ensure app modules are importable
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import SessionLocal, engine  # noqa: E402
from app.models.base import Base  # noqa: E402
from app.models.school import School, SchoolSetting  # noqa: E402
from app.models.user import User, UserRole, StudentProfile  # noqa: E402
from app.models.role import Role  # noqa: E402
from app.models.department import Department  # noqa: E402
from app.models.program import Program  # noqa: E402
from app.models.event import Event, EventStatus  # noqa: E402
from app.models.event_type import EventType  # noqa: E402
from app.models.governance_hierarchy import (  # noqa: E402
    GovernanceUnit,
    GovernanceUnitType,
)
from app.models.associations import program_department_association  # noqa: E402
from app.utils.passwords import hash_password_bcrypt  # noqa: E402

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
STUDENTS_PER_SCHOOL = 2000
DEFAULT_PASSWORD = hash_password_bcrypt("Student@123")
ADMIN_PASSWORD = hash_password_bcrypt("Admin@123")
EMBEDDING_DIM = 512
EMBEDDING_DTYPE = "float32"
EMBEDDING_PROVIDER = "seed-demo"


def _generate_face_embedding() -> bytes:
    """Generate a random normalized 512-d float32 embedding (2048 bytes)."""
    raw = [random.gauss(0, 1) for _ in range(EMBEDDING_DIM)]
    norm = math.sqrt(sum(x * x for x in raw))
    normalized = [x / norm for x in raw]
    return struct.pack(f"{EMBEDDING_DIM}f", *normalized)

SCHOOLS = [
    {
        "name": "JRMSU",
        "school_name": "Jose Rizal Memorial State University",
        "school_code": "JRMSU",
        "address": "Gov. Guading Adasa St, Dapitan City, Zamboanga del Norte",
        "primary_color": "#162F65",
        "departments": [
            {
                "name": "College of Engineering and Information Technology",
                "programs": [
                    "Bachelor of Science in Information Technology",
                    "Bachelor of Science in Computer Science",
                    "Bachelor of Science in Electrical Engineering",
                ],
            },
            {
                "name": "College of Arts and Sciences",
                "programs": [
                    "Bachelor of Science in Biology",
                    "Bachelor of Arts in English",
                ],
            },
            {
                "name": "College of Education",
                "programs": [
                    "Bachelor of Secondary Education",
                    "Bachelor of Elementary Education",
                ],
            },
            {
                "name": "College of Engineering",
                "programs": [
                    "Bachelor of Science in Civil Engineering",
                ],
            },
        ],
    },
    {
        "name": "ZPPSU",
        "school_name": "Zamboanga Peninsula Polytechnic State University",
        "school_code": "ZPPSU",
        "address": "R.T. Lim Blvd, Zamboanga City",
        "primary_color": "#0D6E37",
        "departments": [
            {
                "name": "College of Engineering and Information Technology",
                "programs": [
                    "Bachelor of Science in Information Technology",
                    "Bachelor of Science in Industrial Technology",
                ],
            },
            {
                "name": "College of Business Administration",
                "programs": [
                    "Bachelor of Science in Business Administration",
                    "Bachelor of Science in Accountancy",
                ],
            },
            {
                "name": "College of Arts and Sciences",
                "programs": [
                    "Bachelor of Science in Criminology",
                    "Bachelor of Science in Psychology",
                ],
            },
        ],
    },
    {
        "name": "WMSU",
        "school_name": "Western Mindanao State University",
        "school_code": "WMSU",
        "address": "Normal Road, Baliwasan, Zamboanga City",
        "primary_color": "#8B0000",
        "departments": [
            {
                "name": "College of Computing Studies",
                "programs": [
                    "Bachelor of Science in Computer Science",
                    "Bachelor of Science in Information Systems",
                ],
            },
            {
                "name": "College of Education",
                "programs": [
                    "Bachelor of Secondary Education",
                    "Bachelor of Elementary Education",
                ],
            },
            {
                "name": "College of Engineering",
                "programs": [
                    "Bachelor of Science in Civil Engineering",
                    "Bachelor of Science in Electrical Engineering",
                ],
            },
        ],
    },
    {
        "name": "ADZU",
        "school_name": "Ateneo de Zamboanga University",
        "school_code": "ADZU",
        "address": "La Purisima St, Zamboanga City",
        "primary_color": "#003399",
        "departments": [
            {
                "name": "College of Information and Computing Sciences",
                "programs": [
                    "Bachelor of Science in Information Technology",
                    "Bachelor of Science in Computer Science",
                ],
            },
            {
                "name": "College of Arts and Sciences",
                "programs": [
                    "Bachelor of Science in Psychology",
                    "Bachelor of Arts in Communication",
                ],
            },
            {
                "name": "College of Education",
                "programs": [
                    "Bachelor of Elementary Education",
                    "Bachelor of Secondary Education",
                ],
            },
        ],
    },
    {
        "name": "UZ",
        "school_name": "Universidad de Zamboanga",
        "school_code": "UZ",
        "address": "Main Campus, Tetuan, Zamboanga City",
        "primary_color": "#006400",
        "departments": [
            {
                "name": "College of Criminal Justice Education",
                "programs": [
                    "Bachelor of Science in Criminology",
                ],
            },
            {
                "name": "College of Business Administration",
                "programs": [
                    "Bachelor of Science in Business Administration",
                    "Bachelor of Science in Hospitality Management",
                ],
            },
            {
                "name": "College of Arts and Sciences",
                "programs": [
                    "Bachelor of Science in Nursing",
                    "Bachelor of Science in Psychology",
                ],
            },
        ],
    },
]

FIRST_NAMES = [
    "Juan", "Maria", "Jose", "Ana", "Pedro", "Rosa", "Carlos", "Luz",
    "Miguel", "Carmen", "Rafael", "Elena", "Antonio", "Teresa", "Francisco",
    "Isabel", "Manuel", "Gloria", "Ricardo", "Patricia", "Fernando", "Diana",
    "Roberto", "Sofia", "Eduardo", "Angela", "Andres", "Beatriz", "Gabriel",
    "Cristina", "Santiago", "Monica", "Diego", "Lucia", "Arturo", "Daniela",
    "Emilio", "Valeria", "Oscar", "Nicole", "Marco", "Jasmine", "Leo",
    "Bianca", "Ryan", "Grace", "Kenneth", "Joy", "Mark", "Faith",
    "John", "Mary", "James", "Rose", "Paul", "Lyn", "Christian", "Mae",
    "Patrick", "Anne", "Jerome", "Kris", "Kevin", "Jessa", "Kyle", "Kim",
    "Joshua", "Sarah", "Daniel", "Hazel", "Alex", "Claire", "Bryan", "Ella",
    "Jayson", "April", "Renz", "Mika", "Carlo", "Pia", "Lance", "Jade",
    "Troy", "Alyssa", "Ivan", "Trish", "Neil", "Vina", "Sean", "Zara",
    "Nico", "Bea", "Jude", "Lara", "Ruel", "Faye", "Vince", "Gem",
]

LAST_NAMES = [
    "Santos", "Reyes", "Cruz", "Dela Cruz", "Ramos", "Mendoza", "Torres",
    "Gonzales", "Garcia", "Lopez", "Hernandez", "Martinez", "Rodriguez",
    "Flores", "Rivera", "Aquino", "Villanueva", "Castro", "Bautista",
    "Alvarez", "Perez", "Fernandez", "Navarro", "Santiago", "Manalo",
    "Tolentino", "Salazar", "Diaz", "Ocampo", "Pascual", "Soriano",
    "Aguilar", "Castillo", "De Leon", "Miranda", "Morales", "Medina",
    "Romero", "Vargas", "Jimenez", "Guerrero", "Fuentes", "Espinosa",
    "Marquez", "Rosales", "Gutierrez", "Padilla", "Mercado", "Lim", "Tan",
]

SECTIONS = ["A", "B", "C", "D", "E"]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_roles(session) -> dict[str, int]:
    """Return {role_name: role_id}, creating any missing roles."""
    existing = {r.name: r.id for r in session.query(Role).all()}
    for name in ("admin", "campus_admin", "student"):
        if name not in existing:
            role = Role(name=name)
            session.add(role)
            session.flush()
            existing[name] = role.id
    return existing


def _create_school(session, spec: dict) -> School:
    """Create a school with settings if it doesn't exist."""
    existing = session.query(School).filter_by(school_code=spec["school_code"]).first()
    if existing:
        print(f"  School '{spec['school_code']}' already exists (id={existing.id}), skipping.")
        return existing

    school = School(
        name=spec["name"],
        school_name=spec["school_name"],
        school_code=spec["school_code"],
        address=spec["address"],
        primary_color=spec["primary_color"],
        subscription_status="active",
        subscription_plan="premium",
        subscription_start=date.today(),
    )
    session.add(school)
    session.flush()

    settings = SchoolSetting(school_id=school.id)
    session.add(settings)
    session.flush()

    print(f"  Created school '{spec['school_code']}' (id={school.id})")
    return school


def _create_departments_programs(session, school: School, spec: dict):
    """Create departments and programs, return list of (dept_id, program_id) tuples."""
    dept_program_pairs = []

    for dept_spec in spec["departments"]:
        dept = (
            session.query(Department)
            .filter_by(school_id=school.id, name=dept_spec["name"])
            .first()
        )
        if not dept:
            dept = Department(school_id=school.id, name=dept_spec["name"])
            session.add(dept)
            session.flush()

        for prog_name in dept_spec["programs"]:
            prog = (
                session.query(Program)
                .filter_by(school_id=school.id, name=prog_name)
                .first()
            )
            if not prog:
                prog = Program(school_id=school.id, name=prog_name)
                session.add(prog)
                session.flush()
                # Link program <-> department
                session.execute(
                    program_department_association.insert().values(
                        program_id=prog.id, department_id=dept.id
                    )
                )
            dept_program_pairs.append((dept.id, prog.id))

    session.flush()
    print(f"    {len(dept_program_pairs)} department-program pairs ready")
    return dept_program_pairs


def _create_event_types(session, school: School) -> dict[str, int]:
    """Create standard event types for a school. Return {code: id}."""
    result = {}
    defs = [
        ("Assembly", "assembly"),
        ("Meeting", "meeting"),
        ("Orientation", "orientation"),
    ]
    for name, code in defs:
        existing = (
            session.query(EventType)
            .filter_by(school_id=school.id, name=name)
            .first()
        )
        if not existing:
            et = EventType(school_id=school.id, name=name, code=code)
            session.add(et)
            session.flush()
            result[code] = et.id
        else:
            result[code] = existing.id
    return result


def _create_admin(session, school: School, roles: dict[str, int]) -> User:
    """Create a campus admin for the school."""
    email = f"admin@{school.school_code.lower()}.edu"
    existing = session.query(User).filter_by(email=email).first()
    if existing:
        return existing

    admin = User(
        email=email,
        school_id=school.id,
        password_hash=ADMIN_PASSWORD,
        first_name="Campus",
        last_name=f"Admin ({school.school_code})",
        is_active=True,
        must_change_password=False,
    )
    session.add(admin)
    session.flush()
    session.add(UserRole(user_id=admin.id, role_id=roles["campus_admin"]))
    session.flush()
    print(f"    Created admin: {email}")
    return admin


def _create_students_batch(
    session,
    school: School,
    dept_program_pairs: list[tuple[int, int]],
    roles: dict[str, int],
    count: int,
) -> list[int]:
    """Batch-create students. Returns list of user IDs."""
    # Check how many students already exist for this school
    existing_count = (
        session.query(StudentProfile)
        .filter_by(school_id=school.id)
        .count()
    )
    if existing_count >= count:
        print(f"    {existing_count} students already exist, skipping.")
        return []

    remaining = count - existing_count
    print(f"    Creating {remaining} students (batch insert)...")

    student_role_id = roles["student"]
    user_ids = []
    batch_size = 500

    for batch_start in range(0, remaining, batch_size):
        batch_end = min(batch_start + batch_size, remaining)
        idx_start = existing_count + batch_start

        for i in range(batch_start, batch_end):
            idx = existing_count + i + 1
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            email = f"student{idx:05d}@{school.school_code.lower()}.edu"
            student_id_str = f"{school.school_code}-{idx:05d}"
            dept_id, prog_id = random.choice(dept_program_pairs)
            year = random.randint(1, 4)
            section = random.choice(SECTIONS)

            user = User(
                email=email,
                school_id=school.id,
                password_hash=DEFAULT_PASSWORD,
                first_name=first,
                middle_name=None,
                last_name=last,
                is_active=True,
                must_change_password=True,
            )
            session.add(user)
            session.flush()

            session.add(UserRole(user_id=user.id, role_id=student_role_id))

            embedding = _generate_face_embedding()
            profile = StudentProfile(
                user_id=user.id,
                school_id=school.id,
                student_id=student_id_str,
                department_id=dept_id,
                program_id=prog_id,
                year_level=year,
                section=section,
                face_encoding=embedding,
                embedding_provider=EMBEDDING_PROVIDER,
                embedding_dtype=EMBEDDING_DTYPE,
                embedding_dimension=EMBEDDING_DIM,
                embedding_normalized=True,
                is_face_registered=True,
            )
            session.add(profile)
            user_ids.append(user.id)

        session.flush()
        done = min(batch_end, remaining)
        print(f"      ... {done}/{remaining}")

    session.commit()
    print(f"    ✓ {remaining} students created")
    return user_ids


def _create_governance(session, school: School, admin: User) -> list[GovernanceUnit]:
    """Create SSG → SG → ORG governance hierarchy."""
    existing = (
        session.query(GovernanceUnit)
        .filter_by(school_id=school.id)
        .count()
    )
    if existing >= 3:
        units = session.query(GovernanceUnit).filter_by(school_id=school.id).all()
        print(f"    Governance units already exist ({existing}), skipping.")
        return units

    ssg = GovernanceUnit(
        unit_code=f"{school.school_code}-SSG",
        unit_name=f"{school.school_code} Supreme Student Government",
        unit_type=GovernanceUnitType.SSG,
        school_id=school.id,
        created_by_user_id=admin.id,
    )
    session.add(ssg)
    session.flush()

    sg = GovernanceUnit(
        unit_code=f"{school.school_code}-SG",
        unit_name=f"{school.school_code} Student Government",
        unit_type=GovernanceUnitType.SG,
        parent_unit_id=ssg.id,
        school_id=school.id,
        created_by_user_id=admin.id,
    )
    session.add(sg)
    session.flush()

    org = GovernanceUnit(
        unit_code=f"{school.school_code}-ORG",
        unit_name=f"{school.school_code} Student Organization",
        unit_type=GovernanceUnitType.ORG,
        parent_unit_id=sg.id,
        school_id=school.id,
        created_by_user_id=admin.id,
    )
    session.add(org)
    session.flush()

    print(f"    Created governance: SSG → SG → ORG")
    return [ssg, sg, org]


def _create_events(
    session,
    school: School,
    admin: User,
    governance_units: list[GovernanceUnit],
    event_types: dict[str, int],
):
    """Create 1 event per governance unit (3 total)."""
    existing = session.query(Event).filter_by(school_id=school.id).count()
    if existing >= 3:
        print(f"    Events already exist ({existing}), skipping.")
        return

    event_configs = [
        {
            "name": f"{school.school_code} General Assembly",
            "location": f"{school.school_name} Gymnasium",
            "type_code": "assembly",
            "unit": governance_units[0],  # SSG
            "days_offset": 7,
        },
        {
            "name": f"{school.school_code} Department Meeting",
            "location": f"{school.school_name} Conference Hall",
            "type_code": "meeting",
            "unit": governance_units[1],  # SG
            "days_offset": 14,
        },
        {
            "name": f"{school.school_code} Club Orientation",
            "location": f"{school.school_name} AVR",
            "type_code": "orientation",
            "unit": governance_units[2],  # ORG
            "days_offset": 21,
        },
    ]

    for cfg in event_configs:
        start = _now() + timedelta(days=cfg["days_offset"], hours=8)
        end = start + timedelta(hours=3)
        event = Event(
            school_id=school.id,
            created_by_user_id=admin.id,
            name=cfg["name"],
            location=cfg["location"],
            start_datetime=start,
            end_datetime=end,
            status=EventStatus.UPCOMING,
            event_type_id=event_types.get(cfg["type_code"]),
        )
        session.add(event)

    session.flush()
    print(f"    Created 3 events (Assembly, Meeting, Orientation)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("Aura Demo Seeder — 10K Students, 5 Schools")
    print("=" * 60)
    t0 = time.time()

    session = SessionLocal()
    try:
        roles = _ensure_roles(session)
        session.commit()
        print(f"Roles ready: {list(roles.keys())}")

        total_students = 0
        for i, spec in enumerate(SCHOOLS, 1):
            print(f"\n[{i}/5] Processing {spec['school_code']}...")
            school = _create_school(session, spec)
            session.commit()

            dept_prog = _create_departments_programs(session, school, spec)
            session.commit()

            event_types = _create_event_types(session, school)
            session.commit()

            admin = _create_admin(session, school, roles)
            session.commit()

            user_ids = _create_students_batch(
                session, school, dept_prog, roles, STUDENTS_PER_SCHOOL
            )
            total_students += len(user_ids)

            gov_units = _create_governance(session, school, admin)
            session.commit()

            _create_events(session, school, admin, gov_units, event_types)
            session.commit()

        elapsed = time.time() - t0
        print(f"\n{'=' * 60}")
        print(f"✓ Done in {elapsed:.1f}s")
        print(f"  Schools:    5")
        print(f"  Students:   {total_students}")
        print(f"  Events:     15 (3 per school)")
        print(f"  Governance: 15 units (SSG + SG + ORG per school)")
        print(f"{'=' * 60}")

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
