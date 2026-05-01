# Changelog Fix Error Ledger (Tester)

> Source-only basis: `doc/changelog/branch-updates.md`  
> Scope: this log uses only commits in changelog entries that include `fix` in the commit message.  
> Note: changelog entries provide date only; exact commit time is not documented in the source file.

---

## Documented Bug/Error-to-Fix Register

| Bug/Error # | Documented Bug/Error                                                            | Status | Fix Commit | Changelog Date | Time in Changelog |
|---|---------------------------------------------------------------------------------|---|---|---|---|
| 1 | Seeder suffix was appended to first name instead of saved in `User.suffix`.     | Resolved | `039961a` | 2026-04-25 | Not specified |
| 2 | Campus admin view had a white-page rendering issue.                             | Resolved | `10648ad` | 2026-04-25 | Not specified |
| 3 | Migrations failed on fresh DB due to missing table-existence guards.            | Resolved | `25f401d` | 2026-04-25 | Not specified |
| 4 | Root `.env.example` was missing and needed restoration.                         | Resolved | `2dd8567` | 2026-04-25 | Not specified |
| 5 | Branding storage mount path needed bind-mount relocation.                       | Resolved | `2e1f78b` | 2026-04-25 | Not specified |
| 6 | Backend port conflict required restoring service port `8001`.                   | Resolved | `2ec8809` | 2026-04-25 | Not specified |
| 7 | Docker healthcheck relied on curl and needed Python-based check.                | Resolved | `34b1dd1` | 2026-04-25 | Not specified |
| 8 | Map behavior issue required a fix pass.                                         | Resolved | `570f250` | 2026-04-25 | Not specified |
| 9 | Seeder email generation needed collision-resistant retry behavior.              | Resolved | `798313e` | 2026-04-25 | Not specified |
| 10 | PgAdmin storage path required bind-mount correction.                            | Resolved | `7be104a` | 2026-04-25 | Not specified |
| 11 | Frontend chat sidebar had invalid nested button structure.                      | Resolved | `9d4214f` | 2026-04-25 | Not specified |
| 12 | Face attendance/verification errors were inconsistent and needed normalization. | Resolved | `a29a0ac` | 2026-04-25 | Not specified |
| 13 | Backend startup crashed on email-init failure; needed warning-only degrade mode. | Resolved | `ca85538` | 2026-04-25 | Not specified |
| 14 | InsightFace model storage path required bind-mount relocation.                  | Resolved | `ccaf3a4` | 2026-04-25 | Not specified |
| 15 | Postgres data path required bind-mount relocation.                              | Resolved | `e347c9f` | 2026-04-25 | Not specified |
| 16 | SG/ORG event visibility and face-rec account locking scope needed enforcement.  | Resolved | `eab6f3b` | 2026-04-25 | Not specified |
| 17 | Seeding behavior needed opt-in profile and bootstrap dependency wiring.         | Resolved | `ef05af9` | 2026-04-25 | Not specified |
| 18 | `EventStatus` enum persistence used wrong casing and needed lowercase values.   | Resolved | `f155a4c` | 2026-04-25 | Not specified |
| 19 | Session expiry check had timezone comparison mismatch.                          | Resolved | `f73133c` | 2026-04-25 | Not specified |
| 20 | Backend Docker service lacked healthcheck coverage.                             | Resolved | `f8aa30e` | 2026-04-25 | Not specified |
| 21 | School settings flow crashed on manual Pydantic validation error.               | Resolved | `3ef9a09` | 2026-04-26 | Not specified |
| 22 | CI compose/env path, frontend casing, and node warnings needed correction.      | Resolved | `6194936` | 2026-04-26 | Not specified |
| 23 | CI ssh-action used invalid `script_stop` input.                                 | Resolved | `8f11fe2` | 2026-04-26 | Not specified |
| 24 | CI referenced non-existent frontend lint/test scripts.                          | Resolved | `bf7a8e7` | 2026-04-26 | Not specified |
| 25 | Database image lacked pgvector support for vector extension.                    | Resolved | `c4ae534` | 2026-04-26 | Not specified |
| 26 | Bootstrap command missed required admin credential args.                        | Resolved | `d868e98` | 2026-04-26 | Not specified |
| 27 | Deploy flow needed bind-mount directory creation and ownership setup.           | Resolved | `f10055f` | 2026-04-26 | Not specified |
| 28 | Compose startup could fail without `SECRET_KEY`; fallback default required.     | Resolved | `f723626` | 2026-04-26 | Not specified |
| 29 | Docker production build missed `db_normalized` folder.                          | Resolved | `038cbbf` | 2026-04-27 | Not specified |
| 30 | Normalized-schema misalignment blocked backend startup and auth flow.           | Resolved | `0adef00` | 2026-04-27 | Not specified |
| 31 | Sanctions service/alembic env drifted from normalized schema contract.          | Resolved | `20ea2a8` | 2026-04-27 | Not specified |
| 32 | Alembic env path setup required `sys.path` initialization before app imports.   | Resolved | `28ce3b1` | 2026-04-27 | Not specified |
| 33 | Conflicting Alembic migration heads blocked deployment upgrade flow.            | Resolved | `28f3903` | 2026-04-27 | Not specified |
| 34 | Migrations needed idempotency checks to avoid duplicate object errors.          | Resolved | `4c8805b` | 2026-04-27 | Not specified |
| 35 | Normalized-schema migration needed non-destructive behavior.                    | Resolved | `7a8f47a` | 2026-04-27 | Not specified |
| 36 | Deploy flow required explicit migration-first execution for clearer logging.    | Resolved | `855b411` | 2026-04-27 | Not specified |
| 37 | Seeder demo generator was accidentally removed and had to be restored.          | Resolved | `93f7d02` | 2026-04-27 | Not specified |
| 38 | Critical frontend AI components were accidentally deleted in branch sync.       | Resolved | `b692243` | 2026-04-27 | Not specified |
| 39 | Docker/CI configs still pointed to old `assistant-v2` directory.                | Resolved | `cffa80b` | 2026-04-27 | Not specified |
| 40 | Parent migration path logic used wrong schema location and needed correction.   | Resolved | `f3b0689` | 2026-04-27 | Not specified |
| 41 | CI missing env file validation and gitignore casing issues.                     | Resolved | `9323700` | 2026-04-27 | Not specified |
| 42 | Seeder had unresolvable static import warning in seed.py.                       | Resolved | `201ae84` | 2026-04-28 | Not specified |
| 43 | Seeder date validation allowed start date later than end date.                  | Resolved | `aaaa01c` | 2026-04-28 | Not specified |
| 44 | Seeder alignment with pilot schema and new implementations needed fixes.        | Resolved | `04cacf8` | 2026-04-28 | Not specified |
| 45 | Forgot password function not properly exported in backendApi.js.                | Resolved | `8bb49ea` | 2026-04-28 | Not specified |
| 46 | ForgotPasswordView used non-existent api.js instead of backendApi.js.           | Resolved | `59e02ea` | 2026-04-28 | Not specified |
| 47 | Stale attendanceFlow imports in useGovernanceWorkspace needed removal.          | Resolved | `e5a8e27` | 2026-04-28 | Not specified |
| 48 | Runtime-config.js script tag lacked defer attribute causing Vite warning.       | Resolved | `b9b8cfd` | 2026-04-28 | Not specified |
| 49 | Stale column names in admin_server list_schools query.                          | Resolved | `c1c6196` | 2026-04-28 | Not specified |
| 50 | BaseUrl deprecation warning in jsconfig.json needed silencing.                  | Resolved | `28dc7e5` | 2026-04-28 | Not specified |
| 51 | Integration test fixture context teardown crash in parallel workers.            | Resolved | `4f5562b` | 2026-04-28 | Not specified |
| 52 | Vite HMR connection timeout on networkidle wait in CI.                          | Resolved | `bb3f738` | 2026-04-28 | Not specified |
| 53 | Vite cold start timeout in CI with custom test.extend context fixture.          | Resolved | `4b1838c` | 2026-04-28 | Not specified |
| 54 | LocalStorage not cleared before login tests causing session bleed.              | Resolved | `2a741a8` | 2026-04-28 | Not specified |
| 55 | E2E tests missing backend test data (campus_admin@test.com).                    | Resolved | `9a7e928` | 2026-04-28 | Not specified |
| 56 | E2E tests #email selector not found due to localStorage state.                  | Resolved | `007d691` | 2026-04-28 | Not specified |
| 57 | LocalStorage and sessionStorage not cleared before page load in E2E.            | Resolved | `a6c8a54` | 2026-04-28 | Not specified |
| 58 | LocalStorage:5173 not explicitly cleared in storageState config.                | Resolved | `110b59b` | 2026-04-28 | Not specified |
| 59 | GitHub Actions base path auto-detection served app at /RIZAL_v1/ not /.        | Resolved | `838c005` | 2026-04-28 | Not specified |
| 60 | Vite config base path auto-detection caused E2E tests to fail.                  | Resolved | `9292715` | 2026-04-28 | Not specified |
| 61 | Mobile viewport not used in Playwright causing selector mismatches.             | Resolved | `7480a08` | 2026-04-28 | Not specified |
| 62 | Desktop-blocking screen in App.vue prevented rendering on all viewports.        | Resolved | `c22a53c` | 2026-04-28 | Not specified |
| 63 | Terms modal click in E2E login helper caused navigation failure.                | Resolved | `a885c0e` | 2026-04-28 | Not specified |
| 64 | Chat trigger selector used wrong aria-label in E2E tests.                       | Resolved | `a200c89` | 2026-04-28 | Not specified |
| 65 | Two-step chat open flow not implemented in E2E tests.                           | Resolved | `2ac9e7f` | 2026-04-28 | Not specified |
| 66 | Assistant E2E tests didn't match actual chat state (under development).         | Resolved | `9eaf51e` | 2026-04-28 | Not specified |
| 67 | Frontend-assistant E2E tests ran when chat not connected to assistant.          | Resolved | `45232f1` | 2026-04-28 | Not specified |
| 68 | Test_integration.py included in assistant unit test run causing failures.       | Resolved | `b123495` | 2026-04-28 | Not specified |
| 69 | VITE_APP_BASE_PATH not forced to / in E2E CI job.                               | Resolved | `6ff5e86` | 2026-04-28 | Not specified |
| 70 | Segfault on exit (139) not ignored in integration-tests CI job.                 | Resolved | `57c5ee2` | 2026-04-28 | Not specified |
| 71 | LocalStorage not cleared before every E2E test causing session bleed.           | Resolved | `092bd36` | 2026-04-28 | Not specified |
| 72 | Fresh browser context not used per test causing localStorage bleed.             | Resolved | `fbaffc5` | 2026-04-28 | Not specified |
| 73 | JSDoc type annotations missing in E2E login helpers causing ts-check errors.    | Resolved | `d0f467c` | 2026-04-28 | Not specified |
| 74 | Mcp_servers and backend not in pyrightconfig extraPaths for Pylance.            | Resolved | `9633574` | 2026-04-28 | Not specified |
| 75 | TermsModal emitted close instead of agree/decline events.                       | Resolved | `354ee69` | 2026-04-28 | Not specified |
| 76 | Frontend index.html not set to no-cache causing stale chunk errors.             | Resolved | `999fc22` | 2026-04-28 | Not specified |
| 77 | Stale chunk error showed boundary UI instead of auto-reloading.                 | Resolved | `1b5b555` | 2026-04-28 | Not specified |
| 78 | Backend .env and .env.example out of sync with config.py.                       | Resolved | `4fe6541` | 2026-04-28 | Not specified |
| 79 | Corrupt pwa icons needed replacement with correct production versions.          | Resolved | `c5fd561` | 2026-04-28 | Not specified |
| 80 | Corrupt logo/pwa images needed replacement and binary gitattributes.            | Resolved | `74ded60` | 2026-04-28 | Not specified |
| 81 | Assistant .env missing so SECRET_KEY unavailable for JWT verification.          | Resolved | `d53f7f9` | 2026-04-28 | Not specified |
| 82 | Dotenv load in auth.py happened after SECRET_KEY read at module level.          | Resolved | `a70910f` | 2026-04-28 | Not specified |
| 83 | Thought tags not stripped from assistant model output.                          | Resolved | `9c037c0` | 2026-04-28 | Not specified |
| 84 | Assistant env missing DATABASE_URL so MCP tools couldn't query backend DB.      | Resolved | `b6d2843` | 2026-04-28 | Not specified |
| 85 | %BASE_URL% placeholders in index.html causing path resolution issues.           | Resolved | `0b1637c` | 2026-04-28 | Not specified |
| 86 | Base path override in vite.config breaking logo paths.                          | Resolved | `6a98429` | 2026-04-28 | Not specified |
| 87 | Alembic env.py import pointed to wrong path (app.models.aura_norm).             | Resolved | `1f35bd6` | 2026-04-28 | Not specified |
| 88 | Exit code 134 (SIGABRT) not handled as non-fatal CPython shutdown crash.        | Resolved | `6a3fa07` | 2026-04-28 | Not specified |
| 89 | Test_google_auth.py used standalone SQLite causing privacy_consent_types FK error. | Resolved | `fd00aa4` | 2026-04-28 | Not specified |
| 90 | Thought tag streaming not properly handled across chunk boundaries.             | Resolved | `089d320` | 2026-04-28 | Not specified |

---

## Source Reference

- [branch-updates.md](../../../changelog/branch-updates.md)
