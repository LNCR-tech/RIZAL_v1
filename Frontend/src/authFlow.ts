import type { AuthSession } from "./api/authApi";
import type { FacialVerificationRole } from "./api/facialVerificationApi";
import {
  normalizeLogoUrl,
  type SchoolSettings,
} from "./api/schoolSettingsApi";

const normalizeRole = (role: string) => role.trim().toLowerCase().replace(/_/g, "-");

const hasAnyRole = (roles: string[], ...roleNames: string[]) => {
  const normalizedRoles = new Set(roles.map(normalizeRole));
  return roleNames.some((roleName) => normalizedRoles.has(normalizeRole(roleName)));
};

export const hasStudentRole = (roles: string[]) => hasAnyRole(roles, "student");

export const resolveDashboardPath = (roles: string[]): string => {
  const isStudent = hasStudentRole(roles);
  const isSsg = hasAnyRole(roles, "ssg");
  const isEventOrganizer = hasAnyRole(roles, "event-organizer");

  if (hasAnyRole(roles, "admin")) return "/admin_dashboard";
  if (hasAnyRole(roles, "school-it")) return "/school_it_dashboard";
  if (isStudent && isSsg && isEventOrganizer) return "/student_ssg_eventorganizer_dashboard";
  if (isStudent && isSsg) return "/student_ssg_dashboard";
  if (isStudent) return "/student_dashboard";
  if (isSsg) return "/ssg_dashboard";
  if (isEventOrganizer) return "/event_organizer_dashboard";
  return "/";
};

export const getRequiredFaceVerificationRole = (
  roles: string[]
): FacialVerificationRole | null => {
  if (hasAnyRole(roles, "admin")) {
    return "admin";
  }
  if (hasAnyRole(roles, "school-it")) {
    return "school_IT";
  }
  return null;
};

export const resolvePostAuthenticationPath = ({
  roles,
  mustChangePassword,
}: {
  roles: string[];
  mustChangePassword: boolean;
}) => {
  if (mustChangePassword) {
    return "/change-password";
  }

  if (hasStudentRole(roles)) {
    return "/student_face_registration";
  }

  return resolveDashboardPath(roles);
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
