# VALID8 — Full QA + Documentation Assessment

> **Role:** Senior QA Engineer & Documentation Specialist
> **Date:** 2026-04-08
> **Project:** VALID8 — Student Attendance Recognition System
> **Status:** System is IN PROGRESS / Near Completion
>
> See also: [test-plan.md](./test-plan.md) · [test-cases.md](./test-cases.md) · [bug-reports.md](./bug-reports.md)

---

## Phase 1 — Project Scan

### What Type of System Is This?

VALID8 is a **full-stack SaaS web application** with:

- A **Vue 3 + Vite** single-page frontend (also wrapped with Capacitor for mobile)
- A **FastAPI (Python)** REST API backend
- **PostgreSQL** as the primary database (Alembic migrations)
- **Redis + Celery** for async task queue (email dispatch)
- **Docker Compose** for both development and production deployments
- **Google Gmail API** (OAuth2) as the sole email transport
- **InsightFace + ONNX Runtime** for face-recognition attendance
- **Railway** as the cloud deployment target

### Current Progress Level

**Near completion (~75–80%).** Core features are built and passing automated tests. What remains:

- Stabilizing mobile-responsive UI
- AI/anomaly detection features (marked In Progress)
- SMS notifications (placeholder only)
- A staging environment (TBD)
- Resolving two documentation-level bugs found during this review

### Main Modules Detected

| Module | Location |
|---|---|
| Authentication / Session | `Backend/app/routers/auth.py`, `services/auth_session.py` |
| User Management | `Backend/app/routers/users/` (package — 5 submodules) |
| Student Bulk Import | `Backend/app/routers/admin_import.py`, `services/student_import_service.py` |
| Event Management | `Backend/app/routers/events/` (package — 5 submodules) |
| Attendance (Manual + Face) | `Backend/app/routers/attendance/` + `services/attendance_face_scan.py` |
| Governance Hierarchy | `Backend/app/routers/governance_hierarchy.py`, `services/governance_hierarchy_service/` |
| Notifications (Email) | `Backend/app/services/email_service/` (package), `notification_center_service.py` |
| Reports and Audit | `Backend/app/routers/audit_logs.py`, `routers/school.py` |
| Health / Infra | `Backend/app/routers/health.py`, Alembic migrations |
| Frontend (SPA) | `Frontend/src/views/dashboard/` (30 Vue components), `router/index.js` |

---

## Phase 2 — Feature Understanding

### Feature 1: Authentication and Session Management

**What it does:** Users log in with email + password. If MFA is enabled, an email code is required. Users flagged `must_change_password = true` are blocked from accessing the app until they change their password. Sessions are tracked and can be individually revoked. Inactive schools are auto-blocked.

**Expected behavior:** Login → token issued → role-based dashboard redirect. Invalid credentials = no token.

**Missing/unclear:** FR-01.1 and FR-01.2 are listed with identical text in `functional-requirements.md`. One of them likely covers token/session maintenance — needs clarification. *(See BUG-008)*

---

### Feature 2: Student Bulk Import (Preview-First)

**What it does:** Campus Admins upload an Excel file of students. A **preview step** must be completed first — it reports conflicts and invalid rows. Only after the admin approves the preview is the actual import allowed. After import, onboarding credential emails are sent to each student.

**Expected behavior:** Upload → preview → resolve conflicts → approve → import → Celery queues emails → Gmail API delivers.

**Missing/unclear:** No automated test exists for the edge case of an empty Excel file.

---

### Feature 3: Event Management

**What it does:** Authorized roles create events with name, location, schedule, and scoping (campus-wide, department, or program). Events support custom check-in and sign-out windows including a configurable sign-out delay. A background scheduler auto-transitions event status (upcoming → ongoing → completed).

**Expected behavior:** Create event → status auto-syncs → attendance windows open and close as configured.

**Missing:** No dedicated end-to-end UI test covering event creation through the frontend form.

---

### Feature 4: Attendance (Manual + Face Recognition)

**What it does:** Officers manually record time-in/out, OR students scan their face at an attendance station. A two-phase model (sign-in → `incomplete` → sign-out → `present` or `late`) ensures only fully completed attendance is counted as valid. Geofencing can enforce location. In-app notifications are sent upon successful sign-in and sign-out.

**Expected behavior:** Face scan → match → phase-aware status → attendance record → in-app notification.

