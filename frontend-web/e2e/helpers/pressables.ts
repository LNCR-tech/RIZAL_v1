import { expect, test as playwrightTest, type Page } from "@playwright/test";
import { waitForBootOverlayToClear } from "./auth";

const PRESSABLE_SELECTOR = [
  "button",
  "a[href]",
  "[role='button']",
  "[role='link']",
  "[role='switch']",
  "[role='tab']",
].join(", ");

const RISKY_LABEL_PATTERN =
  /\b(delete|remove|reset|archive|deactivate|activate|approve|reject|retention|dispatch|publish|save|submit|send|confirm|upload|download|export|retry|try again|check in|check-in|sign out|sign-out|log out|logout|go back|back to|google|learn more|use current location|open location|copy conversation|delete conversation|talk to|aura ai|chat)\b/i;

const NON_APP_HREF_PATTERN = /^(mailto:|tel:|javascript:)/i;
const REPEATED_CALENDAR_LABEL_PATTERN = /^\d{1,2}(?:\s+\d+)?$/;

export type PressableRoute = {
  name: string;
  path: string;
};

type RouteSourceHint = {
  pattern: RegExp;
  files: string[];
};

type PressableCandidate = {
  domIndex: number;
  label: string;
  tagName: string;
  id: string;
  className: string;
  name: string;
  role: string;
  type: string;
  href: string;
  target: string;
  testId: string;
  ariaExpanded: string | null;
  ariaPressed: string | null;
  isNavigation: boolean;
  cssPath: string;
  outerHTML: string;
  signature: string;
};

type PageEffectSnapshot = {
  url: string;
  title: string;
  bodyTextHash: number;
  visibleTextLength: number;
  visibleControlCount: number;
  dialogLikeCount: number;
  menuLikeCount: number;
  toastLikeCount: number;
  expandedCount: number;
  pressedCount: number;
  selectedCount: number;
  checkedCount: number;
  openDetailsCount: number;
  formControlStateHash: number;
  activeLikeClassHash: number;
  clickedElementHash: number;
  clickedElementVisible: boolean;
};

const ROUTER_SOURCE_FILE = "frontend-web/src/router/index.js";

