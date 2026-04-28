# 🚨 PRODUCTION SERVER FIX GUIDE

## Current Situation

**Container Names**: `rizal_v1-*` (e.g., `rizal_v1-db-1`, `rizal_v1-migrate-1`)  
**Docker Compose File**: `docker-compose.prod.yml`  
**Status**: ✅ **Already using pgvector image!**

---

## 🔍 DIAGNOSIS

The good news: **`docker-compose.prod.yml` already has the correct pgvector image** (line 38):

```yaml
db:
  image: pgvector/pgvector:pg15  # ✅ Correct!
```

The migration is failing for a **different reason**. Let's diagnose:

---

## 📋 STEP 1: Check Migration Logs

```bash
# SSH to production server
ssh ubuntu@your-server-ip

# Check what migration is failing
docker logs rizal_v1-migrate-1 --tail 100
```

Look for:
- ❌ **Syntax errors** in our new migration
- ❌ **Database connection issues**
- ❌ **Alembic version conflicts**
- ❌ **Missing dependencies**

---

## 🔧 STEP 2: Common Issues & Fixes

### Issue A: Our New Migration Has Syntax Error

If you see errors related to `85616f5dcc97_make_time_in_nullable.py`:

```bash
# Check the migration file
cat backend/alembic/versions/85616f5dcc97_make_time_in_nullable.py
```

**Fix**: The migration syntax looks correct, but let's verify the database state:

```bash
# Check if attendances table exists
docker exec rizal_v1-db-1 psql -U postgres -d fastapi_db -c "\d attendances"

# Check current migration version
docker exec rizal_v1-db-1 psql -U postgres -d fastapi_db -c "SELECT * FROM alembic_version;"
```

### Issue B: Database Not Initialized

If you see "relation does not exist" errors:

```bash
# Check if database exists
docker exec rizal_v1-db-1 psql -U postgres -l

# Check if tables exist
docker exec rizal_v1-db-1 psql -U postgres -d fastapi_db -c "\dt"
```

**Fix**: Database might need initialization:

```bash
# Recreate database
docker exec rizal_v1-db-1 psql -U postgres -c "DROP DATABASE IF EXISTS fastapi_db;"
docker exec rizal_v1-db-1 psql -U postgres -c "CREATE DATABASE fastapi_db;"

# Run migrations again
docker compose -f docker-compose.prod.yml up migrate
```

### Issue C: Alembic Version Conflict

If you see "Can't locate revision" or "Multiple heads" errors:

```bash
# Check alembic history
docker compose -f docker-compose.prod.yml run --rm migrate alembic history

# Check current head
docker compose -f docker-compose.prod.yml run --rm migrate alembic current
```

**Fix**: Reset alembic version:

```bash
# Backup first!
docker exec rizal_v1-db-1 pg_dump -U postgres -d fastapi_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Check what version is in database
docker exec rizal_v1-db-1 psql -U postgres -d fastapi_db -c "SELECT * FROM alembic_version;"

# If needed, manually set to previous version
docker exec rizal_v1-db-1 psql -U postgres -d fastapi_db -c "UPDATE alembic_version SET version_num = 'h9i0j1k2l3m4';"

# Run migration again
docker compose -f docker-compose.prod.yml up migrate
```

### Issue D: Migration Dependency Missing

If you see "Can't locate revision 'h9i0j1k2l3m4'":

Our migration depends on `h9i0j1k2l3m4`. Check if it exists:

```bash
ls -la backend/alembic/versions/ | grep h9i0j1k2l3m4
```

**Fix**: The dependency chain might be broken. We need to update the migration's `down_revision`.

---

## 🚀 STEP 3: Safe Restart Procedure

After identifying and fixing the issue:

```bash
# 1. Stop all services
docker compose -f docker-compose.prod.yml down

# 2. Start database only
docker compose -f docker-compose.prod.yml up -d db

# 3. Wait for database to be healthy
sleep 10
docker compose -f docker-compose.prod.yml ps db

# 4. Run migration manually to see detailed output
docker compose -f docker-compose.prod.yml run --rm migrate

# 5. If migration succeeds, start all services
docker compose -f docker-compose.prod.yml up -d

# 6. Monitor logs
docker compose -f docker-compose.prod.yml logs -f
```

---

## 🔍 STEP 4: Detailed Diagnosis Script

