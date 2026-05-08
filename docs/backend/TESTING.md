# Backend Testing Hardening

## Overview
The backend testing strategy ensures all endpoints, database interactions, and authorization rules are thoroughly validated before deployment.

## Test Categories

1. **Unit Tests**: Fast tests for isolated functions and classes.
2. **Integration Tests**: Tests covering API endpoints and their interaction with the database.
3. **Auth & RBAC Tests**: Dedicated tests to ensure proper access control (JWT validation, role checks).
4. **API Contract Tests**: Validation of request/response schemas.
5. **Business Logic Tests**: Tests for complex logic (e.g., reports generation, attendance calculation).

## Required Quality Gates
- **Linting**: Enforced with `flake8`.
- **Coverage**: Minimum coverage thresholds must be met.
- **Migration Tests**: Ensure database schemas can upgrade and downgrade cleanly.
- **Seeder Tests**: Verify the deterministic CI user data is correctly loaded.

## Running Tests Locally
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_health.py
```

## Face Scan Regression Checks

When backend face-scan tuning changes, verify both the backend protection and the user-facing speed:

1. Start Gather or the public attendance kiosk and choose an active event.
2. Confirm the first scan fires immediately after the camera feed becomes live.
3. Re-scan the same recognized student and confirm the cooldown window is now about `3` seconds.
4. Keep scanning at normal kiosk speed for at least `30` seconds and confirm no regular scan loop hits a `429`.
5. Burst the endpoint much faster than normal and confirm throttling still happens instead of allowing unlimited CPU-heavy face requests.