const ROUTE_SOURCE_HINTS: RouteSourceHint[] = [
  { pattern: /^\/$/, files: ["frontend-web/src/views/desktop/auth/LoginView.vue", "frontend-web/src/views/mobile/auth/LoginView.vue"] },
  { pattern: /^\/forgot-password$/, files: ["frontend-web/src/views/desktop/auth/ForgotPasswordView.vue", "frontend-web/src/views/auth/ForgotPasswordView.vue"] },

  { pattern: /^\/(?:exposed\/)?dashboard\/schedule\/[^/]+\/attendance$/, files: ["frontend-web/src/views/dashboard/AttendanceView.vue"] },
  { pattern: /^\/(?:exposed\/)?dashboard\/schedule\/[^/]+$/, files: ["frontend-web/src/views/dashboard/EventDetailView.vue"] },
  { pattern: /^\/(?:exposed\/)?dashboard\/profile\/security$/, files: ["frontend-web/src/views/dashboard/ProfileSecurityView.vue"] },
  { pattern: /^\/(?:exposed\/)?dashboard\/profile$/, files: ["frontend-web/src/views/dashboard/ProfileView.vue"] },
  { pattern: /^\/(?:exposed\/)?dashboard\/schedule$/, files: ["frontend-web/src/views/dashboard/ScheduleView.vue"] },
  { pattern: /^\/(?:exposed\/)?dashboard\/analytics$/, files: ["frontend-web/src/views/dashboard/AnalyticsView.vue"] },
  { pattern: /^\/(?:exposed\/)?dashboard\/gather\/attendance$/, files: ["frontend-web/src/views/mobile/dashboard/GatherAttendanceView.vue"] },
  { pattern: /^\/(?:exposed\/)?dashboard\/gather$/, files: ["frontend-web/src/views/dashboard/GatherWelcomeView.vue"] },
  { pattern: /^\/(?:exposed\/)?dashboard$/, files: ["frontend-web/src/views/dashboard/HomeView.vue"] },

  { pattern: /^\/(?:exposed\/)?workspace\/users\/department\/[^/]+\/program\/[^/]+$/, files: ["frontend-web/src/views/dashboard/SchoolItProgramStudentsView.vue"] },
  { pattern: /^\/(?:exposed\/)?workspace\/users\/department\/[^/]+$/, files: ["frontend-web/src/views/dashboard/SchoolItDepartmentProgramsView.vue"] },
  { pattern: /^\/(?:exposed\/)?workspace\/users\/import$/, files: ["frontend-web/src/views/dashboard/SchoolItImportStudentsView.vue"] },
  { pattern: /^\/(?:exposed\/)?workspace\/users\/unassigned$/, files: ["frontend-web/src/views/dashboard/SchoolItUnassignedStudentsView.vue"] },
  { pattern: /^\/(?:exposed\/)?workspace\/student-council$/, files: ["frontend-web/src/views/dashboard/SchoolItStudentCouncilView.vue"] },
  { pattern: /^\/(?:exposed\/)?workspace\/schedule\/monitor$/, files: ["frontend-web/src/views/dashboard/SchoolItAttendanceMonitorView.vue"] },
  { pattern: /^\/(?:exposed\/)?workspace\/schedule\/reports$/, files: ["frontend-web/src/views/dashboard/SchoolItEventReportsView.vue"] },
  { pattern: /^\/(?:exposed\/)?workspace\/schedule\/[^/]+$/, files: ["frontend-web/src/views/dashboard/EventDetailView.vue"] },
  { pattern: /^\/(?:exposed\/)?workspace\/schedule$/, files: ["frontend-web/src/views/dashboard/SchoolItScheduleView.vue"] },
  { pattern: /^\/workspace\/profile$/, files: ["frontend-web/src/views/dashboard/ProfileView.vue"] },
  { pattern: /^\/exposed\/workspace\/profile$/, files: ["frontend-web/src/views/dashboard/WorkspacePlaceholderView.vue"] },
  { pattern: /^\/(?:exposed\/)?workspace\/settings$/, files: ["frontend-web/src/views/dashboard/SchoolItSettingsView.vue"] },
  { pattern: /^\/(?:exposed\/)?workspace\/users$/, files: ["frontend-web/src/views/dashboard/SchoolItUsersView.vue"] },
  { pattern: /^\/(?:exposed\/)?workspace$/, files: ["frontend-web/src/views/dashboard/SchoolItHomeView.vue"] },

  { pattern: /^\/(?:exposed\/)?governance\/events\/[^/]+$/, files: ["frontend-web/src/views/dashboard/EventDetailView.vue"] },
  { pattern: /^\/(?:exposed\/)?governance\/members$/, files: ["frontend-web/src/views/dashboard/SgMembersView.vue"] },
  { pattern: /^\/(?:exposed\/)?governance\/create-unit$/, files: ["frontend-web/src/views/dashboard/SgCreateUnitView.vue"] },
  { pattern: /^\/(?:exposed\/)?governance\/gather\/attendance$/, files: ["frontend-web/src/views/mobile/dashboard/GatherAttendanceView.vue"] },
  { pattern: /^\/(?:exposed\/)?governance\/gather$/, files: ["frontend-web/src/views/dashboard/GatherWelcomeView.vue"] },
  { pattern: /^\/(?:exposed\/)?governance(?:\/(?:students|admin|events))?$/, files: ["frontend-web/src/views/dashboard/GovernanceWorkspaceView.vue", "frontend-web/src/components/events/EventEditorSheet.vue"] },

  { pattern: /^\/(?:exposed\/)?admin(?:\/(?:schools|accounts|oversight|profile))?$/, files: ["frontend-web/src/views/dashboard/AdminWorkspaceView.vue"] },
];

export const PREVIEW_DASHBOARD_ROUTES: PressableRoute[] = [
  { name: "login", path: "/" },
  { name: "forgot password", path: "/forgot-password" },
  { name: "student home preview", path: "/exposed/dashboard" },
  { name: "student schedule preview", path: "/exposed/dashboard/schedule" },
  { name: "student event detail preview", path: "/exposed/dashboard/schedule/1" },
  { name: "student attendance preview", path: "/exposed/dashboard/schedule/1/attendance" },
  { name: "student analytics preview", path: "/exposed/dashboard/analytics" },
  { name: "student profile preview", path: "/exposed/dashboard/profile" },
  { name: "student profile security preview", path: "/exposed/dashboard/profile/security" },
  { name: "gather preview", path: "/exposed/dashboard/gather" },
  { name: "gather attendance preview", path: "/exposed/dashboard/gather/attendance" },
];

