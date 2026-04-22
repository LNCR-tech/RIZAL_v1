"""Use: Seeds the backend with demo data.
Where to use: Run this script during local setup when you want explicit demo records.
Role: Script layer. It prepares local-development data outside the running API.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure `Backend/app` is importable when called from repo root.
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.app_settings import APP_SETTINGS
from app.seeder import (
    DEFAULT_DEMO_CREDENTIALS_PATH,
    BootstrapSeedOptions,
    DemoSeedOptions,
    run_demo_seed,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Seed the Aura backend with explicit demo data.",
    )
    parser.add_argument(
        "--wipe-existing",
        action="store_true",
        help="Remove existing application data before rebuilding the bootstrap and demo dataset.",
    )
    parser.add_argument(
        "--schools",
        type=int,
        default=APP_SETTINGS.demo_seed_schools,
        help="Target number of demo schools.",
    )
    parser.add_argument(
        "--users",
        type=int,
        default=APP_SETTINGS.demo_seed_users,
        help="Target number of demo users.",
    )
    parser.add_argument(
        "--email-domain",
        default=APP_SETTINGS.demo_seed_email_domain,
        help="Email domain to use for generated demo credentials.",
    )
    parser.add_argument(
        "--credentials-path",
        default=str(DEFAULT_DEMO_CREDENTIALS_PATH),
        help="CSV path where generated demo credentials will be written.",
    )
    parser.add_argument(
        "--massive-attendance",
        action="store_true",
        help="Generate the large attendance + sanctions dataset instead of the regular demo dataset.",
    )
    parser.add_argument(
        "--massive-students",
        type=int,
        default=APP_SETTINGS.demo_massive_students,
        help="Student count to use with --massive-attendance.",
    )
    parser.add_argument(
        "--massive-records",
        type=int,
        default=APP_SETTINGS.demo_massive_records,
        help="Attendance record count to use with --massive-attendance.",
    )
    parser.add_argument(
        "--admin-email",
        default=APP_SETTINGS.default_admin_email,
        help="Bootstrap platform-admin email to preserve or create before demo data is added.",
    )
    parser.add_argument(
        "--admin-password",
        default=APP_SETTINGS.default_admin_password,
        help="Bootstrap platform-admin password to set when the admin account is created or repaired.",
    )
    parser.add_argument(
        "--school-name",
        default=APP_SETTINGS.default_school_name,
        help="Default school name for the bootstrap school.",
    )
    parser.add_argument(
        "--school-code",
        default=APP_SETTINGS.default_school_code,
        help="Default school code for the bootstrap school.",
    )
    parser.add_argument(
        "--school-address",
        default=APP_SETTINGS.default_school_address,
        help="Default school address for the bootstrap school.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()

    bootstrap_options = BootstrapSeedOptions(
        admin_email=args.admin_email,
        admin_password=args.admin_password,
        school_name=args.school_name,
        school_code=args.school_code,
        school_address=args.school_address,
    )
    demo_options = DemoSeedOptions(
        wipe_existing=args.wipe_existing,
        schools_target=max(1, args.schools),
        users_target=max(1, args.users),
        email_domain=args.email_domain,
        credentials_path=Path(args.credentials_path).expanduser().resolve(),
        massive_attendance=args.massive_attendance,
        massive_students=max(1, args.massive_students),
        massive_records=max(1, args.massive_records),
    )

    try:
        run_demo_seed(options=demo_options, bootstrap_options=bootstrap_options)
        return 0
    except KeyboardInterrupt:
        print("\nDemo seeding cancelled by user")
        return 130
    except Exception as exc:
        print(f"Demo seeding failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
