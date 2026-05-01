# Branch Updates Log

> **Status:** ACTIVE
> **Last Updated:** 2026-05-02
> **Purpose:** Raw branch-level update log and changelog single source of truth (SSOT).

---

## SSOT Rule

- `branch-updates.md` = raw updates written first
- `backend.md` = backend-only filtered, finalized summary
- `frontend.md` = frontend-only filtered, finalized summary
- Rule: **Write once, reference everywhere**

## How To Use This File

1. Record the raw branch update here first.
2. When the change is stable, add the filtered summary to [backend.md](./backend.md) or [frontend.md](./frontend.md).
3. Keep branch language raw here and product language finalized in the filtered changelog files.
4. Record removals here when tracked files disappear upstream so the combined docs still preserve that history.

---

## Raw Updates

### [2026-05-02] `integrate/pilot-merge`

- **Status:** Recorded
- **Raw change:** Governance event creation now initializes timing controls from school settings and keeps them user-overridable per event.
- **Raw frontend scope:** `SgEventsView` create-event UI now loads school event defaults before create, exposes create-time timing fields (`early_check_in_minutes`, `late_threshold_minutes`, `sign_out_grace_minutes`, `sign_out_open_delay_minutes`), blocks submit when defaults are unavailable, and sends explicit timing values in create payloads. Governance Workspace create-event modal (`EventEditorSheet`) now seeds those same fields from school defaults instead of `0` when creating new events. Frontend school-settings normalization now includes event default timing fields.
- **Source files:** `frontend-web/src/views/dashboard/SgEventsView.vue`, `frontend-web/src/views/dashboard/GovernanceWorkspaceView.vue`, `frontend-web/src/components/events/EventEditorSheet.vue`, `frontend-web/src/services/backendNormalizers.js`
- **Reference targets:** [frontend.md](./frontend.md)

### Repository and Shared Operations History

### [2026-04-28] `integrate/pilot-merge`

- **Status:** Recorded
- **Raw change:** Major repository restructure, CI/CD expansion, Google OAuth integration, and comprehensive testing infrastructure.
- **Raw repository scope:** Split `frontend/` into `frontend-web/` and `frontend-apk/` for clearer separation of web and mobile builds; added comprehensive E2E testing with Playwright covering frontend↔backend and frontend↔assistant flows; added integration tests for assistant↔backend and MCP tools↔DB; implemented Google OAuth authentication flow with backend `/auth/google` endpoint and frontend sign-in components; added new database tables (`issue_reports`, `user_feedbacks`, `reports`) with age/gender columns to users; implemented forgot password flow; added responsive layout with viewport-based switching and desktop login split-screen redesign; enhanced assistant with thought tag streaming as collapsible UI sections and DATABASE_URL connectivity for MCP tools; hardened CI pipeline with frontend gates, diagnostics, and comprehensive test coverage documentation (`CI_PIPELINE.txt`); cleaned up documentation structure by moving service-specific docs to their respective folders; fixed numerous E2E test issues including localStorage session bleed, stale chunk errors, and Vite HMR timeouts; replaced corrupt PWA icons and logo images; deprecated unused env vars (`AURA_NORM_ENABLED`, `AURA_NORM_SCHEMA`, `DATABASE_ADMIN_URL`); refactored backend models from `app/models/aura_norm` to `app/models/core`; added `BasePagination` component, `RouteErrorBoundary`, and `NotFoundView` to frontend; improved governance workspace with attendance validation service and backend normalizer enhancements.
- **Source commits:** `2d59520` - "feat(ci): harden frontend gates and diagnostics"; `532f88e` - "feat: responsive layout - viewport-based switching + desktop login split-screen redesign"; `0b1637c` - "fix: remove %BASE_URL% placeholders from index.html"; `8319cec` - "feat: add issue_reports and user_feedbacks with lookup tables for dynamic types/categories"; `e4c83fc` - "feat: add issue_reports, user_feedbacks tables and age/gender to users"; `5df22c6` - "feat: add reports table and age/gender columns to users"; `089d320` - "fix: properly handle thought tag streaming across chunk boundaries and tool turns"; `807058d` - "Revert 'fix: strip thought tags from conversation titles and sidebar last_message'"; `2a23462` - "fix: strip thought tags from conversation titles and sidebar last_message"; `160f4b1` - "feat: store raw thought tags in DB content, parse on frontend when loading history"; `d3c29b6` - "feat: add chevron indicator to thought toggle"; `2d8af1f` - "fix: always start fresh conversation on chat open instead of restoring last session"; `dcd8d94` - "chore: align docker ports with pilot stack"; `b6d2843` - "fix: add DATABASE_URL to assistant env so MCP tools can query backend database"; `0a06d33` - "feat: stream thought tags as collapsible sections in chat UI"; `9c037c0` - "fix: strip thought tags from assistant model output"; `a70910f` - "fix: move dotenv load to auth.py before SECRET_KEY is read at module level"; `d53f7f9` - "fix: load .env in assistant main.py so SECRET_KEY is available for JWT verification"; `74ded60` - "fix: replace corrupt logo/pwa images and add binary gitattributes"; `c5fd561` - "fix: replace corrupt pwa icons with correct ones from production"; `6a98429` - "fix: remove base path override from vite.config causing broken logo paths"; `00a13fa` - "feat: sync frontend-web/src from production branch"; `1f35bd6` - "fix: update alembic env.py import to app.models.core"; `d423427` - "refactor: rename app/models/aura_norm to app/models/core and remove dead config"; `6541f0b` - "chore: deprecate AURA_NORM_ENABLED and AURA_NORM_SCHEMA from backend env"; `8271112` - "chore: deprecate unused DATABASE_ADMIN_URL from backend env"; `4fe6541` - "fix: sync backend .env and .env.example with config.py"; `1b5b555` - "fix(frontend): auto-reload on stale chunk error instead of showing boundary UI"; `999fc22` - "fix(frontend): no-cache index.html to prevent stale chunk errors"; `6a3fa07` - "fix: handle exit code 134 (SIGABRT) alongside 139 (SIGSEGV) as non-fatal CPython shutdown crashes"; `fd00aa4` - "fix: rewrite test_google_auth.py to use shared conftest fixtures instead of standalone SQLite"; `0b2262a` - "feat: port Google OAuth authentication from aurav3-production"; `8b2115e` - "docs: correctly separate CI improvements from CD in CI_PIPELINE.txt TODO section"; `24ed820` - "docs: add TODO section to CI_PIPELINE.txt"; `3271e61` - "docs: add CI_PIPELINE.txt summarizing all test jobs and coverage"; `45232f1` - "fix: remove frontend-assistant e2e tests"; `4c5db7f` - "debug: add page URL and nav rail count logging when chat pill not found"; `9eaf51e` - "fix: rewrite assistant e2e tests to match actual chat state"; `2ac9e7f` - "fix: two-step chat open flow in e2e tests"; `a200c89` - "fix: correct chat trigger selector to aria-label"; `a885c0e` - "fix: remove terms modal click from e2e login helper"; `c22a53c` - "fix: remove desktop-blocking screen from App.vue"; `92e3eae` - "chore: add frontend-web .gitignore"; `7480a08` - "fix: use mobile viewport in Playwright"; `9292715` - "fix: remove GitHub Actions base path auto-detection from vite.config.js"; `838c005` - "fix: pass VITE_APP_BASE_PATH=/ to Vite webServer"; `110b59b` - "fix: explicitly clear localhost:5173 localStorage in storageState config"; `a6c8a54` - "fix: use context().addInitScript to clear localStorage"; `007d691` - "debug: add page HTML logging and video recording"; `9a7e928` - "fix: seed backend test data in e2e CI job"; `2a741a8` - "fix: use addInitScript to clear localStorage before every login test"; `4b1838c` - "fix: replace networkidle with domcontentloaded + waitForSelector"; `bb3f738` - "fix: wait for networkidle on goto and increase action/navigation timeouts"; `4f5562b` - "fix: replace custom test.extend context fixture with storageState reset"; `9633574` - "fix: add mcp_servers and backend to pyrightconfig extraPaths"; `d0f467c` - "fix: add JSDoc type annotations to e2e login helpers"; `3aadf1d` - "perf: bump Playwright workers to 3 for 4-vCPU public runner"; `fbaffc5` - "fix: use fresh browser context per test"; `092bd36` - "fix: clear localStorage before every e2e test"; `57c5ee2` - "fix: ignore segfault on exit (139) in integration-tests CI job"; `6ff5e86` - "fix: force VITE_APP_BASE_PATH=/ in e2e CI job"; `b123495` - "fix: exclude test_integration.py from assistant unit test run"; `770f599` - "Reapply 'fix: TermsModal now emits agree/decline'"; `e3d1925` - "Revert 'fix: TermsModal now emits agree/decline'"; `354ee69` - "fix: TermsModal now emits agree/decline instead of close"; `78f4cfc` - "test: add Playwright E2E tests for frontend↔backend and frontend↔assistant"; `fd1c646` - "ci: add integration tests job to CI pipeline"; `28dc7e5` - "fix: silence baseUrl deprecation in jsconfig.json"; `c1c6196` - "test: add in-process integration tests for assistant↔backend"; `b9b8cfd` - "fix: add defer to runtime-config.js script tag"; `e5a8e27` - "fix: remove stale attendanceFlow imports from useGovernanceWorkspace"; `885f81f` - "deleted redundant documentation"; `011f56b` - "clean up env files, fix stale frontend/ doc references"; `8055f0c` - "split frontend/ into frontend-web/ and frontend-apk/"; `c8896b9` - "port production: forgot password flow, RouteErrorBoundary, NotFoundView"; `8bb49ea` - "fix: Add forgotPassword export to backendApi.js"; `59e02ea` - "fix: Use backendApi.js instead of non-existent api.js"; `d0bc443` - "feat: Add forgot password flow and remove Quick Attendance/Mock Views"; `997ed84` - "remove accidentally committed error_log.txt"; `ab24330` - "remove obsolete repair_rfid.py script"
- **Reference targets:** [backend.md](./backend.md), [frontend.md](./frontend.md), [../technical/deployment/ci-cd-pipeline.md](../technical/deployment/ci-cd-pipeline.md), [../technical/testing/test-plan.md](../technical/testing/test-plan.md)

