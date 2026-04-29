import {
  getAttendanceRecordTimestamp,
  getLatestAttendanceRecordsByEvent,
  isValidCompletedAttendanceRecord,
  resolveAttendanceDisplayStatus,
} from '@/services/attendanceFlow.js'
import { downloadBlobFile } from '@/services/fileDownload.js'

const STATUS_ORDER = ['present', 'late', 'absent', 'excused']

const STATUS_LABELS = {
  present: 'Present',
  late: 'Late',
  absent: 'Absent',
  excused: 'Excused',
}

function formatWholeNumber(value) {
  return new Intl.NumberFormat('en-US').format(Number(value || 0))
}

function formatDateTime(value) {
  if (!value) return 'Not recorded'

  try {
    return new Intl.DateTimeFormat('en-PH', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    }).format(new Date(value))
  } catch {
    return 'Not recorded'
  }
}

function formatDateRange(startValue, endValue) {
  if (!startValue) return 'Schedule pending'

  try {
    const start = new Date(startValue)
    const end = endValue ? new Date(endValue) : null
    const startLabel = new Intl.DateTimeFormat('en-PH', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    }).format(start)

    if (!end || Number.isNaN(end.getTime())) return startLabel

    const sameDay = start.toDateString() === end.toDateString()
    if (!sameDay) {
      const endLabel = new Intl.DateTimeFormat('en-PH', {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
      }).format(end)
      return `${startLabel} - ${endLabel}`
    }

    const endLabel = new Intl.DateTimeFormat('en-PH', {
      hour: 'numeric',
      minute: '2-digit',
    }).format(end)
    return `${startLabel} - ${endLabel}`
  } catch {
    return 'Schedule pending'
  }
}

function sanitizeFilename(value = 'report') {
  return String(value || 'report')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '') || 'report'
}

function toCsvField(value) {
  const stringValue = String(value ?? '')
  if (!/[",\r\n]/.test(stringValue)) return stringValue
  return `"${stringValue.replace(/"/g, '""')}"`
}

export function resolveStudentSummaryStatus(record = null) {
  const displayStatus = resolveAttendanceDisplayStatus(record)

  if (displayStatus === 'absent') return 'absent'
  if (displayStatus === 'late' && isValidCompletedAttendanceRecord(record)) return 'late'
  if (displayStatus === 'present' && isValidCompletedAttendanceRecord(record)) return 'present'
  if (displayStatus === 'excused') return 'excused'
  return ''
}

export function buildStudentStatusSummary({ attendanceRecords = [], events = [] } = {}) {
  const latestRecords = getLatestAttendanceRecordsByEvent(attendanceRecords)
  const eventLookup = Object.fromEntries(
    (Array.isArray(events) ? events : []).map((event) => [Number(event?.id), event]),
  )

  const rows = latestRecords
    .map((record) => {
      const statusKey = resolveStudentSummaryStatus(record)
      if (!statusKey) return null

      const eventId = Number(record?.event_id)
      const event = eventLookup[eventId] || null
      const timestamp = getAttendanceRecordTimestamp(record)

      return {
        key: `${eventId}-${timestamp}`,
        eventId,
        eventName: event?.name || `Event ${eventId}`,
        location: event?.location || 'Location pending',
        scheduleLabel: formatDateRange(event?.start_datetime || event?.start_time, event?.end_datetime || event?.end_time),
        statusKey,
        statusLabel: STATUS_LABELS[statusKey],
        timeInLabel: formatDateTime(record?.time_in),
        timeOutLabel: formatDateTime(record?.time_out),
        timestamp,
      }
    })
    .filter(Boolean)
    .sort((left, right) => right.timestamp - left.timestamp)

  const counts = STATUS_ORDER.reduce((accumulator, key) => {
    accumulator[key] = 0
    return accumulator
  }, {})

  rows.forEach((row) => {
    counts[row.statusKey] += 1
  })

  const totalMarked = STATUS_ORDER.reduce((total, key) => total + counts[key], 0)
  const attendedCount = counts.present + counts.late
  const attendanceRate = totalMarked > 0
    ? Math.round((attendedCount / totalMarked) * 100)
    : 0

  const items = STATUS_ORDER.map((key) => {
    const value = counts[key]
    const share = totalMarked > 0 ? Math.round((value / totalMarked) * 100) : 0

    return {
      key,
      label: STATUS_LABELS[key],
      value,
      valueLabel: formatWholeNumber(value),
      share,
      shareLabel: `${share}%`,
    }
  })

  return {
    totalMarked,
    totalMarkedLabel: formatWholeNumber(totalMarked),
    attendedCount,
    attendedCountLabel: formatWholeNumber(attendedCount),
    missedCount: counts.absent,
    missedCountLabel: formatWholeNumber(counts.absent),
    excusedCount: counts.excused,
    excusedCountLabel: formatWholeNumber(counts.excused),
    lateCount: counts.late,
    lateCountLabel: formatWholeNumber(counts.late),
    presentCount: counts.present,
    presentCountLabel: formatWholeNumber(counts.present),
    attendanceRate,
    attendanceRateLabel: `${attendanceRate}%`,
    items,
    rows,
  }
}

export async function downloadStudentStatusSummaryCsv({ user = null, summary = null } = {}) {
  const safeSummary = summary || buildStudentStatusSummary()
  const csvLines = [
    ['Student', [user?.first_name, user?.middle_name, user?.last_name].filter(Boolean).join(' ') || user?.email || 'Student'],
    ['Attendance Rate', safeSummary.attendanceRateLabel || '0%'],
    ['Total Marked Events', safeSummary.totalMarkedLabel || '0'],
    ['Present', safeSummary.presentCountLabel || '0'],
    ['Late', safeSummary.lateCountLabel || '0'],
    ['Absent', safeSummary.missedCountLabel || '0'],
    ['Excused', safeSummary.excusedCountLabel || '0'],
    [],
    ['Event', 'Location', 'Schedule', 'Status', 'Time In', 'Time Out'],
    ...(Array.isArray(safeSummary.rows) ? safeSummary.rows : []).map((row) => ([
      row.eventName,
      row.location,
      row.scheduleLabel,
      row.statusLabel,
      row.timeInLabel,
      row.timeOutLabel,
    ])),
  ]

  const csvContent = `\uFEFF${csvLines.map((line) => line.map(toCsvField).join(',')).join('\r\n')}`
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const filenameBase = [user?.first_name, user?.last_name].filter(Boolean).join('-') || user?.email || 'student'
  return downloadBlobFile(blob, `${sanitizeFilename(filenameBase)}-status-summary.csv`, {
    title: 'Student status summary',
  })
}
