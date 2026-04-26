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


import os
import sys

def _load_normalized_schema_sql() -> str:
    print(f"DEBUG: [f19c2a7b3d10] Current working directory: {os.getcwd()}", flush=True)
    
    # Define possible locations for schema.sql
    possible_paths = [
        # Relative to this script (inside backend/alembic/versions/)
        Path(__file__).absolute().parents[2] / "app" / "db" / "schema.sql",
        # Relative to current working directory (usually /app or backend/)
        Path("app/db/schema.sql"),
        Path("backend/app/db/schema.sql"),
        # Absolute paths common in Docker
        Path("/app/app/db/schema.sql"),
        Path("/app/db/schema.sql"),
    ]
    
    for sql_path in possible_paths:
        print(f"DEBUG: [f19c2a7b3d10] Checking path: {sql_path}", flush=True)
        if sql_path.exists():
            print(f"DEBUG: [f19c2a7b3d10] FOUND schema.sql at: {sql_path}", flush=True)
            return sql_path.read_text(encoding="utf-8")
            
    print(f"ERROR: [f19c2a7b3d10] schema.sql NOT FOUND!", flush=True)
    raise FileNotFoundError("Could not find schema.sql in any searched location.")


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

