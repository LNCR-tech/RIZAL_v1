import { expect, test } from "./base";

const USERS = {
  campus_admin: { email: "campus_admin@test.com", password: "TestPass123!" },
  student: { email: "student@test.com", password: "TestPass123!" },
};

const AUTHENTICATED_PATH_PATTERN =
  /^\/(workspace|dashboard|admin|governance|privileged-face|face-registration|change-password)(?:\/|$)/i;
const STUDENT_ALLOWED_PATH_PATTERN =
  /^\/(dashboard|face-registration|change-password|privileged-face)(?:\/|$)/i;
const CAMPUS_ADMIN_ALLOWED_PATH_PATTERN =
  /^\/(workspace|face-registration|change-password|privileged-face)(?:\/|$)/i;

async function expectPathnameToMatch(
  page: import("@playwright/test").Page,
  pattern: RegExp,
  timeout = 20_000,
) {
  await expect(page).toHaveURL((url) => pattern.test(url.pathname), { timeout });
}

async function waitForBootOverlayToClear(
  page: import("@playwright/test").Page,
  timeout = 15_000,
) {
  const locator = page.locator(".app-boot-screen").first();
  // Wait a tiny bit for it to potentially mount
  await page.waitForTimeout(100);
  if (await locator.isVisible()) {
    await locator.waitFor({ state: "hidden", timeout }).catch(() => null);
  }
}

async function readStoredToken(page: import("@playwright/test").Page) {
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

async function gotoLoginAndWait(page: import("@playwright/test").Page) {
  const response = await page.goto("/", { waitUntil: "domcontentloaded" });
  const status = response?.status() ?? 0;
  expect(status).toBeGreaterThanOrEqual(200);
  expect(status).toBeLessThan(400);

  await page.waitForLoadState("networkidle", { timeout: 15_000 }).catch(() => null);
  await waitForBootOverlayToClear(page);
  await expect(page.locator("#email")).toBeVisible({ timeout: 20_000 });
  await expect(page.locator("#password")).toBeVisible();
}

async function settleTermsModalIfShown(page: import("@playwright/test").Page) {
  const acknowledgeButton = page.getByRole("button", { name: /i understand/i });
  if (await acknowledgeButton.isVisible({ timeout: 3_000 }).catch(() => false)) {
    await acknowledgeButton.click();
  }
}

async function loginAs(
  page: import("@playwright/test").Page,
  credentials: { email: string; password: string },
) {
  await gotoLoginAndWait(page);
  await page.fill("#email", credentials.email);
  await page.fill("#password", credentials.password);
  await waitForBootOverlayToClear(page);
  await page.getByRole("button", { name: /log in|login|sign in/i }).click();

  // Wait for token BEFORE handling modal, as the token is set prior to showing the modal
  await expect
    .poll(async () => Boolean(await readStoredToken(page)), { timeout: 20_000 })
    .toBe(true);

  await settleTermsModalIfShown(page);
  await expectPathnameToMatch(page, AUTHENTICATED_PATH_PATTERN);
}

test.describe("RBAC Frontend Tests", () => {
  test("student login lands on student dashboard route", async ({ page }) => {
    await loginAs(page, USERS.student);
    await expectPathnameToMatch(page, STUDENT_ALLOWED_PATH_PATTERN);
  });

  test("campus admin login lands on workspace route", async ({ page }) => {
    await loginAs(page, USERS.campus_admin);
    await expectPathnameToMatch(page, CAMPUS_ADMIN_ALLOWED_PATH_PATTERN);
  });

  test("student cannot access admin routes directly", async ({ page }) => {
    await loginAs(page, USERS.student);
    await expectPathnameToMatch(page, STUDENT_ALLOWED_PATH_PATTERN);

    await page.goto("/admin/schools", { waitUntil: "domcontentloaded" });
    await page.waitForLoadState("networkidle", { timeout: 10_000 }).catch(() => null);
    await expect(page).not.toHaveURL((url) => /^\/admin(?:\/|$)/i.test(url.pathname));
  });
});
