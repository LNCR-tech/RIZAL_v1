# Backend Rewrite Plan (DB Normalization)

Goal: migrate toward the normalized target schema (`db_normalized/new_db_schema.sql`) **without any frontend changes**.

## Non-Negotiable Constraint

Frontend-facing REST API stays stable:
- same routes/paths
- same request bodies
- same response shapes

All adaptation happens behind the API (models/services/queries/serialization), and optionally with transitional DB compatibility views.

## Recommended Migration Shape

1. **Side-by-side schema**: create normalized tables in a separate schema (example: `aura_norm`) while keeping current `public.*` tables intact.
2. **Backfill**: copy data from legacy tables/JSON into normalized tables.
3. **Dual-write window**: backend writes to both old + new (short-lived).
4. **Cutover reads**: backend reads from normalized tables (API output remains identical).
5. **Cleanup**: drop legacy columns/tables only after parity is confirmed.

## What Changes In The Backend (High Level)

- SQLAlchemy models: add normalized child tables for data currently stored in JSON blobs (sanction item definitions, note tags, delegation scopes, etc.).
- Service/query layer: replace “read JSON column” with JOINs to normalized tables and then *re-assemble the same response payloads*.
- Filtering: where redundant `school_id` columns are removed in normalized tables, derive tenant filters via JOIN chains (`event_id -> events.school_id`, etc.).
- Preferences: keep `user_notification_preferences` as the legacy-compatible source of truth until the backend is explicitly updated; optional 4NF tables can be introduced side-by-side without affecting runtime.

## Important Domain Distinction: Governance Unit Types vs Auth Roles

- Governance unit types are effectively **hardcoded enums** in the backend (example: `SSG`, `SG`, `ORG`). Treat these as application-level constants unless you explicitly plan a backend change to make them data-driven.
- Auth/permission roles like `admin`, `campus_admin`, `student`, `faculty`, `school_it`, etc. are **data-driven** and live in the `roles` table. Normalization work should preserve that: keep roles as a relational table and keep assignment via `user_roles` (ideally with a composite PK/unique constraint on `(user_id, role_id)`).

## Transitional Option: DB Compatibility Views

If you want the backend to switch over with minimal query churn:
- create `aura_compat.*` views that expose the **old column shapes** while reading from `aura_norm.*`
- point backend read models at `aura_compat` during cutover (writes still handled in services)

This avoids any frontend changes because the API still emits the same JSON contracts.
