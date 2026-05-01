# Setup Guide

> **Status:** Maintained
> **Last Updated:** 2026-03-28
>
> **Source of truth:**
> - `docker-compose.yml`
> - `Backend/Dockerfile`
> - `Frontend/Dockerfile`
> - `docs/technical/deployment/deployment-guide.md`
> - `docs/technical/deployment/environment-variables.md`

---

## Purpose

This guide provides a reproducible developer onboarding flow for local setup, validation, and day-to-day development.

## Onboarding Risk Controls

| Risk | Control in this guide |
|---|---|
| Difficult onboarding | Ordered setup steps with commands and verification endpoints. |
| Missing configuration | Explicit environment-variable references and preflight checks. |
| Outdated instructions | Source-of-truth references and update rule at the end of this file. |

## Prerequisites

- Docker Desktop (or Docker Engine with Compose)
- Git
- Access to the repository
- Basic terminal access

Optional but recommended:

- A local `Backend/.env` for direct backend runs outside Compose

## Local Setup (Compose)

### 1. Clone the repository

```bash
git clone https://github.com/<org>/AURA_PUBLICFACE.git
cd AURA_PUBLICFACE
```

### 2. Preflight checks

```bash
docker compose config
```

If you plan to run production-style compose locally:

```bash
docker compose -f docker-compose.prod.yml config
```

### 3. Start development services

```bash
docker compose up --build -d
```

### 4. Run migrations

```bash
docker compose exec backend alembic upgrade head
```

### 5. Verify services

| Service | URL |
|---|---|
| Frontend | `http://localhost:5173` |
| Backend API root | `http://localhost:8000/` |
| Swagger UI | `http://localhost:8000/docs` |
| ReDoc | `http://localhost:8000/redoc` |
| Mailpit | `http://localhost:8025` |
| pgAdmin | `http://localhost:5050` |

### 6. Run quality checks

```bash
# Backend tests
docker compose exec backend python -m pytest

# Frontend lint
docker compose exec frontend npm run lint
```

### 7. Stop services

```bash
docker compose down
```

To reset DB volumes:

```bash
docker compose down -v
```

## Daily Development Flow

1. Pull latest integration branch changes.
2. Rebuild only when dependencies or Dockerfiles change.
3. Apply migrations before testing affected features.
4. Validate API routes through `/docs` when backend routes change.
5. Keep docs updated with code behavior in the same branch.

## Common Setup Issues

| Symptom | Likely cause | Action |
|---|---|---|
| Compose fails before startup | Invalid compose config or missing env file | Run `docker compose config` and fix reported key. |
| Backend unavailable on `:8000` | Backend container failed | Check `docker compose logs backend --tail 100`. |
| Worker tasks not running | Redis or worker startup issue | Check `docker compose logs worker --tail 100`. |
| Migration errors | Schema mismatch or DB startup timing | Ensure DB is healthy, then rerun `alembic upgrade head`. |

Known note for production compose:

- Current `docker-compose.prod.yml` contains `restart: unless-` for Redis, which must be corrected before production deployment.

## Documentation Enforcement

- If setup steps change, update this file in the same pull request.
- If deployment flow changes, update:
  - `docs/technical/deployment/deployment-guide.md`
  - `docs/technical/deployment/environment-variables.md`
  - `docs/technical/deployment/ci-cd-pipeline.md`
- If backend behavior changes, follow `AGENTS.md` and update `Backend/docs/BACKEND_CHANGELOG.md` and affected backend guides.
