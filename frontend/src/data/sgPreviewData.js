import {
  normalizeEvent,
  normalizeEventAttendanceWithStudent,
  normalizeGovernanceUnitDetail,
  normalizeGovernanceUserSummary,
  normalizeSchoolSettings,
  normalizeUserWithRelations,
} from '@/services/backendNormalizers.js'
import { mapGovernanceMemberToCouncilMember } from '@/services/studentCouncilManagement.js'
import { withBase } from '@/services/appPath.js'

const PREVIEW_SCHOOL = normalizeSchoolSettings({
  school_id: 701,
  school_name: 'Jose Rizal Memorial State University',
  school_code: 'JRMSU',
  logo_url: withBase('logos/aura.png'),
  primary_color: '#AAFF00',
  secondary_color: '#64748B',
  accent_color: '#0A0A0A',
})

const SSG_PERMISSION_CODES = [
  'create_sg',
  'manage_students',
  'view_students',
  'manage_members',
  'manage_events',
  'manage_attendance',
  'manage_announcements',
  'assign_permissions',
]

const SG_PERMISSION_CODES = [
  'create_org',
  'manage_students',
  'view_students',
  'manage_members',
  'manage_events',
  'manage_attendance',
  'manage_announcements',
  'assign_permissions',
]

function isoOffset({ days = 0, hours = 0, minutes = 0 } = {}) {
  const date = new Date()
  date.setDate(date.getDate() + days)
  date.setHours(date.getHours() + hours)
  date.setMinutes(date.getMinutes() + minutes)
  return date.toISOString()
}

function createPermissionRecords(codes = []) {
  return codes.map((permissionCode, index) => ({
    id: index + 1,
    permission_code: permissionCode,
    permission_name: permissionCode
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (character) => character.toUpperCase()),
  }))
}

function createStudent({
  id,
  studentId,
  firstName,
  lastName,
  email,
  departmentId = null,
  departmentName = null,
  programId = null,
  programName = null,
  yearLevel = null,
}) {
  return normalizeGovernanceUserSummary({
    id,
    email,
    first_name: firstName,
    last_name: lastName,
    school_id: PREVIEW_SCHOOL.school_id,
    is_active: true,
    student_profile: {
      id: id + 1000,
      student_id: studentId,
      department_id: departmentId,
      program_id: programId,
      department_name: departmentName,
      program_name: programName,
      year_level: yearLevel,
    },
  })
}

function createMember({ id, user, positionTitle, permissionCodes = [] }) {
  return {
    id,
    governance_unit_id: null,
    user_id: user.id,
    position_title: positionTitle,
    is_active: true,
    assigned_at: isoOffset({ days: -120 + id }),
    user,
    member_permissions: createPermissionRecords(permissionCodes).map((permission, index) => ({
      id: id * 100 + index + 1,
      permission_id: permission.id,
      permission_code: permission.permission_code,
      permission_name: permission.permission_name,
      permission,
    })),
  }
}

function createGovernanceAccess(unit, permissionCodes = []) {
  return {
    user_id: unit?.members?.[0]?.user_id ?? null,
    school_id: PREVIEW_SCHOOL.school_id,
    permission_codes: [...permissionCodes],
    units: [
      {
        governance_unit_id: unit.id,
        unit_type: unit.unit_type,
        unit_code: unit.unit_code,
        unit_name: unit.unit_name,
        position_title: unit.members?.[0]?.position_title || '',
        permission_codes: [...permissionCodes],
        is_active: true,
      },
    ],
  }
}

function createCouncilEvents(rawEvents = []) {
  return rawEvents.map((event) => normalizeEvent({
    ...event,
    school_id: PREVIEW_SCHOOL.school_id,
  }))
}

