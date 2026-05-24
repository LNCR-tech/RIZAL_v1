# CI Testing Changes

This file documents the local-only automated testing changes added for UI/UX and pressable-control coverage.

## Scope

- These changes add runnable Playwright tests and test helpers.
- These changes do not modify `.github/workflows/ci.yml`.
- The new tests are intended to run locally through `npm run test:e2e:uiux`.
- The local UI/UX script runs with one Playwright worker to avoid local browser overload from the broad route crawler.
- The dynamic pressable crawler has no per-route cap. It clicks every collected safe pressable for each route.
- The dynamic pressable crawler now fails a pressable if clicking it produces no detectable UI result.
- No files were removed.

## Added Files

### `frontend-web/e2e/helpers/pressables.ts`

- Adds shared helpers for dynamic pressable-control coverage.
- Defines route lists for preview dashboard, workspace, governance, admin, student, and campus-admin pages.
- Finds visible safe pressables such as buttons, links, switches, and tabs.
- Skips risky or destructive controls such as delete, reset, approve, reject, publish, save, submit, upload, download, export, retry, sign out, and external links.
- Skips permission/state-dependent attendance controls such as check-in/sign-out.
- Skips global navigation/back controls because exact workflow tests cover route navigation more reliably.
- Returns every collected page-local safe pressable. There is no default cap.
- Checks that clicking a safe pressable keeps the app usable, does not show the fatal app screen, and does not land on the Not Found page.
- Captures a before/after page-effect snapshot so no-op buttons are reported as test failures.
- Records locating details for each failed pressable, including route, label, tag, role, type, id, class, name, `data-testid`, DOM index, CSS path, and an HTML snippet.
- Wraps each click in a Playwright `test.step`, so the failing output names the exact route and pressable that failed.
- Adds expected checks when the control has a known signal, such as:
  - internal link navigates to its own href
  - `aria-expanded` toggles or opens a menu/dialog
  - `aria-pressed` toggles
- Accepts other visible UI effects by comparing URL, title, visible text, visible control count, dialog/menu/toast count, ARIA selected/checked/open counts, form-control state, active/open/selected classes, and the clicked element snapshot.

### `frontend-web/e2e/workflows/pressable-coverage.spec.ts`

- Adds dynamic safe-pressable tests.
- Covers public preview/login pages.
- Covers School IT preview pages.
- Covers governance and admin preview pages.
- Covers authenticated student pages using mock auth.
- Covers authenticated campus-admin pages using mock auth.
- Splits coverage into one Playwright test per route so uncapped per-route crawling has its own timeout budget.
- Each test block includes a comment explaining what the test does.

### `frontend-web/e2e/workflows/expected-ui-actions.spec.ts`

- Adds exact expected-result tests for important UI actions.
- Covers login password visibility and forgot-password navigation.
- Covers student nav, profile notification toggle, edit profile open/cancel, and security route navigation.
- Covers campus-admin nav, schedule settings, monitor route, reports route, and settings route.
- Covers governance event creation UI and audience selector field visibility.
- Covers workspace preview schedule settings, monitor route, and reports route.
- Each test block includes a comment explaining what the test does.

### `CI_changes.md`

- Adds this local documentation file.
- Records every file addition/change/removal in this testing pass.

## Changed Files

### `frontend-web/e2e/base.ts`

- Expanded Playwright mock-auth responses so UI/UX tests can run without the backend.
- Added mock departments and programs for audience/year-level selector tests.
- Added mock events for event list/detail screens.
- Added mock admin school and School IT account data for admin screens.
- Added mock governance unit/access data for governance screens.
- Added mock GET responses for:
  - departments
  - programs
  - users
  - governance access
  - governance units
  - governance students
  - governance SSG setup
  - admin school list
  - School IT account list
  - audit logs
  - notification logs
  - governance settings
  - governance requests
  - event list
  - event detail
  - event time status
  - event attendance/report endpoints
- Added a mock backend-hosted Aura logo image response for preview data that resolves media through the backend base URL.
- Added a harmless warning allowlist for browser WebGL `ReadPixels` performance noise from animated login visuals.

