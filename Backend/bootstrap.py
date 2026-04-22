"""Use: Bootstraps the backend with the minimum production dataset.
Where to use: Run this script after migrations in production to create the first admin and default school.
Role: Script layer. It prepares baseline production data outside the running API.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.app_settings import APP_SETTINGS
from app.seeder import BootstrapSeedOptions, run_production_bootstrap


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bootstrap the Aura backend with the first platform admin and default school.",
    )
    parser.add_argument(
        "--admin-email",
        required=True,
        help="Email address for the first platform admin.",
    )
    parser.add_argument(
        "--admin-password",
        required=True,
        help="Password for the first platform admin.",
    )
    parser.add_argument(
        "--school-name",
        default=APP_SETTINGS.default_school_name,
        help="Default school name.",
    )
    parser.add_argument(
        "--school-code",
        default=APP_SETTINGS.default_school_code,
        help="Default school code.",
    )
    parser.add_argument(
        "--school-address",
        default=APP_SETTINGS.default_school_address,
        help="Default school address.",
    )
    parser.add_argument(
        "--school-logo-url",
        default=APP_SETTINGS.default_school_logo_url,
        help="Optional logo URL for the default school.",
    )
    parser.add_argument(
        "--school-primary-color",
        default=APP_SETTINGS.default_school_primary_color,
        help="Primary branding color for the default school.",
    )
    parser.add_argument(
        "--school-secondary-color",
        default=APP_SETTINGS.default_school_secondary_color,
        help="Secondary branding color for the default school.",
    )
    parser.add_argument(
        "--subscription-status",
        default=APP_SETTINGS.default_subscription_status,
        help="Subscription status for the default school.",
    )
    parser.add_argument(
        "--subscription-plan",
        default=APP_SETTINGS.default_subscription_plan,
        help="Subscription plan for the default school.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()

    options = BootstrapSeedOptions(
        admin_email=args.admin_email,
        admin_password=args.admin_password,
        school_name=args.school_name,
        school_code=args.school_code,
        school_address=args.school_address,
        school_logo_url=args.school_logo_url,
        school_primary_color=args.school_primary_color,
        school_secondary_color=args.school_secondary_color,
        subscription_status=args.subscription_status,
        subscription_plan=args.subscription_plan,
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
