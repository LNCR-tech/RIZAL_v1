# Tool Usage Guide

> **Status:** ACTIVE
> **Last Updated:** 2026-04-17
> **Author Role:** QA Tester / Documentation Specialist

See also: [qa-toolchain-workflow.md](./qa-toolchain-workflow.md) · [api-smoke.http](./api-smoke.http) · [playwright-test-cases.md](./playwright-test-cases.md) · [bug-reports.md](./bug-reports.md) · [qodana-error-reference.md](./qodana-error-reference.md)

---

## Purpose

This guide explains how to use the QA toolchain in this project inside IntelliJ IDEA:

- `api-smoke.http`
- IntelliJ HTTP Client
- Playwright
- GitHub Issues
- Qodana
- testing documentation files in `doc/technical/testing/`

This is written as a step-by-step working guide, not a theory summary.

---

## 1. How to Use `api-smoke.http`

### File location

- [api-smoke.http](C:/Users/gabri/OneDrive/Desktop/MOBILE/AURAV3/doc/technical/testing/api-smoke.http)

### What this file does

This file is a ready-to-run API smoke suite for IntelliJ HTTP Client. It currently checks:

1. `GET /health`
2. `POST /login`
3. `GET /api/users/preferences/me`
4. `PUT /api/users/preferences/me`
5. one unauthorized request to confirm access control

### Before you run it

Make sure:

1. the backend is running on `http://localhost:8000`
2. you have valid test credentials from seed logs or local test accounts
3. the API routes exist in the current branch

### Fastest way to use it

Open [api-smoke.http](C:/Users/gabri/OneDrive/Desktop/MOBILE/AURAV3/doc/technical/testing/api-smoke.http) and update these top variables:

```http
@baseUrl = http://localhost:8000
@adminEmail = admin@example.com
@adminPassword = change-me
@studentEmail = student@example.com
@studentPassword = change-me
```

Then:

1. click the green run icon beside a request
2. start with `Health check`
3. run `Login with JSON body`
4. run the authenticated preferences requests after login

### How token handling works in this file

The login request contains this response script:

```js
if (response.body && response.body.access_token) {
  client.global.set("accessToken", response.body.access_token);
}
```

That means:

- after a successful login
- IntelliJ stores the token as a global variable
- later requests reuse it in:

```http
Authorization: Bearer {{accessToken}}
```

### What the test blocks mean

Example:

```http
> {%
client.test("Health returns 200", function () {
  client.assert(response.status === 200, "Expected HTTP 200 from /health");
});
%}
```

This means:

- IntelliJ runs the request
- then runs the JavaScript test block
- if the assertion fails, the request is marked as failed

### Common problems

| Problem | Likely Cause | Fix |
|---|---|---|
| `Connection refused` | Backend is not running | Start backend first |
| `401` on authenticated request | Login did not succeed or token was not stored | Re-run login and verify `access_token` exists |
| `404` | Route path changed | Check backend route definitions |
| `422` | Request body shape is wrong | Compare payload with backend schema |
| `500` | Server-side bug | Check backend logs and create a bug report if reproducible |

---

## 2. How to Use IntelliJ HTTP Client

### Menu options from IntelliJ

From the menu shown in your screenshot:

- `Create Request in HTTP Client`
- `Open HTTP Requests Collection`
- `Show HTTP Requests History`
- `Convert cURL to HTTP Request`
- `Add to HTTP Client...`
- `Import from Postman Collection File`

### What each option is for

| Menu Item | Use It For |
|---|---|
| `Create Request in HTTP Client` | Create a new `.http` request file from scratch |
| `Open HTTP Requests Collection` | Open JetBrains sample requests/examples |
| `Show HTTP Requests History` | Re-run previous requests and inspect responses |
| `Convert cURL to HTTP Request` | Turn a terminal `curl` command into `.http` format |
| `Add to HTTP Client...` | Add selected request details into an HTTP Client file |
| `Import from Postman Collection File` | Convert Postman collection JSON into `.http` requests |

