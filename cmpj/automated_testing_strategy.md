# Automated Testing Strategy: Framework and Scope

This document defines the strategy and functional boundaries for the automated tester implementation.

## 1. Implementation Overview

The testing framework consists of a standalone Python runner (`cmpj/auto_tests/run_tests.py`) designed to simulate user interactions without a graphical interface.

Operational workflow:

1. Direct API access against the backend (default `http://localhost:8000`) via `httpx`.
2. Role-based session simulation (Admin, Campus Admin, Student).
3. Governance and event-default validation through `/api/governance/*` routes.
4. Optional face verification status checks through `/api/auth/security/face-status`.

## 2. How to Run

1. Ensure the backend API is running.
2. Provide admin credentials via environment variables or CLI:
   - `ADMIN_EMAIL` and `ADMIN_PASSWORD`, or `--admin-email` / `--admin-password`.
3. Run:

```powershell
python cmpj/auto_tests/run_tests.py --base-url http://localhost:8000
```

4. Results are written to PSV logs under `cmpj/` by default.

## 3. Security Guardrails

- Do not enable bypass flags in production environments.
- If MFA or face verification bypass flags exist in dev, use them only for local QA.

## 4. Automated Test Coverage

The framework is designed to verify core backend flows including:

- Authentication and access control.
- School provisioning (create school + campus admin).
- Governance setup and permissions.
- Event creation and time-status endpoints.
- Bulk import preview.
- Multi-tenant isolation checks.

## 5. Testing Limitations

- UI/UX verification is manual.
- Cross-browser behavior requires manual checks.

