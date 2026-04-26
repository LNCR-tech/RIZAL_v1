import sys
from pathlib import Path

# Mocking the path logic from the migration script
def test_path_resolution():
    print("--- Testing Path Resolution ---")
    # Simulate being in backend/alembic/versions/
    # In reality, this script is in the root or artifacts, so we have to adjust
    backend_dir = Path("C:/Users/cmpj/dev/work/Collab/aurav3-pilot/backend")
    sql_path = backend_dir / "app" / "db" / "schema.sql"
    
    print(f"Looking for schema.sql at: {sql_path}")
    if sql_path.exists():
        print("SUCCESS: File found!")
        return sql_path
    else:
        print("FAILURE: File NOT found!")
        return None

def test_sql_loading(sql_path):
    if not sql_path: return
    print("\n--- Testing SQL Loading ---")
    try:
        content = sql_path.read_text(encoding="utf-8")
        print(f"SUCCESS: Loaded {len(content)} characters.")
        return content
    except Exception as e:
        print(f"FAILURE: Could not load file: {e}")
        return None

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

def test_splitting(content):
    if not content: return
    print("\n--- Testing Statement Splitting ---")
    statements = _split_sql_statements(content)
    print(f"SUCCESS: Split into {len(statements)} statements.")
    
    print("\nFirst 3 statements:")
    for i, s in enumerate(statements[:3]):
        print(f"{i+1}: {s[:100]}...")

if __name__ == "__main__":
    path = test_path_resolution()
    content = test_sql_loading(path)
    test_splitting(content)
