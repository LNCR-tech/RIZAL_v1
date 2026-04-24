import { computed, ref, watch, unref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { useSgDashboard } from '@/composables/useSgDashboard.js'
import { useSgPreviewBundle } from '@/composables/useSgPreviewBundle.js'
import {
  getEventAttendance,
  getEventAttendanceReport,
  getCampusSsgSetup,
  getEvents,
  getGovernanceAccess,
  getGovernanceAnnouncements,
  getGovernanceDashboardOverview,
  getGovernanceStudents,
  getGovernanceUnitDetail,
  getGovernanceUnits,
} from '@/services/backendApi.js'
import {
  downloadGovernanceMasterlistCsv,
  downloadGovernanceParPdf,
} from '@/services/governanceReportExport.js'
import {
  normalizeGovernanceContext,
  resolvePreferredGovernanceUnit,
} from '@/services/governanceScope.js'
import {
  getGovernanceSectionDefinition,
  getGovernanceSectionDefinitions,
} from '@/data/governanceNavigation.js'
import {
  resolveEventDetailLocation,
  withPreservedGovernancePreviewQuery,
} from '@/services/routeWorkspace.js'

const MAX_UPCOMING_EVENTS = 5
const MAX_ANNOUNCEMENTS = 4
const MAX_ATTENTION_ITEMS = 4
const MAX_REPORT_EVENTS = 6

function resolveSourceValue(source, fallback = null) {
  if (typeof source === 'function') return source()
  const resolved = unref(source)
  return resolved == null ? fallback : resolved
}

function toNumber(value, fallback = null) {
  const normalized = Number(value)
  return Number.isFinite(normalized) ? normalized : fallback
}

function toNonNegativeInt(value) {
  const normalized = Number(value)
  return Number.isFinite(normalized) && normalized > 0 ? Math.round(normalized) : 0
}

function clampPercent(value) {
  const normalized = Number(value)
  if (!Number.isFinite(normalized)) return 0
  return Math.max(0, Math.min(100, Math.round(normalized)))
}

function isObject(value) {
  return Boolean(value) && typeof value === 'object'
}

function cloneRecord(value) {
  return isObject(value) ? { ...value } : value
}

function cloneArray(values = []) {
  return Array.isArray(values) ? values.map(cloneRecord) : []
}

function cloneRecordMap(values = {}) {
  return Object.entries(isObject(values) ? values : {}).reduce((accumulator, [key, records]) => {
    accumulator[key] = cloneArray(records)
    return accumulator
  }, {})
}

function formatCompactNumber(value) {
  const normalizedValue = Number(value || 0)
  if (!Number.isFinite(normalizedValue)) return '0'
  return new Intl.NumberFormat('en-US', {
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(normalizedValue)
}

function formatWholeNumber(value) {
  return new Intl.NumberFormat('en-US').format(toNonNegativeInt(value))
}

function formatPercentage(value) {
  return `${clampPercent(value)}%`
}

function formatPermissionLabel(value) {
  return String(value || '')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())
}

function sortGovernanceEvents(values = []) {
  const statusRank = {
    ongoing: 0,
    active: 0,
    upcoming: 1,
    completed: 2,
    cancelled: 3,
  }

  return [...values].sort((left, right) => {
    const leftRank = statusRank[String(left?.status || '').toLowerCase()] ?? 99
    const rightRank = statusRank[String(right?.status || '').toLowerCase()] ?? 99
    if (leftRank !== rightRank) return leftRank - rightRank

    return new Date(left?.start_datetime || left?.start_time || 0)
      - new Date(right?.start_datetime || right?.start_time || 0)
  })
}

function sortAnnouncements(values = []) {
  return [...values].sort((left, right) => {
    return new Date(right?.created_at || right?.updated_at || 0)
      - new Date(left?.created_at || left?.updated_at || 0)
  })
}

function formatDateTime(value, options = {}) {
  if (!value) return ''

  try {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      ...options,
    }).format(new Date(value))
  } catch {
    return ''
  }
}

function formatDateRange(startValue, endValue) {
  const startDate = startValue ? new Date(startValue) : null
  const endDate = endValue ? new Date(endValue) : null

  if (!startDate || Number.isNaN(startDate.getTime())) return 'Schedule pending'

  const sameDay = endDate && !Number.isNaN(endDate.getTime())
    ? startDate.toDateString() === endDate.toDateString()
    : false

  const startLabel = formatDateTime(startValue)
  if (!sameDay || !endDate || Number.isNaN(endDate.getTime())) {
    return startLabel
  }

  const endLabel = new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: '2-digit',
  }).format(endDate)

  return `${startLabel} - ${endLabel}`
}

function getStatusLabel(status) {
  const normalized = String(status || '').trim().toLowerCase()
  return normalized ? normalized.charAt(0).toUpperCase() + normalized.slice(1) : 'Unknown'
}

function getStudentUserRecord(student = null) {
  return student?.user || student || null
}

function formatStudentName(student) {
  const user = getStudentUserRecord(student)
  const firstName = user?.first_name
  const lastName = user?.last_name
  return [firstName, lastName].filter(Boolean).join(' ').trim() || user?.email || 'Student'
}

function formatStudentMeta(student) {
  const user = getStudentUserRecord(student)
  return (
    student?.student_profile?.student_id
    || user?.student_profile?.student_id
    || user?.email
    || 'Student record'
  )
}

function formatAnnouncementTime(value) {
  return formatDateTime(value) || 'Recently updated'
}

function formatDateOnly(value) {
  if (!value) return ''

  try {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
    }).format(new Date(value))
  } catch {
    return ''
  }
}

function formatTimeOnly(value) {
  if (!value) return ''

  try {
    return new Intl.DateTimeFormat('en-US', {
      hour: 'numeric',
      minute: '2-digit',
    }).format(new Date(value))
  } catch {
    return ''
  }
}

function formatEventLine(event) {
  const location = String(event?.location || 'Location pending').trim()
  const schedule = formatDateRange(event?.start_datetime || event?.start_time, event?.end_datetime || event?.end_time)
  return schedule ? `${location} · ${schedule}` : location
}

function getEventTimestamp(event = null, key = 'start') {
  const rawValue = key === 'end'
    ? (event?.end_datetime || event?.end_time)
    : (event?.start_datetime || event?.start_time)

  const timestamp = rawValue ? new Date(rawValue).getTime() : Number.NaN
  return Number.isFinite(timestamp) ? timestamp : null
}

function isEventLive(event = null) {
  const status = String(event?.status || '').toLowerCase()
  if (status === 'ongoing' || status === 'active') return true

  const now = Date.now()
  const start = getEventTimestamp(event, 'start')
  const end = getEventTimestamp(event, 'end')

  if (start == null || end == null) return false
  return now >= start && now <= end
}

function isEventCompleted(event = null) {
  const status = String(event?.status || '').toLowerCase()
  if (status === 'completed') return true

  const end = getEventTimestamp(event, 'end')
  return end != null && end < Date.now()
}

function isEventUpcoming(event = null) {
  if (isEventLive(event)) return false

  const status = String(event?.status || '').toLowerCase()
  if (status === 'upcoming') return true

  const start = getEventTimestamp(event, 'start')
  return start != null && start > Date.now()
}

function isWithinNextWeek(event = null) {
  if (isEventLive(event)) return true

  const start = getEventTimestamp(event, 'start')
  if (start == null) return false

  const now = Date.now()
  const oneWeekFromNow = now + (7 * 24 * 60 * 60 * 1000)
  return start >= now && start <= oneWeekFromNow
}

