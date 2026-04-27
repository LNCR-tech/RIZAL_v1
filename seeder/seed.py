import sys
import os
import logging
import random
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load .env from seeder/ directory
load_dotenv(Path(__file__).resolve().parent / ".env")

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("Seeder")

# Inject backend path so app.* modules resolve correctly
repo_root = Path(__file__).resolve().parent.parent
backend_path = repo_root / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from app.core.database import SessionLocal  # type: ignore
from modules.core import wipe_records, seed_roles, seed_permission_catalog, seed_platform_admin, seed_attendance_methods, seed_attendance_statuses, seed_event_types
from modules.demo import run_demo
from config import load_config

cfg = load_config()

def _ensure_backend_schema_up_to_date() -> None:
    """
    Ensure the database schema matches the backend models by running Alembic migrations.

    The demo seeder truncates and reuses existing tables. If the DB was created from an
    older revision, missing columns can cause runtime API failures (for example, events
    not loading for students). Running `alembic upgrade head` here keeps the seeder
    self-healing for typical local/dev workflows.
    """
    try:
        from alembic import command
        from alembic.config import Config
        from alembic.runtime.migration import MigrationContext
        from alembic.script import ScriptDirectory
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "Alembic is required to run the demo seeder. "
            "Install backend dependencies (pip install -r backend/requirements.txt)."
        ) from exc

    from app.core.database import engine  # imported after sys.path injection

    backend_dir = repo_root / "backend"
    alembic_ini = backend_dir / "alembic.ini"
    if not alembic_ini.exists():
        raise RuntimeError(f"Missing Alembic config: {alembic_ini}")

    alembic_cfg = Config(str(alembic_ini))
    # Make script_location absolute so it works when running from `seeder/`.
    alembic_cfg.set_main_option("script_location", str(backend_dir / "alembic"))

    script = ScriptDirectory.from_config(alembic_cfg)
    head_revision = script.get_current_head()
    with engine.connect() as conn:
        current_revision = MigrationContext.configure(conn).get_current_revision()

    if head_revision and current_revision != head_revision:
        logger.info(f"Upgrading DB schema via Alembic: {current_revision} -> {head_revision}")
        command.upgrade(alembic_cfg, "head")


