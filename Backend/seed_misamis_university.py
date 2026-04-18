"""Entry script for the Misamis University large dataset seed."""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.misamis_university_seeder import main


if __name__ == "__main__":
    raise SystemExit(main())