function summarizePreviewAttendance(previewBundle = null) {
  const summary = previewBundle?.attendance?.summary
  if (!isObject(summary)) return null

  const present = toNonNegativeInt(summary.total_present)
  const late = toNonNegativeInt(summary.total_late)
  const absent = toNonNegativeInt(summary.total_absent)
  const attended = present + late
  const total = attended + absent

  if (total <= 0) return null

  return {
    totalParticipants: total,
    attendees: attended,
    attendanceRate: clampPercent((attended / total) * 100),
  }
}

function buildPreviewReportsMap(values = []) {
  return (Array.isArray(values) ? values : []).reduce((accumulator, report) => {
    const eventId = Number(report?.event_id)
    if (!Number.isFinite(eventId)) return accumulator

    accumulator[eventId] = { ...report }
    return accumulator
  }, {})
}

function buildPreviewAttendanceMap(values = {}) {
  return cloneRecordMap(values)
}

function getAnnouncementReachData(announcement = null) {
  if (!isObject(announcement)) {
    return {
      percentage: null,
      seenCount: null,
      audienceCount: null,
      hasAnalytics: false,
    }
  }

  const percentage = [
    announcement.reach_rate,
    announcement.seen_percent,
    announcement.read_percent,
    announcement.view_rate,
  ]
    .map((value) => toNumber(value, null))
    .find((value) => value != null)

  const seenCount = [
    announcement.seen_count,
    announcement.seen_students,
    announcement.view_count,
    announcement.read_count,
    announcement.reach_count,
  ]
    .map((value) => toNumber(value, null))
    .find((value) => value != null)

  const audienceCount = [
    announcement.audience_count,
    announcement.target_count,
    announcement.recipient_count,
    announcement.total_recipients,
    announcement.delivered_count,
  ]
    .map((value) => toNumber(value, null))
    .find((value) => value != null)

  if (percentage != null) {
    return {
      percentage: clampPercent(percentage),
      seenCount,
      audienceCount,
      hasAnalytics: true,
    }
  }

  if (seenCount != null && audienceCount != null && audienceCount > 0) {
    return {
      percentage: clampPercent((seenCount / audienceCount) * 100),
      seenCount,
      audienceCount,
      hasAnalytics: true,
    }
  }

  return {
    percentage: null,
    seenCount,
    audienceCount,
    hasAnalytics: false,
  }
}

function hasSignedInAttendanceRecord(attendance = null) {
  if (!attendance || typeof attendance !== 'object') return false
  if (attendance.time_in) return true

  const status = String(
    attendance.display_status
    || attendance.check_in_status
    || attendance.status
    || ''
  ).trim().toLowerCase()

  return status === 'present' || status === 'late'
}

function buildAttendanceRecordKey(record = null) {
  const attendance = record?.attendance || record || {}
  const numericProfileId = Number(attendance?.student_id)
  if (Number.isFinite(numericProfileId)) return `profile:${numericProfileId}`

  const studentId = String(record?.student_id || '').trim()
  if (studentId) return `student:${studentId.toLowerCase()}`

  const studentName = String(record?.student_name || '').trim().toLowerCase()
  if (studentName) return `name:${studentName}`

  return `row:${String(attendance?.id || '').trim()}`
}

function dedupeAttendanceRecords(records = []) {
  const latestByStudent = new Map()

  for (const record of Array.isArray(records) ? records : []) {
    const key = buildAttendanceRecordKey(record)
    const existing = latestByStudent.get(key)
    const nextTimestamp = new Date(record?.attendance?.time_out || record?.attendance?.time_in || record?.created_at || 0).getTime()
    const existingTimestamp = new Date(existing?.attendance?.time_out || existing?.attendance?.time_in || existing?.created_at || 0).getTime()

    if (!existing || nextTimestamp >= existingTimestamp) {
      latestByStudent.set(key, record)
    }
  }

  return Array.from(latestByStudent.values())
}

function resolveStudentLookupKeys(student = null) {
  const keys = []
  const studentProfile = student?.student_profile || {}

  if (Number.isFinite(Number(student?.id))) keys.push(`user:${Number(student.id)}`)
  if (Number.isFinite(Number(studentProfile?.id))) keys.push(`profile:${Number(studentProfile.id)}`)

  const studentId = String(studentProfile?.student_id || '').trim()
  if (studentId) keys.push(`student:${studentId.toLowerCase()}`)

  const fullName = [student?.first_name, student?.last_name].filter(Boolean).join(' ').trim().toLowerCase()
  if (fullName) keys.push(`name:${fullName}`)

  return keys
}

function buildAttendanceStudentLookup(students = []) {
  const lookup = new Map()

  ;(Array.isArray(students) ? students : []).forEach((student) => {
    resolveStudentLookupKeys(student).forEach((key) => {
      if (!lookup.has(key)) lookup.set(key, student)
    })
  })

  return lookup
}

function resolveMatchedStudent(record = null, lookup = new Map()) {
  const attendance = record?.attendance || {}
  const keys = []
  const numericProfileId = Number(attendance?.student_id)
  if (Number.isFinite(numericProfileId)) keys.push(`profile:${numericProfileId}`)

  const recordStudentId = String(record?.student_id || '').trim()
  if (recordStudentId) keys.push(`student:${recordStudentId.toLowerCase()}`)

  const recordStudentName = String(record?.student_name || '').trim().toLowerCase()
  if (recordStudentName) keys.push(`name:${recordStudentName}`)

  for (const key of keys) {
    if (lookup.has(key)) return lookup.get(key)
  }

  return null
}

function buildRankedBreakdown(items = [], { title = '', summary = '', unitLabel = 'attendees' } = {}) {
  const sortedItems = [...items]
    .filter((item) => Number(item?.value) > 0)
    .sort((left, right) => Number(right.value) - Number(left.value))
    .slice(0, 5)

  const total = sortedItems.reduce((accumulator, item) => accumulator + (Number(item.value) || 0), 0)
  const peak = Math.max(1, ...sortedItems.map((item) => Number(item.value) || 0))

  return {
    title,
    summary,
    unitLabel,
    items: sortedItems.map((item, index) => {
      const value = Number(item.value) || 0
      const share = total > 0 ? (value / total) * 100 : 0

      return {
        key: item.key || `${item.label}-${index}`,
        label: item.label,
        value,
        valueLabel: formatWholeNumber(value),
        ratio: peak > 0 ? (value / peak) * 100 : 0,
        meta: `${formatPercentage(share)} of visible participation`,
      }
    }),
  }
}

