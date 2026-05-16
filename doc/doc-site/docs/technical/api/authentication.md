---
sidebar_position: 2
title: Authentication
---

# Authentication

🔒 **Restricted**: Developer documentation

## Overview

Aura uses JWT-based authentication with role-based access control.

## Login Flow

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123"
}
```

Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "user@example.com",
    "role": "student"
  }
}
```

## Using the Token

Include the token in the Authorization header:

```bash
GET /api/v1/users/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

## Token Expiration

- Access tokens expire after 24 hours
- Refresh tokens expire after 30 days

## Roles

- `student` - Basic user access
- `ssg` / `sg` / `org` - Student government, event management
- `admin` - Platform admin, full system access
- `campus_admin` - School-level admin
- `school_it` - Technical configuration
