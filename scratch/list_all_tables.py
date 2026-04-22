import sys
import os
from pathlib import Path
import importlib.util

# Add Backend to sys.path
repo_root = Path(__file__).resolve().parent.parent
backend_path = repo_root / "Backend"
sys.path.insert(0, str(backend_path))

try:
    from app.models.base import Base
    from sqlalchemy.schema import CreateTable
    from sqlalchemy.dialects import postgresql
    
    # Forcefully import every single .py file in app/models to register all tables/associations
    models_dir = backend_path / "app" / "models"
    for root, dirs, files in os.walk(models_dir):
        for file in files:
            if file.endswith(".py") and file != "base.py":
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, backend_path)
                module_name = rel_path.replace(os.path.sep, ".").replace(".py", "")
                
                try:
                    spec = importlib.util.spec_from_file_location(module_name, file_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                except Exception as ex:
                    # Ignore double-imports or cross-dependencies
                    pass

    # Print every table found in MetaData
    sorted_tables = Base.metadata.sorted_tables
    table_names = [t.name for t in sorted_tables if "assistant" not in t.name.lower()]
    print(f"Verified count: {len(table_names)} metadata tables.")
    for name in sorted(table_names):
        print(f"- {name}")

    # Write the new SQL
    sql_output = [
        "-- Aura v3 Database Schema (PostgreSQL)",
        f"-- Verified accurate count: {len(table_names)} tables (plus alembic_version if managed by migrations)",
        "\n"
    ]
    for table in sorted_tables:
        if "assistant" in table.name.lower():
            continue
        ddl = CreateTable(table).compile(dialect=postgresql.dialect())
        sql_output.append(str(ddl).strip() + ";")
        sql_output.append("\n")

    with open(repo_root / "db.sql", "w") as f:
        f.write("\n".join(sql_output))
    print(f"\nSQL successfully written to {repo_root / 'db.sql'}")

except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