### `frontend-web/package.json`

- Updated `test:e2e:uiux` to pass `--workers=1`.
- Updated `test:e2e:uiux:backend` to pass `--workers=1`.
- This keeps the local UI/UX suite stable on this machine; it does not change the GitHub Actions workflow.

## Removed Files

- None.

## Local Commands

Run the UI/UX tests locally:

```powershell
cd "C:\Users\ACER\Documents\Software Dev\AURA\RIZAL_v1\frontend-web"
npm run test:e2e:uiux
```

Run only the new expected-result tests:

```powershell
npx playwright test e2e/workflows/expected-ui-actions.spec.ts
```

Run only the new dynamic pressable tests:

```powershell
npx playwright test e2e/workflows/pressable-coverage.spec.ts
```

## Verification

- `npx playwright test --list e2e/workflows` listed 16 workflow tests.
- `npx playwright test e2e/workflows/expected-ui-actions.spec.ts --project=chromium --reporter=list` passed: 5/5.
- `npx playwright test e2e/workflows/pressable-coverage.spec.ts --project=chromium --reporter=list` passed: 5/5.
- `npm run test:e2e:uiux -- --project=chromium --reporter=list` passed: 16/16 in about 8.9 minutes.

## Follow-Up Change: Remove Pressable Cap

- Removed `PLAYWRIGHT_MAX_PRESSABLES_PER_ROUTE`.
- Removed the `.slice(...)` cap from `collectSafePressables`.
- Changed `pressable-coverage.spec.ts` from five grouped tests into one generated test per route.
- The crawler still skips risky/destructive controls, global navigation, date-only calendar buttons, external links, hidden controls, and disabled controls.
- The crawler now tests every safe pressable that remains after those safety filters.
- After this change, `npx playwright test --list e2e/workflows/pressable-coverage.spec.ts` lists 52 dynamic pressable tests.
- After this change, `npx playwright test --list e2e/workflows` lists 63 workflow tests total.
- Targeted uncapped verification passed for the login route and workspace schedule preview route.
- The full uncapped UI/UX suite has not been rerun yet after this follow-up change; expect it to take longer than the earlier capped 8.9 minute run.

## Follow-Up Change: No-Op Pressable Detection

- Updated `frontend-web/e2e/helpers/pressables.ts` so a collected safe pressable must produce an observable result after click.
- A pressable passes when it performs an expected result such as:
  - navigating to its internal `href`
  - toggling `aria-expanded`
  - toggling `aria-pressed`
  - changing visible page text/state
  - opening/closing a dialog, menu, toast, details element, or selected/checked state
  - changing a visible form control, such as the login password visibility toggle changing the password input type
- A pressable fails when the click leaves the page in the same detectable state.
- Failure output is intentionally location-heavy so the bad control can be found quickly after the run.
- The failure includes:
  - route name and route path
  - before and after URLs
  - label, tag, role, type, id, class, name, and `data-testid`
  - DOM index among pressables
  - generated CSS path
  - HTML snippet
  - Playwright screenshot, video, trace, and error-context artifact paths

## Latest Verification

- `npx playwright test e2e/workflows/pressable-coverage.spec.ts --project=chromium --reporter=list --grep "^.*login keeps"` passed: 1/1.
- `npx playwright test e2e/workflows/pressable-coverage.spec.ts --project=chromium --reporter=list --grep "student profile preview"` failed as expected on the no-op `Settings` button in `/exposed/dashboard/profile`.
- The profile `Settings` failure now reports `No detectable UI result after clicking pressable` and includes the generated CSS path plus the button HTML.
- The full UI/UX suite has not been rerun after no-op detection. It will fail until existing no-op pressables are fixed, disabled, removed, or given a specific expected-result behavior.

## Follow-Up Change: Assistant Tests in CI

- Updated `.github/workflows/ci.yml`.
- Added a dedicated `assistant-tests` job.
- The job installs `assistant/requirements.txt`.
- The job runs `pytest tests/` from the `assistant` directory.
- The job uses a local SQLite assistant database through `ASSISTANT_DB_URL=sqlite:///./test_assistant_ci.db`.
- The existing E2E Playwright job now waits for `assistant-tests` in addition to backend and frontend tests.
- No coverage threshold was added.

