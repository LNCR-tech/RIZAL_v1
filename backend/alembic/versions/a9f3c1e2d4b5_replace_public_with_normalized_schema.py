"""Replace public schema with normalized schema

Revision ID: a9f3c1e2d4b5
Revises: f19c2a7b3d10
Create Date: 2026-04-27

"""

from __future__ import annotations

import sys
import os
from pathlib import Path

import sqlalchemy as sa
from alembic import op

revision = "a9f3c1e2d4b5"
down_revision = "f19c2a7b3d10"
branch_labels = None
depends_on = None


def _load_normalized_schema_sql() -> str:
    print(f"DEBUG: Current working directory: {os.getcwd()}", flush=True)
    
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
        print(f"DEBUG: Checking path: {sql_path}", flush=True)
        if sql_path.exists():
            print(f"DEBUG: FOUND schema.sql at: {sql_path}", flush=True)
            return sql_path.read_text(encoding="utf-8")
            
    print(f"ERROR: schema.sql NOT FOUND in any of the {len(possible_paths)} locations!", flush=True)
    raise FileNotFoundError("Could not find schema.sql in any searched location.")


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
    print(f"DEBUG: Starting normalization migration...", flush=True)
    try:
        sql = _load_normalized_schema_sql()
        statements = _split_sql_statements(sql)
        print(f"DEBUG: Loaded {len(statements)} SQL statements from schema.sql", flush=True)

        with op.get_context().autocommit_block():
            bind = op.get_bind()
            conn = bind.connection.dbapi_connection.cursor()
            
            for i, statement in enumerate(statements):
                stmt_stripped = statement.strip()
                if stmt_stripped:
                    # Print first 50 chars of statement for debugging
                    if (i + 1) % 10 == 0 or (i + 1) == len(statements):
                        print(f"DEBUG: Executing statement {i+1}/{len(statements)}: {stmt_stripped[:50]}...", flush=True)
                    conn.execute(stmt_stripped)
            print("DEBUG: All statements executed successfully!", flush=True)
    except Exception as e:
        print(f"ERROR: Migration failed!", flush=True)
        print(f"ERROR DETAILS: {str(e)}", flush=True)
        sys.stdout.flush()
        raise


def downgrade() -> None:
    raise NotImplementedError(
        "Downgrade not supported — no data existed before this migration."
    )