function buildEventHealthInsight(focusEntry = null) {
  if (!focusEntry?.report) {
    return {
      focusEntry: null,
      percentage: 0,
      valueLabel: '--',
      totalLabel: '0',
      attendedLabel: '0',
      lateLabel: '0',
      absentLabel: '0',
      secondaryPercentage: 0,
      secondaryValueLabel: '--',
      secondaryLabel: 'No-show',
      eyebrow: 'Event Health',
      title: 'Awaiting attendance reports',
      summary: 'Live event health will appear after attendance reports are available.',
      statusLabel: 'No report',
      eventDateLabel: '',
    }
  }

  const report = focusEntry.report
  const event = focusEntry.event
  const totalParticipants = toNonNegativeInt(report.total_participants)
  const attendees = toNonNegativeInt(report.attendees)
  const lateAttendees = toNonNegativeInt(report.late_attendees)
  const absentees = toNonNegativeInt(report.absentees)
  const incompleteAttendees = toNonNegativeInt(report.incomplete_attendees)
  const attendanceRate = clampPercent(
    report.attendance_rate != null && report.attendance_rate !== ''
      ? report.attendance_rate
      : totalParticipants > 0
      ? (attendees / totalParticipants) * 100
      : 0
  )
  const noShowRate = totalParticipants > 0 ? clampPercent((absentees / totalParticipants) * 100) : 0

  return {
    focusEntry,
    percentage: attendanceRate,
    valueLabel: formatPercentage(attendanceRate),
    totalLabel: formatWholeNumber(totalParticipants),
    attendedLabel: formatWholeNumber(attendees),
    lateLabel: formatWholeNumber(lateAttendees),
    absentLabel: formatWholeNumber(absentees),
    incompleteLabel: formatWholeNumber(incompleteAttendees),
    secondaryPercentage: noShowRate,
    secondaryValueLabel: formatPercentage(noShowRate),
    secondaryLabel: 'No-show',
    eyebrow: isEventLive(event) ? 'Live Event Health' : 'Latest Event Health',
    title: event?.name || report.event_name || 'Governance event',
    summary: `${formatWholeNumber(attendees)} checked in from ${formatWholeNumber(totalParticipants)} expected participants.`,
    statusLabel: isEventLive(event) ? 'Live now' : 'Reported',
    eventDateLabel: formatDateRange(event?.start_datetime || report.event_date, event?.end_datetime),
  }
}

function buildDemographicInsight({
  focusEntry = null,
  attendanceRecords = [],
  reportEntries = [],
  attendanceRecordsByEventId = {},
  students = [],
} = {}) {
  const lookup = buildAttendanceStudentLookup(students)
  const departmentCounts = new Map()
  const yearCounts = new Map()
  const programCounts = new Map()
  let matchedRecords = 0

  const normalizedSources = focusEntry
    ? [{
      event: focusEntry.event,
      report: focusEntry.report,
      records: dedupeAttendanceRecords(attendanceRecords),
    }]
    : reportEntries.map((entry) => ({
      event: entry?.event,
      report: entry?.report,
      records: dedupeAttendanceRecords(attendanceRecordsByEventId[Number(entry?.event?.id)] || []),
    }))

  normalizedSources.forEach((source) => {
    source.records.forEach((record) => {
      if (!hasSignedInAttendanceRecord(record?.attendance)) return
      const student = resolveMatchedStudent(record, lookup)
      if (!student) return

      matchedRecords += 1
      const profile = student.student_profile || {}
      const departmentName = String(profile.department_name || '').trim()
      const programName = String(profile.program_name || '').trim()
      const yearLevel = Number(profile.year_level)

      if (departmentName) {
        departmentCounts.set(departmentName, (departmentCounts.get(departmentName) || 0) + 1)
      }
      if (programName) {
        programCounts.set(programName, (programCounts.get(programName) || 0) + 1)
      }
      if (Number.isFinite(yearLevel)) {
        const yearLabel = `Year ${yearLevel}`
        yearCounts.set(yearLabel, (yearCounts.get(yearLabel) || 0) + 1)
      }
    })
  })

  if (matchedRecords > 0 && departmentCounts.size > 1) {
    return buildRankedBreakdown(
      Array.from(departmentCounts.entries()).map(([label, value]) => ({ label, value })),
      {
        title: 'College Reach',
        summary: focusEntry
          ? 'Attendance spread across colleges for the selected event.'
          : 'Attendance spread across the colleges represented in recent reported events.',
      }
    )
  }

  if (matchedRecords > 0 && yearCounts.size > 1) {
    return buildRankedBreakdown(
      Array.from(yearCounts.entries()).map(([label, value]) => ({ label, value })),
      {
        title: 'Year Level Split',
        summary: focusEntry
          ? 'Attendance grouped by year level for the selected event.'
          : 'Recent participation grouped by year level.',
      }
    )
  }

  if (matchedRecords > 0 && programCounts.size > 1) {
    return buildRankedBreakdown(
      Array.from(programCounts.entries()).map(([label, value]) => ({ label, value })),
      {
        title: 'Program Participation',
        summary: focusEntry
          ? 'Attendance grouped by academic program for the selected event.'
          : 'Recent participation grouped by academic program.',
      }
    )
  }

  const departmentByProgram = new Map()
  ;(Array.isArray(students) ? students : []).forEach((student) => {
    const profile = student?.student_profile || {}
    const programName = String(profile.program_name || '').trim()
    const departmentName = String(profile.department_name || '').trim()
    if (programName && departmentName && !departmentByProgram.has(programName)) {
      departmentByProgram.set(programName, departmentName)
    }
  })

  const fallbackDepartmentCounts = new Map()
  const fallbackProgramCounts = new Map()

  normalizedSources.forEach((source) => {
    const breakdown = Array.isArray(source?.report?.program_breakdown) ? source.report.program_breakdown : []
    breakdown.forEach((item) => {
      const programName = String(item?.program || '').trim()
      const attendedCount = toNonNegativeInt(item?.present) + toNonNegativeInt(item?.late)
      if (!programName || attendedCount <= 0) return

      fallbackProgramCounts.set(programName, (fallbackProgramCounts.get(programName) || 0) + attendedCount)
      const departmentName = departmentByProgram.get(programName)
      if (departmentName) {
        fallbackDepartmentCounts.set(departmentName, (fallbackDepartmentCounts.get(departmentName) || 0) + attendedCount)
      }
    })
  })

  if (fallbackDepartmentCounts.size > 1) {
    return buildRankedBreakdown(
      Array.from(fallbackDepartmentCounts.entries()).map(([label, value]) => ({ label, value })),
      {
        title: 'College Reach',
        summary: focusEntry
          ? 'Estimated from the selected event attendance breakdown exposed by the backend.'
          : 'Estimated from the latest program attendance breakdown exposed by the backend.',
      }
    )
  }

  if (fallbackProgramCounts.size > 1) {
    return buildRankedBreakdown(
      Array.from(fallbackProgramCounts.entries()).map(([label, value]) => ({ label, value })),
      {
        title: 'Program Participation',
        summary: focusEntry
          ? 'Derived from the selected event program attendance breakdown.'
          : 'Derived from the backend program attendance breakdown.',
      }
    )
  }

  return {
    title: 'College Reach',
    summary: focusEntry
      ? 'College participation will appear once attendance rows expose enough student scope detail.'
      : 'Demographic participation will appear once attendance rows expose enough student scope detail.',
    items: [],
  }
}

