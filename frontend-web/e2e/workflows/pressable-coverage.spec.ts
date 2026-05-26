import { test } from "../base";
import { E2E_USERS, loginAs } from "../helpers/auth";
import {
  AUTHENTICATED_CAMPUS_ROUTES,
  AUTHENTICATED_STUDENT_ROUTES,
  PREVIEW_DASHBOARD_ROUTES,
  PREVIEW_GOVERNANCE_ADMIN_ROUTES,
  PREVIEW_WORKSPACE_ROUTES,
  type PressableRoute,
  exerciseSafePressablesOnRoute,
  getRouteSourceLabel,
} from "../helpers/pressables";

function definePreviewPressableTests(groupName: string, routes: PressableRoute[]) {
  test.describe(groupName, () => {
    for (const route of routes) {
      test(`${route.name} [${getRouteSourceLabel(route)}] keeps every collected safe pressable usable`, async ({ page }) => {
        // This route-level test clicks every safe pressable collected on this page, with no per-route cap.
        test.setTimeout(180_000);
        await exerciseSafePressablesOnRoute(page, route);
      });
    }
  });
}

function defineAuthenticatedPressableTests(
  groupName: string,
  routes: PressableRoute[],
  user: { email: string; password: string },
) {
  test.describe(groupName, () => {
    for (const route of routes) {
      test(`${route.name} [${getRouteSourceLabel(route)}] keeps every collected safe pressable usable`, async ({ page }) => {
        // This authenticated route-level test logs in, opens the route, and clicks every collected safe pressable.
        test.skip(
          process.env.PLAYWRIGHT_MOCK_AUTH !== "true",
          "Authenticated broad pressable coverage needs Playwright mock auth.",
        );
        test.setTimeout(180_000);

        await loginAs(page, user);
        await exerciseSafePressablesOnRoute(page, route);
      });
    }
  });
}

// These preview tests cover public student-dashboard pages and login/reset controls without a backend.
definePreviewPressableTests("preview dashboard safe pressables", PREVIEW_DASHBOARD_ROUTES);

// These preview tests cover School IT pages and their page-local safe controls without a backend.
definePreviewPressableTests("preview workspace safe pressables", PREVIEW_WORKSPACE_ROUTES);

// These preview tests cover governance/admin pages and their page-local safe controls without a backend.
definePreviewPressableTests("preview governance and admin safe pressables", PREVIEW_GOVERNANCE_ADMIN_ROUTES);

// These tests cover authenticated student pages using the Playwright mock-auth layer.
defineAuthenticatedPressableTests(
  "student authenticated safe pressables",
  AUTHENTICATED_STUDENT_ROUTES,
  E2E_USERS.student,
);

// These tests cover authenticated campus-admin pages using the Playwright mock-auth layer.
defineAuthenticatedPressableTests(
  "campus admin authenticated safe pressables",
  AUTHENTICATED_CAMPUS_ROUTES,
  E2E_USERS.campusAdmin,
);
