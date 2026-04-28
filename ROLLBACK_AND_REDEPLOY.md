# 🚨 ROLLBACK AND REDEPLOY - Production Server

## The Issue

The migration partially ran and failed, so the database thinks it's at version `add_attendance_consistency_check` but the constraint wasn't actually created.

We need to:
1. ✅ Rollback the failed migration
2. ✅ Pull the fixed code
3. ✅ Run the migration again

---

## 🚀 **DEPLOYMENT STEPS**

### Step 1: Rollback the Failed Migration

```bash
# SSH to production
ssh ubuntu@your-server-ip

# Navigate to project
cd ~/RIZAL_v1

# Rollback to previous migration
docker compose -f docker-compose.prod.yml run --rm migrate alembic downgrade -1

# Verify we're back to 85616f5dcc97
docker exec rizal_v1-db-1 psql -U postgres -d fastapi_db -c "SELECT * FROM alembic_version;"
```

**Expected output**: `version_num = 85616f5dcc97`

### Step 2: Pull the Fixed Code

```bash
# Pull the fix
git pull origin aura_ci_cd

# Verify the fix is there
grep -A 5 "def upgrade" backend/alembic/versions/add_attendance_consistency_check.py
```

**Expected**: Should show cleanup BEFORE constraint creation

### Step 3: Restart Services

```bash
# Stop all services
docker compose -f docker-compose.prod.yml down

# Start everything (migration will run automatically)
docker compose -f docker-compose.prod.yml up -d

# Monitor migration
docker logs rizal_v1-migrate-1 -f
```

### Step 4: Verify Success

```bash
# Check services
docker compose -f docker-compose.prod.yml ps

# Verify constraint was created
docker exec rizal_v1-db-1 psql -U postgres -d fastapi_db -c "\d attendances"

# Check for bad data (should be 0)
docker exec rizal_v1-db-1 psql -U postgres -d fastapi_db -c "
SELECT COUNT(*) FROM attendances 
WHERE time_in IS NULL AND method IS NOT NULL;
"
```

---

## ✅ **EXPECTED OUTPUT**

### Step 1 - Rollback:
```
INFO  [alembic.runtime.migration] Running downgrade add_attendance_consistency_check -> 85616f5dcc97
```

### Step 3 - Migration:
```
INFO  [alembic.runtime.migration] Running upgrade 85616f5dcc97 -> add_attendance_consistency_check
```

### Step 4 - Services:
```
NAME                    STATUS
rizal_v1-db-1          Up (healthy)
rizal_v1-backend-1     Up (healthy)
rizal_v1-worker-1      Up
rizal_v1-beat-1        Up
rizal_v1-assistant-1   Up
rizal_v1-frontend-1    Up
```

---

## 🆘 **IF ROLLBACK FAILS**

If the rollback command fails because the constraint doesn't exist:

```bash
# Manually set the alembic version back
docker exec rizal_v1-db-1 psql -U postgres -d fastapi_db -c "
UPDATE alembic_version SET version_num = '85616f5dcc97';
"

# Verify
docker exec rizal_v1-db-1 psql -U postgres -d fastapi_db -c "SELECT * FROM alembic_version;"

# Then continue with Step 2
```

---

## 🔍 **ALTERNATIVE: Manual Cleanup + Constraint**

If you want to skip the migration and do it manually:

```bash
# 1. Clean bad data
docker exec rizal_v1-db-1 psql -U postgres -d fastapi_db -c "
UPDATE attendances 
SET method = NULL, check_in_status = NULL
WHERE time_in IS NULL AND method IS NOT NULL;
"

# 2. Verify cleanup
docker exec rizal_v1-db-1 psql -U postgres -d fastapi_db -c "
SELECT COUNT(*) FROM attendances 
WHERE time_in IS NULL AND method IS NOT NULL;
"
# Should return 0

# 3. Add constraint manually
docker exec rizal_v1-db-1 psql -U postgres -d fastapi_db -c "
ALTER TABLE attendances 
ADD CONSTRAINT attendance_time_in_method_consistency 
CHECK ((time_in IS NULL AND method IS NULL) OR (time_in IS NOT NULL AND method IS NOT NULL));
"

# 4. Update alembic version
docker exec rizal_v1-db-1 psql -U postgres -d fastapi_db -c "
UPDATE alembic_version SET version_num = 'add_attendance_consistency_check';
"

# 5. Start services
docker compose -f docker-compose.prod.yml up -d
```

---

## 📊 **WHAT THE FIX DOES**

### Before (Broken Order):
```python
def upgrade():
    # 1. Create constraint FIRST ❌
    op.create_check_constraint(...)
    
    # 2. Clean data SECOND ❌
    op.execute("UPDATE attendances...")
```

**Problem**: Constraint fails because bad data still exists!

### After (Fixed Order):
```python
def upgrade():
    # 1. Clean data FIRST ✅
    op.execute("UPDATE attendances...")
    
    # 2. Create constraint SECOND ✅
    op.create_check_constraint(...)
```

**Solution**: Bad data is cleaned before constraint is applied!

---

## 🎯 **QUICK SUMMARY**

**What happened**:
1. Migration tried to add constraint
2. Bad data existed in database
3. Constraint creation failed
4. Migration marked as "applied" but constraint doesn't exist

**What we're doing**:
1. Rollback the failed migration
2. Pull the fixed code (cleanup BEFORE constraint)
3. Run migration again
4. This time it will succeed

---

## ⏱️ **TIMELINE**

- **Rollback**: 10 seconds
- **Pull code**: 10 seconds
- **Restart services**: 2-3 minutes
- **Total**: ~3-4 minutes

---

**Ready to deploy!** 🚀

Just follow Steps 1-4 above in order.

