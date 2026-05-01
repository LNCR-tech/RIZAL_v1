import fs from "node:fs";
import path from "node:path";

const options = parseArguments(process.argv.slice(2));

const stage = requireOption(options, "stage");
const command = options.command || "unknown";
const logPath = options.log || `${stage}.log`;
const summaryPath = options["summary-path"] || `ci-reports/${stage}.md`;
const exitCode = readPositiveOrZeroInteger(options["exit-code"], 0);
const maxAnnotations = readPositiveOrZeroInteger(
  options["max-annotations"],
  25,
);
const excerptLines = readPositiveOrZeroInteger(options["excerpt-lines"], 80);
const rootDirectory = process.cwd();
const absoluteLogPath = path.resolve(rootDirectory, logPath);
const timestamp = new Date().toISOString();

const logContents = fs.existsSync(absoluteLogPath)
  ? fs.readFileSync(absoluteLogPath, "utf8")
  : "";
const logLines = splitLines(logContents);
const diagnostics = dedupeDiagnostics(
  extractDiagnostics(logLines, rootDirectory),
);
const fallbackSignals = collectFallbackSignals(logLines, 12);
const failureExcerpt = takeTrailingLines(logLines, excerptLines);
const status = exitCode === 0 ? "passed" : "failed";
const summaryMarkdown = buildSummary({
  command,
  diagnostics,
  exitCode,
  fallbackSignals,
  failureExcerpt,
  logPath,
  stage,
  status,
  timestamp,
});

writeSummary(summaryPath, summaryMarkdown);
appendGitHubStepSummary(summaryMarkdown);

if (exitCode !== 0) {
  emitGitHubAnnotations(stage, diagnostics, fallbackSignals, maxAnnotations);
}

console.log(
  `[${stage}] ${status} (exit=${exitCode}) with ${diagnostics.length} parsed diagnostics.`,
);

function parseArguments(argumentList) {
  const parsed = {};

  for (let index = 0; index < argumentList.length; index += 1) {
    const token = argumentList[index];
    if (!token.startsWith("--")) continue;

    const key = token.slice(2);
    const nextToken = argumentList[index + 1];

    if (!nextToken || nextToken.startsWith("--")) {
      parsed[key] = "true";
      continue;
    }

    parsed[key] = nextToken;
    index += 1;
  }

  return parsed;
}

function requireOption(parsedOptions, key) {
  const value = String(parsedOptions[key] || "").trim();
  if (!value) {
    console.error(`Missing required option: --${key}`);
    process.exit(1);
  }
  return value;
}

function readPositiveOrZeroInteger(value, fallbackValue) {
  const numericValue = Number(value);
  return Number.isInteger(numericValue) && numericValue >= 0
    ? numericValue
    : fallbackValue;
}

function splitLines(contents) {
  if (!contents) return [];
  return contents.replaceAll("\0", "").split(/\r?\n/);
}

