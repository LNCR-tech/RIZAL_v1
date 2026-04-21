[← Back to Main README](../../README.md)

# MCP Folder (Schema + Query Services)

This folder contains two small services that expose:
- role-scoped schema introspection
- role-scoped, safe query execution

Both services rely on the same policy rules defined in `policy.py`.

## Files

- `policy.py`  
  Central allowlist + required filters per role.

- `schema_server.py`  
  POST `/schema` returns allowed tables/columns for the given role.

- `query_server.py`  
  POST `/query` executes **read-only** queries with strict guards.

## Environment Variables

These services connect to the tenant (website) database:

```
TENANT_DATABASE_URL=postgresql://...
```

## Run (dev)

```powershell
cd C:\Users\cmpj\dev\ai_apps\agentic_ai\mcp
uvicorn schema_server:app --reload --port 9001
uvicorn query_server:app --reload --port 9002
```

## Example Requests

### Schema

```json
POST /schema
{
  "role": "student"
}
```

### Query (structured)

```json
POST /query
{
  "role": "student",
  "table": "events",
  "columns": ["id", "title", "starts_at"],
  "filters": {"school_id": 1},
  "limit": 50
}
```

### Query (raw SQL)

```json
POST /query
{
  "role": "campus_admin",
  "sql": "select id, title from events where school_id = :school_id order by starts_at desc limit 50",
  "params": {"school_id": 1}
}
```

## Write Queries + Undo

Write queries are allowed for roles that have write access in `policy.py`.

Rules:
- `DELETE` is **blocked** in `/query`
- `INSERT` and `UPDATE` are allowed
- `UPDATE` must include a `WHERE` clause
- `INSERT` must include `RETURNING` so undo can be generated

When a write is accepted, the response includes an `undo` block:

```json
{
  "count": 1,
  "undo": {
    "steps": [
      {
        "sql": "update events set title = :old_title where id = :pk_id",
        "params": {"old_title": "Old title", "pk_id": 12}
      }
    ]
  }
}
```

Apply undo:

```json
POST /undo
{
  "steps": [
    {
      "sql": "update events set title = :old_title where id = :pk_id",
      "params": {"old_title": "Old title", "pk_id": 12}
    }
  ]
}
```

## Notes

- Raw SQL is validated but still risky. Prefer structured queries.
- Required filters (like `school_id`) are enforced by policy.
