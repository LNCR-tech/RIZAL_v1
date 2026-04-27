# Backend Normalized Schema (aura_norm) Guide

This repo contains a **proposed normalized schema** in `db_normalized/new_db_schema.sql`.

To avoid breaking the current website behavior (and to avoid frontend changes), the backend introduces this schema **side-by-side** under a separate PostgreSQL schema named `aura_norm`.

## What This Change Does (and Does Not Do)

**Does:**
- Adds an Alembic revision that can create the `aura_norm` schema + tables from `db_normalized/new_db_schema.sql`.
- Adds a small set of SQLAlchemy model stubs under `backend/app/models/aura_norm/` for future incremental adoption.

**Does not (yet):**
- Migrate any production data from `public.*` into `aura_norm.*`.
- Switch the running API to read/write `aura_norm.*`.
- Change any frontend-facing REST routes, request bodies, or response shapes.

## How To Apply The Migration

From `backend/`:

1. Ensure `DATABASE_URL` points at the DB you want to migrate.
2. Run:
   - `alembic upgrade head`

The revision `backend/alembic/versions/f19c2a7b3d10_create_aura_norm_schema.py` reads and executes `db_normalized/new_db_schema.sql` statement-by-statement.

## How To Verify

In psql:
- `\\dn` should show `aura_norm`
- `\\dt aura_norm.*` should show the normalized tables (e.g. `schools`, `users`, `events`, …)

## Notes / Caveats

- The SQL includes `CREATE EXTENSION IF NOT EXISTS citext;`. On some managed Postgres providers this requires elevated privileges.
- Because this is side-by-side, the current app can continue using `public.*` tables until the backend is explicitly updated to cut over.

## Optional Settings (No Behavior Change By Default)

The backend settings now include:
- `AURA_NORM_ENABLED` (default: false)
- `AURA_NORM_SCHEMA` (default: `aura_norm`)

These are placeholders for a future backend cutover; current endpoints still use `public.*`.
