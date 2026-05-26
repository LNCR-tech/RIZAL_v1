import { expect, test } from "../base";
import {
  E2E_USERS,
  expectPathnameToMatch,
  loginAs,
  readStoredToken,
  waitForBootOverlayToClear,
} from "../helpers/auth";

const STUDENT_DASHBOARD_ROUTE = /^\/dashboard(?:\/|$)/i;

test.describe("browser session behavior", () => {
  test("student session survives a page reload", async ({ page }) => {
    await loginAs(page, E2E_USERS.student);
    await expectPathnameToMatch(page, STUDENT_DASHBOARD_ROUTE);

    const tokenBeforeReload = await readStoredToken(page);
    expect(tokenBeforeReload).toBeTruthy();

    // Reloading is a common real-user action; the app should hydrate from storage.
    await page.reload({ waitUntil: "domcontentloaded" });
    await page.waitForLoadState("networkidle", { timeout: 15_000 }).catch(() => null);
    await waitForBootOverlayToClear(page);

    await expectPathnameToMatch(page, STUDENT_DASHBOARD_ROUTE);
    await expect(page.locator("#email")).toHaveCount(0);
    await expect.poll(async () => await readStoredToken(page)).toBe(tokenBeforeReload);
  });

  test("student logout clears token and returns to login", async ({ page }) => {
    await loginAs(page, E2E_USERS.student);
    await expectPathnameToMatch(page, STUDENT_DASHBOARD_ROUTE);

    // The top bar profile pill exposes Sign Out after expanding the pill.
    await page.locator(".profile-pill").click();
    const signOutText = page.getByText(/^Sign Out$/);
    await expect(signOutText).toBeVisible({ timeout: 5_000 });
    await signOutText.click();

    await expect(page.locator("#email")).toBeVisible({ timeout: 15_000 });
    await expect.poll(async () => Boolean(await readStoredToken(page))).toBe(false);
  });

  test("protected route with no valid local session returns to login", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });

    // This simulates a stale browser tab with only a garbage token left behind.
    await page.evaluate(() => {
      localStorage.setItem("aura_token", "invalid-e2e-token");
      localStorage.removeItem("aura_user_roles");
      localStorage.removeItem("aura_auth_meta");
      localStorage.removeItem("aura_dashboard_cache_v1");
    });

    await page.goto("/dashboard", { waitUntil: "domcontentloaded" });
    await page.waitForLoadState("networkidle", { timeout: 15_000 }).catch(() => null);

    await expect(page.locator("#email")).toBeVisible({ timeout: 15_000 });
    await expect(page).toHaveURL((url) => url.pathname === "/");
  });
});
