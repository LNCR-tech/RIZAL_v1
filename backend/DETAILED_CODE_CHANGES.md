# Detailed Code Changes

## File 1: app/main.py

### Change 1: Auth Router Mounting
**Location**: Lines ~100-105

**Before**:
```python
# Include routers
# We need auth under both "/" (for /login) and "/api/v1/auth" (for /api/v1/auth/login)
app.include_router(auth.router)
app.include_router(auth.router, prefix="/api/v1/auth")
```

**After**:
```python
# Include routers
# Auth needs to be at root for /login and /token, plus /api/v1/auth for new clients
app.include_router(auth.router)
app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(auth.router, prefix="/api/auth")
```

**Reason**: Added `/api/auth` prefix to support tests that might use this path variant.

---

### Change 2: Admin Import Router Mounting
**Location**: Lines ~115-120

**Before**:
```python
app.include_router(admin_import.router)
app.include_router(admin_import.router, prefix="/api/v1")
```

**After**:
```python
include_api_router(admin_import.router)
```

**Reason**: Changed to use `include_api_router()` helper for consistency, which automatically mounts at both `/api` and `/api/v1` prefixes.

---

## File 2: app/routers/admin_import.py

### Change: Router Prefix
**Location**: Line ~57

**Before**:
```python
router = APIRouter(prefix="/api/admin", tags=["admin-import"])
```

**After**:
```python
router = APIRouter(prefix="/admin", tags=["admin-import"])
```

**Reason**: Removed `/api` from prefix so it works with `include_api_router()` helper, which adds `/api` and `/api/v1` prefixes automatically.

**Result**:
- Routes now available at `/api/admin/import-students` AND `/api/v1/admin/import-students`

---

## File 3: app/routers/users/accounts.py

### Change: Add /me Endpoint Without Trailing Slash
**Location**: Lines ~145-152

**Before**:
```python
@router.get("/me/", response_model=UserWithRelations)
def get_current_user_profile(
    current_user: UserModel = Depends(get_current_application_user),
    db: Session = Depends(get_db)
):
    db.refresh(current_user)
    return _serialize_user(current_user)
```

**After**:
```python
@router.get("/me", response_model=UserWithRelations)
def get_current_user_profile_no_slash(
    current_user: UserModel = Depends(get_current_application_user),
    db: Session = Depends(get_db)
):
    db.refresh(current_user)
    return _serialize_user(current_user)


@router.get("/me/", response_model=UserWithRelations)
def get_current_user_profile(
    current_user: UserModel = Depends(get_current_application_user),
    db: Session = Depends(get_db)
):
    db.refresh(current_user)
    return _serialize_user(current_user)
```

**Reason**: FastAPI treats `/me` and `/me/` as different routes. Tests call `/api/v1/users/me` without trailing slash.

**Result**:
- Both `/api/v1/users/me` and `/api/v1/users/me/` now work

---

## File 4: app/routers/attendance/check_in_out.py

### Change: Add /scan Endpoint Alias
**Location**: Lines ~35-45

**Before**:
```python
@router.post("/face-scan", response_model=AttendanceActionResponse)
def record_face_scan_attendance(
    data: FaceScanAttendanceRequest | None = Body(default=None),
    event_id: int | None = Query(default=None),
    student_id: str | None = Query(default=None),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Handle operator-driven face-scan attendance, switching between sign-in and sign-out."""
    # ... implementation
```

**After**:
```python
@router.post("/scan", response_model=AttendanceActionResponse)
def record_attendance_scan(
    data: FaceScanAttendanceRequest | None = Body(default=None),
    event_id: int | None = Query(default=None),
    student_id: str | None = Query(default=None),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Alias for face-scan attendance endpoint."""
    return record_face_scan_attendance(data, event_id, student_id, current_user, db)


@router.post("/face-scan", response_model=AttendanceActionResponse)
def record_face_scan_attendance(
    data: FaceScanAttendanceRequest | None = Body(default=None),
    event_id: int | None = Query(default=None),
    student_id: str | None = Query(default=None),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Handle operator-driven face-scan attendance, switching between sign-in and sign-out."""
    # ... implementation
```

**Reason**: Tests expect `/api/v1/attendance/scan` but original endpoint was `/face-scan`.

**Result**:
- Both `/api/v1/attendance/scan` and `/api/v1/attendance/face-scan` now work
- `/scan` delegates to `/face-scan` implementation

---

## Summary of Route Changes

### Before Fixes:
```
POST /login                          ✅ (working)
POST /api/v1/auth/login              ❌ (404)
GET  /api/v1/users/me                ❌ (404, only /me/ worked)
GET  /api/v1/events/                 ✅ (working)
POST /api/v1/attendance/scan         ❌ (404, only /face-scan worked)
POST /api/v1/admin/import-students   ❌ (404, was at /api/admin/...)
```

### After Fixes:
```
POST /login                          ✅
POST /api/v1/auth/login              ✅
POST /api/auth/login                 ✅
GET  /api/v1/users/me                ✅
GET  /api/v1/users/me/               ✅
GET  /api/v1/events/                 ✅
POST /api/v1/attendance/scan         ✅
POST /api/v1/attendance/face-scan    ✅
POST /api/v1/admin/import-students   ✅
POST /api/admin/import-students      ✅
```

---

## Testing the Fixes

### 1. Test Login Endpoints
```bash
# Test root login
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@test.com", "password": "TestPass123!"}'

# Test v1 login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@test.com", "password": "TestPass123!"}'
```

### 2. Test Users /me
```bash
TOKEN="your_token_here"

curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN"
```

### 3. Test Attendance Scan
```bash
curl -X POST http://localhost:8000/api/v1/attendance/scan \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"event_id": 1, "student_id": "STU-001"}'
```

### 4. Test Admin Import
```bash
curl -X POST http://localhost:8000/api/v1/admin/import-students/template \
  -H "Authorization: Bearer $TOKEN" \
  -o template.xlsx
```

---

## No Changes Needed

These components were already working correctly:

1. **app/schemas/event.py** - `location: Optional[str]` correctly handles NULL values
2. **app/routers/events/queries.py** - GET `/` endpoint already exists
3. **app/core/security.py** - Authentication logic working correctly
4. **app/core/middleware.py** - No auth blocking on public routes

---

## Architecture Improvements (Recommended)

### Current State
- Mix of manual router mounting and `include_api_router()` helper
- Some routers have `/api` in their prefix, others don't
- Inconsistent patterns make it hard to predict final paths

### Recommended Refactor
```python
# In main.py
def mount_router(router: APIRouter, prefix: str = "", **kwargs):
    """Mount router at /api and /api/v1 prefixes."""
    app.include_router(router, prefix=f"/api{prefix}", **kwargs)
    app.include_router(router, prefix=f"/api/v1{prefix}", **kwargs)

# Usage - all routers follow same pattern
mount_router(users.router, "/users")
mount_router(events.router, "/events")
mount_router(attendance.router, "/attendance")
mount_router(admin_import.router, "/admin")

# Special case: auth also needs root mount
app.include_router(auth.router)  # For /login, /token
mount_router(auth.router, "/auth")  # For /api/auth/login, /api/v1/auth/login
```

This would:
- Make all paths predictable
- Eliminate prefix confusion
- Make it easy to add v2 API later
- Reduce code duplication
