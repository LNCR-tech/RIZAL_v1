import sys
import logging
import random
import argparse
from pathlib import Path

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
from modules.core import ensure_tables, wipe_records, seed_roles, seed_permission_catalog, seed_platform_admin
from modules.demo import run_demo
from config import load_config

cfg = load_config()


def main():
    if not cfg.SEED_DATABASE:
        logger.info("Database seeding is disabled (SEED_DATABASE=False in variables.py). Skipping...")
        return

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
        ensure_tables()
        if cfg.SEED_WIPE_EXISTING:
            wipe_records(db, preserve_platform_admin=cfg.SEED_ADMIN_EMAIL)

        seed_roles(db)
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
        logger.exception(f"Seeding failed: {str(e)}")
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