export const PREVIEW_WORKSPACE_ROUTES: PressableRoute[] = [
  { name: "workspace home preview", path: "/exposed/workspace" },
  { name: "workspace users preview", path: "/exposed/workspace/users" },
  { name: "workspace import preview", path: "/exposed/workspace/users/import" },
  { name: "workspace department preview", path: "/exposed/workspace/users/department/1" },
  { name: "workspace program preview", path: "/exposed/workspace/users/department/1/program/1" },
  { name: "workspace unassigned preview", path: "/exposed/workspace/users/unassigned" },
  { name: "workspace student council preview", path: "/exposed/workspace/student-council" },
  { name: "workspace schedule preview", path: "/exposed/workspace/schedule" },
  { name: "workspace monitor preview", path: "/exposed/workspace/schedule/monitor" },
  { name: "workspace reports preview", path: "/exposed/workspace/schedule/reports" },
  { name: "workspace event detail preview", path: "/exposed/workspace/schedule/1" },
  { name: "workspace settings preview", path: "/exposed/workspace/settings" },
  { name: "workspace profile preview", path: "/exposed/workspace/profile" },
];

export const PREVIEW_GOVERNANCE_ADMIN_ROUTES: PressableRoute[] = [
  { name: "governance home preview", path: "/exposed/governance" },
  { name: "governance students preview", path: "/exposed/governance/students" },
  { name: "governance admin preview", path: "/exposed/governance/admin" },
  { name: "governance members preview", path: "/exposed/governance/members" },
  { name: "governance events preview", path: "/exposed/governance/events" },
  { name: "governance event detail preview", path: "/exposed/governance/events/1" },
  { name: "governance create unit preview", path: "/exposed/governance/create-unit" },
  { name: "governance gather preview", path: "/exposed/governance/gather" },
  { name: "governance gather attendance preview", path: "/exposed/governance/gather/attendance" },
  { name: "admin home preview", path: "/exposed/admin" },
  { name: "admin schools preview", path: "/exposed/admin/schools" },
  { name: "admin accounts preview", path: "/exposed/admin/accounts" },
  { name: "admin oversight preview", path: "/exposed/admin/oversight" },
  { name: "admin profile preview", path: "/exposed/admin/profile" },
];

export const AUTHENTICATED_STUDENT_ROUTES: PressableRoute[] = [
  { name: "student home", path: "/dashboard" },
  { name: "student schedule", path: "/dashboard/schedule" },
  { name: "student analytics", path: "/dashboard/analytics" },
  { name: "student profile", path: "/dashboard/profile" },
  { name: "student gather", path: "/dashboard/gather" },
];

export const AUTHENTICATED_CAMPUS_ROUTES: PressableRoute[] = [
  { name: "campus workspace home", path: "/workspace" },
  { name: "campus users", path: "/workspace/users" },
  { name: "campus import", path: "/workspace/users/import" },
  { name: "campus student council", path: "/workspace/student-council" },
  { name: "campus schedule", path: "/workspace/schedule" },
  { name: "campus monitor", path: "/workspace/schedule/monitor" },
  { name: "campus reports", path: "/workspace/schedule/reports" },
  { name: "campus settings", path: "/workspace/settings" },
  { name: "campus profile", path: "/workspace/profile" },
];

export function getRouteSourceFiles(route: PressableRoute) {
  const pathname = normalizeRoutePath(route.path);
  const match = ROUTE_SOURCE_HINTS.find((hint) => hint.pattern.test(pathname));
  const files = match?.files?.length ? match.files : [];
  return [...new Set([...files, ROUTER_SOURCE_FILE])];
}

export function getRouteSourceLabel(route: PressableRoute) {
  const labels = getRouteSourceFiles(route)
    .filter((file) => file !== ROUTER_SOURCE_FILE)
    .map((file) => file.split("/").pop() || file)
    .filter((label, index, allLabels) => allLabels.indexOf(label) === index);

  return labels.join(" + ") || ROUTER_SOURCE_FILE;
}