### [2026-04-27] `integrate/pilot-merge`

- **Status:** Recorded
- **Raw change:** Stabilized normalized-schema deployment and resolved backend startup/auth regressions.
- **Raw repository scope:** Completed the normalized-schema migration recovery path by adding non-destructive guards, merging conflicting Alembic heads, moving canonical schema SQL under `backend/app/db/schema.sql`, hardening Alembic path resolution in Docker, and aligning backend models/services/routers to the normalized schema contract.
- **Source commits:** `20ea2a8` - "fix: align sanctions service with normalized schema and fix alembic env"; `7a8f47a` - "fix: make normalized schema migration non-destructive"; `28f3903` - "fix(migrations): merge conflicting heads to restore deployment"; `038cbbf` - "fix(deploy): fix missing db_normalized folder in Docker production build"; `273154d` - "chore: move master schema to backend/app/db and revert docker build hacks"; `5919f1c` - "debug(migrations): add verbose logging to pinpoint normalization failure"; `855b411` - "fix(deploy): use explicit migration-first workflow for better logging"; `11d07e0` - "debug(migrations): final clean rewrite with explicit path logging and flushing"; `ad7aa0e` - "debug(migrations): bulletproof path resolution and package initialization"; `28ce3b1` - "fix(migrations): initialize sys.path before app imports in env.py"; `f3b0689` - "fix(migrations): update parent migration path logic to use official schema location"; `4c8805b` - "fix(migrations): add idempotency check to avoid duplicate object errors"; `2a25772` - "chore: align backend models to normalized schema"; `0adef00` - "fix: resolve schema alignment issues blocking backend startup and auth flow"
- **Reference targets:** [backend.md](./backend.md), [../technical/database/migrations.md](../technical/database/migrations.md), [../technical/backend/overview.md](../technical/backend/overview.md)

### [2026-04-27] `integrate/pilot-merge`

