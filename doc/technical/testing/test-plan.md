# Test Plan — VALID8 Attendance Recognition System

> **Status:** ACTIVE — IN PROGRESS
> **Last Updated:** 2026-04-08
> **Author Role:** QA Engineer / Documentation Specialist
>
> See also: [test-cases.md](./test-cases.md) · [bug-reports.md](./bug-reports.md) · [functional-requirements.md](../../requirements/functional-requirements.md)

---

## 1. Purpose

This document defines how testing is planned, who is responsible, what is covered,
how defects are tracked, and what conditions must be met before a release can proceed.
Every tester and developer touching this project must follow this plan.

---

## 2. System Overview (Quick Reference)

| Item | Value |
|---|---|
| Project Name | VALID8 — Student Attendance Recognition System |
| System Type | Full-stack SaaS web application + mobile-ready frontend |
| Backend | FastAPI (Python), PostgreSQL, Celery, Alembic |
| Frontend | Vue 3 + Vite, Capacitor (mobile wrapper) |
| Infrastructure | Docker Compose (dev) · Docker Compose prod · Railway (cloud) |
| Auth | JWT session tokens, MFA via email, face-recognition gate |
| Face Recognition | InsightFace + ONNX Runtime |
| Email Delivery | Google Gmail API (OAuth2), Celery async task queue |
| Test Suite | pytest (21 test files, ~190+ automated test cases) |

---

## 3. Scope

### 3.1 In Scope

| Area | Coverage |
|---|---|
| Backend API functional testing | FR-01 through FR-07 |
| Auth and session management | Login, MFA, password change, session revoke |
| User and student management | CRUD, role assignment, bulk Excel import |
| Event management | Create, update, workflow status, attendance windows |
| Attendance | Manual, face-recognition scan, sign-in/sign-out phases |
| Governance hierarchy | SSG → SG → ORG unit scoping, permissions |
| Notifications | Email delivery, inbox, fallback path |
| Reporting and audit | Per-student/event reports, audit log, health endpoint |
| Frontend route guards | Auth, role-based redirection, face-enrollment gates |
| Import preview-first flow | Preview token enforcement, conflict detection |
| Regression testing | Re-run after every backend code change |

### 3.2 Out of Scope

- UI visual polish and cross-browser CSS differences
- Third-party infrastructure certification (Google OAuth endpoints, Railway platform)
- SMS notifications (placeholder only — FR-06.3)
- AI/anomaly detection features (listed as In Progress — not yet testable)
- Payment or billing flows (explicitly out of project scope)
- One-off local experiments with no reproducible steps

---

## 4. Test Environments

| Environment | URL | Purpose |
|---|---|---|
| Local (Docker) | `http://localhost:8000` (API) · `http://localhost:5173` (UI) | Main dev and regression testing |
| Local API Docs | `http://localhost:8000/docs` | Manual exploratory and Swagger smoke tests |
| Staging | TBD | Pre-release integration and stakeholder validation |
| Production | TBD (Railway deployment) | Smoke checks only — no destructive tests |

> **Setup note:** See `docs/technical/deployment/` and the project `README.md` for local Docker startup instructions.

---

## 5. Testing Strategy

### 5.1 Test Levels and Methods

| Test Level | Method | Evidence Location |
|---|---|---|
| Unit / Service | Automated `pytest` | `Backend/app/tests/test_*.py` |
| API / Integration | Automated `pytest` with `TestClient` | Route-level status and payload assertions |
| System / Flow | Manual + automated support | Import, governance scope, face-scan end-to-end checks |
| Frontend Route Guard | Manual browser walkthrough | Login → role-based redirect → face-enrollment gate |
| Performance Baseline | Scripted (`tools/load_test.py`) | Login concurrency observations |
| Security Smoke | Manual | JWT expiry, inactive school guard, unauthorized endpoint access |

### 5.2 Testing Types Applied

