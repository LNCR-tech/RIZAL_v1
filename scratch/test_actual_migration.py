import sys
import os
from pathlib import Path
from unittest.mock import MagicMock

# 1. Add backend to sys.path so we can import things correctly
backend_path = Path("C:/Users/cmpj/dev/work/Collab/aurav3-pilot/backend")
sys.path.append(str(backend_path))

# 2. Mock Alembic 'op' and 'context'
import alembic
from alembic import op

# Mocking the alembic operations
mock_op = MagicMock()
mock_context = MagicMock()
op.get_context = MagicMock(return_value=mock_context)
op.get_bind = MagicMock()

# Mocking the autocommit_block context manager
class MockAutocommitBlock:
    def __enter__(self):
        return MagicMock()
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

mock_context.autocommit_block.return_value = MockAutocommitBlock()

# 3. Import the actual migration script
# We have to import it by path because of the weird filename
import importlib.util
spec = importlib.util.spec_from_file_location(
    "migration", 
    str(backend_path / "alembic/versions/a9f3c1e2d4b5_replace_public_with_normalized_schema.py")
)
migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration)

# 4. Run the upgrade function
print("--- RUNNING LOCAL UPGRADE TEST ---")
try:
    migration.upgrade()
    print("\nLOCAL TEST PASSED: The code successfully found, loaded, and split the SQL!")
except Exception as e:
    print(f"\nLOCAL TEST FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
