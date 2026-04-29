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
  await expect(page).not.toHaveURL('/', { timeout: 10000 })
}

/** Opens the full AuraChatWindow from the desktop side nav pill */
/** @param {import('@playwright/test').Page} page */
async function openChatWindow(page) {
  // Click the collapsed pill to open mini chat first
  await page.locator('.nav-rail__shell').locator('img[alt="Aura"]').first().click()
  // Then click expand to full window
  await page.locator('[aria-label="Expand chat to full window"]').click()
  await expect(page.locator('[aria-label="Talk with Aura"]')).toBeVisible({ timeout: 5000 })
}

// ---------------------------------------------------------------------------
// Frontend → Assistant: Chat UI contract
// ---------------------------------------------------------------------------

test('chat window opens when Aura button is clicked', async ({ page }) => {
  await login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
  await openChatWindow(page)
  await expect(page.locator('.chat-input')).toBeVisible()
})

test('chat window shows under development notice', async ({ page }) => {
  await login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
  await openChatWindow(page)
  await expect(page.locator('.chat-disabled-note')).toBeVisible()
})

test('chat input is disabled when feature is under development', async ({ page }) => {
  await login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
  await openChatWindow(page)
  await expect(page.locator('.chat-input')).toBeDisabled()
})

test('chat window closes when close button is clicked', async ({ page }) => {
  await login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
  await openChatWindow(page)
  await page.locator('[aria-label="Close chat"]').click()
  await expect(page.locator('[aria-label="Talk with Aura"]')).not.toBeVisible({ timeout: 3000 })
})