## Follow-Up Change: Deterministic Backend Test Seed Data

- Updated `backend/tests/conftest.py`.
- The shared backend test seed now creates deterministic student users for year-level tests:
  - `student@test.com`, Year 1
  - `student_year2@test.com`, Year 2
  - `student_year5@test.com`, Year 5
- The shared backend test seed now creates a deterministic event named `Seed Year Level Event`.
- The seed event has an `ALL` event target so tests that need at least one event no longer skip just because no event exists.
- Existing test users are reset to known roles, school IDs, passwords, and active student-profile data.

## Follow-Up Change: Backend Year-Level Filtering Tests

- Added `backend/tests/test_year_level_filtering.py`.
- Added an API-level test that creates a Year 2 scoped event and verifies:
  - the backend persists `event_targets` with `scope_type=YEAR_LEVEL`
  - a Year 2 student is eligible
  - a Year 1 student is rejected with `STUDENT_NOT_INCLUDED_IN_EVENT_SCOPE`
- Added an API-level test that creates a `COURSE_YEAR` scoped event and verifies:
  - matching course and matching year passes
  - matching course with the wrong year fails
- Each test includes comments explaining what the test protects.

## Follow-Up Change: Frontend Year-Level Filtering Tests

- Added `frontend-web/tests/unit/components/EventEditorSheet.spec.js`.
- The component tests verify that the event editor:
  - shows only the year selector for `YEAR_LEVEL`
  - shows department plus year for `DEPARTMENT_YEAR`
  - shows course plus year for `COURSE_YEAR`
  - emits the exact backend `event_targets` payload for each scope
- Added one exact Playwright workflow test to `frontend-web/e2e/workflows/expected-ui-actions.spec.ts`.
- The new Playwright test creates a preview governance event with a Year 4 audience and verifies the event appears in the visible feed.
- The new Playwright test uses the current calendar month because the preview feed only displays the current calendar month.

## Latest Verification After CI/Year-Level Changes

- `npx vitest run tests/unit/components/EventEditorSheet.spec.js tests/unit/services/eventEditor.spec.js` passed: 2 files, 47 tests.
- `npx playwright test e2e/workflows/expected-ui-actions.spec.ts --project=chromium --reporter=list --grep "year-level audience"` passed: 1/1.
- `npx playwright test --list e2e/workflows/expected-ui-actions.spec.ts` listed 6 exact UI action tests.
- `node -e "JSON.parse(require('fs').readFileSync('frontend-web/package.json','utf8')); console.log('package.json ok')"` passed.
- `git diff --check` found no whitespace errors; it only printed Windows line-ending warnings.
- Backend and assistant pytest verification could not be run locally through the default Python because `pytest` is not installed.
- Backend and assistant pytest verification also could not use the repo virtualenvs because both virtualenvs point to an old missing Python path: `C:\Users\USER\AppData\Local\Programs\Python\Python312\python.exe`.

## Follow-Up Change: URL Resolution Unit Test Isolation

- Updated `frontend-web/tests/unit/services/urlResolution.spec.js`.
- The test now stubs `VITE_API_BASE_URL` and `VITE_ASSISTANT_BASE_URL` to empty strings before each URL fallback assertion.
- This makes the fallback tests independent from local `.env` values such as `http://localhost:8000` and `http://localhost:8500`.
- Added a setup comment explaining why the env stubs are needed.
- Verified `npx vitest run tests/unit/services/urlResolution.spec.js` passed: 1 file, 6 tests.
- Verified `npm run test:unit` passed: 6 files, 83 tests.
- Vitest still reports `close timed out after 10000ms` after successful completion; this is a lingering-process warning after tests pass, not a failed assertion.

## Follow-Up Change: Playwright Failure Source Hints

