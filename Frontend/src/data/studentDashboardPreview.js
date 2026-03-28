import {
  normalizeAttendanceRecord,
  normalizeEvent,
  normalizeSchoolSettings,
  normalizeUserWithRelations,
} from '@/services/backendNormalizers.js'

const PREVIEW_SCHOOL_ID = 1999

function buildRelativeIso({ days = 0, hours = 0, minutes = 0 }) {
  const date = new Date()
  date.setDate(date.getDate() + days)
  date.setHours(date.getHours() + hours)
  date.setMinutes(date.getMinutes() + minutes)
  return date.toISOString()
}

export const studentDashboardPreviewData = {
  user: normalizeUserWithRelations({
    id: 199901,
    email: 'student.preview@aura.local',
    first_name: 'User',
    last_name: 'Preview',
    school_id: PREVIEW_SCHOOL_ID,
    school_name: 'University Name',
    school_code: 'UNI',
    roles: [{ role: { id: 2, name: 'student' } }],
    student_profile: {
      id: 199911,
      user_id: 199901,
      school_id: PREVIEW_SCHOOL_ID,
      student_id: '2026-001',
      department_id: 1,
      program_id: 1,
      year_level: 2,
      is_face_registered: true,
      registration_complete: true,
    },
  }),
  schoolSettings: normalizeSchoolSettings({
    school_id: PREVIEW_SCHOOL_ID,
    school_name: 'University Name',
    school_code: 'UNI',
    logo_url: '/logos/aura.png',
    primary_color: '#AAFF00',
    secondary_color: '#64748B',
    accent_color: '#0A0A0A',
  }),
  events: [
    normalizeEvent({
      id: 1,
      school_id: PREVIEW_SCHOOL_ID,
      name: 'University Assembly',
      location: 'Main Campus',
      status: 'ongoing',
      start_datetime: buildRelativeIso({ hours: -1 }),
      end_datetime: buildRelativeIso({ hours: 2 }),
    }),
    normalizeEvent({
      id: 2,
      school_id: PREVIEW_SCHOOL_ID,
      name: 'Program Orientation',
      location: 'Auditorium',
      status: 'upcoming',
      start_datetime: buildRelativeIso({ days: 1, hours: 2 }),
      end_datetime: buildRelativeIso({ days: 1, hours: 4 }),
    }),
    normalizeEvent({
      id: 3,
      school_id: PREVIEW_SCHOOL_ID,
      name: 'Leadership Summit',
      location: 'Conference Hall',
      status: 'upcoming',
      start_datetime: buildRelativeIso({ days: 3, hours: 3 }),
      end_datetime: buildRelativeIso({ days: 3, hours: 6 }),
    }),
  ],
  attendanceRecords: [
    normalizeAttendanceRecord({
      id: 101,
      event_id: 1,
      status: 'present',
      time_in: buildRelativeIso({ hours: -1, minutes: 12 }),
      created_at: buildRelativeIso({ hours: -1, minutes: 12 }),
    }),
    normalizeAttendanceRecord({
      id: 102,
      event_id: 2,
      status: 'late',
      time_in: buildRelativeIso({ days: -3, hours: -2, minutes: -8 }),
      created_at: buildRelativeIso({ days: -3, hours: -2, minutes: -8 }),
    }),
    normalizeAttendanceRecord({
      id: 103,
      event_id: 3,
      status: 'absent',
      created_at: buildRelativeIso({ days: -9, hours: -1 }),
    }),
  ],
}
