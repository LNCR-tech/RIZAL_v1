---
sidebar_position: 1
title: API Overview
---

# API Reference

🔒 **Restricted**: This documentation is for developers and technical staff only.

## Base URL

```
Development: http://localhost:8001/api/v1
Production: https://api.aura.school/api/v1
```

## Authentication

All API requests require a Bearer token:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.aura.school/api/v1/users/me
```

See [Authentication Guide](./authentication) for details.

## Core Endpoints

| Endpoint | Description |
|----------|-------------|
| `/auth/*` | Authentication and session management |
| `/users/*` | User management |
| `/events/*` | Event CRUD operations |
| `/attendance/*` | Attendance tracking |
| `/face/*` | Face recognition enrollment/verification |
| `/reports/*` | Report generation |

## Response Format

All responses follow this structure:

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation successful"
}
```

Errors:

```json
{
  "success": false,
  "error": "Error message",
  "code": "ERROR_CODE"
}
```

## Rate Limiting

- 100 requests per minute per user
- 1000 requests per hour per IP

## Pagination

List endpoints support pagination:

```
GET /api/v1/users?page=1&limit=20
```

## Next Steps

- [Authentication](./authentication) — Learn about auth flows
- [Endpoints](./endpoints) — Full endpoint reference
