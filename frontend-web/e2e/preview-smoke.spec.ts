import { expect, test } from "./base";

type ImportantRoute = {
  path: string;
  name: string;
  assertReady: (page: any) => Promise<void>;
};

const IMPORTANT_ROUTES: ImportantRoute[] = [
  {
    path: "/",
    name: "login",
    assertReady: async (page) => {
      await expect(page.locator("#email")).toBeVisible({ timeout: 15_000 });
      await expect(page.locator("#password")).toBeVisible();
    },
  },
  {
    path: "/exposed/dashboard/gather",
    name: "gather",
    assertReady: async (page) => {
      await expect(page.locator(".gather-welcome")).toBeVisible({
        timeout: 15_000,
      });
    },
  },
  {
    path: "/exposed/dashboard/analytics",
    name: "analytics",
    assertReady: async (page) => {
      await expect(page.locator(".analytics-page")).toBeVisible({
        timeout: 15_000,
      });
    },
  },
  {
    path: "/exposed/governance/events",
    name: "events",
    assertReady: async (page) => {
      await expect(page.locator(".governance-workspace")).toBeVisible({
        timeout: 20_000,
      });
    },
  },
  {
    path: "/exposed/dashboard/profile",
    name: "profile",
    assertReady: async (page) => {
      await expect(page.locator(".profile-page")).toBeVisible({
        timeout: 15_000,
      });
    },
  },
];

test("production smoke routes load with no chunk, asset, or runtime failures", async ({ page }) => {
  for (const route of IMPORTANT_ROUTES) {
    await test.step(`route ${route.name}: ${route.path}`, async () => {
      const response = await page.goto(route.path, { waitUntil: "domcontentloaded" });
      const status = response?.status() ?? 0;
      expect(status).toBeGreaterThanOrEqual(200);
      expect(status).toBeLessThan(400);
      await route.assertReady(page);
      await expect(page.locator(".not-found-view__title")).toHaveCount(0);
    });
  }
});

test("mobile viewport renders critical routes without layout breakage", async ({ page }, testInfo) => {
  test.skip(!testInfo.project.use?.isMobile, "This smoke check only applies to the mobile project.");

  const routesToCheck = ["/", "/exposed/dashboard/analytics", "/exposed/dashboard/profile"];
  for (const route of routesToCheck) {
    await test.step(`mobile render ${route}`, async () => {
      await page.goto(route, { waitUntil: "domcontentloaded" });
      
      const viewport = await page.evaluate(() => ({
        innerWidth: window.innerWidth,
        scrollWidth: document.documentElement.scrollWidth,
        innerHeight: window.innerHeight,
        scrollHeight: document.documentElement.scrollHeight,
      }));
      
      expect(viewport.scrollWidth).toBeLessThanOrEqual(viewport.innerWidth + 4);
      expect(viewport.scrollHeight).toBeGreaterThan(viewport.innerHeight / 2);
      await expect(page.locator(".not-found-view__title")).toHaveCount(0);
    });
  }
});
