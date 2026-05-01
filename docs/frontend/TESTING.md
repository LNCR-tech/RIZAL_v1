# Frontend Test Hardening

## Overview
The frontend requires rigorous testing to ensure cross-browser compatibility, responsive design, and robust user interactions.

## Quality Gates
Before any deployment to Staging or Production, the following checks must pass:
1. **Linting**: Zero warnings tolerated.
2. **Typechecking**: `vue-tsc` must pass perfectly.
3. **Unit Tests**: `vitest` for component logic and state management (Pinia).
4. **E2E Tests**: Playwright scripts testing the full user journey (desktop and mobile viewports).

## Error Zero Tolerance
- Console errors during E2E tests will fail the build.
- Asset 404 detection is active during smoke tests.

## Running Locally
```bash
npm run test:unit
npm run test:e2e
```