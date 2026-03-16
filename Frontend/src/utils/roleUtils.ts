export const normalizeRole = (role: string): string => {
  const normalized = role.trim().toLowerCase().replace(/_/g, "-");
  if (normalized === "school-it" || normalized === "campus-admin") {
    return "campus-admin";
  }
  return normalized;
};

export const hasAnyRole = (roles: string[], ...roleNames: string[]): boolean => {
  const normalizedRoles = new Set(roles.map(normalizeRole));
  return roleNames.some((roleName) => normalizedRoles.has(normalizeRole(roleName)));
};

export const isCampusAdminRole = (role: string): boolean => normalizeRole(role) === "campus-admin";

export const formatRoleLabel = (role: string): string => {
  const normalized = normalizeRole(role);
  if (normalized === "campus-admin") return "Campus Admin";
  if (normalized === "ssg") return "SSG Officer";
  if (normalized === "admin") return "Admin";
  if (normalized === "student") return "Student";
  return role;
};
