[<- Back to docs index](../../README.md)

# Aura Project Audit Report

<!--nav-->
[← Navigation Map](../user/navigation.md) | [🏠 Home](/README.md) | [Project Audit →](project_audit.md)

---
<!--/nav-->

Audit date: 2026-04-17
Repository: `Aura_Merged_Project`
Audit mode: static repository review plus targeted local verification

## Scope

This audit covers:

- `backend/` FastAPI application, services, models, migrations, tests, and docs
- `frontend/` Vue 3 + Vite + Capacitor application, routing, API client layer, and build scripts
- `Assistant/` Python assistant service, MCP tool integration, auth handling, and storage model
- top-level Docker Compose, production Compose, environment templates, and CI workflow

This audit was performed against the current repository state without changing existing application code.

## Executive Summary

Aura is a large multi-service student operations platform that combines attendance tracking, governance management, sanctions workflows, school administration, branding, reporting, bulk student import, and an AI assistant. From a feature perspective, the project is substantial and already beyond prototype scope. The backend is the strongest layer: it has clear domain separation, strong test coverage, and a meaningful migration history. The frontend is also broad and functional, but it carries more integration complexity than it should. The assistant service is powerful, but it is currently the highest-risk operational component because it mixes LLM orchestration, direct data access, backend actions, and conversation storage in a single process.

Overall assessment:

- Product maturity: high
- Backend engineering maturity: medium-high
- Frontend engineering maturity: medium
- Security hardening maturity: medium
- Operational maturity: medium
- Assistant maturity: medium-low relative to risk surface

There were no obvious signs of a broken repository. Local verification passed for the full backend test suite, frontend build, frontend smoke tests, and Compose config validation. The main issues are not "the app does not work"; they are production hardening, contract consistency, and long-term maintainability.

## Project Overview

Aura is designed as a school-focused operations platform with several distinct user groups:

- students
- governance members such as SSG / SG / org roles
- school IT / campus administrators
- platform-level administrators

Core business capabilities observed in the repository:

- JWT-based authentication and session validation
- role-aware access control across school-scoped and platform-scoped users
- attendance tracking with event workflows and attendance status support
- face-recognition registration and attendance flows
- liveness / anti-spoof support using ONNX models
- public attendance / kiosk-style attendance scanning
- governance hierarchy management and governance-specific dashboards
- sanctions workflows and clearance deadlines
- school settings and branding
- Excel-based bulk student import backed by Celery workers
- notification and email flows
- assistant-driven analytics, query, and controlled backend actions

## Architecture Overview

### Frontend

The frontend is a Vue 3 single-page application built with Vite. It includes:

- desktop and mobile layout variants
- Capacitor integration for native mobile packaging
- a large route tree that supports student, governance, school IT, admin, and preview modes
- a central API client that normalizes backend responses and compensates for route inconsistencies
- dashboards, charts, sanctions views, governance views, profile/security views, and attendance workflows

### Backend

The backend is a FastAPI service with:

- SQLAlchemy ORM models
- Alembic migrations
- role-aware routers split across auth, users, attendance, events, reports, governance, sanctions, notifications, school settings, import, and security
- Celery worker and beat support
- face recognition and liveness services
- email transport abstraction and local Mailpit support

### Assistant

The assistant is a separate FastAPI service that:

- verifies JWTs from the main application
- stores conversations and daily usage
- exposes streaming assistant responses
- integrates MCP sub-apps for schema access, query access, school admin actions, and student import flows
- allows constrained backend actions and report fetches using the user's bearer token

### Infrastructure

The repository provides both development and production Docker Compose files covering:

- Postgres
- Redis
- backend
- frontend
- assistant
- Celery worker
- Celery beat
- Mailpit in development

## Strengths

- The backend domain structure is strong. Models, schemas, services, and routers are separated in a way that is understandable and scalable.
- The migration history is substantial and indicates real schema evolution rather than a throwaway prototype.
- Backend test coverage is materially better than expected for a project of this size.
- The project has good feature breadth with clear user-domain segmentation.
- The frontend successfully builds in production mode and appears organized around business workflows rather than isolated demo screens.
- The repository already includes backend documentation in `docs/backend/`, which is a positive sign for maintainability.
- Docker Compose is complete enough to describe the intended runtime topology for both local and production deployments.

