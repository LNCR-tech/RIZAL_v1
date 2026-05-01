# Backend Changelog

[<- Back to doc index](../README.md)

> **Status:** ACTIVE
> **Last Updated:** 2026-04-28
> **Purpose:** Backend-only filtered and finalized change summary for AURA v3.2.

---

## SSOT Rule

- Raw change details live in [branch-updates.md](./branch-updates.md)
- This file keeps only backend-scoped, finalized wording
- Do not duplicate full branch narratives here
- Rule: **Write once, reference everywhere**

---

## Finalized Backend Entries

### [2026-04-28] Repository Restructure, Google OAuth, and Testing Infrastructure

- Implemented Google OAuth authentication with backend `/auth/google` endpoint supporting credential exchange, user lookup/creation, and JWT token generation.
- Added new database tables: `issue_reports`, `user_feedbacks`, `reports` with lookup tables for dynamic types/categories; added age/gender columns to users table.
- Refactored backend models from `app/models/aura_norm` to `app/models/core` and updated all import references.
- Deprecated unused environment variables: `AURA_NORM_ENABLED`, `AURA_NORM_SCHEMA`, `DATABASE_ADMIN_URL`.
- Added comprehensive integration tests for assistant↔backend communication and MCP tools↔database queries.
- Fixed assistant DATABASE_URL connectivity so MCP tools can query backend database directly.
- Added attendance validation service for improved governance workspace data integrity.
- Enhanced backend normalizers with improved data transformation logic.
- Fixed dotenv loading order in assistant to ensure SECRET_KEY is available for JWT verification.
- Handled CPython shutdown crashes (exit codes 134/139) as non-fatal in test environments.
- Rewrote Google auth tests to use shared conftest fixtures instead of standalone SQLite.
- **Source commits:** `0b2262a`, `8319cec`, `e4c83fc`, `5df22c6`, `d423427`, `6541f0b`, `8271112`, `4fe6541`, `b6d2843`, `a70910f`, `d53f7f9`, `6a3fa07`, `fd00aa4`, `c1c6196`, `fd1c646`, `57c5ee2`, `e5a8e27`, `c8896b9`
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-28] Documentation Cleanup and Service Reorganization

- Moved backend-specific documentation from `docs/` to `backend/docs/` for better service isolation.
- Moved database documentation to `database/` folder.
- Cleaned up redundant documentation files and fixed stale path references.
- Updated all navigation links to reflect new documentation structure.
- **Source commits:** `885f81f`, `011f56b`, `8055f0c`
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-27] Normalized-Schema Cutover Stabilization and Startup/Auth Recovery

- Aligned backend models and sanctions logic to normalized-schema expectations and moved canonical schema SQL under `backend/app/db/schema.sql`.
- Stabilized Alembic deployment behavior with non-destructive normalization migration logic, conflicting-head merge migration, path-resolution fixes, and duplicate-object idempotency checks.
- Resolved post-cutover runtime mismatches that blocked startup/auth and affected governance, notification, subscription, and seeder-linked backend paths.
- **Source commits:** `20ea2a8`, `7a8f47a`, `28f3903`, `038cbbf`, `273154d`, `5919f1c`, `11d07e0`, `ad7aa0e`, `28ce3b1`, `f3b0689`, `4c8805b`, `2a25772`, `0adef00`
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-27] Assistant Service Rename and Deployment Wiring Sync

- Renamed `assistant-v2/` to `assistant/` and synchronized backend-adjacent compose/CI/doc references to prevent path drift in deployment automation.
- Tightened deployment safeguards by improving env validation and branch-gated auto-deploy behavior during pre-production integration.
- Kept backend deployment paths consistent after merge-forward into pre-production.
- **Source commits:** `7028cdc`, `cffa80b`, `a7ab0a9`, `9323700`, `27cab35`
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-26] Pgvector Face-Embedding Support and Validation Hardening

- Added pgvector-backed face embedding migration/runtime support for attendance matching, including indexing/backfill-oriented operational flow.
- Switched production database image to `pgvector/pgvector:pg15` to guarantee extension availability during deployment.
- Added guardrails for manual Pydantic validation errors in school-facing backend logic to avoid crash paths.
- **Source commits:** `acd882f`, `c4ae534`, `3ef9a09`
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-26] CI/CD and Production Compose Hardening