Run this on the production server:

```bash
#!/bin/bash
echo "=== AURA PRODUCTION DIAGNOSIS ==="
echo ""

echo "1. Container Status:"
docker compose -f docker-compose.prod.yml ps
echo ""

echo "2. Database Status:"
docker exec rizal_v1-db-1 psql -U postgres -c "SELECT version();" 2>&1
echo ""

echo "3. Database List:"
docker exec rizal_v1-db-1 psql -U postgres -l 2>&1
echo ""

echo "4. Tables in fastapi_db:"
docker exec rizal_v1-db-1 psql -U postgres -d fastapi_db -c "\dt" 2>&1
echo ""

echo "5. Current Alembic Version:"
docker exec rizal_v1-db-1 psql -U postgres -d fastapi_db -c "SELECT * FROM alembic_version;" 2>&1
echo ""

echo "6. Attendances Table Structure:"
docker exec rizal_v1-db-1 psql -U postgres -d fastapi_db -c "\d attendances" 2>&1
echo ""

echo "7. Migration Container Logs:"
docker logs rizal_v1-migrate-1 --tail 50 2>&1
echo ""

echo "8. Backend Container Status:"
docker compose -f docker-compose.prod.yml ps backend
echo ""

echo "9. Available Migrations:"
ls -la backend/alembic/versions/ | tail -10
echo ""

echo "=== END DIAGNOSIS ==="
```

Save as `diagnose_prod.sh`, make executable, and run:

```bash
chmod +x diagnose_prod.sh
./diagnose_prod.sh > diagnosis_$(date +%Y%m%d_%H%M%S).txt
cat diagnosis_*.txt
```

---

## 🆘 EMERGENCY ROLLBACK

If nothing works and you need to get the server running:

```bash
# 1. Stop everything
docker compose -f docker-compose.prod.yml down

# 2. Restore from backup (if you have one)
docker compose -f docker-compose.prod.yml up -d db
sleep 10
docker exec -i rizal_v1-db-1 psql -U postgres -d fastapi_db < backup_YYYYMMDD_HHMMSS.sql

# 3. Temporarily skip our new migration
cd backend/alembic/versions
mv 85616f5dcc97_make_time_in_nullable.py 85616f5dcc97_make_time_in_nullable.py.skip

# 4. Start services
cd ~/RIZAL_v1  # or wherever your project is
docker compose -f docker-compose.prod.yml up -d

# 5. Restore migration file later
cd backend/alembic/versions
mv 85616f5dcc97_make_time_in_nullable.py.skip 85616f5dcc97_make_time_in_nullable.py
```

---

## 📊 EXPECTED BEHAVIOR

When working correctly:

```bash
# Migration logs should show:
INFO  [alembic.runtime.migration] Running upgrade h9i0j1k2l3m4 -> 85616f5dcc97, make time_in nullable
INFO  [alembic.runtime.migration] Running upgrade 85616f5dcc97 -> f7a8b9c0d1e2, add student face embeddings vector index

# Services should be:
NAME                    STATUS
rizal_v1-db-1          Up (healthy)
rizal_v1-redis-1       Up
rizal_v1-backend-1     Up (healthy)
rizal_v1-worker-1      Up
rizal_v1-beat-1        Up
rizal_v1-assistant-1   Up
rizal_v1-frontend-1    Up
rizal_v1-pgadmin-1     Up
```

---

## 🎯 MOST LIKELY ISSUE

Based on the error pattern, the most likely issues are:

1. **Migration dependency not found** (`h9i0j1k2l3m4`)
2. **Database not initialized** (no tables)
3. **Alembic version mismatch**

Run the diagnosis script above to identify which one.

---

## 📞 NEXT STEPS

1. **Run diagnosis script** to identify the exact error
2. **Share the output** so we can provide specific fix
3. **Apply appropriate fix** from Issue A/B/C/D above
4. **Verify services start** correctly
5. **Test application** functionality

---

## ⚠️ IMPORTANT

- ✅ **Always backup before changes**
- ✅ **Test fixes on local first** if possible
- ✅ **Monitor logs after restart**
- ✅ **Have rollback plan ready**

---

**Created**: 2026-04-29  
**For**: Production Ubuntu Server  
**Project**: rizal_v1 (docker-compose.prod.yml)

