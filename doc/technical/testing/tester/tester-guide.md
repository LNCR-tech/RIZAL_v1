# Tester Guide — VALID8 Attendance Recognition System

> **Written by:** QA Engineer / Documentation Specialist
> **Date Started:** 2026-04-08
> **Purpose:** This is a personal + handoff guide. It documents every step taken during the QA process —
> from the first file opened to the last test case written. Any future tester can pick this up and
> continue exactly where things left off.
>
> See also: [qa-assessment.md](./qa-assessment.md) · [test-plan.md](./test-plan.md) · [test-cases.md](./test-cases.md) · [bug-reports.md](./bug-reports.md)

---

## What This Guide Is For

This guide answers three questions:

1. **What did I (the QA) actually do, step by step?**
2. **How should a new tester get started on this project?**
3. **What is still left to do?**

If you are reading this as a future tester — welcome. Everything you need is in this folder and the files it links to. Read this guide first, then open the others.

---

## Step 1 — Understand the Project Before Testing Anything

> **Rule:** Never write a test before you understand what the system is supposed to do.

### What I Did First

1. Opened `docs/project-overview/project-summary.md` — learned the system is called **VALID8**, a school attendance SaaS
2. Read `docs/requirements/functional-requirements.md` — learned the 7 feature groups (FR-01 through FR-07)
3. Scanned the folder structure of `Backend/` and `Frontend/src/` to understand what was already built
4. Read `Backend/app/main.py` to see all registered API routes
5. Read `Frontend/src/router/index.js` to understand all frontend pages and access guards

### What I Learned

- The backend is FastAPI (Python) with 16+ routers/modules
- The frontend is Vue 3 with 30 views across 4 role dashboards (Platform Admin, Campus Admin, Student)
- There are already 21 automated test files in `Backend/app/tests/`
- The system uses face recognition, geofencing, governance scoping, and Celery email queues — all of which need specific attention during testing

### If You Are a New Tester — Read These Files First

| File | Why |
|---|---|
| `docs/project-overview/project-summary.md` | What the system does and what is in/out of scope |
| `docs/requirements/functional-requirements.md` | What the system is supposed to do (FR-01 to FR-07) |
| `Backend/docs/BACKEND_PROJECT_STRUCTURE_GUIDE.md` | How the backend code is organized |
| `Backend/docs/BACKEND_CHANGELOG.md` | What changed recently and why |
| `docs/technical/testing/test-plan.md` | The full testing strategy |

---

## Step 2 — Set Up the Local Environment

> **Rule:** You cannot test without a working environment. Set this up before writing any tests.

### How to Start the Local Stack

```bash
# Start everything (backend, frontend, database, Celery, Redis)
docker compose up -d --build

# Check that all containers are healthy
docker compose ps

# View seed output to get demo credentials
docker compose logs --tail=200 seed

# Open the backend API docs
# http://localhost:8000/docs

# Open the frontend
# http://localhost:5173
```

### Demo Accounts (from seed logs)

Check the seed logs — they print the demo accounts for each role. You will need:

- A **student** account — to test login, attendance, schedule
- A **Campus Admin / School IT** account — to test import, users, settings
- An **SSG officer** account — to test manual attendance, event management
- An **admin** account — to test the admin workspace

### Key Environment Files

| File | What It Does |
|---|---|
| `Backend/.env` | Backend configuration — DB URL, email config, face scan config |
| `Frontend/.env.example` | Frontend API base URL and runtime config |
| `docker-compose.yml` | Full local stack definition |

> **Important:** If the backend does not start, check `Backend/.env` exists and is correct.
> Run `docker compose logs backend` to read startup errors.

---

## Step 3 — Read What Tests Already Exist

> **Rule:** Do not write tests that already exist. Find the gaps instead.

### Existing Automated Test Files

Located in `Backend/app/tests/`:

| File | What It Tests |
|---|---|
| `test_api.py` | Large regression test — login, events, attendance, health, import |
| `test_auth_session_login_guard.py` | Inactive school blocking |
| `test_admin_import_preview_flow.py` | Preview-first import enforcement |
| `test_import_repository.py` | Import data repository layer |
| `test_student_import_service.py` | Import service business logic |
| `test_student_import_email_delivery.py` | Onboarding email after import |
| `test_email_service.py` | Gmail API email delivery |
| `test_event_time_status.py` | Event time phase transitions |
| `test_event_workflow_status.py` | Event status auto-sync |
| `test_attendance_status_support.py` | Manual attendance status logic |
| `test_public_attendance.py` | Face scan public attendance endpoint |
| `test_event_geolocation_service.py` | Geofence per event |
| `test_geolocation.py` | Geolocation service |
| `test_governance_hierarchy_api.py` | SSG/SG/ORG scope enforcement (very large) |
| `test_face_recognition_schemas.py` | Face registration response schema |
| `test_attendance_schemas.py` | Attendance response null `student_id` |
| `test_auth_task_dispatcher.py` | Celery task dispatching |
| `test_models.py` | Database model integrity |
| `test_config.py` | Config loading |

