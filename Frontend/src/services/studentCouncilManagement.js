const COUNCIL_ROLE_NAMES = ['ssg', 'student_council', 'student council']
export const GOVERNANCE_PERMISSION_CODES = [
  'create_sg',
  'create_org',
  'manage_students',
  'view_students',
  'manage_members',
  'manage_events',
  'manage_attendance',
  'manage_announcements',
  'assign_permissions',
  'view_sanctioned_students_list',
  'view_student_sanction_detail',
  'approve_sanction_compliance',
  'configure_event_sanctions',
  'export_sanctioned_students',
  'view_sanctions_dashboard',
]

const BACKEND_PERMISSION_LABELS = {
  create_sg: 'Create College Level Councils',
  create_org: 'Create Organizations',
  manage_students: 'Edit Student Profiles',
  view_students: 'View Student Directory',
  manage_members: 'Manage Members',
  manage_events: 'Manage Events',
  manage_attendance: 'Manage Attendance',
  manage_announcements: 'Publish Announcements',
  assign_permissions: 'Manage Permissions',
  view_sanctioned_students_list: 'View Sanctioned Students List',
  view_student_sanction_detail: 'View Student Sanction Detail',
  approve_sanction_compliance: 'Approve Sanction Compliance',
  configure_event_sanctions: 'Configure Event Sanctions',
  export_sanctioned_students: 'Export Sanctioned Students',
  view_sanctions_dashboard: 'View Sanctions Dashboard',
}

const BACKEND_PERMISSION_TO_UI = {
  create_sg: 'create-college-level-councils',
  create_org: 'create-organizations',
  manage_members: 'manage-members',
  manage_events: 'manage-events',
  manage_announcements: 'publish-announcements',
  manage_attendance: 'manage-attendance',
  view_students: 'view-student-directory',
  manage_students: 'edit-student-profiles',
  assign_permissions: 'manage-permissions',
  view_sanctioned_students_list: 'view-sanctioned-students-list',
  view_student_sanction_detail: 'view-student-sanction-detail',
  approve_sanction_compliance: 'approve-sanction-compliance',
  configure_event_sanctions: 'configure-event-sanctions',
  export_sanctioned_students: 'export-sanctioned-students',
  view_sanctions_dashboard: 'view-sanctions-dashboard',
}

const UI_PERMISSION_TO_BACKEND = Object.fromEntries(
  Object.entries(BACKEND_PERMISSION_TO_UI).map(([backendCode, uiCode]) => [uiCode, backendCode])
)

export const defaultStudentCouncilPermissionCatalog = [
  {
    id: 'event-management',
    label: 'Event Management',
    permissions: [
      { id: 'manage-events', label: 'Manage Events' },
      { id: 'publish-announcements', label: 'Publish Announcements' },
      { id: 'configure-event-sanctions', label: 'Configure Event Sanctions' },
      { id: 'view-sanctions-dashboard', label: 'View Sanctions Dashboard' },
    ],
  },
  {
    id: 'sanctions-management',
    label: 'Sanctions Management',
    permissions: [
      { id: 'view-sanctioned-students-list', label: 'View Sanctioned Students List' },
      { id: 'view-student-sanction-detail', label: 'View Student Sanction Detail' },
      { id: 'approve-sanction-compliance', label: 'Approve Sanction Compliance' },
      { id: 'export-sanctioned-students', label: 'Export Sanctioned Students' },
    ],
  },
  {
    id: 'attendance-management',
    label: 'Attendance Management',
    permissions: [
      { id: 'manage-attendance', label: 'Manage Attendance' },
    ],
  },
  {
    id: 'student-management',
    label: 'Student Management',
    permissions: [
      { id: 'view-student-directory', label: 'View Student Directory' },
      { id: 'edit-student-profiles', label: 'Edit Student Profiles' },
    ],
  },
  {
    id: 'college-level-council-management',
    label: 'College-Level Council Management',
    permissions: [
      { id: 'create-college-level-councils', label: 'Create College Level Councils' },
      { id: 'manage-permissions', label: 'Manage Permissions' },
      { id: 'manage-members', label: 'Manage Members' },
    ],
  },
]

export function createEmptyCouncilDraft() {
  return {
    acronym: '',
    name: '',
    description: '',
    scopeId: '',
  }
}

export function createEmptyCouncilMemberDraft() {
  return {
    studentId: null,
    position: '',
    permissionIds: [],
  }
}

export function createStudentCouncilStorageKey(schoolId, preview = false) {
  const normalizedSchoolId = Number(schoolId)
  if (!Number.isFinite(normalizedSchoolId)) {
    return preview ? 'aura_student_council_preview' : 'aura_student_council'
  }

  return preview
    ? `aura_student_council_preview_${normalizedSchoolId}`
    : `aura_student_council_${normalizedSchoolId}`
}

