import {
  BackendApiError,
  getAttendanceOverview as fetchAttendanceOverview,
  getAttendanceSummary as fetchAttendanceSummary,
  getAuditLogs as fetchAuditLogs,
  getDepartments as fetchDepartments,
  getEventAttendance as fetchEventAttendance,
  getEventAttendanceReport as fetchEventAttendanceReport,
  getEvents as fetchEvents,
  getNotificationLogs as fetchNotificationLogs,
  getStudentAttendanceReport as fetchStudentAttendanceReport,
  getStudentAttendanceStats as fetchStudentAttendanceStats,
  getStudentImportStatus as fetchStudentImportStatus,
  downloadImportErrors as fetchImportErrorsFile,
  downloadPreviewImportErrors as fetchPreviewErrorsFile,
  downloadPreviewRetryFile as fetchPreviewRetryFile,
  resolveApiBaseUrl,
} from '@/services/backendApi.js'

export class ReportServiceError extends Error {
  constructor(message, { status = 0, details = null, cause = null } = {}) {
    super(message)
    this.name = 'ReportServiceError'
    this.status = status
    this.details = details
    this.cause = cause
  }
}

function normalizeContext(options = {}) {
  const baseUrl = resolveApiBaseUrl(options?.baseUrl || '')
  const token = String(options?.token || '').trim()

  if (!token) {
    throw new ReportServiceError('Missing access token.', { status: 401 })
  }

  return { baseUrl, token }
}

function normalizeId(value, label) {
  const normalized = Number(value)
  if (!Number.isFinite(normalized) || normalized <= 0) {
    throw new ReportServiceError(`${label} must be a valid positive number.`)
  }
  return normalized
}

function toReportServiceError(error, fallbackMessage) {
  if (error instanceof ReportServiceError) return error
  if (error instanceof BackendApiError) {
    return new ReportServiceError(error.message || fallbackMessage, {
      status: error.status || 0,
      details: error.details || null,
      cause: error,
    })
  }

  return new ReportServiceError(fallbackMessage, {
    details: {
      cause: error?.message || null,
    },
    cause: error,
  })
}

async function runWithReportErrorHandling(action, fallbackMessage) {
  try {
    return await action()
  } catch (error) {
    throw toReportServiceError(error, fallbackMessage)
  }
}

export async function getEventAttendanceReport(eventId, options = {}) {
  return runWithReportErrorHandling(async () => {
    const { baseUrl, token } = normalizeContext(options)
    const normalizedEventId = normalizeId(eventId, 'eventId')
    return fetchEventAttendanceReport(baseUrl, token, normalizedEventId, options?.params || {})
  }, 'Unable to load event attendance report.')
}

export async function getReportEvents(options = {}) {
  return runWithReportErrorHandling(async () => {
    const { baseUrl, token } = normalizeContext(options)
    return fetchEvents(baseUrl, token, options?.params || {})
  }, 'Unable to load report events.')
}

export async function getReportDepartments(options = {}) {
  return runWithReportErrorHandling(async () => {
    const { baseUrl, token } = normalizeContext(options)
    return fetchDepartments(baseUrl, token)
  }, 'Unable to load report departments.')
}

export async function getEventAttendanceRecords(eventId, options = {}) {
  return runWithReportErrorHandling(async () => {
    const { baseUrl, token } = normalizeContext(options)
    const normalizedEventId = normalizeId(eventId, 'eventId')
    return fetchEventAttendance(baseUrl, token, normalizedEventId, options?.params || {})
  }, 'Unable to load event attendance records.')
}

export async function getStudentReport(studentId, options = {}) {
  return runWithReportErrorHandling(async () => {
    const { baseUrl, token } = normalizeContext(options)
    const normalizedStudentId = normalizeId(studentId, 'studentId')
    return fetchStudentAttendanceReport(baseUrl, token, normalizedStudentId, options?.params || {})
  }, 'Unable to load student report.')
}

export async function getStudentStats(studentId, options = {}) {
  return runWithReportErrorHandling(async () => {
    const { baseUrl, token } = normalizeContext(options)
    const normalizedStudentId = normalizeId(studentId, 'studentId')
    return fetchStudentAttendanceStats(baseUrl, token, normalizedStudentId, options?.params || {})
  }, 'Unable to load student attendance stats.')
}

export async function getSchoolSummary(options = {}) {
  return runWithReportErrorHandling(async () => {
    const { baseUrl, token } = normalizeContext(options)
    return fetchAttendanceSummary(baseUrl, token, options?.params || {})
  }, 'Unable to load school attendance summary.')
}

export async function getAttendanceOverview(options = {}) {
  return runWithReportErrorHandling(async () => {
    const { baseUrl, token } = normalizeContext(options)
    return fetchAttendanceOverview(baseUrl, token, options?.params || {})
  }, 'Unable to load attendance overview.')
}

export async function getAuditLogs(options = {}) {
  return runWithReportErrorHandling(async () => {
    const { baseUrl, token } = normalizeContext(options)
    return fetchAuditLogs(baseUrl, token, options?.params || {})
  }, 'Unable to load audit logs.')
}

export async function getNotificationLogs(options = {}) {
  return runWithReportErrorHandling(async () => {
    const { baseUrl, token } = normalizeContext(options)
    return fetchNotificationLogs(baseUrl, token, options?.params || {})
  }, 'Unable to load notification logs.')
}

export async function getImportReports(options = {}) {
  return runWithReportErrorHandling(async () => {
    const { baseUrl, token } = normalizeContext(options)
    const jobId = options?.jobId ? String(options.jobId).trim() : ''
    const previewToken = options?.previewToken ? String(options.previewToken).trim() : ''

    const includePreviewErrorsFile = Boolean(options?.includePreviewErrorsFile)
    const includePreviewRetryFile = Boolean(options?.includePreviewRetryFile)
    const includeImportErrorsFile = Boolean(options?.includeImportErrorsFile)

    const result = {
      jobStatus: null,
      previewErrorsFile: null,
      previewRetryFile: null,
      importErrorsFile: null,
    }

    const tasks = []

    if (jobId) {
      tasks.push(
        fetchStudentImportStatus(baseUrl, token, jobId).then((payload) => {
          result.jobStatus = payload
        })
      )
    }

    if (previewToken && includePreviewErrorsFile) {
      tasks.push(
        fetchPreviewErrorsFile(baseUrl, token, previewToken).then((payload) => {
          result.previewErrorsFile = payload
        })
      )
    }

    if (previewToken && includePreviewRetryFile) {
      tasks.push(
        fetchPreviewRetryFile(baseUrl, token, previewToken).then((payload) => {
          result.previewRetryFile = payload
        })
      )
    }

    if (jobId && includeImportErrorsFile) {
      tasks.push(
        fetchImportErrorsFile(baseUrl, token, jobId).then((payload) => {
          result.importErrorsFile = payload
        })
      )
    }

    await Promise.all(tasks)
    return result
  }, 'Unable to load import reports.')
}

export default {
  getReportEvents,
  getReportDepartments,
  getEventAttendanceReport,
  getEventAttendanceRecords,
  getStudentReport,
  getStudentStats,
  getSchoolSummary,
  getAttendanceOverview,
  getAuditLogs,
  getNotificationLogs,
  getImportReports,
}
