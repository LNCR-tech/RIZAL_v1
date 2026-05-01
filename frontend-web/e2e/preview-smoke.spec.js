// @ts-check
import { expect, test } from "@playwright/test";

const APP_ORIGIN = new URL(
  process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:4173",
).origin;

const CHUNK_FAILURE_PATTERN =
  /(Loading chunk [\w-]+ failed|Failed to fetch dynamically imported module|Importing a module script failed|ChunkLoadError|dynamically imported module)/i;

const IMPORTANT_ROUTES = [
  {
    path: "/",
    name: "login",
    assertReady: async (page) => {
      await expect(page.locator("#email")).toBeVisible({ timeout: 15_000 });
      await expect(page.locator("#password")).toBeVisible();
      await expect(page.getByRole("button", { name: "Log In" })).toBeVisible();
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

/**
 */
function collectRuntimeDiagnostics() {
  return {
    consoleErrors: [],
    pageErrors: [],
    asset404s: [],
    chunkLoadFailures: [],
  };
}

/**
 * @param {import("@playwright/test").Page} page
 * @param {{consoleErrors: string[], pageErrors: string[], asset404s: string[], chunkLoadFailures: string[]}} diagnostics
 */
function attachDiagnostics(page, diagnostics) {
  page.on("console", (message) => {
    if (message.type() !== "error") return;
    const text = message.text();
    diagnostics.consoleErrors.push(text);
    if (CHUNK_FAILURE_PATTERN.test(text)) {
      diagnostics.chunkLoadFailures.push(`console: ${text}`);
    }
  });

  page.on("pageerror", (error) => {
    const text = error.message || String(error);
    diagnostics.pageErrors.push(text);
    if (CHUNK_FAILURE_PATTERN.test(text)) {
      diagnostics.chunkLoadFailures.push(`pageerror: ${text}`);
    }
  });

  page.on("requestfailed", (request) => {
    const url = request.url();
    if (!url.startsWith(APP_ORIGIN)) return;
    const isJsOrCss = /\.(js|mjs|css)(?:\?|$)/i.test(url);
    if (!isJsOrCss) return;
    const errorText = request.failure()?.errorText || "Request failed";
    diagnostics.asset404s.push(`requestfailed ${url} :: ${errorText}`);
    if (/\.(js|mjs)(?:\?|$)/i.test(url)) {
      diagnostics.chunkLoadFailures.push(
        `requestfailed ${url} :: ${errorText}`,
      );
    }
  });

  page.on("response", (response) => {
    const url = response.url();
    if (!url.startsWith(APP_ORIGIN)) return;
    const request = response.request();
    const resourceType = request.resourceType();
    const isJsOrCss =
      resourceType === "script" ||
      resourceType === "stylesheet" ||
      /\.(js|mjs|css)(?:\?|$)/i.test(url);
    if (!isJsOrCss) return;
    if (response.status() < 400) return;
    diagnostics.asset404s.push(`${response.status()} ${url}`);
    if (/\.(js|mjs)(?:\?|$)/i.test(url)) {
      diagnostics.chunkLoadFailures.push(`${response.status()} ${url}`);
    }
  });
}

/**
 * @param {import("@playwright/test").Page} page
 * @param {{ path: string, name: string, assertReady: (page: import("@playwright/test").Page) => Promise<void> }} route
 */
async function assertRouteRenders(page, route) {
  const response = await page.goto(route.path, {
    waitUntil: "domcontentloaded",
  });
  const status = response?.status() ?? 0;
  expect(status, `Route ${route.path} failed to load`).toBeGreaterThanOrEqual(
    200,
  );
  expect(status, `Route ${route.path} failed to load`).toBeLessThan(400);

  await route.assertReady(page);
  await expect(
    page.locator(".not-found-view__title"),
    `Route ${route.path} resolved to NotFoundView`,
  ).toHaveCount(0);
}

/**
 * @param {import("@playwright/test").Page} page
 */
async function assertMobileViewportStable(page) {
  const viewport = await page.evaluate(() => ({
    innerWidth: window.innerWidth,
    scrollWidth: document.documentElement.scrollWidth,
    innerHeight: window.innerHeight,
    scrollHeight: document.documentElement.scrollHeight,
  }));
  expect(
    viewport.scrollWidth,
    `Horizontal overflow detected (${viewport.scrollWidth}px > ${viewport.innerWidth}px)`,
  ).toBeLessThanOrEqual(viewport.innerWidth + 4);
  expect(
    viewport.scrollHeight,
    "Mobile viewport rendered an empty page.",
  ).toBeGreaterThan(viewport.innerHeight / 2);
}

test("production smoke routes load with no chunk, asset, or runtime failures", async ({
  page,
}) => {
  const diagnostics = collectRuntimeDiagnostics();
  attachDiagnostics(page, diagnostics);

  for (const route of IMPORTANT_ROUTES) {
    await test.step(`route ${route.name}: ${route.path}`, async () => {
      await assertRouteRenders(page, route);
    });
  }

  expect(
    diagnostics.chunkLoadFailures,
    diagnostics.chunkLoadFailures.join("\n") ||
      "No chunk load failures expected.",
  ).toEqual([]);
  expect(
    diagnostics.asset404s,
    diagnostics.asset404s.join("\n") || "No JS/CSS asset 404s expected.",
  ).toEqual([]);
  expect(
    diagnostics.consoleErrors,
    diagnostics.consoleErrors.join("\n") || "No console errors expected.",
  ).toEqual([]);
  expect(
    diagnostics.pageErrors,
    diagnostics.pageErrors.join("\n") || "No uncaught page errors expected.",
  ).toEqual([]);
});

test("mobile viewport renders critical routes without layout breakage", async ({
  page,
}, testInfo) => {
  test.skip(
    !testInfo.project.use?.isMobile,
    "This smoke check only applies to the mobile project.",
  );

  const routesToCheck = [
    "/",
    "/exposed/dashboard/analytics",
    "/exposed/dashboard/profile",
  ];
  for (const route of routesToCheck) {
    await test.step(`mobile render ${route}`, async () => {
      await page.goto(route, { waitUntil: "domcontentloaded" });
      await assertMobileViewportStable(page);
      await expect(page.locator(".not-found-view__title")).toHaveCount(0);
    });
  }
});