export function loadStudentCouncilState(storageKey) {
  if (typeof localStorage === 'undefined' || !storageKey) return null

  try {
    const raw = localStorage.getItem(storageKey)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    if (!parsed || typeof parsed !== 'object') return null

    return {
      council: parsed.council && typeof parsed.council === 'object' ? parsed.council : null,
      members: Array.isArray(parsed.members) ? parsed.members : [],
    }
  } catch {
    return null
  }
}

export function saveStudentCouncilState(storageKey, payload) {
  if (typeof localStorage === 'undefined' || !storageKey) return

  const safePayload = {
    council: payload?.council && typeof payload.council === 'object' ? payload.council : null,
    members: Array.isArray(payload?.members) ? payload.members : [],
  }

  localStorage.setItem(storageKey, JSON.stringify(safePayload))
}

export function buildStudentCouncilCandidates({ users = [], programs = [], departments = [] } = {}) {
  const programLookup = createProgramLookup(programs)
  const departmentLookup = createDepartmentLookup(departments)

  return users
    .filter(isStudentUser)
    .map((user) => {
      const profile = user.student_profile || {}
      const program = programLookup.get(Number(profile.program_id)) || null
      const department = departmentLookup.get(Number(profile.department_id)) || null
      const fullName = [user.first_name, user.last_name].filter(Boolean).join(' ').trim() || user.email || 'Student'

      return {
        id: Number(user.id),
        userId: Number(user.id),
        studentId: String(profile.student_id || user.id || ''),
        fullName,
        programName: program?.name || '',
        departmentName: department?.name || '',
        email: user.email || '',
        searchText: [
          fullName,
          profile.student_id,
          program?.name,
          department?.name,
          user.email,
        ].filter(Boolean).join(' ').toLowerCase(),
      }
    })
}

export function mapGovernanceStudentCandidateToCouncilCandidate(candidate = {}) {
  const user = candidate.user || {}
  const profile = candidate.student_profile || {}
  const fullName = [user.first_name, user.last_name].filter(Boolean).join(' ').trim() || user.email || 'Student'

  return {
    id: Number(user.id),
    userId: Number(user.id),
    studentId: String(profile.student_id || user.id || ''),
    fullName,
    programName: profile.program_name || '',
    departmentName: profile.department_name || '',
    email: user.email || '',
    isCurrentGovernanceMember: Boolean(candidate.is_current_governance_member),
    searchText: [
      fullName,
      profile.student_id,
      profile.program_name,
      profile.department_name,
      user.email,
    ].filter(Boolean).join(' ').toLowerCase(),
  }
}

export function resolveStudentCouncilAcronym(council = {}) {
  const explicitAcronym = String(
    council?.acronym
    || council?.unit_code
    || council?.organization_acronym
    || ''
  ).trim()

  if (explicitAcronym) return explicitAcronym

  return buildAcronym(
    council?.name
    || council?.unit_name
    || council?.organization_name
    || ''
  )
}

export function mapGovernanceUnitToCouncilRecord(unit = {}) {
  if (!unit || typeof unit !== 'object') return null

  return {
    id: Number(unit.id),
    acronym: resolveStudentCouncilAcronym(unit),
    name: String(unit.unit_name || '').trim(),
    description: String(unit.description || '').trim(),
    memberCount: Array.isArray(unit.members) ? unit.members.length : 0,
    permissionIds: Array.isArray(unit.unit_permissions)
      ? normalizePermissionIds(
        unit.unit_permissions.map((permission) => mapBackendPermissionCodeToUi(permission.permission_code))
      )
      : [],
  }
}

export function deriveStudentCouncilRecord({ schoolSettings = null, users = [] } = {}) {
  const councilUsers = users.filter(isStudentCouncilUser)
  const leadProfile = councilUsers[0]?.ssg_profile || null
  if (!leadProfile && !councilUsers.length) return null

  const schoolName = schoolSettings?.school_name || 'Student Council'
  const fallbackAcronym = buildAcronym(schoolSettings?.school_code || schoolName)

  return {
    id: Number(leadProfile?.id ?? Date.now()),
    acronym: String(
      leadProfile?.organization_acronym
      || leadProfile?.acronym
      || fallbackAcronym
      || 'SC'
    ).trim(),
    name: String(
      leadProfile?.organization_name
      || leadProfile?.name
      || `${schoolName} Student Council`
    ).trim(),
    description: String(
      leadProfile?.description
      || `The central governing body overseeing all students and campus organizations for ${schoolName}.`
    ).trim(),
  }
}