## Detailed Findings

### High Severity

#### 1. Production configuration still permits insecure fallback secrets and credentials

What this means:

- the backend can start with a known fallback JWT secret
- production Compose still defaults to `postgres/postgres`
- some production defaults are still localhost-oriented rather than explicitly required

Impact:

- accidental insecure deployments are possible
- a misconfigured environment can silently boot with weak secrets instead of failing fast

Evidence:

- `backend/app/core/config.py` defaults `DATABASE_URL` and `SECRET_KEY`
- `docker-compose.prod.yml` defaults database credentials and login / CORS values

Relevant paths:

- `backend/app/core/config.py`
- `docker-compose.prod.yml`
- `.env.example`

Recommendation:

- remove production fallbacks for database credentials and secret keys
- fail startup if required production secrets are missing
- treat `docker-compose.prod.yml` as strict, not permissive

#### 2. Assistant production posture is too permissive for its risk level

What this means:

- assistant CORS currently allows all origins
- assistant auto-creates tables on startup
- assistant shares production-like responsibilities without equivalent hardening

Impact:

- change control for assistant schema is weak
- operational behavior is less predictable across environments
- an already high-trust service has a lower hardening baseline than the backend

Evidence:

- wildcard CORS in `Assistant/assistant.py`
- `Base.metadata.create_all(...)` behind `ASSISTANT_AUTO_MIGRATE=true`

Relevant paths:

- `Assistant/assistant.py`
- `docker-compose.prod.yml`

Recommendation:

- replace wildcard CORS with an explicit allowlist
- disable startup schema creation in production
- move assistant schema management to migrations
- document the assistant deployment and trust model separately

### Medium Severity

#### 3. Assistant database isolation is only partial and currently inconsistent

What this means:

- the assistant defines `ASSISTANT_DB_SCHEMA`, but tool execution still hardcodes `public`
- MCP query logic also hardcodes `public` in at least one metadata query
- production defaults point assistant and application services at the same database

Impact:

- schema isolation assumptions are unreliable
- future multi-schema or multi-tenant expansion will be harder
- auditing and least-privilege separation are weaker than they appear

Relevant paths:

- `Assistant/assistant.py`
- `Assistant/mcp/query_server.py`
- `Assistant/mcp/schema_server.py`
- `docker-compose.prod.yml`

Recommendation:

- either fully commit to shared-schema operation and document it clearly, or
- implement real schema separation end-to-end, including MCP utilities and connection roles

#### 4. Backend route conventions are inconsistent and the frontend compensates for that inconsistency

What this means:

- some routers are mounted under `/api`
- others expose their own prefixes directly
- the frontend API layer retries alternative routes to handle both shapes

Impact:

- client logic is more complex than needed
- reverse proxying and external API documentation become harder to reason about
- route drift is easier to introduce over time

Relevant paths:

- `backend/app/main.py`
- `backend/app/routers/`
- `backend/app/reports/router.py`
- `frontend/src/services/backendApi.js`

Recommendation:

- standardize route prefixes across the backend
- remove compatibility fallbacks from the frontend once the contract is normalized
- publish one canonical API prefix policy

#### 5. CI coverage is much thinner than the repository size suggests

What this means:

- GitHub Actions runs only two backend tests
- frontend "lint" checks only for unresolved merge markers
- frontend smoke tests are basic source-level assertions
- there is no visible assistant test suite in the repository

Impact:

- local quality can be much better than CI-enforced quality
- risky changes may merge without meaningful regression detection
- the assistant service currently has the least safety net despite high risk

Relevant paths:

- `.github/workflows/ci.yml`
- `frontend/scripts/lint.mjs`
- `frontend/scripts/smoke.test.mjs`
- `Assistant/`

Recommendation:

- run the full backend suite in CI or at least a representative matrix
- replace placeholder frontend lint with ESLint and optionally type checks
- add component / integration coverage for critical frontend workflows
- add direct tests for assistant auth, tool safety, and conversation flows