- **Status:** Recorded
- **Raw change:** Synced assistant-service rename and tightened deployment safety controls.
- **Raw repository scope:** Renamed `assistant-v2/` to `assistant/` and updated compose/CI/doc references, restored accidentally removed frontend AI components and seeder demo generator after production cleanup, and added stricter deployment checks/branch gates for automated release flows.
- **Source commits:** `7028cdc` - "chore: rename assistant-v2 to assistant and cleanup legacy schema files"; `cffa80b` - "fix: update docker and ci configs to use renamed assistant directory"; `b692243` - "fix(frontend): restore critical AI components accidentally deleted in branch sync"; `93f7d02` - "fix(seeder): restore demo data generator accidentally removed in production cleanup"; `a7ab0a9` - "ci: restrict auto-deploy to production branches"; `9323700` - "ci: fix missing env file in deploy-ec2 validation and gitignore casing"; `27cab35` - "merge: integrate pilot fixes into pre-production"
- **Reference targets:** [backend.md](./backend.md), [frontend.md](./frontend.md), [../technical/deployment/ci-cd-pipeline.md](../technical/deployment/ci-cd-pipeline.md)

### [2026-04-26] `integrate/pilot-merge`

- **Status:** Recorded
- **Raw change:** Added production CI/CD pipeline coverage and hardened AWS deployment defaults.
- **Raw repository scope:** Added and refined GitHub Actions workflows (`ci.yml`, `deploy-ec2.yml`), expanded trigger controls for pre-production and deployment branches, hardened compose validation and frontend/backend build checks, and updated production scripts to ensure host bind-mount directories and ownership are created before stack startup.
- **Source commits:** `588d4d7` - "Add deploy-ec2.yml workflow file"; `bb5da4f` - "Refactor CI/CD workflow for backend deployment"; `ac2e03f` - "chore: remove demo seeder, test files, dev artifacts; add CI/CD pipeline"; `431c278` - "ci: add Pre-Production-v1 branch to CI/CD triggers"; `a023318` - "chore: switch deployment branch to Pre-Production-v1"; `6194936` - "fix(ci): fix compose-config env path, frontend casing, node.js warnings"; `bf7a8e7` - "fix(ci): remove non-existent lint/test scripts from frontend checks"; `8f11fe2` - "fix(ci): remove invalid script_stop input from ssh-action"; `03a0294` - "refactor: DRY docker-compose.prod.yml, clean .env, merge best CI/CD from aura_ci_cd"; `fc8fc15` - "ci: add aura_ci_cd branch to CI/CD triggers"; `f723626` - "fix: use fallback default for SECRET_KEY in compose (prevents deploy failure)"; `c4ae534` - "fix: use pgvector/pgvector:pg15 image for vector extension support"; `d868e98` - "fix: add required --admin-email and --admin-password args to bootstrap command"; `f10055f` - "fix(deploy): add bind-mount directory creation and ownership in all deploy paths"; `1ffce65` - "chore: update .gitignore with docker-data, ssh keys, and security docs"
- **Reference targets:** [backend.md](./backend.md), [frontend.md](./frontend.md), [../technical/deployment/deployment-guide.md](../technical/deployment/deployment-guide.md), [../technical/deployment/ci-cd-pipeline.md](../technical/deployment/ci-cd-pipeline.md)

### [2026-04-26] `integrate/pilot-merge`

- **Status:** Recorded
- **Raw change:** Introduced normalized-schema planning assets and synchronized latest pre-production frontend state.
- **Raw repository scope:** Added `db_normalized/` schema-playground docs/artifacts, refreshed schema diagrams and SQL references, and replaced frontend state twice to align with main/pre-production snapshots while keeping release integration active.
- **Source commits:** `3826af1` - "db_normalized: add normalized schema playground and docs"; `1b08d36` - "Replace frontend with main version"; `a0e7e09` - "newest frontend + pre production"; `3ef9a09` - "fix(school): catch ValidationError from manual Pydantic form instantiation"
- **Reference targets:** [backend.md](./backend.md), [frontend.md](./frontend.md), [../technical/database/migrations.md](../technical/database/migrations.md)

### [2026-04-25] `integrate/pilot-merge`

- **Status:** Recorded
- **Raw change:** Completed deployment-script rollout and navigation cleanup across documentation trees.
- **Raw repository scope:** Added Linux deployment scripts and one-click startup flows, expanded platform-specific run guides (including WSL Redis/Celery notes), corrected local-vs-production email transport docs, and normalized navigation/back-link behavior across major doc sets.
- **Source commits:** `adf59e1` - "feat: add Linux deployment script"; `2f09ec9` - "docs: add Linux deployment guide"; `8e61348` - "docs(linux-deploy): clarify local vs production distinction"; `f377fa5` - "docs(linux-deploy): fix local EMAIL_TRANSPORT options"; `7e211d3` - "feat(deploy): add production docker-compose and AWS deploy guide"; `df4dba5` - "feat(deploy): add start.sh production stack manager"; `4bdfefa` - "feat(deploy): zero-config docker compose + one-click start.sh for Ubuntu/AWS"; `2e48afc` - "docs: add how-to-run guide covering all platforms and update README index"; `07d465b` - "docs: complete local-dev and common-commands with full manual setup steps"; `ca1c30b` - "docs: add Windows-specific notes for Redis (WSL) and Celery --pool=solo"; `a96dcec` - "docs: fix back links to point to parent page instead of always root README"; `700ac13` - "docs(seeder): add back link to root README and fix stale math note"; `83454c9` - "docs: add Prev/Next/Home nav buttons to all 44 doc files"; `bcefe72` - "docs: remove all redundant back links across all doc files"
- **Reference targets:** [backend.md](./backend.md), [frontend.md](./frontend.md), [../technical/deployment/deployment-guide.md](../technical/deployment/deployment-guide.md)

### [2026-04-25] `integrate/pilot-merge`

