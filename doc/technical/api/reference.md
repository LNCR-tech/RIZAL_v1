# API Reference

> **Project:** Valid8 Attendance Recognition System
> **Last Updated:** 2026-03-28
>
> This guide outlines the most common API calls for frontend integration.

---

### Request/Response Pattern
- **Success**: All successful responses return JSON.
- **Errors**: Standard format: `{"detail": "Error message"}`.
- **Dates**: ISO 8601 (e.g., `2026-03-28T14:30:00Z`).
- **Headers**: `Authorization: Bearer <TOKEN>` (Required for all restricted paths).

---

## 🛡️ Authentication

### `POST /login`
Standard login endpoint.

**Request:**
```json
{
  "email": "user@school.edu",
  "password": "Password123"
}
```

**Success Response:**
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "email": "user@school.edu",
  "roles": ["student"],
  "user_id": 1,
  "school_id": 1,
  "must_change_password": false,
  "session_id": "uuid-string"
}
```

---

## 🏛️ Governance Hierarchy (`/api/governance-hierarchy/*`)

### `POST /api/governance-hierarchy/units`
**Role:** `Campus Admin`
Creates a new governance unit (SSG, SG, ORG).

**Body:**
```json
{
  "name": "College of Engineering SG",
  "unit_type": "SG",
  "parent_unit_id": 1, 
  "department_id": 4
}
```

### `GET /api/governance-hierarchy/units`
**Roles:** Any authenticated user. Returns units for your school.

### `POST /api/governance-hierarchy/units/{unit_id}/members`
**Role:** `Campus Admin`, `SSG`
Assigns a user to a governance unit.

**Body:**
```json
{
  "user_id": 25,
  "position_title": "Secretary General"
}
```

---

## 📅 Events Management (`/events/*`)

### `POST /events/`
**Roles:** `Campus Admin`, `SSG`, `SG`, `ORG` Officers.
Creates an event. Organization is assigned by the Campus Admin to these officers.

**Body:**
```json
{
  "name": "Freshman Orientation 2026",
  "start_datetime": "2026-08-15T09:00:00",
  "end_datetime": "2026-08-15T12:00:00",
  "location": "Main Auditorium",
  "early_check_in_minutes": 30,
  "late_threshold_minutes": 15,
  "auto_status_update": true,
  "department_ids": [1],
  "program_ids": []
}
```

---

## 📸 Attendance & Face Recognition

### `POST /attendance/face-scan`
**Roles:** Kiosk / Public Scanner
Records attendance via face matching.

**Body:**
```json
{
  "event_id": 101,
  "student_id": 505
}
```

### `POST /face/register`
**Roles:** `Student` (via profile) or Admin
Uploads face encoding for future recognition.
**Content-Type:** `multipart/form-data`