#### 6. Web session tokens are stored in `localStorage`

What this means:

- the frontend stores bearer tokens and auth metadata in browser storage
- any XSS issue would have direct access to the token

Impact:

- session theft risk is higher than with HTTP-only cookies
- the security posture depends more heavily on perfect frontend XSS hygiene

Relevant paths:

- `frontend/src/composables/useAuth.js`
- `frontend/src/services/sessionPersistence.js`
- `frontend/src/services/localAuth.js`

Recommendation:

- for web, prefer secure HTTP-only cookies if architecture allows
- for native, use secure storage instead of general-purpose local storage
- if tokens must remain client-readable, add a documented XSS hardening checklist and CSP enforcement

### Low Severity

#### 7. A few core files are already monoliths

Observed examples:

- `Assistant/assistant.py` exceeds 2,000 lines
- `frontend/src/services/backendApi.js` is very large
- `frontend/src/router/index.js` is very large

Impact:

- onboarding slows down
- changes become harder to isolate and test
- merge conflicts become more frequent

Recommendation:

- split the assistant by concerns: auth, tool execution, persistence, provider client, routes
- split the frontend API client by domain
- split router definitions by workspace or role

## Verification Performed

The following checks were executed locally during the audit:

- `docker compose config --quiet`
- `python -m compileall Backend Assistant`
- `python -m pytest -q backend/app/tests backend/tests`
- `npm run lint` in `frontend/`
- `npm run test` in `frontend/`
- `npm run build` in `frontend/`

Results:

- full backend suite passed: `238 passed`
- targeted CI-style backend tests passed
- frontend lint passed
- frontend smoke tests passed
- frontend production build passed

Warnings observed:

- deprecated `python_multipart` import warning from Starlette dependency path
- deprecated `httpx` TestClient shortcut usage in tests

These are maintenance warnings, not immediate functional failures.

## Improvement Priorities

### Priority 1: production hardening

- remove insecure fallback secrets and DB credentials
- lock down assistant CORS
- disable assistant startup schema creation in production
- document required production env vars and fail fast when missing

### Priority 2: contract simplification

- normalize backend route prefixes
- simplify frontend API fallback logic
- tighten assistant backend allowlist documentation and tests

### Priority 3: quality gates

- expand CI to run the full backend suite
- replace placeholder frontend lint with real linting
- add assistant tests
- add frontend integration coverage for login, dashboard bootstrap, attendance, and sanctions workflows

### Priority 4: maintainability refactors

- split large frontend service files by domain
- split large route files by workspace
- modularize the assistant service
- introduce bundle-size tracking for the frontend

## Suggested 30-Day Action Plan

### Week 1

- enforce required production secrets
- remove production credential fallbacks
- lock assistant CORS to known origins

### Week 2

- disable assistant auto-migrate in production
- define an assistant migration path
- decide on shared-schema vs isolated-schema strategy

### Week 3

- standardize backend route prefixes
- remove obsolete frontend path fallback branches after backend normalization

### Week 4

- upgrade CI to run the full backend suite
- replace frontend merge-marker lint with ESLint
- add an initial assistant test module for auth and tool safety

## Strategic Recommendations

- Treat the backend as the reference layer. It is currently the most disciplined part of the repository.
- Treat the assistant as a privileged integration boundary, not just another API service.
- Reduce frontend resilience logic that exists only to absorb backend inconsistency. It adds hidden complexity.
- Keep using docs for backend changes; the existing `docs/backend/` practice is worth preserving and extending.

## Limitations of This Audit

- The audit did not run the full Docker stack end-to-end.
- The audit did not execute live assistant tool calls against a running model provider.
- Existing local worktree changes were present and were not modified.
- This report evaluates the repository as it exists on 2026-04-17, not external infrastructure not captured in source control.

## Final Assessment

Aura is a serious application with real engineering work behind it. The codebase is not in rescue territory. The current gap is that the repository's operational and security posture has not fully caught up to the product's breadth, especially around production defaults, API contract consistency, and assistant-service hardening. If those areas are addressed, the project can move from "feature-rich and functional" to "defensible and maintainable in production."