**Missing:** AI-enhanced anomaly detection is listed as In Progress but has no test coverage yet.

---

### Feature 5: Governance Hierarchy (SSG → SG → ORG)

**What it does:** Three governance levels: SSG (campus-wide), SG (department-level), ORG (program-level). Each unit has officers with specific permissions. Events and attendance are scoped per unit so officers can only act on their own students.

**Expected behavior:** SG officer can only record attendance for their department's students. Out-of-scope attempts are denied.

**Missing:** No UI-level test covering SG-specific dashboard views.

---

### Feature 6: Email Notifications

**What it does:** Transactional emails sent for: student onboarding, password reset, MFA codes, missed events, and attendance notifications. All emails use Gmail API only (SMTP removed). Celery handles async dispatch; if Celery is unavailable, an inline fallback sends the email synchronously.

**Expected behavior:** Event occurs → Celery task published → Gmail API sends → `email_delivery_logs` records `status=sent`.

**Missing:** SMS notifications (FR-06.3) is a placeholder only — not yet implemented.

---

### Feature 7: Reporting, Audit, and Health

**What it does:** Per-student and per-event attendance reports. Non-editable school audit log. A `/health` endpoint exposes service status and DB pool info.

**Expected behavior:** Reports accurately reflect attendance data including incomplete attendances. Health endpoint returns `200` with pool status.

---

## Phase 3 — Testing Strategy

### What Should Be Tested

| Layer | What to Test |
|---|---|
| **API (Backend)** | Every endpoint: status codes, response schemas, auth guards, business rules |
| **Database** | Schema integrity, null handling, migration idempotency |
| **Frontend Routes** | Role-based guards; face-enrollment gate; password-change gate |
| **Email Delivery** | Gmail API transport, Celery dispatch, inline fallback |
| **Governance Scoping** | Cross-department/program boundary enforcement |
| **Import Flow** | Preview token enforcement, conflict detection, empty file edge case |
| **Face Scan** | Phase timing, geofence, bypass accounts, null student ID edge case |

### Types of Testing Applied

| Type | Status |
|---|---|
| Functional Testing | ✅ Covered via automated pytest (21 test files) |
| Integration Testing | ✅ Import → Email → Celery → delivery log chains covered |
| Regression Testing | ✅ Run after every backend change (per AGENTS.md rule) |
| Edge Case Testing | ✅ Null student ID, sign-out delay, empty imports |
| Negative Testing | ✅ Wrong credentials, duplicate attendance, out-of-scope actions |
| UI/UX Testing | ⚠️ Manual only — no automated browser tests |
| Performance Testing | ⚠️ Basic only via `tools/load_test.py` |
| Security Testing | ⚠️ Manual only — no dedicated security test suite |
| Mobile Testing | ❌ Not yet — Capacitor integration in progress |

---

## Phase 4 — Tool Recommendations

### Backend Testing

| Tool | Why Use It | Level |
|---|---|---|
| **pytest** *(already in use)* | Industry standard for Python APIs; fast, simple syntax | Beginner–Advanced |
| **pytest-cov** | Measures how much of your code is actually tested (coverage report) | Beginner |
| **Hypothesis** | Generates random inputs to find edge cases automatically | Intermediate |
| **Locust** | Better alternative to custom load_test.py — web dashboard, user simulation | Intermediate |

### Frontend / UI Testing

| Tool | Why Use It | Level |
|---|---|---|
| **Playwright** | Browser automation for Vue 3 apps — tests login, routing, role guards | Intermediate |
| **Vitest** | Vue 3-native unit testing (same config as Vite) | Beginner |
| **Vue Test Utils** | Official Vue 3 component testing library | Beginner |

### API Testing (Manual)

| Tool | Why Use It | Level |
|---|---|---|
| **Swagger UI** (`/docs`) *(already available)* | In-browser API exploration — no setup needed | Beginner |
| **Postman** | Save test collections, share with team, use environment variables | Beginner |
| **Insomnia** | Lighter-weight alternative to Postman | Beginner |

### Bug Tracking

| Tool | Why Use It | Level |
|---|---|---|
| **GitHub Issues** | Already in the Git ecosystem — link to commits and PRs | Beginner |
| **Linear** | Modern, fast — great for small teams | Beginner |
| **Jira** | Enterprise-grade — overkill for now but good to learn | Advanced |

### Documentation

