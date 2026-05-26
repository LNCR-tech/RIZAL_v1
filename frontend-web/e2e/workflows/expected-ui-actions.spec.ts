import { expect, test } from "../base";
import {
  E2E_USERS,
  expectPathnameToMatch,
  gotoLoginAndWait,
  loginAs,
  readStoredToken,
} from "../helpers/auth";
import { navigateAndAssertUsable } from "../helpers/pressables";

// This test checks login-page controls with exact expected outcomes: password visibility and forgot-password navigation.
test("login page controls perform the expected visible actions [LoginView.vue]", async ({ page }) => {
  await gotoLoginAndWait(page);

  const passwordInput = page.locator("#password");
  await expect(passwordInput).toHaveAttribute("type", "password");

  await page.getByRole("button", { name: /show password/i }).click();
  await expect(passwordInput).toHaveAttribute("type", "text");

  await page.getByRole("button", { name: /hide password/i }).click();
  await expect(passwordInput).toHaveAttribute("type", "password");

  await page.getByRole("link", { name: /forgot password/i }).click();
  await expectPathnameToMatch(page, /^\/forgot-password$/i);
  await expect(page.getByRole("heading", { name: /find your account/i })).toBeVisible();

  await page.getByRole("button", { name: /back to login/i }).click();
  await expectPathnameToMatch(page, /^\/$/);
  await expect(page.locator("#password")).toBeVisible();
});

// This test checks the failed-login path with exact expected outcomes: backend rejection, no token, and staying on login.
test("login rejects wrong passwords without creating a session [LoginView.vue]", async ({ page }) => {
  test.skip(
    process.env.PLAYWRIGHT_MOCK_AUTH !== "true",
    "Bad-login UI check needs Playwright mock auth so the 401 response is deterministic.",
  );

  await gotoLoginAndWait(page);
  await page.locator("#email").fill(E2E_USERS.student.email);
  await page.locator("#password").fill("WrongPassword!");

  const failedLogin = page.waitForResponse(
    (response) =>
      response.url().includes("/token") &&
      response.request().method() === "POST" &&
      response.status() === 401,
  );
  await page.getByRole("button", { name: /log in|login|sign in/i }).click();
  await failedLogin;

  await expectPathnameToMatch(page, /^\/$/);
  await expect(page.locator("#password")).toBeVisible();
  await expect.poll(async () => await readStoredToken(page)).toBe("");
});

// This test checks that a preview event detail route renders the expected event sections.
test("student event detail preview shows the selected event information [EventDetailView.vue]", async ({ page }) => {
  await navigateAndAssertUsable(page, {
    name: "student event detail preview",
    path: "/exposed/dashboard/schedule/3",
  });

  await expect(page.getByRole("heading", { name: /leadership summit/i })).toBeVisible();
  await expect(page.getByRole("heading", { name: /^schedule$/i })).toBeVisible();
  await expect(page.getByRole("heading", { name: /^location$/i })).toBeVisible();
  await expect(page.getByLabel(/attendance geofence/i)).toBeVisible();
});

// This test checks student navigation and profile controls with exact route/toggle/edit expectations.
test("student navigation and profile controls produce the expected results [ProfileView.vue]", async ({ page }) => {
  test.skip(
    process.env.PLAYWRIGHT_MOCK_AUTH !== "true",
    "Student expected-result UI checks need Playwright mock auth.",
  );

  await loginAs(page, E2E_USERS.student);
  await expectPathnameToMatch(page, /^\/dashboard(?:\/|$)/i);

  await page.locator("button[aria-label='Schedule']").click();
  await expectPathnameToMatch(page, /^\/dashboard\/schedule(?:\/|$)/i);

  await page.locator("button[aria-label='Analytics']").click();
  await expectPathnameToMatch(page, /^\/dashboard\/analytics(?:\/|$)/i);

  await page.locator("button[aria-label='Profile']").click();
  await expectPathnameToMatch(page, /^\/dashboard\/profile(?:\/|$)/i);

  const notificationToggle = page.getByRole("button", { name: /toggle notifications/i });
  const notificationState = await notificationToggle.getAttribute("aria-pressed");
  await notificationToggle.click();
  await expect(notificationToggle).toHaveAttribute(
    "aria-pressed",
    notificationState === "true" ? "false" : "true",
  );

  await page.getByRole("button", { name: /edit profile/i }).click();
  await expect(page.getByRole("heading", { name: /edit profile/i })).toBeVisible();
  await page.getByRole("button", { name: /^cancel$/i }).first().click();
  await expect(page.getByRole("heading", { name: /edit profile/i })).toHaveCount(0);

  await page.getByRole("button", { name: /^security$/i }).click();
  await expectPathnameToMatch(page, /^\/profile\/security(?:\/|$)/i);
});

