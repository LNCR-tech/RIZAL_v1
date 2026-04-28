# Migration Failure Diagnosis

## Issue
Migration container failed with exit code 1, causing server shutdown.

## Likely Causes

### 1. **pgvector Extension Missing** (Most Likely)
The migration `f7a8b9c0d1e2_add_student_face_embeddings_vector_index.py` requires pgvector extension.

**Error Pattern**:
```
psycopg2.errors.FeatureNotSupported: extension "vector" is not available
DETAIL: Could not open extension control file "/usr/share/postgresql/15/extension/vector.control"
```

### 2. **Database Connection Issues**
- DATABASE_URL not set correctly
- Postgres container not ready
- Network issues

### 3. **Migration Syntax Errors**
- Our new migration `85616f5dcc97_make_time_in_nullable.py` has syntax issues
- Alembic version conflicts

## Immediate Actions

### Step 1: Check Migration Logs
```bash
docker logs rizal_v1-migrate-1 --tail 100
```

### Step 2: Check if pgvector is the Issue
```bash
docker exec rizal_v1-db-1 psql -U postgres -d fastapi_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

If this fails with "extension not available", you need to install pgvector.

## Solutions

### Solution A: Install pgvector Extension (RECOMMENDED)

Update `docker-compose.yml`:

```yaml
postgres:
  image: pgvector/pgvector:pg15  # Change from postgres:15
  restart: always
  environment:
    POSTGRES_USER: ${DB_USER:-postgres}
    POSTGRES_PASSWORD: ${DB_PASSWORD:-postgres}
    POSTGRES_DB: ${DB_NAME:-db}
  # ... rest of config
```

Then:
```bash
# Backup first
docker exec rizal_v1-db-1 pg_dump -U postgres -d fastapi_db > backup_before_pgvector.sql

# Recreate with pgvector
docker compose down
docker compose up -d postgres
docker compose up migrate
```

### Solution B: Skip pgvector Migration Temporarily

Modify the failing migration to skip if pgvector is not available:

**File**: `backend/alembic/versions/f7a8b9c0d1e2_add_student_face_embeddings_vector_index.py`

```python
def upgrade() -> None:
    try:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
        # ... rest of migration
    except Exception as e:
        print(f"⚠️ Skipping pgvector migration: {e}")
        print("Face embedding search will not be available until pgvector is installed.")
        return
```

### Solution C: Rollback Our Changes (If Our Migration is the Problem)

If the issue is with our `85616f5dcc97_make_time_in_nullable.py` migration:

```bash
# Check which migration is failing
docker logs rizal_v1-migrate-1 2>&1 | grep "Running upgrade"

# If it's our migration, we can temporarily remove it
git stash
docker compose up migrate
```

## Verification Steps

After applying a solution:

1. **Check migration succeeded**:
```bash
docker logs rizal_v1-migrate-1
# Should show: "Running upgrade ... -> 85616f5dcc97, make time_in nullable"
```

2. **Verify database schema**:
```bash
docker exec rizal_v1-db-1 psql -U postgres -d fastapi_db -c "\d attendances"
# Check if time_in is nullable
```

3. **Check alembic version**:
```bash
docker exec rizal_v1-db-1 psql -U postgres -d fastapi_db -c "SELECT * FROM alembic_version;"
```

4. **Start services**:
```bash
docker compose up -d
```

## Prevention

To prevent this in production:

1. ✅ Always test migrations locally first
2. ✅ Use pgvector-enabled Postgres image from the start
3. ✅ Add migration health checks
4. ✅ Have rollback plan ready
5. ✅ Monitor migration logs during deployment

## Next Steps

1. Run Step 1 to see the actual error
2. Choose appropriate solution based on error
3. Apply fix
4. Verify services start correctly
5. Test the application

