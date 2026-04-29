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
  // The pill is the Aura AI button in the side nav — click it to open mini chat
  const pill = page.locator('.nav-rail__shell').getByTitle('Open full chat').locator('..')
  // If pill is already open, just click expand; otherwise click pill first
  const expandBtn = page.locator('[aria-label="Expand chat to full window"]')
  if (!await expandBtn.isVisible()) {
    // Click the collapsed pill (the div containing the Aura logo + "Aura AI" text)
    await page.locator('.nav-rail__shell').locator('img[alt="Aura"]').first().click()
  }
  await expandBtn.click()
  await expect(page.locator('[aria-label="Talk with Aura"]')).toBeVisible({ timeout: 5000 })
}

// ---------------------------------------------------------------------------
// Frontend → Assistant: Chat contract
// ---------------------------------------------------------------------------

test('chat window opens when Aura button is clicked', async ({ page }) => {
  await login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
  await openChatWindow(page)
  await expect(page.locator('.chat-input')).toBeVisible()
})

test('chat input is interactive after window opens', async ({ page }) => {
  await login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
  await openChatWindow(page)

  const input = page.locator('.chat-input')
  await expect(input).toBeEnabled()
  await input.fill('hello')
  await expect(input).toHaveValue('hello')
})

test('sending a message shows user bubble and triggers assistant response', async ({ page }) => {
  await login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
  await openChatWindow(page)

  const input = page.locator('.chat-input')
  await input.fill('hello')
  await page.locator('[aria-label="Send message"]').click()

  await expect(page.locator('.bubble--user').last()).toContainText('hello', { timeout: 5000 })
  await expect(page.locator('.bubble--ai, .bubble--typing')).toBeVisible({ timeout: 15000 })
})

test('AI response bubble appears after message is sent', async ({ page }) => {
  await login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
  await openChatWindow(page)

  const input = page.locator('.chat-input')
  await input.fill('ping')
  await page.locator('[aria-label="Send message"]').click()

  await expect(page.locator('.bubble--ai:not(.bubble--typing)')).toBeVisible({ timeout: 20000 })
})

test('chat window closes when close button is clicked', async ({ page }) => {
  await login(page, ADMIN_EMAIL, ADMIN_PASSWORD)
  await openChatWindow(page)

  await page.locator('[aria-label="Close chat"]').click()
  await expect(page.locator('[aria-label="Talk with Aura"]')).not.toBeVisible({ timeout: 3000 })
})
