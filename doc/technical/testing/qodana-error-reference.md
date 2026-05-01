# Qodana Error Reference

> **Status:** ACTIVE
> **Last Updated:** 2026-04-18
> **Author Role:** QA Tester / Documentation Specialist

See also: [tool-usage-guide.md](./tool-usage-guide.md) · [qa-toolchain-workflow.md](./qa-toolchain-workflow.md) · [bug-reports.md](./bug-reports.md)

---

## Purpose

This file explains what "error codes" mean in Qodana for this project.

There are two different things people usually call an error code:

1. `Qodana exit codes`
2. `Qodana inspection IDs`

These are not the same.

---

## 1. Qodana Exit Codes

Exit codes describe why the whole Qodana run failed.

| Exit Code | Meaning | QA Interpretation |
|---|---|---|
| `7` | EAP linter license expired | Tooling/config issue |
| `137` | Qodana or Docker crashed because of memory pressure | Environment/resource issue |
| `255` | Quality gate failed because detected problems exceeded threshold | Code-quality gate failure |

### Important note

An exit code tells you why the scan job failed.

It does **not** tell you which source-code problem caused the failure.

For that, you need the inspection IDs in the report.

---

## 2. Qodana Inspection IDs

Inspection IDs are the identifiers attached to individual findings.

Examples:

- `PyTypeChecker`
- `PyUnresolvedReferences`
- `JSUnresolvedReference`
- `VueMissingComponentImportInspection`

These are the real per-finding identifiers you should use when documenting Qodana results.

---

## 3. Recommended Reporting Format for This Project

Qodana does not usually assign a numeric code per source finding.

To make bug reports and QA reports easier to read, use this format:

```md
- Run Status: Failed
- Qodana Exit Code: 255
- Finding Code: QD-PY-001
- Inspection ID: PyTypeChecker
- Severity: High
- File: Backend/app/services/example.py
- Summary: Wrong type passed into service helper
```

### What each field means

| Field | Meaning |
|---|---|
| `Qodana Exit Code` | Why the scan run failed |
| `Finding Code` | Your internal QA shortcut code |
| `Inspection ID` | The real JetBrains inspection identifier |
| `Severity` | Your QA triage severity |

---

## 4. Internal Finding Codes for This Repo

These internal codes are recommended for documentation use in this project.

They are **project-level QA labels**, not official JetBrains numeric codes.

### Python findings

| Internal Code | Inspection ID | Meaning | Suggested Severity |
|---|---|---|---|
| `QD-PY-001` | `PyTypeChecker` | Wrong Python type is passed, returned, or assigned | High |
| `QD-PY-002` | `PyUnresolvedReferences` | Missing import, missing symbol, or typo in a name | High |
| `QD-PY-003` | `PyArgumentList` | Function or method called with wrong arguments | High |
| `QD-PY-004` | `PyCallingNonCallable` | Code tries to call a non-function value | High |
| `QD-PY-005` | `PyUnboundLocalVariable` | Variable may be used before assignment | High |
| `QD-PY-006` | `PyPackageRequirements` | Code imports a package that is missing from the environment | Medium |
| `QD-PY-007` | `PyInterpreter` | Python interpreter or environment setup issue | Medium |
| `QD-PY-008` | `PyUnusedLocal` | Dead or unused local Python code | Low |

### JavaScript and Vue findings

| Internal Code | Inspection ID | Meaning | Suggested Severity |
|---|---|---|---|
| `QD-JS-001` | `JSUnresolvedReference` | JS symbol used but not defined/imported | High |
| `QD-JS-002` | `JSUndeclaredVariable` | Variable used before declaration | High |
| `QD-JS-003` | `JSCheckFunctionSignatures` | Function called with invalid parameter shape | High |
| `QD-JS-004` | `JSIgnoredPromiseFromCall` | Promise ignored, possible async bug | Medium |
| `QD-JS-005` | `ES6MissingAwait` | Async call is probably missing `await` | Medium |
| `QD-JS-006` | `JSUnusedLocalSymbols` | Unused JS local symbol or dead code | Low |
| `QD-JS-007` | `JSFileReferences` | Broken import/file/module reference | High |
| `QD-VUE-001` | `VueUnrecognizedDirective` | Invalid or misspelled Vue directive | High |
| `QD-VUE-002` | `VueUnrecognizedSlot` | Invalid slot usage or slot mismatch | Medium |
| `QD-VUE-003` | `VueMissingComponentImportInspection` | Component used but not imported/registered | High |
| `QD-VUE-004` | `VueDuplicateTag` | Invalid or duplicate Vue template tags | Medium |

