import { expect, test } from "./base";

const USERS = {
  campus_admin: { email: "campus_admin@test.com", password: "TestPass123!" },
  student: { email: "student@test.com", password: "TestPass123!" },
};

const STUDENT_HOME_ROUTE = /^\/dashboard(?:\/|$)/i;
const CAMPUS_ADMIN_HOME_ROUTE = /^\/workspace(?:\/|$)/i;

async function gotoLoginAndWait(page: import("@playwright/test").Page) {
  const response = await page.goto("/", { waitUntil: "domcontentloaded" });
  const status = response?.status() ?? 0;
  expect(status).toBeGreaterThanOrEqual(200);
  expect(status).toBeLessThan(400);

  await page.waitForLoadState("networkidle", { timeout: 15_000 }).catch(() => null);
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
  await page.getByRole("button", { name: /log in|login|sign in/i }).click();
  await settleTermsModalIfShown(page);
}

test.describe("RBAC Frontend Tests", () => {
  test("student login lands on student dashboard route", async ({ page }) => {
    await loginAs(page, USERS.student);
    await expect(page).toHaveURL(STUDENT_HOME_ROUTE, { timeout: 20_000 });
  });

  test("campus admin login lands on workspace route", async ({ page }) => {
    await loginAs(page, USERS.campus_admin);
    await expect(page).toHaveURL(CAMPUS_ADMIN_HOME_ROUTE, { timeout: 20_000 });
  });

  test("student cannot access admin routes directly", async ({ page }) => {
    await loginAs(page, USERS.student);
    await expect(page).toHaveURL(STUDENT_HOME_ROUTE, { timeout: 20_000 });

    await page.goto("/admin/schools", { waitUntil: "domcontentloaded" });
    await page.waitForLoadState("networkidle", { timeout: 10_000 }).catch(() => null);
    await expect(page).not.toHaveURL(/^\/admin(?:\/|$)/i);
  });
});
