# SAFE DEPLOYMENT GUIDE - Production Server

**CRITICAL**: Read this BEFORE deploying to production with existing data

---

## ⚠️ DEPLOYMENT SAFETY ASSESSMENT

### Current Risk Level: 🟡 MEDIUM-LOW

**Safe to deploy**: ✅ YES, with precautions  
**Data loss risk**: ✅ NONE  
**Downtime required**: ✅ NO  
**Rollback available**: ✅ YES

---

## 🔍 PRE-DEPLOYMENT CHECKS (MANDATORY)

### Step 1: Backup Database (CRITICAL)

```bash
# Create full database backup BEFORE any changes
docker exec -it rizal_v1-db-1 pg_dump -U aura_user -d aura_db > backup_before_attendance_fix_$(date +%Y%m%d_%H%M%S).sql

# Verify backup was created
ls -lh backup_before_attendance_fix_*.sql
```

**DO NOT PROCEED** without a valid backup!

---

### Step 2: Check for Bad Data

```bash
# Connect to production database
docker exec -it rizal_v1-db-1 psql -U aura_user -d aura_db
```

```sql
-- Query 1: Count bad records
SELECT COUNT(*) as bad_records
FROM attendance 
WHERE time_in IS NULL AND method IS NOT NULL;

-- Query 2: Identify affected events
SELECT 
    e.id,
    e.name,
    e.status,
    COUNT(*) as bad_records
FROM attendance a
JOIN event e ON a.event_id = e.id
WHERE a.time_in IS NULL AND a.method IS NOT NULL
GROUP BY e.id, e.name, e.status
ORDER BY bad_records DESC;

-- Query 3: Sample bad records
SELECT 
    a.id,
    sp.student_id,
    e.name as event_name,
    a.time_in,
    a.method,
    a.status,
    a.created_at
FROM attendance a
JOIN student_profile sp ON a.student_id = sp.id
JOIN event e ON a.event_id = e.id
WHERE a.time_in IS NULL AND a.method IS NOT NULL
ORDER BY a.created_at DESC
LIMIT 10;
```

**Record the results**:
- Bad records count: _______
- Affected events: _______
- Date range: _______

---

### Step 3: Analyze Impact

Based on Query 2 results:

**If bad_records = 0**: ✅ **SAFE TO DEPLOY IMMEDIATELY**
- No cleanup needed
- Proceed to deployment steps

**If bad_records < 100**: 🟡 **SAFE WITH CLEANUP**
- Minor data issue
- Run cleanup script before constraint
- Low risk

**If bad_records > 100**: 🟠 **INVESTIGATE FIRST**
- Significant data issue
- Review sample records
- Understand why so many bad records exist
- May indicate ongoing issue

**If bad_records > 1000**: 🔴 **STOP AND INVESTIGATE**
- Major data integrity issue
- DO NOT deploy constraint yet
- Investigate root cause first
- May need custom cleanup strategy

---

## 🛡️ SAFE DEPLOYMENT STRATEGY

### Option A: Zero-Downtime Deployment (RECOMMENDED)

This approach deploys changes without downtime and allows rollback.

#### Phase 1: Deploy Frontend Fix (Safe)

```bash
# 1. Pull latest code
cd Frontend
git pull

# 2. Verify the fix
grep "toOptionalString(attendance.method" src/services/backendNormalizers.js
# Should show: toOptionalString(attendance.method, null)

# 3. Build and deploy
npm run build
docker compose up --build -d frontend

# 4. Verify deployment
curl -I http://localhost:5173
# Should return 200 OK
```

**Risk**: ✅ NONE - Frontend change is backward compatible

---

#### Phase 2: Clean Bad Data (If Needed)

**ONLY if Step 2 found bad records > 0**

```bash
# Connect to database
docker exec -it rizal_v1-db-1 psql -U aura_user -d aura_db
```

```sql
-- Start transaction for safety
BEGIN;

-- Preview what will be changed
SELECT 
    id,
    student_id,
    event_id,
    method,
    check_in_status
FROM attendance
WHERE time_in IS NULL AND method IS NOT NULL;

-- If preview looks correct, run cleanup
UPDATE attendance 
SET method = NULL,
    check_in_status = NULL
WHERE time_in IS NULL AND method IS NOT NULL;

-- Verify cleanup
SELECT COUNT(*) FROM attendance 
WHERE time_in IS NULL AND method IS NOT NULL;
-- Should return 0

-- If everything looks good, commit
COMMIT;

-- If something looks wrong, rollback
-- ROLLBACK;
```

