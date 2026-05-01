# Bug Reports — VALID8 Attendance Recognition System

> **Status:** ACTIVE — IN PROGRESS
> **Last Updated:** 2026-04-18
> **Author Role:** QA Engineer / Documentation Specialist
>
> See also: [test-cases.md](./test-cases.md) · [test-plan.md](./test-plan.md)

---

## Purpose

This file is the centralized defect register for testing, retesting, and release decisions.
Every confirmed bug must live here with a unique ID before a release can be approved.

---

## Tracking Rules

- Use one unique bug ID per issue: `BUG-001`, `BUG-002`, and so on.
- Every failed test case in [test-cases.md](./test-cases.md) must link back to a bug ID here.
- Keep status current — do **not** leave resolved bugs as `Open`.
- Link each bug to impacted requirement IDs to preserve traceability.
- When a Qodana finding is confirmed as a real defect, record the Qodana fields using the dedicated template below.

---

## Status Workflow

| Status | Meaning | Exit Condition |
|---|---|---|
| Open | Confirmed defect awaiting assignment | Owner assigned and fix started |
| In Progress | Fix is actively being implemented | Fix merged and ready for validation |
| Blocked | Fix cannot continue due to external dependency | Blocking issue removed |
| Resolved | Fix implemented and ready for retest | QA retest completed |
| Verified | Retest passed; regression risk checked | Included in release notes/changelog |
| Closed | Finalized for target release | Documentation and cross-references updated |

---

## Severity Guide

| Severity | Definition | Release Impact |
|---|---|---|
| Critical | Security breach, data loss, or system-down behavior | Release blocker — fix before release |
| High | Core feature broken with no acceptable workaround | Release blocker unless formally waived |
| Medium | Partial degradation with workaround available | Can release with documented approval |
| Low | Minor issue with limited impact | Non-blocking — schedule in next cycle |

---

## Bug Report Template

```markdown
## BUG-XXX: [Short Title]

| Field | Value |
|---|---|
| Date Reported | YYYY-MM-DD |
| Reported By | Name / Role |
| Severity | Critical / High / Medium / Low |
| Priority | P1 / P2 / P3 |
| Status | Open / In Progress / Blocked / Resolved / Verified / Closed |
| Environment | Local Docker / Staging / Production |
| Requirement Impact | FR-XX.X |
| Linked Test Case | TC-XXXX or N/A |
| Endpoint / Area | e.g. POST /api/attendance/manual |
| Description | What happened |
| Steps to Reproduce | 1) ... 2) ... 3) ... |
| Expected Result | What should happen |
| Actual Result | What actually happened |
| Root Cause | Why it happened |
| Fix Summary | What was changed to resolve it |
| Verification Evidence | Test file, run output, or retest notes |
```

---

## Qodana Bug Report Template

Use this template when the issue was first identified by Qodana static analysis.

```markdown
## BUG-XXX: [Short Title]

| Field | Value |
|---|---|
| Date Reported | YYYY-MM-DD |
| Reported By | Name / Role |
| Severity | Critical / High / Medium / Low |
| Priority | P1 / P2 / P3 |
| Status | Open / In Progress / Blocked / Resolved / Verified / Closed |
| Environment | Local Docker / Staging / Production / CI |
| Requirement Impact | FR-XX.X or N/A |
| Linked Test Case | TC-XXXX or N/A |
| Area | Backend / Frontend / Assistant / Tooling |
| Qodana Exit Code | `7` / `137` / `255` or N/A |
| Qodana Finding Code | e.g. `QD-PY-001` |
| Qodana Inspection ID | e.g. `PyTypeChecker` |
| File | e.g. `Backend/app/services/example.py` |
| Description | What Qodana detected |
| Runtime Risk | Why this can matter in actual app behavior |
| Steps to Reproduce | 1) Run Qodana 2) Open the flagged file 3) inspect the reported line or code block |
| Expected Result | No valid static-analysis defect remains after the fix |
| Actual Result | Qodana reports the issue and the defect is confirmed or credible |
| Root Cause | Why the code pattern exists |
| Fix Summary | What was changed to remove the problem |
| Verification Evidence | Qodana rerun, diff, test output, or manual retest |
```

### When to log a Qodana finding as a bug

Create a bug entry when the finding is:

- clearly a correctness or security problem
- reproducible in code review, local execution, or follow-up testing
- important enough to track to completion

Do not create a formal bug entry for:

- obvious false positives
- cleanup-only findings fixed immediately in the same working session
- duplicate findings already tracked under another bug ID

Reference:

- [qodana-error-reference.md](./qodana-error-reference.md)

---

## Active Register

---

## BUG-001: Alembic migration fails without DATABASE_URL environment variable