### How to Run Them

```bash
# Run everything
docker compose exec backend python -m pytest

# Run one specific file
docker compose exec backend python -m pytest app/tests/test_api.py -v

# Run with coverage report
docker compose exec backend python -m pytest --cov=app --cov-report=html
```

---

## Step 4 — Write the Test Plan First

> **Rule:** Before running or writing tests, document the plan. This tells your team what you are doing and why.

### What I Did

1. Opened the existing `test-plan.md` — it was a basic shell with minimum detail
2. Rewrote and expanded it into 11 full sections:
   - System overview
   - Scope (in and out)
   - Test environments
   - Testing strategy (types and methods)
   - Requirement traceability matrix (FR-01 → FR-07)
   - Test execution commands
   - Entry and exit criteria
   - Defect workflow
   - Documentation maintenance rules

### Key Decisions Made in the Test Plan

- **Staging is TBD** — no staging URL exists yet. This is a risk.
- **UI testing is manual only** — no Playwright or automated browser tests exist yet.
- **Performance testing is basic** — only `tools/load_test.py`. Should be replaced with Locust.
- **SMS is out of scope** — FR-06.3 is a placeholder and should not be tested until implemented.

---

## Step 5 — Write the Test Cases

> **Rule:** Every test case must link to a requirement ID. If there is no requirement for it, question whether it should be tested.

### What I Did

1. Started with the existing 8 test cases in `test-cases.md` — they were a good base
2. Identified every functional requirement (FR-01 through FR-07) and checked if it had test coverage
3. Added 15 new test cases to cover:
   - Forced password change gate (TC-FR01-03)
   - Face-enrollment gate frontend redirect (TC-FR01-05)
   - Wrong password negative test (TC-FR01-04)
   - Onboarding email after import (TC-FR02-03)
   - Sign-out delay blocking (TC-FR03-03)
   - Incomplete attendance display status (TC-FR04-03)
   - Null student ID in face registration (TC-FR04-04)
   - Geofence out-of-range rejection (TC-FR04-05)
   - Upcoming event visibility for all students (TC-FR05-02)
   - Email after user creation (TC-FR06-01)
   - Celery fallback behavior (TC-FR06-02)
4. Added a **Gap Analysis table** at the bottom listing tests that still need to be written

### How I Decided What Was Missing

I compared each FR row against what test files existed. If a behavior was in the requirements but I could not find a corresponding test file or assertion — I flagged it as a gap.

---

## Step 6 — Log Every Bug You Find

> **Rule:** Every test failure gets a bug ID. No exceptions. You cannot mark a test as "failed" without a corresponding bug entry.

### What I Did

1. Reviewed `bug-reports.md` — it had 2 entries (BUG-001 and BUG-002)
2. Read `Backend/docs/BACKEND_CHANGELOG.md` — the changelog records every fix made since project start
3. Backfilled 4 more bugs from changelog entries that had fixes but no bug register entry:
   - BUG-003: Face registration 500 for null student ID
   - BUG-004: Attendance endpoint 500 for null student ID
   - BUG-005: Merge conflict markers crash the backend
   - BUG-006: CRLF script line endings break Docker on Windows
4. **Found 2 new bugs during this review:**
   - **BUG-007:** Live Git conflict markers are still in `BACKEND_CHANGELOG.md` (documentation bug)
   - **BUG-008:** FR-01.1 and FR-01.2 are word-for-word identical in `functional-requirements.md`

### The Bug Report Format

Every bug entry must have:
- A unique ID (BUG-001, BUG-002...)
- Severity (Critical / High / Medium / Low)
- Status (Open → In Progress → Resolved → Verified → Closed)
- Steps to reproduce
- Expected vs. actual result
- Root cause
- Fix summary
- Verification evidence

---

## Step 7 — Write the QA Assessment

> **Rule:** Summarize everything in one document so anyone can read the full picture without opening 10 files.

### What I Did

After completing Phases 1–6, I wrote `qa-assessment.md` which contains all 9 phases in one place:
- Phase 1: Project scan and system identification
- Phase 2: Feature understanding for each module
- Phase 3: Testing strategy overview
- Phase 4: Tool recommendations
- Phase 5: Test case summary table
- Phase 6: Bug log and risk analysis
- Phase 7: Documentation output
- Phase 8: Traceability matrix (requirement → test → bug)
- Phase 9: Improvement suggestions

