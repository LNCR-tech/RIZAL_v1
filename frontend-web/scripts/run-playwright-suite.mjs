import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const rawArgs = process.argv.slice(2);
const playwrightArgs = [];
const env = { ...process.env };

for (const arg of rawArgs) {
  if (arg === "--mock-auth") {
    env.PLAYWRIGHT_MOCK_AUTH = "true";
    env.PLAYWRIGHT_REQUIRE_BACKEND = "false";
    continue;
  }

  if (arg === "--require-backend") {
    env.PLAYWRIGHT_MOCK_AUTH = "false";
    env.PLAYWRIGHT_REQUIRE_BACKEND = "true";
    continue;
  }

  playwrightArgs.push(arg);
}

// Keep this wrapper small: it only sets cross-platform env flags and delegates to Playwright.
const playwrightCliPath = fileURLToPath(
  new URL("../node_modules/@playwright/test/cli.js", import.meta.url),
);
const child = spawn(process.execPath, [playwrightCliPath, "test", ...playwrightArgs], {
  env,
  stdio: "inherit",
});

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 1);
});