- **Status:** Recorded
- **Raw change:** Hardened compose runtime behavior for face attendance, migration safety, and persistent host data.
- **Raw repository scope:** Fixed session-expiry timezone comparison and event-status enum normalization, hardened face-attendance/verification error handling, added migration and backend health guards, updated port/env mappings, and moved postgres/pgadmin/branding/insightface storage toward explicit host bind mounts with seed opt-in profile behavior.
- **Source commits:** `f73133c` - "Fix session expiry timezone comparison"; `25f401d` - "fix(migrations): add table existence guards to prevent errors on fresh DB"; `f8aa30e` - "fix(docker): add healthcheck to backend service"; `34b1dd1` - "fix(docker): use python healthcheck instead of curl"; `f155a4c` - "fix(models): use enum values (lowercase) for EventStatus column"; `a29a0ac` - "fix(face): normalize attendance and verification face errors"; `7823fa6` - "Add"; `2ec8809` - "fix(docker): restore backend port 8001 to avoid conflict with caps_backend"; `7be104a` - "fix(docker): mount pgadmin data to /home/ubuntu/Aura/docker-data/pgadmin"; `ef05af9` - "fix(docker): make seed opt-in via profile, backend depends on bootstrap"; `e347c9f` - "fix(docker): move postgres data to bind mount at /home/ubuntu/Aura/docker-data/postgres"; `2e1f78b` - "fix(docker): move branding storage to bind mount at /home/ubuntu/Aura/docker-data/branding"; `ccaf3a4` - "fix(docker): move insightface models to bind mount at /home/ubuntu/Aura/docker-data/insightface"; `5576224` - "Update port mappings and environment variables"
- **Reference targets:** [backend.md](./backend.md), [frontend.md](./frontend.md), [../technical/deployment/deployment-guide.md](../technical/deployment/deployment-guide.md)

### [2026-04-25] `integrate/pilot-merge`

- **Status:** Recorded
- **Raw change:** Added single-command startup orchestration and refreshed env/documentation alignment.
- **Raw repository scope:** Added compose-level migrate/bootstrap service sequencing so stack startup requires fewer manual steps, restored and refined root `.env.example`, and synchronized startup/env docs with the merged runtime behavior.
- **Source commits:** `b6b3dbe` - "feat(docker): add migrate/bootstrap services for single-command startup"; `2dd8567` - "fix: restore missing .env.example"; `07b5c27` - "docs: update docker and env docs for single-command startup and production deployment"; `1541582` - "docs: fix stale multi-step docker instructions in README and common-commands"
- **Reference targets:** [backend.md](./backend.md), [frontend.md](./frontend.md)

### [2026-04-25] `integrate/pilot-merge`

- **Status:** Recorded
- **Raw change:** Reworked seeder configuration flow and seeded-startup toggles.
- **Raw repository scope:** Ported and aligned the demo seeder with current schema, replaced `.env`-driven seeder config with `variables.py`/module config flow, added compose-seeding toggle plumbing, and then refined toggle ownership so seeder control stays centralized.
- **Source commits:** `3871036` - "feat(seeder): port demo seeder from aurav3 worktree"; `d74fa29` - "refactor(seeder): replace .env config with variables.py"; `f90ee2f` - "feat(seeder): add config.py to validate variables.py on startup"; `5483f08` - "feat(seeder): add SEED_DATABASE docker toggle - runs seeder on compose up when true"; `49ec7a5` - "refactor(seeder): revert env override - SEED_DATABASE toggle lives in seeder/variables.py only"; `039961a` - "fix(seeder): store suffix in User.suffix column instead of appending to first_name"; `798313e` - "fix(seeder): add collision-resistant email generation with retry loop"
- **Reference targets:** [backend.md](./backend.md), [../technical/testing/test-plan.md](../technical/testing/test-plan.md)

### [2026-04-24] `integrate/pilot-merge`

- **Status:** Recorded
- **Raw change:** Merged updated backend/frontend runtime behavior with mail transport toggle alignment.
- **Raw repository scope:** Synced backend and compose mail transport handling (Mailpit/Mailjet-related behavior), refreshed env docs, and aligned merged project state after cross-branch integration.
- **Source commit:** `24e41f7` - "feat: merged new frontend and backend with added mailpit-mailjet toggle"
- **Reference targets:** [backend.md](./backend.md), [frontend.md](./frontend.md)

### [2026-04-17] `aurav3`

- **Status:** Recorded
- **Raw change:** Removed the tracked root environment example.
- **Raw repository scope:** Deleted the root `.env.example` from the branch. Runtime setup documentation, `Backend/.env`, compose files, and frontend runtime config handling now serve as the active configuration reference instead of a tracked root example file.
- **Source commit:** `f4692a5` - "Deleted Files: .env.example"
- **Reference targets:** [backend.md](./backend.md), [frontend.md](./frontend.md), [../technical/deployment/environment-variables.md](../technical/deployment/environment-variables.md)

### [2026-04-17] `aurav3`

- **Status:** Recorded
- **Raw change:** Synced the current project state and added audit/code-quality assets.
- **Raw repository scope:** Added `AUDIT_REPORT.md` and `qodana.yaml`, tightened sanctions access behavior in the backend, refreshed SG sanctions and event-management flows in the frontend, and documented the current repository state for audit purposes.
- **Source commit:** `3c214e1` - "chore: sync current Aura project state"
- **Reference targets:** [backend.md](./backend.md), [frontend.md](./frontend.md), [../reviews/repository-audit-report-summary.md](../reviews/repository-audit-report-summary.md)

### Frontend Branch History (`aura_frontendv3` and merged `aurav3` frontend work)

### [2026-04-27] `integrate/pilot-merge`

- **Status:** Recorded
- **Raw change:** Restored frontend AI surfaces after branch-sync regressions and aligned assistant rename assets.
- **Raw frontend scope:** Restored deleted AI UI components and assistant integration files, then synced asset/config references after `assistant-v2` to `assistant` rename while preserving Android splash/icon resources and runtime branding assets.
- **Source commits:** `b692243` - "fix(frontend): restore critical AI components accidentally deleted in branch sync"; `cffa80b` - "fix: update docker and ci configs to use renamed assistant directory"
- **Reference targets:** [frontend.md](./frontend.md), [backend.md](./backend.md)

### [2026-04-26] `integrate/pilot-merge`

- **Status:** Recorded
- **Raw change:** Synced frontend baseline to latest main/pre-production state.
- **Raw frontend scope:** Replaced frontend tree with main snapshot and then refreshed with newest pre-production content to keep release integration aligned.
- **Source commits:** `1b08d36` - "Replace frontend with main version"; `a0e7e09` - "newest frontend + pre production"
- **Reference targets:** [frontend.md](./frontend.md)

### [2026-04-25] `integrate/pilot-merge`

