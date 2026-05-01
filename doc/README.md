# AURA Documentation Workspace

[<- Back to project root](../README.md)

> **Project:** Aura (Student Attendance System)
> **Documentation Workspace:** `doc/`
> **Last Updated:** 2026-04-27

---

## SSOT Rule

This `doc/` folder is a working documentation workspace for notes and handouts.
The canonical product and engineering documentation is under `docs/`.

If any content in `doc/` conflicts with `docs/`, treat `docs/` as the single source of truth.

### Runtime and Configuration SSOT Files

- `backend/app/core/config.py`
- `backend/app/core/app_settings.py`
- `assistant/lib/app_settings.py`
- `frontend/vite.config.js`
- `frontend/runtime-config.js.template`
- `frontend/scripts/write-capacitor-config.mjs`
- `docker-compose.yml`
- `.env.example`

---

## Current Project Layout (Top Level)

- `backend/`: FastAPI API, Alembic migrations, Celery workers and beat
- `assistant/`: Active assistant service
- `frontend/`: Vue 3 + Vite SPA with Capacitor Android workspace in `frontend/aura-apk/`
- `docs/`: Canonical docs (SSOT)
- `doc/`: Working docs, meeting notes, and user handouts
- `docker-init/`: DB init scripts
- `seeder/`: Seeder artifacts/scripts

---

## Canonical Documentation Entry Points

- [Getting Started (Docker)](../docs/getting-started/docker.md)
- [Getting Started (Local Dev)](../docs/getting-started/local-dev.md)
- [Environment Variables](../docs/reference/env.md)
- [Ports and URLs](../docs/reference/ports.md)
- [Repository Layout](../docs/reference/repository-layout.md)
- [Backend Docs](../docs/backend/README.md)
- [Frontend Docs](../docs/frontend/README.md)
- [Assistant Docs](../docs/assistant/README.md)
- [User Overview](../docs/user/overview.md)
- [Navigation Map](../docs/user/navigation.md)

---

## `doc/` Workspace Contents

- `overview/`: Business and scope summaries
- `requirements/`: Functional and non-functional requirements
- `technical/`: Implementation notes and guides
- `user-guide/`: End-user guides, including APK user manual
- `changelog/`: Historical branch/service change notes
- `meetings/`: Decisions and planning notes
- `agentic/`: AI subsystem writeups
- `reviews/`: Review artifacts

---

## Maintenance Workflow

1. Update canonical docs under `docs/` first.
2. Reflect only needed summaries/handouts in `doc/`.
3. Do not duplicate large env matrices, route maps, or API contracts in both trees.
4. Link to canonical `docs/` pages whenever possible.
