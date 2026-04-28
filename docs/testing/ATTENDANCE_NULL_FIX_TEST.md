# Attendance NULL Value Fix - Test Plan

## Changes Made

### Backend Changes

1. **`backend/app/services/event_attendance_service.py`**
   - Changed `method="manual"` to `method=None` for absent students who never signed in
   - Ensures NULL values are preserved for time_in, time_out, method, check_in_status, check_out_status

2. **`backend/app/routers/attendance/overrides.py`**
   - Fixed `mark_excused_attendance` to set NULL values for all time/method fields
   - Added explicit NULL assignments for time_in, time_out, method, check_in_status, check_out_status

### Frontend Changes

3. **`frontend/src/services/attendanceFlow.js`**
   - Added `formatMethodDisplay()` helper to show "N/A" when method is NULL
   - Updated `resolveAttendanceActionState()` to handle NULL time_in properly
   - Updated `resolveAttendanceDisplayStatus()` to show empty string for students with no time_in (unless finalized as absent/excused)
   - Existing helpers already handle NULL: `formatTimeInDisplay()`, `formatTimeOutDisplay()`, `formatDurationDisplay()`

## Test Scenario

### Setup
1. Create event "Test ni Gab" with multiple students (e.g., Gab, Student2, Student3)
2. Event should be in ongoing state (check-in window open)

### Test Steps

#### Step 1: Initial State (Before Any Sign-In)
**Action**: View event attendance list

**Expected Results**:
- All students show "No record yet" or empty status
- No attendance records in database yet
- No time_in, time_out, or method values

**Database Query**:
```sql
SELECT 
    sp.student_id,
    a.time_in,
    a.time_out,
    a.method,
    a.status,
    a.check_in_status,
    a.check_out_status
FROM attendance a
JOIN student_profile sp ON a.student_id = sp.id
JOIN event e ON a.event_id = e.id
WHERE e.name = 'Test ni Gab'
ORDER BY sp.student_id;
```

**Expected**: No rows returned (no attendance records yet)

#### Step 2: Gab Signs In
**Action**: Gab performs face scan or manual check-in

**Expected Results**:
- Gab shows "Checked in" or "Waiting for sign out"
- Gab has actual time_in timestamp
- Gab has method = "face_scan" or "manual"
- Other students still show "No record yet"
- Other students have NO attendance records

**Database Query**: Same as above

**Expected**:
```
student_id | time_in              | time_out | method     | status  | check_in_status | check_out_status
-----------|----------------------|----------|------------|---------|-----------------|------------------
gab123     | 2024-01-15 10:30:00 | NULL     | face_scan  | present | present         | NULL
```

**Critical**: Student2 and Student3 should NOT appear in results

#### Step 3: Event Ends (Finalization)
**Action**: Event status changes to "completed" and finalize_completed_event_attendance runs

**Expected Results**:
- Gab shows "Absent" (no sign-out recorded)
- Gab still has time_in, method stays "face_scan"
- Gab time_out remains NULL
- Student2 and Student3 now show "Absent"
- Student2 and Student3 have attendance records created
- Student2 and Student3 have NULL time_in, NULL time_out, NULL method

**Database Query**: Same as above

**Expected**:
```
student_id | time_in              | time_out | method     | status | check_in_status | check_out_status
-----------|----------------------|----------|------------|--------|-----------------|------------------
gab123     | 2024-01-15 10:30:00 | NULL     | face_scan  | absent | present         | NULL
student2   | NULL                 | NULL     | NULL       | absent | NULL            | NULL
student3   | NULL                 | NULL     | NULL       | absent | NULL            | NULL
```

#### Step 4: Frontend Display Verification
**Action**: View attendance table in admin panel

**Expected Display**:

| Student ID | Time In            | Time Out           | Duration | Method    | Status |
|------------|--------------------|--------------------|----------|-----------|--------|
| gab123     | 10:30 AM          | No sign-out record | N/A      | face_scan | Absent |
| student2   | No sign-in record | No sign-out record | N/A      | N/A       | Absent |
| student3   | No sign-in record | No sign-out record | N/A      | N/A       | Absent |

**Critical Checks**:
- ✅ Gab shows actual time_in
- ✅ Gab shows actual method
- ✅ Student2/Student3 show "No sign-in record"
- ✅ Student2/Student3 show "N/A" for method
- ✅ Student2/Student3 do NOT show same timestamp as Gab
- ✅ Student2/Student3 do NOT show "Manual" method

## Additional Test Cases

### Test Case: Mark Excused
**Action**: Mark Student2 as excused before event ends

**Expected**:
```sql
student_id | time_in | time_out | method | status  | check_in_status | check_out_status
-----------|---------|----------|--------|---------|-----------------|------------------
student2   | NULL    | NULL     | NULL   | excused | NULL            | NULL
```

**Display**: 
- Time In: "No sign-in record"
- Time Out: "No sign-out record"
- Method: "N/A"
- Status: "Excused"

### Test Case: Complete Sign-In and Sign-Out
**Action**: Student3 signs in and signs out properly

**Expected**:
```sql
student_id | time_in              | time_out             | method     | status  | check_in_status | check_out_status
-----------|----------------------|----------------------|------------|---------|-----------------|------------------
student3   | 2024-01-15 10:35:00 | 2024-01-15 12:00:00 | face_scan  | present | present         | present
```

**Display**:
- Time In: "10:35 AM"
- Time Out: "12:00 PM"
- Duration: "1h 25m"
- Method: "face_scan"
- Status: "Present"

## Validation Checklist

- [ ] Backend: method=None for students who never signed in
- [ ] Backend: time_in=None for students who never signed in
- [ ] Backend: time_out=None for students who never signed out
- [ ] Backend: check_in_status=None when no sign-in
- [ ] Backend: check_out_status=None when no sign-out
- [ ] Frontend: "No sign-in record" displayed when time_in is NULL
- [ ] Frontend: "No sign-out record" displayed when time_out is NULL
- [ ] Frontend: "N/A" displayed when method is NULL
- [ ] Frontend: "N/A" displayed when duration cannot be calculated
- [ ] Frontend: No fake timestamps shown
- [ ] Frontend: Students without sign-in don't show "Manual" method
- [ ] Frontend: Event cards show correct action state for students with no time_in

## Files Changed

### Backend
- `backend/app/services/event_attendance_service.py`
- `backend/app/routers/attendance/overrides.py`

### Frontend
- `frontend/src/services/attendanceFlow.js`

## Deployment Notes

1. No database migration needed (columns already support NULL)
2. Existing data with method="manual" and NULL time_in should be cleaned up:
   ```sql
   UPDATE attendance 
   SET method = NULL 
   WHERE time_in IS NULL AND method = 'manual';
   ```
3. Test on staging before production
4. Monitor logs for any NULL-related errors after deployment
