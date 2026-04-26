"""Replace public schema with normalized schema

Revision ID: a9f3c1e2d4b5
Revises: f19c2a7b3d10
Create Date: 2026-04-27

"""

from __future__ import annotations

from pathlib import Path

import sqlalchemy as sa
from alembic import op

revision = "a9f3c1e2d4b5"
down_revision = "f19c2a7b3d10"
branch_labels = None
depends_on = None


def _load_normalized_schema_sql() -> str:
    repo_root = Path(__file__).resolve().parents[3]
    sql_path = repo_root / "db_normalized" / "new_db_schema.sql"
    return sql_path.read_text(encoding="utf-8")


def _split_sql_statements(sql: str) -> list[str]:
    statements: list[str] = []
    buff: list[str] = []
    in_single_quote = False
    in_double_quote = False
    i = 0
    while i < len(sql):
        ch = sql[i]
        if ch == "'" and not in_double_quote:
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


def upgrade() -> None:
    bind = op.get_bind()
    raw_conn = bind.connection.dbapi_connection
    cursor = raw_conn.cursor()

    raw_sql = _load_normalized_schema_sql()
    raw_sql = raw_sql.replace("CREATE SCHEMA IF NOT EXISTS aura_norm;", "")
    raw_sql = raw_sql.replace("SET search_path TO aura_norm, public;", "")
    # Remove the extension line from the SQL — we handle it separately below.
    raw_sql = raw_sql.replace("CREATE EXTENSION IF NOT EXISTS citext;", "")

    cursor.execute("DROP SCHEMA public CASCADE")
    cursor.execute("CREATE SCHEMA public")
    cursor.execute("GRANT ALL ON SCHEMA public TO public")
    cursor.execute("CREATE EXTENSION IF NOT EXISTS citext SCHEMA public")
    # Set search_path for the remainder of this transaction.
    cursor.execute("SELECT set_config('search_path', 'public', false)")

    for stmt in _split_sql_statements(raw_sql):
        stripped = stmt.strip()
        if not stripped or stripped.startswith("--"):
            continue
        if stripped.upper() in {"BEGIN", "COMMIT"}:
            continue
        cursor.execute(stripped)

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS alembic_version "
        "(version_num VARCHAR(32) NOT NULL, "
        "CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))"
    )
    cursor.execute(f"INSERT INTO alembic_version (version_num) VALUES ('{revision}')")
    cursor.close()


def downgrade() -> None:
    raise NotImplementedError(
        "Downgrade not supported — no data existed before this migration."
    )
