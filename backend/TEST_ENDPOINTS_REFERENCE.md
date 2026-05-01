# Test Endpoint Quick Reference

## Authentication Endpoints

### POST /api/v1/auth/login
**Expected**: 200 with valid credentials  
**Returns**: `{"access_token": "...", "token_type": "bearer", ...}`  
**Status**: ✅ FIXED

### POST /login
**Expected**: 200 with valid credentials (legacy path)  
**Returns**: Same as above  
**Status**: ✅ FIXED

### POST /token
**Expected**: 200 with OAuth2 form data  
**Returns**: Same as above  
**Status**: ✅ Already working

---

## User Endpoints

### GET /api/v1/users/me
**Expected**: 200 with valid token  
**Returns**: 
```json
{
  "id": 1,
  "email": "user@test.com",
  "first_name": "Test",
  "last_name": "User",
  "roles": [{"code": "admin", "display_name": "Admin"}]
}
```
**Status**: ✅ FIXED

### GET /api/v1/users/
**Expected**: 200 for admin/campus_admin, 403 for others  
**Returns**: List of users  
**Status**: ✅ Already working

---

## Event Endpoints

### GET /api/v1/events/
**Expected**: 200 for authenticated users  
**Returns**: List of events or `{"items": [...], "total": N}`  
**Status**: ✅ Already working

### POST /api/v1/events/
**Expected**: 
- 200/201 for admin/campus_admin with valid payload
- 422 for admin/campus_admin with invalid payload
- 403 for student
**Status**: ✅ Already working

---

## Attendance Endpoints

### POST /api/v1/attendance/scan
**Expected**: 200 for valid scan, 400/409 for duplicate  
**Payload**: 
```json
{
  "event_id": 1,
  "student_id": "STU-001"
}
```
**Status**: ✅ FIXED

### POST /api/v1/attendance/face-scan
**Expected**: Same as /scan (original endpoint)  
**Status**: ✅ Already working

---

## Admin Import Endpoints

### POST /api/v1/admin/import-students
**Expected**: 200 for admin/campus_admin with valid file  
**Payload**: multipart/form-data with `file` field  
**Returns**: `{"job_id": "...", "status": "pending"}`  
**Status**: ✅ FIXED

### GET /api/v1/admin/import-students/template
**Expected**: 200, returns Excel file  
**Status**: ✅ FIXED

---

## Public Endpoints

### GET /health
**Expected**: 200 for everyone (no auth required)  
**Returns**: `{"status": "healthy"}`  
**Status**: ✅ Already working

---

## RBAC Matrix Expected Behavior

| Route | Method | Role | Expected Status |
|-------|--------|------|----------------|
| /health | GET | unauthenticated | 200 |
| /api/v1/auth/login | POST | unauthenticated | 422 (no payload) |
| /api/v1/schools/ | GET | admin | 200 |
| /api/v1/schools/ | GET | campus_admin | 403 |
| /api/v1/schools/ | GET | student | 403 |
| /api/v1/schools/ | GET | unauthenticated | 401 |
| /api/v1/users/ | GET | admin | 200 |
| /api/v1/users/ | GET | campus_admin | 200 |
| /api/v1/users/ | GET | ssg | 403 |
| /api/v1/users/ | GET | student | 403 |
| /api/v1/events/ | POST | admin | 200 or 422 |
| /api/v1/events/ | POST | campus_admin | 422 (allowed) |
| /api/v1/events/ | POST | student | 403 |
| /api/v1/users/me | GET | student | 200 |
| /api/v1/users/me | GET | unauthenticated | 401 |

**Note**: 422 is acceptable for "allowed but bad payload" to differentiate from 403 "forbidden"

---

## Common Test Patterns

### Token Fixtures (conftest.py)
```python
@pytest.fixture(scope="session")
def admin_token(client):
    r = client.post("/login", json={"email": "admin@test.com", "password": "TestPass123!"})
    assert r.status_code == 200
    return r.json()["access_token"]
```

### Using Tokens in Tests
```python
def test_protected_route(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    r = client.get("/api/v1/users/", headers=headers)
    assert r.status_code == 200
```

### Testing RBAC
```python
# Expect 403 for insufficient role
r = client.get("/api/v1/schools/", headers=student_headers)
assert r.status_code == 403

# Expect 401 for no auth
r = client.get("/api/v1/users/")
assert r.status_code == 401

# Expect 200 for correct role
r = client.get("/api/v1/users/", headers=admin_headers)
assert r.status_code == 200
```

---

## Debugging Tips

### Check Route Registration
```python
# In main.py or test file
for route in app.routes:
    print(f"{route.methods} {route.path}")
```

### Check Token Contents
```python
import jwt
token_data = jwt.decode(token, options={"verify_signature": False})
print(token_data)
```

### Check Database State
```python
# In test
def test_debug_users(db_session):
    from app.models.user import User
    users = db_session.query(User).all()
    for u in users:
        print(f"{u.email} - roles: {[r.role.code for r in u.roles]}")
```

---

## Next Steps

1. **Start PostgreSQL** with correct credentials
2. **Run seed script** to populate test data
3. **Run tests** in order:
   ```bash
   pytest tests/test_auth.py -xvs
   pytest tests/test_api_contract.py -xvs
   pytest tests/test_rbac_matrix.py -xvs
   pytest tests/test_events.py -xvs
   pytest tests/test_attendance_logic.py -xvs
   pytest tests/test_bulk_import.py -xvs
   ```
4. **Check coverage**:
   ```bash
   pytest tests/ --cov=app --cov-report=html
   ```
