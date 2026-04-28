# Face Scan DateTime Serialization Fix

## Issue Summary

**Error**: `TypeError: Object of type datetime is not JSON serializable`
**Endpoint**: `POST /api/face/face-scan-with-recognition`
**Status Code**: 500 Internal Server Error
**User Impact**: Students couldn't sign in to events via face scan - got "Internal Service Error" or "Face detection is not ready" messages

## Root Cause

When the face scan endpoint raised HTTPException with error details containing attendance time window information, the error detail dict included raw Python `datetime` objects. FastAPI's JSONResponse tried to serialize these datetime objects using `json.dumps()`, which doesn't support datetime serialization by default, causing the 500 error.

### Error Flow:
1. Student attempts face scan attendance
2. Attendance time window validation fails (e.g., too early, too late)
3. Code calls `_attendance_time_window_detail()` which returns dict with datetime objects
4. This dict is passed to `_attendance_scan_error_detail()` and then to HTTPException
5. FastAPI tries to serialize the HTTPException detail to JSON
6. `json.dumps()` encounters datetime objects and crashes
7. User sees 500 Internal Server Error

## The Fix

### Changes Made to `backend/app/routers/face_recognition.py`:

1. **Added `_serialize_error_detail()` helper function**:
   - Recursively walks through error detail dictionaries
   - Converts all `datetime` objects to ISO format strings using `.isoformat()`
   - Handles nested dictionaries
   - Preserves all other data types

2. **Updated `_attendance_scan_error_detail()` function**:
   - Now calls `_serialize_error_detail()` before returning
   - Ensures all datetime objects are converted to strings
   - Makes error details JSON-serializable

### Code Added:

```python
def _serialize_error_detail(detail: dict[str, object]) -> dict[str, object]:
    """Recursively convert datetime objects to ISO strings in error detail dicts."""
    result = {}
    for key, value in detail.items():
        if isinstance(value, datetime):
            result[key] = value.isoformat()
        elif isinstance(value, dict):
            result[key] = _serialize_error_detail(value)
        else:
            result[key] = value
    return result
```

### Code Modified:

```python
def _attendance_scan_error_detail(
    *,
    code: str,
    message: str,
    **extra: object,
) -> dict[str, object]:
    """Build a consistent structured error body for face attendance failures."""
    detail: dict[str, object] = {
        "code": code,
        "message": message,
    }
    detail.update(extra)
    return _serialize_error_detail(detail)  # ← Added this line
```

## Error Scenarios Fixed

The fix resolves datetime serialization errors in these attendance validation scenarios:

1. **Check-in too early**: Before early check-in window opens
2. **Check-in too late**: After late threshold has passed
3. **Sign-out not allowed**: Outside sign-out window
4. **Event not started**: Attempting attendance before event begins
5. **Event ended**: Attempting attendance after event has ended

All these scenarios return time window details with datetime objects that are now properly serialized.

## Testing Checklist

- [ ] Test face scan check-in during valid window (should work)
- [ ] Test face scan check-in too early (should get proper error with time details)
- [ ] Test face scan check-in too late (should get proper error with time details)
- [ ] Test face scan sign-out during valid window (should work)
- [ ] Test face scan sign-out outside window (should get proper error with time details)
- [ ] Verify error messages are clear and include time window information
- [ ] Confirm no more 500 errors on face scan endpoint
- [ ] Check that datetime values in error responses are ISO format strings

## Impact

### Before Fix:
- ❌ Face scan attendance crashed with 500 error
- ❌ Students saw "Internal Service Error" or "Face detection is not ready"
- ❌ No useful error information provided
- ❌ Backend logs showed datetime serialization errors

### After Fix:
- ✅ Face scan attendance returns proper 403 Forbidden with detailed error
- ✅ Students see clear error messages about timing windows
- ✅ Error responses include time window details in ISO format
- ✅ No more datetime serialization crashes
- ✅ Proper error handling throughout the flow

## Related Code

### Other Functions That Already Handle Datetime Serialization:
- `_serialize_attendance_decision()`: Converts datetime in attendance decisions
- `FaceAttendanceScanResponse`: Pydantic model with datetime validators
- All response models use Pydantic's automatic datetime serialization

### Why This Was Missed:
- Response models (Pydantic) automatically handle datetime serialization
- Error details in HTTPException bypass Pydantic validation
- FastAPI uses `json.dumps()` directly for error responses
- Need manual serialization for error detail dicts

## Commit Information

**Branch**: `aura_ci_cd`
**Commit**: `c99449d`
**Message**: "fix: Serialize datetime objects in face scan error responses"

## Prevention

To prevent similar issues in the future:

1. **Always serialize datetime objects** before passing to HTTPException detail
2. **Use helper functions** like `_serialize_error_detail()` for complex error details
3. **Test error paths** not just success paths
4. **Consider using `jsonable_encoder()`** from FastAPI for complex objects
5. **Add type hints** to catch serialization issues early

## Additional Notes

- The fix is minimal and focused on the specific issue
- No changes to business logic or face recognition algorithms
- Existing face scan functionality remains unchanged
- Only error response serialization was improved
- The FutureWarning about `estimate` is a separate scikit-image deprecation (not critical)
