# Migrations Log

> **Status:** Maintained
> **Last Updated:** 2026-04-27
>
> **Source of truth:**
> - `backend/alembic/versions/`
> - `backend/alembic/env.py`
> - `backend/app/db/schema.sql`

---

## Purpose

This page tracks the active migration chain used by `integrate/pilot-merge`, including the normalized-schema cutover and the recovery fixes added on April 27, 2026.

## Current Migration State

| Item | Value |
|---|---|
| Migration directory | `backend/alembic/versions/` |
| Total migration files | `11` |
| Baseline revision | `e79235331d71` |
| Current merged head revision | `c7115ee2a54d` |
| Merge-head parents | `a9f3c1e2d4b5`, `f7a8b9c0d1e2` |
| Normalized schema SQL path | `backend/app/db/schema.sql` |

## Operational Workflow

```bash
# Validate revision graph
docker compose exec backend alembic history

# Show current DB revision
docker compose exec backend alembic current

# Apply all pending heads (recommended in this branch)
docker compose exec backend alembic upgrade heads

# Target single merge head (optional explicit form)
docker compose exec backend alembic upgrade c7115ee2a54d
```

Production migration-first deployment path:

```bash
docker compose -f docker-compose.prod.yml run --rm migrate
docker compose -f docker-compose.prod.yml run --rm bootstrap
docker compose -f docker-compose.prod.yml up --build -d
```

## Revision Timeline (Active Chain)

| Date | Revision | Summary |
|---|---|---|
| 2026-04-24 | `e79235331d71` | Initial baseline migration for current branch lineage. |
| 2026-04-24 | `7d43d19e7a58` | Added `event_types` and `event_type_id` relation support. |
| 2026-04-25 | `a1b2c3d4e5f6` | Added user `prefix` and `suffix` columns. |
| 2026-04-25 | `b2c3d4e5f6a7` | Added faculty profiles table. |
| 2026-04-25 | `c4d5e6f7a8b9` | Made attendance timestamps timezone-aware (UTC). |
| 2026-04-25 | `d5e6f7a8b9c0` | Made common system timestamps timezone-aware (UTC). |
| 2026-04-25 | `e6f7a8b9c0d1` | Added event-create idempotency fields. |
| 2026-04-25 | `f7a8b9c0d1e2` | Added pgvector-backed `student_face_embeddings` structure and indexes. |
| 2026-04-26 | `f19c2a7b3d10` | Added side-by-side `aura_norm` normalized schema creation path. |
| 2026-04-27 | `a9f3c1e2d4b5` | Replaced public schema path with normalized schema migration flow (non-destructive and idempotency hardened). |
| 2026-04-27 | `c7115ee2a54d` | Merge migration to reconcile normalization and face-recognition heads. |

## April 27 Recovery Notes

- Alembic environment loading was hardened to initialize Python path before app imports.
- Normalization migration pathing was updated to use official schema SQL location under `backend/app/db`.
- Duplicate-object/idempotency handling was added to avoid repeated migration failures.
- Conflicting heads were merged to restore deterministic deployment.

## Risk Controls

- Treat normalization migrations as forward-only for production unless a tested rollback plan exists.
- Validate `backend/app/db/schema.sql` availability in image/build context before running migration jobs.
- Keep migration and model changes in the same change set to avoid startup-time ORM/schema drift.
- Run `alembic history` and `alembic current` after every deploy that includes schema changes.

## Verification Checklist

1. Run migration graph checks:
   - `alembic history`
   - `alembic current`
2. Verify backend startup and `/health`.
3. Validate auth login, event creation, attendance write, and sanctions read paths.
4. Confirm face attendance paths after pgvector migration:
   - registration/update
   - matching flow
   - fallback behavior on missing embeddings

## Traceability

- Backend changelog mapping: [../../changelog/backend.md](../../changelog/backend.md)
- Raw branch mapping: [../../changelog/branch-updates.md](../../changelog/branch-updates.md)
- Deployment context: [../deployment/deployment-guide.md](../deployment/deployment-guide.md)