- **Status:** Recorded
- **Raw change:** Normalized face-verification and attendance UI error handling.
- **Raw frontend scope:** Updated face-scan and privileged verification views to match backend-normalized face error contracts and reduce inconsistent attendance/verification failure states shown to users.
- **Source commit:** `a29a0ac` - "fix(face): normalize attendance and verification face errors"
- **Reference targets:** [frontend.md](./frontend.md), [backend.md](./backend.md)

### [2026-04-25] `integrate/pilot-merge`

- **Status:** Recorded
- **Raw change:** Replaced frontend baseline and synchronized Android workspace.
- **Raw frontend scope:** Normalized directory casing to `frontend/`, replaced frontend contents with `aura_mobileapk_v1.3` branch state, and synced Capacitor Android workspace/build assets and mobile-facing dashboard/event flows.
- **Source commits:** `640c25e` - "Rename Frontend directory to lowercase"; `2d0db6f` - "Replace Frontend with aura_mobileapk_v1.3 branch contents"
- **Reference targets:** [frontend.md](./frontend.md)

### [2026-04-25] `integrate/pilot-merge`

- **Status:** Recorded
- **Raw change:** Merged assistant chat streaming and rich chat UI surfaces.
- **Raw frontend scope:** Replaced stub chat with real SSE streaming, added richer markdown/chart/conversation UI paths for assistant interactions, and applied follow-up UI correctness fixes in chat rendering and sidebar structure.
- **Source commits:** `cc0c0e0` - "feat(frontend): wire assistant - replace stub useChat with real SSE streaming"; `04c27be` - "feat(frontend): full assistant UI merge from aurav3 - markdown, charts, conversation list, copy button"; `9d4214f` - "fix(frontend): replace nested button with div in chat sidebar item"
- **Reference targets:** [frontend.md](./frontend.md), [backend.md](./backend.md)

### [2026-04-25] `integrate/pilot-merge`

- **Status:** Recorded
- **Raw change:** Expanded location search and governance/council frontend stability updates.
- **Raw frontend scope:** Added searchable location handling in event creation/editor flows, refreshed SG/governance workspace behavior, optimized dashboard loading paths, and fixed campus-admin schedule white-page rendering.
- **Source commits:** `5681063` - "Frontend: Add a features for searchable location"; `464c40c` - "Enhance the location searching"; `10648ad` - "Fix the white page in the campus_admin side"; `6a80bc8` - "Optimize the sudden loading in the SSG dashboard"; `1c01cf0` - "manage sg members"; `1a4fbea` - "council"
- **Reference targets:** [frontend.md](./frontend.md)

### [2026-04-25] `integrate/pilot-merge`

- **Status:** Recorded
- **Raw change:** Frontend local-env tracking cleanup and docs matrix sync.
- **Raw frontend scope:** Untracked machine-local frontend env overrides and aligned frontend env/config docs and examples with the merged compose/runtime assistant origin wiring.
- **Source commits:** `99e7504` - "Clarify env requirements and untrack frontend local env files"; `1a64068` - "Stop tracking local frontend env override"; `c27e605` - "docs(frontend): add missing ASSISTANT_ORIGIN and AURA_ASSISTANT_BASE_URL to repo-root Docker Compose optional vars"
- **Reference targets:** [frontend.md](./frontend.md), [../technical/deployment/environment-variables.md](../technical/deployment/environment-variables.md)

### [2026-04-17] `aurav3`

- **Status:** Recorded
- **Raw change:** Restored face MFA and synchronized user preferences.
- **Raw frontend scope:** Added remembered-login behavior, restored privileged face-verification routing during sign-in, synced dark mode and font-size preferences with backend account storage, and updated the profile/settings flow so user configuration can be saved and loaded across devices.
- **Source commit:** `cf4ae60` - "feat: restore face MFA and sync user preferences"
- **Reference targets:** [frontend.md](./frontend.md), [backend.md](./backend.md)

### [2026-04-17] `aurav3`

- **Status:** Recorded
- **Raw change:** Synced the current Aura frontend workspace state.
- **Raw frontend scope:** Expanded the governance event workspace with sanctions flows, refreshed SG event-management and sanctions drill-down routes, added shared dashboard chart helpers, and aligned governance/admin/workspace copy and behavior with the current Aura branch state.
- **Source commit:** `3c214e1` - "chore: sync current Aura project state"
- **Reference targets:** [frontend.md](./frontend.md)

### [2026-04-16] `aurav3`

- **Status:** Recorded
- **Raw change:** Applied the Aura update across current frontend workspaces.
- **Raw frontend scope:** Refreshed the admin workspace, updated preview/admin dashboard data, aligned assistant chat usage with stored conversation scope, and updated frontend routing and copy to match the current Aura-branded backend state.
- **Source commit:** `1da24c2` - "aura update"
- **Reference targets:** [frontend.md](./frontend.md)

### [2026-04-13] `aurav3`

- **Status:** Recorded
- **Raw change:** Added system audit and latest workspace updates.
- **Raw frontend scope:** Expanded the home, profile, admin, school IT, and SG dashboard surfaces; refreshed notification handling; added dashboard chart helpers; and aligned the frontend with newer backend notification, attendance, and workspace behaviors.
- **Source commit:** `c9af977` - "feat: system audit and latest workspace updates"
- **Reference targets:** [frontend.md](./frontend.md)

### [2026-04-17] `aura_frontendv3`

- **Status:** Recorded
- **Raw change:** Deleted tracked frontend environment files from the branch.
- **Raw frontend scope:** Removed `.env.local`, `.env.docker`, `.env.docker.example`, and `.env.development.local` from version control so local or deployment-specific frontend configuration is no longer treated as tracked documentation or tracked runtime defaults.
- **Source commit:** `46f95ac` - "Deleted: .env.local, .env.docker, .env.docker.example, .env.development.local"
- **Reference targets:** [frontend.md](./frontend.md), [../technical/deployment/environment-variables.md](../technical/deployment/environment-variables.md)

### [2026-04-05] `aura_frontendv3`

- **Status:** Recorded
- **Raw change:** Flutter/mobile-oriented user analytics work landed.
- **Raw frontend scope:** Added mobile dashboard views, attendance filters, and expanded user-side analytics support. Updated the app shell and frontend normalization behavior to support the hybrid/mobile rendering path.
- **Source commit:** `548389a` - "Flutter and analytics user side"
- **Reference targets:** [frontend.md](./frontend.md)

