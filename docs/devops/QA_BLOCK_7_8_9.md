# QA Block Summary

## BLOCK 7 - Frontend Role E2E Tests
**Goal**: Verify the frontend reacts correctly to JWT role scopes (Campus Admin vs Student).
**Files**: `frontend-web/e2e/rbac.spec.ts`
**Risk covered**: Students navigating to `/admin/users` via URL, missing dashboards, console errors when hitting restricted endpoints.

## BLOCK 8 - Security / Negative Tests
**Goal**: Explicitly test for injection, rate limiting (XSS payloads, SQLi payloads), and bad actors.
**Files**: `backend/tests/test_security_negative.py`
**Risk covered**: Insecure parameter handling, XSS execution in Event names, Cross-school data leaks.

## BLOCK 9 - Performance Smoke Tests
**Goal**: Catch slow endpoints *before* they merge by failing CI if core routes breach SLA.
**Files**: `backend/tests/test_performance_smoke.py`
**Risk covered**: N+1 queries being merged that kill the database on the events list or user me endpoints.

## How to run locally
`pytest backend/tests/test_security_negative.py backend/tests/test_performance_smoke.py`
`npm run test:e2e --prefix frontend-web`