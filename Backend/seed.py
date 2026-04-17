"""Use: Seeds the backend with starter data.
Where to use: Use this script during local setup or when you need sample backend records.
Role: Script layer. It prepares initial data outside the running API.
"""

import sys
from pathlib import Path

# Ensure `Backend/app` is importable when called from repo root.
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.seeder import run_seeder


if __name__ == "__main__":
    try:
        run_seeder()
    except KeyboardInterrupt:
        print("\nSeeding cancelled by user")
    except Exception as exc:
        print(f"Seeding failed: {exc}")
        sys.exit(1)

