import { test as base } from "@playwright/test";

const parsedTestDelayMs = Number.parseInt(
  process.env.PLAYWRIGHT_TEST_DELAY_MS || "0",
  10,
);
const testDelayMs =
  Number.isFinite(parsedTestDelayMs) && parsedTestDelayMs > 0
    ? parsedTestDelayMs
    : 0;
const mockAuthEnabled =
  (process.env.PLAYWRIGHT_MOCK_AUTH || "").trim().toLowerCase() === "true";
const mockAuthPassword = process.env.PLAYWRIGHT_MOCK_AUTH_PASSWORD || "TestPass123!";
const mockBackendBaseUrl =
  process.env.PLAYWRIGHT_BACKEND_BASE_URL ||
  process.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";

type MockSession = {
  email: string;
  roles: string[];
  userId: number;
  schoolId: number | null;
};

function normalizeEmail(value: string): string {
  return String(value || "").trim().toLowerCase();
}

function resolveRolesForEmail(email: string): string[] {
  const normalized = normalizeEmail(email);
  if (normalized.includes("campus_admin")) return ["campus_admin"];
  if (normalized.includes("school_admin")) return ["school_admin"];
  if (normalized.includes("admin")) return ["admin"];
  if (normalized.includes("ssg")) return ["ssg"];
  return ["student"];
}

function resolveSchoolContext(roles: string[]): { schoolId: number | null; schoolName: string | null } {
  const isGlobalAdmin = roles.includes("admin");
  if (isGlobalAdmin) {
    return { schoolId: null, schoolName: null };
  }
  return { schoolId: 1, schoolName: "Test University" };
}

function createTokenForEmail(email: string): string {
  const tokenSeed = normalizeEmail(email).replace(/[^a-z0-9]/g, "").slice(0, 20);
  return `mock-e2e-${tokenSeed || "token"}`;
}

function normalizeOrigin(value: string): string {
  try {
    return new URL(String(value || "").trim()).origin.toLowerCase();
  } catch {
    return "";
  }
}

const mockDepartments = [
  { id: 1, name: "College of Engineering", code: "COE", school_id: 1 },
  { id: 2, name: "College of Business", code: "COB", school_id: 1 },
];

const mockPrograms = [
  { id: 1, name: "BS Computer Science", code: "BSCS", school_id: 1, department_id: 1 },
  { id: 2, name: "BS Information Technology", code: "BSIT", school_id: 1, department_id: 1 },
];

const mockEvents = [
  {
    id: 1,
    name: "E2E Orientation",
    title: "E2E Orientation",
    description: "Mock event used by Playwright UI checks.",
    location_name: "Main Hall",
    start_time: "2026-05-23T09:00:00Z",
    end_time: "2026-05-23T11:00:00Z",
    status: "upcoming",
    school_id: 1,
    require_geofence: false,
    latitude: null,
    longitude: null,
    radius_meters: null,
    event_targets: [{ scope_type: "ALL" }],
  },
];

const mockAdminSchools = [
  {
    school_id: 1,
    id: 1,
    school_name: "Test University",
    school_code: "TEST-001",
    subscription_status: "trial",
    active_status: true,
    primary_color: "#162F65",
    secondary_color: "#2C5F9E",
    accent_color: "#000000",
  },
];

const mockSchoolItAccounts = [
  {
    id: 201,
    user_id: 201,
    email: "campus_admin@test.com",
    first_name: "Campus",
    last_name: "Admin",
    school_id: 1,
    school_name: "Test University",
    is_active: true,
    roles: ["campus_admin"],
  },
];

const mockGovernanceUnit = {
  id: 7001,
  governance_unit_id: 7001,
  unit_code: "SSG",
  unit_name: "Supreme Student Government",
  unit_type: "SSG",
  school_id: 1,
  is_active: true,
  permission_codes: ["manage_events", "manage_members", "assign_permissions"],
};

