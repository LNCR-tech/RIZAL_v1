# Frontend Changelog

[<- Back to doc index](../README.md)

> **Status:** ACTIVE
> **Last Updated:** 2026-04-28
> **Purpose:** Frontend-only filtered and finalized change summary for AURA v3.2.

---

## SSOT Rule

- Raw change details live in [branch-updates.md](./branch-updates.md)
- This file keeps only frontend-scoped, finalized wording
- Do not duplicate full branch narratives here
- Rule: **Write once, reference everywhere**

---

## Finalized Frontend Entries

### [2026-04-28] Frontend Restructure and Responsive Layout Overhaul

- Split `frontend/` into `frontend-web/` (Vue SPA) and `frontend-apk/` (Capacitor Android native) for clearer separation of concerns.
- Implemented responsive layout with viewport-based switching between mobile and desktop views.
- Redesigned desktop login with split-screen layout for improved UX.
- Added `RouteErrorBoundary` component for graceful error handling across routes.
- Added `NotFoundView` for 404 error pages.
- Implemented auto-reload on stale chunk errors instead of showing error boundary UI.
- Added no-cache headers to index.html to prevent stale chunk errors during deployments.
- Fixed corrupt PWA icons and logo images; added binary gitattributes for proper handling.
- Removed `%BASE_URL%` placeholders from index.html that were causing path resolution issues.
- Fixed base path override in vite.config that was breaking logo paths.
- Synced frontend-web/src from production branch for latest stable features.
- **Source commits:** `532f88e`, `0b1637c`, `1b5b555`, `999fc22`, `74ded60`, `c5fd561`, `6a98429`, `00a13fa`, `8055f0c`, `c8896b9`
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-28] Google OAuth and Forgot Password Features

- Implemented Google OAuth sign-in with `GoogleSignInButton` component for both desktop and mobile login views.
- Added complete forgot password flow with email-based password reset.
- Added `useForgotPasswordViewModel` and `useGoogleLogin` composables for auth logic.
- Created dedicated `ForgotPasswordView` for desktop and mobile platforms.
- Updated `useLoginViewModel` to support multiple authentication methods.
- Fixed backendApi.js to properly export forgotPassword function.
- Removed obsolete Quick Attendance and Mock Views.
- **Source commits:** `0b2262a`, `d0bc443`, `8bb49ea`, `59e02ea`, `c8896b9`
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-28] E2E Testing Infrastructure with Playwright

- Added comprehensive Playwright E2E tests covering frontend↔backend and frontend↔assistant flows.
- Implemented E2E tests for login, authentication, navigation, and chat functionality.
- Fixed numerous E2E test issues: localStorage session bleed, stale chunk errors, Vite HMR timeouts.
- Added proper test isolation with fresh browser contexts per test.
- Configured Playwright with mobile viewport for accurate mobile testing.
- Added video recording and HTML logging for debugging failed tests.
- Seeded backend test data in CI for consistent test environments.
- Fixed TermsModal to emit agree/decline events instead of generic close.
- Removed desktop-blocking screen from App.vue for proper rendering on all viewports.
- Added frontend-web .gitignore to exclude test artifacts.
- Bumped Playwright workers to 3 for faster CI execution on 4-vCPU runners.
- **Source commits:** `78f4cfc`, `2d59520`, `45232f1`, `9eaf51e`, `2ac9e7f`, `a200c89`, `a885c0e`, `c22a53c`, `92e3eae`, `7480a08`, `9292715`, `838c005`, `110b59b`, `a6c8a54`, `007d691`, `9a7e928`, `2a741a8`, `4b1838c`, `bb3f738`, `4f5562b`, `9633574`, `d0f467c`, `3aadf1d`, `fbaffc5`, `092bd36`, `770f599`, `354ee69`
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-28] Assistant UI Enhancements

- Implemented thought tag streaming as collapsible sections in chat UI with chevron indicators.
- Store raw thought tags in database content, parse on frontend when loading history.
- Fixed thought tag handling across chunk boundaries and tool turns.
- Strip thought tags from conversation titles and sidebar last_message for cleaner display.
- Always start fresh conversation on chat open instead of restoring last session.
- Aligned docker ports with pilot stack configuration.
- Added defer attribute to runtime-config.js script tag to suppress Vite warnings.
- **Source commits:** `089d320`, `160f4b1`, `d3c29b6`, `2d8af1f`, `0a06d33`, `9c037c0`, `2a23462`, `807058d`, `dcd8d94`, `b9b8cfd`
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-28] Frontend Code Quality and Maintenance

- Added `BasePagination` component for consistent pagination UI across views.
- Removed stale attendanceFlow imports from useGovernanceWorkspace composable.
- Inlined formatDurationLabel, resolveMethodLabel, and resolveStatusLabel utilities.
- Fixed JSDoc type annotations in E2E login helpers to silence TypeScript errors.
- Added pyrightconfig.json for proper Pylance import resolution.
- Silenced baseUrl deprecation warning in jsconfig.json.
- Cleaned up redundant documentation and fixed stale frontend/ path references.
- **Source commits:** `0b2262a`, `e5a8e27`, `d0f467c`, `28dc7e5`, `885f81f`, `011f56b`
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-27] AI Surface Recovery and Assistant Rename Asset Sync

- Restored critical frontend AI components that were accidentally removed during branch synchronization.
- Synced frontend-facing assistant integration references after the `assistant-v2` to `assistant` rename.
- Refreshed Android splash/icon and branding asset paths in the same stabilization window.
- **Source commits:** `b692243`, `cffa80b`
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-26] Frontend Baseline Re-Sync to Main and Pre-Production

