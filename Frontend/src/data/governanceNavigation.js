import {
  BarChart3,
  Building2,
  CalendarDays,
  LayoutGrid,
  Megaphone,
  ShieldCheck,
  UsersRound,
} from 'lucide-vue-next'

const SECTION_DEFINITIONS = {
  overview: {
    key: 'overview',
    navLabel: 'Home',
    route: '/governance',
    previewRoute: '/exposed/governance',
    navIcon: LayoutGrid,
    panelIcon: LayoutGrid,
    title: 'Governance Home',
    description: 'See the live pulse of your governance unit before you jump into events, directory work, or admin structure.',
    placeholderTitle: 'Governance overview',
    placeholderDescription: 'This landing page will stay focused on the most useful SG, SSG, and ORG summaries first.',
    featureList: [
      'Upcoming events and attendance operations surface here first.',
      'Recent governance announcements will stay visible here.',
      'Quick actions will point to the tools your unit uses most.',
    ],
  },
  events: {
    key: 'events',
    navLabel: 'Events',
    route: '/governance/events',
    previewRoute: '/exposed/governance/events',
    navIcon: Megaphone,
    panelIcon: CalendarDays,
    title: 'Events',
    description: 'This workspace will own event operations, announcements, and attendance management for the active governance unit.',
    placeholderTitle: 'Events workspace',
    placeholderDescription: 'This temporary screen reserves the slot for event publishing, announcement posting, and attendance management.',
    featureList: [
      'Manage governance-scoped events from the backend event feed.',
      'Fold attendance management into the event workflow.',
      'Keep announcements tied to the unit that owns the event.',
    ],
  },
  reports: {
    key: 'reports',
    navLabel: 'Reports',
    route: '/governance/reports',
    previewRoute: '/exposed/governance/reports',
    navIcon: BarChart3,
    panelIcon: BarChart3,
    title: 'Reports',
    description: 'Review scoped attendance analytics, event performance, and follow-up signals for the active governance unit.',
    placeholderTitle: 'Governance reports',
    placeholderDescription: 'This screen is reserved for scoped analytics, attendance reporting, and sanction follow-up views.',
    featureList: [
      'Inspect governance-scoped attendance reports per event.',
      'Track engagement, demographic reach, and peak arrival windows.',
      'Open sanction follow-up work without leaving the governance workspace.',
    ],
  },
  students: {
    key: 'students',
    navLabel: 'Students',
    route: '/governance/students',
    previewRoute: '/exposed/governance/students',
    navIcon: UsersRound,
    panelIcon: UsersRound,
    title: 'Students',
    description: 'Browse the student directory inside your current governance scope before the full management tools land here.',
    placeholderTitle: 'Student directory',
    placeholderDescription: 'This temporary screen keeps the directory slot visible while we prepare scoped student browsing and profile editing.',
    featureList: [
      'View students inside the active governance scope.',
      'Keep profile edits aligned to the permissions returned by the backend.',
      'Surface the directory without mixing it into the student dashboard.',
    ],
  },
  governance: {
    key: 'governance',
    navLabel: 'Governance',
    route: '/governance/admin',
    previewRoute: '/exposed/governance/admin',
    navIcon: Building2,
    panelIcon: ShieldCheck,
    title: 'Governance',
    description: 'This area will hold unit structure, members, permissions, and creation tools for councils and organizations.',
    placeholderTitle: 'Governance admin',
    placeholderDescription: 'This temporary screen marks the place for member management, permission controls, and unit structure tools.',
    featureList: [
      'Manage officers, members, and permission assignments.',
      'Create lower-level councils or organizations when the backend scope allows it.',
      'Keep structural governance tools separate from student-facing screens.',
    ],
  },
}

export const governanceSectionOrder = [
  'overview',
  'events',
  'reports',
  'students',
  'governance',
]

export function getGovernanceSectionDefinition(sectionKey = 'overview') {
  return SECTION_DEFINITIONS[sectionKey] || SECTION_DEFINITIONS.overview
}

export function getGovernanceSectionDefinitions() {
  return governanceSectionOrder.map((sectionKey) => getGovernanceSectionDefinition(sectionKey))
}

export function getGovernanceNavigationItems(preview = false) {
  return getGovernanceSectionDefinitions().map((section) => ({
    name: section.navLabel,
    route: preview ? section.previewRoute : section.route,
    icon: section.navIcon,
  }))
}