| Tool | Why Use It | Level |
|---|---|---|
| **Markdown + Git** *(already in use)* | Version-controlled, always in sync with code | Beginner |
| **MkDocs + Material Theme** | Converts your docs into a beautiful static documentation site | Beginner |
| **Swagger / OpenAPI** | Auto-generated from FastAPI — live API docs always in sync | Beginner |
| **Mermaid** | Add diagrams (flowcharts, ERDs) directly in Markdown | Beginner |

---

## Phase 5 — Test Case Summary

> Full test cases with steps and evidence: [test-cases.md](./test-cases.md)

| TC ID | Area | Type | Status |
|---|---|---|---|
| TC-FR01-01 | Login — valid credentials | Automated | ✅ Passed |
| TC-FR01-02 | Login — inactive school blocked | Automated | ✅ Passed |
| TC-FR01-03 | Force password change gate | Manual | ✅ Passed |
| TC-FR01-04 | Login — wrong password (negative) | Automated | ✅ Passed |
| TC-FR01-05 | Face-enrollment gate redirect | Manual | ✅ Passed |
| TC-FR02-01 | Import preview shows conflicts | Automated | ✅ Passed |
| TC-FR02-02 | Import blocked without preview token | Automated | ✅ Passed |
| TC-FR02-03 | Onboarding email sent after import | Automated + Manual | ✅ Passed |
| TC-FR02-04 | Import with empty Excel file | Manual | ⏳ NOT RUN |
| TC-FR03-01 | Event default attendance windows | Automated | ✅ Passed |
| TC-FR03-02 | Event workflow status auto-sync | Automated | ✅ Passed |
| TC-FR03-03 | Sign-out delay rejects early sign-out | Automated | ✅ Passed |
| TC-FR04-01 | Duplicate manual attendance blocked | Automated | ✅ Passed |
| TC-FR04-02 | Face scan sign-in/sign-out phases | Automated | ✅ Passed |
| TC-FR04-03 | Incomplete attendance display status | Automated | ✅ Passed |
| TC-FR04-04 | Null student ID — face registration | Automated | ✅ Passed |
| TC-FR04-05 | Out-of-range geofence rejection | Automated | ✅ Passed |
| TC-FR05-01 | Out-of-scope attendance denied | Automated | ✅ Passed |
| TC-FR05-02 | Upcoming events visible school-wide | Automated | ✅ Passed |
| TC-FR06-01 | Email sent after user creation | Automated | ✅ Passed |
| TC-FR06-02 | Celery failure triggers inline fallback | Automated | ✅ Passed |
| TC-FR07-01 | Health endpoint pool status | Automated | ✅ Passed |
| TC-FR07-02 | Attendance record null student ID safe | Automated | ✅ Passed |

---

## Phase 6 — Bug and Risk Analysis

### Bugs Found During This Review

| Bug ID | Title | Severity | Status |
|---|---|---|---|
| BUG-001 | Alembic migration fails without DATABASE_URL | High | Verified |
| BUG-002 | Queue pool overflow under concurrent login | High | Verified |
| BUG-003 | Face registration 500 for null `student_id` | High | Verified |
| BUG-004 | Attendance endpoint 500 for null `student_id` | High | Verified |
| BUG-005 | Merge conflict markers crash backend on startup | Critical | Verified |
| BUG-006 | CRLF shell scripts break Docker on Windows | High | Verified |
| **BUG-007** | **BACKEND_CHANGELOG.md has live conflict markers** | Low | **Open** |
| **BUG-008** | **FR-01.1 and FR-01.2 are identical in requirements** | Low | **Open** |

### Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Face scan fails on poor camera/lighting | High | High | Manual attendance fallback exists |
| Token expiry not handled on frontend | Medium | Medium | Test session expiry behavior manually |
| Large import file (1000+ rows) blocks request | Medium | High | Celery async used — verify timeout config |
| Geofence accuracy on mobile browsers | Medium | Medium | Test GPS on physical devices |
| SMS placeholder never implemented | High | Medium | Documented as out-of-scope |
| AI anomaly detection scope creep | High | High | Enforce scope per project-summary.md |
| Cross-role UI guard bypass via direct URL | Low | High | Router navigation guard covers this — verify with Playwright |
| Missing staging environment | High | Medium | Define staging URL before production release |

---

## Phase 7 — Documentation Output

