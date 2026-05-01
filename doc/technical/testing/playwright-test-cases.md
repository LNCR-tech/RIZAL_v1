# Playwright Test Cases

> **Status:** ACTIVE
> **Last Updated:** 2026-04-17
> **Author Role:** QA Tester / Documentation Specialist

See also: [qa-toolchain-workflow.md](./qa-toolchain-workflow.md) · [test-cases.md](./test-cases.md)

---

## Purpose

This file defines the recommended Playwright browser test scope for the current Vue frontend.

It is based on the actual app structure already present in:

- `Frontend/src/router/index.js`
- `Frontend/src/views/`
- `Frontend/src/components/navigation/`
- `Frontend/scripts/smoke.test.mjs`

Playwright is not yet installed in this repo, so this document serves as the implementation plan and test-case source of truth.

---

## Recommended Folder Layout

```text
Frontend/tests/e2e/
|-- auth.spec.ts
|-- route-guards.spec.ts
|-- admin-workspace.spec.ts
|-- student-dashboard.spec.ts
`-- sanctions.spec.ts
```

---

## Playwright Test Case Register

## UI-PLW-01: Login with valid credentials redirects to the correct landing page

| Field | Value |
|---|---|
| Area | Authentication |
| Priority | High |
| Preconditions | Valid account from seed logs |
| Steps | 1) Open login page 2) Enter credentials 3) Submit form |
| Expected Result | User lands on the correct role-based route |
| Suggested Spec File | `auth.spec.ts` |

---

## UI-PLW-02: Invalid credentials do not create a session

| Field | Value |
|---|---|
| Area | Authentication |
| Priority | High |
| Preconditions | Known valid email, wrong password |
| Steps | 1) Open login page 2) Submit wrong password |
| Expected Result | Error is shown and protected route is not accessible |
| Suggested Spec File | `auth.spec.ts` |

---

## UI-PLW-03: Student without face enrollment is redirected to face registration

| Field | Value |
|---|---|
| Area | Route Guard |
| Priority | High |
| Preconditions | Student account without face profile |
| Steps | 1) Log in as student 2) Try to open `/dashboard` |
| Expected Result | Router redirects to `/face-registration` |
| Suggested Spec File | `route-guards.spec.ts` |

---

## UI-PLW-04: Must-change-password user is blocked from protected routes

| Field | Value |
|---|---|
| Area | Route Guard |
| Priority | High |
| Preconditions | Account with `must_change_password = true` |
| Steps | 1) Log in 2) Try to open dashboard |
| Expected Result | User is forced to `/change-password` until password is updated |
| Suggested Spec File | `route-guards.spec.ts` |

---

## UI-PLW-05: Remember-me control is visible and persists login longer than default flow

| Field | Value |
|---|---|
| Area | Authentication |
| Priority | Medium |
| Preconditions | Valid account, backend supports `remember_me` |
| Steps | 1) Log in with remember-me enabled 2) Reload app 3) verify session survives expected short-flow boundary |
| Expected Result | Session remains active according to remembered-login behavior |
| Suggested Spec File | `auth.spec.ts` |

---

## UI-PLW-06: Privileged face verification route is available to pending privileged logins

| Field | Value |
|---|---|
| Area | Authentication / MFA |
| Priority | High |
| Preconditions | `admin` or `campus_admin` account with face verification enabled |
| Steps | 1) Log in with privileged account 2) Observe pending face verification flow |
| Expected Result | User is sent to the privileged face verification screen, not directly into the app |
| Suggested Spec File | `route-guards.spec.ts` |

---

## UI-PLW-07: Student sanctions navigation opens the sanctions dashboard

| Field | Value |
|---|---|
| Area | Student Dashboard |
| Priority | Medium |
| Preconditions | Authenticated student account |
| Steps | 1) Open student dashboard 2) Click sanctions navigation item |
| Expected Result | Route changes to the sanctions view without error |
| Suggested Spec File | `sanctions.spec.ts` |

---

## UI-PLW-08: Admin and workspace routes stay isolated by role

| Field | Value |
|---|---|
| Area | Authorization |
| Priority | High |
| Preconditions | Student account and admin account |
| Steps | 1) Log in as student 2) try to open `/admin` or workspace routes |
| Expected Result | Access is denied or redirected away from unauthorized area |
| Suggested Spec File | `admin-workspace.spec.ts` |

---

## UI-PLW-09: Profile configuration save action is available and completes successfully

| Field | Value |
|---|---|
| Area | Profile Settings |
| Priority | Medium |
| Preconditions | Authenticated account |
| Steps | 1) Open profile/settings view 2) change dark mode or font size 3) save configuration |
| Expected Result | Save action succeeds and state remains consistent after reload |
| Suggested Spec File | `student-dashboard.spec.ts` |

---

## Selector Guidance

To make Playwright stable, prefer adding:

- `data-testid="login-submit"`
- `data-testid="remember-me-toggle"`
- `data-testid="student-nav-sanctions"`
- `data-testid="profile-save-config"`

Avoid relying only on:

- deeply nested CSS selectors
- fragile text that changes often
- animation timing without explicit waits

---

## Minimal Playwright Example

```ts
import { test, expect } from '@playwright/test'

test('student without face enrollment is redirected to face registration', async ({ page }) => {
  await page.goto('/login')
  await page.getByLabel('Email').fill('student@example.com')
  await page.getByLabel('Password').fill('secret')
  await page.getByRole('button', { name: /log in/i }).click()

  await expect(page).toHaveURL(/face-registration/)
})
```

---

## Failure Evidence Checklist

When a Playwright test fails, capture:

- failing test name
- URL at failure time
- screenshot
- trace zip
- network error or console error summary

That evidence should then be linked in `bug-reports.md` or the corresponding GitHub Issue.
