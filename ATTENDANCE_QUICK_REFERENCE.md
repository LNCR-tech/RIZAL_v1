# Attendance Logic - Quick Reference Guide

## 🚨 Quick Diagnosis

### Problem: "Students show sign-in but never attended"

**Check 1: Database**
```sql
SELECT id, student_id, time_in, method, status 
FROM attendance 
WHERE time_in IS NULL AND method IS NOT NULL 
LIMIT 5;
```
- **If returns rows**: Bad data exists → Run cleanup script
- **If returns 0**: Data is clean → Check frontend cache

**Check 2: Frontend**
```javascript
// Open browser console on attendance page
// Check network response
fetch('/api/events/1/attendees').then(r => r.json()).then(console.log)
// Look for records with time_in: null but method: "manual"
```
- **If method is "manual"**: Old frontend bug → Clear cache and refresh
- **If method is null**: Frontend is correct

**Check 3: Backend Logs**
```bash
docker logs rizal_v1-backend-1 | grep "Creating attendance"
```
- **If shows unexpected time_in**: Backend issue (unlikely)
- **If shows NULL correctly**: Backend is correct

---

## ✅ Expected Behavior

### Never Attended Student
```json
{
  "time_in": null,
  "time_out": null,
  "method": null,
  "status": "absent",
  "check_in_status": null,
  "check_out_status": null
}
```
**Display**: "No sign-in record" / "N/A"

### Attended Student
```json
{
  "time_in": "2024-01-15T08:30:00Z",
  "time_out": "2024-01-15T10:30:00Z",
  "method": "face_scan",
  "status": "present",
  "check_in_status": "present",
  "check_out_status": "present"
}
```
**Display**: Actual timestamps and method

---

## 🔧 Quick Fixes

### Fix 1: Clean Bad Data
```sql
UPDATE attendance 
SET method = NULL, check_in_status = NULL
WHERE time_in IS NULL AND method IS NOT NULL;
```

### Fix 2: Clear Frontend Cache
```bash
# In browser
Ctrl+Shift+R (Windows/Linux)
Cmd+Shift+R (Mac)
```

### Fix 3: Apply Database Constraint
```bash
docker exec -it rizal_v1-backend-1 alembic upgrade head
```

---

## 📊 Verification Queries

### Data Quality Summary
```sql
SELECT 
    CASE 
        WHEN time_in IS NULL AND method IS NULL THEN 'CORRECT'
        WHEN time_in IS NOT NULL AND method IS NOT NULL THEN 'CORRECT'
        WHEN time_in IS NULL AND method IS NOT NULL THEN 'ERROR'
        WHEN time_in IS NOT NULL AND method IS NULL THEN 'WARNING'
    END as status,
    COUNT(*) as count
FROM attendance
GROUP BY status;
```

### Find Problematic Events
```sql
SELECT 
    e.id,
    e.name,
    COUNT(*) as bad_records
FROM attendance a
JOIN event e ON a.event_id = e.id
WHERE a.time_in IS NULL AND a.method IS NOT NULL
GROUP BY e.id, e.name
ORDER BY bad_records DESC;
```

### Check Recent Attendance
```sql
SELECT 
    a.id,
    sp.student_id,
    e.name,
    a.time_in,
    a.method,
    a.status,
    a.created_at
FROM attendance a
JOIN student_profile sp ON a.student_id = sp.id
JOIN event e ON a.event_id = e.id
ORDER BY a.created_at DESC
LIMIT 20;
```

---

## 🎯 Root Cause Checklist

- [ ] **Historical data**: Records before NULL fix → Run cleanup
- [ ] **Manual edits**: Someone edited database → Apply constraint
- [ ] **Frontend cache**: Old cached data → Clear cache
- [ ] **Migration issue**: Constraint not applied → Run migration
- [ ] **Code regression**: Recent code change → Check git history

---

## 📞 Escalation Path

If issue persists after all fixes:

1. **Collect evidence**:
   ```bash
   # Database state
   docker exec -it rizal_v1-db-1 psql -U aura_user -d aura_db -c "
   SELECT * FROM attendance WHERE time_in IS NULL AND method IS NOT NULL LIMIT 5;
   " > bad_data.txt
   
   # Backend logs
   docker logs rizal_v1-backend-1 --tail 500 > backend.log
   
   # Frontend network logs
   # (Save from browser DevTools Network tab)
   ```

2. **Review audit report**: `ATTENDANCE_LOGIC_AUDIT_REPORT.md`

3. **Check fix summary**: `ATTENDANCE_LOGIC_FIX_SUMMARY.md`

4. **Contact development team** with evidence

---

## 🔍 Debug Commands

### Check Constraint Status
```sql
SELECT conname, pg_get_constraintdef(oid) 
FROM pg_constraint 
WHERE conrelid = 'attendance'::regclass;
```

### Test Constraint
```sql
-- Should FAIL
INSERT INTO attendance (student_id, event_id, time_in, method, status)
VALUES (1, 1, NULL, 'manual', 'absent');

-- Should SUCCEED
INSERT INTO attendance (student_id, event_id, time_in, method, status)
VALUES (1, 1, NULL, NULL, 'absent');
```

### Check Backend Version
```bash
docker exec -it rizal_v1-backend-1 ls -la app/services/attendance_validation.py
# Should exist if validation is deployed
```

### Check Frontend Version
```bash
docker exec -it rizal_v1-frontend-1 cat /usr/share/nginx/html/assets/*.js | grep "toOptionalString(attendance.method"
# Should show null, not 'manual'
```

---

## 📝 Quick Notes

- **NULL is correct**: Students who never signed in SHOULD have NULL time_in/method
- **Constraint prevents bad data**: Database rejects invalid records
- **Frontend preserves NULL**: No default values applied
- **Backend never auto-creates**: Only sign-in endpoints set time_in
- **Event status is computed**: Based on time windows, not manual override

---

**Last Updated**: 2024
**Version**: 1.0
