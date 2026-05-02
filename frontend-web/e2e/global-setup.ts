import type { FullConfig } from "@playwright/test";

const FRONTEND_WAIT_TIMEOUT_MS = Number.parseInt(
  process.env.PLAYWRIGHT_FRONTEND_WAIT_TIMEOUT_MS || "120000",
  10,
);
const BACKEND_WAIT_TIMEOUT_MS = Number.parseInt(
  process.env.PLAYWRIGHT_BACKEND_WAIT_TIMEOUT_MS || "120000",
  10,
);
const POLL_INTERVAL_MS = Number.parseInt(
  process.env.PLAYWRIGHT_HEALTH_POLL_INTERVAL_MS || "2000",
  10,
);
const REQUIRE_BACKEND =
  (process.env.PLAYWRIGHT_REQUIRE_BACKEND || "").trim().toLowerCase() === "true";

function normalizeBaseUrl(value: string) {
  return String(value || "").trim().replace(/\/+$/, "");
}

async function sleep(ms: number) {
  await new Promise((resolve) => setTimeout(resolve, ms));
}

async function waitForHealthyUrl(
  label: string,
  url: string,
  timeoutMs: number,
): Promise<void> {
  const startTime = Date.now();
  let lastError = "No response";

  while (Date.now() - startTime < timeoutMs) {
    try {
      const response = await fetch(url, {
        method: "GET",
        headers: { Accept: "application/json,text/html;q=0.9,*/*;q=0.8" },
      });
      if (response.status >= 200 && response.status < 400) {
        return;
      }
      lastError = `status ${response.status}`;
    } catch (error) {
      lastError = error instanceof Error ? error.message : String(error);
    }

    await sleep(POLL_INTERVAL_MS);
  }

  throw new Error(
    `Timed out waiting for ${label} health check at ${url} after ${timeoutMs}ms. Last error: ${lastError}`,
  );
}

export default async function globalSetup(config: FullConfig) {
  const configuredBaseUrl = String(config.projects[0]?.use?.baseURL || "");
  const baseUrl = normalizeBaseUrl(
    process.env.PLAYWRIGHT_BASE_URL || configuredBaseUrl || "http://127.0.0.1:4173",
  );

  const backendBaseUrl = normalizeBaseUrl(
    process.env.PLAYWRIGHT_BACKEND_BASE_URL ||
      process.env.VITE_API_BASE_URL ||
      "http://127.0.0.1:8000",
  );

  const frontendHealthUrl = process.env.PLAYWRIGHT_FRONTEND_HEALTH_URL || `${baseUrl}/`;
  const backendHealthUrl =
    process.env.PLAYWRIGHT_BACKEND_HEALTH_URL || `${backendBaseUrl}/health`;

  await waitForHealthyUrl("frontend", frontendHealthUrl, FRONTEND_WAIT_TIMEOUT_MS);
  if (REQUIRE_BACKEND) {
    await waitForHealthyUrl("backend", backendHealthUrl, BACKEND_WAIT_TIMEOUT_MS);
  }
}