| Field | Value |
|---|---|
| Date Reported | 2026-03-18 |
| Reported By | Backend Team |
| Severity | High |
| Priority | P1 |
| Status | Verified |
| Environment | Local Docker |
| Requirement Impact | FR-07.2 |
| Linked Test Case | TC-FR07-01 |
| Endpoint / Area | Alembic `env.py` |
| Description | Running `alembic upgrade head` without an exported `DATABASE_URL` failed to connect. |
| Steps to Reproduce | 1) Start local setup without exporting `DATABASE_URL` 2) Run `alembic upgrade head` |
| Expected Result | Migration command resolves database URL from standard project configuration. |
| Actual Result | Migration command failed due to missing runtime variable. |
| Root Cause | Alembic environment did not auto-load the project `.env` file. |
| Fix Summary | `alembic/env.py` updated to load `Backend/.env` before resolving the DB URL. |
| Verification Evidence | Local migration retest succeeded after the change. |

---

## BUG-002: Queue pool overflow under concurrent login load

| Field | Value |
|---|---|
| Date Reported | 2026-03-17 |
| Reported By | Backend Team |
| Severity | High |
| Priority | P1 |
| Status | Verified |
| Environment | Production-like Docker |
| Requirement Impact | FR-01.1, FR-01.6 |
| Linked Test Case | TC-FR01-01, TC-FR01-02 |
| Endpoint / Area | `POST /login` |
| Description | Concurrent login traffic exhausted default SQLAlchemy pool limits, causing request failures. |
| Steps to Reproduce | 1) Start backend with default pool settings 2) Send 50+ concurrent login requests via load test |
| Expected Result | Login remains stable within expected concurrency baseline. |
| Actual Result | Requests failed with pool overflow errors once capacity was exhausted. |
| Root Cause | Default SQLAlchemy pool settings were too low for the observed load profile; login query was not optimized. |
| Fix Summary | Added pool tuning environment variables and optimized the login query to eager-load required relations. |
| Verification Evidence | Retested with `tools/load_test.py` — overflow no longer reproduced at prior failing threshold. |

---

## BUG-003: Face registration returns 500 for students with null `student_id`

| Field | Value |
|---|---|
| Date Reported | 2026-03-27 |
| Reported By | Backend Team |
| Severity | High |
| Priority | P1 |
| Status | Verified |
| Environment | Production |
| Requirement Impact | FR-04.2 |
| Linked Test Case | TC-FR04-04 |
| Endpoint / Area | `POST /api/face/register`, `POST /api/face/register-upload` |
| Description | Student accounts with `student_profile.student_id = null` caused Pydantic validation failure, returning a 500. |
| Steps to Reproduce | 1) Create student account without assigning a student ID 2) Call `/api/face/register` |
| Expected Result | Registration succeeds and response includes `student_id: null`. |
| Actual Result | Pydantic raised a validation error → 500 Internal Server Error. |
| Root Cause | `FaceRegistrationResponse.student_id` was marked non-nullable in schema. |
| Fix Summary | Changed `student_id` in `face_recognition.py` schema to allow `None`. |
| Verification Evidence | `Backend/app/tests/test_face_recognition_schemas.py` regression test added and passing. |

---

## BUG-004: Attendance endpoint returns 500 for students without an external student ID

| Field | Value |
|---|---|
| Date Reported | 2026-03-27 |
| Reported By | Backend Team |
| Severity | High |
| Priority | P1 |
| Status | Verified |
| Environment | Production |
| Requirement Impact | FR-04.3, FR-07.1 |
| Linked Test Case | TC-FR07-02 |
| Endpoint / Area | `GET /api/attendance/me/records` |
| Description | Students with `student_profile.student_id = null` caused response-model validation failures surfacing as CORS-style browser fetch errors. |
| Steps to Reproduce | 1) Log in as student with null student ID 2) Open attendance history page |
| Expected Result | `200` with `student_id: null` — no crash. |
| Actual Result | Response validation failure → `500` on server; CORS error in browser. |
| Root Cause | Attendance response schemas did not allow nullable `student_id`. |
| Fix Summary | Updated `schemas/attendance.py` to permit `student_id = null` across all attendance response payloads. |
| Verification Evidence | `Backend/app/tests/test_attendance_schemas.py` regression added and passing. |

---

## BUG-005: Merge conflict markers left in `student_import_service.py` crash backend