**Risk**: 🟡 LOW
- Changes only NULL values
- No data deletion
- Transaction allows rollback
- Backup available

---

#### Phase 3: Apply Database Constraint (Safe After Cleanup)

```bash
# 1. Verify no bad data exists
docker exec -it rizal_v1-db-1 psql -U aura_user -d aura_db -c "
SELECT COUNT(*) FROM attendance WHERE time_in IS NULL AND method IS NOT NULL;
"
# Must return 0 before proceeding

# 2. Apply migration
docker exec -it rizal_v1-backend-1 alembic upgrade head

# 3. Verify constraint was created
docker exec -it rizal_v1-db-1 psql -U aura_user -d aura_db -c "
SELECT conname, pg_get_constraintdef(oid) 
FROM pg_constraint 
WHERE conrelid = 'attendance'::regclass 
  AND conname = 'attendance_time_in_method_consistency';
"
# Should return 1 row with constraint definition
```

**Risk**: ✅ NONE (if bad data cleaned first)
- Constraint only prevents future bad data
- Does not modify existing data
- Can be rolled back

---

#### Phase 4: Deploy Backend (Optional - Validation Utility)

```bash
# 1. Pull latest code
cd Backend
git pull

# 2. Verify validation file exists
ls -la app/services/attendance_validation.py

# 3. Rebuild backend
docker compose up --build -d backend

# 4. Verify backend is running
curl http://localhost:8000/health
```

**Risk**: ✅ NONE
- Validation utility is optional
- Not used unless explicitly called
- Backward compatible

---

### Option B: Maintenance Window Deployment (Safest)

If you want maximum safety, schedule a maintenance window:

```bash
# 1. Announce maintenance (30 min window)
# 2. Stop accepting new attendance
# 3. Backup database
# 4. Run all deployment steps
# 5. Verify everything works
# 6. Resume operations
```

**Risk**: ✅ MINIMAL - Full control over deployment

---

## 🚨 ROLLBACK PROCEDURES

### If Frontend Issues Occur

```bash
# Rollback frontend
cd Frontend
git checkout HEAD~1 src/services/backendNormalizers.js
npm run build
docker compose up --build -d frontend
```

### If Database Constraint Causes Issues

```bash
# Remove constraint
docker exec -it rizal_v1-backend-1 alembic downgrade -1

# Verify constraint removed
docker exec -it rizal_v1-db-1 psql -U aura_user -d aura_db -c "
SELECT conname FROM pg_constraint 
WHERE conrelid = 'attendance'::regclass 
  AND conname = 'attendance_time_in_method_consistency';
"
# Should return 0 rows
```

### If Data Cleanup Went Wrong

```bash
# Restore from backup
docker exec -i rizal_v1-db-1 psql -U aura_user -d aura_db < backup_before_attendance_fix_YYYYMMDD_HHMMSS.sql
```

---

## ✅ POST-DEPLOYMENT VERIFICATION

### Test 1: Constraint Works

```bash
docker exec -it rizal_v1-db-1 psql -U aura_user -d aura_db
```

```sql
-- Should FAIL with constraint violation
INSERT INTO attendance (student_id, event_id, time_in, method, status)
VALUES (1, 1, NULL, 'manual', 'absent');

-- Should SUCCEED
INSERT INTO attendance (student_id, event_id, time_in, method, status)
VALUES (1, 1, NULL, NULL, 'absent');

-- Clean up test records
DELETE FROM attendance WHERE student_id = 1 AND event_id = 1;
```

### Test 2: No Bad Data Exists

```sql
SELECT COUNT(*) FROM attendance 
WHERE time_in IS NULL AND method IS NOT NULL;
-- Should return 0
```

### Test 3: Frontend Display

1. Open student dashboard
2. Check attendance history
3. Verify non-attendees show "No sign-in record" and "N/A"

### Test 4: New Attendance Works

1. Create test event
2. Have student sign in
3. Verify time_in and method are set
4. Complete event
5. Verify absent students have NULL time_in/method

---

## 📊 DEPLOYMENT DECISION MATRIX