async function installMockAuthRoutes(page: import("@playwright/test").Page): Promise<void> {
  const sessions = new Map<string, MockSession>();
  const backendOrigin = normalizeOrigin(mockBackendBaseUrl);

  const isMockBackendRequest = (request: import("@playwright/test").Request): boolean => {
    if (!backendOrigin) return false;
    return normalizeOrigin(request.url()) === backendOrigin;
  };

  const readSessionFromRequest = (request: import("@playwright/test").Request): MockSession | null => {
    const authorization = request.headers()["authorization"] || request.headers()["Authorization"] || "";
    const parts = authorization.split(" ");
    const token = parts.length >= 2 ? parts[1].trim() : "";
    if (!token) return null;
    return sessions.get(token) || null;
  };

  const fulfillJson = async (
    route: import("@playwright/test").Route,
    payload: unknown,
    status = 200,
  ) => {
    await route.fulfill({
      status,
      contentType: "application/json",
      body: JSON.stringify(payload),
    });
  };

  await page.route("**/*", async (route) => {
    if (route.request().method().toUpperCase() !== "GET") {
      await route.fallback();
      return;
    }

    let url: URL;
    try {
      url = new URL(route.request().url());
    } catch {
      await route.fallback();
      return;
    }

    if (backendOrigin && url.origin.toLowerCase() !== backendOrigin) {
      await route.fallback();
      return;
    }

    const path = (url.pathname.replace(/\/+$/, "").toLowerCase() || "/");

    if (path === "/" || path === "") {
      await fulfillJson(route, { ok: true });
      return;
    }

    if (path === "/api/notifications/inbox/me") {
      await fulfillJson(route, []);
      return;
    }

    if (path === "/api/governance/access/me") {
      await fulfillJson(route, {
        user_id: readSessionFromRequest(route.request())?.userId ?? 1,
        school_id: 1,
        permission_codes: ["manage_events", "manage_members", "assign_permissions"],
        units: [mockGovernanceUnit],
        memberships: [mockGovernanceUnit],
      });
      return;
    }

    if (
      path === "/api/departments" ||
      path === "/departments"
    ) {
      await fulfillJson(route, mockDepartments);
      return;
    }

    if (
      path === "/api/programs" ||
      path === "/programs"
    ) {
      await fulfillJson(route, mockPrograms);
      return;
    }

    if (
      path === "/api/users" ||
      path === "/users"
    ) {
      await fulfillJson(route, []);
      return;
    }

    if (path === "/api/governance/units") {
      await fulfillJson(route, [mockGovernanceUnit]);
      return;
    }

    if (path === "/api/governance/students") {
      await fulfillJson(route, []);
      return;
    }

    if (path === "/attendance/summary") {
      await fulfillJson(route, {
        total_records: 0,
        present_count: 0,
        absent_count: 0,
        late_count: 0,
        attendance_rate: 0,
      });
      return;
    }

    if (path === "/api/governance/ssg/setup") {
      await fulfillJson(route, {
        unit: mockGovernanceUnit,
        members: [],
        candidates: [],
        elections: [],
        settings: null,
      });
      return;
    }

    if (path === "/api/governance/announcements/monitor") {
      await fulfillJson(route, []);
      return;
    }

    if (path === "/api/school/admin/list") {
      await fulfillJson(route, mockAdminSchools);
      return;
    }

    if (path === "/api/school/admin/school-it-accounts") {
      await fulfillJson(route, mockSchoolItAccounts);
      return;
    }

    if (path === "/api/audit-logs") {
      await fulfillJson(route, { data: [], total: 0, page: 1, total_pages: 1, limit: 25 });
      return;
    }

    if (path === "/api/notifications/logs") {
      await fulfillJson(route, []);
      return;
    }

    if (path === "/api/governance/settings/me") {
      await fulfillJson(route, {
        school_id: 1,
        allow_sg_event_creation: true,
        allow_org_event_creation: true,
        require_event_approval: false,
        retention_days: 365,
      });
      return;
    }

    if (path === "/api/governance/requests") {
      await fulfillJson(route, []);
      return;
    }

    if (/^\/api\/governance\/units\/\d+$/.test(path)) {
      await fulfillJson(route, mockGovernanceUnit);
      return;
    }

    if (/^\/api\/governance\/units\/\d+\/announcements$/.test(path)) {
      await fulfillJson(route, []);
      return;
    }

    await route.fallback();
  });

  await page.route(/\/(?:api\/)?token(?:\?.*)?$/i, async (route) => {
    if (!isMockBackendRequest(route.request())) {
      await route.fallback();
      return;
    }

    if (route.request().method().toUpperCase() !== "POST") {
      await route.fallback();
      return;
    }

    const form = new URLSearchParams(route.request().postData() || "");
    const email = normalizeEmail(form.get("username") || form.get("email") || "");
    const password = String(form.get("password") || "");

    if (!email || password !== mockAuthPassword) {
      await route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Incorrect email or password" }),
      });
      return;
    }

    const roles = resolveRolesForEmail(email);
    const userId = Math.max(1, (email.charCodeAt(0) || 1) + 100);
    const schoolContext = resolveSchoolContext(roles);
    const accessToken = createTokenForEmail(email);

    sessions.set(accessToken, {
      email,
      roles,
      userId,
      schoolId: schoolContext.schoolId,
    });

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        access_token: accessToken,
        token_type: "bearer",
        email,
        roles,
        user_id: userId,
        first_name: "E2E",
        last_name: "User",
        school_id: schoolContext.schoolId,
        school_name: schoolContext.schoolName,
        school_code: schoolContext.schoolId == null ? null : "TEST-001",
        logo_url: null,
        primary_color: "#162F65",
        secondary_color: "#2C5F9E",
        accent_color: "#000000",
        must_change_password: false,
        session_id: `sess-${userId}`,
        mfa_required: false,
        face_verification_required: false,
        face_reference_enrolled: true,
        face_verification_pending: false,
        is_admin: roles.includes("admin"),
      }),
    });
  });

  await page.route(/\/(?:api\/)?users\/me\/?$/i, async (route) => {
    if (!isMockBackendRequest(route.request())) {
      await route.fallback();
      return;
    }

    if (route.request().method().toUpperCase() !== "GET") {
      await route.fallback();
      return;
    }

    const session = readSessionFromRequest(route.request());
    if (!session) {
      await route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Not authenticated" }),
      });
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: session.userId,
        email: session.email,
        first_name: "E2E",
        middle_name: null,
        last_name: "User",
        is_active: true,
        school_id: session.schoolId,
        school_name: session.schoolId == null ? null : "Test University",
        school_code: session.schoolId == null ? null : "TEST-001",
        roles: session.roles,
        student_profile: session.roles.includes("student")
          ? {
              id: session.userId + 1000,
              user_id: session.userId,
              school_id: session.schoolId,
              student_id: "2026-0001",
              department_id: 1,
              program_id: 1,
              year_level: 2,
              attendances: [],
              is_face_registered: true,
              registration_complete: true,
              photo_url: null,
              avatar_url: null,
            }
          : null,
        avatar_url: null,
        must_change_password: false,
      }),
    });
  });

  await page.route(/\/api\/school(?:-settings)?\/me\/?$/i, async (route) => {
    if (!isMockBackendRequest(route.request())) {
      await route.fallback();
      return;
    }

    if (route.request().method().toUpperCase() !== "GET") {
      await route.fallback();
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        school_id: 1,
        school_name: "Test University",
        school_code: "TEST-001",
        logo_url: null,
        primary_color: "#162F65",
        secondary_color: "#2C5F9E",
        accent_color: "#000000",
        subscription_status: "trial",
        active_status: true,
        event_default_early_check_in_minutes: 30,
        event_default_late_threshold_minutes: 10,
        event_default_sign_out_grace_minutes: 15,
        event_default_sign_out_open_delay_minutes: 0,
      }),
    });
  });

  await page.route(/\/(?:api\/)?events\/?(?:\?.*)?$/i, async (route) => {
    if (!isMockBackendRequest(route.request())) {
      await route.fallback();
      return;
    }

    if (route.request().method().toUpperCase() !== "GET") {
      await route.fallback();
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockEvents),
    });
  });

  await page.route(/\/(?:api\/)?events\/\d+\/?(?:\?.*)?$/i, async (route) => {
    if (!isMockBackendRequest(route.request())) {
      await route.fallback();
      return;
    }

    if (route.request().method().toUpperCase() !== "GET") {
      await route.fallback();
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockEvents[0]),
    });
  });

  await page.route(/\/(?:api\/)?events\/\d+\/time-status\/?(?:\?.*)?$/i, async (route) => {
    if (!isMockBackendRequest(route.request())) {
      await route.fallback();
      return;
    }

    if (route.request().method().toUpperCase() !== "GET") {
      await route.fallback();
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        event_id: 1,
        status: "upcoming",
        is_check_in_open: false,
        is_sign_out_open: false,
      }),
    });
  });

  await page.route(/\/api\/attendance\/events\/\d+\/(?:report|attendances|attendances-with-students)\/?(?:\?.*)?$/i, async (route) => {
    if (!isMockBackendRequest(route.request())) {
      await route.fallback();
      return;
    }

    if (route.request().method().toUpperCase() !== "GET") {
      await route.fallback();
      return;
    }

    const url = new URL(route.request().url());
    const isReport = /\/report\/?$/i.test(url.pathname);
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(isReport
        ? { rows: [], total: 0, present: 0, absent: 0, late: 0 }
        : []),
    });
  });

  await page.route(/\/api\/attendance\/(?:me\/records|students\/me)\/?(?:\?.*)?$/i, async (route) => {
    if (!isMockBackendRequest(route.request())) {
      await route.fallback();
      return;
    }

    if (route.request().method().toUpperCase() !== "GET") {
      await route.fallback();
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([]),
    });
  });

  await page.route(/\/(?:api\/)?logos\/aura\.png(?:\?.*)?$/i, async (route) => {
    if (!isMockBackendRequest(route.request())) {
      await route.fallback();
      return;
    }

    if (route.request().method().toUpperCase() !== "GET") {
      await route.fallback();
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "image/png",
      body: Buffer.from(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII=",
        "base64",
      ),
    });
  });

  await page.route(/\/(?:api\/)?auth\/security\/face-status\/?$/i, async (route) => {
    if (!isMockBackendRequest(route.request())) {
      await route.fallback();
      return;
    }

    if (route.request().method().toUpperCase() !== "GET") {
      await route.fallback();
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        face_verification_required: false,
        face_reference_enrolled: true,
        provider: "face_recognition",
        updated_at: new Date().toISOString(),
      }),
    });
  });
}

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
      /dotlottie-player\.wasm/i, // CDN fallback warning from login animation
      /Primary WASM load failed/i, // CDN fallback warning from login animation
      /Attempting to load WASM from backup URL/i, // CDN fallback warning from login animation
      /GL Driver Message.*ReadPixels/i, // browser/WebGL performance noise from animated login visuals
      /Failed to load resource.*401/i, // expected during auth failure paths
      /Failed to load resource.*429/i, // expected if hitting rate limits
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
      if (status >= 400 && status !== 401 && status !== 429) { // we expect 401 on bad login, 429 from rate limiting
        const url = res.url();
        if (!isHarmless(url)) {
          badResponses.push(`Bad response ${status}: ${url}`);
        }
      }
    });

    if (mockAuthEnabled) {
      await installMockAuthRoutes(page);
    }

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
