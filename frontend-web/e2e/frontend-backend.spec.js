// @ts-check
/// <reference types="node" />
import { test, expect } from "./base";

const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL || "campus_admin@test.com";
const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD || "TestPass123!";
const AUTHENTICATED_PATH_PATTERN =
  /^\/(workspace|dashboard|admin|governance|privileged-face|face-registration|change-password)(?:\/|$)/i;

/**
 * @param {import("@playwright/test").Page} page
 * @param {RegExp} pattern
 * @param {number} [timeout]
 * @returns {Promise<void>}
 */
async function expectPathnameToMatch(page, pattern, timeout = 20_000) {
  await expect(page).toHaveURL((url) => pattern.test(url.pathname), { timeout });
}

/**
 * @param {import("@playwright/test").Page} page
 * @param {number} [timeout]
 * @returns {Promise<void>}
 */
async function waitForBootOverlayToClear(page, timeout = 15_000) {
  const locator = page.locator(".app-boot-screen").first();
  // Wait a tiny bit for it to potentially mount
  await page.waitForTimeout(100);
  if (await locator.isVisible()) {
    await locator.waitFor({ state: "hidden", timeout }).catch(() => null);
  }
}

/**
 * @typedef {Object} AuthSnapshot
 * @property {string} pathname
 * @property {string|null} localStorageToken
 * @property {string|null} sessionStorageToken
 * @property {string|null} authCookie
 * @property {string[]} localStorageKeys
 * @property {string[]} sessionStorageKeys
 */

/**
 * @param {import("@playwright/test").Page} page
 * @returns {Promise<AuthSnapshot>}
 */
async function readAuthStorageSnapshot(page) {
  return page.evaluate(() => {
    const localStorageToken = localStorage.getItem("aura_token");
    const sessionStorageToken =
      typeof sessionStorage !== "undefined"
        ? sessionStorage.getItem("aura_token")
        : null;
    const authCookie = document.cookie
      .split(";")
      .map((entry) => entry.trim())
      .find((entry) => /^aura_token=/.test(entry));

    return {
      pathname: window.location.pathname,
      localStorageToken,
      sessionStorageToken,
      authCookie: authCookie || null,
      localStorageKeys: Object.keys(localStorage || {}),
      sessionStorageKeys:
        typeof sessionStorage !== "undefined" ? Object.keys(sessionStorage) : [],
    };
  });
}

/**
 * @param {import("@playwright/test").Page} page
 * @returns {Promise<{token: string, snapshot: AuthSnapshot}>}
 */
async function readStoredToken(page) {
  const snapshot = await readAuthStorageSnapshot(page);
  const cookieToken = snapshot.authCookie
    ? decodeURIComponent(String(snapshot.authCookie).split("=").slice(1).join("="))
    : "";
  const resolvedToken =
    snapshot.localStorageToken || snapshot.sessionStorageToken || cookieToken || "";
  return { token: resolvedToken, snapshot };
}

/**
 * @param {import("@playwright/test").Page} page
 * @param {string} email
 * @param {string} password
 * @returns {Promise<void>}
 */
async function submitLogin(page, email, password) {
  await page.goto("/");
  await waitForBootOverlayToClear(page);
  await expect(page.locator("#email")).toBeVisible({ timeout: 20_000 });
  await page.fill("#email", email);
  await page.fill("#password", password);
  // Ensure no transition or splash covers the button before clicking
  await page.waitForTimeout(200);
  await waitForBootOverlayToClear(page);
  // Wait for the login request to complete
  const tokenPromise = page.waitForResponse(r => r.url().includes("/token") && r.request().method() === "POST", { timeout: 15_000 }).catch(() => null);
  await page.getByRole("button", { name: /log in|login|sign in/i }).click();
  await tokenPromise;
}

test("login page renders", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("#email")).toBeVisible({ timeout: 15000 });
  await expect(page.locator("#password")).toBeVisible();
  await expect(
    page.getByRole("button", { name: /log in|login|sign in/i }),
  ).toBeVisible();
});

test("wrong password shows error message", async ({ page }) => {
  await submitLogin(page, ADMIN_EMAIL, "wrongpassword");
  
  await expect(
    page.getByText(/invalid|incorrect|failed|error|credentials/i).first(),
  ).toBeVisible({ timeout: 15_000 });

  const { token } = await readStoredToken(page);
  expect(token).toBeFalsy();
});

test("valid login redirects to an authenticated route", async ({ page }) => {
  await submitLogin(page, ADMIN_EMAIL, ADMIN_PASSWORD);
  
  await expect
    .poll(
      async () => {
        const { token } = await readStoredToken(page);
        return Boolean(token);
      },
      { timeout: 20_000 }
    )
    .toBe(true);

  const tokenSnapshot = await readStoredToken(page);
  expect(tokenSnapshot.token, JSON.stringify(tokenSnapshot.snapshot, null, 2)).toBeTruthy();

  const termsAcknowledgeButton = page.getByRole("button", {
    name: /i understand/i,
  });
  if (
    await termsAcknowledgeButton
      .isVisible({ timeout: 5_000 })
      .catch(() => false)
  ) {
    await termsAcknowledgeButton.click();
  }

  await expectPathnameToMatch(page, AUTHENTICATED_PATH_PATTERN);
  await expect(page.locator("#email")).toHaveCount(0);
});

test("unauthenticated user is redirected to login from protected route", async ({ page }) => {
  await page.goto("/dashboard");
  await expect(page.locator("#email")).toBeVisible({ timeout: 10000 });
});