### HTML findings

| Internal Code | Inspection ID | Meaning | Suggested Severity |
|---|---|---|---|
| `QD-HTML-001` | `HtmlUnknownAttribute` | Unknown HTML attribute in template | Medium |
| `QD-HTML-002` | `HtmlWrongAttributeValue` | Attribute value is invalid | Medium |

### Security and dependency findings

| Internal Code | Inspection ID | Meaning | Suggested Severity |
|---|---|---|---|
| `QD-SEC-001` | `HardcodedPasswords` | Likely secret or password committed in source | Critical |
| `QD-SEC-002` | `HttpUrlsUsage` | Insecure plain HTTP URL detected | Medium |
| `QD-SEC-003` | `VulnerableLibrariesLocal` | Dependency has known vulnerability | Critical |

---

## 5. How to Triage a Qodana Result

### Step 1: Check the exit code

Ask:

- did the run fail because of memory?
- because of quality gate?
- because the setup/config is broken?

### Step 2: Read the finding inspection ID

Ask:

- is it a correctness issue?
- a security issue?
- a dead-code issue?
- a config/environment issue?

### Step 3: Assign QA severity

Use this rule:

| Severity | Use When |
|---|---|
| Critical | Secrets, vulnerable dependencies, startup-blocking defects |
| High | Core runtime correctness bug, broken route, broken import, broken auth logic |
| Medium | Async risk, invalid template usage, config inconsistency |
| Low | Dead code, cleanup-only findings, low-risk maintainability issues |

---

## 6. Example Report Entries

### Example A: Quality gate failed because of Python type issues

```md
## Qodana Result

- Run Status: Failed
- Qodana Exit Code: 255
- Finding Code: QD-PY-001
- Inspection ID: PyTypeChecker
- Severity: High
- File: Backend/app/services/security_service.py
- Meaning: Wrong Python type used in a backend service call
- Action: Inspect function input/output types and align with actual schema/model usage
```

### Example B: Broken Vue component import

```md
## Qodana Result

- Run Status: Failed
- Qodana Exit Code: 255
- Finding Code: QD-VUE-003
- Inspection ID: VueMissingComponentImportInspection
- Severity: High
- File: Frontend/src/views/dashboard/ProfileView.vue
- Meaning: A component is used in the template but was not imported or registered
- Action: Import the component and verify the template name matches the registration
```

### Example C: Vulnerable dependency

```md
## Qodana Result

- Run Status: Failed
- Qodana Exit Code: 255
- Finding Code: QD-SEC-003
- Inspection ID: VulnerableLibrariesLocal
- Severity: Critical
- File: Frontend/package-lock.json
- Meaning: One or more dependencies have known security vulnerabilities
- Action: Upgrade or replace the affected dependency and retest impacted flows
```

---

## 7. How to Use This in Bug Reports

When a Qodana finding becomes a real tracked defect, copy these fields into:

- [bug-reports.md](C:/Users/gabri/OneDrive/Desktop/MOBILE/AURAV3/doc/technical/testing/bug-reports.md)
- GitHub Issues

Recommended fields:

```md
- Qodana Exit Code:
- Finding Code:
- Inspection ID:
- File:
- Severity:
- Summary:
- Reproduction or evidence:
```

---

## References

Official sources used:

- Qodana troubleshooting and exit codes: https://www.jetbrains.com/help/qodana/troubleshooting.html
- Qodana quality gate behavior: https://www.jetbrains.com/help/qodana/quality-gate.html
- Qodana code inspections: https://www.jetbrains.com/help/qodana/code-inspections.html
- Inspectopedia overview: https://www.jetbrains.com/help/qodana/inspectopedia.html
