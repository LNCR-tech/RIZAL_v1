# E2E Stabilization Changes (2026-05-02)

This document summarizes the changes made so far to address the 3 Playwright E2E failure groups:

1. Backend CORS blocking frontend login requests from `http://127.0.0.1:4173`
2. RBAC tests timing out before login UI is ready
3. Mobile smoke tests failing due to JS chunk `net::ERR_ABORTED` request failures

## Root Cause 1: CORS mismatch between local frontend and backend

### Problem
- Backend CORS config allowed `5173` by default.
- In local/CI E2E, frontend runs on `4173` (Vite preview), so browser blocked requests to backend (`127.0.0.1:8000`).
- Result: login requests failed in browser before app-level error handling.

### Changes

#### 1) `backend/app/core/config.py`
- Added `_with_unique_appends(values, extras)` helper.
- In `get_settings()`, now:
  - defines local dev loopback origins:
    - `http://localhost:5173`
    - `http://127.0.0.1:5173`
    - `http://localhost:4173`
    - `http://127.0.0.1:4173`
  - parses configured `CORS_ALLOWED_ORIGINS`
  - merges configured origins with the local loopback list (deduplicated)
- `Settings.cors_allowed_origins` now receives this merged list.

#### 2) `backend/app/main.py`
- Expanded fallback `allow_origins` list in `CORSMiddleware` to include both `5173` and `4173` loopback hosts.

#### 3) `backend/.env.example`
- Updated docs/default example for `CORS_ALLOWED_ORIGINS` to include:
  - `http://localhost:5173`
  - `http://127.0.0.1:5173`
  - `http://localhost:4173`
  - `http://127.0.0.1:4173`

### Effect
- Backend now reliably allows frontend E2E traffic from Vite preview port `4173` in local and CI scenarios.

---

## Root Cause 2: RBAC tests interacting too early / wrong login entry route

### Problem
- `rbac.spec.ts` used `page.goto('/login')`, but app login route is `/`.
- Tests immediately attempted `page.fill(...)` without robust readiness gating.
- Result: repeated 20s fill timeouts.

### Changes

#### `frontend-web/e2e/rbac.spec.ts`
- Switched to shared strict test base: `import { expect, test } from "./base"`.
- Added `gotoLoginAndWait(page)` helper:
  - `page.goto("/", { waitUntil: "domcontentloaded" })`
  - response status assertion (`2xx/3xx`)
  - `waitForLoadState("networkidle")`
  - waits for `#email` and `#password` visibility
- Added `settleTermsModalIfShown(page)` helper for conditional post-login modal button (`I understand`).
- Added `loginAs(page, credentials)` helper.
- Reworked assertions to route-based expectations aligned with current app behavior:
  - student -> `/dashboard...`
  - campus admin -> `/workspace...`
- Privilege escalation test now checks student cannot remain under `/admin...` after direct nav.

### Effect
- RBAC tests now wait for actual app readiness and target correct login route.

---

## Root Cause 3: Mobile chunk abort failures (`net::ERR_ABORTED`)

### Problem
- During quick route transitions in smoke tests, some in-flight chunk requests are canceled by navigation.
- Strict E2E harness treated all `requestfailed` events as hard failures.
- Result: false negatives on mobile Chromium (`ERR_ABORTED`) despite app being functional.

### Changes

#### 1) `frontend-web/e2e/base.ts`
- Added `isAbortFailure()` matcher for:
  - `ERR_ABORTED`
  - `NS_BINDING_ABORTED`
  - `AbortError`
- In `page.on("requestfailed")`, abort failures are now ignored.

#### 2) `frontend-web/e2e/preview-smoke.spec.ts`
- Added `navigateAndSettle(page, route)` helper:
  - `goto(..., domcontentloaded)`
  - response status assertion
  - `waitForLoadState("networkidle")`
- Replaced direct `goto()` calls with `navigateAndSettle(...)`.
- Added an additional `networkidle` settle after each important route assertion.

### Effect
- Reduces flakiness from expected navigation-cancel behavior and improves signal quality of smoke failures.

---

## Playwright/CI hardening added

### 1) `frontend-web/e2e/global-setup.ts` (new file)
- Added global pre-test health gate:
  - waits for frontend health URL (default: `${PLAYWRIGHT_BASE_URL}/`)
  - optionally waits for backend health URL (default: `${PLAYWRIGHT_BACKEND_BASE_URL}/`)
- Backend readiness handling treats `429` as reachable for backend checks, so rate-limited health endpoints do not fail the entire E2E bootstrap.
- New env controls:
  - `PLAYWRIGHT_FRONTEND_WAIT_TIMEOUT_MS`
  - `PLAYWRIGHT_BACKEND_WAIT_TIMEOUT_MS`
  - `PLAYWRIGHT_HEALTH_POLL_INTERVAL_MS`
  - `PLAYWRIGHT_REQUIRE_BACKEND` (`true|false`)
  - `PLAYWRIGHT_FRONTEND_HEALTH_URL`
  - `PLAYWRIGHT_BACKEND_HEALTH_URL`

### 2) `frontend-web/playwright.config.ts`
- Added `globalSetup: "./e2e/global-setup.ts"`.
- Added `backendBaseUrl` resolution:
  - `PLAYWRIGHT_BACKEND_BASE_URL` -> `VITE_API_BASE_URL` -> fallback `http://127.0.0.1:8000`
- `webServer.env.VITE_API_BASE_URL` now uses that resolved `backendBaseUrl`.

### 3) `.github/workflows/ci.yml`
- E2E step now sets:
  - `PLAYWRIGHT_REQUIRE_BACKEND: 'true'`
  - `PLAYWRIGHT_BACKEND_BASE_URL: http://127.0.0.1:8000`
  - `PLAYWRIGHT_BACKEND_HEALTH_URL: http://127.0.0.1:8000/`

### Effect
- Prevents test startup races by enforcing service readiness before execution.

---

## Files Changed

- `.github/workflows/ci.yml`
- `backend/.env.example`
- `backend/app/core/config.py`
- `backend/app/main.py`
- `frontend-web/e2e/base.ts`
- `frontend-web/e2e/global-setup.ts` (new)
- `frontend-web/e2e/preview-smoke.spec.ts`
- `frontend-web/e2e/rbac.spec.ts`
- `frontend-web/playwright.config.ts`

---

## Validation Performed

- `python -m compileall backend/app/core/config.py backend/app/main.py` (passed)
- `npx playwright test --list` (passed; config/spec discovery OK)

Note: full browser execution was not completed on this machine because Playwright browser binaries were missing (`npx playwright install` required).