function createEventReport({
  eventId,
  eventName,
  eventDate,
  eventLocation,
  totalParticipants = 0,
  attendees = 0,
  lateAttendees = 0,
  incompleteAttendees = 0,
  absentees = 0,
  programBreakdown = [],
}) {
  const normalizedTotalParticipants = Number(totalParticipants) || 0
  const normalizedAttendees = Number(attendees) || 0

  return {
    event_id: eventId,
    event_name: eventName,
    event_date: eventDate,
    event_location: eventLocation,
    total_participants: normalizedTotalParticipants,
    attendees: normalizedAttendees,
    late_attendees: Number(lateAttendees) || 0,
    incomplete_attendees: Number(incompleteAttendees) || 0,
    absentees: Number(absentees) || 0,
    attendance_rate: normalizedTotalParticipants > 0
      ? Math.round((normalizedAttendees / normalizedTotalParticipants) * 100)
      : 0,
    program_breakdown: Array.isArray(programBreakdown)
      ? programBreakdown.map((item) => ({
        program: item.program,
        total: Number(item.total) || 0,
        present: Number(item.present) || 0,
        late: Number(item.late) || 0,
        incomplete: Number(item.incomplete) || 0,
        absent: Number(item.absent) || 0,
      }))
      : [],
  }
}

function createAttendancePreviewRow({
  id,
  eventId,
  student,
  timeIn = null,
  timeOut = null,
  status = 'present',
  method = 'face_scan',
}) {
  const firstName = String(student?.first_name || '').trim()
  const lastName = String(student?.last_name || '').trim()
  const fullName = [firstName, lastName].filter(Boolean).join(' ').trim() || student?.email || 'Student'
  const normalizedStatus = String(status || 'present').toLowerCase()
  const durationMinutes = timeIn && timeOut
    ? Math.max(0, Math.round((new Date(timeOut).getTime() - new Date(timeIn).getTime()) / 60000))
    : null

  return normalizeEventAttendanceWithStudent({
    student_id: student?.student_profile?.student_id || student?.id || null,
    student_name: fullName,
    attendance: {
      id,
      event_id: eventId,
      student_id: student?.student_profile?.id || student?.id || null,
      method,
      status: normalizedStatus,
      display_status: normalizedStatus,
      time_in: timeIn,
      time_out: timeOut,
      duration_minutes: durationMinutes,
      completion_state: normalizedStatus === 'absent'
        ? 'completed'
        : timeIn && timeOut
        ? 'completed'
        : timeIn
        ? 'incomplete'
        : null,
    },
  })
}

