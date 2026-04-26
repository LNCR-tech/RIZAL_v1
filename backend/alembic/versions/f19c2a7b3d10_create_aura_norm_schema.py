"""create aura_norm normalized schema (side-by-side)

Revision ID: f19c2a7b3d10
Revises: e6f7a8b9c0d1
Create Date: 2026-04-26
"""

from __future__ import annotations

from pathlib import Path

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "f19c2a7b3d10"
down_revision = "e6f7a8b9c0d1"
branch_labels = None
depends_on = None


def _split_sql_statements(sql: str) -> list[str]:
    statements: list[str] = []
    buff: list[str] = []
    in_single_quote = False
    in_double_quote = False
    i = 0
    while i < len(sql):
        ch = sql[i]
        if ch == "'" and not in_double_quote:
            # handle escaped single quote ''
            next_ch = sql[i + 1] if i + 1 < len(sql) else ""
            if in_single_quote and next_ch == "'":
                buff.append(ch)
                buff.append(next_ch)
                i += 2
                continue
            in_single_quote = not in_single_quote
            buff.append(ch)
            i += 1
            continue
        if ch == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            buff.append(ch)
            i += 1
            continue
        if ch == ";" and not in_single_quote and not in_double_quote:
            stmt = "".join(buff).strip()
            if stmt:
                statements.append(stmt)
            buff = []
            i += 1
            continue
        buff.append(ch)
        i += 1
    tail = "".join(buff).strip()
    if tail:
        statements.append(tail)
    return statements


def _load_normalized_schema_sql() -> str:
    # versions/ -> alembic/ -> backend/ -> repo root
    repo_root = Path(__file__).resolve().parents[3]
    sql_path = repo_root / "db_normalized" / "new_db_schema.sql"
    return sql_path.read_text(encoding="utf-8")


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "aura_norm" in inspector.get_schema_names():
        existing = set(inspector.get_table_names(schema="aura_norm"))
        if "schools" in existing and "users" in existing:
            return

    raw_sql = _load_normalized_schema_sql()
    for stmt in _split_sql_statements(raw_sql):
        upper = stmt.strip().upper()
        if upper in {"BEGIN", "COMMIT"}:
            continue
        op.execute(stmt)


def downgrade() -> None:
    op.execute("DROP SCHEMA IF EXISTS aura_norm CASCADE")

