import fs from "node:fs";
import path from "node:path";

const projectRoot = process.cwd();
const ignoredDirectories = new Set([
  ".git",
  "coverage",
  "dist",
  "docs",
  "node_modules",
  "playwright-report",
  "test-results",
]);

const ignoredFiles = new Set(["package-lock.json"]);

const textExtensions = new Set([
  ".cjs",
  ".css",
  ".env",
  ".example",
  ".html",
  ".js",
  ".json",
  ".md",
  ".mjs",
  ".scss",
  ".ts",
  ".tsx",
  ".vue",
  ".yaml",
  ".yml",
]);

const patterns = [
  { name: "Google API key", regex: /\bAIza[0-9A-Za-z_-]{35}\b/g },
  { name: "OpenAI key", regex: /\bsk-[A-Za-z0-9_-]{20,}\b/g },
  { name: "AWS access key", regex: /\bAKIA[0-9A-Z]{16}\b/g },
  { name: "Stripe live secret", regex: /\bsk_live_[0-9A-Za-z]{16,}\b/g },
  { name: "Private key block", regex: /-----BEGIN [A-Z ]*PRIVATE KEY-----/g },
  {
    name: "Suspicious inline API key assignment",
    regex:
      /\b(?:api|access|private|secret)[-_ ]?key\b\s*[:=]\s*['"`][^'"`\s]{16,}['"`]/gi,
  },
];

const findings = [];
scanDirectory(projectRoot);

if (findings.length > 0) {
  console.error("Potential frontend secrets detected:");
  for (const finding of findings) {
    console.error(
      `- ${finding.file}:${finding.line} [${finding.pattern}] ${finding.preview}`,
    );
  }
  process.exit(1);
}

console.log(
  "No hardcoded secrets or API keys were detected in the frontend repository scan.",
);

function scanDirectory(directory) {
  const entries = fs.readdirSync(directory, { withFileTypes: true });

  for (const entry of entries) {
    if (ignoredDirectories.has(entry.name)) continue;

    const resolvedPath = path.join(directory, entry.name);

    if (entry.isDirectory()) {
      scanDirectory(resolvedPath);
      continue;
    }

    if (!shouldScanFile(entry.name)) continue;
    scanFile(resolvedPath);
  }
}

function shouldScanFile(fileName) {
  if (ignoredFiles.has(fileName)) return false;

  const extension = path.extname(fileName);
  if (textExtensions.has(extension)) return true;

  return fileName.startsWith(".env");
}

function scanFile(filePath) {
  const contents = fs.readFileSync(filePath, "utf8");
  const lines = contents.split(/\r?\n/);

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    if (line.includes("secret-scan: allow")) continue;

    for (const pattern of patterns) {
      pattern.regex.lastIndex = 0;
      if (!pattern.regex.test(line)) continue;

      findings.push({
        file: path.relative(projectRoot, filePath),
        line: index + 1,
        pattern: pattern.name,
        preview: line.trim(),
      });
    }
  }
}
