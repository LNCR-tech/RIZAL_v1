import fs from "node:fs";
import path from "node:path";

const distDir = path.resolve(process.cwd(), process.argv[2] || "dist");
const maxJavaScriptBytes = readThreshold("FRONTEND_MAX_JS_BYTES", 1_400 * 1024);
const maxCssBytes = readThreshold("FRONTEND_MAX_CSS_BYTES", 150 * 1024);
const maxTotalDistBytes = readThreshold(
  "FRONTEND_MAX_TOTAL_DIST_BYTES",
  8 * 1024 * 1024,
);

if (!fs.existsSync(distDir)) {
  fail(`Build output directory is missing: ${distDir}`);
}

const indexHtmlPath = path.join(distDir, "index.html");
if (!fs.existsSync(indexHtmlPath)) {
  fail(`Build output is incomplete. Missing ${indexHtmlPath}.`);
}

const files = collectFiles(distDir);
const assetFiles = files.filter((file) => path.basename(file) !== "index.html");

if (assetFiles.length === 0) {
  fail(`Build output is incomplete. No assets were generated in ${distDir}.`);
}

const jsFiles = [];
const cssFiles = [];
let totalDistBytes = 0;

for (const filePath of files) {
  const stats = fs.statSync(filePath);
  totalDistBytes += stats.size;

  if (filePath.endsWith(".js")) {
    jsFiles.push({ filePath, size: stats.size });
  }

  if (filePath.endsWith(".css")) {
    cssFiles.push({ filePath, size: stats.size });
  }
}

if (jsFiles.length === 0) {
  fail("Build output is missing JavaScript assets.");
}

if (cssFiles.length === 0) {
  fail("Build output is missing CSS assets.");
}

const oversizeJavaScript = jsFiles.filter(
  (asset) => asset.size > maxJavaScriptBytes,
);
const oversizeCss = cssFiles.filter((asset) => asset.size > maxCssBytes);

if (oversizeJavaScript.length > 0) {
  fail(
    `JavaScript bundle threshold exceeded (${formatBytes(maxJavaScriptBytes)} max):\n${formatAssetList(oversizeJavaScript)}`,
  );
}

if (oversizeCss.length > 0) {
  fail(
    `CSS bundle threshold exceeded (${formatBytes(maxCssBytes)} max):\n${formatAssetList(oversizeCss)}`,
  );
}

if (totalDistBytes > maxTotalDistBytes) {
  fail(
    `Total dist size exceeded (${formatBytes(maxTotalDistBytes)} max). Current size: ${formatBytes(totalDistBytes)}.`,
  );
}

const largestAssets = [...jsFiles, ...cssFiles]
  .sort((left, right) => right.size - left.size)
  .slice(0, 10);

console.log(`Validated dist/ integrity with ${files.length} generated files.`);
console.log(`Largest frontend assets:\n${formatAssetList(largestAssets)}`);

function readThreshold(envKey, fallbackValue) {
  const value = Number(process.env[envKey] ?? fallbackValue);
  return Number.isFinite(value) && value > 0 ? value : fallbackValue;
}

function collectFiles(directory) {
  const entries = fs.readdirSync(directory, { withFileTypes: true });
  const files = [];

  for (const entry of entries) {
    const resolvedPath = path.join(directory, entry.name);

    if (entry.isDirectory()) {
      files.push(...collectFiles(resolvedPath));
      continue;
    }

    files.push(resolvedPath);
  }

  return files;
}

function formatBytes(size) {
  return `${(size / 1024).toFixed(2)} KiB`;
}

function formatAssetList(assets) {
  return assets
    .map(
      (asset) =>
        `- ${path.relative(distDir, asset.filePath)}: ${formatBytes(asset.size)}`,
    )
    .join("\n");
}

function fail(message) {
  console.error(message);
  process.exit(1);
}