### [2026-04-03] `aura_frontendv3`

- **Status:** Recorded
- **Raw change:** Routing fixes landed after the mobile/desktop view split.
- **Raw frontend scope:** Corrected route definitions so the new mobile view layer and the desktop dashboard structure resolve consistently after the view-separation refactor.
- **Source commit:** `3348531` - "Rerouting"
- **Reference targets:** [frontend.md](./frontend.md)

### [2026-04-03] `aura_frontendv3`

- **Status:** Recorded
- **Raw change:** Frontend views were separated by platform.
- **Raw frontend scope:** Added the dedicated mobile view layer, Capacitor configuration, frontend Android build documentation, and layout-agnostic dashboard views that can be reused across desktop and mobile contexts.
- **Source commit:** `006203a` - "Separation of the view"
- **Reference targets:** [frontend.md](./frontend.md)

### [2026-04-02] `aura_frontendv3`

- **Status:** Recorded
- **Raw change:** Desktop and mobile frontend architecture was introduced.
- **Raw frontend scope:** Added the dashboard shell, broadened platform-aware routing, and expanded School IT reporting and schedule views to fit the new architecture.
- **Source commit:** `a553a9a` - "feat: add desktop and mobile frontend architecture"
- **Reference targets:** [frontend.md](./frontend.md)

### [2026-03-27] `aura_frontendv3`

- **Status:** Recorded
- **Raw change:** Deployment-ready frontend runtime configuration landed.
- **Raw frontend scope:** Added runtime environment injection, updated Docker and Nginx templates, and shifted the frontend toward environment-backed startup configuration rather than baked-in build-time values.
- **Source commit:** `958d587` - "Prepare deployment branch with env-backed frontend"
- **Reference targets:** [frontend.md](./frontend.md)

### [2026-03-25] `aura_frontendv3`

- **Status:** Recorded
- **Raw change:** The frontend was pushed toward MVP readiness.
- **Raw frontend scope:** Added SG and governance-facing dashboard flows, extended admin and School IT views, expanded PWA/mobile support, and added related composables, preview data, and UI support files.
- **Source commit:** `5f8b4fe` - "Semi ready for mvp"
- **Reference targets:** [frontend.md](./frontend.md)

### [2026-03-20] `aura_frontendv3`

- **Status:** Recorded
- **Raw change:** Dockerized demo frontend setup landed with School IT expansion work.
- **Raw frontend scope:** Added Docker-based frontend serving and expanded School IT dashboard, import, department/program, settings, and session-management support.
- **Source commit:** `2aba9a6` - "dockerize demo frontend setup"
- **Reference targets:** [frontend.md](./frontend.md)

### [2026-03-15] `aura_frontendv3`

- **Status:** Recorded
- **Raw change:** Android optimization and School IT workspace buildout landed.
- **Raw frontend scope:** Added School IT home, users, and student-council management flows, privileged face verification, document branding utilities, and Android/PWA-focused frontend refinements.
- **Source commits:** `c3673b2` - "optimize android"; `1f75db0` - "add school it dashboard(unfinished)"
- **Reference targets:** [frontend.md](./frontend.md)

### [2026-03-14] `aura_frontendv3`

- **Status:** Recorded
- **Raw change:** Student dashboard readiness and UI refinement work landed.
- **Raw frontend scope:** Added or expanded the mobile dashboard, profile/security flows, backend integration helper services, session/auth support, and frontend API tooling while polishing the core student dashboard views.
- **Source commits:** `31fc893` - "User(student) Done"; `4a88a86` - "Refinement-User Dashboard Ready"
- **Reference targets:** [frontend.md](./frontend.md)

### [2026-03-13] `aura_frontendv3`

- **Status:** Recorded
- **Raw change:** Live dashboard API integration and admin setup tooling landed.
- **Raw frontend scope:** Connected the frontend to the live backend API, added session-driven dashboard loading, introduced face registration workflow support, and added the frontend API lab route/tooling.
- **Source commit:** `c4670fe` - "Integrate live dashboard API and admin setup lab"
- **Reference targets:** [frontend.md](./frontend.md)

### [2026-03-10] `aura_frontendv3`

- **Status:** Recorded
- **Raw change:** Clean UI rewrite baseline landed for the frontend branch.
- **Raw frontend scope:** Established the Vue/Vite/Tailwind frontend baseline, dynamic school branding, student dashboard shell, auth composable, navigation system, and mock-data-backed UI workflow.
- **Source commit:** `ebd4be2` - "Clean Ui Ver"
- **Reference targets:** [frontend.md](./frontend.md)

### Backend and Cross-branch History

### [2026-04-27] `integrate/pilot-merge`

- **Status:** Recorded
- **Raw change:** Completed normalized-schema cutover stabilization and backend startup recovery.
- **Raw backend scope:** Aligned sanctions service and multiple model modules to normalized schema assumptions, moved canonical schema SQL under `backend/app/db`, iteratively hardened Alembic migration pathing and idempotency behavior, merged conflicting migration heads, and fixed post-migration startup/auth/router mismatches.
- **Source commits:** `20ea2a8` - "fix: align sanctions service with normalized schema and fix alembic env"; `7a8f47a` - "fix: make normalized schema migration non-destructive"; `28f3903` - "fix(migrations): merge conflicting heads to restore deployment"; `038cbbf` - "fix(deploy): fix missing db_normalized folder in Docker production build"; `273154d` - "chore: move master schema to backend/app/db and revert docker build hacks"; `5919f1c` - "debug(migrations): add verbose logging to pinpoint normalization failure"; `11d07e0` - "debug(migrations): final clean rewrite with explicit path logging and flushing"; `ad7aa0e` - "debug(migrations): bulletproof path resolution and package initialization"; `28ce3b1` - "fix(migrations): initialize sys.path before app imports in env.py"; `f3b0689` - "fix(migrations): update parent migration path logic to use official schema location"; `4c8805b` - "fix(migrations): add idempotency check to avoid duplicate object errors"; `2a25772` - "chore: align backend models to normalized schema"; `0adef00` - "fix: resolve schema alignment issues blocking backend startup and auth flow"
- **Reference targets:** [backend.md](./backend.md), [../technical/database/migrations.md](../technical/database/migrations.md), [../technical/backend/overview.md](../technical/backend/overview.md)

