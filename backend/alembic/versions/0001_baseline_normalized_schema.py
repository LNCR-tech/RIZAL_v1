"""baseline normalized schema

Revision ID: 0001_baseline
Revises:
Create Date: 2026-05-01 00:00:00.000000
"""

from pathlib import Path
from alembic import op
import sqlalchemy as sa

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None

_SCHEMA_SQL = Path(__file__).parent.parent / "schema.sql"


def upgrade() -> None:
    sql = _SCHEMA_SQL.read_text(encoding="utf-8")
    for stmt in sql.split(";"):
        stmt = stmt.strip()
        if stmt and stmt.upper() not in ("BEGIN", "COMMIT"):
            op.execute(sa.text(stmt))


def downgrade() -> None:
    pass
