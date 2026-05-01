// @ts-check
import { test, expect } from "./base";

const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL || "campus_admin@test.com";
const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD || "TestPass123!";
const AUTHENTICATED_PATH_PATTERN =
  /^\/(workspace|dashboard|admin|governance|privileged-face|face-registration|change-password)(?:\/|$)/i;

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
  await submitLogin(page, ADMIN_EMAIL, "wrongpassword");
  
  await expect(
    page.getByText(/invalid|incorrect|failed|error|credentials/i).first(),
  ).toBeVisible({ timeout: 15_000 });

  const token = await page.evaluate(() => localStorage.getItem("aura_token"));
  expect(token).toBeFalsy();
});

test("valid login redirects to an authenticated route", async ({ page }) => {
  await submitLogin(page, ADMIN_EMAIL, ADMIN_PASSWORD);
  
  await expect
    .poll(
      () => page.evaluate(() => Boolean(localStorage.getItem("aura_token"))),
      { timeout: 15_000 }
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

  await expect(page).toHaveURL(AUTHENTICATED_PATH_PATTERN, { timeout: 20000 });
  await expect(page.locator("#email")).toHaveCount(0);
});

test("unauthenticated user is redirected to login from protected route", async ({ page }) => {
  await page.goto("/dashboard");
  await expect(page.locator("#email")).toBeVisible({ timeout: 10000 });
});