- Replaced the frontend tree with the latest main snapshot and then re-synced to the newest pre-production state.
- Kept release integration current while larger backend/deployment normalization work was landing.
- **Source commits:** `1b08d36`, `a0e7e09`
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-25] Face Verification and Attendance Error-Normalization UX

- Updated face-scan attendance and privileged face verification views to consume normalized backend face error contracts.
- Reduced inconsistent failure rendering across attendance and privileged verification flows.
- **Source commits:** `a29a0ac`
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-25] Frontend Baseline Replacement and Android Workspace Sync

- Replaced the frontend baseline with the `aura_mobileapk_v1.3` branch contents and aligned the merged structure under lowercase `frontend/`.
- Synced Capacitor Android workspace assets, app bootstrap/runtime integration, and related mobile attendance/event surfaces.
- Updated package/runtime wiring to match the merged mobile-capable frontend baseline.
- **Source commits:** `640c25e`, `2d0db6f`
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-25] Assistant Chat Merge: Real SSE Streaming plus Rich UI

- Replaced stubbed chat flow with real assistant SSE streaming and updated assistant base URL wiring.
- Merged richer assistant UI features including markdown rendering, visualization/chart surfaces, conversation list behaviors, and copy actions.
- Applied follow-up UI correctness fixes (including chat sidebar DOM nesting cleanup).
- **Source commits:** `cc0c0e0`, `04c27be`, `9d4214f`
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-25] Searchable Event Location UX and Map Interaction Improvements

- Added searchable event location flows across event editor/event picker views.
- Improved location display handling and map-related event interaction behavior across SG event screens.
- Synced supporting frontend services for location parsing and display.
- **Source commits:** `5681063`, `464c40c`, `570f250`
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-25] Governance/Council and Workspace Stability Refresh

- Extended governance/council management routing and workspace data flow updates.
- Improved SG dashboard loading behavior and fixed campus-admin white-page schedule rendering issues.
- Synced privileged face-verification and governance-related UI paths with backend changes.
- **Source commits:** `1c01cf0`, `1a4fbea`, `6a80bc8`, `10648ad`, `2657db0`, `6d72849`
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-25] Frontend Env-Tracking Cleanup and Config Matrix Alignment

- Stopped tracking machine-local frontend env override files in version control.
- Clarified frontend and repo-root env requirements and assistant origin optional variables in docs and examples.
- Kept frontend configuration docs aligned to the merged compose/runtime behavior.
- **Source commits:** `99e7504`, `1a64068`, `c27e605`
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-17] Privileged Face MFA Return and Account Preference Sync

- Restored privileged face-verification handling in the frontend login and route-guard flow.
- Added remembered login preference support and synced account-level app preferences for dark mode and font size.
- Expanded the profile screen so users can save configuration back to the backend and re-apply it on another device.
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-17] Governance Event Workspace and Sanctions Workflow Refresh

- Expanded the governance event workspace with sanctions controls, event editing improvements, and stronger scope-aware event handling.
- Added shared dashboard chart helpers and refreshed SG dashboard/event views with newer workspace metrics and flows.
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-16] Admin Workspace and Assistant Experience Sync

- Refreshed admin workspace reporting, charts, and oversight panels.
- Updated the frontend assistant chat flow to use stored conversation state and the current authenticated account scope more explicitly.
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-13] Workspace Dashboard and Notification Infrastructure Refresh

- Added dashboard report chart helpers and expanded workspace dashboards, notification flows, and home/profile surfaces.
- Synced the frontend with the current backend mail, notification, and workspace behavior changes.
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-05] Mobile Dashboard and User Analytics

- Added the mobile-first student dashboard view layer and expanded user-facing analytics support.
- Added attendance filtering and improved frontend normalization for analytics and attendance responses.
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-03] Routing and Mobile View Separation

- Split desktop and mobile rendering paths into dedicated view layers.
- Corrected routing to align the new mobile view structure with the existing desktop dashboard flows.
- Added Capacitor-oriented frontend support and Android build documentation.
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-04-02] Desktop and Mobile Frontend Architecture

- Introduced explicit desktop and mobile frontend architecture boundaries for dashboard rendering.
- Added the dashboard shell and extended School IT schedule and reporting views.
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-03-27] Deployment Frontend with Environment-backed Runtime Configuration

- Moved frontend deployment toward runtime-injected environment configuration.
- Updated Docker, Nginx, and runtime config templates so the frontend can be built once and configured per environment at startup.
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-03-25] MVP Readiness, Governance, and PWA Expansion

- Expanded the frontend with governance, SG, admin, and School IT workspace features.
- Added PWA assets and mobile support refinements for broader deployment readiness.
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-03-20] Dockerized Demo Frontend and School IT Expansion

- Added Dockerized frontend serving for demo and deployment scenarios.
- Expanded School IT workspace views, services, and supporting composables.
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-03-15] School IT Workspace Foundation and Android Optimization

- Established the School IT workspace foundation, including council, users, home, and related management flows.
- Added privileged face verification, document branding support, and Android/PWA optimization work.
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-03-14] Student Dashboard Ready and Security/Profile Expansion

- Marked the student dashboard flows as ready and expanded profile, security, and mobile dashboard support.
- Added backend integration helper services, session/auth support, and developer-facing API lab improvements.
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-03-13] Live Dashboard API Integration and Admin Setup Tooling

- Connected the frontend to the live backend dashboard API and added session-driven dashboard loading.
- Added face registration and API lab support to the frontend developer workflow.
- **Raw source:** [branch-updates.md](./branch-updates.md)

### [2026-03-10] Clean UI Frontend Rewrite Baseline

- Rebuilt the Aura frontend on Vue 3, Vite, Tailwind, and a school-aware theming system.
- Established the initial student dashboard, navigation, auth composable, and mock-data-backed UI baseline.
- **Raw source:** [branch-updates.md](./branch-updates.md)