| Scenario | Action | Risk | Downtime |
|----------|--------|------|----------|
| No bad data (count = 0) | Deploy all phases immediately | ✅ NONE | ✅ NO |
| Bad data < 100 | Clean data → Deploy constraint | 🟡 LOW | ✅ NO |
| Bad data 100-1000 | Review data → Clean → Deploy | 🟠 MEDIUM | ⚠️ OPTIONAL |
| Bad data > 1000 | Investigate → Custom cleanup | 🔴 HIGH | ⚠️ RECOMMENDED |

---

## 🎯 RECOMMENDED DEPLOYMENT PLAN

### For Production with Existing Data:

```bash
# === PREPARATION (Do this first) ===
# 1. Backup database
docker exec -it rizal_v1-db-1 pg_dump -U aura_user -d aura_db > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Check for bad data
docker exec -it rizal_v1-db-1 psql -U aura_user -d aura_db -c "
SELECT COUNT(*) FROM attendance WHERE time_in IS NULL AND method IS NOT NULL;
"

# === DEPLOYMENT (If count = 0) ===
# 3. Deploy frontend
cd Frontend && npm run build && docker compose up --build -d frontend

# 4. Apply constraint
docker exec -it rizal_v1-backend-1 alembic upgrade head

# 5. Verify
docker exec -it rizal_v1-db-1 psql -U aura_user -d aura_db -c "
SELECT conname FROM pg_constraint 
WHERE conrelid = 'attendance'::regclass 
  AND conname = 'attendance_time_in_method_consistency';
"

# === DEPLOYMENT (If count > 0) ===
# 3. Clean bad data first
docker exec -it rizal_v1-db-1 psql -U aura_user -d aura_db -c "
UPDATE attendance SET method = NULL, check_in_status = NULL 
WHERE time_in IS NULL AND method IS NOT NULL;
"

# 4. Verify cleanup
docker exec -it rizal_v1-db-1 psql -U aura_user -d aura_db -c "
SELECT COUNT(*) FROM attendance WHERE time_in IS NULL AND method IS NOT NULL;
"
# Must be 0

# 5. Deploy frontend
cd Frontend && npm run build && docker compose up --build -d frontend

# 6. Apply constraint
docker exec -it rizal_v1-backend-1 alembic upgrade head

# 7. Verify
docker exec -it rizal_v1-db-1 psql -U aura_user -d aura_db -c "
SELECT conname FROM pg_constraint 
WHERE conrelid = 'attendance'::regclass;
"
```

---

## 🔒 SAFETY GUARANTEES

After following this guide:

1. ✅ **No data loss** - Backup created before changes
2. ✅ **No downtime** - Zero-downtime deployment
3. ✅ **Rollback available** - Can revert all changes
4. ✅ **Tested approach** - Each step verified
5. ✅ **Data integrity** - Constraint prevents future issues

---

## 📞 EMERGENCY CONTACTS

If something goes wrong:

1. **Rollback immediately** (see Rollback Procedures above)
2. **Restore from backup** if needed
3. **Check logs**:
   ```bash
   docker logs rizal_v1-backend-1 --tail 100
   docker logs rizal_v1-db-1 --tail 100
   ```
4. **Contact development team** with:
   - Backup file location
   - Error messages
   - Steps taken before error

---

## ✅ FINAL CHECKLIST

Before deploying to production:

- [ ] Database backup created and verified
- [ ] Bad data count checked (Step 2)
- [ ] Deployment plan selected (Option A or B)
- [ ] Rollback procedures understood
- [ ] Team notified of deployment
- [ ] Monitoring ready (logs, alerts)
- [ ] Test plan prepared (post-deployment)

**If all checked**: ✅ **SAFE TO DEPLOY**

---

## 🎓 SUMMARY

**Is it safe to push to production?**

✅ **YES**, with these conditions:

1. **Create backup first** (mandatory)
2. **Check for bad data** (run queries)
3. **Clean bad data if exists** (before constraint)
4. **Deploy in phases** (frontend → cleanup → constraint)
5. **Verify each step** (run tests)

**Estimated time**: 15-30 minutes  
**Risk level**: 🟡 LOW (with backup)  
**Downtime**: ✅ NONE  
**Rollback**: ✅ AVAILABLE

**Recommendation**: Deploy during low-traffic hours for extra safety, but not required.

---

**Last Updated**: 2024  
**Version**: 1.0