### Recommended workflow for this project

1. keep reusable requests in `doc/technical/testing/*.http`
2. keep public values in an environment file
3. keep secrets and passwords in a private environment file
4. use response scripts for status checks and token capture
5. use request history only as temporary evidence, not as source of truth

### Environment files

JetBrains HTTP Client supports:

- `http-client.env.json`
- `http-client.private.env.json`

I added example files here:

- [http-client.env.json.example](C:/Users/gabri/OneDrive/Desktop/MOBILE/AURAV3/doc/technical/testing/http-client.env.json.example)
- [http-client.private.env.json.example](C:/Users/gabri/OneDrive/Desktop/MOBILE/AURAV3/doc/technical/testing/http-client.private.env.json.example)

Use them when you want cleaner environment switching instead of editing variables inside `.http` files.

### Example environment usage

If your `.http` file contains:

```http
GET {{baseUrl}}/health
```

and your environment file contains:

```json
{
  "local": {
    "baseUrl": "http://localhost:8000"
  }
}
```

then IntelliJ substitutes `{{baseUrl}}` with that value when you run the request with the `local` environment selected.

### Recommended HTTP Client use cases

- smoke testing after a backend change
- quick regression of login/auth flows
- checking a new endpoint before writing automated tests
- reproducing a bug with fixed payloads
- turning a Swagger or cURL sample into a reusable test request

---

## 3. How to Use Playwright

### Current repo status

Playwright is not installed yet in this repository.

Current frontend automation:

- [smoke.test.mjs](C:/Users/gabri/OneDrive/Desktop/MOBILE/AURAV3/Frontend/scripts/smoke.test.mjs)

That file checks source wiring, but it is not a real browser E2E suite.

### When to use Playwright

Use Playwright for:

- login flows
- redirects after login
- route guards
- remember-me behavior
- dashboard navigation
- sanctions/settings/profile flows

### Recommended install path

Because the frontend uses `npm`, install Playwright under `Frontend/`.

Typical setup flow:

```bash
cd Frontend
npm init playwright@latest
```

Recommended folder target:

```text
Frontend/tests/e2e/
```

### How to run Playwright after installation

```bash
cd Frontend
npx playwright test
npx playwright test --ui
npx playwright test --headed
npx playwright show-report
```

### Good beginner workflow

1. write one login test first
2. run it in headed mode
3. fix selectors until stable
4. save traces/screenshots on failure
5. only then expand to route guards and dashboard flows

### What to automate first in this project

1. student login
2. forced password change redirect
3. face registration redirect
4. privileged face verification route
5. admin/student route isolation

Detailed browser test list:

- [playwright-test-cases.md](C:/Users/gabri/OneDrive/Desktop/MOBILE/AURAV3/doc/technical/testing/playwright-test-cases.md)

### Beginner advice

Do not start with long multi-page end-to-end flows. Start with:

- one page
- one action
- one assertion

Then grow the suite gradually.

---

## 4. How to Use GitHub Issues

### When to create an issue

Create a GitHub Issue when the problem is:

- reproducible
- confirmed
- worth tracking to completion

Do not create an issue for:

- a typo you already fixed locally and verified
- one-time environment mistakes
- duplicate bugs already logged

### Recommended issue workflow

1. reproduce the bug
2. gather evidence
3. identify affected area and severity
4. create GitHub Issue
5. link it in [bug-reports.md](C:/Users/gabri/OneDrive/Desktop/MOBILE/AURAV3/doc/technical/testing/bug-reports.md)
6. retest after fix

### Evidence to attach

- screenshot
- terminal error
- backend log snippet
- failing HTTP request
- Playwright trace or video

### Severity guide

| Severity | Meaning |
|---|---|
| Critical | Security issue, data loss, startup failure, unrecoverable crash |
| High | Core feature broken, no usable workaround |
| Medium | Partial break, workaround exists |
| Low | Cosmetic or documentation issue |