function createSsgPreviewBundle() {
  const students = [
    createStudent({
      id: 5101,
      studentId: '2026-SSG-001',
      firstName: 'Lea',
      lastName: 'Navarro',
      email: 'lea.navarro@preview.aura',
      departmentId: 11,
      departmentName: 'College of Engineering',
      programId: 111,
      programName: 'BS Computer Engineering',
      yearLevel: 4,
    }),
    createStudent({
      id: 5102,
      studentId: '2026-SSG-002',
      firstName: 'Noel',
      lastName: 'Rivera',
      email: 'noel.rivera@preview.aura',
      departmentId: 12,
      departmentName: 'College of Arts and Sciences',
      programId: 121,
      programName: 'BS Biology',
      yearLevel: 3,
    }),
    createStudent({
      id: 5103,
      studentId: '2026-SSG-003',
      firstName: 'Aya',
      lastName: 'Torres',
      email: 'aya.torres@preview.aura',
      departmentId: 13,
      departmentName: 'College of Business',
      programId: 131,
      programName: 'BS Accountancy',
      yearLevel: 2,
    }),
    createStudent({
      id: 5104,
      studentId: '2026-SSG-004',
      firstName: 'Marco',
      lastName: 'Sison',
      email: 'marco.sison@preview.aura',
      departmentId: 14,
      departmentName: 'College of Education',
      programId: 141,
      programName: 'B Secondary Education',
      yearLevel: 4,
    }),
    createStudent({
      id: 5105,
      studentId: '2026-SSG-005',
      firstName: 'Celine',
      lastName: 'Uy',
      email: 'celine.uy@preview.aura',
      departmentId: 15,
      departmentName: 'College of Computing',
      programId: 151,
      programName: 'BS Information Technology',
      yearLevel: 1,
    }),
    createStudent({
      id: 5106,
      studentId: '2026-SSG-006',
      firstName: 'Andre',
      lastName: 'Bello',
      email: 'andre.bello@preview.aura',
      departmentId: 16,
      departmentName: 'College of Hospitality',
      programId: 161,
      programName: 'BS Hospitality Management',
      yearLevel: 2,
    }),
  ]

  const currentUser = normalizeUserWithRelations({
    id: 5001,
    email: 'ssg.president@preview.aura',
    first_name: 'Mira',
    last_name: 'Santos',
    school_id: PREVIEW_SCHOOL.school_id,
    school_name: PREVIEW_SCHOOL.school_name,
    school_code: PREVIEW_SCHOOL.school_code,
    roles: [
      { role: { id: 1, name: 'student' } },
      { role: { id: 2, name: 'student_council' } },
    ],
    student_profile: {
      id: 5901,
      user_id: 5001,
      school_id: PREVIEW_SCHOOL.school_id,
      student_id: '2026-SSG-000',
      department_id: 15,
      program_id: 151,
      year_level: 4,
      is_face_registered: true,
      registration_complete: true,
    },
    ssg_profile: {
      id: 7001,
      organization_acronym: 'SSG',
      organization_name: 'Supreme Student Government',
      position_title: 'President',
    },
  })

  const unit = normalizeGovernanceUnitDetail({
    id: 7001,
    unit_code: 'SSG',
    unit_name: 'Supreme Student Government',
    description: 'Campus-wide student governance responsible for university-level initiatives and college council oversight.',
    unit_type: 'SSG',
    school_id: PREVIEW_SCHOOL.school_id,
    is_active: true,
    created_at: isoOffset({ days: -320 }),
    updated_at: isoOffset({ days: -3 }),
    members: [
      createMember({
        id: 1,
        user: normalizeGovernanceUserSummary({
          ...currentUser,
          student_profile: {
            student_id: '2026-SSG-000',
            department_id: 15,
            program_id: 151,
            department_name: 'College of Computing',
            program_name: 'BS Information Technology',
            year_level: 4,
          },
        }),
        positionTitle: 'President',
        permissionCodes: SSG_PERMISSION_CODES,
      }),
      createMember({
        id: 2,
        user: students[0],
        positionTitle: 'Vice President',
        permissionCodes: ['manage_events', 'manage_members', 'assign_permissions'],
      }),
      createMember({
        id: 3,
        user: students[2],
        positionTitle: 'Secretary',
        permissionCodes: ['manage_announcements', 'manage_students', 'view_students'],
      }),
      createMember({
        id: 4,
        user: students[3],
        positionTitle: 'Treasurer',
        permissionCodes: ['manage_events', 'manage_attendance'],
      }),
    ],
    unit_permissions: createPermissionRecords(SSG_PERMISSION_CODES).map((permission, index) => ({
      id: index + 1,
      governance_unit_id: 7001,
      permission_id: permission.id,
      permission_code: permission.permission_code,
      permission_name: permission.permission_name,
      permission,
    })),
  })

  return {
    variant: 'ssg',
    user: currentUser,
    schoolSettings: PREVIEW_SCHOOL,
    totalImportedStudents: 14876,
    permissionCodes: [...SSG_PERMISSION_CODES],
    governanceAccess: createGovernanceAccess(unit, SSG_PERMISSION_CODES),
    activeUnit: unit,
    members: unit.members.map(mapGovernanceMemberToCouncilMember),
    students,
    events: createCouncilEvents([
      {
        id: 7201,
        name: 'University Leadership Summit',
        location: 'Main Auditorium',
        scope_label: 'Campus Wide',
        status: 'upcoming',
        start_datetime: isoOffset({ days: 2, hours: 9 }),
        end_datetime: isoOffset({ days: 2, hours: 13 }),
        geo_required: true,
        geo_latitude: 8.1549,
        geo_longitude: 123.8417,
        geo_radius_m: 180,
        geo_max_accuracy_m: 40,
      },
      {
        id: 7202,
        name: 'Charter Day Rally',
        location: 'University Oval',
        scope_label: 'Campus Wide',
        status: 'ongoing',
        start_datetime: isoOffset({ hours: -1 }),
        end_datetime: isoOffset({ hours: 2 }),
        geo_required: true,
        geo_latitude: 8.1555,
        geo_longitude: 123.8421,
        geo_radius_m: 220,
        geo_max_accuracy_m: 45,
      },
      {
        id: 7203,
        name: 'Student Wellness Congress',
        location: 'Cultural Center',
        scope_label: 'Campus Wide',
        status: 'completed',
        start_datetime: isoOffset({ days: -6, hours: 8 }),
        end_datetime: isoOffset({ days: -6, hours: 12 }),
        geo_required: false,
      },
    ]),
    announcements: [
      {
        id: 7301,
        title: 'Leadership Summit Dry Run',
        body: 'All college councils must submit their final delegate count before 5:00 PM today.',
        status: 'published',
        created_at: isoOffset({ hours: -7 }),
        seen_count: 450,
        audience_count: 548,
      },
      {
        id: 7302,
        title: 'Campus Cleanup Mobilization',
        body: 'Department representatives should report to the University Oval at 7:30 AM.',
        status: 'published',
        created_at: isoOffset({ days: -1, hours: -2 }),
        seen_count: 398,
        audience_count: 548,
      },
    ],
    eventReports: [
      createEventReport({
        eventId: 7202,
        eventName: 'Charter Day Rally',
        eventDate: isoOffset({ hours: -1 }),
        eventLocation: 'University Oval',
        totalParticipants: 520,
        attendees: 432,
        lateAttendees: 46,
        incompleteAttendees: 18,
        absentees: 42,
        programBreakdown: [
          { program: 'BS Computer Engineering', total: 120, present: 96, late: 10, incomplete: 4, absent: 10 },
          { program: 'BS Biology', total: 98, present: 74, late: 8, incomplete: 3, absent: 13 },
          { program: 'BS Accountancy', total: 104, present: 88, late: 9, incomplete: 4, absent: 3 },
          { program: 'B Secondary Education', total: 92, present: 71, late: 7, incomplete: 3, absent: 11 },
          { program: 'BS Information Technology', total: 106, present: 103, late: 12, incomplete: 4, absent: 5 },
        ],
      }),
      createEventReport({
        eventId: 7203,
        eventName: 'Student Wellness Congress',
        eventDate: isoOffset({ days: -6, hours: 8 }),
        eventLocation: 'Cultural Center',
        totalParticipants: 468,
        attendees: 384,
        lateAttendees: 38,
        incompleteAttendees: 0,
        absentees: 46,
        programBreakdown: [
          { program: 'BS Computer Engineering', total: 96, present: 82, late: 7, incomplete: 0, absent: 7 },
          { program: 'BS Biology', total: 90, present: 71, late: 8, incomplete: 0, absent: 11 },
          { program: 'BS Accountancy', total: 94, present: 78, late: 6, incomplete: 0, absent: 10 },
          { program: 'B Secondary Education', total: 88, present: 70, late: 7, incomplete: 0, absent: 11 },
          { program: 'BS Information Technology', total: 100, present: 83, late: 10, incomplete: 0, absent: 7 },
        ],
      }),
    ],
    eventAttendanceRecords: {
      7202: [
        createAttendancePreviewRow({ id: 7501, eventId: 7202, student: students[0], timeIn: isoOffset({ minutes: -52 }), timeOut: isoOffset({ hours: 1, minutes: 4 }), status: 'present' }),
        createAttendancePreviewRow({ id: 7502, eventId: 7202, student: students[1], timeIn: isoOffset({ minutes: -31 }), timeOut: isoOffset({ hours: 1, minutes: 12 }), status: 'late' }),
        createAttendancePreviewRow({ id: 7503, eventId: 7202, student: students[2], timeIn: isoOffset({ minutes: -44 }), timeOut: null, status: 'present' }),
        createAttendancePreviewRow({ id: 7504, eventId: 7202, student: students[3], timeIn: isoOffset({ minutes: -22 }), timeOut: isoOffset({ hours: 1, minutes: 20 }), status: 'late' }),
        createAttendancePreviewRow({ id: 7505, eventId: 7202, student: students[4], timeIn: isoOffset({ minutes: -63 }), timeOut: isoOffset({ hours: 1, minutes: 3 }), status: 'present' }),
        createAttendancePreviewRow({ id: 7506, eventId: 7202, student: students[5], timeIn: null, timeOut: null, status: 'absent', method: 'manual' }),
      ],
      7203: [
        createAttendancePreviewRow({ id: 7511, eventId: 7203, student: students[0], timeIn: isoOffset({ days: -6, hours: 8, minutes: 12 }), timeOut: isoOffset({ days: -6, hours: 11, minutes: 42 }), status: 'present' }),
        createAttendancePreviewRow({ id: 7512, eventId: 7203, student: students[1], timeIn: isoOffset({ days: -6, hours: 8, minutes: 29 }), timeOut: isoOffset({ days: -6, hours: 11, minutes: 31 }), status: 'late' }),
        createAttendancePreviewRow({ id: 7513, eventId: 7203, student: students[2], timeIn: isoOffset({ days: -6, hours: 8, minutes: 18 }), timeOut: isoOffset({ days: -6, hours: 11, minutes: 55 }), status: 'present' }),
        createAttendancePreviewRow({ id: 7514, eventId: 7203, student: students[3], timeIn: isoOffset({ days: -6, hours: 8, minutes: 41 }), timeOut: isoOffset({ days: -6, hours: 11, minutes: 27 }), status: 'late' }),
        createAttendancePreviewRow({ id: 7515, eventId: 7203, student: students[4], timeIn: null, timeOut: null, status: 'absent', method: 'manual' }),
      ],
    },
    attendance: {
      summary: {
        total_events: 12,
        total_present: 1486,
        total_absent: 238,
        total_late: 142,
      },
      records: [
        {
          id: 7401,
          event_id: 7203,
          event_name: 'Student Wellness Congress',
          created_at: isoOffset({ days: -6, hours: 12 }),
          status: 'present',
        },
        {
          id: 7402,
          event_id: 7194,
          event_name: 'Campus Leaders Assembly',
          created_at: isoOffset({ days: -14, hours: 11 }),
          status: 'late',
        },
        {
          id: 7403,
          event_id: 7182,
          event_name: 'Student Services Forum',
          created_at: isoOffset({ days: -21, hours: 10 }),
          status: 'present',
        },
      ],
    },
    createUnit: {
      childType: 'SG',
      scopeOptions: [
        { value: '11', label: 'College of Engineering' },
        { value: '12', label: 'College of Arts and Sciences' },
        { value: '13', label: 'College of Business' },
        { value: '14', label: 'College of Education' },
      ],
    },
  }
}

