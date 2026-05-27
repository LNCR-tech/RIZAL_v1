# Forgot Password — Frontend Implementation Guide

This documents the self-service forgot password flow using the email code system. The admin-approval flow has been removed. All users (students, campus admins) now use this single flow.

---

## Flow Overview

```
[User enters email]
        ↓
POST /auth/forgot-password
        ↓
[Backend emails a 6-digit code — valid 15 minutes]
        ↓
[User enters code + new password]
        ↓
POST /auth/reset-password
        ↓
[Password updated — user can log in]
```

---

## Step 1 — Request a Reset Code

**Endpoint:** `POST /auth/forgot-password`

**Auth required:** No

**Request body:**
```json
{
  "email": "user@example.com"
}
```

**Response (always 200, regardless of whether the email exists):**
```json
{
  "message": "If an account with that email exists, a reset code has been sent."
}
```

**Notes:**
- Always returns the same generic message — do not tell the user whether the email was found or not (security).
- Rate limited — too many requests from the same IP/email will return `429 Too Many Requests`.
- Works for all roles: `student`, `campus_admin`. Does NOT work for platform `admin` accounts (no school_id).
- The 6-digit code is valid for **15 minutes** from the moment it is sent.

---

## Step 2 — Submit Code and New Password

**Endpoint:** `POST /auth/reset-password`

**Auth required:** No

**Request body:**
```json
{
  "email": "user@example.com",
  "code": "482910",
  "new_password": "NewPass123!"
}
```

**Success response (200):**
```json
{
  "message": "Password has been reset successfully."
}
```

**Error responses:**

| Status | Detail | Meaning |
|--------|--------|---------|
| `400` | `"Invalid or expired reset code."` | Wrong code, already used code, or code older than 15 min |
| `422` | Validation error | Missing fields or password too weak |
| `429` | Rate limit exceeded | Too many attempts |

**Password requirements** (enforced by backend):
- Minimum 8 characters
- At least one uppercase letter
- At least one number

---

## UI Recommendations

### Screen 1 — Enter Email
- Single email input + "Send code" button
- On submit: call `POST /auth/forgot-password`
- Always show: *"If an account with that email exists, a reset code has been sent."*
- Do NOT show different messages for found vs. not found emails

### Screen 2 — Enter Code + New Password
- 6-digit code input (consider a segmented/OTP-style input)
- New password input + confirm password input
- "Resend code" button (calls Step 1 again — rate limited, add a cooldown timer in the UI)
- Expiry note: *"Code expires in 15 minutes"*
- On submit: call `POST /auth/reset-password`
- On `400`: show *"Invalid or expired reset code. Please request a new one."*
- On success: navigate to login screen

---

## Frontend Files to Remove (Approval Flow Cleanup)

The admin approval flow has been removed from the backend. To avoid broken UI, the frontend dev needs to remove these from the Flutter app:

| File | What to remove |
|------|----------------|
| `lib/features/admin/presentation/admin_home_screen.dart` | `"Pending password resets"` section (the `pendingAsync.when(...)` widget and `_approveReset` method) |
| `lib/features/admin/application/admin_providers.dart` | `pendingResetsProvider` |
| `lib/features/admin/data/admin_repository.dart` | `pendingResets()` and `approveReset()` methods |
| `lib/shared/models/admin.dart` | `PasswordResetRequest` class |
| `lib/core/network/api_paths.dart` | `passwordResetRequests` and `approvePasswordReset(id)` constants |
| `lib/features/help/data/help_content.dart` | Update line referencing admin-approval flow for Campus Admins |

---

## What Was Removed from the Backend

| Removed | Reason |
|---------|--------|
| `GET /auth/password-reset-requests` | Admin approval flow endpoint |
| `POST /auth/password-reset-requests/{id}/approve` | Admin approval flow endpoint |
| `PasswordResetRequestItem` schema | Only used by approval endpoints |
| `PasswordResetApprovalResponse` schema | Only used by approval endpoints |
| `PasswordResetRequest` model (ORM import) | No longer queried — DB table left intact |
| `_requires_platform_admin_password_reset_approval()` helper | No longer needed |

> **Note:** The `password_reset_requests` DB table is **not dropped** — historical data is preserved. Only the API endpoints were removed.
