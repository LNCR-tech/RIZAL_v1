import { defineConfig, devices } from "@playwright/test";

const parsedPort = Number.parseInt(process.env.PLAYWRIGHT_PORT || "4173", 10);
const previewPort = Number.isFinite(parsedPort) ? parsedPort : 4173;
const baseURL =
  process.env.PLAYWRIGHT_BASE_URL || `http://127.0.0.1:${previewPort}`;
const serverUrl = process.env.PLAYWRIGHT_WEB_SERVER_URL || baseURL;
const backendBaseUrl =
  process.env.PLAYWRIGHT_BACKEND_BASE_URL ||
  process.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";
const serverCommand =
  process.env.PLAYWRIGHT_WEB_SERVER_COMMAND ||
  `npm run build && npm run preview -- --host 127.0.0.1 --port ${previewPort}`;
const storageOrigin = new URL(baseURL).origin;

const reuseExistingServer =
  process.env.PLAYWRIGHT_REUSE_SERVER === "true" ||
  (!!process.env.PLAYWRIGHT_BASE_URL &&
    process.env.PLAYWRIGHT_REUSE_SERVER !== "false") ||
  (!process.env.CI && process.env.PLAYWRIGHT_REUSE_SERVER !== "false");

export default defineConfig({
  testDir: "./e2e",
  globalSetup: "./e2e/global-setup.ts",
  timeout: 45_000,
  expect: {
    timeout: 10_000,
  },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 2 : undefined,
  outputDir: "test-results",
  reporter: process.env.CI
    ? [
        ["list"],
        ["html", { open: "never", outputFolder: "playwright-report" }],
        ["junit", { outputFile: "test-results/playwright-junit.xml" }],
      ]
    : [
        ["list"],
        ["html", { open: "never", outputFolder: "playwright-report" }],
      ],

  use: {
    baseURL,
    headless: true,
    screenshot: "only-on-failure",
    video: "retain-on-failure",
    trace: "retain-on-failure",
    storageState: {
      cookies: [],
      origins: [
        {
          origin: storageOrigin,
          localStorage: [],
        },
      ],
    },
    actionTimeout: 20_000,
    navigationTimeout: 30_000,
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "mobile-chromium",
      testMatch: /preview-smoke\.spec\.ts$/,
      use: { ...devices["Pixel 7"] },
    },
  ],

  webServer: {
    command: serverCommand,
    url: serverUrl,
    reuseExistingServer,
    timeout: 180_000,
    env: {
      VITE_APP_BASE_PATH: "/",
      VITE_API_BASE_URL: backendBaseUrl,
      VITE_ASSISTANT_BASE_URL:
        process.env.VITE_ASSISTANT_BASE_URL || "http://127.0.0.1:8500",
    },
  },
});
