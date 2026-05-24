import { expect, test } from "../base";
import { gotoLoginAndWait } from "../helpers/auth";
import { navigateAndAssertUsable } from "../helpers/pressables";

type QualityRoute = {
  name: string;
  path: string;
  source: string;
};

const QUALITY_ROUTES: QualityRoute[] = [
  { name: "student dashboard preview", path: "/exposed/dashboard", source: "HomeView.vue" },
  { name: "student schedule preview", path: "/exposed/dashboard/schedule", source: "ScheduleView.vue" },
  { name: "student profile preview", path: "/exposed/dashboard/profile", source: "ProfileView.vue" },
  { name: "workspace schedule preview", path: "/exposed/workspace/schedule", source: "SchoolItScheduleView.vue" },
  { name: "governance events preview", path: "/exposed/governance/events", source: "GovernanceWorkspaceView.vue" },
];

const RESPONSIVE_VIEWPORTS = [
  { name: "mobile", width: 390, height: 844 },
  { name: "tablet", width: 768, height: 1024 },
  { name: "desktop", width: 1440, height: 900 },
];

async function collectUnnamedVisiblePressables(page: import("@playwright/test").Page) {
  return page.evaluate(() => {
    function isVisible(element: Element) {
      const rect = element.getBoundingClientRect();
      const style = window.getComputedStyle(element);
      return (
        rect.width > 0 &&
        rect.height > 0 &&
        style.display !== "none" &&
        style.visibility !== "hidden" &&
        !element.closest("[aria-hidden='true']")
      );
    }

    function textById(id: string) {
      return id
        .split(/\s+/)
        .map((part) => document.getElementById(part)?.textContent?.trim() || "")
        .filter(Boolean)
        .join(" ");
    }

    function accessibleName(element: Element) {
      const ariaLabel = element.getAttribute("aria-label") || "";
      const ariaLabelledBy = element.getAttribute("aria-labelledby") || "";
      const title = element.getAttribute("title") || "";
      const value = element.getAttribute("value") || "";
      const innerText = (element as HTMLElement).innerText || element.textContent || "";
      return [
        ariaLabel,
        ariaLabelledBy ? textById(ariaLabelledBy) : "",
        title,
        value,
        innerText,
      ]
        .map((part) => String(part || "").replace(/\s+/g, " ").trim())
        .find(Boolean) || "";
    }

    return [...document.querySelectorAll("button, a[href], [role='button'], [role='link']")]
      .filter(isVisible)
      .map((element, index) => ({
        index,
        tag: element.tagName.toLowerCase(),
        role: element.getAttribute("role") || "",
        className: element.getAttribute("class") || "",
        html: element.outerHTML.replace(/\s+/g, " ").slice(0, 220),
        name: accessibleName(element),
      }))
      .filter((entry) => !entry.name);
  });
}

async function assertNoHorizontalOverflow(page: import("@playwright/test").Page) {
  const result = await page.evaluate(() => {
    const documentWidth = Math.max(
      document.body.scrollWidth,
      document.documentElement.scrollWidth,
    );
    const overflowPx = Math.max(0, documentWidth - window.innerWidth);
    return {
      overflowPx,
      documentWidth,
      viewportWidth: window.innerWidth,
    };
  });

  expect(
    result.overflowPx,
    `Horizontal overflow ${result.overflowPx}px at ${result.viewportWidth}px viewport`,
  ).toBeLessThanOrEqual(8);
}

test.describe("UI quality automation", () => {
  test("visible buttons and links expose accessible names on key routes", async ({ page }) => {
    // This UI/UX test catches icon-only or custom clickable controls that screen readers cannot name.
    await gotoLoginAndWait(page);
    let unnamed = await collectUnnamedVisiblePressables(page);
    expect(unnamed, `Unnamed pressables on login route: ${JSON.stringify(unnamed, null, 2)}`).toEqual([]);

    for (const route of QUALITY_ROUTES) {
      await navigateAndAssertUsable(page, route);
      unnamed = await collectUnnamedVisiblePressables(page);
      expect(
        unnamed,
        `Unnamed pressables on ${route.name} [${route.source}]: ${JSON.stringify(unnamed, null, 2)}`,
      ).toEqual([]);
    }
  });

  test("key routes do not create horizontal overflow across common viewport sizes", async ({ page }) => {
    // This UI/UX test catches layout regressions where content spills sideways on mobile/tablet/desktop.
    test.setTimeout(180_000);

    for (const viewport of RESPONSIVE_VIEWPORTS) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });

      await gotoLoginAndWait(page);
      await assertNoHorizontalOverflow(page);

      for (const route of QUALITY_ROUTES) {
        await navigateAndAssertUsable(page, route);
        await assertNoHorizontalOverflow(page);
      }
    }
  });
});
