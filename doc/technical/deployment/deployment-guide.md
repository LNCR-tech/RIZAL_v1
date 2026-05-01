# Deployment Guide

> **Status:** Maintained
> **Last Updated:** 2026-04-27
>
> **Source of truth:**
> - `docker-compose.yml`
> - `docker-compose.prod.yml`
> - `backend/Dockerfile`
> - `backend/Dockerfile.prod`
> - `frontend/Dockerfile`
> - `frontend/Dockerfile.prod`
> - `start.sh`
> - `deploy.sh`
> - `migrate-volumes-v2.sh`
> - `.github/workflows/deploy-ec2.yml`

---

## Purpose

This page documents the current AURA deployment paths after the April 25 to April 27 branch updates:

- compose-first startup with `migrate` and `bootstrap` init jobs
- production bind-mount persistence under `/home/ubuntu/Aura/docker-data`
- migration-first deployment verification in CI and remote deploy scripts
- assistant service path normalized to `assistant/` (not `assistant-v2/`)

See also:
- [environment-variables.md](./environment-variables.md)
- [ci-cd-pipeline.md](./ci-cd-pipeline.md)
- [migrations.md](../database/migrations.md)

## Deployment Model

| Environment | Main compose file | Runtime behavior |
|---|---|---|
| Development / integration | `docker-compose.yml` | Starts infra plus app services; includes `migrate` and `bootstrap` init sequence before backend service health checks. |
| Production | `docker-compose.prod.yml` | Uses production Dockerfiles, explicit `.env`, pgvector Postgres image, and migration-first release flow. |

## Key Changes Captured (2026-04-25 to 2026-04-27)

- Added Linux/AWS deployment scripts (`start.sh`, `deploy.sh`) and improved full-stack one-click startup behavior.
- Added production CI/CD workflows and deploy validation.
- Added/standardized bind-mount ownership preparation for `postgres`, `pgadmin`, `imports`, `branding`, and `insightface` data paths.
- Switched production DB image to `pgvector/pgvector:pg15`.
- Hardened migration execution with explicit migration-first workflow and normalization-migration recovery fixes.
- Renamed assistant service directory references from `assistant-v2` to `assistant`.

## Preflight Checklist

Run these checks before any deploy:

1. Confirm branch and compose target.
2. Ensure `.env` exists for production compose.
3. Validate compose files:

```bash
docker compose config --quiet
docker compose -f docker-compose.prod.yml config --quiet
```

4. Ensure required host data directories exist (or run `start.sh`/`deploy.sh` to create them):
   - `/home/ubuntu/Aura/docker-data/postgres`
   - `/home/ubuntu/Aura/docker-data/pgadmin`
   - `/home/ubuntu/Aura/docker-data/imports`
   - `/home/ubuntu/Aura/docker-data/branding`
   - `/home/ubuntu/Aura/docker-data/insightface`

5. Confirm migration path health before restart:

```bash
docker compose -f docker-compose.prod.yml run --rm migrate
```

## Development Startup

```bash
docker compose up --build -d
```

Optional explicit init checks:

```bash
docker compose run --rm migrate
docker compose run --rm bootstrap
```

Quick verification:

- Frontend: `http://localhost`
- Backend docs: `http://localhost:8000/docs`
- Assistant docs: `http://localhost:8500/docs`
- pgAdmin: `http://localhost:5050`

Useful commands:

```bash
docker compose ps
docker compose logs backend --tail 150
docker compose logs worker --tail 150
docker compose logs assistant --tail 150
```

## Production Startup (Manual Path)

### 1. Prepare `.env`

Use `.env.production.example` or your secure template and keep secrets out of git.

### 2. Prepare bind-mount ownership

Either run `start.sh`/`deploy.sh`, or apply the ownership model manually:

- postgres: `999:999`
- pgadmin: `5050:5050`
- backend/worker writable data (`imports`, `branding`, `insightface`): `1000:1000`

### 3. Validate compose

```bash
docker compose -f docker-compose.prod.yml config --quiet
```

### 4. Run migration-first release

```bash
docker compose -f docker-compose.prod.yml run --rm migrate
docker compose -f docker-compose.prod.yml run --rm bootstrap
docker compose -f docker-compose.prod.yml up --build -d
```

### 5. Verify deployment

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs backend --tail 150
docker compose -f docker-compose.prod.yml logs worker --tail 150
docker compose -f docker-compose.prod.yml logs assistant --tail 150
```

Health endpoints:

- `http://<host>/`
- `http://<host>/docs`
- `http://<host>/openapi.json`
- `http://<host>:8500/docs`

## Scripted Deployment Paths

### `start.sh`

Use for one-click Ubuntu/AWS setup and lifecycle commands:

- `./start.sh` (setup + start)
- `./start.sh update`
- `./start.sh logs [service]`
- `./start.sh reset` (destructive to volumes)

### `deploy.sh`

Use for guided production deployment with prompted `.env` setup and host URL initialization.

### `migrate-volumes-v2.sh`

Use to migrate from named volumes or legacy local paths into `/home/ubuntu/Aura/docker-data`.

## CI/CD Deployment Notes

- `deploy-ec2.yml` runs migration-first deployment steps for the integration branch pipeline.
- `ci.yml` handles compose validation, backend/frontend checks, build tests, and branch-gated auto-deploy logic.
- Branch trigger behavior is documented in [ci-cd-pipeline.md](./ci-cd-pipeline.md).

## Rollback

If release validation fails:

1. Checkout last known-good commit.
2. Re-run migration inspection (`alembic current`, `alembic history`).
3. Rebuild with the same compose file.
4. Validate backend `/health` and critical auth/event/attendance flows.

## Common Deployment Failures

| Symptom | Likely cause | Validation step |
|---|---|---|
| `env file ... not found` | Missing `.env` for production compose | `docker compose -f docker-compose.prod.yml config --quiet` |
| Migration fails with duplicate object errors | Older normalization path replay without idempotency checks | Re-run current head migration path and inspect migration revisions |
| `schema.sql` not found during migration | Incorrect schema file path in container image or volume | Validate `backend/app/db/schema.sql` exists in built image context |
| Backend starts but auth/routes fail post-migration | Model/schema mismatch after normalization cutover | Inspect backend logs and verify active Alembic revision |
| Assistant container build/runtime fails | stale `assistant-v2` path assumptions | Verify compose, CI, and docs all reference `assistant/` |

## Documentation Rules

- Update this file whenever compose files, deploy scripts, or workflow deploy jobs change.
- Keep commands aligned with real service names and current branch behavior.
- Keep secrets as placeholders only.
