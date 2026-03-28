const defaultSchoolLogo = '/logos/aura.png'
import {
  normalizeDepartment,
  normalizeEvent,
  normalizeProgram,
  normalizeSchoolSettings,
  normalizeUserWithRelations,
} from '@/services/backendNormalizers.js'

const PREVIEW_SCHOOL_ID = 999
const PREVIEW_ROLE = 'campus_admin'

const previewProgramSeeds = [
  { name: 'BS Computer Engineering', department_id: 1 },
  { name: 'BS Civil Engineering', department_id: 1 },
  { name: 'BS Electrical Engineering', department_id: 1 },
  { name: 'BS Information Technology', department_id: 1 },
  { name: 'BS Computer Science', department_id: 1 },
  { name: 'BS Data Science', department_id: 1 },
  { name: 'BS Mechanical Engineering', department_id: 2 },
  { name: 'BS Industrial Engineering', department_id: 2 },
  { name: 'BS Architecture', department_id: 2 },
  { name: 'BA Communication', department_id: 3 },
  { name: 'BA English Language Studies', department_id: 3 },
  { name: 'BA Political Science', department_id: 3 },
  { name: 'BS Accountancy', department_id: 4 },
  { name: 'BS Business Administration', department_id: 4 },
  { name: 'BS Hospitality Management', department_id: 4 },
  { name: 'B Secondary Education', department_id: 5 },
  { name: 'B Elementary Education', department_id: 5 },
  { name: 'Bachelor of Physical Education', department_id: 5 },
  { name: 'BS Biology', department_id: 6 },
  { name: 'BS Chemistry', department_id: 6 },
  { name: 'BS Mathematics', department_id: 6 },
]

function buildPreviewPrograms() {
  const items = previewProgramSeeds.map((seed, index) => ({
    id: index + 1,
    school_id: PREVIEW_SCHOOL_ID,
    name: seed.name,
    department_ids: [seed.department_id],
  }))

  while (items.length < 42) {
    const fillerIndex = items.length + 1
    const departmentId = ((fillerIndex - 1) % 6) + 1
    items.push({
      id: fillerIndex,
      school_id: PREVIEW_SCHOOL_ID,
      name: `Program Studies ${fillerIndex}`,
      department_ids: [departmentId],
    })
  }

  return items
}

function buildPreviewUsers() {
  return [
    {
      id: 999101,
      email: 'student.one@aura.local',
      first_name: 'Aly',
      last_name: 'Domingo',
      school_id: PREVIEW_SCHOOL_ID,
      school_name: 'University Name',
      roles: [{ role: { id: 2, name: 'student' } }],
      must_change_password: true,
      student_profile: {
        id: 999201,
        user_id: 999101,
        school_id: PREVIEW_SCHOOL_ID,
        student_id: '2026-001',
        department_id: 1,
        program_id: 1,
        year_level: 2,
        is_face_registered: true,
        registration_complete: true,
      },
    },
    {
      id: 999102,
      email: 'student.two@aura.local',
      first_name: 'Mika',
      last_name: 'Velasco',
      school_id: PREVIEW_SCHOOL_ID,
      school_name: 'University Name',
      roles: [{ role: { id: 2, name: 'student' } }],
      must_change_password: true,
      student_profile: {
        id: 999202,
        user_id: 999102,
        school_id: PREVIEW_SCHOOL_ID,
        student_id: '2026-002',
        department_id: 1,
        program_id: 2,
        year_level: 1,
        is_face_registered: false,
        registration_complete: false,
      },
    },
    {
      id: 999103,
      email: 'student.three@aura.local',
      first_name: 'Jade',
      last_name: 'Morales',
      school_id: PREVIEW_SCHOOL_ID,
      school_name: 'University Name',
      roles: [{ role: { id: 2, name: 'student' } }],
      must_change_password: false,
      student_profile: {
        id: 999203,
        user_id: 999103,
        school_id: PREVIEW_SCHOOL_ID,
        student_id: '2026-003',
        department_id: 3,
        program_id: 10,
        year_level: 2,
        is_face_registered: true,
        registration_complete: true,
      },
    },
    {
      id: 999104,
      email: 'student.four@aura.local',
      first_name: 'Kyle',
      last_name: 'Santos',
      school_id: PREVIEW_SCHOOL_ID,
      school_name: 'University Name',
      roles: [{ role: { id: 2, name: 'student' } }],
      must_change_password: true,
      student_profile: {
        id: 999204,
        user_id: 999104,
        school_id: PREVIEW_SCHOOL_ID,
        student_id: '2026-004',
        department_id: 4,
        program_id: 13,
        year_level: 3,
        is_face_registered: true,
        registration_complete: true,
      },
    },
    {
      id: 999105,
      email: 'student.five@aura.local',
      first_name: 'Paolo',
      last_name: 'Ramos',
      school_id: PREVIEW_SCHOOL_ID,
      school_name: 'University Name',
      roles: [{ role: { id: 2, name: 'student' } }],
      must_change_password: false,
      student_profile: {
        id: 999205,
        user_id: 999105,
        school_id: PREVIEW_SCHOOL_ID,
        student_id: '2026-005',
        department_id: 6,
        program_id: 19,
        year_level: 4,
        is_face_registered: true,
        registration_complete: true,
      },
    },
  ]
}

