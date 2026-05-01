# Aura Frontend v3 Developer Guide

> **Status:** ACTIVE
> **Last Updated:** 2026-04-17

## Purpose

This is the combined-project frontend guide for the real frontend source of truth that came from `tempdocs2/docs` and was then aligned to the latest fetched `origin/aurav3` branch state.

## Stack

| Layer | Technology |
|---|---|
| Framework | Vue 3 |
| Build tool | Vite |
| Styling | Tailwind CSS 4 + CSS variables |
| Routing | Vue Router 4 |
| Mobile packaging | Capacitor |
| Auth storage | local browser storage plus auth/session metadata helpers |
| Runtime API config | `backendBaseUrl.js` + runtime config injection |

## What The Frontend Covers

The current frontend supports distinct role and workspace experiences for:

- students
- governance members
- School IT users
- platform admins
- preview/demo workspace routes under `/exposed/*`

Major product areas currently visible in the frontend:

- login, required password change, face registration, and privileged face MFA
- student dashboard, schedule, analytics, sanctions, and gather flows
- governance event management and sanctions drill-down screens
- School IT user, import, student-council, schedule, settings, and report flows
- admin overview, schools, accounts, oversight, and profile sections
- profile settings with synced dark mode and font-size preferences

## Key Frontend Behaviors Added Or Refreshed In April 2026

- privileged face MFA was restored and now routes through `/privileged/face`
- remembered-login preference is stored locally and forwarded to backend login as `remember_me`
- account-level UI preferences are synced with backend `user_app_preferences`
- governance event management gained dedicated sanctions routes and sanctions detail views
- preview workspaces mirror live admin, dashboard, School IT, and governance routes
- the frontend continues using platform-aware route resolution for desktop and mobile view variants

## Main Code Areas

| Area | Purpose |
|---|---|
| `src/router/` | route tree, access control, platform-aware view resolution |
| `src/services/` | API client, base URL logic, normalizers, local auth, preference helpers |
| `src/composables/` | auth, dashboard session bootstrap, workspace data, chat, notifications |
| `src/views/` | auth, dashboard, governance, School IT, admin, mobile, and tool views |
| `src/layouts/` | shared authenticated app shell |
| `public/` | logos, manifest, and PWA assets |
| `docker-entrypoint.d/` | runtime config injection for containerized deployment |

## Runtime Model

The frontend is built around runtime-resolved backend URLs rather than fixed tracked env files.

Current configuration pattern:

- `window.__AURA_RUNTIME_CONFIG__` when served through container/runtime injection
- Vite env values for development or build-time overrides
- native absolute API URLs for Capacitor builds
- fallback proxy-style web base URL `/__backend__`

Documented removal note:

- tracked frontend `.env.local`, `.env.docker`, `.env.docker.example`, and `.env.development.local` were removed from branch history on `2026-04-17`

## Recommended Reading Order

1. `../architecture/frontend-structure.md`
2. `../api/frontend-integration.md`
3. `./components.md`
4. `./theming-guide.md`
5. `./android-apk-build.md`
6. `../../changelog/frontend.md`

## Docs Index

| File | Contents |
|---|---|
| [Frontend Structure](../architecture/frontend-structure.md) | route groups, layout model, navigation guards |
| [Frontend API Integration](../api/frontend-integration.md) | API client behavior, endpoints, runtime config |
| [Components](./components.md) | component inventory and UI building blocks |
| [Theming Guide](./theming-guide.md) | branding and theme customization |
| [Android APK Build](./android-apk-build.md) | Android and Capacitor build guide |
| [Frontend Changelog](../../changelog/frontend.md) | finalized frontend change history |
| [Branch Updates](../../changelog/branch-updates.md) | raw frontend and merged branch history |

## Developer Checks

```bash
cd Frontend
npm install
npm run build
npm run lint
npm run test
```

Role and workflow checks worth repeating after changes:

1. student login, dashboard, analytics, sanctions, and gather
2. governance login, events, sanctions, and event detail
3. School IT users/import/schedule/report routes
4. admin overview, schools, accounts, and oversight
5. privileged login requiring face verification
6. profile preference save and reload on another session
