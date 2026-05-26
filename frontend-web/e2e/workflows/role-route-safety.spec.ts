import { expect, test } from "../base";
import {
  E2E_USERS,
  expectPathnameToMatch,
  loginAs,
} from "../helpers/auth";

const STUDENT_SAFE_ROUTE = /^\/dashboard(?:\/|$)/i;
const CAMPUS_ADMIN_SAFE_ROUTE = /^\/workspace(?:\/|$)/i;
const GOVERNANCE_CURRENT_SAFE_ROUTE = /^\/dashboard(?:\/|$)/i;

test.describe("safe route redirects", () => {
  test("student is redirected away from privileged routes", async ({ page }) => {
    await loginAs(page, E2E_USERS.student);
    await expectPathnameToMatch(page, STUDENT_SAFE_ROUTE);

    // Students must not be able to force privileged workspaces by typing URLs.
    for (const target of ["/admin/schools", "/workspace/users"]) {
      await page.goto(target, { waitUntil: "domcontentloaded" });
      await page.waitForLoadState("networkidle", { timeout: 10_000 }).catch(() => null);

      await expect(page).not.toHaveURL((url) => url.pathname.startsWith(target));
      await expectPathnameToMatch(page, STUDENT_SAFE_ROUTE);
    }
  });

  test("campus admin is redirected away from student and platform-admin routes", async ({ page }) => {
    await loginAs(page, E2E_USERS.campusAdmin);
    await expectPathnameToMatch(page, CAMPUS_ADMIN_SAFE_ROUTE);

    // Campus admins should stay inside the school workspace, not student or global admin routes.
    for (const target of ["/dashboard", "/admin/accounts"]) {
      await page.goto(target, { waitUntil: "domcontentloaded" });
      await page.waitForLoadState("networkidle", { timeout: 10_000 }).catch(() => null);

      await expect(page).not.toHaveURL((url) => url.pathname.startsWith(target));
      await expectPathnameToMatch(page, CAMPUS_ADMIN_SAFE_ROUTE);
    }
  });

  test("governance user is redirected away from privileged routes", async ({ page }) => {
    test.skip(
      process.env.PLAYWRIGHT_MOCK_AUTH !== "true",
      "This extended role exists in the Playwright mock-auth layer, not every seeded backend.",
    );

    await loginAs(page, E2E_USERS.ssg);
    await expectPathnameToMatch(page, GOVERNANCE_CURRENT_SAFE_ROUTE);

    // Governance officers should not land in platform or school IT workspaces.
    for (const target of ["/admin/schools", "/workspace/users"]) {
      await page.goto(target, { waitUntil: "domcontentloaded" });
      await page.waitForLoadState("networkidle", { timeout: 10_000 }).catch(() => null);

      await expect(page).not.toHaveURL((url) => url.pathname.startsWith(target));
      await expectPathnameToMatch(page, GOVERNANCE_CURRENT_SAFE_ROUTE);
    }
  });
});