| Field | Value |
|---|---|
| Date Reported | 2026-03-28 |
| Reported By | Backend Team |
| Severity | Critical |
| Priority | P1 |
| Status | Verified |
| Environment | Local Docker (Windows checkout) |
| Requirement Impact | FR-02.3 |
| Linked Test Case | TC-FR02-01, TC-FR02-02 |
| Endpoint / Area | `Backend/app/services/student_import_service.py` |
| Description | Accidentally committed Git conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) caused an `IndentationError` on backend startup. |
| Steps to Reproduce | 1) Run `docker compose up -d --build` on the affected commit |
| Expected Result | Backend starts normally at `http://localhost:8000`. |
| Actual Result | Backend container entered a restart loop due to `IndentationError`. |
| Root Cause | Merge conflict markers were not removed before committing. |
| Fix Summary | Removed conflict markers; kept intended behavior (Celery task publish with inline fallback). |
| Verification Evidence | Backend startup confirmed clean; `http://localhost:8000/docs` loads. |

---

## BUG-006: CRLF line endings in shell scripts break Docker startup on Windows

| Field | Value |
|---|---|
| Date Reported | 2026-03-28 |
| Reported By | Backend Team |
| Severity | High |
| Priority | P1 |
| Status | Verified |
| Environment | Local Docker (Windows) |
| Requirement Impact | FR-07.2 |
| Linked Test Case | TC-FR07-01 |
| Endpoint / Area | `Backend/scripts/run-service.sh` |
| Description | Windows CRLF line endings in bind-mounted shell scripts caused `/bin/sh` parsing failures inside Linux containers. |
| Steps to Reproduce | 1) Clone repository on Windows 2) Run `docker compose up -d --build` |
| Expected Result | Backend and migrate services start successfully. |
| Actual Result | `docker compose up` fails early — `run-service.sh` exits with parse error. |
| Root Cause | Windows default Git checkout converts LF to CRLF; shell scripts must be LF. |
| Fix Summary | Added `.gitattributes` rule to force `*.sh` as LF; normalized existing scripts. |
| Verification Evidence | Fresh Windows Docker startup tested and passed after the change. |

---

## BUG-007: Duplicate/conflicting entries in BACKEND_CHANGELOG.md (unresolved merge conflict markers)

| Field | Value |
|---|---|
| Date Reported | 2026-04-08 |
| Reported By | Documentation Specialist (QA Review) |
| Severity | Low |
| Priority | P3 |
| Status | Open |
| Environment | N/A — documentation file |
| Requirement Impact | N/A |
| Linked Test Case | N/A |
| Endpoint / Area | `Backend/docs/BACKEND_CHANGELOG.md` (lines ~301–359) |
| Description | The `BACKEND_CHANGELOG.md` file contains live Git conflict markers (`>>>>>>>`, `<<<<<<<`, `=======`) left from a past merge. Two overlapping "How to Test" sections exist for the same change entry. |
| Steps to Reproduce | 1) Open `Backend/docs/BACKEND_CHANGELOG.md` 2) Search for `<<<<<<<` |
| Expected Result | Clean changelog with no conflict markers. |
| Actual Result | Raw merge conflict markers remain in the documentation file. |
| Root Cause | Merge commit was not properly resolved before being pushed. |
| Fix Summary | **Pending** — remove conflict markers and keep the correct "How to Test" section. |
| Verification Evidence | Pending resolution. |

---

## BUG-008: FR-01.1 and FR-01.2 are listed as identical requirements

| Field | Value |
|---|---|
| Date Reported | 2026-04-08 |
| Reported By | Documentation Specialist (QA Review) |
| Severity | Low |
| Priority | P3 |
| Status | Open |
| Environment | N/A — documentation file |
| Requirement Impact | FR-01.1, FR-01.2 |
| Linked Test Case | TC-FR01-01 |
| Endpoint / Area | `docs/requirements/functional-requirements.md` |
| Description | FR-01.1 and FR-01.2 are listed with identical text: "Users must log in with email and password." FR-01.2 likely intended to describe a different requirement (e.g., MFA or token refresh). |
| Steps to Reproduce | 1) Open `functional-requirements.md` 2) Compare FR-01.1 and FR-01.2 |
| Expected Result | Each requirement has a unique, distinct description. |
| Actual Result | Both FR-01.1 and FR-01.2 have the same text — FR-01.2 appears to be a copy-paste error. |
| Root Cause | Duplicate entry created during document authoring. |
| Fix Summary | **Pending** — clarify what FR-01.2 should describe (e.g., JWT token-based session maintenance, or email MFA trigger). |
| Verification Evidence | Pending owner clarification. |

---

## Release Gate Rule

- Any bug with `Open`, `In Progress`, or `Blocked` status **and** `Critical` or `High` severity must be resolved before release sign-off.
- `Low` and `Medium` bugs may ship with documented product owner approval.
- All `Verified` and `Closed` bugs are eligible for changelog reference.
