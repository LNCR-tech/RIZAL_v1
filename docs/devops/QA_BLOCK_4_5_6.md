# QA Block Summary

## BLOCK 4 - Bulk Import Tests
**Goal**: Validate admin import functionality for students, ensuring data constraints and failure reports work.
**Files**: `backend/tests/test_bulk_import.py`
**Risk covered**: Corrupted database from bad CSVs, duplicate ID/email constraints not catching errors, 500 errors on invalid foreign keys (departments).

## BLOCK 5 - API Contract Tests
**Goal**: Verify that payload shapes remain consistent and expected by the frontend.
**Files**: `backend/tests/test_api_contract.py`
**Risk covered**: Frontend breaking because backend changed `/me` shape or removed pagination wrappers silently.

## BLOCK 6 - Database Integrity Tests
**Goal**: Ensure migrations run cleanly and database engine enforces relationships.
**Files**: `backend/tests/test_database_integrity.py`
**Risk covered**: Orphaned foreign keys, multiple alembic heads causing deployment failures, lack of unique constraints on emails.

## How to run locally
`pytest backend/tests/test_bulk_import.py backend/tests/test_api_contract.py backend/tests/test_database_integrity.py`
