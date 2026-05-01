// @ts-check
import { test, expect } from "@playwright/test";

const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL || "campus_admin@test.com";
const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD || "TestPass123!";
const LOGIN_API_PATH_PATTERN = /\/(?:api\/)?token$/i;
const AUTH_ERROR_TEXT_PATTERN = /invalid|incorrect|failed|error|credentials/i;
const CORS_ERROR_PATTERN =
  /blocked by CORS policy|access-control-allow-origin|cors/i;
const AUTHENTICATED_PATH_PATTERN =
  /^\/(workspace|dashboard|admin|governance|privileged|face-registration|change-password)(?:\/|$)/i;

/**
 * @typedef {{
 *   consoleErrors: string[];
 *   pageErrors: string[];
 *   failedRequests: string[];
 *   loginRequestFailures: string[];
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
    pageErrors: [],
    failedRequests: [],
    loginRequestFailures: [],
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

  page.on("pageerror", (error) => {
    diagnostics.pageErrors.push(truncate(error?.message || String(error)));
  });

  page.on("requestfailed", (request) => {
    const item = `${request.method()} ${request.url()} :: ${request.failure()?.errorText || "request failed"}`;
    diagnostics.failedRequests.push(truncate(item));
    if (isLoginApiRequest(request.url())) {
      diagnostics.loginRequestFailures.push(truncate(item));
    }
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
  const loginRequestFailures =
    diagnostics.loginRequestFailures.join("\n") ||
    "<no login request failures>";
  const consoleErrors =
    diagnostics.consoleErrors.join("\n") || "<no console errors>";
  const pageErrors = diagnostics.pageErrors.join("\n") || "<no page errors>";
  const failedRequests =
    diagnostics.failedRequests.join("\n") || "<no failed requests>";

  return [
    "Auth diagnostics:",
    `LOGIN_API:\n${loginApi}`,
    `LOGIN_REQUEST_FAILURES:\n${loginRequestFailures}`,
    `FAILED_REQUESTS:\n${failedRequests}`,
    `CONSOLE_ERRORS:\n${consoleErrors}`,
    `PAGE_ERRORS:\n${pageErrors}`,
  ].join("\n");
}

function classifyLoginFailure(diagnostics) {
  const allErrorText = [...diagnostics.consoleErrors, ...diagnostics.pageErrors]
    .join("\n")
    .toLowerCase();
  if (CORS_ERROR_PATTERN.test(allErrorText)) {
    return "CORS_BLOCKED";
  }
  if (diagnostics.loginApiResponses.some((line) => /^401\s/.test(line))) {
    return "INVALID_CREDENTIALS";
  }
  if (diagnostics.loginApiResponses.some((line) => /^404\s/.test(line))) {
    return "API_ROUTE_MISCONFIGURED";
  }
  if (diagnostics.loginApiResponses.some((line) => /^405\s/.test(line))) {
    return "API_METHOD_MISCONFIGURED";
  }
  if (diagnostics.loginApiResponses.some((line) => /^5\d\d\s/.test(line))) {
    return "API_SERVER_ERROR";
  }
  if (
    diagnostics.loginRequestFailures.length > 0 &&
    diagnostics.loginApiResponses.length === 0
  ) {
    return "API_UNREACHABLE";
  }
  return "UNKNOWN";
}

async function ensureLoginAttemptObserved(diagnostics, contextLabel) {
  await expect
    .poll(
      async () => {
        await flushDiagnostics(diagnostics);
        return (
          diagnostics.loginApiResponses.length > 0 ||
          diagnostics.loginRequestFailures.length > 0 ||
          diagnostics.consoleErrors.some((text) =>
            CORS_ERROR_PATTERN.test(text),
          )
        );
      },
      {
        timeout: 15_000,
        message: `No login API activity observed for ${contextLabel}.`,
      },
    )
    .toBe(true);
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
  await ensureLoginAttemptObserved(diagnostics, "wrong-password login");

  const loginFailureType = classifyLoginFailure(diagnostics);
  if (loginFailureType !== "INVALID_CREDENTIALS") {
    const reasonByType = {
      CORS_BLOCKED: "CORS blocked the login request.",
      API_UNREACHABLE: "Login API was unreachable from frontend preview.",
      API_ROUTE_MISCONFIGURED:
        "Login API path/proxy is misconfigured (404 returned).",
      API_METHOD_MISCONFIGURED:
        "Login API method is misconfigured (405 returned).",
      API_SERVER_ERROR: "Login API returned a 5xx server error.",
      UNKNOWN: "Wrong-password request did not fail as invalid credentials.",
    };
    const reason =
      reasonByType[loginFailureType] ??
      `Unexpected wrong-password failure type: ${loginFailureType}.`;
    throw new Error(`${reason}\n${await diagnosticsSummary(diagnostics)}`);
  }

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
  await ensureLoginAttemptObserved(diagnostics, "valid login");

  const hasSuccessfulLoginResponse = await expect
    .poll(async () => {
      await flushDiagnostics(diagnostics);
      return diagnostics.loginApiResponses.some((line) =>
        /^2\d\d\s/.test(line),
      );
    })
    .toBeTruthy()
    .then(() => true)
    .catch(() => false);

  if (!hasSuccessfulLoginResponse) {
    const loginFailureType = classifyLoginFailure(diagnostics);
    const reason =
      loginFailureType === "CORS_BLOCKED"
        ? "CORS blocked the auth request."
        : loginFailureType === "API_UNREACHABLE"
          ? "Login API was unreachable from frontend preview."
          : loginFailureType === "INVALID_CREDENTIALS"
            ? "Credentials were rejected by the login API."
            : loginFailureType === "API_ROUTE_MISCONFIGURED"
              ? "Login API path/proxy is misconfigured (404 returned)."
              : loginFailureType === "API_METHOD_MISCONFIGURED"
                ? "Login API method is misconfigured (405 returned)."
                : loginFailureType === "API_SERVER_ERROR"
                  ? "Login API returned a 5xx server error."
                  : "Login API did not return a successful response.";
    throw new Error(`${reason}\n${await diagnosticsSummary(diagnostics)}`);
  }

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