function buildEngagementTimeline(entries = []) {
  if (!entries.length) {
    return {
      summary: 'Trend lines will appear after the governance workspace has multiple reported events.',
      points: [],
    }
  }

  const monthlyBuckets = new Map()

  entries.forEach((entry) => {
    const rawDate = entry?.event?.start_datetime || entry?.report?.event_date || null
    const parsed = rawDate ? new Date(rawDate) : null
    if (!parsed || Number.isNaN(parsed.getTime())) return

    const monthKey = `${parsed.getFullYear()}-${String(parsed.getMonth() + 1).padStart(2, '0')}`
    if (!monthlyBuckets.has(monthKey)) {
      monthlyBuckets.set(monthKey, {
        key: monthKey,
        label: new Intl.DateTimeFormat('en-US', { month: 'short' }).format(parsed),
        totalParticipants: 0,
        attendees: 0,
        events: 0,
      })
    }

    const bucket = monthlyBuckets.get(monthKey)
    bucket.totalParticipants += toNonNegativeInt(entry?.report?.total_participants)
    bucket.attendees += toNonNegativeInt(entry?.report?.attendees)
    bucket.events += 1
  })

  const sourceBuckets = monthlyBuckets.size >= 2
    ? Array.from(monthlyBuckets.values()).sort((left, right) => left.key.localeCompare(right.key)).slice(-6)
    : [...entries]
      .sort((left, right) => getEventTimestamp(left.event, 'start') - getEventTimestamp(right.event, 'start'))
      .slice(-6)
      .map((entry, index) => ({
        key: `${entry?.event?.id || index}`,
        label: formatDateOnly(entry?.event?.start_datetime || entry?.report?.event_date) || `Event ${index + 1}`,
        totalParticipants: toNonNegativeInt(entry?.report?.total_participants),
        attendees: toNonNegativeInt(entry?.report?.attendees),
        events: 1,
      }))

  const points = sourceBuckets.map((bucket, index) => {
    const percentage = bucket.totalParticipants > 0
      ? clampPercent((bucket.attendees / bucket.totalParticipants) * 100)
      : 0

    return {
      key: bucket.key || `point-${index}`,
      label: bucket.label,
      value: percentage,
      valueLabel: formatPercentage(percentage),
    }
  })

  const peakPoint = [...points].sort((left, right) => right.value - left.value)[0] || null

  return {
    summary: peakPoint
      ? `${peakPoint.label} delivered the strongest engagement at ${peakPoint.valueLabel}.`
      : 'Trend lines will appear after the governance workspace has multiple reported events.',
    points,
  }
}

function formatHourBucketLabel(hour) {
  try {
    const date = new Date()
    date.setHours(Number(hour) || 0, 0, 0, 0)
    return new Intl.DateTimeFormat('en-US', { hour: 'numeric' }).format(date)
  } catch {
    return `${hour}:00`
  }
}

function toHourBucketKey(value) {
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return null
  parsed.setMinutes(0, 0, 0)
  return String(parsed.getTime())
}

function buildEventHourBuckets(event = null) {
  const startValue = event?.start_datetime || event?.start_time
  const endValue = event?.end_datetime || event?.end_time || startValue
  if (!startValue || !endValue) return []

  const startDate = new Date(startValue)
  const endDate = new Date(endValue)
  if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) return []

  const startBucket = new Date(startDate)
  startBucket.setMinutes(0, 0, 0)
  const endBucket = new Date(endDate)
  endBucket.setMinutes(0, 0, 0)

  if (endBucket < startBucket) return []

  const buckets = []
  const cursor = new Date(startBucket)

  while (cursor <= endBucket && buckets.length < 24) {
    buckets.push({
      key: String(cursor.getTime()),
      label: formatTimeOnly(cursor),
      timestamp: cursor.getTime(),
      value: 0,
    })
    cursor.setHours(cursor.getHours() + 1)
  }

  return buckets
}

function buildArrivalInsight({ event = null, attendanceRecords = [] } = {}) {
  const records = dedupeAttendanceRecords(attendanceRecords)
  const eventBuckets = buildEventHourBuckets(event)
  const bucketMap = new Map()

  eventBuckets.forEach((bucket) => {
    bucketMap.set(bucket.key, { ...bucket })
  })

  records.forEach((record) => {
    const timeIn = record?.attendance?.time_in
    if (!timeIn) return

    const hourKey = toHourBucketKey(timeIn)
    if (!hourKey) return

    if (bucketMap.has(hourKey)) {
      const existing = bucketMap.get(hourKey)
      existing.value += 1
      return
    }

    const parsed = new Date(timeIn)
    const fallbackKey = `hour-${parsed.getHours()}`
    if (!bucketMap.has(fallbackKey)) {
      bucketMap.set(fallbackKey, {
        key: fallbackKey,
        label: formatHourBucketLabel(parsed.getHours()),
        timestamp: parsed.getTime(),
        value: 0,
      })
    }
    bucketMap.get(fallbackKey).value += 1
  })

  const normalizedBuckets = Array.from(bucketMap.values())
    .sort((left, right) => Number(left.timestamp || 0) - Number(right.timestamp || 0))

  const totalAttendance = normalizedBuckets.reduce((sum, item) => sum + toNonNegativeInt(item.value), 0)
  const normalizedItems = normalizedBuckets.map((item) => {
    const value = toNonNegativeInt(item.value)
    const percentage = totalAttendance > 0 ? (value / totalAttendance) * 100 : 0

    return {
      key: item.key,
      label: item.label,
      value,
      valueLabel: formatWholeNumber(value),
      percentage,
      percentageLabel: formatPercentage(Math.round(percentage)),
      ratio: percentage,
    }
  })

  const peak = [...normalizedItems].sort((left, right) => right.value - left.value)[0] || null

  return {
    startLabel: normalizedItems[0]?.label || '',
    endLabel: normalizedItems[normalizedItems.length - 1]?.label || '',
    summary: peak
      ? `${peak.label} had the heaviest arrivals with ${peak.valueLabel} students (${peak.percentageLabel}).`
      : 'Arrival trends will appear once sign-in timestamps are available.',
    peak,
    items: normalizedItems,
  }
}

