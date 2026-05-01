# Installation Guide

[<- Back to doc index](../README.md)

> **Status:** ACTIVE
> **Last Updated:** 2026-04-25

---

## SSOT Note

Canonical setup instructions are maintained in:
- [docs/getting-started/docker.md](../../docs/getting-started/docker.md)
- [docs/getting-started/local-dev.md](../../docs/getting-started/local-dev.md)
- [docs/reference/env.md](../../docs/reference/env.md)

If this guide conflicts with those pages, follow `docs/*`.

---

## Who This Is For

This guide is for school administrators and deployment operators installing Aura for users.

For developers, use:
- [docs/getting-started/local-dev.md](../../docs/getting-started/local-dev.md)

---

## Quick Install (Repo-Root Docker)

1. From repo root, create `.env`:

```powershell
Copy-Item .\.env.example .\.env -Force
notepad .\.env
```

2. Set required shared values in `.env`:
- `SECRET_KEY`
- `AI_API_KEY`
- `AI_API_BASE`
- `AI_MODEL`

3. Start the stack:

```powershell
docker compose up --build
```

4. Wait for services to initialize (migrations and bootstrap run automatically).

5. Verify access:
- Frontend: `http://localhost:5173`
- Backend API docs: `http://localhost:8000/docs`
- Assistant API docs: `http://localhost:8500/docs`
- pgAdmin: `http://localhost:5050`
- Mailpit: `http://localhost:8025`

---

## First Login

1. Open the frontend URL.
2. Sign in with the seeded admin account.
3. Change password immediately.

Default admin credentials are controlled in `backend/app/core/app_settings.py`.

---

## APK Distribution

For Android end users, see:
- [APK User Manual](./apk_manual.md)

For technical APK build/distribution details, see:
- [Android APK Build Guide](../technical/frontend/android-apk-build.md)

---

## Quick Troubleshooting

| Problem | Check | Fix |
|---|---|---|
| Services fail to start | Docker Desktop status and `.env` values | Restart Docker, fix env values, run again |
| Backend not reachable | Backend container logs | Resolve startup error, then restart stack |
| Migration issues | DB connection values | Correct `DATABASE_URL`, restart compose flow |
| Email tests fail | `EMAIL_TRANSPORT` and SMTP/Mailjet values | Set valid mail config and restart backend |
| Frontend loads but API fails | `BACKEND_ORIGIN`/proxy configuration | Align frontend backend target and retry |

---

## Verification Checklist

- [ ] `.env` created from `.env.example`
- [ ] Required AI and secret values configured
- [ ] `docker compose up --build` completed
- [ ] Frontend, backend, assistant URLs reachable
- [ ] Admin login works
- [ ] Test email path validated (if enabled)

