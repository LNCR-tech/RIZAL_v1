// Role configuration for the Aura documentation portal.
// Backend roles may arrive with underscores; the doc-site uses hyphenated keys.

export const ROLES = {
  ADMIN: 'admin',
  CAMPUS_ADMIN: 'campus-admin',
  SCHOOL_IT: 'school-it',
  SSG: 'ssg',
  SG: 'sg',
  ORG: 'org',
  STUDENT: 'student',
};

export const ROLE_LABELS = {
  [ROLES.ADMIN]: 'Platform Admin',
  [ROLES.CAMPUS_ADMIN]: 'Campus Admin',
  [ROLES.SCHOOL_IT]: 'School IT',
  [ROLES.SSG]: 'Supreme Student Government',
  [ROLES.SG]: 'Student Government',
  [ROLES.ORG]: 'Organization Officer',
  [ROLES.STUDENT]: 'Student',
};

export const USER_DOC_ROLES = [
  ROLES.ADMIN,
  ROLES.CAMPUS_ADMIN,
  ROLES.SCHOOL_IT,
  ROLES.SSG,
  ROLES.SG,
  ROLES.ORG,
  ROLES.STUDENT,
];

export const EVENT_MANAGER_ROLES = [
  ROLES.ADMIN,
  ROLES.CAMPUS_ADMIN,
  ROLES.SSG,
  ROLES.SG,
  ROLES.ORG,
];

export const TECHNICAL_DOC_ROLES = [
  ROLES.ADMIN,
  ROLES.CAMPUS_ADMIN,
  ROLES.SCHOOL_IT,
];

const ROLE_ALIASES = {
  admin: ROLES.ADMIN,
  'platform-admin': ROLES.ADMIN,
  campusadmin: ROLES.CAMPUS_ADMIN,
  'campus-admin': ROLES.CAMPUS_ADMIN,
  schoolit: ROLES.SCHOOL_IT,
  'school-it': ROLES.SCHOOL_IT,
  it: ROLES.SCHOOL_IT,
  ssg: ROLES.SSG,
  sg: ROLES.SG,
  org: ROLES.ORG,
  organization: ROLES.ORG,
  student: ROLES.STUDENT,
};

export const normalizeRole = (role) => {
  if (!role) return '';

  const normalized = String(role)
    .trim()
    .toLowerCase()
    .replace(/[\s_]+/g, '-');

  return ROLE_ALIASES[normalized] || ROLE_ALIASES[normalized.replace(/-/g, '')] || normalized;
};

export const getRoleDisplayName = (role) => {
  const normalized = normalizeRole(role);
  return ROLE_LABELS[normalized] || role || 'Unknown role';
};

export const isStudent = (role) => normalizeRole(role) === ROLES.STUDENT;

export const isEventManager = (role) => EVENT_MANAGER_ROLES.includes(normalizeRole(role));

export const hasAdminPrivileges = (role) => TECHNICAL_DOC_ROLES.includes(normalizeRole(role));

export const canAccessRoute = (role, pathname) => {
  const normalizedRole = normalizeRole(role);

  if (!normalizedRole) return false;
  if (pathname.startsWith('/technical')) {
    return TECHNICAL_DOC_ROLES.includes(normalizedRole);
  }

  return USER_DOC_ROLES.includes(normalizedRole);
};

export const getAccessLabel = (role) => {
  if (hasAdminPrivileges(role)) return 'Technical access';
  if (isEventManager(role)) return 'Event docs access';
  return 'User guide access';
};
