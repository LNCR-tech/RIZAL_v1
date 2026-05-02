# Security Guide

## Before Production Deployment

### 1. Generate Strong Credentials

```powershell
# Windows PowerShell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | ForEach-Object {[char]$_})
```

```bash
# Linux/Mac
openssl rand -hex 32
```

### 2. Required Environment Variables

Each service has its own `.env.example`. Copy it to `.env` and fill in all values.

Critical variables that must be set before deployment:

- `SECRET_KEY` — minimum 32 characters, random
- `DATABASE_URL` — point to your production Postgres
- `ADMIN_EMAIL` / `ADMIN_PASSWORD` — strong credentials, not defaults
- `AI_API_KEY` — from your AI provider
- `MAILJET_API_KEY` / `MAILJET_API_SECRET` — from Mailjet

### 3. Production Checklist

- [ ] `SECRET_KEY` is a long random string (not the default)
- [ ] Database credentials are not `postgres/postgres`
- [ ] `API_DOCS_ENABLED=false`
- [ ] `RATE_LIMIT_FAIL_OPEN=false`
- [ ] `TRUSTED_HOSTS` set to your actual domain (no `*`)
- [ ] `CORS_ALLOWED_ORIGINS` set to your frontend domain only
- [ ] All URLs use HTTPS
- [ ] `.env` is in `.gitignore` and not committed
- [ ] pgAdmin is not publicly exposed (use SSH tunnel or VPN)
- [ ] Database and Redis ports are not publicly exposed

### 4. Security Features

- JWT authentication with session validation
- bcrypt password hashing
- Role-based access control (RBAC)
- Rate limiting on all sensitive endpoints (fail-closed)
- CORS and trusted host validation
- Non-root users in all Docker containers
- Face recognition with liveness/anti-spoof (ONNX)
- MFA challenge support

### 5. Incident Response

If credentials are compromised:
1. Revoke the exposed key/secret from the provider dashboard immediately
2. Rotate `SECRET_KEY` and restart all services (this invalidates all sessions)
3. Force password reset for affected users
4. Review `school_audit_logs` for suspicious activity