- Added and refined production CI/CD workflows (`ci.yml`, `deploy-ec2.yml`) with stronger compose validation and backend build/deploy safety.
- Hardened production compose defaults (secret fallback and explicit bootstrap credential wiring) and deployment scripts for host bind-mount directory ownership preparation.
- Aligned repository cleanup and release flow so backend deployment is reproducible on AWS/Ubuntu paths.
- **Source commits:** `588d4d7`, `bb5da4f`, `ac2e03f`, `03a0294`, `f723626`, `d868e98`, `f10055f`
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-25] Face Error Normalization, Session-Time Fixes, and Docker Runtime Reliability

- Normalized backend face attendance/verification error handling and aligned session-expiry timezone comparisons plus event-status enum casing behavior.
- Added migration safety and health checks to reduce first-run and startup failure cases in compose-managed environments.
- Updated compose runtime behavior for persistent host data mounts, seed opt-in profile behavior, and non-conflicting backend port/env wiring.
- **Source commits:** `a29a0ac`, `7823fa6`, `f73133c`, `f155a4c`, `25f401d`, `f8aa30e`, `34b1dd1`, `2ec8809`, `ef05af9`, `e347c9f`, `2e1f78b`, `ccaf3a4`, `5576224`
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-25] Timezone-Aware Timestamp Migration and Event-Create Idempotency

- Migrated attendance and common system timestamp persistence to timezone-aware UTC paths and aligned backend time helpers and serializers.
- Added event-create idempotency fields and behavior so repeated create submissions can safely resolve to one stored event for the same user/key pair.
- Updated backend runtime behavior docs and tests to cover the migration and idempotency behavior.
- **Source commits:** `570f250`
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-25] Strict SG/ORG Event Visibility and Face-Recognition Account Locking

- Enforced stricter student department/program scope visibility on SG/ORG event paths.
- Hardened face-recognition account-lock handling and updated route-level tests for governance and face attendance flows.
- Synced policy documentation for face-attendance mode behavior.
- **Source commits:** `eab6f3b`
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-25] User Schema Expansion for Name Prefix/Suffix and Faculty Profiles

- Added user `prefix` and `suffix` columns and corresponding model support.
- Added faculty profile schema/model support through a dedicated migration.
- Kept compatibility with existing user/profile behavior while expanding schema coverage.
- **Source commits:** `c306c69`, `d2a67b5`
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-25] Governance Member Controls and Privileged Face-Gate Updates

- Expanded governance member management and related security-center/session handling paths.
- Added or refined privileged face-gate toggles and related attendance/security schema usage.
- Added or updated tests around the updated governance and privileged-face behavior.
- **Source commits:** `6d72849`, `2657db0`
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-25] Startup Reliability: Optional Bootstrap Credentials and Non-Fatal Email Init

- Made bootstrap admin credentials optional by falling back to configured defaults in app settings.
- Changed backend startup email initialization failure from hard-fail to warning so service boot can continue in degraded mode.
- Updated startup docs for local development reliability.
- **Source commits:** `410f225`, `ca85538`
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-25] Single-Command Compose Startup and Seeder Toggle Wiring

- Added compose-level migrate/bootstrap startup flow to reduce manual startup sequencing.
- Added and then refined `SEED_DATABASE` control so seeding toggle ownership remains in `seeder/variables.py` logic.
- Synced `.env.example` and compose wiring for the new startup/seeding behavior.
- **Source commits:** `b6b3dbe`, `5483f08`, `49ec7a5`
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-24] Mail Transport Merge Sync (Mailpit/Mailjet Behavior Alignment)

- Merged backend and compose behavior updates for mail transport configuration pathways.
- Synced backend email transport config/tests with the merged state and updated env documentation.
- **Source commits:** `24e41f7`
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-17] Railway Runtime Supervisor and Multi-Head Alembic Startup