### [2026-04-27] `integrate/pilot-merge`

- **Status:** Recorded
- **Raw change:** Synchronized backend/deploy references for assistant directory rename.
- **Raw backend scope:** Updated compose and CI references to the renamed `assistant/` service path and integrated pilot fixes into pre-production deployment flow with stricter branch-based release controls.
- **Source commits:** `7028cdc` - "chore: rename assistant-v2 to assistant and cleanup legacy schema files"; `cffa80b` - "fix: update docker and ci configs to use renamed assistant directory"; `a7ab0a9` - "ci: restrict auto-deploy to production branches"; `9323700` - "ci: fix missing env file in deploy-ec2 validation and gitignore casing"; `27cab35` - "merge: integrate pilot fixes into pre-production"
- **Reference targets:** [backend.md](./backend.md), [../technical/deployment/ci-cd-pipeline.md](../technical/deployment/ci-cd-pipeline.md)

### [2026-04-26] `integrate/pilot-merge`

- **Status:** Recorded
- **Raw change:** Added pgvector-backed face embeddings and backend validation resilience fixes.
- **Raw backend scope:** Added migration and runtime support for `student_face_embeddings` with pgvector indexing/backfill support, switched production DB image to pgvector-capable Postgres, and patched school settings validation handling to avoid crash paths from manual Pydantic instantiation.
- **Source commits:** `acd882f` - "Add pgvector-backed face attendance matching"; `c4ae534` - "fix: use pgvector/pgvector:pg15 image for vector extension support"; `3ef9a09` - "fix(school): catch ValidationError from manual Pydantic form instantiation"
- **Reference targets:** [backend.md](./backend.md), [../technical/database/migrations.md](../technical/database/migrations.md), [../technical/deployment/deployment-guide.md](../technical/deployment/deployment-guide.md)

### [2026-04-25] `integrate/pilot-merge`

- **Status:** Recorded
- **Raw change:** Hardened backend runtime behavior for face error normalization, migration safety, and deployment health.
- **Raw backend scope:** Normalized face attendance/verification error contracts end-to-end, fixed timezone-related session expiry comparisons, normalized event-status enum persistence casing, added migration table-existence guards plus backend health checks, and expanded compose runtime wiring for persistent host-volume mounts.
- **Source commits:** `f73133c` - "Fix session expiry timezone comparison"; `25f401d` - "fix(migrations): add table existence guards to prevent errors on fresh DB"; `f8aa30e` - "fix(docker): add healthcheck to backend service"; `34b1dd1` - "fix(docker): use python healthcheck instead of curl"; `f155a4c` - "fix(models): use enum values (lowercase) for EventStatus column"; `a29a0ac` - "fix(face): normalize attendance and verification face errors"; `7823fa6` - "Add"; `2ec8809` - "fix(docker): restore backend port 8001 to avoid conflict with caps_backend"; `7be104a` - "fix(docker): mount pgadmin data to /home/ubuntu/Aura/docker-data/pgadmin"; `ef05af9` - "fix(docker): make seed opt-in via profile, backend depends on bootstrap"; `e347c9f` - "fix(docker): move postgres data to bind mount at /home/ubuntu/Aura/docker-data/postgres"; `2e1f78b` - "fix(docker): move branding storage to bind mount at /home/ubuntu/Aura/docker-data/branding"; `ccaf3a4` - "fix(docker): move insightface models to bind mount at /home/ubuntu/Aura/docker-data/insightface"; `5576224` - "Update port mappings and environment variables"
- **Reference targets:** [backend.md](./backend.md), [../technical/deployment/deployment-guide.md](../technical/deployment/deployment-guide.md)

### [2026-04-25] `integrate/pilot-merge`

- **Status:** Recorded
- **Raw change:** Applied backend timezone-idempotency reliability pass.
- **Raw backend scope:** Added migration-backed timezone-aware storage for attendance/common system timestamps, introduced event-create idempotency fields/behavior, and synced backend route/service/model test coverage around those changes.
- **Source commit:** `570f250` - "Fix the map"
- **Reference targets:** [backend.md](./backend.md), [frontend.md](./frontend.md)

### [2026-04-25] `integrate/pilot-merge`

- **Status:** Recorded
- **Raw change:** Tightened SG/ORG event scope and face-recognition account locking behavior.
- **Raw backend scope:** Enforced stricter student department/program visibility on governance event queries, tightened face-recognition locking paths, and updated governance/face route tests plus policy docs.
- **Source commit:** `eab6f3b` - "fix(events): enforce strict student dept/program scope for SG/ORG event visibility, face rec account locking"
- **Reference targets:** [backend.md](./backend.md), [frontend.md](./frontend.md)

### [2026-04-25] `integrate/pilot-merge`

- **Status:** Recorded
- **Raw change:** Expanded backend user/profile schema and governance security-center controls.
- **Raw backend scope:** Added user `prefix`/`suffix` columns and faculty profile schema support via migrations; also synced governance member management and security-center/session-linked attendance behavior updates with corresponding schema/test adjustments.
- **Source commits:** `c306c69` - "feat(schema): add prefix and suffix columns to users table"; `d2a67b5` - "feat(schema): add FacultyProfile model and migration"; `6d72849` - "manage council members"; `2657db0` - "added face rec toggle and manage sg members"
- **Reference targets:** [backend.md](./backend.md), [frontend.md](./frontend.md)

### [2026-04-25] `integrate/pilot-merge`

- **Status:** Recorded
- **Raw change:** Improved backend startup resilience and bootstrap defaults.
- **Raw backend scope:** Made bootstrap admin credentials optional by defaulting to app settings and degraded email transport initialization failures to warnings so backend startup can continue in degraded mode.
- **Source commits:** `410f225` - "feat(bootstrap): make --admin-email and --admin-password optional with app_settings defaults"; `ca85538` - "fix(backend): degrade email startup failure to warning instead of crash"
- **Reference targets:** [backend.md](./backend.md)

### [2026-04-17] `aurav3`

- **Status:** Recorded
- **Raw change:** Restored privileged face MFA and synced account-level user preferences.
- **Raw backend scope:** Added the `user_app_preferences` model, migration, routes, and service helpers; restored privileged face MFA handling for `admin` and `campus_admin`; and added `remember_me` session lifetime support.
- **Source commit:** `cf4ae60` - "feat: restore face MFA and sync user preferences"
- **Reference targets:** [backend.md](./backend.md), [frontend.md](./frontend.md)

