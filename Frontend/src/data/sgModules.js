import { CalendarDays, Megaphone, ClipboardCheck, Users, Eye, Building2, Landmark, UserPlus, Shield, ShieldAlert } from 'lucide-vue-next'

/**
 * Permission-to-card mapping for the SG Dashboard.
 * Each module defines a card with its required permission code, label, icon, and route.
 * Grouped into sections for the dashboard layout.
 */

const SG_MODULE_SECTIONS = [
  {
    id: 'event-management',
    title: 'Event Management',
    modules: [
      {
        id: 'manage-events',
        permissionCode: 'manage_events',
        label: 'Manage Events',
        description: 'Create, edit, and manage events within your council scope.',
        icon: CalendarDays,
        route: '/governance/events',
      },
      {
        id: 'publish-announcements',
        permissionCode: 'manage_announcements',
        label: 'Publish Announcements',
        description: 'Create and publish announcements to students.',
        icon: Megaphone,
        route: '/governance/announcements',
      },
    ],
  },
  {
    id: 'attendance-management',
    title: 'Attendance Management',
    modules: [
      {
        id: 'manage-attendance',
        permissionCode: 'manage_attendance',
        label: 'Manage Attendance',
        description: 'Track and manage event attendance records.',
        icon: ClipboardCheck,
        route: '/governance/attendance',
      },
      {
        id: 'sanctions-dashboard',
        permissionCode: 'view_sanctions_dashboard',
        label: 'Sanctions Dashboard',
        description: 'Track absences, pending sanctions, and compliance approvals.',
        icon: ShieldAlert,
        route: '/governance/events/sanctions',
      },
    ],
  },
  {
    id: 'student-management',
    title: 'Student Management',
    modules: [
      {
        id: 'manage-students',
        permissionCode: 'manage_students',
        label: 'Manage Students',
        description: 'Edit and manage student profiles within scope.',
        icon: Users,
        route: '/governance/students',
      },
      {
        id: 'view-students',
        permissionCode: 'view_students',
        label: 'View Students',
        description: 'Browse the student directory.',
        icon: Eye,
        route: '/governance/students',
      },
    ],
  },
  {
    id: 'council-management',
    title: 'Governance Management',
    modules: [
      {
        id: 'create-sg',
        permissionCode: 'create_sg',
        label: 'Create College-Level Council',
        description: 'Create college-level SG child units under this council.',
        icon: Landmark,
        route: '/governance/create-unit',
      },
      {
        id: 'create-org',
        permissionCode: 'create_org',
        label: 'Create Organization',
        description: 'Create student organization units under this council.',
        icon: Building2,
        route: '/governance/create-unit',
      },
      {
        id: 'manage-members',
        permissionCode: 'manage_members',
        label: 'Manage Members',
        description: 'Add, edit, or remove governance members.',
        icon: UserPlus,
        route: '/governance/members',
      },
      {
        id: 'assign-permissions',
        permissionCode: 'assign_permissions',
        label: 'Manage Permissions',
        description: 'Grant or revoke governance permission codes for members.',
        icon: Shield,
        route: '/governance/members',
      },
    ],
  },
]

/**
 * Returns only the sections/modules that the user has permission for.
 * Sections with zero visible modules are excluded entirely.
 */
export function getVisibleSections(permissionCodes = []) {
  const codeSet = new Set(permissionCodes)

  return SG_MODULE_SECTIONS
    .map((section) => ({
      ...section,
      modules: section.modules.filter((mod) => mod.id === 'view-students' || codeSet.has(mod.permissionCode)),
    }))
    .filter((section) => section.modules.length > 0)
}

/**
 * Returns ALL sections with ALL modules — used when showing everything
 * and marking unpermitted cards as disabled visually.
 */
export function getAllSections() {
  return SG_MODULE_SECTIONS.map((section) => ({
    ...section,
    modules: [...section.modules],
  }))
}

/**
 * Returns a flat list of all visible modules for search filtering.
 */
export function getVisibleModules(permissionCodes = []) {
  return getVisibleSections(permissionCodes).flatMap((section) => section.modules)
}

/**
 * Filters sections by a search query matching module labels.
 */
export function filterSectionsBySearch(sections = [], query = '') {
  const normalizedQuery = String(query || '').trim().toLowerCase()
  if (!normalizedQuery) return sections

  return sections
    .map((section) => ({
      ...section,
      modules: section.modules.filter((mod) =>
        mod.label.toLowerCase().includes(normalizedQuery) ||
        mod.description.toLowerCase().includes(normalizedQuery) ||
        section.title.toLowerCase().includes(normalizedQuery)
      ),
    }))
    .filter((section) => section.modules.length > 0)
}
