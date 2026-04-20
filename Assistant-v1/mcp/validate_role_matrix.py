from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError

from policy import BASE_ROLE_POLICIES, PERMISSION_POLICIES


def main() -> int:
    assistant_env = Path(__file__).resolve().parents[1] / ".env"
    root_env = Path(__file__).resolve().parents[2] / ".env"
    load_dotenv(root_env, override=False)
    load_dotenv(assistant_env, override=False)

    db_url = (
        os.getenv("TENANT_DATABASE_URL")
        or os.getenv("APP_DATABASE_URL")
        or os.getenv("DATABASE_URL")
    )
    if not db_url:
        print("TENANT_DATABASE_URL (or APP_DATABASE_URL/DATABASE_URL) is required.")
        return 1

    try:
        engine = create_engine(db_url, pool_pre_ping=True)
        with engine.connect() as conn:
            inspector = inspect(conn)
            table_names = set(inspector.get_table_names(schema="public"))
            columns_by_table = {
                table: {column["name"] for column in inspector.get_columns(table, schema="public")}
                for table in table_names
            }
    except SQLAlchemyError as exc:
        print(f"Schema inspection failed: {exc}")
        return 1

    failures: list[str] = []

    def validate_policy(label: str, policy) -> None:
        missing_allowed = sorted(policy.allowed_tables - table_names)
        if missing_allowed:
            failures.append(f"{label}: allowed tables missing in DB: {', '.join(missing_allowed)}")

        missing_write = sorted(policy.allowed_write_tables - policy.allowed_tables)
        if missing_write:
            failures.append(f"{label}: write tables not present in allowed_tables: {', '.join(missing_write)}")

        for table, required_filters in sorted(policy.required_filters.items()):
            if table not in table_names:
                failures.append(f"{label}: scoped table missing in DB: {table}")
                continue

            missing_columns = sorted(required_filters - columns_by_table[table])
            if missing_columns:
                failures.append(
                    f"{label}: required filters missing on {table}: {', '.join(missing_columns)}"
                )

    for role, policy in BASE_ROLE_POLICIES.items():
        validate_policy(f"role:{role}", policy)
    for permission, policy in PERMISSION_POLICIES.items():
        validate_policy(f"permission:{permission}", policy)

    if failures:
        print("ROLE MATRIX VALIDATION FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("ROLE MATRIX VALIDATION PASSED")
    for role, policy in BASE_ROLE_POLICIES.items():
        print(
            f"- role:{role}: {len(policy.allowed_tables)} tables, "
            f"{len(policy.allowed_write_tables)} write tables, "
            f"{len(policy.required_filters)} scoped tables"
        )
    for permission, policy in PERMISSION_POLICIES.items():
        print(
            f"- permission:{permission}: {len(policy.allowed_tables)} tables, "
            f"{len(policy.allowed_write_tables)} write tables, "
            f"{len(policy.required_filters)} scoped tables"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