// This test checks campus-admin navigation cards and settings controls with exact route/display expectations.
test("campus admin workspace controls produce the expected results [SchoolItScheduleView.vue]", async ({ page }) => {
  test.skip(
    process.env.PLAYWRIGHT_MOCK_AUTH !== "true",
    "Campus expected-result UI checks need Playwright mock auth.",
  );

  await loginAs(page, E2E_USERS.campusAdmin);
  await expectPathnameToMatch(page, /^\/workspace(?:\/|$)/i);

  await page.locator("button[aria-label='Users']").click();
  await expectPathnameToMatch(page, /^\/workspace\/users(?:\/|$)/i);

  await page.locator("button[aria-label='Schedule']").click();
  await expectPathnameToMatch(page, /^\/workspace\/schedule(?:\/|$)/i);

  await page.getByRole("button", { name: /event settings/i }).click();
  await expect(page.getByText(/start checking in/i)).toBeVisible();
  await expect(page.getByText(/mark student late after/i)).toBeVisible();

  await page.getByRole("button", { name: /attendance\s*monitor/i }).click();
  await expectPathnameToMatch(page, /^\/workspace\/schedule\/monitor(?:\/|$)/i);

  await navigateAndAssertUsable(page, { name: "campus schedule", path: "/workspace/schedule" });
  await page.getByRole("button", { name: /reports/i }).click();
  await expectPathnameToMatch(page, /^\/workspace\/schedule\/reports(?:\/|$)/i);

  await page.locator("button[aria-label='Settings']").click();
  await expectPathnameToMatch(page, /^\/workspace\/settings(?:\/|$)/i);
});

// This test checks the governance create flow and audience selectors with exact field-visibility expectations.
test("governance event create controls expose the expected audience fields [GovernanceWorkspaceView.vue + EventEditorSheet.vue]", async ({ page }) => {
  await navigateAndAssertUsable(page, {
    name: "governance events preview",
    path: "/exposed/governance/events",
  });

  await page.getByRole("button", { name: /open event and announcement create options/i }).click();
  await expect(page.getByRole("dialog", { name: /what do you want to create/i })).toBeVisible();

  await page.getByRole("button", { name: /event.*create and publish/i }).click();
  await expect(page.getByRole("dialog", { name: /create event/i })).toBeVisible();
  await expect(page.getByTestId("audience-section")).toBeVisible();

  const scopeSelect = page.getByTestId("audience-scope-select");
  await scopeSelect.selectOption("YEAR_LEVEL");
  await expect(page.getByTestId("year-level-field")).toBeVisible();
  await expect(page.getByTestId("department-field")).toHaveCount(0);
  await expect(page.getByTestId("course-field")).toHaveCount(0);

  await scopeSelect.selectOption("DEPARTMENT_YEAR");
  await expect(page.getByTestId("year-level-field")).toBeVisible();
  await expect(page.getByTestId("department-field")).toBeVisible();
  await expect(page.getByTestId("course-field")).toHaveCount(0);

  await scopeSelect.selectOption("COURSE_YEAR");
  await expect(page.getByTestId("year-level-field")).toBeVisible();
  await expect(page.getByTestId("course-field")).toBeVisible();
  await expect(page.getByTestId("department-field")).toHaveCount(0);

  await page.getByRole("button", { name: /close event editor/i }).click();
  await expect(page.getByRole("dialog", { name: /create event/i })).toHaveCount(0);
});

// This test checks that creating a preview governance event with a year-level audience submits successfully and adds it to the event feed.
test("governance event create accepts a year-level audience [GovernanceWorkspaceView.vue + EventEditorSheet.vue]", async ({ page }) => {
  const eventName = "Automated Year 4 Audience Event";
  const currentMonth = new Date();
  const monthValue = `${currentMonth.getFullYear()}-${String(currentMonth.getMonth() + 1).padStart(2, "0")}`;

  await navigateAndAssertUsable(page, {
    name: "governance events preview",
    path: "/exposed/governance/events",
  });

  await page.getByRole("button", { name: /open event and announcement create options/i }).click();
  await page.getByRole("button", { name: /event.*create and publish/i }).click();
  await expect(page.getByRole("dialog", { name: /create event/i })).toBeVisible();

  await page.locator("input[name='event_name']").fill(eventName);
  await page.locator("input[name='event_start_datetime']").fill(`${monthValue}-15T09:00`);
  await page.locator("input[name='event_end_datetime']").fill(`${monthValue}-15T11:00`);
  await page.locator("input[name='event_location']").fill("Automation Hall");

  await page.getByTestId("audience-scope-select").selectOption("YEAR_LEVEL");
  await page.getByTestId("year-level-select").selectOption("4");
  await expect(page.getByTestId("year-level-select")).toHaveValue("4");

  await page.getByRole("button", { name: /^create event$/i }).click();
  await expect(page.getByRole("dialog", { name: /create event/i })).toHaveCount(0);
  await expect(page.getByText(eventName)).toBeVisible();
});

// This test checks preview schedule cards with exact route outcomes and a visible settings panel.
test("workspace preview schedule controls produce the expected results [SchoolItScheduleView.vue]", async ({ page }) => {
  await navigateAndAssertUsable(page, {
    name: "workspace schedule preview",
    path: "/exposed/workspace/schedule",
  });

  await page.getByRole("button", { name: /event settings/i }).click();
  await expect(page.getByText(/start checking in/i)).toBeVisible();

  await page.getByRole("button", { name: /attendance\s*monitor/i }).click();
  await expectPathnameToMatch(page, /^\/exposed\/workspace\/schedule\/monitor(?:\/|$)/i);

  await navigateAndAssertUsable(page, {
    name: "workspace schedule preview",
    path: "/exposed/workspace/schedule",
  });
  await page.getByRole("button", { name: /reports/i }).click();
  await expectPathnameToMatch(page, /^\/exposed\/workspace\/schedule\/reports(?:\/|$)/i);
});
