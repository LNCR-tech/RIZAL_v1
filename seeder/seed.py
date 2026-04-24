import os
import sys
import logging
import random
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("Seeder")

# Inject Backend path to sys.path so app.* modules resolve correctly
repo_root = Path(__file__).resolve().parent.parent
backend_path = repo_root / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# Now we can import the app modules safely
from app.core.database import SessionLocal
from modules.core import ensure_tables, wipe_records, seed_roles, seed_permission_catalog, seed_platform_admin
from modules.demo import run_demo

def str_to_bool(val: str) -> bool:
    return str(val).lower() in ("true", "1", "yes", "t", "y")

def get_env_int(key: str, default: int) -> int:
    val = os.getenv(key, "")
    if not val or not str(val).strip():
        return default
    try:
        return int(str(val).strip())
    except Exception:
        return default

def parse_mmddyy(val: str) -> tuple[int, int, int]:
    try:
        m, d, y = val.split(",")
        return int(m.strip()), int(d.strip()), int(y.strip())
    except Exception:
        return (1, 1, 2024)

def main():
    load_dotenv(repo_root / ".env")
    
    # Gatekeeper: Check if seeding is enabled globally
    seed_enabled = str_to_bool(os.getenv("SEED_DATABASE", "false"))
    if not seed_enabled:
        logger.info("Database seeding is disabled (SEED_DATABASE=false). Skipping...")
        return
    
    parser = argparse.ArgumentParser(description="Aura v3 Database Seeder (Production Grade)")
    subparsers = parser.add_subparsers(dest="command", help="Seeder commands")
    
    # -------------------------------------------------------------------------
    # Subcommand: demo
    # -------------------------------------------------------------------------
    demo_p = subparsers.add_parser("demo", help="Generate stochastic dummy schools and records")
    demo_p.add_argument("--schools", type=int, default=get_env_int("SEED_N_SCHOOLS", 5))
    demo_p.add_argument("--min-colleges", type=int, default=get_env_int("SEED_MIN_COLLEGES", 3))
    demo_p.add_argument("--max-colleges", type=int, default=get_env_int("SEED_MAX_COLLEGES", 8))
    demo_p.add_argument("--min-students", type=int, default=get_env_int("SEED_MIN_STUDENTS", 50))
    demo_p.add_argument("--max-students", type=int, default=get_env_int("SEED_MAX_STUDENTS", 250))
    demo_p.add_argument("--min-events", type=int, default=get_env_int("SEED_MIN_EVENTS", 30))
    demo_p.add_argument("--max-events", type=int, default=get_env_int("SEED_MAX_EVENTS", 100))
    demo_p.add_argument("--min-programs", type=int, default=get_env_int("SEED_MIN_PROGRAMS", 1))
    demo_p.add_argument("--start-mmddyy", type=str, default=os.getenv("SEED_START_MMDDYY", "1,1,2024"))
    demo_p.add_argument("--end-mmddyy", type=str, default=os.getenv("SEED_END_MMDDYY", "12,31,2026"))
    demo_p.add_argument("--credentials-format", type=str, choices=["csv", "tsv", "psv"], default=os.getenv("SEED_CREDENTIALS_FORMAT", "csv").lower())
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
        
    # Global Configs
    randomizer_key = int(os.getenv("SEED_RANDOMIZER_KEY", "42"))
    wipe_existing = str_to_bool(os.getenv("SEED_WIPE_EXISTING", "false"))
    unique_passwords = str_to_bool(os.getenv("SEED_UNIQUE_PASSWORDS", "false"))
    suffix_prob = float(os.getenv("SEED_USER_SUFFIX_PROBABILITY", "0.3"))
    admin_email = os.getenv("SEED_ADMIN_EMAIL", "admin@example.com")
    admin_pw = os.getenv("SEED_ADMIN_PASSWORD", "ChangeMe123!")
    
    logger.info(f"Using Deterministic RNG Seed: {randomizer_key}")
    rng = random.Random(randomizer_key)
    
    db = SessionLocal()
    try:
        ensure_tables()
        if wipe_existing:
            wipe_records(db, preserve_platform_admin=admin_email)
            
        seed_roles(db)
        seed_permission_catalog(db)
        
        from modules.helpers import hash_passwords_parallel
        admin_hash = hash_passwords_parallel([admin_pw], rounds=12, workers=1)[0]
        seed_platform_admin(db, email=admin_email, password_hash=admin_hash)
        
        if args.command == "demo":
            # Edge-case swap protections
            actual_min_students = min(args.min_students, args.max_students)
            actual_max_students = max(args.min_students, args.max_students)
            actual_min_events = min(args.min_events, args.max_events)
            actual_max_events = max(args.min_events, args.max_events)
            actual_min_colleges = min(args.min_colleges, args.max_colleges)
            actual_max_colleges = max(args.min_colleges, args.max_colleges)

            run_demo(
                db,
                rng=rng,
                n_schools=max(1, args.schools),
                min_students=max(0, actual_min_students),
                max_students=max(0, actual_max_students),
                min_events=max(0, actual_min_events),
                max_events=max(0, actual_max_events),
                min_colleges=max(1, actual_min_colleges),
                max_colleges=max(1, actual_max_colleges),
                min_programs=max(1, args.min_programs),
                start_date=parse_mmddyy(args.start_mmddyy),
                end_date=parse_mmddyy(args.end_mmddyy),
                suffix_probability=suffix_prob,
                unique_passwords=unique_passwords,
                credentials_format=args.credentials_format,
                seed_admin_email=admin_email,
                seed_admin_password=admin_pw
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

if __name__ == "__main__":
    main()