- Updated `frontend-web/e2e/helpers/pressables.ts`.
- Added route-to-source-file hints for dashboard, workspace, governance, admin, login, and forgot-password routes.
- Dynamic pressable no-op failures now include a `Likely source files` section.
- Dynamic pressable no-op failures still include label, tag, role, type, class, `data-testid`, DOM index, CSS path, and HTML snippet.

- Updated `frontend-web/e2e/workflows/pressable-coverage.spec.ts`.
- Dynamic pressable test titles now include the likely source component in brackets, so the Playwright failure summary is easier to scan.
- Updated `frontend-web/e2e/workflows/expected-ui-actions.spec.ts`.
- Exact UI action test titles now include likely source components in brackets.
- Verified `npx playwright test --list e2e/workflows/pressable-coverage.spec.ts --reporter=list` lists 52 tests with source hints.
- Verified `npx playwright test --list e2e/workflows/expected-ui-actions.spec.ts --reporter=list` lists 6 tests with source hints.
- Verified `npm run typecheck` passed.
- Verified the known profile `Settings` no-op failure now reports `frontend-web/src/views/dashboard/ProfileView.vue` and `frontend-web/src/router/index.js` as likely source files.

## Follow-Up Change: Remove Root Seeder Dependency

- Removed the leftover local `seeder/` directory from this machine.
- The root `seeder/` directory was already removed from git by the latest pull from `main`; the local copy only contained ignored files such as `.env` and Python cache files.
- Updated `.github/workflows/ci.yml`.
- Replaced the E2E `Seed DB` step that used `working-directory: seeder` and `python seed.py --ci-mode demo --schools 1`.
- The E2E workflow now seeds deterministic test data from `backend/tests/conftest.py` by calling `_seed(db)` from the backend working directory.
- This keeps the Playwright E2E job from depending on the deleted root `seeder/` folder while still creating the expected test users:
  - `admin@test.com`
  - `campus_admin@test.com`
  - `student@test.com`
- The backend application module `backend/app/seeder.py` was not removed because it is still the production bootstrap helper for baseline roles, event types, and the first admin account.

## Follow-Up Change: Coverage Expansion

- Added `frontend-web/tests/unit/services/locationDisplay.spec.js`.
- These tests cover coordinate labels, reverse-geocode labels, failed reverse-geocode responses, suggestion search filtering/sorting, empty search handling, distance measurement, and venue distance text.
- Added `frontend-web/tests/unit/services/devicePermissions.spec.js`.
- These tests cover web camera permission success/denial, geolocation granted/denied states, normalized browser coordinates, missing geolocation support, and precise-location rejection when accuracy stays too low.
- Added `frontend-web/tests/unit/components/EventLocationPicker.spec.js`.
- These tests cover existing coordinate rendering, clear pin behavior, search suggestions, selected suggestions, search errors, current-location success, current-location failure, and disabled/read-only behavior.
- Added `backend/tests/test_event_api_edge_cases.py`.
- These tests cover invalid event target field combinations, unknown program targets, incomplete required geofence fields, overlong idempotency keys, empty target updates, and invalid report date filters.
- Added `assistant/tests/test_deterministic_ai_behaviour.py`.
- These tests cover deterministic data intent detection, upcoming-event answers from mocked backend data, student absence answers, non-student attendance refusal, chart intent detection, chart visual payload shape, and raw attendance chart fallback.
- Updated `frontend-web/e2e/workflows/expected-ui-actions.spec.ts`.
- Added exact Playwright checks for bad-login rejection and student event-detail preview content.
- Added `frontend-web/e2e/workflows/ui-quality.spec.ts`.
- Added UI/UX checks that:
  - visible buttons and links on key routes have accessible names
  - key routes do not create horizontal overflow on mobile, tablet, or desktop viewport sizes
- Updated `frontend-web/src/views/dashboard/SchoolItScheduleView.vue`.
- Added `aria-label="Search events"` to the School IT schedule search icon button after the new accessibility-name test found it had no accessible name.

## Coverage Expansion Verification