- **Functional Testing** — Every FR-01 through FR-07 requirement linked to at least one test case
- **Integration Testing** — Covers cross-service flows (import → email → Celery → delivery log)
- **Regression Testing** — Run full test suite after every backend change before merging
- **Edge Case Testing** — Null `student_id`, empty import files, expired tokens, out-of-scope governance actions
- **Negative Testing** — Invalid credentials, missing preview token, duplicate attendance, unauthorized roles
- **UI/UX Testing** — Manual browser walk-through per role (student, SSG, Campus Admin, Admin)
- **Security Testing** — Session guard, inactive school block, JWT tampering, face gate bypass toggle

---

## 6. Requirement Traceability Matrix

| Requirement Group | Coverage Focus | Primary Test Sources |
|---|---|---|
| **FR-01** Authentication and session | Login, MFA, inactive-school guard, password-change gate, session revoke | `test_api.py`, `test_auth_session_login_guard.py` |
| **FR-02** User management | User CRUD, role assign, bulk import preview-first flow, conflict detection | `test_api.py`, `test_admin_import_preview_flow.py`, `test_import_repository.py`, `test_student_import_service.py` |
| **FR-03** Event management | Event creation defaults, workflow status auto-sync, attendance windows, sign-out delay | `test_api.py`, `test_event_time_status.py`, `test_event_workflow_status.py` |
| **FR-04** Attendance | Manual attendance, face-scan phases, sign-in/sign-out completion, geofence, excused status | `test_attendance_status_support.py`, `test_public_attendance.py`, `test_event_geolocation_service.py`, `test_geolocation.py` |
| **FR-05** Governance hierarchy | Unit creation, officer assignments, scoped events, out-of-scope action denial | `test_governance_hierarchy_api.py` |
| **FR-06** Notifications | Email delivery, Celery task dispatch, inline fallback, Gmail API only transport | `test_email_service.py`, `test_student_import_email_delivery.py` |
| **FR-07** Reporting and audit | Health endpoint, attendance reports, audit log impact checks | `test_api.py` |

---

## 7. Test Execution Commands

```bash
# Full backend test suite inside Docker
docker compose exec backend python -m pytest

# Specific test module
docker compose exec backend python -m pytest app/tests/test_api.py -v

# Run governance hierarchy API tests
docker compose exec backend python -m pytest app/tests/test_governance_hierarchy_api.py -q

# Run all email delivery tests
docker compose exec backend python -m pytest app/tests/test_email_service.py app/tests/test_student_import_email_delivery.py -q

# Run via dedicated test service
docker compose run --rm test_backend

# Run load/concurrency baseline
docker compose exec backend python tools/load_test.py
```

---

## 8. Entry Criteria

Before testing begins on a feature or branch:

- [ ] Target branch is updated and `alembic upgrade head` migrations are applied
- [ ] Docker environment is running (`docker compose up -d` is healthy)
- [ ] Required environment variables are loaded (`.env` present and correct)
- [ ] Related requirement IDs are identified and documented in the test case
- [ ] Seed data is loaded (run `docker compose logs seed` to confirm)

---

## 9. Exit Criteria

Before a release is approved:

- [ ] All `Critical` and `High` priority tests pass
- [ ] No `Open`, `In Progress`, or `Blocked` bugs with Critical or High severity remain
- [ ] All failed tests reference a bug ID in [bug-reports.md](./bug-reports.md)
- [ ] Updated results are reflected in [test-cases.md](./test-cases.md)
- [ ] Backend changelog updated per `AGENTS.md` rule
- [ ] Documentation Specialist has reviewed all new test cases for traceability

---

## 10. Defect Workflow Rule

Every failure discovered during execution must have either:
- an existing bug ID linked in [bug-reports.md](./bug-reports.md), **or**
- a newly created bug entry before release sign-off.

No test is allowed to sit as "failed" without a corresponding bug ID.

---

## 11. Documentation Maintenance Rule

| Trigger | What to Update |
|---|---|
| New feature added | Add test cases in `test-cases.md`; add FR in `functional-requirements.md` |
| Requirement behavior changes | Update `test-cases.md` |
| Bug found | Add entry in `bug-reports.md` |
| Bug resolved and retested | Change bug status to `Verified` then `Closed` |
| Scope changes | Update Section 3 of this file |
| Environment changes | Update Section 4 of this file |
| Backend code changes | Update `Backend/docs/BACKEND_CHANGELOG.md` per `AGENTS.md` |
