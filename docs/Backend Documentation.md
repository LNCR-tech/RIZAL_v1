# RIZAL v1 Backend API Documentation

Complete reference for all API endpoints. Intended for frontend developers integrating with the backend.

---

## Table of Contents

1. [Base URL & Headers](#base-url--headers)
2. [Authentication](#authentication)
3. [Roles & Permissions](#roles--permissions)
4. [Rate Limiting](#rate-limiting)
5. [Pagination](#pagination)
6. [Health](#health)
7. [Authentication Endpoints](#authentication-endpoints)
8. [School Management](#school-management)
9. [User Management](#user-management)
10. [Student Management](#student-management)
11. [Departments](#departments)
12. [Programs](#programs)
13. [Events](#events)
14. [Attendance](#attendance)
15. [Face Recognition](#face-recognition)
16. [Public Attendance Kiosk](#public-attendance-kiosk)
17. [Governance Hierarchy](#governance-hierarchy)
18. [Sanctions](#sanctions)
19. [Notifications](#notifications)
20. [Data Governance](#data-governance)
21. [Bulk Import](#bulk-import)
22. [Audit Logs](#audit-logs)
23. [Common Schemas](#common-schemas)

---

## Base URL & Headers

All requests are sent to the backend server. Include this header on every authenticated request:

```
Authorization: Bearer <access_token>
Content-Type: application/json
```

For file uploads use `Content-Type: multipart/form-data`.

---

## Authentication

### Login Flow

1. POST `/login` with email + password → get `access_token`
2. Include `Authorization: Bearer <token>` on every subsequent request
3. Token contains: `email`, `roles`, `school_id`, `user_id`, `must_change_password`, `face_verification_required`, `face_reference_enrolled`

### Password Change Gate

If `must_change_password = true` in the token response, the user **cannot access any endpoint** until they change their password via `POST /auth/change-password`. Only these endpoints are exempt:
- `POST /auth/change-password`
- `POST /auth/password-change-prompt/dismiss`
- `GET /health`

### Face Verification Gate

If `face_verification_required = true` and `face_reference_enrolled = false`, the user cannot access most endpoints until they complete face registration.

---

## Roles & Permissions

| Role | Access Level |
|------|-------------|
| `admin` | Platform-wide superuser. Full access to all schools. |
| `campus_admin` | School-level admin. Manages one school. Also called "school_IT". |
| `student` | Student user. Can only access their own data, attendance, events. |
| `ssg` | Student Supreme Government. School-wide governance. |
| `sg` | Student Government. Department-level governance. |
| `org` | Student Organization. Course/program-level governance. |

---

## Rate Limiting

When rate limited, the response is:

```json
{
  "code": "rate_limit_exceeded",
  "message": "Too many requests",
  "limit": 10,
  "window_seconds": 300,
  "retry_after_seconds": 240
}
```

HTTP status: `429 Too Many Requests`

| Endpoint group | Default limit |
|----------------|--------------|
| Login | 10 per 5 minutes per IP:email |
| Forgot password | 5 per 5 minutes per IP:email |
| Face endpoints | 80 per 60 seconds per user |
| Public endpoints | 120 per 60 seconds per IP |
| Authenticated mutations | 120 per 60 seconds per user |

---

## Pagination

Most list endpoints use **offset-based pagination** via two query parameters:

| Param | Type | Default | Max | Description |
|-------|------|---------|-----|-------------|
| `skip` | int | `0` | — | Number of records to skip (offset) |
| `limit` | int | `100` | varies | Max records to return per page |

### How to paginate

**Page 1 (first 50):**
```
GET /events/?skip=0&limit=50
```

**Page 2 (next 50):**
```
GET /events/?skip=50&limit=50
```

**Page 3 (next 50):**
```
GET /events/?skip=100&limit=50
```

### Response formats

Most list endpoints return a **plain JSON array**:
```json
[ { ...item... }, { ...item... } ]
```

The **Sanctions** endpoint (`GET /sanctions/events/{event_id}/students`) returns a **paginated wrapper** that includes the total count:
```json
{
  "total": 85,
  "items": [ { ...item... }, { ...item... } ],
  "skip": 0,
  "limit": 50
}
```

Use `total` to calculate total pages: `total_pages = ceil(total / limit)`.

### Limits per endpoint

| Endpoint | Default limit | Max limit |
|----------|--------------|-----------|
| `GET /events/` | 100 | 1000 |
| `GET /events/ongoing` | 100 | 1000 |
| `GET /api/users/` | 100 | 500 |
| `GET /api/users/by-role/{role}` | 100 | 500 |
| `GET /departments/` | 100 | 1000 |
| `GET /programs/` | 100 | 1000 |
| `GET /attendance/students/me` | 100 | — |
| `GET /sanctions/events/{id}/students` | 50 | 250 |
| `GET /api/governance/students` | — | 250 |
| `GET /api/governance/students/search` | 20 | 50 |
| `GET /api/governance/announcements/monitor` | 100 | 250 |
| `GET /api/notifications/logs` | 100 | 500 |
| `GET /api/audit-logs` | 50 | 500 |
| `GET /api/governance/requests` | 100 | 500 |

---

## Health

### GET `/health`

No auth required. Returns backend readiness.

**Response 200:**
```json
{
  "status": "ok",
  "timestamp": "2024-01-01T00:00:00Z",
  "database": { "ok": true, "detail": null },
  "face_runtime": { "ready": true, "state": "ready", "reason": null, "provider": "insightface" },
  "readiness": "ready",
  "pool": { "size": 10, "checked_out": 1 }
}
```

Returns `503` if the database or face runtime is degraded.

### GET `/health/readiness`

Kubernetes-style readiness probe. Returns `200` if ready, `503` if not.

---

## Authentication Endpoints

### POST `/token`

OAuth2-compatible token endpoint (used by Swagger UI / API clients that follow the OAuth2 standard).

**Request (form data):**
```
username=student@school.edu
password=secretpassword
remember_me=false
```

**Response 200:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "email": "student@school.edu",
  "roles": ["student"],
  "user_id": 42,
  "school_id": 1,
  "school_name": "Example University",
  "school_code": "EU-001",
  "logo_url": "https://...",
  "primary_color": "#162F65",
  "secondary_color": "#2C5F9E",
  "must_change_password": false,
  "face_verification_required": false,
  "face_reference_enrolled": true,
  "face_verification_pending": false
}
```

**Errors:**
- `401` — Invalid credentials
- `403` — Account inactive
- `429` — Rate limited

---

### POST `/login`

Extended login endpoint. Preferred for mobile and web frontends.

**Request body:**
```json
{
  "email": "student@school.edu",
  "password": "secretpassword",
  "remember_me": false
}
```

**Response:** Same as `/token` above.

---

### POST `/auth/google`

Login with a Google ID token (Google Sign-In).

**Request body:**
```json
{
  "id_token": "<google_id_token>"
}
```

**Response:** Same as `/token` above.

**Errors:**
- `403` — Google login is disabled for this school
- `401` — Token invalid or unverified
- `404` — No account registered with that Google email

---

### POST `/auth/change-password`

Change your own password. Clears `must_change_password` flag.

**Auth:** Any authenticated user

**Request body:**
```json
{
  "current_password": "old_password",
  "new_password": "new_secure_password"
}
```

**Response 200:**
```json
{ "message": "Password changed successfully" }
```

---

### POST `/auth/password-change-prompt/dismiss`

Dismiss the password change reminder without changing it. Clears `should_prompt_password_change`.

**Auth:** Any authenticated user

**Response 200:**
```json
{ "message": "Password change prompt dismissed" }
```

---

### POST `/auth/forgot-password`

Request a password reset. An admin must approve it.

**Request body:**
```json
{
  "email": "student@school.edu"
}
```

**Response 200** (always returns success to prevent email enumeration):
```json
{
  "message": "If an account with that email exists, a password reset request has been submitted for approval."
}
```

---

### GET `/auth/password-reset-requests`

List pending password reset requests awaiting approval.

**Auth:** `admin` or `campus_admin`

**Response 200:**
```json
[
  {
    "id": 1,
    "user_id": 42,
    "email": "student@school.edu",
    "first_name": "Juan",
    "last_name": "Dela Cruz",
    "roles": ["student"],
    "status": "pending",
    "requested_at": "2024-01-01T10:00:00Z"
  }
]
```

---

### POST `/auth/password-reset-requests/{request_id}/approve`

Approve a password reset request. Generates a temporary password and emails it.

**Auth:** `admin` or `campus_admin`

**Path param:** `request_id` — integer ID from the list above

**Response 200:**
```json
{
  "id": 1,
  "user_id": 42,
  "status": "approved",
  "resolved_at": "2024-01-01T10:05:00Z",
  "message": "Password reset approved. Temporary password sent to student@school.edu."
}
```

**Errors:**
- `403` — Campus Admin trying to approve their own account or another admin
- `404` — Request not found

---

## School Management

### POST `/api/school/create`

Create a new school. Platform admin only.

**Auth:** `admin`

**Request (multipart form):**
```
school_name=Example University
primary_color=#162F65
secondary_color=#2C5F9E    (optional)
school_code=EU-001          (optional)
logo=<file>                 (optional, image file)
```

**Response 201:**
```json
{
  "school_id": 1,
  "school_name": "Example University",
  "school_code": "EU-001",
  "logo_url": null,
  "primary_color": "#162F65",
  "secondary_color": "#2C5F9E",
  "accent_color": null,
  "subscription_status": "trial",
  "active_status": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

---

### POST `/api/school/admin/create-school-it`

Create a school and its Campus Admin account in one call.

**Auth:** `admin`

**Request (multipart form):**
```
school_name=Example University
primary_color=#162F65
school_it_email=admin@example.edu
school_it_first_name=Maria
school_it_last_name=Santos
school_it_password=<optional, auto-generated if omitted>
logo=<file>  (optional)
```

**Response 201:**
```json
{
  "school": { ...SchoolBrandingResponse... },
  "school_it_user_id": 5,
  "school_it_email": "admin@example.edu",
  "generated_temporary_password": "<auto_generated>"
}
```

> If `school_it_password` is omitted, `generated_temporary_password` contains the auto-generated one. If you provided a password, this field is `null`. The Campus Admin will have `must_change_password = true`.

---

### GET `/api/school/admin/list`

List all schools.

**Auth:** `admin`

**Response 200:**
```json
[
  {
    "school_id": 1,
    "school_name": "Example University",
    "school_code": "EU-001",
    "subscription_status": "trial",
    "active_status": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

---

### GET `/api/school/me`

Get the school of the currently logged-in user.

**Auth:** Any authenticated user

**Response 200:** `SchoolBrandingResponse`

---

### GET `/api/school/{school_id}`

Get a specific school by ID.

**Auth:** Any authenticated user (Campus Admin can only access their own school)

**Response 200:** `SchoolBrandingResponse`

---

### PUT `/api/school/update`

Update the current school's settings (branding, event defaults).

**Auth:** `campus_admin`

**Request (multipart form, all fields optional):**
```
school_name=Updated Name
primary_color=#123456
secondary_color=#654321
school_code=EU-002
logo=<file>
event_default_early_check_in_minutes=30
event_default_late_threshold_minutes=15
event_default_sign_out_grace_minutes=60
```

**Response 200:** `SchoolBrandingResponse`

---

### PATCH `/api/school/admin/{school_id}/status`

Update a school's active/subscription status.

**Auth:** `admin`

**Request body:**
```json
{
  "active_status": true,
  "subscription_status": "active"
}
```

**Response 200:** `SchoolBrandingResponse`

---

### GET `/api/school/admin/school-it-accounts`

List all Campus Admin accounts across all schools.

**Auth:** `admin`

**Response 200:**
```json
[
  {
    "user_id": 5,
    "email": "admin@example.edu",
    "first_name": "Maria",
    "last_name": "Santos",
    "school_id": 1,
    "school_name": "Example University",
    "is_active": true
  }
]
```

---

### PATCH `/api/school/admin/school-it-accounts/{user_id}/status`

Activate or deactivate a Campus Admin account.

**Auth:** `admin`

**Request body:**
```json
{ "is_active": false }
```

**Response 200:** `SchoolITAccountResponse`

---

### POST `/api/school/admin/school-it-accounts/{user_id}/reset-password`

Reset a Campus Admin's password. Generates a new temporary password.

**Auth:** `admin`

**Response 200:**
```json
{
  "user_id": 5,
  "email": "admin@example.edu",
  "temporary_password": "<auto_generated>",
  "must_change_password": true
}
```

---

## User Management

### POST `/api/users/`

Create a new user account.

**Auth:** `admin` or `campus_admin`

**Request body:**
```json
{
  "email": "juan@school.edu",
  "password": "optional_password",
  "first_name": "Juan",
  "middle_name": "Antonio",
  "last_name": "Dela Cruz",
  "roles": ["student"]
}
```

> **Roles:** `admin`, `campus_admin`, `student`, `ssg`, `sg`, `org`
>
> If `password` is omitted, one is auto-generated. The user will have `must_change_password = true`.

**Response 201:**
```json
{
  "id": 42,
  "email": "juan@school.edu",
  "roles": ["student"],
  "school_id": 1,
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "generated_temporary_password": "Abcd1234xyz"
}
```

---

### GET `/api/users/`

List all users in the school.

**Auth:** `admin` or `campus_admin`

**Query params:**
- `skip` (int, default 0) — pagination offset
- `limit` (int, default 100, max 500)

**Response 200:** List of `UserWithRelations`

---

### GET `/api/users/by-role/{role_name}`

List users filtered by role.

**Auth:** `admin` or `campus_admin`

**Path param:** `role_name` — one of: `admin`, `campus_admin`, `student`, `ssg`, `sg`, `org`

**Query params:** `skip`, `limit`

**Response 200:** List of `UserWithRelations`

---

### GET `/api/users/me`

Get the current authenticated user's profile.

**Auth:** Any authenticated user

**Response 200:** `UserWithRelations`

```json
{
  "id": 42,
  "email": "juan@school.edu",
  "first_name": "Juan",
  "middle_name": "Antonio",
  "last_name": "Dela Cruz",
  "roles": ["student"],
  "school_id": 1,
  "is_active": true,
  "face_scan_bypass_enabled": false,
  "created_at": "2024-01-01T00:00:00Z",
  "student_profile": {
    "id": 10,
    "student_id": "CS-2023-001",
    "department_id": 2,
    "program_id": 3,
    "year_level": 2,
    "student_status": "ACTIVE",
    "promotion_locked": false,
    "is_face_registered": false,
    "registration_complete": false
  }
}
```

---

### PATCH `/api/users/{user_id}`

Update user name/email. A user can edit their own account; admins can edit anyone.

**Auth:** Any authenticated user (self), or `admin`/`campus_admin` (any user in school)

**Request body (all optional):**
```json
{
  "email": "new@school.edu",
  "first_name": "Juan",
  "middle_name": "B",
  "last_name": "Cruz"
}
```

**Response 200:** `UserWithRelations`

---

### PATCH `/api/users/{user_id}/password`

Update another user's password (admin operation).

**Auth:** `admin` or `campus_admin`

**Request body:**
```json
{ "password": "newpassword123" }
```

**Response 200:**
```json
{ "message": "Password updated successfully" }
```

---

### PATCH `/api/users/{user_id}/roles`

Update a user's roles.

**Auth:** `admin` or `campus_admin`

**Request body:**
```json
{ "roles": ["student", "ssg"] }
```

**Response 200:** `UserWithRelations`

---

### PATCH `/api/users/{user_id}/activate`

Activate a user account.

**Auth:** `admin` or `campus_admin`

**Response 200:** `UserWithRelations`

---

### PATCH `/api/users/{user_id}/deactivate`

Deactivate a user account.

**Auth:** `admin` or `campus_admin`

**Response 200:** `UserWithRelations`

---

## Student Management

### POST `/api/users/students`

Create a student account with profile in one request.

**Auth:** `admin` or `campus_admin`

**Request body:**
```json
{
  "email": "juan@school.edu",
  "first_name": "Juan",
  "middle_name": "A",
  "last_name": "Dela Cruz",
  "student_id": "CS-2023-001",
  "department_id": 2,
  "program_id": 3,
  "year_level": 1,
  "student_status": "ACTIVE",
  "promotion_locked": false
}
```

> **student_status values:** `ACTIVE`, `GRADUATED`, `INACTIVE`, `TRANSFERRED`, `ARCHIVED`
>
> **year_level:** 1 to 5
>
> A temporary password is auto-generated. It will be in `generated_temporary_password`.

**Response 201:** `UserCreateResponse` including `student_profile`

---

### GET `/api/users/{user_id}/student-profile`

Get a student's profile.

**Auth:** Any authenticated user

**Response 200:** `StudentProfile`

---

### POST `/api/users/{user_id}/student-profile`

Create a student profile for an existing user.

**Auth:** `admin` or `campus_admin`

**Request body:**
```json
{
  "student_id": "CS-2023-001",
  "department_id": 2,
  "program_id": 3,
  "year_level": 1,
  "student_status": "ACTIVE",
  "promotion_locked": false
}
```

**Response 201:** `StudentProfile`

---

### PATCH `/api/users/{user_id}/student-profile`

Update a student's profile.

**Auth:** `admin` or `campus_admin`

**Request body:** Same fields as create, all optional.

**Response 200:** `StudentProfile`

---

## Departments

### POST `/departments/`

Create a department.

**Auth:** `campus_admin`

**Request body:**
```json
{ "name": "College of Computer Studies" }
```

> `name` must be 2–100 characters and unique within the school.

**Response 201:**
```json
{
  "id": 1,
  "school_id": 1,
  "name": "College of Computer Studies"
}
```

---

### GET `/departments/`

List all departments.

**Auth:** Any authenticated user

**Query params:** `skip` (0), `limit` (100, max 1000)

**Response 200:** List of `Department`

---

### GET `/departments/{department_id}`

Get a department by ID.

**Auth:** Any authenticated user

**Response 200:** `Department`

---

### PATCH `/departments/{department_id}`

Update a department's name.

**Auth:** `campus_admin`

**Request body:**
```json
{ "name": "New Name" }
```

**Response 200:** `Department`

---

### DELETE `/departments/{department_id}`

Delete a department.

**Auth:** `campus_admin`

**Response 204:** No content

---

## Programs

Programs represent courses/degree programs. Each program belongs to one or more departments.

### POST `/programs/`

Create a program.

**Auth:** `campus_admin`

**Request body:**
```json
{
  "name": "BS Computer Science",
  "department_ids": [1, 2]
}
```

**Response 201:**
```json
{
  "id": 3,
  "school_id": 1,
  "name": "BS Computer Science",
  "departments": [
    { "id": 1, "name": "College of Computer Studies" }
  ],
  "department_ids": [1]
}
```

---

### GET `/programs/`

List all programs.

**Auth:** Any authenticated user

**Query params:** `skip` (0), `limit` (100, max 1000)

**Response 200:** List of `Program`

---

### GET `/programs/{program_id}`

Get a program by ID.

**Auth:** Any authenticated user

**Response 200:** `Program`

---

### PATCH `/programs/{program_id}`

Update a program.

**Auth:** `campus_admin`

**Request body (all optional):**
```json
{
  "name": "Updated Name",
  "department_ids": [1]
}
```

**Response 200:** `Program`

---

### DELETE `/programs/{program_id}`

Delete a program.

**Auth:** `campus_admin`

**Response 204:** No content

---

## Events

### Event Targeting (year_levels)

When creating or updating an event, you specify which students it targets using `year_levels`. The backend automatically resolves this based on who created the event:

| Who creates | year_levels = [] | year_levels = [1, 2] |
|-------------|------------------|----------------------|
| Campus Admin / SSG | ALL students | Year 1 and Year 2 students |
| SG (department) | All in department | Department + Year 1 and Year 2 |
| ORG (course/program) | All in course | Course + Year 1 and Year 2 |

---

### POST `/events/`

Create a new event.

**Auth:** `campus_admin`, `ssg`, `sg`, `org` (with appropriate permissions)

**Request body:**
```json
{
  "name": "Freshmen Orientation",
  "location": "Main Auditorium",
  "description": "Welcome event for new students",
  "venue": "Building A, Room 101",
  "notes": "Bring your school ID",
  "banner_url": "https://...",
  "start_datetime": "2024-06-15T08:00:00+08:00",
  "end_datetime": "2024-06-15T12:00:00+08:00",
  "early_check_in_minutes": 30,
  "late_threshold_minutes": 15,
  "sign_out_grace_minutes": 60,
  "sign_out_open_delay_minutes": 0,
  "geo_latitude": 14.5995,
  "geo_longitude": 120.9842,
  "geo_radius_m": 100,
  "geo_required": false,
  "geo_max_accuracy_m": 30,
  "year_levels": [1, 2],
  "event_type_id": 1,
  "status": "upcoming"
}
```

> **Required fields:** `name`, `start_datetime`, `end_datetime`
>
> **Optional fields:** All others. `year_levels` is a list of year levels (1–5). Empty list means "all year levels".
>
> **status values:** `upcoming`, `ongoing`, `completed`, `cancelled` (default: `upcoming`)
>
> All datetimes are stored in Philippine Time (UTC+8). Include timezone info in ISO 8601 format.
>
> `sign_out_open_delay_minutes` cannot exceed `sign_out_grace_minutes`.

**Response 201:** `Event`

---

### GET `/events/`

List events.

**Auth:** Any authenticated user

**Query params:**
- `skip` (int, default 0)
- `limit` (int, default 100, max 1000)
- `status` — filter by: `upcoming`, `ongoing`, `completed`, `cancelled`
- `start_from` (datetime) — filter events starting after this time
- `end_at` (datetime) — filter events ending before this time
- `governance_context` — governance unit type filter

**Response 200:** List of `Event`

---

### GET `/events/ongoing`

List currently ongoing events.

**Auth:** Any authenticated user

**Query params:** `skip`, `limit`, `governance_context`

**Response 200:** List of `Event`

---

### GET `/events/{event_id}`

Get full event details including attendances and related data.

**Auth:** Any authenticated user

**Response 200:** `EventWithRelations`

```json
{
  "id": 1,
  "school_id": 1,
  "name": "Freshmen Orientation",
  "location": "Main Auditorium",
  "description": "...",
  "venue": "...",
  "start_datetime": "2024-06-15T08:00:00+08:00",
  "end_datetime": "2024-06-15T12:00:00+08:00",
  "status": "upcoming",
  "early_check_in_minutes": 30,
  "late_threshold_minutes": 15,
  "sign_out_grace_minutes": 60,
  "sign_out_open_delay_minutes": 0,
  "geo_latitude": 14.5995,
  "geo_longitude": 120.9842,
  "geo_radius_m": 100,
  "geo_required": false,
  "geo_max_accuracy_m": 30,
  "banner_url": null,
  "event_type": null,
  "departments": [],
  "programs": [],
  "event_targets": [],
  "department_ids": [],
  "program_ids": [],
  "present_until_override_at": null,
  "late_until_override_at": null,
  "sign_out_override_until": null,
  "attendances": [],
  "attendance_summary": {
    "present": 0,
    "late": 0,
    "absent": 0
  }
}
```

---

### PUT `/events/{event_id}`

Update an event.

**Auth:** Event creator or admin/campus_admin

**Request body:** Same as create, all fields optional.

```json
{
  "name": "Updated Event Name",
  "year_levels": [1, 2, 3],
  "start_datetime": "2024-06-15T09:00:00+08:00",
  "end_datetime": "2024-06-15T13:00:00+08:00"
}
```

**Response 200:** `Event`

---

### DELETE `/events/{event_id}`

Delete an event.

**Auth:** Event creator or admin/campus_admin

**Response 204:** No content

---

### GET `/events/{event_id}/time-status`

Get current time status for the event (is check-in open? is sign-out open? etc.)

**Auth:** Any authenticated user

**Response 200:**
```json
{
  "event_status": "early_check_in",
  "current_time": "2024-06-15T07:45:00+08:00",
  "check_in_opens_at": "2024-06-15T07:30:00+08:00",
  "start_time": "2024-06-15T08:00:00+08:00",
  "end_time": "2024-06-15T12:00:00+08:00",
  "late_threshold_time": "2024-06-15T08:15:00+08:00",
  "attendance_override_active": false,
  "effective_present_until_at": "2024-06-15T08:15:00+08:00",
  "effective_late_until_at": "2024-06-15T12:00:00+08:00",
  "sign_out_opens_at": "2024-06-15T12:00:00+08:00",
  "normal_sign_out_closes_at": "2024-06-15T13:00:00+08:00",
  "effective_sign_out_closes_at": "2024-06-15T13:00:00+08:00",
  "timezone_name": "Asia/Manila"
}
```

**event_status values:**
| Value | Meaning |
|-------|---------|
| `before_check_in` | Too early to check in |
| `early_check_in` | Early check-in window is open |
| `late_check_in` | Past start time, late check-in still allowed |
| `absent_check_in` | Too late to check in (absent) |
| `sign_out_pending` | Event has started, sign-out not yet open |
| `sign_out_open` | Sign-out window is open |
| `closed` | Event fully closed |

---

### POST `/events/{event_id}/verify-location`

Verify if a GPS coordinate is within the event's geofence.

**Auth:** Any authenticated user

**Request body:**
```json
{
  "latitude": 14.5995,
  "longitude": 120.9842,
  "accuracy_m": 15.0
}
```

**Response 200:**
```json
{
  "ok": true,
  "reason": null,
  "distance_m": 12.5,
  "effective_distance_m": 27.5,
  "radius_m": 100.0,
  "accuracy_m": 15.0,
  "time_status": { ...EventTimeStatusInfo... },
  "attendance_decision": {
    "action": "check_in",
    "event_status": "early_check_in",
    "attendance_allowed": true,
    "attendance_status": "present",
    "message": "Check-in is open",
    ...
  }
}
```

---

### PATCH `/events/{event_id}/status`

Manually override event status.

**Auth:** Event manager (admin, campus_admin, or governance user with MANAGE_EVENTS permission)

**Request body:**
```json
{ "status": "ongoing" }
```

**Response 200:** `Event`

---

### POST `/events/{event_id}/sign-out/open-early`

Open sign-out before the event ends.

**Auth:** Event attendance manager

**Request body:**
```json
{
  "use_sign_out_grace_minutes": true,
  "close_after_minutes": null
}
```

> If `use_sign_out_grace_minutes = false`, you must provide `close_after_minutes` (1–1440).

**Response 200:** `Event`

---

## Attendance

### GET `/attendance/students/me`

Get my own attendance records as a student.

**Auth:** Student role required

**Query params:**
- `event_id` (int, optional) — filter by event
- `skip` (int, default 0)
- `limit` (int, default 100)

**Response 200:** List of `Attendance`

```json
[
  {
    "id": 1,
    "event_id": 5,
    "student_id": 10,
    "time_in": "2024-06-15T07:50:00+08:00",
    "time_out": "2024-06-15T12:10:00+08:00",
    "method": "face_scan",
    "status": "present",
    "display_status": "Present",
    "completion_state": "complete",
    "is_valid_attendance": true,
    "notes": null,
    "verified_by": null
  }
]
```

---

### POST `/attendance/scan`

Record attendance via face scan (operator-driven).

**Auth:** User with attendance operator access (event manager or campus_admin)

**Request body:**
```json
{
  "event_id": 5,
  "student_id": "CS-2023-001"
}
```

**Response 200:**
```json
{
  "message": "Check-in recorded",
  "attendance_id": 101,
  "student_id": "CS-2023-001",
  "time_in": "2024-06-15T07:55:00+08:00",
  "time_out": null,
  "duration_minutes": null
}
```

---

### POST `/attendance/manual`

Record attendance manually (no face scan).

**Auth:** User with attendance operator access

**Query params:** `governance_context` (optional)

**Request body:**
```json
{
  "event_id": 5,
  "student_id": "CS-2023-001",
  "time_in": "2024-06-15T08:00:00+08:00",
  "time_out": "2024-06-15T12:00:00+08:00",
  "status": "present",
  "notes": "Manually verified"
}
```

> **status values:** `present`, `late`, `absent`, `excused`, `incomplete`

**Response 200:** `AttendanceActionResponse`

---

### Attendance Records Endpoints

#### GET `/attendance/records`

List attendance records with filtering.

**Auth:** Attendance operator or admin

**Query params:**
- `event_id` (required)
- `skip`, `limit`
- `status` — filter by attendance status

**Response 200:** List of `Attendance`

---

### Attendance Override Endpoints

#### POST `/attendance/{attendance_id}/time-out`

Record sign-out for an existing attendance record.

**Auth:** Attendance operator

**Request body:**
```json
{
  "time_out": "2024-06-15T12:00:00+08:00"
}
```

**Response 200:** `Attendance`

---

### Attendance Report Endpoints

#### GET `/attendance/reports/event/{event_id}`

Get attendance report summary for an event.

**Auth:** Event manager or admin

**Response 200:**
```json
{
  "event_name": "Freshmen Orientation",
  "event_date": "2024-06-15",
  "total_participants": 120,
  "attendees": 95,
  "late_attendees": 15,
  "absentees": 10,
  "attendance_rate": 79.17,
  "programs": [
    { "name": "BS Computer Science", "attendees": 50, "total": 60 }
  ]
}
```

---

## Face Recognition

### POST `/face/register/student`

Register a face for the currently logged-in student.

**Auth:** Student role (self-service)

**Rate limit:** Face rule (80/min)

**Request (multipart form):**
```
image=<image_file>
```

Supported formats: JPEG, PNG. Max size: 5 MB.

**Response 200:**
```json
{
  "message": "Face registered successfully",
  "student_id": "CS-2023-001",
  "liveness": {
    "label": "real",
    "score": 0.98
  }
}
```

**Errors:**
- `400` — No face detected, multiple faces, invalid image
- `422` — Liveness check failed (spoof detected)

---

### POST `/face/verify/student`

Verify a face for privileged operations (security-level MFA).

**Auth:** Any authenticated user

**Rate limit:** Face rule

**Request body:**
```json
{
  "image_base64": "<base64_encoded_image>",
  "threshold": 0.35
}
```

**Response 200:**
```json
{
  "matched": true,
  "distance": 0.28,
  "confidence": 0.72,
  "threshold": 0.35,
  "liveness": { "label": "real", "score": 0.97 },
  "verified_at": "2024-06-15T10:00:00Z",
  "access_token": "face_session_token",
  "session_id": "abc123"
}
```

---

### GET `/face/status`

Get current face verification status for the logged-in user.

**Auth:** Any authenticated user

**Response 200:**
```json
{
  "user_id": 42,
  "face_verification_required": true,
  "face_reference_enrolled": false,
  "liveness_enabled": true,
  "face_runtime_ready": true,
  "anti_spoof_ready": true,
  "live_capture_required": false,
  "face_runtime_state": "ready",
  "face_runtime_reason": null,
  "face_runtime_provider": "insightface"
}
```

---

### GET `/face/reference`

Get face reference enrollment status.

**Auth:** Any authenticated user

**Response 200:**
```json
{
  "user_id": 42,
  "face_reference_enrolled": true,
  "provider": "insightface",
  "updated_at": "2024-01-01T00:00:00Z",
  "liveness": { "label": "real", "score": 0.97 }
}
```

---

### POST `/face/attendance/scan`

Student self-service face attendance scan.

**Auth:** Student role

**Rate limit:** Public rule

**Request body:**
```json
{
  "event_id": 5,
  "image_base64": "<base64_encoded_image>",
  "latitude": 14.5995,
  "longitude": 120.9842,
  "accuracy_m": 15.0,
  "threshold": null
}
```

> `latitude`, `longitude`, `accuracy_m` are optional but required if the event has `geo_required = true`.

**Response 200:**
```json
{
  "action": "check_in",
  "student_id": "CS-2023-001",
  "student_name": "Juan Dela Cruz",
  "attendance_id": 101,
  "distance": 0.27,
  "confidence": 0.73,
  "threshold": 0.40,
  "liveness": { "label": "real", "score": 0.98 },
  "geo": { "ok": true, "distance_m": 12.5 },
  "time_in": "2024-06-15T07:55:00+08:00",
  "time_out": null,
  "duration_minutes": null,
  "message": "Check-in recorded successfully"
}
```

**Errors:**
- `400` — No face detected, or event not found
- `403` — Student not in event scope
- `409` — Already checked in / sign-out already recorded
- `422` — Spoof detected (liveness failed)

---

## Public Attendance Kiosk

No authentication required. These are used by a kiosk device on the event site.

### POST `/public-attendance/events/nearby`

Find events near the kiosk's location.

**Rate limit:** Public rule

**Request body:**
```json
{
  "latitude": 14.5995,
  "longitude": 120.9842,
  "accuracy_m": 10.0
}
```

**Response 200:**
```json
{
  "events": [
    {
      "id": 5,
      "school_id": 1,
      "school_name": "Example University",
      "name": "Freshmen Orientation",
      "location": "Main Auditorium",
      "start_datetime": "2024-06-15T08:00:00+08:00",
      "end_datetime": "2024-06-15T12:00:00+08:00",
      "geo_radius_m": 100.0,
      "distance_m": 12.5,
      "effective_distance_m": 22.5,
      "accuracy_m": 10.0,
      "attendance_phase": "sign_in",
      "phase_message": "Check-in is open",
      "scope_label": "Campus-wide",
      "departments": [],
      "programs": []
    }
  ],
  "scan_cooldown_seconds": 3
}
```

---

### POST `/public-attendance/events/{event_id}/multi-face-scan`

Submit a camera frame for multi-face attendance detection. The kiosk sends a full frame and the backend detects and identifies all faces in it.

**Rate limit:** Public rule + per-client throttle (min interval ~0.45s)

**Request body:**
```json
{
  "image_base64": "<base64_encoded_image>",
  "latitude": 14.5995,
  "longitude": 120.9842,
  "accuracy_m": 10.0,
  "threshold": null,
  "cooldown_student_ids": ["CS-2023-001", "CS-2023-002"]
}
```

> `cooldown_student_ids` — list of student IDs the kiosk has already scanned recently (to skip re-scanning within the cooldown window).

**Response 200:**
```json
{
  "event_id": 5,
  "event_phase": "sign_in",
  "message": "Public attendance scan processed successfully.",
  "scan_cooldown_seconds": 3,
  "geo": { "ok": true, "distance_m": 12.5, "radius_m": 100 },
  "outcomes": [
    {
      "action": "checked_in",
      "reason_code": null,
      "message": "Check-in recorded",
      "student_id": "CS-2023-001",
      "student_name": "Juan Dela Cruz",
      "attendance_id": 101,
      "distance": 0.26,
      "confidence": 0.74,
      "threshold": 0.40,
      "liveness": { "label": "real", "score": 0.97 },
      "time_in": "2024-06-15T07:55:00+08:00",
      "time_out": null,
      "duration_minutes": null
    },
    {
      "action": "liveness_failed",
      "reason_code": "spoof_detected",
      "message": "Live face verification failed for one detected face.",
      "liveness": { "label": "spoof", "score": 0.12 }
    }
  ]
}
```

**Outcome action values:**
| action | Meaning |
|--------|---------|
| `checked_in` | Successfully checked in |
| `signed_out` | Successfully signed out |
| `liveness_failed` | Spoof detected — face rejected |
| `no_match` | Face detected but no registered student found |
| `out_of_scope` | Student found but not eligible for this event |
| `cooldown_skipped` | In client cooldown — skipped |
| `duplicate_face` | Same student appeared twice in same frame |
| `already_recorded` | Attendance already exists |

---

## Governance Hierarchy

Governance units represent student government bodies:
- **SSG** — Supreme Student Government (school-wide)
- **SG** — Student Government (department-level)
- **ORG** — Student Organization (course/program-level)

### GET `/api/governance/access/me`

Get the current user's governance access (what units they belong to, what permissions they have).

**Auth:** Campus Admin, student, or governance member

**Response 200:**
```json
{
  "unit_types": ["ssg"],
  "units": [
    {
      "id": 1,
      "name": "Supreme Student Government",
      "unit_type": "SSG",
      "is_active": true
    }
  ],
  "permissions": ["manage_events", "view_attendance"]
}
```

---

### GET `/api/governance/units`

List governance units.

**Auth:** Campus Admin, student, or governance member

**Query params:**
- `unit_type` — filter by: `SSG`, `SG`, `ORG`
- `parent_unit_id` (int, optional)
- `include_inactive` (bool, default false)

**Response 200:** List of `GovernanceUnitSummaryResponse`

---

### POST `/api/governance/units`

Create a governance unit.

**Auth:** Campus Admin or authorized governance member

**Request body:**
```json
{
  "name": "Supreme Student Government",
  "unit_type": "SSG",
  "parent_unit_id": null,
  "department_id": null,
  "program_id": null
}
```

> **unit_type values:** `SSG`, `SG`, `ORG`
>
> For SG: provide `department_id`. For ORG: provide `program_id`.

**Response 201:** `GovernanceUnitDetailResponse`

---

### GET `/api/governance/units/{governance_unit_id}`

Get governance unit details.

**Auth:** Campus Admin or governance member

**Response 200:** `GovernanceUnitDetailResponse`

---

### PATCH `/api/governance/units/{governance_unit_id}`

Update a governance unit.

**Auth:** Campus Admin or authorized governance member

**Request body (all optional):**
```json
{
  "name": "Updated Name",
  "is_active": true
}
```

**Response 200:** `GovernanceUnitDetailResponse`

---

### DELETE `/api/governance/units/{governance_unit_id}`

Delete a governance unit.

**Auth:** Campus Admin

**Response 204:** No content

---

### GET `/api/governance/ssg/setup`

Get or create the SSG setup for the current school.

**Auth:** Campus Admin, student, or governance member

**Response 200:** `GovernanceSsgSetupResponse`

---

### POST `/api/governance/units/{governance_unit_id}/members`

Assign a student as a member of a governance unit.

**Auth:** Campus Admin or governance unit leader

**Request body:**
```json
{
  "user_id": 42,
  "role_label": "President",
  "is_active": true
}
```

**Response 201:** `GovernanceMemberResponse`

---

### PATCH `/api/governance/members/{governance_member_id}`

Update a governance member (role, active status).

**Auth:** Campus Admin or governance unit leader

**Request body (all optional):**
```json
{
  "role_label": "Vice President",
  "is_active": false
}
```

**Response 200:** `GovernanceMemberResponse`

---

### DELETE `/api/governance/members/{governance_member_id}`

Remove a member from a governance unit.

**Auth:** Campus Admin or governance unit leader

**Response 204:** No content

---

### POST `/api/governance/units/{governance_unit_id}/permissions`

Assign a permission to a governance unit.

**Auth:** Campus Admin

**Request body:**
```json
{
  "permission_code": "manage_events"
}
```

**Permission codes:** `manage_events`, `view_attendance`, `configure_event_sanctions`, `approve_sanction_compliance`, `view_sanctioned_students_list`, `view_student_sanction_detail`, `view_sanctions_dashboard`, `export_sanctioned_students`

**Response 201:** `GovernanceUnitPermissionResponse`

---

### GET `/api/governance/units/{governance_unit_id}/announcements`

List announcements for a governance unit.

**Auth:** Campus Admin, student, or governance member

**Response 200:** List of `GovernanceAnnouncementResponse`

---

### POST `/api/governance/units/{governance_unit_id}/announcements`

Create an announcement.

**Auth:** Governance member with unit access

**Request body:**
```json
{
  "title": "Important Reminder",
  "content": "All students are required to attend...",
  "status": "published"
}
```

**Response 201:** `GovernanceAnnouncementResponse`

---

### PATCH `/api/governance/announcements/{announcement_id}`

Update an announcement.

**Auth:** Governance member (author or leader)

**Request body (all optional):**
```json
{
  "title": "Updated Title",
  "content": "Updated content",
  "status": "archived"
}
```

**Response 200:** `GovernanceAnnouncementResponse`

---

### DELETE `/api/governance/announcements/{announcement_id}`

Delete an announcement.

**Auth:** Governance member (author or leader)

**Response 204:** No content

---

### GET `/api/governance/students`

List students accessible to the current governance user.

**Auth:** Campus Admin, student, or governance member

**Query params:**
- `governance_context` — `SSG`, `SG`, or `ORG`
- `skip`, `limit` (max 250)

**Response 200:** List of `GovernanceAccessibleStudentResponse`

---

### GET `/api/governance/students/search`

Search student candidates for governance membership.

**Auth:** Governance member

**Query params:**
- `q` — search term (name or student ID)
- `governance_unit_id` (int, optional)
- `limit` (max 50)

**Response 200:** List of `GovernanceStudentCandidateResponse`

---

### GET `/api/governance/units/{governance_unit_id}/event-defaults`

Get event timing defaults for a governance unit.

**Auth:** Governance member

**Response 200:** `GovernanceEventDefaultsResponse`

---

### PUT `/api/governance/units/{governance_unit_id}/event-defaults`

Update event timing defaults for a governance unit.

**Auth:** Governance member

**Request body (all optional):**
```json
{
  "early_check_in_minutes": 30,
  "late_threshold_minutes": 15,
  "sign_out_grace_minutes": 60
}
```

**Response 200:** `GovernanceEventDefaultsResponse`

---

## Sanctions

### GET `/sanctions/events/{event_id}/config`

Get sanction configuration for an event.

**Auth:** `admin`, `campus_admin`, or governance member with `configure_event_sanctions` or `manage_events` permission

**Response 200:** `SanctionConfigResponse`

---

### PUT `/sanctions/events/{event_id}/config`

Create or update sanction configuration for an event.

**Auth:** Same as GET config

**Request body:**
```json
{
  "sanction_enabled": true,
  "absent_penalty": "Community Service",
  "late_penalty": "Warning",
  "notes": "Strict attendance required"
}
```

**Response 200:** `SanctionConfigResponse`

---

### GET `/sanctions/events/{event_id}/students`

List students sanctioned for an event.

**Auth:** Governance member with `view_sanctioned_students_list` permission

**Query params:**
- `skip` (int, default 0)
- `limit` (int, default 50, max 250)
- `status` — filter: `pending`, `complied`, `approved`, `waived`

**Response 200:**
```json
{
  "total": 85,
  "items": [
    {
      "id": 1,
      "event_id": 5,
      "user_id": 42,
      "student_id": "CS-2023-001",
      "student_name": "Juan Dela Cruz",
      "compliance_status": "pending",
      "penalty_description": "Community Service",
      "created_at": "2024-06-15T12:00:00Z"
    }
  ],
  "skip": 0,
  "limit": 50
}
```

---

### POST `/sanctions/events/{event_id}/students/{user_id}/approve`

Approve a student's sanction compliance.

**Auth:** Governance member with `approve_sanction_compliance` permission

**Response 200:** `SanctionRecordResponse`

---

### GET `/sanctions/events/{event_id}/delegation`

Get sanction delegation configuration (which governance units handle sanctions for this event).

**Auth:** Same as sanction config

**Response 200:** List of `SanctionDelegationResponse`

---

### PUT `/sanctions/events/{event_id}/delegation`

Set sanction delegation.

**Auth:** Same as sanction config

**Request body:**
```json
{
  "delegations": [
    { "governance_unit_id": 1, "is_active": true }
  ]
}
```

**Response 200:** List of `SanctionDelegationResponse`

---

### GET `/sanctions/dashboard`

Get sanctions dashboard summary.

**Auth:** Governance member with `view_sanctions_dashboard` permission

**Response 200:** `SanctionsDashboardResponse`

---

### GET `/sanctions/students/me`

Get my own sanction records (student self-view).

**Auth:** Any authenticated user

**Response 200:** List of `SanctionRecordResponse`

---

### GET `/sanctions/students/{user_id}`

Get a specific student's sanction records.

**Auth:** Governance member with `view_student_sanction_detail` permission

**Response 200:** `SanctionStudentDetailResponse`

---

### GET `/sanctions/events/{event_id}/export`

Download an Excel file of sanctioned students for an event.

**Auth:** Governance member with `export_sanctioned_students` permission

**Response 200:** Excel file download

---

### POST `/sanctions/clearance-deadline`

Create a clearance deadline.

**Auth:** Governance member with `configure_event_sanctions` permission

**Request body:**
```json
{
  "deadline_at": "2024-07-01T23:59:00+08:00",
  "notes": "Clear all sanctions before this date"
}
```

**Response 200:** `ClearanceDeadlineResponse`

---

### GET `/sanctions/clearance-deadline`

Get the active clearance deadline.

**Auth:** Any authenticated user

**Response 200:** `ClearanceDeadlineResponse` or `null`

---

## Notifications

### GET `/api/notifications/preferences/me`

Get your notification preferences.

**Auth:** Any authenticated user

**Response 200:**
```json
{
  "user_id": 42,
  "email_enabled": true,
  "sms_enabled": false,
  "sms_number": null,
  "notify_missed_events": true,
  "notify_low_attendance": true,
  "notify_account_security": true,
  "notify_subscription": false,
  "updated_at": "2024-01-01T00:00:00Z"
}
```

---

### PUT `/api/notifications/preferences/me`

Update your notification preferences.

**Auth:** Any authenticated user

**Request body (all optional):**
```json
{
  "email_enabled": true,
  "sms_enabled": false,
  "sms_number": "+639171234567",
  "notify_missed_events": false
}
```

**Response 200:** `NotificationPreferenceResponse`

---

### GET `/api/notifications/logs`

List notification delivery logs.

**Auth:** `admin` or `campus_admin`

**Query params:**
- `school_id` (int, optional — admin only)
- `category` (string, optional)
- `status` (string, optional)
- `user_id` (int, optional)
- `limit` (100, max 500)

**Response 200:** List of `NotificationLogItem`

---

### POST `/api/notifications/dispatch/event-announcement`

Send an event announcement notification to all eligible students.

**Auth:** `admin` or `campus_admin`

**Query params:**
- `event_id` (int, required)
- `school_id` (int, optional — admin only)

**Response 200:**
```json
{
  "processed_users": 120,
  "sent": 115,
  "failed": 5,
  "skipped": 0,
  "category": "event_announcement"
}
```

---

### POST `/api/notifications/dispatch/event-reminder`

Send event reminder notification.

**Auth:** `admin` or `campus_admin`

**Query params:** Same as announcement

**Response 200:** `NotificationDispatchSummary`

---

### POST `/api/notifications/dispatch/missed-events`

Send missed events notification to students who were absent.

**Auth:** `admin` or `campus_admin`

**Response 200:** `NotificationDispatchSummary`

---

### POST `/api/notifications/dispatch/low-attendance`

Send low attendance warning notifications.

**Auth:** `admin` or `campus_admin`

**Response 200:** `NotificationDispatchSummary`

---

### POST `/api/notifications/test`

Send a test notification (email or SMS).

**Auth:** `admin` or `campus_admin`

**Request body:**
```json
{
  "channel": "email",
  "message": "This is a test notification"
}
```

**Response 200:**
```json
{ "message": "Test notification sent" }
```

---

## Data Governance

### GET `/api/governance/settings/me`

Get data governance settings for the school.

**Auth:** `admin` or `campus_admin`

**Response 200:**
```json
{
  "school_id": 1,
  "attendance_retention_days": 365,
  "audit_log_retention_days": 90,
  "import_file_retention_days": 30,
  "auto_delete_enabled": false
}
```

---

### PUT `/api/governance/settings/me`

Update data governance settings.

**Auth:** `admin` or `campus_admin`

**Request body (all optional):**
```json
{
  "attendance_retention_days": 730,
  "auto_delete_enabled": true
}
```

**Response 200:** `DataGovernanceSettingResponse`

---

### POST `/api/governance/consents/me`

Record a privacy consent for the current user.

**Auth:** Any authenticated user

**Request body:**
```json
{
  "consent_type": "data_processing",
  "consent_granted": true,
  "consent_version": "1.0",
  "source": "mobile_app"
}
```

**Response 200:** `PrivacyConsentItem`

---

### GET `/api/governance/consents/me`

List my privacy consents.

**Auth:** Any authenticated user

**Response 200:** List of `PrivacyConsentItem`

---

### POST `/api/governance/requests`

Submit a data request (export or deletion).

**Auth:** Any authenticated user

**Request body:**
```json
{
  "request_type": "export",
  "target_user_id": null,
  "reason": "Personal data request"
}
```

> **request_type values:** `export`, `delete`

**Response 200:** `DataRequestItem`

---

### GET `/api/governance/requests`

List data requests.

**Auth:** Any authenticated user (sees own), or admin/campus_admin (sees all in school)

**Query params:**
- `status` — filter by status
- `request_type` — filter by type
- `limit` (max 500)

**Response 200:** List of `DataRequestItem`

---

### PATCH `/api/governance/requests/{request_id}`

Approve or reject a data request.

**Auth:** `admin` or `campus_admin`

**Request body:**
```json
{
  "status": "approved",
  "note": "Approved after verification"
}
```

> For `export` requests: generates a JSON file with user data.
> For `delete` requests: soft-deletes the user (anonymizes email, deactivates account).

**Response 200:** `DataRequestItem`

---

### POST `/api/governance/run-retention`

Run data retention cleanup.

**Auth:** `admin` or `campus_admin`

**Request body:**
```json
{ "dry_run": true }
```

> Set `dry_run: true` to preview how many records would be deleted without actually deleting.
> Auto-delete must be enabled in governance settings before running with `dry_run: false`.

**Response 200:**
```json
{
  "school_id": 1,
  "dry_run": true,
  "deleted_audit_logs": 150,
  "deleted_import_logs": 12,
  "deleted_notifications": 400,
  "summary": "audit_logs=150, import_jobs=12, notifications=400, dry_run=true"
}
```

---

## Bulk Import

### GET `/admin/import-students/template`

Download an Excel template for bulk student import.

**Auth:** `admin` or `campus_admin`

**Response:** Excel file download (`student_import_template.xlsx`)

**Template columns:**
```
Student_ID | Email | Last_Name | First_Name | Middle_Name | Department | Course | Year_Level | Status
```

**Example row:**
```
STU-00001 | student1@example.edu | Doe | Jane | A | Computer Science | BS Computer Science | 1 | ACTIVE
```

> **Password rule:** Auto-generated as `lastname.lower()` (e.g., `doe`). If the last name has only 3 characters or fewer, the system may use a fallback password.
>
> **Status values:** `ACTIVE`, `INACTIVE`, `GRADUATED`, `TRANSFERRED`, `ARCHIVED`

---

### POST `/admin/import-students/preview`

Preview an import file for validation errors before committing.

**Auth:** `admin` or `campus_admin`

**Request (multipart form):**
```
file=<.csv or .xlsx file>
```

Max file size: 50 MB. Only `.csv` and `.xlsx` formats accepted.

**Response 200:**
```json
{
  "filename": "students.xlsx",
  "total_rows": 100,
  "valid_rows": 95,
  "invalid_rows": 5,
  "can_commit": false,
  "preview_token": "uuid-preview-token",
  "rows": [
    {
      "row": 2,
      "status": "valid",
      "errors": [],
      "suggestions": [],
      "row_data": { "Student_ID": "STU-00001", "Email": "student@edu.ph", ... }
    },
    {
      "row": 7,
      "status": "failed",
      "errors": ["Email already exists"],
      "suggestions": ["Use a unique email address"],
      "row_data": { "Student_ID": "STU-00006", "Email": "duplicate@edu.ph", ... }
    }
  ]
}
```

> **`can_commit`** is `true` only when `invalid_rows = 0`. Keep the `preview_token` for the next step.

---

### POST `/admin/import-preview-errors/{preview_token}/remove-invalid`

Remove invalid rows from the preview and mark it ready to commit with only valid rows.

**Auth:** `admin` or `campus_admin`

**Response 200:** Updated `ImportPreviewResponse` with `can_commit: true`

---

### GET `/admin/import-preview-errors/{preview_token}/download`

Download an Excel file listing the failed rows and their errors.

**Auth:** `admin` or `campus_admin`

**Response:** Excel file download

---

### GET `/admin/import-preview-errors/{preview_token}/retry-download`

Download an Excel file containing only the failed rows (for correction and re-upload).

**Auth:** `admin` or `campus_admin`

**Response:** Excel file download

---

### POST `/admin/import-students`

Commit a validated preview to run the actual import.

**Auth:** `admin` or `campus_admin`

**Rate limit:** 3 imports per 5 minutes per user

**Request (form data):**
```
preview_token=<token from preview step>
```

**Response 200:**
```json
{
  "job_id": "uuid-job-id",
  "status": "pending",
  "retried_from_job_id": null
}
```

> The import runs in the background. Poll `/admin/import-status/{job_id}` to track progress.

---

### GET `/admin/import-status/{job_id}`

Check the status of a background import job.

**Auth:** `admin` or `campus_admin`

**Response 200:**
```json
{
  "job_id": "uuid-job-id",
  "status": "completed",
  "total_rows": 95,
  "processed_rows": 95,
  "successful_rows": 93,
  "failed_rows": 2,
  "created_at": "2024-01-01T10:00:00Z",
  "completed_at": "2024-01-01T10:01:30Z",
  "errors": [
    { "row_number": 45, "error": "Duplicate email", "row_data": {...} }
  ],
  "failed_report_url": "/admin/import-errors/uuid-job-id/download"
}
```

**Status values:** `pending`, `processing`, `completed`, `failed`

---

### GET `/admin/import-errors/{job_id}/download`

Download the Excel error report for a completed import job.

**Auth:** `admin` or `campus_admin`

**Response:** Excel file download

---

### POST `/admin/import-students/retry-failed/{job_id}`

Create a new import job that only retries the failed rows from a previous job.

**Auth:** `admin` or `campus_admin`

**Request body (optional):**
```json
{ "row_numbers": [45, 67] }
```

> Omit `row_numbers` to retry all failed rows.

**Response 200:**
```json
{
  "job_id": "new-uuid-job-id",
  "status": "pending",
  "retried_from_job_id": "original-job-id"
}
```

---

## Audit Logs

### GET `/api/audit-logs`

Search school audit logs.

**Auth:** `admin` or `campus_admin`

**Query params:**
- `q` — free text search (max 200 chars)
- `action` — filter by action type
- `status` — filter by status
- `actor_user_id` (int)
- `start_date` (datetime)
- `end_date` (datetime)
- `limit` (50, max 500)
- `offset` (0)

**Response 200:**
```json
{
  "total": 250,
  "items": [
    {
      "id": 1,
      "school_id": 1,
      "actor_user_id": 5,
      "action": "student_bulk_import_attempt",
      "status": "queued",
      "details": "{ \"job_id\": \"...\", \"filename\": \"students.xlsx\" }",
      "created_at": "2024-01-01T10:00:00Z"
    }
  ]
}
```

---

## Common Schemas

### SchoolBrandingResponse

```json
{
  "school_id": 1,
  "school_name": "Example University",
  "school_code": "EU-001",
  "logo_url": "https://...",
  "primary_color": "#162F65",
  "secondary_color": "#2C5F9E",
  "accent_color": null,
  "event_default_early_check_in_minutes": 30,
  "event_default_late_threshold_minutes": 15,
  "event_default_sign_out_grace_minutes": 60,
  "subscription_status": "trial",
  "active_status": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

---

### UserWithRelations

```json
{
  "id": 42,
  "email": "juan@school.edu",
  "first_name": "Juan",
  "middle_name": "A",
  "last_name": "Dela Cruz",
  "roles": ["student"],
  "school_id": 1,
  "is_active": true,
  "face_scan_bypass_enabled": false,
  "created_at": "2024-01-01T00:00:00Z",
  "student_profile": {
    "id": 10,
    "student_id": "CS-2023-001",
    "department_id": 2,
    "program_id": 3,
    "year_level": 2,
    "student_status": "ACTIVE",
    "promotion_locked": false,
    "is_face_registered": true,
    "registration_complete": true
  }
}
```

---

### Event

```json
{
  "id": 1,
  "school_id": 1,
  "name": "Freshmen Orientation",
  "location": "Main Auditorium",
  "description": null,
  "venue": null,
  "notes": null,
  "banner_url": null,
  "start_datetime": "2024-06-15T08:00:00+08:00",
  "end_datetime": "2024-06-15T12:00:00+08:00",
  "status": "upcoming",
  "early_check_in_minutes": 30,
  "late_threshold_minutes": 15,
  "sign_out_grace_minutes": 60,
  "sign_out_open_delay_minutes": 0,
  "geo_latitude": null,
  "geo_longitude": null,
  "geo_radius_m": null,
  "geo_required": false,
  "geo_max_accuracy_m": null,
  "event_type": null,
  "departments": [],
  "programs": [],
  "event_targets": [],
  "department_ids": [],
  "program_ids": [],
  "present_until_override_at": null,
  "late_until_override_at": null,
  "sign_out_override_until": null
}
```

---

### Attendance

```json
{
  "id": 1,
  "event_id": 5,
  "student_id": 10,
  "time_in": "2024-06-15T07:55:00+08:00",
  "time_out": "2024-06-15T12:05:00+08:00",
  "method": "face_scan",
  "status": "present",
  "display_status": "Present",
  "completion_state": "complete",
  "is_valid_attendance": true,
  "notes": null,
  "verified_by": null
}
```

**method values:** `face_scan`, `manual`

**status values:** `present`, `late`, `absent`, `excused`, `incomplete`

**completion_state values:** `complete` (has both time_in and time_out), `pending_sign_out` (only time_in), `incomplete`

---

### Error Responses

**400 Bad Request:**
```json
{ "detail": "Descriptive error message" }
```

**401 Unauthorized:**
```json
{ "detail": "Not authenticated" }
```

**403 Forbidden:**
```json
{ "detail": "You do not have permission to perform this action" }
```

**404 Not Found:**
```json
{ "detail": "Resource not found" }
```

**409 Conflict:**
```json
{ "detail": "Conflict description" }
```

**413 Request Entity Too Large:**
```json
{ "detail": "File size exceeds limit of 50 MB" }
```

**422 Unprocessable Entity:**
```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**429 Too Many Requests:**
```json
{
  "code": "rate_limit_exceeded",
  "message": "Too many requests",
  "limit": 10,
  "window_seconds": 300,
  "retry_after_seconds": 240
}
```

**500 Internal Server Error:**
```json
{ "detail": "Internal server error" }
```
