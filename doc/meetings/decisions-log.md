# Decisions Log

[<- Back to doc index](../README.md)

> **Status:** MUST HAVE
> **Last Updated:** 2026-04-22

---

## Decision Log Format

| Field | Description |
|---|---|
| **ID** | Unique decision ID |
| **Date** | When the decision was made |
| **Decision** | What was decided |
| **Rationale** | Why this decision was made |
| **Alternatives Considered** | Other options that were evaluated |
| **Impact** | What this changes or affects |

---

## D-001: Multi-Tenant Isolation via `school_id`

| Field | Value |
|---|---|
| **Date** | 2026-03-07 |
| **Decision** | All tenant data is isolated by a `school_id` foreign key on every table |
| **Rationale** | Simplest model for a SaaS platform with low cross-school query complexity; avoids separate database per tenant overhead |
| **Alternatives** | Separate databases per school (more isolation but higher ops cost) |
| **Impact** | All queries and route handlers must scope results by `school_id` |

## D-002: Celery and Redis for Background Jobs

| Field | Value |
|---|---|
| **Date** | 2026-03-07 |
| **Decision** | Long-running tasks (import, email) run via Celery workers backed by Redis |
| **Rationale** | Decouples slow operations from the request cycle; prevents API timeout failures on bulk imports |
| **Alternatives** | FastAPI background tasks (no retry, no status tracking); async queues |
| **Impact** | Requires Redis service; job status must be polled by the client |

## D-003: Campus Admin Replaces School IT

| Field | Value |
|---|---|
| **Date** | 2026-03-16 |
| **Decision** | All "School IT" labels, routes, and roles are renamed to "Campus Admin" |
| **Rationale** | "Campus Admin" better reflects the role's responsibilities; avoids confusion with IT support staff |
| **Alternatives** | Keep "School IT" name |
| **Impact** | Legacy `/school_it_*` routes redirect to `/campus_admin_*` for backward compatibility |

## D-004: Governance Hierarchy as Self-Referential Table

| Field | Value |
|---|---|
| **Date** | 2026-03-16 |
| **Decision** | Governance units (SSG, SG, ORG) are modeled as a single `governance_units` table with `parent_unit_id` self-reference |
| **Rationale** | Flexible for arbitrary depth; maps cleanly to Philippine HEI organization structure |
| **Alternatives** | Separate tables per unit type |
| **Impact** | Event and attendance scoping must resolve hierarchy depth at query time |

## D-005: Face Recognition as Primary Attendance Flow

| Field | Value |
|---|---|
| **Date** | 2026-03-28 |
| **Decision** | Project documentation standard uses face recognition as the attendance check-in flow instead of alternate attendance methods |
| **Rationale** | Keeps attendance behavior consistent across requirements, user guides, testing docs, and integration discussions |
| **Alternatives** | Maintain both alternate attendance methods and face-recognition attendance flows in the documentation |
| **Impact** | All documentation must describe attendance check-in as face-recognition-based unless a new scope decision is approved |

## D-006: Agentic Assistant as a Separate Service

| Field | Value |
|---|---|
| **Date** | 2026-04-22 |
| **Decision** | The AI assistant runs as a separate FastAPI service (`Assistant/`) beside the main backend, not embedded in it |
| **Rationale** | Separation of concerns; assistant has its own database, its own conversation storage, and its own JWT validation layer |
| **Alternatives** | Embed assistant routes inside the main backend; use a third-party hosted chat widget |
| **Impact** | Assistant needs its own compose service, its own `ASSISTANT_DB_URL`, and its own deployment config |