def main():
    seed_database = os.environ.get("SEED_DATABASE", "false").strip().lower() == "true"
    seed_wipe = os.environ.get("SEED_WIPE_EXISTING", "true").strip().lower() != "false"
    seed_confirm = os.environ.get("SEED_CONFIRM", "").strip().lower()

    if not seed_database:
        logger.info("Database seeding is disabled (SEED_DATABASE not set to true in .env). Skipping...")
        return

    if seed_confirm != "yes":
        logger.error("")
        logger.error("==========================================================")
        logger.error("  WARNING: SEED_DATABASE=true but SEED_CONFIRM is not set.")
        logger.error("  This will WIPE ALL EXISTING DATA and replace it with")
        logger.error("  generated demo data. This action cannot be undone.")
        logger.error("  Set SEED_CONFIRM=yes in your .env to proceed.")
        logger.error("==========================================================")
        logger.error("")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Aura Database Seeder")
    subparsers = parser.add_subparsers(dest="command", help="Seeder commands")

    demo_p = subparsers.add_parser("demo", help="Generate stochastic dummy schools and records")
    demo_p.add_argument("--schools", type=int, default=cfg.SEED_N_SCHOOLS)
    demo_p.add_argument("--min-colleges", type=int, default=cfg.SEED_MIN_COLLEGES)
    demo_p.add_argument("--max-colleges", type=int, default=cfg.SEED_MAX_COLLEGES)
    demo_p.add_argument("--min-students", type=int, default=cfg.SEED_MIN_STUDENTS)
    demo_p.add_argument("--max-students", type=int, default=cfg.SEED_MAX_STUDENTS)
    demo_p.add_argument("--min-events", type=int, default=cfg.SEED_MIN_EVENTS)
    demo_p.add_argument("--max-events", type=int, default=cfg.SEED_MAX_EVENTS)
    demo_p.add_argument("--min-programs", type=int, default=cfg.SEED_MIN_PROGRAMS)
    demo_p.add_argument("--start-mmddyy", type=str, default="{},{},{}".format(*cfg.SEED_START_MMDDYY))
    demo_p.add_argument("--end-mmddyy", type=str, default="{},{},{}".format(*cfg.SEED_END_MMDDYY))
    demo_p.add_argument("--credentials-format", type=str, choices=["csv", "tsv", "psv"], default=cfg.SEED_CREDENTIALS_FORMAT)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    logger.info(f"Using Deterministic RNG Seed: {cfg.SEED_RANDOMIZER_KEY}")
    rng = random.Random(cfg.SEED_RANDOMIZER_KEY)

    db = SessionLocal()
    try:
        _ensure_backend_schema_up_to_date()
        if seed_wipe:
            wipe_records(db, preserve_platform_admin=cfg.SEED_ADMIN_EMAIL)

        seed_roles(db)
        seed_attendance_methods(db)
        seed_attendance_statuses(db)
        seed_event_types(db)
        seed_permission_catalog(db)

        from modules.helpers import hash_passwords_parallel
        admin_hash = hash_passwords_parallel([cfg.SEED_ADMIN_PASSWORD], rounds=12, workers=1)[0]
        seed_platform_admin(db, email=cfg.SEED_ADMIN_EMAIL, password_hash=admin_hash)

        if args.command == "demo":
            start = _parse_mmddyy(args.start_mmddyy)
            end = _parse_mmddyy(args.end_mmddyy)

            run_demo(
                db,
                rng=rng,
                n_schools=max(1, args.schools),
                min_students=max(0, min(args.min_students, args.max_students)),
                max_students=max(0, max(args.min_students, args.max_students)),
                min_events=max(0, min(args.min_events, args.max_events)),
                max_events=max(0, max(args.min_events, args.max_events)),
                min_colleges=max(1, min(args.min_colleges, args.max_colleges)),
                max_colleges=max(1, max(args.min_colleges, args.max_colleges)),
                min_programs=max(1, args.min_programs),
                start_date=start,
                end_date=end,
                suffix_probability=cfg.SEED_USER_SUFFIX_PROBABILITY,
                unique_passwords=cfg.SEED_UNIQUE_PASSWORDS,
                credentials_format=args.credentials_format,
                seed_admin_email=cfg.SEED_ADMIN_EMAIL,
                seed_admin_password=cfg.SEED_ADMIN_PASSWORD,
            )

    except KeyboardInterrupt:
        logger.warning("\nSeeding interrupted by user.")
        db.rollback()
        sys.exit(1)
    except Exception as e:
        # Extract just the root cause — no traceback spam
        cause = e.__cause__ or e
        msg = str(cause).split("\n")[0].strip()

        if "could not translate host name" in msg or "Connection refused" in msg or "could not connect" in msg.lower():
            logger.error(f"[seeder] Cannot connect to database. Check DATABASE_URL in seeder/.env")
            logger.error(f"[seeder] Detail: {msg}")
        elif "password authentication failed" in msg:
            logger.error(f"[seeder] Database authentication failed. Check POSTGRES_USER/PASSWORD in database/.env")
        elif "database" in msg.lower() and "does not exist" in msg.lower():
            logger.error(f"[seeder] Database does not exist. Run docker-compose up to initialize it first.")
            logger.error(f"[seeder] Detail: {msg}")
        else:
            logger.error(f"[seeder] Seeding failed: {msg}")

        db.rollback()
        sys.exit(1)
    finally:
        db.close()


def _parse_mmddyy(val: str) -> tuple[int, int, int]:
    try:
        m, d, y = val.split(",")
        return int(m.strip()), int(d.strip()), int(y.strip())
    except Exception:
        return (1, 1, 2024)


if __name__ == "__main__":
    main()