### [2026-04-17] `aurav3`

- **Status:** Recorded
- **Raw change:** Synced the current project state.
- **Raw backend scope:** Hardened sanctions route access for governance roles and platform admins, refreshed sanctions tests, updated school-settings fallback behavior, and added Qodana and audit artifacts.
- **Source commit:** `3c214e1` - "chore: sync current Aura project state"
- **Reference targets:** [backend.md](./backend.md)

### [2026-04-16] `aurav3`

- **Status:** Recorded
- **Raw change:** Aura-wide backend and assistant update.
- **Raw backend scope:** Updated Aura-branded default email and notification copy, synced current mail/notification behavior, and refreshed supporting backend docs and transport utilities.
- **Raw assistant scope:** Expanded `Assistant/assistant.py` and `Assistant/system_prompt.txt` to match the current project state and tool surface.
- **Source commit:** `1da24c2` - "aura update"
- **Reference targets:** [backend.md](./backend.md)

### [2026-04-13] `aurav3`

- **Status:** Recorded
- **Raw change:** Added system audit and latest workspace updates.
- **Raw backend scope:** Added local Mailpit SMTP testing support, editable email format references, import-email improvements, email/config test coverage, face-engine warmup safeguards, and related backend documentation.
- **Source commit:** `c9af977` - "feat: system audit and latest workspace updates"
- **Reference targets:** [backend.md](./backend.md)

### [2026-04-03] `#change-face-recognition-into-insightface`

- **Status:** Active
- **Raw change:** Migrated face recognition to InsightFace and added backend environment examples.
- **Raw backend scope:** Replaced the legacy face recognition engine with InsightFace, removing `dlib`, `face-recognition`, and `face_recognition_models` dependencies for easier configuration. Added `.env.example` at that time.
- **Raw frontend scope:** No confirmed frontend-only implementation recorded in this branch entry.
- **Reference targets:** [backend.md](./backend.md)

### [2026-03-28] `Agentic Import Features`

- **Status:** Merged
- **Raw change:** Fixed bulk import and email sender.
- **Raw backend scope:** Updated bulk import onboarding emails to match credentials email and standardized outbound email on Gmail API.
- **Raw frontend scope:** No confirmed frontend-specific change documented from this branch.
- **Reference targets:** [backend.md](./backend.md)

### [2026-03-27] `aura_refractored_code`

- **Status:** Merged
- **Raw change:** Refactored attendance system behavior and added deployment fixes.
- **Raw backend scope:** Added `POST /attendance/mark-absent` and `POST /attendance/mark-excused`, patched Docker entrypoint behavior, improved production container setup, and added administrative tooling under `tools/`.
- **Raw frontend scope:** No confirmed frontend-specific change documented from this branch.
- **Reference targets:** [backend.md](./backend.md)

### [2026-03-22] `STUDENT-HIERARCHY`

- **Status:** Merged
- **Raw change:** Governance dashboards were optimized and face-recognition attendance and auth behavior were adjusted.
- **Raw backend scope:** Attendance flow documentation was aligned to face-recognition-only use, token and session validation were tightened, and role-scoped protections were enforced across attendance paths.
- **Raw frontend scope:** Governance dashboards now rely on server-side paging and the face-recognition attendance UI flow was updated.
- **Reference targets:** [backend.md](./backend.md), [frontend.md](./frontend.md)

### [2026-03-21] `STUDENT-HIERARCHY`

- **Status:** Merged
- **Raw change:** Attendance timing overrides and backend cleanup and documentation landed.
- **Raw backend scope:** Added `present_until_override_at` and `late_until_override_at` to `events`, documented backend modules, and removed unused face and geolocation helpers.
- **Raw frontend scope:** No confirmed frontend-only implementation recorded in this branch entry.
- **Reference targets:** [backend.md](./backend.md)

### [2026-03-18] `STUDENT-HIERARCHY`

- **Status:** Merged
- **Raw change:** Alembic environment loading was fixed for local and Docker runs.
- **Raw backend scope:** `alembic/env.py` now reads `Backend/.env` before resolving `DATABASE_URL`.
- **Raw frontend scope:** None.
- **Reference targets:** [backend.md](./backend.md)

### [2026-03-17] `STUDENT-HIERARCHY`

- **Status:** Merged
- **Raw change:** Authentication hardening, health checks, and DB connection improvements were added.
- **Raw backend scope:** Added `GET /health`, added pool tuning env vars, synced Campus Admin and school activation state, blocked inactive-school sessions, and optimized login queries.
- **Raw frontend scope:** No confirmed frontend-only implementation recorded in this branch entry.
- **Reference targets:** [backend.md](./backend.md)

### [2026-03-16] `STUDENT-HIERARCHY`

- **Status:** Merged
- **Raw change:** Governance hierarchy, scoped events, documentation restructure, and production deployment path were introduced.
- **Raw backend scope:** Added governance tables, role guard improvements, attendance window controls, `user_face_profiles`, production Docker path, and load test tooling.
- **Raw frontend scope:** Added governance dashboards, Campus Admin monitoring views, and the School IT workspace naming shift.
- **Reference targets:** [backend.md](./backend.md), [frontend.md](./frontend.md)

### [2026-03-14] `FACE-AUTOMATION-TEST`

- **Status:** Merged
- **Raw change:** Face attendance automation and event sync work landed.
- **Raw backend scope:** Added Celery Beat event sync, Mailpit support, and backend support for liveness and geolocation checks.
- **Raw frontend scope:** Added face scan and face attendance UI components and flows.
- **Reference targets:** [backend.md](./backend.md), [frontend.md](./frontend.md)

### [2026-03-13] `sas(ssg)v3`

- **Status:** Merged
- **Raw change:** SSG RBAC, SMTP integration, and SSG dashboard refresh were added.
- **Raw backend scope:** Added RBAC-related backend and database support and SMTP email service integration.
- **Raw frontend scope:** Refreshed SSG dashboard and added supporting dashboard components.
- **Reference targets:** [backend.md](./backend.md), [frontend.md](./frontend.md)

