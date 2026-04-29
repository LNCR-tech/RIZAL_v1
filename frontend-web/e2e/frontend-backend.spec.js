// @ts-check
import { test, expect } from '@playwright/test'

const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL || 'campus_admin@test.com'
const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD || 'TestPass123!'

/** @param {import('@playwright/test').Page} page @param {string} email @param {string} password */
async function login(page, email, password) {
  await page.goto('/')
  await page.waitForSelector('#email', { timeout: 15000 })
  await page.fill('#email', email)
  await page.fill('#password', password)
  await page.click('button[type="submit"]')
}

// ---------------------------------------------------------------------------
// Frontend → Backend: Auth contract
// ---------------------------------------------------------------------------

test('login page renders', async ({ page }) => {
  await page.goto('/')
  await expect(page.locator('#email')).toBeVisible({ timeout: 15000 })
  await expect(page.locator('#password')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Log In' })).toBeVisible()
})

test('wrong password shows error message', async ({ page }) => {
  await page.goto('/')
  await page.waitForSelector('#email', { timeout: 15000 })
  await page.fill('#email', ADMIN_EMAIL)
  await page.fill('#password', 'wrongpassword')
  await page.click('button[type="submit"]')
  await expect(page.locator('p.text-red-500')).toBeVisible({ timeout: 8000 })
})

test('valid login redirects to dashboard', async ({ page }) => {
  await login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
  await expect(page).not.toHaveURL('/', { timeout: 10000 })
})

test('unauthenticated user is redirected to login from protected route', async ({ page }) => {
  await page.goto('/dashboard')
  await expect(page).toHaveURL('/', { timeout: 8000 })
})
