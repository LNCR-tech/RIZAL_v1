// @ts-check
import { test, expect } from '@playwright/test'

const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL || 'campus_admin@test.com'
const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD || 'TestPass123!'

/**
 * Helper: complete the login flow including the terms modal.
 * Sets aura_terms_agreed in localStorage before navigating so the
 * router proceeds immediately after the modal's "I Understand" click.
 */
/** @param {import('@playwright/test').Page} page @param {string} email @param {string} password */
async function login(page, email, password) {
  await page.goto('/', { waitUntil: 'domcontentloaded' })
  await page.waitForSelector('#email', { timeout: 15000 })
  await page.fill('#email', email)
  await page.fill('#password', password)
  await page.click('button[type="submit"]')

  // Terms modal appears — click I Understand (now correctly emits agree → router navigates)
  await page.getByRole('button', { name: 'I Understand' }).click()
}

// ---------------------------------------------------------------------------
// Frontend → Backend: Auth contract
// ---------------------------------------------------------------------------

test('login page renders', async ({ page }) => {
  await page.goto('/', { waitUntil: 'domcontentloaded' })
  await expect(page.locator('#email')).toBeVisible({ timeout: 15000 })
  await expect(page.locator('#password')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Log In' })).toBeVisible()
})

test('wrong password shows error message', async ({ page }) => {
  await page.goto('/', { waitUntil: 'domcontentloaded' })
  await page.waitForSelector('#email', { timeout: 15000 })
  await page.fill('#email', ADMIN_EMAIL)
  await page.fill('#password', 'wrongpassword')
  await page.click('button[type="submit"]')

  // Error message should appear — backend returned 401
  await expect(page.locator('p.text-red-500')).toBeVisible({ timeout: 8000 })
})

test('valid login redirects to dashboard', async ({ page }) => {
  await login(page, ADMIN_EMAIL, ADMIN_PASSWORD)

  // Should navigate away from login — URL no longer at root
  await expect(page).not.toHaveURL('/', { timeout: 10000 })
})

test('authenticated user cannot access login page', async ({ page }) => {
  await login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
  const dashboardUrl = page.url()

  // Try to go back to login
  await page.goto('/')

  // Should be redirected back to dashboard
  await expect(page).not.toHaveURL('/', { timeout: 8000 })
  await expect(page).toHaveURL(dashboardUrl, { timeout: 8000 })
})

test('unauthenticated user is redirected to login from protected route', async ({ page }) => {
  // Clear storage before any page load so the router sees no token
  await page.addInitScript(() => localStorage.clear())

  await page.goto('/dashboard')
  await expect(page).toHaveURL('/', { timeout: 8000 })
})