function createSgPreviewBundle() {
  const students = [
    createStudent({
      id: 6101,
      studentId: '2026-SG-001',
      firstName: 'Janel',
      lastName: 'Mercado',
      email: 'janel.mercado@preview.aura',
      departmentId: 11,
      departmentName: 'College of Engineering',
      programId: 111,
      programName: 'BS Computer Engineering',
      yearLevel: 3,
    }),
    createStudent({
      id: 6102,
      studentId: '2026-SG-002',
      firstName: 'Enzo',
      lastName: 'Quiambao',
      email: 'enzo.quiambao@preview.aura',
      departmentId: 11,
      departmentName: 'College of Engineering',
      programId: 112,
      programName: 'BS Electrical Engineering',
      yearLevel: 2,
    }),
    createStudent({
      id: 6103,
      studentId: '2026-SG-003',
      firstName: 'Trina',
      lastName: 'Dizon',
      email: 'trina.dizon@preview.aura',
      departmentId: 11,
      departmentName: 'College of Engineering',
      programId: 113,
      programName: 'BS Mechanical Engineering',
      yearLevel: 4,
    }),
    createStudent({
      id: 6104,
      studentId: '2026-SG-004',
      firstName: 'Harvey',
      lastName: 'Lao',
      email: 'harvey.lao@preview.aura',
      departmentId: 11,
      departmentName: 'College of Engineering',
      programId: 114,
      programName: 'BS Civil Engineering',
      yearLevel: 1,
    }),
    createStudent({
      id: 6105,
      studentId: '2026-SG-005',
      firstName: 'Mina',
      lastName: 'Cabiles',
      email: 'mina.cabiles@preview.aura',
      departmentId: 11,
      departmentName: 'College of Engineering',
      programId: 115,
      programName: 'BS Industrial Engineering',
      yearLevel: 3,
    }),
  ]

  const currentUser = normalizeUserWithRelations({
    id: 6001,
    email: 'engineering.sg@preview.aura',
    first_name: 'Paula',
    last_name: 'Reyes',
    school_id: PREVIEW_SCHOOL.school_id,
    school_name: PREVIEW_SCHOOL.school_name,
    school_code: PREVIEW_SCHOOL.school_code,
    roles: [
      { role: { id: 1, name: 'student' } },
      { role: { id: 2, name: 'student_council' } },
    ],
    student_profile: {
      id: 6901,
      user_id: 6001,
      school_id: PREVIEW_SCHOOL.school_id,
      student_id: '2026-SG-000',
      department_id: 11,
      program_id: 111,
      year_level: 4,
      is_face_registered: true,
      registration_complete: true,
    },
    ssg_profile: {
      id: 7101,
      organization_acronym: 'COE-SG',
      organization_name: 'College of Engineering Student Government',
      position_title: 'President',
    },
  })

  const unit = normalizeGovernanceUnitDetail({
    id: 7101,
    unit_code: 'COE-SG',
    unit_name: 'College of Engineering Student Government',
    description: 'College-scoped governance unit managing engineering events, organizations, and student representation.',
    unit_type: 'SG',
    school_id: PREVIEW_SCHOOL.school_id,
    department_id: 11,
    is_active: true,
    created_at: isoOffset({ days: -210 }),
    updated_at: isoOffset({ days: -2 }),
    members: [
      createMember({
        id: 11,
        user: normalizeGovernanceUserSummary({
          ...currentUser,
          student_profile: {
            student_id: '2026-SG-000',
            department_id: 11,
            program_id: 111,
            department_name: 'College of Engineering',
            program_name: 'BS Computer Engineering',
            year_level: 4,
          },
        }),
        positionTitle: 'President',
        permissionCodes: SG_PERMISSION_CODES,
      }),
      createMember({
        id: 12,
        user: students[1],
        positionTitle: 'Vice President',
        permissionCodes: ['manage_events', 'manage_members', 'create_org'],
      }),
      createMember({
        id: 13,
        user: students[2],
        positionTitle: 'Secretary',
        permissionCodes: ['manage_announcements', 'view_students'],
      }),
      createMember({
        id: 14,
        user: students[4],
        positionTitle: 'Auditor',
        permissionCodes: ['manage_attendance', 'manage_students'],
      }),
    ],
    unit_permissions: createPermissionRecords(SG_PERMISSION_CODES).map((permission, index) => ({
      id: 200 + index + 1,
      governance_unit_id: 7101,
      permission_id: permission.id,
      permission_code: permission.permission_code,
      permission_name: permission.permission_name,
      permission,
    })),
  })

  return {
    variant: 'sg',
    user: currentUser,
    schoolSettings: PREVIEW_SCHOOL,
    permissionCodes: [...SG_PERMISSION_CODES],
    governanceAccess: createGovernanceAccess(unit, SG_PERMISSION_CODES),
    activeUnit: unit,
    members: unit.members.map(mapGovernanceMemberToCouncilMember),
    students,
    events: createCouncilEvents([
      {
        id: 8201,
        name: 'Engineering General Assembly',
        location: 'Engineering Function Hall',
        scope_label: 'College of Engineering',
        status: 'upcoming',
        start_datetime: isoOffset({ days: 1, hours: 10 }),
        end_datetime: isoOffset({ days: 1, hours: 14 }),
        geo_required: true,
        geo_latitude: 8.1552,
        geo_longitude: 123.8427,
        geo_radius_m: 130,
        geo_max_accuracy_m: 35,
      },
      {
        id: 8202,
        name: 'Innovation Expo Briefing',
        location: 'Engineering AVR',
        scope_label: 'College of Engineering',
        status: 'ongoing',
        start_datetime: isoOffset({ hours: -2 }),
        end_datetime: isoOffset({ hours: 1 }),
        geo_required: false,
      },
      {
        id: 8203,
        name: 'Department Intramurals Planning',
        location: 'Dean Conference Room',
        scope_label: 'College of Engineering',
        status: 'completed',
        start_datetime: isoOffset({ days: -4, hours: 9 }),
        end_datetime: isoOffset({ days: -4, hours: 11 }),
        geo_required: false,
      },
    ]),
    announcements: [
      {
        id: 8301,
        title: 'Org Accreditation Window',
        body: 'All engineering organizations must submit their updated officer list before Friday noon.',
        status: 'published',
        created_at: isoOffset({ hours: -9 }),
        seen_count: 198,
        audience_count: 240,
      },
      {
        id: 8302,
        title: 'Assembly Registration Reminder',
        body: 'Program representatives should complete attendance registration before entering the hall.',
        status: 'draft',
        created_at: isoOffset({ days: -2, hours: -4 }),
      },
    ],
    eventReports: [
      createEventReport({
        eventId: 8202,
        eventName: 'Innovation Expo Briefing',
        eventDate: isoOffset({ hours: -2 }),
        eventLocation: 'Engineering AVR',
        totalParticipants: 214,
        attendees: 176,
        lateAttendees: 22,
        incompleteAttendees: 9,
        absentees: 16,
        programBreakdown: [
          { program: 'BS Computer Engineering', total: 64, present: 50, late: 6, incomplete: 2, absent: 6 },
          { program: 'BS Electrical Engineering', total: 46, present: 39, late: 5, incomplete: 1, absent: 1 },
          { program: 'BS Mechanical Engineering', total: 38, present: 30, late: 4, incomplete: 2, absent: 2 },
          { program: 'BS Civil Engineering', total: 32, present: 25, late: 3, incomplete: 1, absent: 3 },
          { program: 'BS Industrial Engineering', total: 34, present: 32, late: 4, incomplete: 3, absent: 1 },
        ],
      }),
      createEventReport({
        eventId: 8203,
        eventName: 'Department Intramurals Planning',
        eventDate: isoOffset({ days: -4, hours: 9 }),
        eventLocation: 'Dean Conference Room',
        totalParticipants: 186,
        attendees: 148,
        lateAttendees: 19,
        incompleteAttendees: 0,
        absentees: 19,
        programBreakdown: [
          { program: 'BS Computer Engineering', total: 52, present: 43, late: 4, incomplete: 0, absent: 5 },
          { program: 'BS Electrical Engineering', total: 38, present: 31, late: 4, incomplete: 0, absent: 3 },
          { program: 'BS Mechanical Engineering', total: 33, present: 25, late: 4, incomplete: 0, absent: 4 },
          { program: 'BS Civil Engineering', total: 30, present: 23, late: 3, incomplete: 0, absent: 4 },
          { program: 'BS Industrial Engineering', total: 33, present: 26, late: 4, incomplete: 0, absent: 3 },
        ],
      }),
    ],
    eventAttendanceRecords: {
      8202: [
        createAttendancePreviewRow({ id: 8501, eventId: 8202, student: students[0], timeIn: isoOffset({ hours: -1, minutes: 44 }), timeOut: null, status: 'present' }),
        createAttendancePreviewRow({ id: 8502, eventId: 8202, student: students[1], timeIn: isoOffset({ hours: -1, minutes: 22 }), timeOut: isoOffset({ minutes: 18 }), status: 'late' }),
        createAttendancePreviewRow({ id: 8503, eventId: 8202, student: students[2], timeIn: isoOffset({ hours: -1, minutes: 38 }), timeOut: isoOffset({ minutes: 24 }), status: 'present' }),
        createAttendancePreviewRow({ id: 8504, eventId: 8202, student: students[3], timeIn: isoOffset({ hours: -1, minutes: 9 }), timeOut: isoOffset({ minutes: 27 }), status: 'late' }),
        createAttendancePreviewRow({ id: 8505, eventId: 8202, student: students[4], timeIn: null, timeOut: null, status: 'absent', method: 'manual' }),
      ],
      8203: [
        createAttendancePreviewRow({ id: 8511, eventId: 8203, student: students[0], timeIn: isoOffset({ days: -4, hours: 9, minutes: 5 }), timeOut: isoOffset({ days: -4, hours: 10, minutes: 46 }), status: 'present' }),
        createAttendancePreviewRow({ id: 8512, eventId: 8203, student: students[1], timeIn: isoOffset({ days: -4, hours: 9, minutes: 18 }), timeOut: isoOffset({ days: -4, hours: 10, minutes: 38 }), status: 'late' }),
        createAttendancePreviewRow({ id: 8513, eventId: 8203, student: students[2], timeIn: isoOffset({ days: -4, hours: 9, minutes: 11 }), timeOut: isoOffset({ days: -4, hours: 10, minutes: 41 }), status: 'present' }),
        createAttendancePreviewRow({ id: 8514, eventId: 8203, student: students[3], timeIn: isoOffset({ days: -4, hours: 9, minutes: 33 }), timeOut: isoOffset({ days: -4, hours: 10, minutes: 37 }), status: 'late' }),
        createAttendancePreviewRow({ id: 8515, eventId: 8203, student: students[4], timeIn: null, timeOut: null, status: 'absent', method: 'manual' }),
      ],
    },
    attendance: {
      summary: {
        total_events: 8,
        total_present: 624,
        total_absent: 74,
        total_late: 58,
      },
      records: [
        {
          id: 8401,
          event_id: 8203,
          event_name: 'Department Intramurals Planning',
          created_at: isoOffset({ days: -4, hours: 11 }),
          status: 'present',
        },
        {
          id: 8402,
          event_id: 8194,
          event_name: 'Engineering Leadership Workshop',
          created_at: isoOffset({ days: -11, hours: 16 }),
          status: 'late',
        },
        {
          id: 8403,
          event_id: 8187,
          event_name: 'Program Officers Sync',
          created_at: isoOffset({ days: -19, hours: 18 }),
          status: 'absent',
        },
      ],
    },
    createUnit: {
      childType: 'ORG',
      scopeOptions: [
        { value: '111', label: 'BS Computer Engineering' },
        { value: '112', label: 'BS Electrical Engineering' },
        { value: '113', label: 'BS Mechanical Engineering' },
        { value: '114', label: 'BS Civil Engineering' },
      ],
    },
  }
}

export function resolveSgPreviewVariant(value = '') {
  const normalized = String(value || '').trim().toLowerCase()
  return normalized === 'sg' ? 'sg' : 'ssg'
}

const sgPreviewBundles = {
  ssg: createSsgPreviewBundle(),
  sg: createSgPreviewBundle(),
}

export function getSgPreviewBundle(variant = 'ssg') {
  return sgPreviewBundles[resolveSgPreviewVariant(variant)]
}

export const sgPreviewUser = getSgPreviewBundle('ssg').user
export const sgPreviewSchoolSettings = getSgPreviewBundle('ssg').schoolSettings
export const sgPreviewPermissionCodes = getSgPreviewBundle('ssg').permissionCodes
export const sgPreviewGovernanceAccess = getSgPreviewBundle('ssg').governanceAccess
export const sgPreviewSsgSetup = {
  unit: getSgPreviewBundle('ssg').activeUnit,
  total_imported_students: 14876,
}
