# QA Toolchain Workflow

> **Status:** ACTIVE
> **Last Updated:** 2026-04-17
> **Author Role:** QA Tester / Documentation Specialist

See also: [test-plan.md](./test-plan.md) · [test-cases.md](./test-cases.md) · [bug-reports.md](./bug-reports.md) · [playwright-test-cases.md](./playwright-test-cases.md) · [api-smoke.http](./api-smoke.http) · [tool-usage-guide.md](./tool-usage-guide.md)

---

## Purpose

This guide defines the practical QA workflow for this project using:

- `Qodana` for static analysis
- `Playwright` for frontend flow automation
- `IntelliJ HTTP Client` for API validation
- `GitHub Issues` for defect tracking
- Markdown files in `doc/technical/testing/` for documentation and traceability

This is a documentation-ready process guide, not just a theory note.

---

## Current Project State

| Tool | Current State | Notes |
|---|---|---|
| Qodana | Configured | Root config exists at `qodana.yaml` |
| Playwright | Not installed yet | Current frontend automation is `Frontend/scripts/smoke.test.mjs` |
| IntelliJ HTTP Client | Ready to use | This guide adds `api-smoke.http` |
| GitHub Issues | Recommended tracker | Use for reproducible bugs only |
| Markdown QA docs | Active | Existing docs already live in `doc/technical/testing/` |

---

## QA Workflow Order

1. Run `Qodana` first to catch static issues before manual or browser testing.
2. Run API smoke checks with IntelliJ HTTP Client.
3. Run automated UI flows with Playwright once installed.
4. Log confirmed defects in GitHub Issues.
5. Update `test-cases.md`, `bug-reports.md`, and related QA docs.

---

## 1. Qodana Workflow

### Config Source

- Root file: [qodana.yaml](C:/Users/gabri/OneDrive/Desktop/MOBILE/AURAV3/qodana.yaml)

### What Qodana Does

Qodana is a static analyzer. It reads source files and reports:

- likely bugs
- unsafe code patterns
- broken imports and references
- dead code
- vulnerable dependencies

It does **not** crash the application by itself. A failed run usually means:

1. the config is invalid, or
2. the scan found issues and the quality gate failed the run

### Practical Meaning of the Main Inspections

| Inspection | What It Means in QA Terms |
|---|---|
| `PyTypeChecker` | Code may pass the wrong type and fail at runtime |
| `PyUnresolvedReferences` | Import/name is missing; feature may break immediately |
| `PyArgumentList` | Function call shape is wrong; endpoint/service may throw |
| `PyCallingNonCallable` | Code is trying to call something that is not a function |
| `PyUnboundLocalVariable` | Variable may be used before assignment |
| `PyUnusedLocal` | Dead local code that increases maintenance risk |
| `VueMissingComponentImportInspection` | Vue page uses a component that was never imported |
| `JSIgnoredPromiseFromCall` | Async failure may be silently ignored |
| `ES6MissingAwait` | Async result probably not waited for; race condition risk |
| `JSFileReferences` | Import path or file reference is broken |

### Why Some Paths Are Excluded

| Excluded Path | Why It Is Excluded |
|---|---|
| `.git`, `.idea`, `.pytest_cache`, `.qodana`, `__pycache__` | Tool metadata and cache, not app source |
| `.env` | Sensitive local config |
| `qodana.sarif.json` | Generated report output |
| `doc`, `tempdocs`, `tempdocs2` | Documentation trees, not runtime code |
| `Backend/.venv`, `Frontend/node_modules` | Installed third-party dependencies |
| `Frontend/dist`, `Frontend/dist-ssr`, `Frontend/.vite` | Build output |
| `Frontend/android`, `Frontend/ios` | Generated native/mobile artifacts |
| `Backend/models/MiniFASNetV2.onnx` | Binary model file |
| `Backend/storage` | Runtime-generated files |
| `Backend/alembic/versions` | Migration history with high static-analysis noise |

### Qodana Triage Rule

When Qodana reports an issue, classify it as:

- `Critical`: security risk, crash risk, broken auth, broken data access
- `High`: core feature can fail in normal usage
- `Medium`: partial break or high-maintenance bad practice
- `Low`: cleanup, readability, or low-risk dead code

---

## 2. Playwright Workflow

### Current State

Playwright is not installed yet in this repo. The current frontend automation is:

- [smoke.test.mjs](C:/Users/gabri/OneDrive/Desktop/MOBILE/AURAV3/Frontend/scripts/smoke.test.mjs)

That file is useful for quick source-level smoke checks, but it is **not** a browser E2E suite.

### Recommended Playwright Coverage

Use Playwright for:

- login and redirect flows
- role-based route guards
- face-enrollment gates
- remember-me behavior
- admin/workspace/dashboard access isolation
- sanctions and settings navigation smoke

Detailed case list: [playwright-test-cases.md](./playwright-test-cases.md)

### Evidence Rule

Every failed Playwright run should preserve:

- screenshot
- trace
- failing URL
- console/network error note

---

## 3. IntelliJ HTTP Client Workflow

### Purpose

Use the IntelliJ HTTP Client for:

- quick API smoke tests
- authenticated endpoint checks
- regression checks after backend changes
- verifying status codes and basic response shapes

### Ready-to-Use File

- [api-smoke.http](C:/Users/gabri/OneDrive/Desktop/MOBILE/AURAV3/doc/technical/testing/api-smoke.http)

### Minimum API Smoke Set

1. `GET /health`
2. `POST /login`
3. `GET /api/users/preferences/me`
4. `PUT /api/users/preferences/me`
5. one unauthorized request to verify access control

---

## 4. GitHub Issues Workflow

### When to Create an Issue

Create a GitHub Issue only when the problem is:

- reproducible
- confirmed
- worth tracking beyond one local note

Do **not** create issues for:

- one-time environment mistakes
- unclear expected behavior not yet discussed with the team
- duplicate reports already logged

### GitHub Issue Format

```md
Title: [Module] Short defect summary

Environment:
- Branch:
- Commit:
- URL:
- Browser/OS:

Steps to Reproduce:
1.
2.
3.

Expected Result:

Actual Result:

Evidence:
- Screenshot:
- Trace:
- Logs:

Severity:
- Critical / High / Medium / Low

Notes:
- Requirement ID:
- Test Case ID:
- Related endpoint/file:
```

### Severity Rule

| Severity | Use When |
|---|---|
| Critical | Security, data loss, startup failure, unrecoverable crash |
| High | Core feature broken with no acceptable workaround |
| Medium | Partial break with workaround |
| Low | Cosmetic or low-risk documentation issue |

---

## 5. Documentation Workflow

### Files to Update After QA Work

| Trigger | Update Required |
|---|---|
| New test identified | `test-cases.md` |
| Confirmed bug found | `bug-reports.md` and GitHub Issue |
| Retest completed | Bug status in `bug-reports.md` |
| Tooling/process change | This file |
| New browser flow automation | `playwright-test-cases.md` |
| API smoke updates | `api-smoke.http` |

### Documentation Rule

A QA run is not complete until:

1. the result is recorded
2. the bug is linked if it failed
3. the evidence location is documented

---

## Recommended Next Steps

1. Install Playwright and create `Frontend/tests/e2e/`
2. Add GitHub Issue templates for bug reports
3. Add a PR checklist that requires Qodana, API smoke, and regression evidence
