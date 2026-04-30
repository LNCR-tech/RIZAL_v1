import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:5173";
const serverUrl = process.env.PLAYWRIGHT_WEB_SERVER_URL || baseURL;
const serverCommand =
  process.env.PLAYWRIGHT_WEB_SERVER_COMMAND ||
  "npm run dev -- --host 127.0.0.1 --port 5173";
const storageOrigin = new URL(baseURL).origin;

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  retries: 0,
  workers: process.env.CI ? 2 : 3,
  reporter: process.env.CI
    ? [["list"], ["html", { open: "never", outputFolder: "playwright-report" }]]
    : "list",

  use: {
    baseURL,
    headless: true,
    screenshot: "only-on-failure",
    video: "off",
    storageState: {
      cookies: [],
      origins: [
        {
          origin: storageOrigin,
          localStorage: [],
        },
      ],
    },
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  webServer: {
    command: serverCommand,
    url: serverUrl,
    reuseExistingServer:
      !process.env.CI && process.env.PLAYWRIGHT_REUSE_SERVER !== "false",
    timeout: 60_000,
    env: {
      VITE_APP_BASE_PATH: "/",
      VITE_API_BASE_URL:
        process.env.VITE_API_BASE_URL || "http://localhost:8000",
      VITE_ASSISTANT_BASE_URL:
        process.env.VITE_ASSISTANT_BASE_URL || "http://localhost:8500",
    },
  },
});
