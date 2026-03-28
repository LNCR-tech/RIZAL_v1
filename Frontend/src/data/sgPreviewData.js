/**
 * Preview data for /exposed/sg route.
 * Shaped exactly like real governance access + SSG setup payloads.
 */
export const sgPreviewGovernanceAccess = {
  units: [
    {
      governance_unit_id: 1,
      unit_type: 'SSG',
      unit_code: 'SSG',
      unit_name: 'Supreme Student Government',
      position_title: 'President',
      is_active: true,
    },
  ],
}

export const sgPreviewSsgSetup = {
  unit: {
    id: 1,
    unit_code: 'SSG',
    unit_name: 'Supreme Student Government',
    description: 'The central governing body overseeing all students and campus organizations.',
    unit_type: 'SSG',
    school_id: 1,
    is_active: true,
    members: [
      {
        id: 1,
        user_id: 1,
        position_title: 'President',
        is_active: true,
        user: {
          id: 1,
          first_name: 'Preview',
          last_name: 'Officer',
          email: 'preview@university.edu',
        },
        member_permissions: [
          { permission_code: 'create_org' },
          { permission_code: 'manage_students' },
          { permission_code: 'view_students' },
          { permission_code: 'manage_members' },
          { permission_code: 'manage_events' },
          { permission_code: 'manage_attendance' },
          { permission_code: 'manage_announcements' },
          { permission_code: 'assign_permissions' },
        ],
      },
    ],
    unit_permissions: [
      { permission_code: 'create_org' },
      { permission_code: 'manage_students' },
      { permission_code: 'view_students' },
      { permission_code: 'manage_members' },
      { permission_code: 'manage_events' },
      { permission_code: 'manage_attendance' },
      { permission_code: 'manage_announcements' },
      { permission_code: 'assign_permissions' },
    ],
  },
  total_imported_students: 0,
}

export const sgPreviewUser = {
  id: 1,
  email: 'preview@university.edu',
  first_name: 'Preview',
  middle_name: null,
  last_name: 'Officer',
  is_active: true,
  roles: [{ role: { id: 2, name: 'student' } }],
  student_profile: {
    student_id: 'PREVIEW-001',
    department_id: 1,
    program_id: 1,
    year_level: 3,
  },
}

export const sgPreviewSchoolSettings = {
  school_id: 1,
  school_name: 'University Preview',
  school_code: 'UNIV',
  logo_url: null,
  primary_color: '#6B8E23',
  secondary_color: '#333333',
  accent_color: '#000000',
}

/**
 * All permission codes available in preview mode.
 */
export const sgPreviewPermissionCodes = [
  'create_sg',
  'create_org',
  'manage_students',
  'view_students',
  'manage_members',
  'manage_events',
  'manage_attendance',
  'manage_announcements',
  'assign_permissions',
]
