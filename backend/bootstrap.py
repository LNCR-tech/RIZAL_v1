"""Bootstrap the backend with the minimum production dataset."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.seeder import BootstrapSeedOptions, run_production_bootstrap
from app.core.config import get_settings


def _build_parser() -> argparse.ArgumentParser:
    settings = get_settings()
    parser = argparse.ArgumentParser(
        description="Bootstrap the Aura backend with the first platform admin account.",
    )
    parser.add_argument(
        "--admin-email",
        required=False,
        help=f"Email for the first platform admin (default: {settings.default_admin_email})",
    )
    parser.add_argument(
        "--admin-password",
        required=False,
        help="Password for the first platform admin (default: from .env)",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    settings = get_settings()

    # Fallback to get_settings() if flags are not provided
    admin_email = args.admin_email or settings.default_admin_email
    admin_password = args.admin_password or settings.default_admin_password

    if not admin_email or not admin_password:
        print("Error: Admin email and password must be provided via flags or .env (DEFAULT_ADMIN_EMAIL/PASSWORD)")
        return 1

    options = BootstrapSeedOptions(
        admin_email=admin_email,
        admin_password=admin_password,
    )

    try:
        run_production_bootstrap(options=options)
        return 0
    except KeyboardInterrupt:
        print("\nProduction bootstrap cancelled by user")
        return 130
    except Exception as exc:
        print(f"Production bootstrap failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
