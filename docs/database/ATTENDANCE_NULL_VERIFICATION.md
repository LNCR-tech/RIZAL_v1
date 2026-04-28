# Database Verification and Cleanup for Attendance NULL Values

## 1. Check for Bad Data (NULL time_in with non-NULL method)

```sql
-- Find attendance records where student never signed in but has a method
SELECT 
    a.id,
    sp.student_id,
    sp.first_name,
    sp.last_name,
    e.name as event_name,
    a.time_in,
    a.time_out,
    a.method,
    a.status,
    a.check_in_status,
    a.check_out_status,
    a.created_at
FROM attendance a
JOIN student_profile sp ON a.student_id = sp.id
JOIN event e ON a.event_id = e.id
WHERE a.time_in IS NULL 
  AND a.method IS NOT NULL
ORDER BY a.created_at DESC;
```

## 2. Cleanup Script (Run ONLY if bad data exists)

```sql
-- Fix: Set method to NULL where time_in is NULL
UPDATE attendance 
SET method = NULL,
    check_in_status = NULL
WHERE time_in IS NULL 
  AND method IS NOT NULL;
```

## 3. Verify Correct Data Structure

```sql
SELECT 
    CASE 
        WHEN time_in IS NULL AND method IS NULL THEN 'CORRECT: No sign-in, no method'
        WHEN time_in IS NOT NULL AND method IS NOT NULL THEN 'CORRECT: Signed in with method'
        WHEN time_in IS NULL AND method IS NOT NULL THEN 'ERROR: No sign-in but has method'
        WHEN time_in IS NOT NULL AND method IS NULL THEN 'WARNING: Signed in but no method'
    END as data_status,
    COUNT(*) as count
FROM attendance
GROUP BY data_status
ORDER BY count DESC;
```

## How to Run

```bash
# Connect to database
docker exec -it rizal_v1-db-1 psql -U aura_user -d aura_db

# Run verification query (section 1)
# If bad data found, run cleanup (section 2)
# Verify fix (section 3)

# Exit
\q
```

## Expected Results After Fix

Students who never signed in:
- `time_in` = NULL
- `time_out` = NULL  
- `method` = NULL
- `check_in_status` = NULL
- `check_out_status` = NULL
- `status` = 'absent' or 'excused'

Students who signed in:
- `time_in` = actual timestamp
- `method` = 'face_scan', 'manual', etc.
- `check_in_status` = 'present', 'late', etc.
