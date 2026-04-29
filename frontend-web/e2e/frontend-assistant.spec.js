// @ts-check
import { test, expect } from '@playwright/test'

const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL || 'campus_admin@test.com'
const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD || 'TestPass123!'

/** @param {import('@playwright/test').Page} page @param {string} email @param {string} password */
async function login(page, email, password) {
  await page.addInitScript(() => localStorage.clear())
  await page.goto('/')
  
  const emailInput = page.locator('#email')
  try {
    await emailInput.waitFor({ state: 'visible', timeout: 15000 })
  } catch (e) {
    console.log('Page HTML when #email not found:', await page.content())
    console.log('Page URL:', page.url())
    throw e
  }
  
  await page.fill('#email', email)
  await page.fill('#password', password)
  await page.click('button[type="submit"]')
  await page.getByRole('button', { name: 'I Understand' }).click()
  await expect(page).not.toHaveURL('/', { timeout: 10000 })
}

// ---------------------------------------------------------------------------
// Frontend → Assistant: Chat contract
// ---------------------------------------------------------------------------

test('chat window opens when Aura button is clicked', async ({ page }) => {
  await login(page, ADMIN_EMAIL, ADMIN_PASSWORD)

  // Find and click the Aura chat trigger button
  await page.locator('[aria-label="Talk with Aura"]').waitFor({ state: 'hidden', timeout: 5000 }).catch(() => null)
  const chatTrigger = page.locator('button[aria-label*="Aura"], button[aria-label*="chat"], button[aria-label*="assistant"]').first()
  await chatTrigger.click()

  await expect(page.locator('[aria-label="Talk with Aura"]')).toBeVisible({ timeout: 5000 })
  await expect(page.locator('.chat-input')).toBeVisible()
})

test('chat input is interactive after window opens', async ({ page }) => {
  await login(page, ADMIN_EMAIL, ADMIN_PASSWORD)

  const chatTrigger = page.locator('button[aria-label*="Aura"], button[aria-label*="chat"], button[aria-label*="assistant"]').first()
  await chatTrigger.click()

  const input = page.locator('.chat-input')
  await expect(input).toBeVisible({ timeout: 5000 })
  await expect(input).toBeEnabled()

  await input.fill('hello')
  await expect(input).toHaveValue('hello')
})

test('sending a message shows user bubble and triggers assistant response', async ({ page }) => {
  await login(page, ADMIN_EMAIL, ADMIN_PASSWORD)

  const chatTrigger = page.locator('button[aria-label*="Aura"], button[aria-label*="chat"], button[aria-label*="assistant"]').first()
  await chatTrigger.click()

  const input = page.locator('.chat-input')
  await expect(input).toBeVisible({ timeout: 5000 })

  await input.fill('hello')
  await page.locator('[aria-label="Send message"]').click()

  // User bubble appears immediately
  await expect(page.locator('.bubble--user').last()).toContainText('hello', { timeout: 5000 })

  // Typing indicator or AI response appears (assistant is live)
  await expect(
    page.locator('.bubble--ai, .bubble--typing')
  ).toBeVisible({ timeout: 15000 })
})

test('AI response bubble appears after message is sent', async ({ page }) => {
  await login(page, ADMIN_EMAIL, ADMIN_PASSWORD)

  const chatTrigger = page.locator('button[aria-label*="Aura"], button[aria-label*="chat"], button[aria-label*="assistant"]').first()
  await chatTrigger.click()

  const input = page.locator('.chat-input')
  await expect(input).toBeVisible({ timeout: 5000 })

  await input.fill('ping')
  await page.locator('[aria-label="Send message"]').click()

  // Wait for a non-typing AI bubble (actual response)
  await expect(
    page.locator('.bubble--ai:not(.bubble--typing)')
  ).toBeVisible({ timeout: 20000 })
})

test('chat window closes when close button is clicked', async ({ page }) => {
  await login(page, ADMIN_EMAIL, ADMIN_PASSWORD)

  const chatTrigger = page.locator('button[aria-label*="Aura"], button[aria-label*="chat"], button[aria-label*="assistant"]').first()
  await chatTrigger.click()

  await expect(page.locator('[aria-label="Talk with Aura"]')).toBeVisible({ timeout: 5000 })

  await page.locator('[aria-label="Close chat"]').click()

  await expect(page.locator('[aria-label="Talk with Aura"]')).not.toBeVisible({ timeout: 3000 })
})