function extractDiagnostics(lines, rootDir) {
  /** @type {{file: string; line: number; column: number; message: string; raw: string}[]} */
  const diagnostics = [];
  let eslintCurrentFile = "";

  for (const rawLine of lines) {
    const line = rawLine || "";
    const trimmedLine = line.trim();

    if (isLikelyFilePathLine(trimmedLine)) {
      eslintCurrentFile = normalizeFilePath(trimmedLine, rootDir);
    }

    const typescriptMatch = line.match(
      /^(.+)\((\d+),(\d+)\): error (TS\d+): (.+)$/,
    );
    if (typescriptMatch) {
      diagnostics.push({
        file: normalizeFilePath(typescriptMatch[1], rootDir),
        line: Number(typescriptMatch[2]),
        column: Number(typescriptMatch[3]),
        message: `${typescriptMatch[4]} ${typescriptMatch[5]}`.trim(),
        raw: line,
      });
      continue;
    }

    const unixDiagnosticMatch = line.match(
      /^(.+?):(\d+):(\d+):\s*(?:error|warning)\s+(.+)$/i,
    );
    if (unixDiagnosticMatch) {
      diagnostics.push({
        file: normalizeFilePath(unixDiagnosticMatch[1], rootDir),
        line: Number(unixDiagnosticMatch[2]),
        column: Number(unixDiagnosticMatch[3]),
        message: unixDiagnosticMatch[4].trim(),
        raw: line,
      });
      continue;
    }

    const rollupDiagnosticMatch = line.match(
      /^CI strict build warning \[[^\]]+\] at (.+?):(\d+):(\d+): (.+)$/i,
    );
    if (rollupDiagnosticMatch) {
      diagnostics.push({
        file: normalizeFilePath(rollupDiagnosticMatch[1], rootDir),
        line: Number(rollupDiagnosticMatch[2]),
        column: Number(rollupDiagnosticMatch[3]),
        message: rollupDiagnosticMatch[4].trim(),
        raw: line,
      });
      continue;
    }

    const eslintStylishMatch = line.match(
      /^\s*(\d+):(\d+)\s+error\s+(.+?)\s{2,}([@\w/-]+)?\s*$/i,
    );
    if (eslintStylishMatch && eslintCurrentFile) {
      const eslintRule = eslintStylishMatch[4]
        ? ` (${eslintStylishMatch[4]})`
        : "";
      diagnostics.push({
        file: eslintCurrentFile,
        line: Number(eslintStylishMatch[1]),
        column: Number(eslintStylishMatch[2]),
        message: `${eslintStylishMatch[3].trim()}${eslintRule}`,
        raw: line,
      });
      continue;
    }

    const playwrightTitleMatch = line.match(
      /^\s*\d+\)\s+\[[^\]]+\]\s+›\s+(.+\.\w+):(\d+):(\d+)\s+›\s+(.+)$/,
    );
    if (playwrightTitleMatch) {
      diagnostics.push({
        file: normalizeFilePath(playwrightTitleMatch[1], rootDir),
        line: Number(playwrightTitleMatch[2]),
        column: Number(playwrightTitleMatch[3]),
        message: playwrightTitleMatch[4].trim(),
        raw: line,
      });
      continue;
    }

    const vitestTraceMatch = line.match(/^\s*❯\s+(.+\.\w+):(\d+):(\d+)\b/);
    if (vitestTraceMatch) {
      diagnostics.push({
        file: normalizeFilePath(vitestTraceMatch[1], rootDir),
        line: Number(vitestTraceMatch[2]),
        column: Number(vitestTraceMatch[3]),
        message: "Vitest stack frame",
        raw: line,
      });
      continue;
    }

    const stackTraceMatch = line.match(/\bat\s+(.+\.\w+):(\d+):(\d+)\b/);
    if (stackTraceMatch && !line.includes("node_modules")) {
      diagnostics.push({
        file: normalizeFilePath(stackTraceMatch[1], rootDir),
        line: Number(stackTraceMatch[2]),
        column: Number(stackTraceMatch[3]),
        message: "Stack trace frame",
        raw: line,
      });
      continue;
    }

    const secretMatch = line.match(/^- (.+):(\d+) \[([^\]]+)\] (.+)$/);
    if (secretMatch) {
      diagnostics.push({
        file: normalizeFilePath(secretMatch[1], rootDir),
        line: Number(secretMatch[2]),
        column: 1,
        message: `${secretMatch[3]} - ${secretMatch[4]}`.trim(),
        raw: line,
      });
    }
  }

  return diagnostics;
}

function dedupeDiagnostics(diagnostics) {
  const seen = new Set();
  const result = [];

  for (const diagnostic of diagnostics) {
    const key = [
      diagnostic.file,
      diagnostic.line,
      diagnostic.column,
      diagnostic.message,
    ].join("|");
    if (seen.has(key)) continue;
    seen.add(key);
    result.push(diagnostic);
  }

  return result;
}

function collectFallbackSignals(lines, limit) {
  const signalPattern =
    /(error|failed|failure|npm ERR!|missing|unmet|cannot find|invalid|exception)/i;
  const uniqueSignals = [];
  const seen = new Set();

  for (let index = lines.length - 1; index >= 0; index -= 1) {
    const candidate = String(lines[index] || "").trim();
    if (!candidate || candidate.length < 8) continue;
    if (!signalPattern.test(candidate)) continue;
    if (seen.has(candidate)) continue;

    seen.add(candidate);
    uniqueSignals.push(truncate(candidate, 300));
    if (uniqueSignals.length >= limit) break;
  }

  return uniqueSignals.reverse();
}

function takeTrailingLines(lines, limit) {
  if (limit <= 0 || lines.length === 0) return "";
  const tail = lines.slice(-limit).join("\n").trimEnd();
  return tail;
}

