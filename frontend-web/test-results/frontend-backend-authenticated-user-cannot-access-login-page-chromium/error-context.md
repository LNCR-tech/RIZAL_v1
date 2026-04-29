# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: frontend-backend.spec.js >> authenticated user cannot access login page
- Location: e2e\frontend-backend.spec.js:41:1

# Error details

```
Error: expect(page).not.toHaveURL(expected) failed

Expected: not "http://localhost:5173/"
Received: "http://localhost:5173/"
Timeout:  8000ms

Call log:
  - Expect "not toHaveURL" with timeout 8000ms
    12 × unexpected value "http://localhost:5173/"

```

# Page snapshot

```yaml
- generic [ref=e5]:
  - banner [ref=e6]:
    - img "Aura" [ref=e7]
  - main [ref=e8]:
    - generic [ref=e9]:
      - heading "Log In." [level=1] [ref=e10]
      - generic [ref=e11]:
        - generic [ref=e12]:
          - generic [ref=e13]: Gmail
          - textbox "Gmail" [ref=e14]
        - generic [ref=e15]:
          - generic [ref=e16]: Password
          - textbox "Password Show password" [ref=e17]:
            - /placeholder: Password
          - button "Show password" [ref=e18]:
            - img [ref=e19]
        - button "Log In" [ref=e22]
        - link "Forgot password?" [ref=e24] [cursor=pointer]:
          - /url: "#"
    - link "Learn more about Aura Project" [ref=e26] [cursor=pointer]:
      - /url: "#"
```

# Test source

```ts
  1  | // @ts-check
  2  | import { test, expect } from '@playwright/test'
  3  | 
  4  | const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL || 'campus_admin@test.com'
  5  | const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD || 'TestPass123!'
  6  | 
  7  | /** @param {import('@playwright/test').Page} page @param {string} email @param {string} password */
  8  | async function login(page, email, password) {
  9  |   await page.goto('/')
  10 |   await page.waitForSelector('#email', { timeout: 15000 })
  11 |   await page.fill('#email', email)
  12 |   await page.fill('#password', password)
  13 |   await page.click('button[type="submit"]')
  14 | }
  15 | 
  16 | // ---------------------------------------------------------------------------
  17 | // Frontend → Backend: Auth contract
  18 | // ---------------------------------------------------------------------------
  19 | 
  20 | test('login page renders', async ({ page }) => {
  21 |   await page.goto('/')
  22 |   await expect(page.locator('#email')).toBeVisible({ timeout: 15000 })
  23 |   await expect(page.locator('#password')).toBeVisible()
  24 |   await expect(page.getByRole('button', { name: 'Log In' })).toBeVisible()
  25 | })
  26 | 
  27 | test('wrong password shows error message', async ({ page }) => {
  28 |   await page.goto('/')
  29 |   await page.waitForSelector('#email', { timeout: 15000 })
  30 |   await page.fill('#email', ADMIN_EMAIL)
  31 |   await page.fill('#password', 'wrongpassword')
  32 |   await page.click('button[type="submit"]')
  33 |   await expect(page.locator('.mobile-login__message')).toBeVisible({ timeout: 8000 })
  34 | })
  35 | 
  36 | test('valid login redirects to dashboard', async ({ page }) => {
  37 |   await login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
  38 |   await expect(page).not.toHaveURL('/', { timeout: 10000 })
  39 | })
  40 | 
  41 | test('authenticated user cannot access login page', async ({ page }) => {
  42 |   await login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
  43 |   const dashboardUrl = page.url()
  44 |   await page.goto('/')
> 45 |   await expect(page).not.toHaveURL('/', { timeout: 8000 })
     |                          ^ Error: expect(page).not.toHaveURL(expected) failed
  46 |   await expect(page).toHaveURL(dashboardUrl, { timeout: 8000 })
  47 | })
  48 | 
  49 | test('unauthenticated user is redirected to login from protected route', async ({ page }) => {
  50 |   await page.goto('/dashboard')
  51 |   await expect(page).toHaveURL('/', { timeout: 8000 })
  52 | })
  53 | 
```