# Authentication Guide

> **Status:** STANDARDIZED
> **Last Updated:** 2026-03-28

---

## Purpose

This document explains the API authentication flow clearly enough for frontend development, QA validation, and integration troubleshooting.

Source routers:

- `Backend/app/routers/auth.py`
- `Backend/app/routers/security_center.py`

## Authentication Model

VALID8 uses Bearer JWT for protected routes.

```http
Authorization: Bearer <access_token>
```

## Auth Flow Summary

1. Client sends credentials to `POST /login`
2. Server returns a full token response
3. Client uses the returned bearer token on protected endpoints
4. Session and security management is handled under `/auth/security/*`

## Primary Endpoints

| Method | Path | Purpose | Auth |
|---|---|---|---|
| POST | `/token` | OAuth2-compatible token endpoint for Swagger UI | None |
| POST | `/login` | Primary frontend login endpoint | None |
| POST | `/auth/change-password` | Changes current user password | Bearer JWT |
| POST | `/auth/forgot-password` | Creates password reset request | None |
| GET | `/auth/password-reset-requests` | Lists pending reset requests | Admin or Campus Admin |
| POST | `/auth/password-reset-requests/{request_id}/approve` | Approves reset request and issues temporary password | Admin or Campus Admin |
| GET | `/auth/security/sessions` | Lists active sessions | Bearer JWT |
| POST | `/auth/security/sessions/{session_id}/revoke` | Revokes one session | Bearer JWT |
| POST | `/auth/security/sessions/revoke-others` | Revokes all sessions except current | Bearer JWT |
| GET | `/auth/security/login-history` | Lists login history | Bearer JWT |

## Login Request Example

```http
POST /login
Content-Type: application/json
```

```json
{
  "email": "admin@school.edu",
  "password": "yourpassword"
}
```

## Login Success Response Example

If successful, `POST /login` returns a token payload:

```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "email": "admin@school.edu",
  "roles": ["admin"],
  "user_id": 1,
  "school_id": 1,
  "must_change_password": false,
  "session_id": "uuid"
}
```

Possible additional flags may appear depending on account state, such as password-change prompts or face-verification guidance.

## Role and Permission Enforcement

## Role and Permission Enforcement

- Protected endpoints validate the JWT first.
- Role checks are enforced server-side before the handler runs.
- Governance accounts may also require explicit governance permissions, not just a role name.

Common permission failure example:

```json
{
  "detail": "Access denied - insufficient role"
}
```

## Common Authentication Errors

| Status | Where It Happens | Meaning |
|---|---|---|
| `401` | `/login`, `/token` | Incorrect credentials or invalid bearer token |
| `403` | Protected routes | Token is valid but role or permission is not sufficient |
| `409` | Account-state checks | School or account state blocks login or follow-up action |
| `422` | Any auth endpoint | Request body is missing required fields or has invalid format |

## Security Center Notes

The security center extends the auth flow with:

- active session listing
- active session listing
- single-session revocation
- revoke-others behavior
- login history review
- privileged face-reference and face-verification endpoints

## Traceability

| Area | Linked Requirement |
|---|---|
| Login | [functional-requirements.md](../../requirements/functional-requirements.md) `FR-01` |
| Session management | [functional-requirements.md](../../requirements/functional-requirements.md) `FR-01` |
| Password reset approval | [use-cases.md](../../requirements/use-cases.md) `UC-01` |

## Documentation Review Rule

If authentication behavior changes in router logic, token response fields, or security-center routes, this file must be updated in the same change cycle.
