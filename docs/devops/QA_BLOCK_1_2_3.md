# QA Block Summary

## BLOCK 1 - Test Audit
The repository possesses a significant number of tests under `backend/tests/`. However, there were hidden failures in `.github/workflows/ci.yml` caused by `|| true` on test steps. 
Risk uncovered: Silent failures in CI pipeline meant broken backend logic could be merged. This has been resolved by removing `|| true`.

## BLOCK 2 - RBAC Matrix Tests
**Goal**: Ensure endpoints enforce their required roles correctly (no 403 leaks or broken 401 flows).
**Files**: `backend/tests/test_rbac_matrix.py` created.
**Risk covered**: Privilege escalation, unauthorized data access.

## BLOCK 3 - Attendance Logic Tests
**Goal**: Validate business rules surrounding event check-ins.
**Files**: `backend/tests/test_attendance_logic.py` created.
**Risk covered**: Duplicate check-ins, early check-ins bypassing policies.

## How to run locally
`pytest backend/tests/test_rbac_matrix.py backend/tests/test_attendance_logic.py`