- Added a backend runtime supervisor path for constrained Railway deployments so one service can launch the API, optional migrations and seeding, Celery worker, and Celery beat.
- Switched operational migration guidance from `alembic upgrade head` to `alembic upgrade heads` because the repository currently has multiple Alembic heads.
- Added runtime startup toggles and small-plan worker controls for deployment tuning.
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-17] Gmail-First Email Transport and Optional Mailpit Local Testing

- Removed hardcoded Mailpit SMTP overrides from `docker-compose.yml` for `backend`, `worker`, and `beat`.
- Documented Gmail API as the environment-driven default transport while keeping Mailpit available for local SMTP inbox testing.
- Updated backend email smoke-test and local delivery guidance accordingly.
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-17] Privileged Face MFA, Remember-Me Sessions, and Synced User Preferences

- Restored privileged face-scan MFA for `admin` and `campus_admin` logins.
- Added `remember_me` session extension support and new backend user app preference routes for dark mode and font-size sync.
- Added the `user_app_preferences` persistence model and migration support.
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-17] Platform-Admin Fallback Access and Governance Sanctions Hardening

- Restored sanctions dashboard and school-settings access for platform admins whose `school_id` remains `NULL`.
- Relaxed sanctions route access for governance users by honoring governance scope, delegation, and `manage_events` fallback where appropriate.
- Tightened sanctions tests and route-level behavior around scoped governance ownership.
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-16] Aura Branding Alignment and Assistant/Workspace Sync

- Standardized backend notification and email fallback copy to `Aura`.
- Synced current project state across backend notifications, transport helpers, and deployment/runtime configuration.
- Added supporting audit-oriented project documentation in the repository.
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-13] Local SMTP/Mailpit Support and Workspace Update Sync

- Added local Mailpit-backed SMTP testing support for backend outbound email.
- Added editable backend email format references and a local email testing guide.
- Improved import email delivery behavior and related backend tests.
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-03] InsightFace Migration and Environment Example

- Migrated face recognition engine to InsightFace.
- Removed legacy `dlib`, `face-recognition`, and `face_recognition_models` dependencies to simplify builds.
- Added backend `.env.example` for local development setup.
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-03-28] Assistant MCP Integration and Import Email Privacy Reversion

- Reverted bulk import onboarding email to obscure temporary credentials, routing users to "Forgot Password" instead.
- Integrated MCP sub-apps directly via proxy mounts inside the `Assistant` engine.
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-03-28] Bulk Import and Email Sender Fixes

- Fixed bulk import onboarding emails and standardized outbound email on Gmail API.
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-03-27] Attendance Refactor and Deployment Hardening

- Added backend attendance actions for absent and excused flows.
- Stabilized Docker and backend runtime behavior for development and deployment environments.
- Added backend-support administrative tooling under `tools/`.
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-03-22] Face Recognition Attendance Alignment and Auth Hardening

- Aligned backend attendance documentation to a face-recognition-only flow.
- Hardened token and session validation across attendance routes.
- Improved governance-related backend paging behavior.
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-03-21] Event Attendance Override Windows

- Added `present_until_override_at` and `late_until_override_at` to `events`.
- Cleaned backend helper code and documented backend modules.
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-03-18] Alembic Environment Loading Fix

- Updated Alembic environment loading so local and Docker migrations resolve `DATABASE_URL` consistently.
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-03-17] Auth Hardening and Health Monitoring

- Added `GET /health` and database pool tuning configuration.
- Synced Campus Admin and school activation behavior in auth flows.
- Improved login query performance and session rejection rules.
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-03-16] Governance Hierarchy and Production Backend Path

- Added governance hierarchy backend model and permission support.
- Added attendance window controls, scoped event logic, `user_face_profiles`, and production deployment assets.
- Added backend load testing support.
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-03-14] Face Automation Backend Support

- Added backend support for face liveness, geolocation checks, Celery Beat event sync, and Mailpit-based email testing.
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-03-13] SSG RBAC and SMTP Integration

- Added backend RBAC support for SSG workflows and integrated SMTP and email-service changes.
- **Raw source:** [branch-updates.md](./branch-updates.md)
