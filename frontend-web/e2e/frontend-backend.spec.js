// @ts-check
import { test, expect } from "@playwright/test";

const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL || "campus_admin@test.com";
const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD || "TestPass123!";
const LOGIN_API_PATH_PATTERN = /\/(?:api\/)?token$/i;
const AUTH_ERROR_TEXT_PATTERN = /invalid|incorrect|failed|error|credentials/i;
const AUTHENTICATED_PATH_PATTERN =
  /^\/(workspace|dashboard|admin|governance|privileged|face-registration|change-password)(?:\/|$)/i;

/**
 * @typedef {{
 *   consoleErrors: string[];
 *   failedRequests: string[];
 *   loginApiResponses: string[];
 *   pendingReads: Promise<void>[];
 * }} AuthDiagnostics
 */

/**
 * @returns {AuthDiagnostics}
 */
function createAuthDiagnostics() {
  return {
    consoleErrors: [],
    failedRequests: [],
    loginApiResponses: [],
    pendingReads: [],
  };
}

/**
 * @param {string} value
 * @param {number} maxLen
 */
function truncate(value, maxLen = 400) {
  const normalized = String(value || "")
    .replace(/\s+/g, " ")
    .trim();
  if (normalized.length <= maxLen) return normalized;
  return `${normalized.slice(0, maxLen)}...`;
}

/**
 * @param {string} rawUrl
 */
function getPathname(rawUrl) {
  try {
    return new URL(rawUrl).pathname;
  } catch {
    return rawUrl;
  }
}

/**
 * @param {string} rawUrl
 */
function isLoginApiRequest(rawUrl) {
  return LOGIN_API_PATH_PATTERN.test(getPathname(rawUrl));
}

/**
 * @param {import("@playwright/test").Page} page
 * @param {AuthDiagnostics} diagnostics
 */
function attachAuthDiagnostics(page, diagnostics) {
  page.on("console", (message) => {
    if (message.type() !== "error") return;
    diagnostics.consoleErrors.push(truncate(message.text()));
  });

  page.on("requestfailed", (request) => {
    const item = `${request.method()} ${request.url()} :: ${request.failure()?.errorText || "request failed"}`;
    diagnostics.failedRequests.push(truncate(item));
  });

  page.on("response", (response) => {
    if (!isLoginApiRequest(response.url())) return;

    const read = response
      .text()
      .then((body) => {
        const detail = truncate(body || "<empty>");
        diagnostics.loginApiResponses.push(
          `${response.status()} ${response.request().method()} ${response.url()} :: ${detail}`,
        );
      })
      .catch((error) => {
        diagnostics.loginApiResponses.push(
          `${response.status()} ${response.request().method()} ${response.url()} :: <body unavailable: ${truncate(error?.message || String(error))}>`,
        );
      });

    diagnostics.pendingReads.push(read);
  });
}

/**
 * @param {AuthDiagnostics} diagnostics
 */
async function flushDiagnostics(diagnostics) {
  await Promise.allSettled(diagnostics.pendingReads);
}

/**
 * @param {AuthDiagnostics} diagnostics
 */
async function diagnosticsSummary(diagnostics) {
  await flushDiagnostics(diagnostics);

  const loginApi =
    diagnostics.loginApiResponses.join("\n") || "<no login API responses>";
  const consoleErrors =
    diagnostics.consoleErrors.join("\n") || "<no console errors>";
  const failedRequests =
    diagnostics.failedRequests.join("\n") || "<no failed requests>";

  return [
    "Auth diagnostics:",
    `LOGIN_API:\n${loginApi}`,
    `FAILED_REQUESTS:\n${failedRequests}`,
    `CONSOLE_ERRORS:\n${consoleErrors}`,
  ].join("\n");
}

async function submitLogin(page, email, password) {
  await page.goto("/");
  await expect(page.locator("#email")).toBeVisible({ timeout: 15_000 });
  await page.fill("#email", email);
  await page.fill("#password", password);
  await page.getByRole("button", { name: /log in|login|sign in/i }).click();
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
  const diagnostics = createAuthDiagnostics();
  attachAuthDiagnostics(page, diagnostics);

  await submitLogin(page, ADMIN_EMAIL, "wrongpassword");

  await expect(
    page.getByText(AUTH_ERROR_TEXT_PATTERN).first(),
    `Expected invalid-credentials message.\n${await diagnosticsSummary(diagnostics)}`,
  ).toBeVisible({ timeout: 15_000 });

  const token = await page.evaluate(() => localStorage.getItem("aura_token"));
  expect(
    token,
    `Token should not exist after failed login.\n${await diagnosticsSummary(diagnostics)}`,
  ).toBeFalsy();
});

test("valid login redirects to an authenticated route", async ({ page }) => {
  const diagnostics = createAuthDiagnostics();
  attachAuthDiagnostics(page, diagnostics);

  await submitLogin(page, ADMIN_EMAIL, ADMIN_PASSWORD);

  await expect
    .poll(
      async () => {
        await flushDiagnostics(diagnostics);
        return diagnostics.loginApiResponses.some((line) =>
          /^2\d\d\s/.test(line),
        );
      },
      { timeout: 15_000 },
    )
    .toBeTruthy();

  await expect
    .poll(
      () => page.evaluate(() => Boolean(localStorage.getItem("aura_token"))),
      {
        timeout: 15_000,
        message: `Expected auth token after login.\n${await diagnosticsSummary(diagnostics)}`,
      },
    )
    .toBe(true);

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

  await expect
    .poll(() => getPathname(page.url()), {
      timeout: 20_000,
      message: `Expected authenticated redirect after login.\n${await diagnosticsSummary(diagnostics)}`,
    })
    .toMatch(AUTHENTICATED_PATH_PATTERN);

  await expect(page.locator("#email")).toHaveCount(0);
});

test("unauthenticated user is redirected to login from protected route", async ({
  page,
}) => {
  await page.goto("/dashboard");

  await expect(page.locator("#email")).toBeVisible({ timeout: 10000 });
});