export function deriveStudentCouncilMembers({ users = [], programs = [], departments = [] } = {}) {
  const candidates = buildStudentCouncilCandidates({ users, programs, departments })
  const candidateLookup = new Map(candidates.map((candidate) => [candidate.userId, candidate]))

  return users
    .filter(isStudentCouncilUser)
    .map((user) => {
      const candidate = candidateLookup.get(Number(user.id))
      const profile = user.ssg_profile || {}
      const permissionIds = normalizePermissionIds(profile.permission_ids || profile.permissions)

      return {
        id: Number(profile.id ?? user.id),
        userId: Number(user.id),
        studentId: candidate?.studentId || String(user.student_profile?.student_id || user.id || ''),
        fullName: candidate?.fullName || [user.first_name, user.last_name].filter(Boolean).join(' ').trim() || user.email || 'Student',
        position: String(
          profile.position
          || profile.title
          || profile.designation
          || profile.role
          || 'Officer'
        ).trim(),
        permissionIds,
      }
    })
}

export function mapGovernanceMemberToCouncilMember(member = {}) {
  const user = member.user || {}
  const profile = user.student_profile || {}
  const permissions = Array.isArray(member.member_permissions)
    ? member.member_permissions
      .map((permission) => mapBackendPermissionCodeToUi(permission.permission_code))
      .filter(Boolean)
    : []

  return {
    id: Number(member.id),
    userId: Number(user.id),
    studentId: String(profile.student_id || user.id || ''),
    fullName: [user.first_name, user.last_name].filter(Boolean).join(' ').trim() || user.email || 'Student',
    position: String(member.position_title || 'Officer').trim(),
    permissionIds: permissions,
    isActive: member.is_active !== false,
  }
}

export function mapUiPermissionIdsToBackend(permissionIds = []) {
  return normalizePermissionIds(permissionIds)
    .map((permissionId) => UI_PERMISSION_TO_BACKEND[permissionId] || null)
    .filter((permissionCode) => GOVERNANCE_PERMISSION_CODES.includes(permissionCode))
}

export function formatGovernancePermissionLabel(permissionId) {
  const normalizedPermissionId = String(permissionId || '').trim().toLowerCase()
  if (!normalizedPermissionId) return ''

  const backendCode = UI_PERMISSION_TO_BACKEND[normalizedPermissionId]
    || normalizedPermissionId.replace(/-/g, '_')

  if (BACKEND_PERMISSION_LABELS[backendCode]) {
    return BACKEND_PERMISSION_LABELS[backendCode]
  }


  return normalizedPermissionId
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

export function mapBackendPermissionCodeToUi(permissionCode) {
  const normalizedCode = String(permissionCode || '').trim().toLowerCase()
  if (!normalizedCode) return ''

  const sanitizedCode = GOVERNANCE_PERMISSION_CODES.includes(normalizedCode)
    ? normalizedCode
    : normalizedCode

  return BACKEND_PERMISSION_TO_UI[sanitizedCode] || sanitizedCode.replace(/_/g, '-')
}

export function normalizePermissionCatalog(catalog = defaultStudentCouncilPermissionCatalog) {
  return Array.isArray(catalog)
    ? catalog.map((category) => ({
      id: String(category.id),
      label: String(category.label),
      permissions: Array.isArray(category.permissions)
        ? category.permissions.map((permission) => ({
          id: String(permission.id),
          label: String(permission.label),
        }))
        : [],
    }))
    : []
}

export function normalizePermissionIds(values) {
  return Array.isArray(values)
    ? [...new Set(values.map((value) => String(value).trim()).filter(Boolean))]
    .filter(Boolean)
    : []
}

export function isStudentCouncilUser(user) {
  const roles = Array.isArray(user?.roles)
    ? user.roles.map((role) => String(role?.role?.name || role?.name || '').toLowerCase())
    : []

  const explicitPermissions = Array.isArray(user?.system_permissions)
    ? user.system_permissions
    : (Array.isArray(user?.permissions) ? user.permissions : []);

  const hasGovernancePermissions = explicitPermissions.some((p) => {
    const code = typeof p === 'string' ? p : (p?.permission_code || p?.name || '');
    return GOVERNANCE_PERMISSION_CODES.includes(code);
  })

  return Boolean(user?.ssg_profile) || roles.some((role) => COUNCIL_ROLE_NAMES.includes(role)) || hasGovernancePermissions
}

export function isStudentUser(user) {
  const roles = Array.isArray(user?.roles)
    ? user.roles.map((role) => String(role?.role?.name || role?.name || '').toLowerCase())
    : []

  return Boolean(user?.student_profile) || roles.includes('student')
}

function createProgramLookup(programs) {
  return new Map(
    (Array.isArray(programs) ? programs : [])
      .map((program) => [Number(program.id), program])
      .filter(([id]) => Number.isFinite(id))
  )
}

function createDepartmentLookup(departments) {
  return new Map(
    (Array.isArray(departments) ? departments : [])
      .map((department) => [Number(department.id), department])
      .filter(([id]) => Number.isFinite(id))
  )
}

function buildAcronym(value) {
  const letters = String(value || '')
    .trim()
    .match(/\b[\p{L}\p{N}]/gu)

  return Array.isArray(letters) ? letters.map((letter) => letter.toUpperCase()).join('') : ''
}