function formatDurationLabel(value) {
  const minutes = Number(value)
  if (!Number.isFinite(minutes) || minutes <= 0) return 'Not available'
  if (minutes < 60) return `${Math.round(minutes)}m`

  const hours = Math.floor(minutes / 60)
  const remainingMinutes = Math.round(minutes % 60)
  return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`
}

function resolveMethodLabel(method) {
  const normalized = String(method || '').trim().toLowerCase()
  if (normalized === 'face_scan') return 'Face Scan'
  if (normalized === 'manual') return 'Manual'
  return normalized ? normalized.replace(/_/g, ' ') : 'Unknown'
}

function resolveStatusLabel(attendance = {}) {
  const status = String(attendance?.display_status || attendance?.status || '').trim().toLowerCase()
  if (status === 'late') return 'Late'
  if (status === 'absent') return 'Absent'
  if (attendance?.completion_state === 'incomplete') return 'Waiting for Sign Out'
  return 'Present'
}

function buildMasterlistRows(records = [], students = []) {
  const lookup = buildAttendanceStudentLookup(students)

  return dedupeAttendanceRecords(records)
    .map((record) => {
      const attendance = record?.attendance || {}
      const student = resolveMatchedStudent(record, lookup)
      const profile = student?.student_profile || {}

      return {
        key: buildAttendanceRecordKey(record),
        studentId: String(record?.student_id || profile?.student_id || 'N/A'),
        studentName: String(record?.student_name || formatStudentName(student) || 'Unknown Student'),
        departmentName: String(profile?.department_name || 'N/A'),
        programName: String(profile?.program_name || 'N/A'),
        yearLabel: Number.isFinite(Number(profile?.year_level)) ? `Year ${profile.year_level}` : 'N/A',
        statusLabel: resolveStatusLabel(attendance),
        timeInLabel: formatDateTime(attendance?.time_in) || 'Not recorded',
        timeOutLabel: formatDateTime(attendance?.time_out) || (attendance?.completion_state === 'incomplete' ? 'Waiting for sign out' : 'Not recorded'),
        durationLabel: formatDurationLabel(attendance?.duration_minutes),
        methodLabel: resolveMethodLabel(attendance?.method),
      }
    })
    .sort((left, right) => left.studentName.localeCompare(right.studentName))
}

export function useGovernanceWorkspace(options = {}) {
  const route = useRoute()
  const router = useRouter()

  const preview = Boolean(options.preview)
  const sectionSource = options.section ?? 'overview'

  const { apiBaseUrl, token, dashboardState } = useDashboardSession()
  const { previewBundle } = useSgPreviewBundle(() => preview)
  const {
    isLoading,
    error,
    permissionCodes,
    officerPosition,
    officerName,
    acronym,
    unitName,
    currentUser,
    schoolSettings,
  } = useSgDashboard(preview)

  const activeUnit = ref(null)
  const students = ref([])
  const events = ref([])
  const announcements = ref([])
  const membersCount = ref(0)
  const attendanceReportsByEventId = ref({})
  const attendanceRecordsByEventId = ref({})
  const supplementalLoading = ref(false)
  const supplementalError = ref('')
  const hasLoadedWorkspace = ref(false)
  const reportsLoading = ref(false)
  const attendanceReportsHydrated = ref(false)
  const attendanceReportsSupported = ref(false)
  const totalImportedStudents = ref(null)
  const isCreateSheetOpen = ref(false)
  const isExportingPar = ref(false)
  const isExportingMasterlist = ref(false)
  const exportError = ref('')

  const sectionDefinitions = computed(() => getGovernanceSectionDefinitions())
  const currentSection = computed(() => getGovernanceSectionDefinition(resolveSourceValue(sectionSource, 'overview')))
  const isOverviewSection = computed(() => currentSection.value.key === 'overview')
  const hasRenderableData = computed(() => (
    Boolean(activeUnit.value)
    || events.value.length > 0
    || students.value.length > 0
    || announcements.value.length > 0
  ))

  const activeUnitType = computed(() => normalizeGovernanceContext(activeUnit.value?.unit_type))
  const activeUnitName = computed(() => (
    String(activeUnit.value?.unit_name || unitName.value || 'Governance workspace').trim()
  ))

  const workspaceEyebrow = computed(() => {
    const labelMap = {
      SSG: 'Supreme Student Government',
      SG: 'Student Government',
      ORG: 'Organization workspace',
    }

    return labelMap[activeUnitType.value] || 'Governance workspace'
  })

  const officerMeta = computed(() => {
    const position = String(officerPosition.value || '').trim()
    const name = String(officerName.value || '').trim()
    if (position && name) return `${position} · ${name}`
    if (name) return name
    if (position) return position
    return 'Active governance member'
  })

  const headerTitle = computed(() => (
    isOverviewSection.value ? activeUnitName.value : currentSection.value.title
  ))

  const headerDescription = computed(() => (
    isOverviewSection.value
      ? 'Track engagement, upcoming work, pending follow-ups, and announcements for your current governance scope.'
      : currentSection.value.description
  ))

  const permissionSet = computed(() => new Set(permissionCodes.value))
  const permissionBadgeList = computed(() => (
    permissionCodes.value.slice(0, 8).map(formatPermissionLabel)
  ))

  const sortedEvents = computed(() => sortGovernanceEvents(events.value))
  const sortedAnnouncements = computed(() => sortAnnouncements(announcements.value))
  const upcomingEvents = computed(() => {
    const preferred = sortedEvents.value.filter((event) => isEventLive(event) || isEventUpcoming(event))
    if (preferred.length) return preferred.slice(0, MAX_UPCOMING_EVENTS)
    return sortedEvents.value.slice(0, MAX_UPCOMING_EVENTS)
  })
  const recentAnnouncements = computed(() => sortedAnnouncements.value.slice(0, MAX_ANNOUNCEMENTS))
  const studentsPreview = computed(() => students.value.slice(0, 6))
  const thisWeekEventsCount = computed(() => (
    sortedEvents.value.filter((event) => isWithinNextWeek(event)).length
  ))
  const liveEventsCount = computed(() => (
    sortedEvents.value.filter((event) => isEventLive(event)).length
  ))

  const reportEntries = computed(() => (
    sortedEvents.value
      .map((event) => ({
        event,
        report: attendanceReportsByEventId.value[Number(event?.id)] || null,
      }))
      .filter((entry) => entry.report)
  ))

  const previewAttendanceSummary = computed(() => summarizePreviewAttendance(previewBundle.value))
  const selectedAnalyticsEventId = ref(null)
  const analyticsEventOptions = computed(() => (
    reportEntries.value.map((entry) => ({
      value: Number(entry?.event?.id),
      label: String(entry?.event?.name || entry?.report?.event_name || 'Untitled event'),
      meta: formatDateOnly(entry?.event?.start_datetime || entry?.report?.event_date),
    }))
  ))
  const analyticsFocusEntry = computed(() => {
    const normalizedSelectedId = Number(selectedAnalyticsEventId.value)
    if (Number.isFinite(normalizedSelectedId)) {
      const matchedEntry = reportEntries.value.find((entry) => Number(entry?.event?.id) === normalizedSelectedId)
      if (matchedEntry) return matchedEntry
    }

    const liveEntry = reportEntries.value.find((entry) => isEventLive(entry?.event))
    return liveEntry || reportEntries.value[0] || null
  })
  const eventHealthInsight = computed(() => buildEventHealthInsight(analyticsFocusEntry.value))
  const analyticsFocusRecords = computed(() => {
    const focusEventId = Number(analyticsFocusEntry.value?.event?.id)
    if (!Number.isFinite(focusEventId)) return []
    return attendanceRecordsByEventId.value[focusEventId] || []
  })
  const demographicInsight = computed(() => buildDemographicInsight({
    focusEntry: analyticsFocusEntry.value,
    attendanceRecords: analyticsFocusRecords.value,
    students: students.value,
  }))
  const engagementTimeline = computed(() => buildEngagementTimeline(reportEntries.value))
  const arrivalInsight = computed(() => buildArrivalInsight({
    event: analyticsFocusEntry.value?.event,
    attendanceRecords: analyticsFocusRecords.value,
  }))
  const focusMasterlistRows = computed(() => buildMasterlistRows(analyticsFocusRecords.value, students.value))
  const canExportPar = computed(() => Boolean(analyticsFocusEntry.value?.report))
  const canExportMasterlist = computed(() => focusMasterlistRows.value.length > 0)

  watch(
    analyticsEventOptions,
    (options) => {
      const normalizedSelectedId = Number(selectedAnalyticsEventId.value)
      const stillExists = options.some((option) => Number(option.value) === normalizedSelectedId)
      if (stillExists) return
      selectedAnalyticsEventId.value = options[0]?.value ?? null
    },
    { immediate: true }
  )

  const engagementMetric = computed(() => {
    if (reportEntries.value.length) {
      const aggregate = reportEntries.value.reduce((accumulator, entry) => ({
        totalParticipants: accumulator.totalParticipants + toNonNegativeInt(entry.report?.total_participants),
        attendees: accumulator.attendees + toNonNegativeInt(entry.report?.attendees),
      }), {
        totalParticipants: 0,
        attendees: 0,
      })

      const percentage = aggregate.totalParticipants > 0
        ? clampPercent((aggregate.attendees / aggregate.totalParticipants) * 100)
        : 0

      return {
        percentage,
        valueLabel: formatPercentage(percentage),
        centerLabel: `${reportEntries.value.length} report${reportEntries.value.length === 1 ? '' : 's'}`,
        hint: aggregate.totalParticipants > 0
          ? `${formatWholeNumber(aggregate.attendees)} attendees across ${formatWholeNumber(aggregate.totalParticipants)} expected participants.`
          : 'Report-backed analytics are still warming up.',
      }
    }

    if (previewAttendanceSummary.value) {
      return {
        percentage: previewAttendanceSummary.value.attendanceRate,
        valueLabel: formatPercentage(previewAttendanceSummary.value.attendanceRate),
        centerLabel: 'preview',
        hint: `${formatWholeNumber(previewAttendanceSummary.value.attendees)} attendees from the preview attendance summary.`,
      }
    }

    return {
      percentage: 0,
      valueLabel: '--',
      centerLabel: 'awaiting reports',
      hint: 'Engagement analytics will appear once attendance reports are available.',
    }
  })

  const activeStudentsMetric = computed(() => ({
    valueLabel: formatCompactNumber(students.value.length),
    hint: membersCount.value > 0
      ? `${formatWholeNumber(membersCount.value)} governance member${membersCount.value === 1 ? '' : 's'} managing this scope.`
      : 'Live roster inside the active governance scope.',
  }))

  const totalStudentsMetric = computed(() => {
    const totalVisible = students.value.length
    const totalImported = toNonNegativeInt(totalImportedStudents.value)
    const resolvedTotal = totalImported > 0 ? totalImported : totalVisible

    return {
      valueLabel: formatCompactNumber(resolvedTotal),
      hint: totalImported > 0
        ? 'Total enrolled students imported into the active SSG workspace.'
        : 'Total students currently exposed by the backend for this governance scope.',
    }
  })

  const eventVolumeMetric = computed(() => {
    if (thisWeekEventsCount.value > 0) {
      return {
        valueLabel: formatCompactNumber(thisWeekEventsCount.value),
        hint: liveEventsCount.value > 0
          ? `${formatWholeNumber(liveEventsCount.value)} happening right now.`
          : 'Events scheduled across the next seven days.',
      }
    }

    return {
      valueLabel: formatCompactNumber(liveEventsCount.value),
      hint: liveEventsCount.value > 0
        ? 'Live governance events right now.'
        : 'No events scheduled for the next seven days.',
    }
  })

  const latestAnnouncement = computed(() => (
    sortedAnnouncements.value.find((announcement) => String(announcement?.status || '').toLowerCase() === 'published')
    || sortedAnnouncements.value[0]
    || null
  ))

  const latestAnnouncementReachMetric = computed(() => {
    const reachData = getAnnouncementReachData(latestAnnouncement.value)

    if (reachData.hasAnalytics) {
      const seenLabel = reachData.seenCount != null ? formatWholeNumber(reachData.seenCount) : '--'
      const audienceLabel = reachData.audienceCount != null ? formatWholeNumber(reachData.audienceCount) : '--'

      return {
        valueLabel: formatPercentage(reachData.percentage),
        hint: `Latest announcement reached ${seenLabel} of ${audienceLabel} students.`,
      }
    }

    if (latestAnnouncement.value) {
      return {
        valueLabel: '--',
        hint: 'Reach analytics are not available on the latest announcement yet.',
      }
    }

    return {
      valueLabel: '--',
      hint: 'Publish an announcement to start tracking reach.',
    }
  })

  const attentionItems = computed(() => {
    const items = []

    const draftAnnouncements = sortedAnnouncements.value
      .filter((announcement) => String(announcement?.status || '').toLowerCase() === 'draft')

    if (draftAnnouncements.length > 0) {
      items.push({
        key: 'draft-announcements',
        tone: 'warning',
        eyebrow: 'Announcements',
        title: `${formatWholeNumber(draftAnnouncements.length)} draft announcement${draftAnnouncements.length === 1 ? '' : 's'} waiting to be published.`,
        description: draftAnnouncements[0]?.title
          ? `Latest draft: ${draftAnnouncements[0].title}`
          : 'Open the Events workspace to publish or revise the pending announcement.',
        actionLabel: 'Open Events',
        action: { type: 'section', sectionKey: 'events' },
      })
    }

    reportEntries.value
      .filter((entry) => toNonNegativeInt(entry.report?.incomplete_attendees) > 0)
      .slice(0, 2)
      .forEach((entry) => {
        items.push({
          key: `incomplete-${entry.event.id}`,
          tone: 'critical',
          eyebrow: 'Attendance',
          title: `Attendance is not finalized for ${entry.event.name || 'this event'}.`,
          description: `${formatWholeNumber(entry.report?.incomplete_attendees)} attendee${toNonNegativeInt(entry.report?.incomplete_attendees) === 1 ? '' : 's'} are still waiting for completion.`,
          actionLabel: 'Manage Event',
          action: { type: 'event', eventId: entry.event.id },
        })
      })

    if (attendanceReportsHydrated.value && attendanceReportsSupported.value) {
      sortedEvents.value
        .filter((event) => isEventCompleted(event))
        .filter((event) => !attendanceReportsByEventId.value[Number(event?.id)])
        .slice(0, 2)
        .forEach((event) => {
          items.push({
            key: `report-${event.id}`,
            tone: 'default',
            eyebrow: 'Reporting',
            title: `Post-event report pending for ${event.name || 'this event'}.`,
            description: 'Open the event and finalize attendance reporting so analytics can stay accurate.',
            actionLabel: 'View Details',
            action: { type: 'event', eventId: event.id },
          })
        })
    }

    const missingLocationEvent = sortedEvents.value.find((event) => {
      if (!isEventUpcoming(event) || !isWithinNextWeek(event)) return false
      const location = String(event?.location || '').trim().toLowerCase()
      return !location || location === 'tba' || location === 'location pending'
    })

    if (missingLocationEvent) {
      items.push({
        key: `location-${missingLocationEvent.id}`,
        tone: 'default',
        eyebrow: 'Events',
        title: `${missingLocationEvent.name || 'Upcoming event'} still needs a confirmed venue.`,
        description: 'Students need a final location before the event goes live.',
        actionLabel: 'Open Events',
        action: { type: 'section', sectionKey: 'events' },
      })
    }

    return items.slice(0, MAX_ATTENTION_ITEMS)
  })

  const isWorkspaceLoading = computed(() => (
    Boolean(isLoading.value)
    || (supplementalLoading.value && !hasLoadedWorkspace.value)
  ))

  const workspaceError = computed(() => supplementalError.value || error.value || '')

  watch(
    [apiBaseUrl, token, () => dashboardState.initialized, () => route.query?.variant],
    async ([url, authToken, isInitialized]) => {
      supplementalError.value = ''

      if (preview) {
        hydratePreviewWorkspace()
        return
      }

      if (!isInitialized || !url || !authToken) {
        resetWorkspaceState()
        return
      }

      await loadGovernanceWorkspace(url, authToken)
    },
    { immediate: true }
  )

  function resetWorkspaceState() {
    activeUnit.value = null
    students.value = []
    events.value = []
    announcements.value = []
    membersCount.value = 0
    totalImportedStudents.value = null
    attendanceReportsByEventId.value = {}
    attendanceRecordsByEventId.value = {}
    supplementalLoading.value = false
    reportsLoading.value = false
    attendanceReportsHydrated.value = false
    attendanceReportsSupported.value = false
    hasLoadedWorkspace.value = false
    exportError.value = ''
  }

  function hydratePreviewWorkspace() {
    const bundle = previewBundle.value

    activeUnit.value = bundle?.activeUnit || null
    students.value = cloneArray(bundle?.students)
    events.value = cloneArray(bundle?.events)
    announcements.value = cloneArray(bundle?.announcements)
    membersCount.value = Array.isArray(bundle?.activeUnit?.members) ? bundle.activeUnit.members.length : 0
    totalImportedStudents.value = toNonNegativeInt(bundle?.totalImportedStudents)
    attendanceReportsByEventId.value = buildPreviewReportsMap(bundle?.eventReports)
    attendanceRecordsByEventId.value = buildPreviewAttendanceMap(bundle?.eventAttendanceRecords)
    attendanceReportsHydrated.value = true
    attendanceReportsSupported.value = Object.keys(attendanceReportsByEventId.value).length > 0
    supplementalLoading.value = false
    reportsLoading.value = false
    supplementalError.value = ''
    hasLoadedWorkspace.value = true
  }

  async function resolveActiveUnitChildUnits(url, authToken, governanceUnitId) {
    if (!Number.isFinite(governanceUnitId)) return []

    let overviewChildUnits = []
    let hasOverviewChildUnits = false

    try {
      const overview = await getGovernanceDashboardOverview(url, authToken, governanceUnitId)
      if (Array.isArray(overview?.child_units)) {
        overviewChildUnits = cloneArray(overview.child_units)
        hasOverviewChildUnits = true
        if (overviewChildUnits.length > 0) {
          return overviewChildUnits
        }
      }
    } catch {
      // Fall through to list query fallback.
    }

    try {
      const fallbackChildUnits = await getGovernanceUnits(url, authToken, {
        parent_unit_id: governanceUnitId,
        include_inactive: false,
      })
      const normalizedFallbackChildUnits = cloneArray(
        (Array.isArray(fallbackChildUnits) ? fallbackChildUnits : [])
          .filter((unit) => unit?.is_active !== false)
      )
      if (normalizedFallbackChildUnits.length > 0) {
        return normalizedFallbackChildUnits
      }
    } catch {
      // Keep existing empty state when fallback cannot be resolved.
    }

    return hasOverviewChildUnits ? overviewChildUnits : []
  }

  async function loadGovernanceWorkspace(url, authToken) {
    supplementalLoading.value = true
    attendanceReportsByEventId.value = {}
    attendanceRecordsByEventId.value = {}
    attendanceReportsHydrated.value = false
    attendanceReportsSupported.value = false
    reportsLoading.value = false

    try {
      const access = await getGovernanceAccess(url, authToken)
      const resolvedUnit = resolvePreferredGovernanceUnit(access)
      const normalizedUnitId = Number(resolvedUnit?.governance_unit_id ?? resolvedUnit?.id)
      const normalizedContext = normalizeGovernanceContext(resolvedUnit?.unit_type)

      if (!resolvedUnit || !normalizedContext) {
        throw new Error('No active SG, SSG, or ORG unit is available for this account.')
      }

      activeUnit.value = resolvedUnit

      const [detailResult, childUnitsResult, studentsResult, eventsResult, announcementsResult, ssgSetupResult] = await Promise.allSettled([
        Number.isFinite(normalizedUnitId)
          ? getGovernanceUnitDetail(url, authToken, normalizedUnitId)
          : Promise.resolve(null),
        Number.isFinite(normalizedUnitId)
          ? resolveActiveUnitChildUnits(url, authToken, normalizedUnitId)
          : Promise.resolve([]),
        getGovernanceStudents(
          url,
          authToken,
          normalizedContext ? { governance_context: normalizedContext } : {},
        ),
        getEvents(url, authToken, { governance_context: normalizedContext }),
        Number.isFinite(normalizedUnitId)
          ? getGovernanceAnnouncements(url, authToken, normalizedUnitId)
          : Promise.resolve([]),
        normalizedContext === 'SSG'
          ? getCampusSsgSetup(url, authToken)
          : Promise.resolve(null),
      ])

      const resolvedChildUnits = (
        childUnitsResult.status === 'fulfilled' && Array.isArray(childUnitsResult.value)
      )
        ? cloneArray(childUnitsResult.value)
        : []

      if (detailResult.status === 'fulfilled' && detailResult.value) {
        const detailUnit = detailResult.value
        const detailChildUnits = Array.isArray(detailUnit?.child_units)
          ? cloneArray(detailUnit.child_units)
          : []

        activeUnit.value = {
          ...detailUnit,
          child_units: detailChildUnits.length > 0 ? detailChildUnits : resolvedChildUnits,
        }
        membersCount.value = Array.isArray(detailUnit?.members) ? detailUnit.members.length : 0
      } else {
        activeUnit.value = {
          ...(activeUnit.value || {}),
          child_units: resolvedChildUnits,
        }
        membersCount.value = 0
      }

      students.value = studentsResult.status === 'fulfilled' && Array.isArray(studentsResult.value)
        ? studentsResult.value.map(cloneRecord)
        : []

      events.value = eventsResult.status === 'fulfilled' && Array.isArray(eventsResult.value)
        ? eventsResult.value.map(cloneRecord)
        : []

      announcements.value = announcementsResult.status === 'fulfilled' && Array.isArray(announcementsResult.value)
        ? announcementsResult.value.map(cloneRecord)
        : []

      totalImportedStudents.value = (
        ssgSetupResult.status === 'fulfilled' && ssgSetupResult.value
          ? toNonNegativeInt(ssgSetupResult.value.total_imported_students)
          : null
      )

      hasLoadedWorkspace.value = true

      void loadEventReports(url, authToken, events.value)
    } catch (loadError) {
      resetWorkspaceState()
      supplementalError.value = loadError?.message || 'Unable to load the governance workspace.'
    } finally {
      supplementalLoading.value = false
    }
  }

  async function loadEventReports(url, authToken, scopedEvents = []) {
    const candidateEvents = sortGovernanceEvents(scopedEvents)
      .filter((event) => isEventLive(event) || isEventCompleted(event))
      .slice(0, MAX_REPORT_EVENTS)

    if (!candidateEvents.length) {
      attendanceReportsByEventId.value = {}
      attendanceRecordsByEventId.value = {}
      attendanceReportsHydrated.value = true
      attendanceReportsSupported.value = false
      reportsLoading.value = false
      return
    }

    reportsLoading.value = true

    try {
      const reportResults = await Promise.allSettled(
        candidateEvents.map(async (event) => {
          const [reportResult, recordsResult] = await Promise.allSettled([
            getEventAttendanceReport(url, authToken, event.id),
            getEventAttendance(url, authToken, event.id, { active_only: false }),
          ])

          return {
            eventId: Number(event?.id),
            report: reportResult.status === 'fulfilled' ? reportResult.value : null,
            records: recordsResult.status === 'fulfilled' ? recordsResult.value : [],
          }
        })
      )

      const nextReports = {}
      const nextRecords = {}
      let didResolveAnyReport = false

      reportResults.forEach((result, index) => {
        const fallbackEventId = Number(candidateEvents[index]?.id)
        const eventId = result.status === 'fulfilled'
          ? Number(result.value?.eventId)
          : fallbackEventId
        if (!Number.isFinite(eventId)) return

        if (result.status === 'fulfilled') {
          nextReports[eventId] = result.value?.report
            ? { ...result.value.report, event_id: eventId }
            : null
          nextRecords[eventId] = cloneArray(result.value?.records)
          if (result.value?.report) {
            didResolveAnyReport = true
          }
        } else {
          nextReports[eventId] = null
          nextRecords[eventId] = []
        }
      })

      attendanceReportsByEventId.value = nextReports
      attendanceRecordsByEventId.value = nextRecords
      attendanceReportsSupported.value = didResolveAnyReport
      attendanceReportsHydrated.value = true
    } finally {
      reportsLoading.value = false
    }
  }

  async function exportPostActivityReport() {
    if (!canExportPar.value || isExportingPar.value) return
    isExportingPar.value = true
    exportError.value = ''

    try {
      await downloadGovernanceParPdf({
        event: analyticsFocusEntry.value?.event,
        report: analyticsFocusEntry.value?.report,
        eventHealth: eventHealthInsight.value,
        demographicBreakdown: demographicInsight.value,
        arrivalInsights: arrivalInsight.value,
      })
    } catch (error) {
      exportError.value = error?.message || 'Unable to export the post-activity report.'
    } finally {
      isExportingPar.value = false
    }
  }

  async function exportMasterlist() {
    if (!canExportMasterlist.value || isExportingMasterlist.value) return
    isExportingMasterlist.value = true
    exportError.value = ''

    try {
      await downloadGovernanceMasterlistCsv({
        event: analyticsFocusEntry.value?.event,
        report: analyticsFocusEntry.value?.report,
        rows: focusMasterlistRows.value,
      })
    } catch (error) {
      exportError.value = error?.message || 'Unable to export the masterlist.'
    } finally {
      isExportingMasterlist.value = false
    }
  }

  function getEventReportSnapshot(eventOrId = null) {
    const normalizedEventId = Number(isObject(eventOrId) ? eventOrId.id : eventOrId)
    const event = Number.isFinite(normalizedEventId)
      ? sortedEvents.value.find((entry) => Number(entry?.id) === normalizedEventId) || null
      : null

    const report = Number.isFinite(normalizedEventId)
      ? attendanceReportsByEventId.value[normalizedEventId] || null
      : null

    const records = Number.isFinite(normalizedEventId)
      ? dedupeAttendanceRecords(attendanceRecordsByEventId.value[normalizedEventId] || [])
      : []

    const checkedInCount = records.filter((record) => hasSignedInAttendanceRecord(record?.attendance)).length
    const checkedOutCount = records.filter((record) => record?.attendance?.time_out).length
    const eventEntry = {
      event,
      report,
      records,
    }

    return {
      event,
      report,
      records,
      checkedInCount,
      checkedOutCount,
      checkedInLabel: formatWholeNumber(checkedInCount),
      checkedOutLabel: formatWholeNumber(checkedOutCount),
      canExportPar: Boolean(report),
      canExportMasterlist: records.length > 0,
      eventHealth: buildEventHealthInsight(report ? eventEntry : null),
      demographicBreakdown: buildDemographicInsight({
        focusEntry: report ? eventEntry : null,
        attendanceRecords: records,
        students: students.value,
      }),
      arrivalInsights: buildArrivalInsight({
        event,
        attendanceRecords: records,
      }),
      masterlistRows: buildMasterlistRows(records, students.value),
    }
  }

  async function exportEventPostActivityReport(eventOrId = null) {
    const snapshot = getEventReportSnapshot(eventOrId)
    if (!snapshot.canExportPar || isExportingPar.value) return

    isExportingPar.value = true
    exportError.value = ''

    try {
      await downloadGovernanceParPdf({
        event: snapshot.event,
        report: snapshot.report,
        eventHealth: snapshot.eventHealth,
        demographicBreakdown: snapshot.demographicBreakdown,
        arrivalInsights: snapshot.arrivalInsights,
      })
    } catch (error) {
      exportError.value = error?.message || 'Unable to export the post-activity report.'
    } finally {
      isExportingPar.value = false
    }
  }

  async function exportEventMasterlist(eventOrId = null) {
    const snapshot = getEventReportSnapshot(eventOrId)
    if (!snapshot.canExportMasterlist || isExportingMasterlist.value) return

    isExportingMasterlist.value = true
    exportError.value = ''

    try {
      await downloadGovernanceMasterlistCsv({
        event: snapshot.event,
        report: snapshot.report,
        rows: snapshot.masterlistRows,
      })
    } catch (error) {
      exportError.value = error?.message || 'Unable to export the masterlist.'
    } finally {
      isExportingMasterlist.value = false
    }
  }

  function hasPermission(permissionCode = '') {
    if (!permissionCode) return true
    return permissionSet.value.has(permissionCode)
  }

  function resolveSectionTarget(sectionKey = 'overview') {
    const section = getGovernanceSectionDefinition(sectionKey)
    return preview
      ? withPreservedGovernancePreviewQuery(route, section.previewRoute)
      : section.route
  }

  function openSection(sectionKey = 'overview') {
    const target = resolveSectionTarget(sectionKey)
    openRoute(target)
  }

  function openRoute(target = null) {
    if (!target) return

    const nextTarget = preview
      ? withPreservedGovernancePreviewQuery(route, target)
      : target

    const resolvedTarget = router.resolve(nextTarget)
    if (route.fullPath === resolvedTarget.fullPath) return
    router.push(nextTarget)
  }

  function openEvent(eventOrId) {
    const eventId = Number(isObject(eventOrId) ? eventOrId.id : eventOrId)
    if (!Number.isFinite(eventId)) return
    openRoute(resolveEventDetailLocation(route, eventId))
  }

  function openAttentionItem(item = null) {
    if (!item?.action) return

    if (item.action.type === 'event') {
      openEvent(item.action.eventId)
      return
    }

    if (item.action.type === 'section') {
      openSection(item.action.sectionKey)
      return
    }

    if (item.action.type === 'route') {
      openRoute(item.action.route)
    }
  }

  function openCreateSheet() {
    isCreateSheetOpen.value = true
  }

  function closeCreateSheet() {
    isCreateSheetOpen.value = false
  }

  function handleCreateAction(action = null) {
    if (!action || action.disabled) return
    closeCreateSheet()

    if (action.route) {
      openRoute(action.route)
      return
    }

    openSection(action.sectionKey)
  }

  function setSelectedAnalyticsEventId(value = null) {
    const normalizedValue = Number(value)
    if (!Number.isFinite(normalizedValue)) return
    selectedAnalyticsEventId.value = normalizedValue
  }

  function getUpcomingEventActionLabel(event = null) {
    return isEventLive(event) ? 'Manage Attendance' : 'View Details'
  }

  function getUpcomingEventTone(event = null) {
    if (isEventLive(event)) return 'live'
    if (isEventUpcoming(event)) return 'upcoming'
    return 'default'
  }

  return {
    currentUser,
    schoolSettings,
    permissionCodes,
    acronym,
    activeUnit,
    activeUnitType,
    activeUnitName,
    workspaceEyebrow,
    officerMeta,
    headerTitle,
    headerDescription,
    membersCount,
    students,
    studentsPreview,
    events,
    upcomingEvents,
    announcements,
    recentAnnouncements,
    permissionBadgeList,
    sectionDefinitions,
    currentSection,
    isOverviewSection,
    hasRenderableData,
    isWorkspaceLoading,
    workspaceError,
    reportsLoading,
    exportError,
    isExportingPar,
    isExportingMasterlist,
    engagementMetric,
    eventHealthInsight,
    demographicInsight,
    engagementTimeline,
    arrivalInsight,
    analyticsEventOptions,
    attendanceRecordsByEventId,
    selectedAnalyticsEventId,
    activeStudentsMetric,
    totalStudentsMetric,
    eventVolumeMetric,
    latestAnnouncementReachMetric,
    attentionItems,
    analyticsFocusEntry,
    focusMasterlistRows,
    canExportPar,
    canExportMasterlist,
    getEventReportSnapshot,
    isCreateSheetOpen,
    hasPermission,
    openSection,
    openRoute,
    openEvent,
    openAttentionItem,
    openCreateSheet,
    closeCreateSheet,
    handleCreateAction,
    setSelectedAnalyticsEventId,
    exportPostActivityReport,
    exportMasterlist,
    exportEventPostActivityReport,
    exportEventMasterlist,
    getUpcomingEventActionLabel,
    getUpcomingEventTone,
    formatStudentName,
    formatStudentMeta,
    formatEventLine,
    formatDateRange,
    formatAnnouncementTime,
    formatWholeNumber,
    formatCompactNumber,
    formatPercentage,
    formatPermissionLabel,
    getStatusLabel,
  }
}