function buildSummary({
  command,
  diagnostics,
  exitCode,
  fallbackSignals,
  failureExcerpt,
  logPath,
  stage,
  status,
  timestamp,
}) {
  const statusBadge = status === "passed" ? "PASSED" : "FAILED";
  const summaryLines = [
    `### Frontend Gate: \`${stage}\` — ${statusBadge}`,
    "",
    `- Timestamp: ${timestamp}`,
    `- Command: \`${command}\``,
    `- Exit code: \`${exitCode}\``,
    `- Log file: \`${logPath}\``,
    `- Parsed diagnostics: \`${diagnostics.length}\``,
  ];

  if (diagnostics.length > 0) {
    summaryLines.push("");
    summaryLines.push("#### Parsed Diagnostics (Top 12)");
    const topDiagnostics = diagnostics.slice(0, 12);
    for (const diagnostic of topDiagnostics) {
      const location = `${diagnostic.file}:${diagnostic.line}:${diagnostic.column}`;
      summaryLines.push(`- \`${location}\` ${diagnostic.message}`);
    }
  }

  if (fallbackSignals.length > 0) {
    summaryLines.push("");
    summaryLines.push("#### Failure Signals");
    for (const signal of fallbackSignals.slice(0, 12)) {
      summaryLines.push(`- ${signal}`);
    }
  }

  if (status === "failed" && failureExcerpt) {
    summaryLines.push("");
    summaryLines.push("#### Log Excerpt (Tail)");
    summaryLines.push("```text");
    summaryLines.push(failureExcerpt);
    summaryLines.push("```");
  }

  summaryLines.push("");
  summaryLines.push("---");
  summaryLines.push("");

  return summaryLines.join("\n");
}

function writeSummary(relativePath, contents) {
  const absolutePath = path.resolve(process.cwd(), relativePath);
  fs.mkdirSync(path.dirname(absolutePath), { recursive: true });
  fs.writeFileSync(absolutePath, contents, "utf8");
}

function appendGitHubStepSummary(contents) {
  const summaryTarget = process.env.GITHUB_STEP_SUMMARY;
  if (!summaryTarget) return;
  fs.appendFileSync(summaryTarget, `${contents}\n`, "utf8");
}

function emitGitHubAnnotations(stage, diagnostics, fallbackSignals, limit) {
  const topDiagnostics = diagnostics.slice(0, limit);

  if (topDiagnostics.length > 0) {
    for (const diagnostic of topDiagnostics) {
      const props = [
        `file=${escapeProperty(diagnostic.file)}`,
        `line=${Number(diagnostic.line) || 1}`,
        `col=${Number(diagnostic.column) || 1}`,
        `title=${escapeProperty(stage)}`,
      ].join(",");
      const message = escapeData(diagnostic.message || "Frontend gate failed.");
      console.log(`::error ${props}::${message}`);
    }
    return;
  }

  const fallback =
    fallbackSignals[0] ||
    "Frontend gate failed. Check uploaded logs for details.";
  const props = `title=${escapeProperty(stage)}`;
  console.log(`::error ${props}::${escapeData(fallback)}`);
}

function isLikelyFilePathLine(value) {
  if (!value) return false;
  if (value.includes("error")) return false;
  if (value.includes("warning")) return false;
  if (value.includes(" ")) return false;
  return /\.(?:[cm]?[jt]sx?|vue|css|scss|json|html|md)$/i.test(value);
}

function normalizeFilePath(filePath, rootDir) {
  const rawPath = String(filePath || "")
    .trim()
    .replace(/\\/g, "/");
  if (!rawPath) return rawPath;

  if (path.isAbsolute(rawPath)) {
    const relative = path.relative(rootDir, rawPath).replace(/\\/g, "/");
    return relative || rawPath;
  }

  return rawPath.replace(/^\.\//, "");
}

function truncate(value, maxLength) {
  if (value.length <= maxLength) return value;
  return `${value.slice(0, maxLength - 3)}...`;
}

function escapeData(value) {
  return String(value)
    .replace(/%/g, "%25")
    .replace(/\r/g, "%0D")
    .replace(/\n/g, "%0A");
}

function escapeProperty(value) {
  return escapeData(value).replace(/:/g, "%3A").replace(/,/g, "%2C");
}
