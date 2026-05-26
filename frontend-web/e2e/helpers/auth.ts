import { expect } from "../base";

export const E2E_PASSWORD = "TestPass123!";

export const E2E_USERS = {
  admin: { email: "admin@test.com", password: E2E_PASSWORD },
  campusAdmin: { email: "campus_admin@test.com", password: E2E_PASSWORD },
  ssg: { email: "ssg@test.com", password: E2E_PASSWORD },
  student: { email: "student@test.com", password: E2E_PASSWORD },
};

export async function waitForBootOverlayToClear(
  page: import("@playwright/test").Page,
  timeout = 15_000,
) {
  const locator = page.locator(".app-boot-screen").first();
  // The app can briefly show a boot overlay during auth/session hydration.
  await page.waitForTimeout(100);
  if (await locator.isVisible().catch(() => false)) {
    await locator.waitFor({ state: "hidden", timeout }).catch(() => null);
  }
}

export async function readStoredToken(page: import("@playwright/test").Page) {
  return page.evaluate(() => {
    const localToken = localStorage.getItem("aura_token");
    const sessionToken =
      typeof sessionStorage !== "undefined"
        ? sessionStorage.getItem("aura_token")
        : null;
    const cookieToken = document.cookie
      .split(";")
      .map((entry) => entry.trim())
      .find((entry) => /^aura_token=/.test(entry));

    return localToken || sessionToken || cookieToken || "";
  });
}

export async function gotoLoginAndWait(page: import("@playwright/test").Page) {
  const response = await page.goto("/", { waitUntil: "domcontentloaded" });
  const status = response?.status() ?? 0;
  expect(status).toBeGreaterThanOrEqual(200);
  expect(status).toBeLessThan(400);

  await page.waitForLoadState("networkidle", { timeout: 15_000 }).catch(() => null);
  await waitForBootOverlayToClear(page);
  await expect(page.locator("#email")).toBeVisible({ timeout: 20_000 });
  await expect(page.locator("#password")).toBeVisible();
}

export async function settleTermsModalIfShown(page: import("@playwright/test").Page) {
  const acknowledgeButton = page.getByRole("button", { name: /i understand/i });
  if (await acknowledgeButton.isVisible({ timeout: 3_000 }).catch(() => false)) {
    await acknowledgeButton.click();
  }
}

export async function loginAs(
  page: import("@playwright/test").Page,
  credentials: { email: string; password: string },
) {
  await gotoLoginAndWait(page);
  await page.fill("#email", credentials.email);
  await page.fill("#password", credentials.password);
  await waitForBootOverlayToClear(page);

  // Waiting on /token makes the test fail where the real login contract breaks,
  // instead of only noticing later when a protected page does not load.
  const tokenPromise = page
    .waitForResponse(
      (response) =>
        response.url().includes("/token") &&
        response.request().method() === "POST",
      { timeout: 15_000 },
    )
    .catch(() => null);

  await page.getByRole("button", { name: /log in|login|sign in/i }).click();
  await tokenPromise;

  await expect
    .poll(async () => Boolean(await readStoredToken(page)), { timeout: 20_000 })
    .toBe(true);

  await settleTermsModalIfShown(page);
}

export async function expectPathnameToMatch(
  page: import("@playwright/test").Page,
  pattern: RegExp,
  timeout = 20_000,
) {
  await expect(page).toHaveURL((url) => pattern.test(url.pathname), { timeout });
}

