# Changelog Fix Error Ledger (Tester)

> Source-only basis: `doc/changelog/branch-updates.md`  
> Scope: this log uses only commits in changelog entries that include `fix` in the commit message.  
> Note: changelog entries provide date only; exact commit time is not documented in the source file.

---

## Documented Bug/Error-to-Fix Register

> **Column Guide**
> - **Documented Bug/Error** — Technical description of the root cause (dev/commit level).
> - **Visible Error (User-Facing)** — What a user *actually sees* on screen when this error occurs (e.g., red error text, blank page, broken button). Use this column to quickly match a reported error to a known bug.

| Bug/Error # | Documented Bug/Error                                                               | Visible Error (User-Facing)                                                              | Status   | Fix Commit | Changelog Date | Time in Changelog |
|---|------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|---|---|---|---|
| 1  | Seeder suffix was appended to first name instead of saved in `User.suffix`.        | User profile shows suffix attached to first name (e.g., "JuanJr." instead of "Juan")    | Resolved | `039961a` | 2026-04-25 | Not specified |
| 2  | Campus admin view had a white-page rendering issue.                                | **Blank/white page** — campus admin dashboard loads but shows nothing                   | Resolved | `10648ad` | 2026-04-25 | Not specified |
| 3  | Migrations failed on fresh DB due to missing table-existence guards.               | **App fails to start** — server error on first launch with empty database                | Resolved | `25f401d` | 2026-04-25 | Not specified |
| 4  | Root `.env.example` was missing and needed restoration.                            | Setup/deploy fails silently; no `.env` template to copy from                            | Resolved | `2dd8567` | 2026-04-25 | Not specified |
| 5  | Branding storage mount path needed bind-mount relocation.                          | **Broken logo/branding images** — school logo does not load or shows broken icon         | Resolved | `2e1f78b` | 2026-04-25 | Not specified |
| 6  | Backend port conflict required restoring service port `8001`.                      | **Cannot connect** — frontend shows network error or API calls fail entirely             | Resolved | `2ec8809` | 2026-04-25 | Not specified |
| 7  | Docker healthcheck relied on curl and needed Python-based check.                   | **Container keeps restarting** — Docker shows service as unhealthy repeatedly            | Resolved | `34b1dd1` | 2026-04-25 | Not specified |
| 8  | Map behavior issue required a fix pass.                                            | **Map not responding** — map freezes, pans incorrectly, or markers misbehave            | Resolved | `570f250` | 2026-04-25 | Not specified |
| 9  | Seeder email generation needed collision-resistant retry behavior.                 | Seeding fails mid-run; duplicate email error shown in terminal                          | Resolved | `798313e` | 2026-04-25 | Not specified |
| 10 | PgAdmin storage path required bind-mount correction.                               | **PgAdmin data lost** on container restart; settings reset every reboot                 | Resolved | `7be104a` | 2026-04-25 | Not specified |
| 11 | Frontend chat sidebar had invalid nested button structure.                         | **Console warning / broken chat button** — button inside button, may not click properly | Resolved | `9d4214f` | 2026-04-25 | Not specified |
| 12 | Face attendance/verification errors were inconsistent and needed normalization.    | **Red error text in face scan** — inconsistent or confusing error messages during face verification | Resolved | `a29a0ac` | 2026-04-25 | Not specified |
| 13 | Backend startup crashed on email-init failure; needed warning-only degrade mode.   | **App won't start** — server crashes at boot if email service is misconfigured          | Resolved | `ca85538` | 2026-04-25 | Not specified |
| 14 | InsightFace model storage path required bind-mount relocation.                     | **Face scan not working** — face recognition fails; model not found error in logs       | Resolved | `ccaf3a4` | 2026-04-25 | Not specified |
| 15 | Postgres data path required bind-mount relocation.                                 | **Database data lost** on container restart; all records gone after reboot              | Resolved | `e347c9f` | 2026-04-25 | Not specified |
| 16 | SG/ORG event visibility and face-rec account locking scope needed enforcement.     | Users see events they shouldn't, or face-rec locks wrong accounts                      | Resolved | `eab6f3b` | 2026-04-25 | Not specified |
| 17 | Seeding behavior needed opt-in profile and bootstrap dependency wiring.            | Seed runs but required demo profiles or admin accounts are missing                     | Resolved | `ef05af9` | 2026-04-25 | Not specified |
| 18 | `EventStatus` enum persistence used wrong casing and needed lowercase values.      | Event status shows wrong value or breaks filtering (e.g., "ACTIVE" vs "active")        | Resolved | `f155a4c` | 2026-04-25 | Not specified |
| 19 | Session expiry check had timezone comparison mismatch.                             | **Unexpected logout** — user gets logged out even with a valid, non-expired session     | Resolved | `f73133c` | 2026-04-25 | Not specified |
| 20 | Backend Docker service lacked healthcheck coverage.                                | **Service silently down** — backend fails but Docker shows it as running               | Resolved | `f8aa30e` | 2026-04-25 | Not specified |
| 21 | School settings flow crashed on manual Pydantic validation error.                  | **School settings page crashes** — error shown when submitting invalid settings form   | Resolved | `3ef9a09` | 2026-04-26 | Not specified |
| 22 | CI compose/env path, frontend casing, and node warnings needed correction.         | CI pipeline fails; frontend build shows casing or Node version warnings in logs        | Resolved | `6194936` | 2026-04-26 | Not specified |
| 23 | CI ssh-action used invalid `script_stop` input.                                    | CI deploy step fails with unrecognized input error in GitHub Actions log               | Resolved | `8f11fe2` | 2026-04-26 | Not specified |
| 24 | CI referenced non-existent frontend lint/test scripts.                             | CI job fails with "script not found" error; lint/test step exits immediately           | Resolved | `bf7a8e7` | 2026-04-26 | Not specified |
| 25 | Database image lacked pgvector support for vector extension.                       | **Backend error on startup** — "extension pgvector not found" error in logs            | Resolved | `c4ae534` | 2026-04-26 | Not specified |
| 26 | Bootstrap command missed required admin credential args.                           | Bootstrap fails; no super-admin account created; login with default creds fails        | Resolved | `d868e98` | 2026-04-26 | Not specified |
| 27 | Deploy flow needed bind-mount directory creation and ownership setup.              | Deploy fails with "permission denied" or "no such directory" error                     | Resolved | `f10055f` | 2026-04-26 | Not specified |
| 28 | Compose startup could fail without `SECRET_KEY`; fallback default required.        | **App fails to start** — cryptic startup error if `SECRET_KEY` is not set in `.env`   | Resolved | `f723626` | 2026-04-26 | Not specified |
| 29 | Docker production build missed `db_normalized` folder.                             | **Backend crashes in production** — missing module/folder error on container start     | Resolved | `038cbbf` | 2026-04-27 | Not specified |
| 30 | Normalized-schema misalignment blocked backend startup and auth flow.              | **Cannot log in** — auth endpoints return 500 error; login button does nothing         | Resolved | `0adef00` | 2026-04-27 | Not specified |
| 31 | Sanctions service/alembic env drifted from normalized schema contract.             | **Backend error** — sanctions-related API calls fail with database column errors       | Resolved | `20ea2a8` | 2026-04-27 | Not specified |
| 32 | Alembic env path setup required `sys.path` initialization before app imports.      | Migrations fail to run; "module not found" error when running `alembic upgrade`        | Resolved | `28ce3b1` | 2026-04-27 | Not specified |
| 33 | Conflicting Alembic migration heads blocked deployment upgrade flow.               | Deploy stalls; "Multiple heads" error shown when running database migrations            | Resolved | `28f3903` | 2026-04-27 | Not specified |
| 34 | Migrations needed idempotency checks to avoid duplicate object errors.             | Migration crashes mid-run with "relation already exists" or "duplicate object" error   | Resolved | `4c8805b` | 2026-04-27 | Not specified |
| 35 | Normalized-schema migration needed non-destructive behavior.                       | Migration wipes or alters existing data unexpectedly during upgrade                    | Resolved | `7a8f47a` | 2026-04-27 | Not specified |
| 36 | Deploy flow required explicit migration-first execution for clearer logging.       | Deploy logs unclear; migrations and app start interleaved causing confusing output     | Resolved | `855b411` | 2026-04-27 | Not specified |
| 37 | Seeder demo generator was accidentally removed and had to be restored.             | Seeding runs but no demo users/events created; empty dashboard after seeding           | Resolved | `93f7d02` | 2026-04-27 | Not specified |
| 38 | Critical frontend AI components were accidentally deleted in branch sync.          | **AI/Assistant features missing** — chat or AI panel not visible in the UI             | Resolved | `b692243` | 2026-04-27 | Not specified |
| 39 | Docker/CI configs still pointed to old `assistant-v2` directory.                   | CI build fails or assistant container not found during deploy                          | Resolved | `cffa80b` | 2026-04-27 | Not specified |
| 40 | Parent migration path logic used wrong schema location and needed correction.      | Migration fails with "path not found" or wrong schema applied to wrong service         | Resolved | `f3b0689` | 2026-04-27 | Not specified |
| 41 | CI missing env file validation and gitignore casing issues.                        | CI silently skips env file checks; casing errors cause file-not-found on Linux         | Resolved | `9323700` | 2026-04-27 | Not specified |
| 42 | Seeder had unresolvable static import warning in seed.py.                          | Warning printed in terminal during seeding; may confuse testers as a real error        | Resolved | `201ae84` | 2026-04-28 | Not specified |
| 43 | Seeder date validation allowed start date later than end date.                     | Events created with invalid date range (end before start); broken event calendar       | Resolved | `aaaa01c` | 2026-04-28 | Not specified |
| 44 | Seeder alignment with pilot schema and new implementations needed fixes.           | Seeding crashes or produces wrong data; missing fields in seeded records               | Resolved | `04cacf8` | 2026-04-28 | Not specified |
| 45 | Forgot password function not properly exported in backendApi.js.                   | **"Forgot Password" does nothing** — button click has no effect; no email sent         | Resolved | `8bb49ea` | 2026-04-28 | Not specified |
| 46 | ForgotPasswordView used non-existent api.js instead of backendApi.js.              | **Forgot password page crashes** — console shows "api is not defined" red error        | Resolved | `59e02ea` | 2026-04-28 | Not specified |
| 47 | Stale attendanceFlow imports in useGovernanceWorkspace needed removal.             | Console shows import error; attendance or governance features may not load             | Resolved | `e5a8e27` | 2026-04-28 | Not specified |
| 48 | Runtime-config.js script tag lacked defer attribute causing Vite warning.          | **Yellow/orange Vite warning** shown in browser console on app load                   | Resolved | `b9b8cfd` | 2026-04-28 | Not specified |
| 49 | Stale column names in admin_server list_schools query.                             | **Schools list page broken** — shows database error or empty table unexpectedly        | Resolved | `c1c6196` | 2026-04-28 | Not specified |
| 50 | BaseUrl deprecation warning in jsconfig.json needed silencing.                     | Deprecation warning shown in IDE/terminal; not user-visible but noisy in logs          | Resolved | `28dc7e5` | 2026-04-28 | Not specified |
| 51 | Integration test fixture context teardown crash in parallel workers.               | CI test run crashes at teardown; flaky failure shown in GitHub Actions test report     | Resolved | `4f5562b` | 2026-04-28 | Not specified |
| 52 | Vite HMR connection timeout on networkidle wait in CI.                             | CI E2E tests timeout waiting for page; "network idle" never reached error in logs      | Resolved | `bb3f738` | 2026-04-28 | Not specified |
| 53 | Vite cold start timeout in CI with custom test.extend context fixture.             | E2E test fails immediately with timeout; Vite dev server not ready in time             | Resolved | `4b1838c` | 2026-04-28 | Not specified |
| 54 | LocalStorage not cleared before login tests causing session bleed.                 | **Auto-logged in as wrong user** — tests/users see previous session data               | Resolved | `2a741a8` | 2026-04-28 | Not specified |
| 55 | E2E tests missing backend test data (campus_admin@test.com).                       | E2E login test fails; "invalid credentials" error for campus admin test account        | Resolved | `9a7e928` | 2026-04-28 | Not specified |
| 56 | E2E tests #email selector not found due to localStorage state.                     | E2E test fails; email input field not found because old session pre-fills the form     | Resolved | `007d691` | 2026-04-28 | Not specified |
| 57 | LocalStorage and sessionStorage not cleared before page load in E2E.               | **Stale session data** causes wrong page or wrong user shown after navigating          | Resolved | `a6c8a54` | 2026-04-28 | Not specified |
| 58 | LocalStorage:5173 not explicitly cleared in storageState config.                   | Session bleeds across E2E tests; logged-in state persists when it shouldn't            | Resolved | `110b59b` | 2026-04-28 | Not specified |
| 59 | GitHub Actions base path auto-detection served app at /RIZAL_v1/ not /.           | **App loads at wrong URL** in CI preview; all asset paths broken (404s)                | Resolved | `838c005` | 2026-04-28 | Not specified |
| 60 | Vite config base path auto-detection caused E2E tests to fail.                     | E2E tests point to wrong URL; page not found or blank page during test run             | Resolved | `9292715` | 2026-04-28 | Not specified |
| 61 | Mobile viewport not used in Playwright causing selector mismatches.                | E2E tests fail on desktop selectors; mobile-only UI elements not found                 | Resolved | `7480a08` | 2026-04-28 | Not specified |
| 62 | Desktop-blocking screen in App.vue prevented rendering on all viewports.           | **"Use mobile device" message** shown on desktop — entire app blocked for desktop users | Resolved | `c22a53c` | 2026-04-28 | Not specified |
| 63 | Terms modal click in E2E login helper caused navigation failure.                   | E2E login test fails after terms modal; app navigates away unexpectedly                | Resolved | `a885c0e` | 2026-04-28 | Not specified |
| 64 | Chat trigger selector used wrong aria-label in E2E tests.                          | E2E test fails; chat button not found — "No element found for aria-label" error        | Resolved | `a200c89` | 2026-04-28 | Not specified |
| 65 | Two-step chat open flow not implemented in E2E tests.                              | E2E chat tests fail; test clicks once but chat requires two interactions to open       | Resolved | `2ac9e7f` | 2026-04-28 | Not specified |
| 66 | Assistant E2E tests didn't match actual chat state (under development).            | E2E assistant tests always fail; chat UI in a different state than tests expect        | Resolved | `9eaf51e` | 2026-04-28 | Not specified |
| 67 | Frontend-assistant E2E tests ran when chat not connected to assistant.             | E2E assistant tests run and fail even when assistant service is offline                | Resolved | `45232f1` | 2026-04-28 | Not specified |
| 68 | Test_integration.py included in assistant unit test run causing failures.          | Unit test run includes integration tests; failures appear in wrong test suite          | Resolved | `b123495` | 2026-04-28 | Not specified |
| 69 | VITE_APP_BASE_PATH not forced to / in E2E CI job.                                  | **App loads at wrong base path** in CI; routes broken, 404 on navigation               | Resolved | `6ff5e86` | 2026-04-28 | Not specified |
| 70 | Segfault on exit (139) not ignored in integration-tests CI job.                    | CI job fails with exit code 139 (segfault) even though all tests passed               | Resolved | `57c5ee2` | 2026-04-28 | Not specified |
| 71 | LocalStorage not cleared before every E2E test causing session bleed.              | **Wrong user logged in** between E2E tests; old session data persists                  | Resolved | `092bd36` | 2026-04-28 | Not specified |
| 72 | Fresh browser context not used per test causing localStorage bleed.                | E2E tests share browser state; one test's login bleeds into the next                   | Resolved | `fbaffc5` | 2026-04-28 | Not specified |
| 73 | JSDoc type annotations missing in E2E login helpers causing ts-check errors.       | Red squiggles / ts-check errors in E2E helper files; not runtime-visible               | Resolved | `d0f467c` | 2026-04-28 | Not specified |
| 74 | Mcp_servers and backend not in pyrightconfig extraPaths for Pylance.               | Pylance/IDE shows "module not found" red underlines in assistant Python files          | Resolved | `9633574` | 2026-04-28 | Not specified |
| 75 | TermsModal emitted close instead of agree/decline events.                          | **Terms modal does nothing on agree/decline** — clicking agree doesn't proceed         | Resolved | `354ee69` | 2026-04-28 | Not specified |
| 76 | Frontend index.html not set to no-cache causing stale chunk errors.                | **Stale chunk error** — app shows error after deploy; old cached JS chunks fail to load | Resolved | `999fc22` | 2026-04-28 | Not specified |
| 77 | Stale chunk error showed boundary UI instead of auto-reloading.                    | **Error boundary screen shown** instead of auto-refresh when chunk fails to load        | Resolved | `1b5b555` | 2026-04-28 | Not specified |
| 78 | Backend .env and .env.example out of sync with config.py.                          | Backend crashes or uses wrong config values; env variable mismatch errors in logs      | Resolved | `4fe6541` | 2026-04-28 | Not specified |
| 79 | Corrupt pwa icons needed replacement with correct production versions.             | **Broken PWA icon** — app icon shows as broken image when installed or in browser tab  | Resolved | `c5fd561` | 2026-04-28 | Not specified |
| 80 | Corrupt logo/pwa images needed replacement and binary gitattributes.               | **Broken logo image** on app / install screen; image renders as corrupted/placeholder  | Resolved | `74ded60` | 2026-04-28 | Not specified |
| 81 | Assistant .env missing so SECRET_KEY unavailable for JWT verification.             | **Assistant chat fails** — all assistant API calls return 401 Unauthorized             | Resolved | `d53f7f9` | 2026-04-28 | Not specified |
| 82 | Dotenv load in auth.py happened after SECRET_KEY read at module level.             | **Assistant returns 401** even with correct token — JWT verification fails at startup  | Resolved | `a70910f` | 2026-04-28 | Not specified |
| 83 | Thought tags not stripped from assistant model output.                             | **`<think>` tags visible in chat** — raw model reasoning text shown to user in chat    | Resolved | `9c037c0` | 2026-04-28 | Not specified |
| 84 | Assistant env missing DATABASE_URL so MCP tools couldn't query backend DB.         | **Assistant gives no data** — queries about records return empty or error responses    | Resolved | `b6d2843` | 2026-04-28 | Not specified |
| 85 | %BASE_URL% placeholders in index.html causing path resolution issues.              | **Assets fail to load** — images/scripts show 404; `%BASE_URL%` visible in page source | Resolved | `0b1637c` | 2026-04-28 | Not specified |
| 86 | Base path override in vite.config breaking logo paths.                             | **Logo broken in production** — logo image returns 404 after deployment                | Resolved | `6a98429` | 2026-04-28 | Not specified |
| 87 | Alembic env.py import pointed to wrong path (app.models.aura_norm).               | Migrations fail with "No module named app.models.aura_norm" error                     | Resolved | `1f35bd6` | 2026-04-28 | Not specified |
| 88 | Exit code 134 (SIGABRT) not handled as non-fatal CPython shutdown crash.           | CI integration-test job fails with exit 134 even when all tests pass                  | Resolved | `6a3fa07` | 2026-04-28 | Not specified |
| 89 | Test_google_auth.py used standalone SQLite causing privacy_consent_types FK error. | Test fails with "FOREIGN KEY constraint failed" error in Google auth test              | Resolved | `fd00aa4` | 2026-04-28 | Not specified |
| 90 | Thought tag streaming not properly handled across chunk boundaries.                | **Partial `<think>` tag visible** mid-stream in chat — model reasoning bleeds into response | Resolved | `089d320` | 2026-04-28 | Not specified |

---

## Source Reference

- [branch-updates.md](../../../changelog/branch-updates.md)
