"""Bootstrap the backend with the minimum production dataset."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.seeder import BootstrapSeedOptions, run_production_bootstrap
from app.core.app_settings import APP_SETTINGS


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bootstrap the Aura backend with the first platform admin account.",
    )
    parser.add_argument(
        "--admin-email",
        required=True,
        help="Email address for the first platform admin (REQUIRED).",
    )
    parser.add_argument(
        "--admin-password",
        required=True,
        help="Password for the first platform admin (REQUIRED). Use a strong password.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()

    options = BootstrapSeedOptions(
        admin_email=args.admin_email,
        admin_password=args.admin_password,
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
