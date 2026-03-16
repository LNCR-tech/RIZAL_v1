import type { AuthSession } from "./api/authApi";
import type { FacialVerificationRole } from "./api/facialVerificationApi";
import {
  normalizeLogoUrl,
  type SchoolSettings,
} from "./api/schoolSettingsApi";
import {
  clearStudentFaceEnrollmentState,
  fetchStudentFaceEnrollmentStatus,
  isStudentFaceEnrollmentRequired,
  setStudentFaceEnrollmentRequired,
} from "./api/studentFaceEnrollmentApi";
import { getStoredGovernanceAccess } from "./hooks/useGovernanceAccess";
import { sanitizeRedirectPath } from "./utils/redirects";
import { hasAnyRole } from "./utils/roleUtils";

export const hasStudentRole = (roles: string[]) => hasAnyRole(roles, "student");

export const resolveDashboardPath = (roles: string[]): string => {
  let resolvedPath = "/";
  if (hasAnyRole(roles, "admin")) {
    resolvedPath = "/admin_dashboard";
  } else if (hasAnyRole(roles, "campus_admin")) {
    resolvedPath = "/campus_admin_dashboard";
  } else {
    const governanceAccess = getStoredGovernanceAccess();
    if (governanceAccess?.units.some((unit) => unit.unit_type === "SSG")) {
      resolvedPath = "/ssg_dashboard";
    } else if (governanceAccess?.units.some((unit) => unit.unit_type === "SG")) {
      resolvedPath = "/sg_dashboard";
    } else if (governanceAccess?.units.some((unit) => unit.unit_type === "ORG")) {
      resolvedPath = "/org_dashboard";
    } else if (hasStudentRole(roles)) {
      resolvedPath = "/student_dashboard";
    }
  }

  return sanitizeRedirectPath(resolvedPath, "/");
};

export const getRequiredFaceVerificationRole = (
  roles: string[]
): FacialVerificationRole | null => {
  if (hasAnyRole(roles, "admin")) {
    return "admin";
  }
  if (hasAnyRole(roles, "campus_admin")) {
    return "campus_admin";
  }
  return null;
};

const resolveStudentPostAuthenticationPath = async ({
  roles,
  authToken,
  userId,
}: {
  roles: string[];
  authToken?: string | null;
  userId?: number | null;
}) => {
  const fallbackDashboardPath = sanitizeRedirectPath(
    resolveDashboardPath(roles),
    "/student_dashboard"
  );

  try {
    const status = await fetchStudentFaceEnrollmentStatus(authToken);
    const resolvedUserId = status.userId ?? userId ?? null;
    const resolvedRoles = status.roles.length > 0 ? status.roles : roles;

    if (!status.hasStudentRole || !status.hasStudentProfile || status.faceRegistered) {
      clearStudentFaceEnrollmentState(resolvedUserId);
      return sanitizeRedirectPath(
        resolveDashboardPath(resolvedRoles),
        fallbackDashboardPath
      );
    }

    if (resolvedUserId != null) {
      setStudentFaceEnrollmentRequired(resolvedUserId, true);
    }

    return sanitizeRedirectPath("/student_face_registration", "/");
  } catch {
    if (isStudentFaceEnrollmentRequired(userId ?? null)) {
      return sanitizeRedirectPath("/student_face_registration", "/");
    }
    return fallbackDashboardPath;
  }
};

export const resolvePostAuthenticationPath = async ({
  roles,
  mustChangePassword,
  authToken,
  userId,
}: {
  roles: string[];
  mustChangePassword: boolean;
  authToken?: string | null;
  userId?: number | null;
}) => {
  if (mustChangePassword) {
    return sanitizeRedirectPath("/change-password", "/");
  }

  if (hasStudentRole(roles)) {
    return resolveStudentPostAuthenticationPath({
      roles,
      authToken,
      userId,
    });
  }

  return sanitizeRedirectPath(resolveDashboardPath(roles), "/");
};

export const buildBrandingFromAuthSession = (
  session: AuthSession
): SchoolSettings | null => {
  if (session.schoolId == null) {
    return null;
  }

  return {
    school_id: session.schoolId,
    school_name: session.schoolName || "School",
    school_code: session.schoolCode || null,
    logo_url: normalizeLogoUrl(session.logoUrl),
    primary_color: session.primaryColor || "#162F65",
    secondary_color: session.secondaryColor || "#2C5F9E",
    event_default_early_check_in_minutes: 30,
    event_default_late_threshold_minutes: 10,
    event_default_sign_out_grace_minutes: 20,
    subscription_status: "trial",
    active_status: true,
  };
};

export const syncRememberedEmail = (
  email: string | null | undefined,
  rememberMe: boolean
) => {
  if (rememberMe && email) {
    localStorage.setItem("rememberedEmail", email);
    return;
  }
  localStorage.removeItem("rememberedEmail");
};