function buildRelativeIso({ days = 0, hours = 0, minutes = 0 }) {
  const date = new Date()
  date.setDate(date.getDate() + days)
  date.setHours(date.getHours() + hours)
  date.setMinutes(date.getMinutes() + minutes)
  return date.toISOString()
}

function normalizeAttendanceSummaryPayload(payload = {}) {
  const summary = payload?.summary ?? {}

  return {
    summary: {
      total_attendance_records: toCount(summary.total_attendance_records),
      present_count: toCount(summary.present_count),
      late_count: toCount(summary.late_count),
      attended_count: toCount(summary.attended_count),
      absent_count: toCount(summary.absent_count),
      excused_count: toCount(summary.excused_count),
      attendance_rate: toPercent(summary.attendance_rate),
      unique_students: toCount(summary.unique_students),
      unique_events: toCount(summary.unique_events),
    },
  }
}

function toCount(value) {
  const normalized = Number(value)
  return Number.isFinite(normalized) && normalized > 0 ? Math.round(normalized) : 0
}

function toPercent(value) {
  const normalized = Number(value)
  if (!Number.isFinite(normalized)) return 0
  return Math.max(0, Math.min(100, normalized))
}

function createRawPreviewPayload() {
  return {
    user: {
      id: 999001,
      email: 'schoolit.preview@aura.local',
      first_name: 'School IT',
      middle_name: null,
      last_name: 'Preview',
      school_id: PREVIEW_SCHOOL_ID,
      school_name: 'University Name',
      school_code: 'UNI',
      avatar_url: '',
      roles: [{ role: { id: 1, name: PREVIEW_ROLE } }],
    },
    schoolSettings: {
      school_id: PREVIEW_SCHOOL_ID,
      school_name: 'University Name',
      school_code: 'UNI',
      logo_url: defaultSchoolLogo,
      primary_color: '#AAFF00',
      secondary_color: '#64748B',
      accent_color: '#0A0A0A',
    },
    departments: [
      { id: 1, school_id: PREVIEW_SCHOOL_ID, name: 'College of Computing' },
      { id: 2, school_id: PREVIEW_SCHOOL_ID, name: 'College of Engineering' },
      { id: 3, school_id: PREVIEW_SCHOOL_ID, name: 'College of Arts' },
      { id: 4, school_id: PREVIEW_SCHOOL_ID, name: 'College of Business' },
      { id: 5, school_id: PREVIEW_SCHOOL_ID, name: 'College of Education' },
      { id: 6, school_id: PREVIEW_SCHOOL_ID, name: 'College of Science' },
    ],
    programs: buildPreviewPrograms(),
    users: buildPreviewUsers(),
    events: [
      {
        id: 1,
        school_id: PREVIEW_SCHOOL_ID,
        name: 'University Assembly',
        location: 'Main Campus',
        status: 'ongoing',
        start_datetime: buildRelativeIso({ hours: -1 }),
        end_datetime: buildRelativeIso({ hours: 2 }),
        attendance_summary: {
          total_attendance_records: 120,
          present_count: 68,
          late_count: 14,
          absent_count: 24,
          excused_count: 14,
        },
        attendances: [],
      },
      {
        id: 2,
        school_id: PREVIEW_SCHOOL_ID,
        name: 'Program Orientation',
        location: 'Auditorium',
        status: 'upcoming',
        start_datetime: buildRelativeIso({ days: 1, hours: 2 }),
        end_datetime: buildRelativeIso({ days: 1, hours: 4 }),
        attendance_summary: {
          total_attendance_records: 0,
          present_count: 0,
          late_count: 0,
          absent_count: 0,
          excused_count: 0,
        },
        attendances: [],
      },
    ],
    attendanceSummary: {
      summary: {
        total_attendance_records: 120,
        present_count: 68,
        late_count: 14,
        attended_count: 82,
        absent_count: 24,
        excused_count: 14,
        attendance_rate: 68.33,
        unique_students: 96,
        unique_events: 3,
      },
    },
  }
}

export function createSchoolItPreviewData(overrides = {}) {
  const raw = createRawPreviewPayload()
  const merged = {
    ...raw,
    ...overrides,
  }

  const schoolSettings = normalizeSchoolSettings(merged.schoolSettings)
  const user = normalizeUserWithRelations({
    ...merged.user,
    school_id: merged.user?.school_id ?? schoolSettings?.school_id,
    school_name: merged.user?.school_name ?? schoolSettings?.school_name,
    school_code: merged.user?.school_code ?? schoolSettings?.school_code,
  })

  return {
    user,
    schoolSettings,
    departments: Array.isArray(merged.departments)
      ? merged.departments.map(normalizeDepartment)
      : [],
    programs: Array.isArray(merged.programs)
      ? merged.programs.map(normalizeProgram)
      : [],
    users: Array.isArray(merged.users)
      ? merged.users.map(normalizeUserWithRelations)
      : [],
    events: Array.isArray(merged.events)
      ? merged.events.map(normalizeEvent)
      : [],
    attendanceSummary: normalizeAttendanceSummaryPayload(merged.attendanceSummary),
  }
}

export const schoolItPreviewData = createSchoolItPreviewData()