### Ready-to-use repository form

I added a GitHub Issue form here:

- [.github/ISSUE_TEMPLATE/bug-report.yml](C:/Users/gabri/OneDrive/Desktop/MOBILE/AURAV3/.github/ISSUE_TEMPLATE/bug-report.yml)

and the chooser config here:

- [.github/ISSUE_TEMPLATE/config.yml](C:/Users/gabri/OneDrive/Desktop/MOBILE/AURAV3/.github/ISSUE_TEMPLATE/config.yml)

These make GitHub collect structured bug information instead of free-form issue text.

---

## 5. How to Use Qodana

### Config file

- [qodana.yaml](C:/Users/gabri/OneDrive/Desktop/MOBILE/AURAV3/qodana.yaml)
- [qodana-error-reference.md](C:/Users/gabri/OneDrive/Desktop/MOBILE/AURAV3/doc/technical/testing/qodana-error-reference.md)

### What Qodana is for

Use Qodana before browser or manual testing to catch:

- invalid imports
- wrong argument usage
- missing Vue component imports
- dead code
- vulnerable dependencies

### Basic workflow

1. run Qodana
2. review the report
3. classify findings by severity
4. fix clear correctness issues first
5. retest affected APIs/UI flows after fixes

### Interpreting results

- `red` or failed run does not automatically mean the app is broken
- it means the scan found something serious enough to fail the quality gate or the config/setup failed

### Best use in QA

Treat Qodana as:

- an early-warning tool
- a regression guard
- a source of likely bug candidates

not as final proof that a feature is working

---

## 6. How to Use the QA Docs Folder

### Main files

| File | Purpose |
|---|---|
| [test-plan.md](C:/Users/gabri/OneDrive/Desktop/MOBILE/AURAV3/doc/technical/testing/test-plan.md) | overall strategy and release criteria |
| [test-cases.md](C:/Users/gabri/OneDrive/Desktop/MOBILE/AURAV3/doc/technical/testing/test-cases.md) | requirement-linked test cases |
| [bug-reports.md](C:/Users/gabri/OneDrive/Desktop/MOBILE/AURAV3/doc/technical/testing/bug-reports.md) | defect register |
| [qa-toolchain-workflow.md](C:/Users/gabri/OneDrive/Desktop/MOBILE/AURAV3/doc/technical/testing/qa-toolchain-workflow.md) | toolchain process flow |
| [tool-usage-guide.md](C:/Users/gabri/OneDrive/Desktop/MOBILE/AURAV3/doc/technical/testing/tool-usage-guide.md) | this file |

### Rule for updates

When a test fails:

1. update test result
2. create or link bug
3. attach evidence
4. retest after fix

That keeps requirement -> test -> bug -> verification traceability intact.

---

## 7. Suggested Beginner Workflow for This Project

1. Run Qodana and note serious findings.
2. Open [api-smoke.http](C:/Users/gabri/OneDrive/Desktop/MOBILE/AURAV3/doc/technical/testing/api-smoke.http) in IntelliJ and run smoke checks.
3. If an API request fails, log it in `bug-reports.md` and GitHub Issues.
4. Once Playwright is installed, automate the repeated browser checks.
5. Update the testing docs after every confirmed result.

---

## References

Official docs used for this guide:

- JetBrains HTTP Client: https://www.jetbrains.com/help/idea/http-client-variables.html
- JetBrains HTTP Client CLI and test scripts: https://www.jetbrains.com/help/idea/http-client-cli.html
- JetBrains HTTP Client overview: https://www.jetbrains.com/pages/intellij-idea-http-client
- Qodana overview: https://www.jetbrains.com/help/qodana/about-qodana.html
- Qodana local/CLI deployment: https://www.jetbrains.com/help/qodana/deploy-qodana.html
- Playwright installation: https://playwright.dev/docs/intro
- Playwright running tests: https://playwright.dev/docs/running-tests
- GitHub issue templates and forms: https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/configuring-issue-templates-for-your-repository
