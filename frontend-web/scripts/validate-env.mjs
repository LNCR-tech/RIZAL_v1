import fs from "node:fs";
import path from "node:path";

const projectRoot = process.cwd();
const envFiles = [
  ".env.example",
  ".env",
  ".env.local",
  ".env.production",
  ".env.production.local",
  ".env.ci",
];

const env = {};
const sources = new Map();

for (const relativePath of envFiles) {
  const absolutePath = path.join(projectRoot, relativePath);
  if (!fs.existsSync(absolutePath)) continue;

  const parsed = parseEnvFile(fs.readFileSync(absolutePath, "utf8"));
  for (const [key, value] of Object.entries(parsed)) {
    env[key] = value;
    sources.set(key, relativePath);
  }
}

for (const [key, value] of Object.entries(process.env)) {
  if (typeof value !== "undefined") {
    env[key] = value;
    sources.set(key, "process.env");
  }
}

const requiredVariables = [
  { key: "VITE_API_BASE_URL", kind: "absolute-url", disallowApiPath: true },
  { key: "VITE_ASSISTANT_BASE_URL", kind: "absolute-url" },
  { key: "BACKEND_ORIGIN", kind: "absolute-url", disallowApiPath: true },
  { key: "AURA_API_BASE_URL", kind: "path-or-absolute-url" },
  { key: "VITE_API_TIMEOUT_MS", kind: "positive-integer" },
  { key: "AURA_API_TIMEOUT_MS", kind: "positive-integer" },
  { key: "AURA_PORT", kind: "port" },
];

const optionalVariables = [
  {
    key: "VITE_BACKEND_PROXY_TARGET",
    kind: "absolute-url",
    disallowApiPath: true,
  },
  {
    key: "VITE_NATIVE_API_BASE_URL",
    kind: "absolute-url",
    disallowApiPath: true,
  },
  { key: "VITE_APP_BASE_PATH", kind: "web-base-path" },
];

const errors = [];

for (const spec of requiredVariables) {
  validateVariable(spec, true);
}

for (const spec of optionalVariables) {
  validateVariable(spec, false);
}

if (errors.length > 0) {
  console.error("Frontend environment validation failed:");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log(
  `Validated frontend environment contract for ${requiredVariables.length} required variables and ${optionalVariables.length} optional overrides.`,
);

function validateVariable(spec, required) {
  const rawValue = String(env[spec.key] ?? "").trim();
  const source = sources.get(spec.key) || "unset";

  if (!rawValue) {
    if (required) {
      errors.push(`${spec.key} is required but missing.`);
    }
    return;
  }

  switch (spec.kind) {
    case "absolute-url":
      validateAbsoluteUrl(spec.key, rawValue, source, spec.disallowApiPath);
      break;
    case "path-or-absolute-url":
      validatePathOrAbsoluteUrl(spec.key, rawValue, source);
      break;
    case "positive-integer":
      validatePositiveInteger(spec.key, rawValue, source);
      break;
    case "port":
      validatePort(spec.key, rawValue, source);
      break;
    case "web-base-path":
      validateWebBasePath(spec.key, rawValue, source);
      break;
    default:
      errors.push(`${spec.key} uses an unsupported validation rule.`);
  }
}

function validateAbsoluteUrl(key, value, source, disallowApiPath = false) {
  let url;
  try {
    url = new URL(value);
  } catch {
    errors.push(
      `${key} must be an absolute http(s) URL. Found "${value}" in ${source}.`,
    );
    return;
  }

  if (!["http:", "https:"].includes(url.protocol)) {
    errors.push(
      `${key} must use http or https. Found "${value}" in ${source}.`,
    );
  }

  if (disallowApiPath && /\/api\/?$/i.test(url.pathname)) {
    errors.push(
      `${key} must point to the backend origin, not a /api path. Found "${value}" in ${source}.`,
    );
  }
}

function validatePathOrAbsoluteUrl(key, value, source) {
  if (value.startsWith("/")) return;

  try {
    const url = new URL(value);
    if (!["http:", "https:"].includes(url.protocol)) {
      errors.push(
        `${key} must be an absolute http(s) URL or a root-relative path. Found "${value}" in ${source}.`,
      );
    }
  } catch {
    errors.push(
      `${key} must be an absolute http(s) URL or a root-relative path. Found "${value}" in ${source}.`,
    );
  }
}

function validatePositiveInteger(key, value, source) {
  const numericValue = Number(value);
  if (!Number.isInteger(numericValue) || numericValue <= 0) {
    errors.push(
      `${key} must be a positive integer. Found "${value}" in ${source}.`,
    );
  }
}

function validatePort(key, value, source) {
  const numericValue = Number(value);
  if (
    !Number.isInteger(numericValue) ||
    numericValue < 1 ||
    numericValue > 65535
  ) {
    errors.push(
      `${key} must be a valid TCP port. Found "${value}" in ${source}.`,
    );
  }
}

function validateWebBasePath(key, value, source) {
  if (!value.startsWith("/")) {
    errors.push(`${key} must start with "/". Found "${value}" in ${source}.`);
  }

  if (!value.endsWith("/")) {
    errors.push(`${key} must end with "/". Found "${value}" in ${source}.`);
  }
}

function parseEnvFile(contents) {
  const parsed = {};

  for (const rawLine of contents.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) continue;

    const separatorIndex = line.indexOf("=");
    if (separatorIndex < 1) continue;

    const key = line.slice(0, separatorIndex).trim();
    let value = line.slice(separatorIndex + 1).trim();

    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }

    parsed[key] = value;
  }

  return parsed;
}
