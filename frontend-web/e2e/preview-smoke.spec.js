// @ts-check
import { expect, test } from "@playwright/test";

/**
 * @param {import('@playwright/test').Page} page
 * @returns {string[]}
 */
function captureRuntimeErrors(page) {
  /** @type {string[]} */
  const runtimeErrors = [];

  page.on("pageerror", (error) => {
    runtimeErrors.push(`pageerror: ${error.message}`);
  });

  page.on("console", (message) => {
    if (message.type() === "error") {
      runtimeErrors.push(`console: ${message.text()}`);
    }
  });

  return runtimeErrors;
}

/**
 * @param {string[]} runtimeErrors
 */
function assertNoRuntimeErrors(runtimeErrors) {
  expect(
    runtimeErrors,
    runtimeErrors.join("\n") || "Expected no runtime errors.",
  ).toEqual([]);
}

test("preview login page loads cleanly", async ({ page }) => {
  const runtimeErrors = captureRuntimeErrors(page);

  await page.goto("/");
  await expect(page.locator("#email")).toBeVisible({ timeout: 15_000 });
  await expect(page.locator("#password")).toBeVisible();
  await expect(page.getByRole("button", { name: "Log In" })).toBeVisible();

  assertNoRuntimeErrors(runtimeErrors);
});

test("preview dashboard navigation works", async ({ page }) => {
  const runtimeErrors = captureRuntimeErrors(page);

  await page.goto("/exposed/dashboard");
  await expect(
    page.getByRole("button", { name: "Schedule" }).first(),
  ).toBeVisible({
    timeout: 15_000,
  });
  await page.getByRole("button", { name: "Schedule" }).first().click();
  await expect(page).toHaveURL(/\/exposed\/dashboard\/schedule$/);

  await page.getByRole("button", { name: "Profile" }).first().click();
  await expect(page).toHaveURL(/\/exposed\/dashboard\/profile$/);

  assertNoRuntimeErrors(runtimeErrors);
});

test("preview workspace navigation works", async ({ page }) => {
  const runtimeErrors = captureRuntimeErrors(page);

  await page.goto("/exposed/workspace");
  await expect(page.getByRole("button", { name: "Users" }).first()).toBeVisible(
    {
      timeout: 15_000,
    },
  );
  await page.getByRole("button", { name: "Users" }).first().click();
  await expect(page).toHaveURL(/\/exposed\/workspace\/users$/);

  await page.getByRole("button", { name: "Settings" }).first().click();
  await expect(page).toHaveURL(/\/exposed\/workspace\/settings$/);

  assertNoRuntimeErrors(runtimeErrors);
});
