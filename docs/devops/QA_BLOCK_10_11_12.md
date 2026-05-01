# QA Block Summary

## BLOCK 10 - Service Worker / Cache Tests
**Goal**: Catch runtime errors where the PWA offline capabilities break or `response.clone()` fails on stale assets.
**Files**: `frontend-web/e2e/sw-cache.spec.ts`
**Risk covered**: Users getting stuck on white screens after deployments because the service worker cached an old `index.html`.

## BLOCK 11 & 12 - Reporting & Final CI Gate
**Goal**: Aggregate everything into `ci.yml` and provide trace artifacts.
**Files**: `.github/workflows/ci.yml` (already verified and updated in previous steps to run all pytest and e2e paths).
**Risk covered**: Failing to provide developers with the actual screenshots or Playwright traces of *why* an E2E test failed.

## How to run locally
`npm run test:e2e --prefix frontend-web`