function normalizeRoutePath(path: string) {
  try {
    return new URL(path, "http://127.0.0.1").pathname.replace(/\/+$/, "") || "/";
  } catch {
    return String(path || "").replace(/[?#].*$/, "").replace(/\/+$/, "") || "/";
  }
}

export async function navigateAndAssertUsable(page: Page, route: PressableRoute) {
  const response = await page.goto(route.path, { waitUntil: "domcontentloaded" });
  const status = response?.status() ?? 0;
  expect(status, `${route.name} returned HTTP ${status}`).toBeGreaterThanOrEqual(200);
  expect(status, `${route.name} returned HTTP ${status}`).toBeLessThan(400);

  await page.waitForLoadState("networkidle", { timeout: 15_000 }).catch(() => null);
  await waitForBootOverlayToClear(page);
  await assertPageStillUsable(page, route.name);
}

export async function assertPageStillUsable(page: Page, contextLabel: string) {
  await expect(page.locator("body"), `${contextLabel}: body should remain visible`).toBeVisible();
  await expect(page.locator(".app-fatal"), `${contextLabel}: fatal app screen should not show`).toHaveCount(0);
  await expect(page.locator(".not-found-view__title"), `${contextLabel}: should not land on Not Found`).toHaveCount(0);
}

export async function exerciseSafePressablesOnRoute(page: Page, route: PressableRoute) {
  await navigateAndAssertUsable(page, route);
  const initialCandidates = await collectSafePressables(page);
  const expectedPathname = new URL(route.path, page.url()).pathname;

  for (const initialCandidate of initialCandidates) {
    const currentCandidates = await collectSafePressables(page);
    const candidate =
      currentCandidates.find((item) => item.signature === initialCandidate.signature) ||
      currentCandidates.find((item) => item.domIndex === initialCandidate.domIndex);

    if (!candidate) continue;

    await playwrightTest.step(`press ${route.name}: ${candidate.label || candidate.testId || candidate.cssPath}`, async () => {
      await testPressableCandidate(page, route, candidate);
    });

    const currentPathname = new URL(page.url()).pathname;
    if (currentPathname !== expectedPathname) {
      await navigateAndAssertUsable(page, route);
    } else {
      await page.keyboard.press("Escape").catch(() => null);
      await page.waitForTimeout(100);
    }
  }
}

async function collectSafePressables(page: Page): Promise<PressableCandidate[]> {
  const candidates = await page.evaluate((selector) => {
    const elements = Array.from(document.querySelectorAll(selector));

    const isVisible = (element: Element) => {
      if (!(element instanceof HTMLElement)) return false;
      if (element.closest("[aria-hidden='true'], .sr-only")) return false;

      const style = window.getComputedStyle(element);
      const rect = element.getBoundingClientRect();
      if (
        style.visibility !== "hidden" &&
        style.display !== "none" &&
        Number(style.opacity || "1") > 0 &&
        rect.width > 0 &&
        rect.height > 0
      ) {
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;
        const topElement = document.elementFromPoint(centerX, centerY);
        return Boolean(topElement && (element === topElement || element.contains(topElement)));
      }

      return false;
    };

    const readLabel = (element: Element) => {
      if (!(element instanceof HTMLElement)) return "";
      const ariaLabel = element.getAttribute("aria-label") || "";
      const title = element.getAttribute("title") || "";
      const value = element instanceof HTMLInputElement ? element.value : "";
      const href = element instanceof HTMLAnchorElement ? element.href : "";
      return (ariaLabel || title || element.innerText || value || href || "").trim().replace(/\s+/g, " ");
    };

    const isGlobalNavigation = (element: Element) => {
      const navAncestor = element.closest("nav, aside");
      if (!navAncestor) return false;

      const label = navAncestor.getAttribute("aria-label") || "";
      const className = navAncestor.getAttribute("class") || "";
      return /navigation|nav-rail|bottom-nav/i.test(`${label} ${className}`);
    };

    const escapeCssIdent = (value: string) => {
      if (window.CSS?.escape) return window.CSS.escape(value);
      return value.replace(/[^a-zA-Z0-9_-]/g, "\\$&");
    };

    const buildCssPath = (element: HTMLElement) => {
      const parts: string[] = [];
      let current: HTMLElement | null = element;

      while (current && current !== document.body && parts.length < 6) {
        const tag = current.tagName.toLowerCase();
        if (current.id) {
          parts.unshift(`${tag}#${escapeCssIdent(current.id)}`);
          break;
        }

        const parent = current.parentElement;
        if (!parent) {
          parts.unshift(tag);
          break;
        }

        const sameTagSiblings = Array.from(parent.children)
          .filter((child) => child.tagName === current?.tagName);
        const position = sameTagSiblings.indexOf(current) + 1;
        parts.unshift(`${tag}:nth-of-type(${position})`);
        current = parent;
      }

      return parts.join(" > ");
    };

    return elements
      .map((element, domIndex) => {
        if (!(element instanceof HTMLElement)) return null;
        if (!isVisible(element)) return null;

        const disabled =
          element.hasAttribute("disabled") ||
          element.getAttribute("aria-disabled") === "true";
        if (disabled) return null;

        const href = element instanceof HTMLAnchorElement ? element.href : "";
        const candidate = {
          domIndex,
          label: readLabel(element),
          tagName: element.tagName.toLowerCase(),
          id: element.id || "",
          className: typeof element.className === "string" ? element.className : "",
          name: element.getAttribute("name") || "",
          role: element.getAttribute("role") || "",
          type: element.getAttribute("type") || "",
          href,
          target: element.getAttribute("target") || "",
          testId: element.getAttribute("data-testid") || "",
          ariaExpanded: element.getAttribute("aria-expanded"),
          ariaPressed: element.getAttribute("aria-pressed"),
          isNavigation: isGlobalNavigation(element),
          cssPath: buildCssPath(element),
          outerHTML: element.outerHTML.replace(/\s+/g, " ").trim().slice(0, 800),
        };

        return {
          ...candidate,
          signature: [
            candidate.domIndex,
            candidate.tagName,
            candidate.role,
            candidate.type,
            candidate.label,
            candidate.href,
            candidate.testId,
            candidate.cssPath,
          ].join("|"),
        };
      })
      .filter(Boolean);
  }, PRESSABLE_SELECTOR);

  return (candidates as PressableCandidate[]).filter((candidate) => {
    if (!candidate.label && !candidate.testId) return false;
    if (candidate.isNavigation) return false;
    if (REPEATED_CALENDAR_LABEL_PATTERN.test(candidate.label)) return false;
    if (candidate.type.toLowerCase() === "submit") return false;
    if (candidate.target === "_blank") return false;
    if (NON_APP_HREF_PATTERN.test(candidate.href)) return false;
    if (candidate.href) {
      const hrefUrl = new URL(candidate.href);
      const pageUrl = new URL(page.url());
      if (hrefUrl.origin !== pageUrl.origin) return false;
      if (hrefUrl.pathname === pageUrl.pathname && !hrefUrl.hash) return false;
    }
    return !RISKY_LABEL_PATTERN.test(`${candidate.label} ${candidate.testId}`);
  });
}

async function testPressableCandidate(
  page: Page,
  route: PressableRoute,
  candidate: PressableCandidate,
) {
  const beforeUrl = new URL(page.url());
  const locator = page.locator(PRESSABLE_SELECTOR).nth(candidate.domIndex);
  const description = `${route.name}: ${candidate.label || candidate.testId}`;

  await expect(locator, `${description} should still be visible before clicking`).toBeVisible();
  const beforeEffect = await readPageEffectSnapshot(page, candidate);
  await locator.click({ timeout: 7_500 });
  await page.waitForLoadState("domcontentloaded", { timeout: 10_000 }).catch(() => null);
  await page.waitForLoadState("networkidle", { timeout: 10_000 }).catch(() => null);
  await page.waitForTimeout(250);

  await assertPageStillUsable(page, description);
  await assertExpectedOutcome(page, locator, candidate, beforeUrl, beforeEffect, route, description);
}

async function assertExpectedOutcome(
  page: Page,
  locator: ReturnType<Page["locator"]>,
  candidate: PressableCandidate,
  beforeUrl: URL,
  beforeEffect: PageEffectSnapshot,
  route: PressableRoute,
  description: string,
) {
  if (candidate.href) {
    const targetUrl = new URL(candidate.href);
    if (targetUrl.pathname !== beforeUrl.pathname) {
      await expect(page, `${description} should navigate to its own internal href`).toHaveURL((url) => (
        url.pathname === targetUrl.pathname
      ));
      return;
    }
  }

  const afterUrl = new URL(page.url());
  const stayedOnSamePath = afterUrl.pathname === beforeUrl.pathname;

  if (stayedOnSamePath && candidate.ariaExpanded != null) {
    const nextExpanded = await locator.getAttribute("aria-expanded").catch(() => null);
    const hasDialogOrMenu = await page
      .locator("[role='dialog'], [role='menu'], .governance-create-sheet__backdrop, .edit-overlay")
      .count();
    expect(
      nextExpanded !== candidate.ariaExpanded || hasDialogOrMenu > 0,
      `${description} should toggle expanded state or reveal a menu/dialog`,
    ).toBeTruthy();
    return;
  }

  if (stayedOnSamePath && candidate.ariaPressed != null) {
    const nextPressed = await locator.getAttribute("aria-pressed").catch(() => null);
    expect(nextPressed, `${description} should toggle pressed state`).not.toBe(candidate.ariaPressed);
    return;
  }

  const afterEffect = await readPageEffectSnapshot(page, candidate);
  const changedFields = describeEffectChanges(beforeEffect, afterEffect);
  if (changedFields.length > 0) {
    return;
  }

  throw new Error(buildNoOpPressableError({
    route,
    candidate,
    beforeEffect,
    afterEffect,
  }));
}

async function readPageEffectSnapshot(
  page: Page,
  candidate: PressableCandidate,
): Promise<PageEffectSnapshot> {
  return page.evaluate(({ cssPath }) => {
    const hashText = (value: string) => {
      let hash = 0;
      for (let index = 0; index < value.length; index += 1) {
        hash = ((hash << 5) - hash + value.charCodeAt(index)) | 0;
      }
      return hash;
    };

    const isVisible = (element: Element | null) => {
      if (!(element instanceof HTMLElement)) return false;
      const style = window.getComputedStyle(element);
      const rect = element.getBoundingClientRect();
      return (
        style.visibility !== "hidden" &&
        style.display !== "none" &&
        Number(style.opacity || "1") > 0 &&
        rect.width > 0 &&
        rect.height > 0
      );
    };

    const visibleText = Array.from(document.body.querySelectorAll("body *"))
      .filter(isVisible)
      .map((element) => (element.textContent || "").replace(/\s+/g, " ").trim())
      .filter(Boolean)
      .join("|")
      .slice(0, 50_000);

    const activeLikeClassText = Array.from(document.querySelectorAll("[class]"))
      .filter((element) => /active|open|selected|expanded|visible|show|shown|current|editing|creating|expanded/i.test(String(element.getAttribute("class") || "")))
      .map((element) => `${element.tagName.toLowerCase()}.${String(element.getAttribute("class") || "").trim()}`)
      .join("|");

    const formControlStateText = Array.from(document.querySelectorAll("input, select, textarea"))
      .filter(isVisible)
      .map((element) => {
        if (element instanceof HTMLInputElement) {
          return [
            "input",
            element.type,
            element.name,
            element.placeholder,
            element.value,
            element.checked ? "checked" : "unchecked",
            element.disabled ? "disabled" : "enabled",
          ].join(":");
        }

        if (element instanceof HTMLSelectElement) {
          return [
            "select",
            element.name,
            element.value,
            element.selectedIndex,
            element.disabled ? "disabled" : "enabled",
          ].join(":");
        }

        if (element instanceof HTMLTextAreaElement) {
          return [
            "textarea",
            element.name,
            element.placeholder,
            element.value,
            element.disabled ? "disabled" : "enabled",
          ].join(":");
        }

        return "";
      })
      .join("|");

    const clickedElement = cssPath ? document.querySelector(cssPath) : null;
    const clickedElementText = clickedElement
      ? [
          clickedElement.tagName.toLowerCase(),
          clickedElement.getAttribute("id") || "",
          clickedElement.getAttribute("class") || "",
          clickedElement.getAttribute("aria-expanded") || "",
          clickedElement.getAttribute("aria-pressed") || "",
          clickedElement.getAttribute("aria-selected") || "",
          clickedElement.getAttribute("aria-checked") || "",
          clickedElement.textContent || "",
        ].join("|")
      : "";

    return {
      url: window.location.href,
      title: document.title || "",
      bodyTextHash: hashText(visibleText),
      visibleTextLength: visibleText.length,
      visibleControlCount: Array.from(document.querySelectorAll("button, a[href], [role='button'], [role='link'], [role='switch'], [role='tab']")).filter(isVisible).length,
      dialogLikeCount: Array.from(document.querySelectorAll("[role='dialog'], dialog, .modal, .sheet, .drawer, .edit-overlay, .governance-create-sheet__backdrop")).filter(isVisible).length,
      menuLikeCount: Array.from(document.querySelectorAll("[role='menu'], .menu, .popover, .dropdown, [popover]")).filter(isVisible).length,
      toastLikeCount: Array.from(document.querySelectorAll("[role='alert'], .toast, .notification, .alert, .snackbar")).filter(isVisible).length,
      expandedCount: document.querySelectorAll("[aria-expanded='true']").length,
      pressedCount: document.querySelectorAll("[aria-pressed='true']").length,
      selectedCount: document.querySelectorAll("[aria-selected='true'], .is-selected, .selected").length,
      checkedCount: document.querySelectorAll("[aria-checked='true'], input:checked").length,
      openDetailsCount: document.querySelectorAll("details[open]").length,
      formControlStateHash: hashText(formControlStateText),
      activeLikeClassHash: hashText(activeLikeClassText),
      clickedElementHash: hashText(clickedElementText),
      clickedElementVisible: isVisible(clickedElement),
    };
  }, { cssPath: candidate.cssPath });
}

function describeEffectChanges(
  beforeEffect: PageEffectSnapshot,
  afterEffect: PageEffectSnapshot,
) {
  const changedFields: string[] = [];
  for (const key of Object.keys(beforeEffect) as Array<keyof PageEffectSnapshot>) {
    if (beforeEffect[key] !== afterEffect[key]) {
      changedFields.push(String(key));
    }
  }
  return changedFields;
}

function buildNoOpPressableError({
  route,
  candidate,
  beforeEffect,
  afterEffect,
}: {
  route: PressableRoute;
  candidate: PressableCandidate;
  beforeEffect: PageEffectSnapshot;
  afterEffect: PageEffectSnapshot;
}) {
  const sourceFiles = getRouteSourceFiles(route);

  return [
    "No detectable UI result after clicking pressable.",
    "",
    `Route: ${route.name} (${route.path})`,
    `URL before: ${beforeEffect.url}`,
    `URL after: ${afterEffect.url}`,
    "",
    "Likely source files:",
    ...sourceFiles.map((file) => `- ${file}`),
    "",
    "Pressable:",
    `- label: ${candidate.label || "(no label)"}`,
    `- tag: ${candidate.tagName}`,
    `- role: ${candidate.role || "(none)"}`,
    `- type: ${candidate.type || "(none)"}`,
    `- id: ${candidate.id || "(none)"}`,
    `- class: ${candidate.className || "(none)"}`,
    `- name: ${candidate.name || "(none)"}`,
    `- data-testid: ${candidate.testId || "(none)"}`,
    `- domIndex among pressables: ${candidate.domIndex}`,
    `- cssPath: ${candidate.cssPath || "(none)"}`,
    `- html: ${candidate.outerHTML || "(unavailable)"}`,
    "",
    "Why this failed:",
    "The click did not change URL, visible text/state, dialog/menu/toast counts, common active/open/selected classes, or the clicked element snapshot.",
    "",
    "How to locate it:",
    "- Start with the likely source file above.",
    "- Search for the label, aria-label, class, data-testid, or nearby text shown in the Pressable section.",
    "- If the element comes from a shared child component, follow that component import from the likely source file.",
    "",
    "Fix options:",
    "- Wire this control to a real user-visible action.",
    "- If it opens a panel/menu, add aria-expanded or a visible dialog/menu assertion.",
    "- If it toggles a value, add aria-pressed, aria-selected, aria-checked, or a specific workflow test.",
    "- If it is intentionally inactive, disable it or remove it from the UI.",
  ].join("\n");
}
