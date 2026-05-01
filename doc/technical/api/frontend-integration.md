# Frontend API Integration Guide

> **Status:** ACTIVE
> **Last Updated:** 2026-04-18

## Purpose

This page explains how the Aura frontend talks to the backend in the current `origin/aurav3` branch state.

## Current Client Shape

The frontend does not use Axios anymore. The live API layer is a `fetch`-based client in `Frontend/src/services/backendApi.js`.

Core supporting files:

- `Frontend/src/services/backendApi.js`
- `Frontend/src/services/backendBaseUrl.js`
- `Frontend/src/services/backendNormalizers.js`
- `Frontend/src/services/localAuth.js`
- `Frontend/src/services/sessionExpiry.js`
- `Frontend/src/services/userPreferences.js`

## Base URL Resolution

`backendBaseUrl.js` resolves the API base URL from:

1. explicit runtime value
2. `window.__AURA_RUNTIME_CONFIG__`
3. Vite env values such as `VITE_API_BASE_URL`
4. native-platform fallbacks for Capacitor builds

Default web API base:

- `/__backend__`

Important runtime behavior:

- native builds should provide an absolute API URL
- ngrok URLs get an extra request header to skip the browser warning page
- import-related requests can use longer timeout values than normal API requests

## Request Behavior

The API client adds these behaviors on top of `fetch`:

- token-based `Authorization: Bearer ...` headers
- JSON and non-JSON response parsing
- centralized `BackendApiError` handling
- timeout handling with clearer offline and slow-backend messages
- session-expiry notification when authenticated calls return `401`
- fallback route retries when the backend exposes both `/api/*` and legacy direct prefixes

That fallback behavior exists because the backend route contract is still mixed in the current branch.

## Authentication Flow

Login uses:

- `loginForAccessToken(baseUrl, { username, password, rememberMe })`

This sends form data to:

- `POST /token`
- fallback: `POST /api/token`

The login request includes:

```text
username=<email>
password=<password>
remember_me=true|false
```

Frontend-side flow after login:

1. store access token and auth metadata
2. store remembered-login preference locally
3. redirect to `ChangePassword` if required
4. redirect to `PrivilegedFaceVerification` if the backend returned a face-pending session
5. otherwise initialize the full dashboard session and route the user to the correct workspace

## Important Endpoint Groups Used By The Frontend

### Session, profile, and preferences

- `GET /api/users/me/` or `/users/me/`
- `GET /api/users/preferences/me`
- `PUT /api/users/preferences/me`
- `POST /auth/change-password`

These endpoints power:

- profile bootstrap
- stored account settings sync
- dark mode and font-size persistence across devices
- password settings and required password-change flow

### Face and privileged verification

- `GET /api/auth/security/face-status`
- `POST /api/auth/security/face-reference`
- `POST /api/auth/security/face-verify`
- `POST /api/face/register`
- `POST /api/face/face-scan-with-recognition`

These power:

- first-time face registration
- profile face updates
- privileged face MFA after login
- attendance scan submission

### Events and attendance

- `GET /api/events/` or `/events/`
- `GET /api/events/:id` or `/events/:id`
- `PATCH /api/events/:id` or `/events/:id`
- `GET /api/attendance/me/records` and fallbacks
- `GET /api/attendance/events/:eventId/attendances-with-students`
- `GET /api/attendance/events/:eventId/report`
- `POST /api/attendance/face-scan-timeout`

### Governance and sanctions

- `GET /api/governance/access/me`
- `GET /api/governance/units`
- `GET /api/governance/units/:id/dashboard-overview`
- `GET /api/sanctions/dashboard`
- `GET /api/sanctions/events/:eventId/config`
- `PUT /api/sanctions/events/:eventId/config`
- `GET /api/sanctions/events/:eventId/students`
- `POST /api/sanctions/events/:eventId/students/:userId/approve`
- `GET /api/sanctions/events/:eventId/delegation`
- `PUT /api/sanctions/events/:eventId/delegation`
- `GET /api/sanctions/students/me`
- `GET /api/sanctions/students/:userId`
- `POST /api/sanctions/clearance-deadline`
- `GET /api/sanctions/clearance-deadline`

These power the governance event workspace, sanctions dashboard, sanctions detail screens, and student sanction views.

### School IT and admin operations

- departments, programs, and user CRUD endpoints under `/api/departments/*`, `/api/programs/*`, and `/api/users/*`
- import endpoints under `/api/admin/import-students*`
- school settings endpoints under `/api/school-settings/me` and related fallbacks

## Frontend Service Notes

Important frontend service behaviors now tied to backend integration:

- `userPreferences.js` stores remembered-login and font-size preferences locally
- backend `user_app_preferences` keeps the account-level dark-mode and font-size source of truth
- `sessionExpiry.js` surfaces expired-session feedback after `401` responses
- long-running face registration calls use a larger timeout because the face engine may still be warming up
- the face registration helper retries known InsightFace warm-up responses instead of failing immediately

## Runtime Configuration And Removed Tracked Env Files

The frontend branch no longer treats tracked `.env.*` files as the long-term source of truth.

Removed from tracked frontend branch history on `2026-04-17`:

- `.env.local`
- `.env.docker`
- `.env.docker.example`
- `.env.development.local`

The active documented runtime configuration model is now:

- container/runtime injection for production
- `window.__AURA_RUNTIME_CONFIG__`
- Vite env values only where explicitly documented
- `backendBaseUrl.js` as the final resolver

## Developer Testing

Useful checks for frontend/backend integration:

```bash
# Frontend build
cd Frontend && npm run build

# Frontend smoke and lint checks
cd Frontend && npm run lint
cd Frontend && npm run test
```

Manual checks that matter most:

1. login with and without `remember_me`
2. privileged login that triggers face MFA
3. profile preference save and reload on another session
4. governance event sanctions flows
5. School IT import and schedule/report routes
6. dashboard sanctions and gather routes

## Related Docs

- `error-contract.md`
- `../architecture/frontend-structure.md`
- `../frontend/README.md`
- `../../changelog/frontend.md`
- `../deployment/environment-variables.md`