| File | Status |
|---|---|
| `docs/technical/testing/test-plan.md` | ✅ Major revision — 11 sections, full traceability |
| `docs/technical/testing/test-cases.md` | ✅ Major revision — 23 test cases + gap analysis |
| `docs/technical/testing/bug-reports.md` | ✅ Major revision — 8 bugs, 2 new findings |
| `docs/technical/testing/qa-assessment.md` | ✅ This file — full QA review |
| `docs/technical/testing/tester-guide.md` | ✅ Personal and handoff guide for testers |

---

## Phase 8 — Traceability Matrix

| Requirement | Test Case(s) | Expected Result | Linked Bug |
|---|---|---|---|
| FR-01.1 Login with email/password | TC-FR01-01, TC-FR01-04 | 200 + token / 401 for wrong password | — |
| FR-01.2 (Duplicate — needs clarification) | TC-FR01-01 | Needs clarification | BUG-008 |
| FR-01.3 Must-change-password gate | TC-FR01-03 | Redirect to `/change-password` | — |
| FR-01.6 Inactive school blocked | TC-FR01-02 | Session denied | — |
| FR-02.3 Bulk import preview-first | TC-FR02-01, TC-FR02-02, TC-FR02-04 | Conflicts flagged; token enforced | — |
| FR-03.3 Attendance windows | TC-FR03-01, TC-FR03-03 | Defaults applied; delay enforced | — |
| FR-03.5 Auto event status | TC-FR03-02 | Correct status transitions | — |
| FR-04.1 Manual attendance | TC-FR04-01 | No duplicate records | — |
| FR-04.2 Face recognition | TC-FR04-02, TC-FR04-04 | Phase-aware; null ID safe | BUG-003 (resolved) |
| FR-04.3 Student attendance access | TC-FR07-02 | Null student ID returns safely | BUG-004 (resolved) |
| FR-05.3 Governance scoping | TC-FR05-01, TC-FR05-02 | Out-of-scope denied; upcoming visible | — |
| FR-06.1 Email notifications | TC-FR06-01, TC-FR06-02 | Sent or fallback sent | — |
| FR-07.2 Health and audit | TC-FR07-01 | 200 with pool status | BUG-001 (resolved) |

---

## Phase 9 — Improvement Suggestions

### Testing Process

1. Add `pytest-cov` — run `pytest --cov=app --cov-report=html` to find zero-coverage files
2. Add Playwright tests — automate the frontend login → role → dashboard flow
3. Write TC-FR02-04 — empty Excel file import automated test
4. Set up a staging environment before any production release
5. Integrate full pytest suite into GitHub Actions CI on every PR

### Documentation Quality

1. Fix BUG-007 — remove Git conflict markers from BACKEND_CHANGELOG.md
2. Fix BUG-008 — clarify FR-01.2 so it is distinct from FR-01.1
3. Expand the troubleshooting table in `user-guide/how-to-use.md`
4. Add Mermaid flow diagrams to the testing and architecture docs

### Tool Usage

1. Add `pytest-cov` to `requirements.txt` for coverage reporting
2. Export a Postman collection from Swagger UI and save it in `tools/`
3. Set up MkDocs to publish `docs/` as a browsable static site

### Team Workflow

1. Make it a team rule — `docker compose run --rm test_backend` must pass before any backend PR merge
2. Enforce the BACKEND_CHANGELOG.md update rule on every code review
3. Add a PR template checklist: tests run, changelog updated, test cases added, bug IDs linked

---

## Prioritized Action List

| Priority | Action | File |
|---|---|---|
| 🔴 High | Fix BUG-007 — remove conflict markers from BACKEND_CHANGELOG.md | `Backend/docs/BACKEND_CHANGELOG.md` |
| 🔴 High | Fix BUG-008 — clarify FR-01.2 requirement text | `docs/requirements/functional-requirements.md` |
| 🟡 Medium | Write TC-FR02-04 — empty Excel import edge case automated test | `Backend/app/tests/` |
| 🟡 Medium | Add `pytest-cov` and run a coverage report | `Backend/requirements.txt` |
| 🟡 Medium | Define staging environment URL | `test-plan.md` Section 4 |
| 🟢 Low | Set up Playwright for frontend route guard tests | `Frontend/tests/` |
| 🟢 Low | Set up MkDocs to publish `docs/` as a static site | Root `mkdocs.yml` |
| 🟢 Low | Export Postman collection from Swagger UI | `tools/postman_collection.json` |