- `npx vitest run tests/unit/services/locationDisplay.spec.js tests/unit/services/devicePermissions.spec.js tests/unit/components/EventLocationPicker.spec.js --reporter=dot` passed: 3 files, 20 tests.
- `npm run test:unit` passed: 9 files, 103 tests.
- Frontend unit coverage increased to:
  - statements: 58.85%
  - branches: 54.58%
  - functions: 65.72%
  - lines: 60.33%
- `npx playwright test --list e2e/workflows --reporter=list` now lists 68 workflow tests.
- `node ./scripts/run-playwright-suite.mjs --mock-auth e2e/workflows/expected-ui-actions.spec.ts e2e/workflows/ui-quality.spec.ts --project=chromium --reporter=list --workers=1` passed: 10/10.
- `npm run lint` passed.
- `npm run typecheck` passed.
- `python -m py_compile tests/test_event_api_edge_cases.py` passed from the backend directory.
- `python -m py_compile tests/test_deterministic_ai_behaviour.py` passed from the assistant directory.
- Backend and assistant pytest verification could not be run locally because the current Python executable is `C:\Python314\python.exe` and does not have `pytest` installed.
- `git diff --check` found no whitespace errors; it only printed Windows line-ending warnings.

## Current CI Capabilities

After the latest testing changes, the GitHub CI workflow can check the following areas.

### Security

- Runs `npm audit --audit-level=high` for frontend dependencies.
- Scans backend application code for simple hardcoded `api_key`, `password`, or `secret` assignment patterns.

### Backend

- Starts Postgres and Redis service containers.
- Installs backend dependencies.
- Runs backend lint with `flake8`.
- Creates the test database.
- Runs Alembic migrations.
- Runs backend pytest tests with coverage XML output.
- Uses deterministic backend seed data for shared event, student, and year-level test cases.
- Covers extra event API edge cases for invalid audiences, geofence validation, idempotency-key limits, empty target updates, and invalid report date filters.

### Assistant / AI

- Installs assistant dependencies.
- Runs `assistant/tests` directly with pytest.
- Tests assistant health, auth rejection, streaming shape, conversation storage, conversation isolation, quota behavior, and tool-call events.
- Tests deterministic AI behavior without real model calls, including data-answer intent detection, role-safe student attendance answers, and chart payload shape.
- Uses mocked AI responses for CI stability.
- Uses a SQLite assistant test database, so CI does not need a real AI API call for these tests.

### Frontend

- Installs frontend dependencies.
- Runs frontend lint.
- Runs frontend typecheck.
- Runs frontend unit tests.
- Includes unit coverage for event audience/year-level UI behavior.
- Includes unit coverage for location display helpers, device permission helpers, and the event location picker.

### E2E / Playwright

- Waits for backend, frontend, and assistant test jobs before running E2E.
- Starts Postgres and Redis.
- Runs backend migrations.
- Seeds deterministic E2E data from the backend test fixture helper instead of the deleted root `seeder/` folder.
- Starts the backend server.
- Starts the assistant server.
- Builds and starts the frontend preview server.
- Runs Playwright against the real running app.
- Fails on browser console errors.
- Exact UI action tests now include bad-login rejection and event-detail preview rendering.
- UI/UX quality tests check accessible names on visible buttons/links and horizontal overflow across mobile, tablet, and desktop viewports.
- Uploads Playwright screenshots, videos, traces, reports, backend logs, assistant logs, and frontend preview logs.

### Local UI/UX Tests Added In This Pass

- Exact UI action tests cover login controls, student profile controls, campus workspace controls, governance audience fields, workspace schedule controls, and preview governance event creation with a year-level audience.
- Dynamic pressable tests collect visible safe buttons, links, role buttons, switches, and tabs.
- Dynamic pressable tests click every collected safe pressable after filtering risky/destructive controls.
- No-op pressables now fail with route, label, DOM index, generated CSS path, HTML snippet, screenshot, video, trace, and error-context paths.

### Important Caveat

- GitHub CI only sees files that are committed and pushed.
- Any new test file that remains untracked will not run in CI.
- If the new local UI/UX files are added as-is, the broad pressable suite is expected to fail until known no-op controls, such as the student profile `Settings` button, are fixed, disabled, removed, or given a visible expected result.
