import { test as base } from "@playwright/test";

const parsedTestDelayMs = Number.parseInt(
  process.env.PLAYWRIGHT_TEST_DELAY_MS || "0",
  10,
);
const testDelayMs =
  Number.isFinite(parsedTestDelayMs) && parsedTestDelayMs > 0
    ? parsedTestDelayMs
    : 0;

export const test = base.extend<{ strictPage: import("@playwright/test").Page }>({
  page: async ({ page }, use) => {
    const consoleErrors: string[] = [];
    const pageErrors: string[] = [];
    const requestFailures: string[] = [];
    const badResponses: string[] = [];

    // Harmless warning allowlist
    const HARMLESS_PATTERNS = [
      /favicon\.ico/i, // missing favicon
      /Third-party cookie will be blocked/i, // browser warning
      /AuraChatWindow/i, // some ai demo component warning
    ];

    const isHarmless = (msg: string) => HARMLESS_PATTERNS.some(p => p.test(msg));
    const isAbortFailure = (msg: string) =>
      /ERR_ABORTED|NS_BINDING_ABORTED|AbortError/i.test(msg);

    page.on("console", msg => {
      if (msg.type() === "error" || msg.type() === "warning") {
        if (!isHarmless(msg.text())) {
          consoleErrors.push(`Console ${msg.type()}: ${msg.text()}`);
        }
      }
    });

    page.on("pageerror", err => {
      const errText = err.message || String(err);
      if (!isHarmless(errText)) {
        pageErrors.push(`Page error: ${errText}`);
      }
    });

    page.on("requestfailed", req => {
      const url = req.url();
      const failText = req.failure()?.errorText || "failed";
      if (isAbortFailure(failText)) {
        return;
      }
      if (!isHarmless(url) && !isHarmless(failText)) {
        requestFailures.push(`Request failed: ${url} - ${failText}`);
      }
    });

    page.on("response", res => {
      const status = res.status();
      if (status >= 400 && status !== 401) { // we expect 401 on bad login
        const url = res.url();
        if (!isHarmless(url)) {
          badResponses.push(`Bad response ${status}: ${url}`);
        }
      }
    });

    if (testDelayMs > 0) {
      await page.waitForTimeout(testDelayMs);
    }

    await use(page);

    const errors = [
      ...consoleErrors,
      ...pageErrors,
      ...requestFailures,
      ...badResponses
    ];

    if (errors.length > 0) {
      throw new Error(`Strict mode violations detected:\n${errors.join("\n")}`);
    }
  }
});

export { expect } from "@playwright/test";