---

## Step 8 — Traceability (Link Everything Together)

> **Rule:** You should be able to trace any requirement to at least one test case and any test failure to at least one bug ID.

### How Traceability Works in This Project

```
Requirement (functional-requirements.md)
    ↓
Test Case (test-cases.md)
    ↓
Automated or Manual Execution
    ↓ (if fails)
Bug Report (bug-reports.md)
    ↓ (when fixed)
Regression Test Re-run
    ↓
Changelog Entry (BACKEND_CHANGELOG.md)
```

### Traceability Quick Reference

| Requirement | Test Case | Bug (if any) |
|---|---|---|
| FR-01.1 Login | TC-FR01-01, TC-FR01-04 | — |
| FR-01.3 Password gate | TC-FR01-03 | — |
| FR-01.6 Inactive school | TC-FR01-02 | — |
| FR-02.3 Bulk import | TC-FR02-01 to TC-FR02-04 | — |
| FR-03.3 Attendance windows | TC-FR03-01, TC-FR03-03 | — |
| FR-04.2 Face recognition | TC-FR04-02, TC-FR04-04 | BUG-003 (resolved) |
| FR-04.3 Student records | TC-FR07-02 | BUG-004 (resolved) |
| FR-05.3 Governance scope | TC-FR05-01, TC-FR05-02 | — |
| FR-06.1 Email | TC-FR06-01, TC-FR06-02 | — |
| FR-07.2 Health | TC-FR07-01 | BUG-001 (resolved) |

---

## What Is Still Left to Do

> These are open items as of 2026-04-08. The next tester should pick up from here.

| Status | Item | Where |
|---|---|---|
| 🔴 Open | Fix BUG-007 — remove conflict markers from BACKEND_CHANGELOG.md | `Backend/docs/BACKEND_CHANGELOG.md` |
| 🔴 Open | Fix BUG-008 — clarify FR-01.2 requirement text | `docs/requirements/functional-requirements.md` |
| ⏳ Not Run | TC-FR02-04 — empty Excel file import test | Manual test + write automated version |
| ❌ Missing | Playwright tests for frontend route guards | New — `Frontend/tests/` |
| ❌ Missing | `pytest-cov` coverage report | Install + run against full test suite |
| ❌ Missing | Staging environment URL | Update test-plan.md Section 4 |
| ❌ Missing | Postman collection export | Save to `tools/postman_collection.json` |
| ❌ Missing | MkDocs setup | `mkdocs.yml` at project root |

---

## Tools Used in This QA Session

| Tool | Purpose | How to Get It |
|---|---|---|
| `pytest` | Run all automated backend tests | Already installed in Docker |
| `pytest --cov` | Coverage report | `pip install pytest-cov` |
| `Swagger UI` at `/docs` | Explore and manually test all API endpoints | Available at `http://localhost:8000/docs` |
| Markdown + Git | Write and version-control all QA docs | Already in use |
| Docker Compose | Spin up the full local test environment | Already configured |

### Recommended Tools to Add

| Tool | Purpose | Priority |
|---|---|---|
| **Playwright** | Automated browser/frontend testing | High |
| **Postman** | Shareable API test collections | Medium |
| **Locust** | Proper load testing with a dashboard | Medium |
| **MkDocs** | Convert `docs/` to a browsable site | Low |

---

## Advice for Future Testers

1. **Read the requirements first.** Do not start testing blind. Every test must link to a requirement.
2. **Check the changelog before testing.** `BACKEND_CHANGELOG.md` tells you what changed recently — this is where bugs hide.
3. **Run the full test suite before you change anything.** Know the baseline — how many tests pass before your change.
4. **Every failure gets a bug ID.** Do not leave a failing test without a matching entry in `bug-reports.md`.
5. **Update the docs when you find something.** If you discover a behavior that is not documented, document it.
6. **Ask before assuming.** If a requirement is unclear (like FR-01.2 in this project), ask the team before writing test cases for it.
7. **Test the edge cases.** The happy path almost always works. Test null values, empty inputs, expired tokens, and boundary conditions.

---

## File Index — Testing Folder

| File | Purpose |
|---|---|
| `test-plan.md` | Master testing strategy — scope, environments, criteria, commands |
| `test-cases.md` | All test cases with steps, expected results, and status |
| `bug-reports.md` | All discovered bugs with full details and status tracking |
| `qa-assessment.md` | Full 9-phase QA and documentation review |
| `tester-guide.md` | **This file** — personal and handoff guide, step by step |
