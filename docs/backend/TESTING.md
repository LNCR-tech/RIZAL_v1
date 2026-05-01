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
