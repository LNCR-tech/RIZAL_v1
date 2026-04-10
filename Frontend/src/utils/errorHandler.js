const ERROR_LOG_KEY = 'error_log'
const MAX_ERRORS = 50

export function logError(context, error, additionalInfo = {}) {
  try {
    const errorEntry = {
      timestamp: new Date().toISOString(),
      context,
      message: error?.message || String(error),
      stack: error?.stack || null,
      ...additionalInfo,
    }

    const existing = getErrorLog()
    existing.unshift(errorEntry)

    if (existing.length > MAX_ERRORS) {
      existing.splice(MAX_ERRORS)
    }

    localStorage.setItem(ERROR_LOG_KEY, JSON.stringify(existing))

    console.error(`[${context}]`, error)
  } catch (e) {
    console.error('Failed to log error:', e)
  }
}

export function getErrorLog() {
  try {
    const data = localStorage.getItem(ERROR_LOG_KEY)
    return data ? JSON.parse(data) : []
  } catch {
    return []
  }
}

export function clearErrorLog() {
  try {
    localStorage.removeItem(ERROR_LOG_KEY)
  } catch {
    // Ignore
  }
}

export function getErrorByContext(context) {
  const errors = getErrorLog()
  return errors.filter(e => e.context === context)
}

export function formatErrorMessage(error) {
  if (!error) return 'An unknown error occurred.'

  if (typeof error === 'string') return error

  if (error?.detail) {
    if (typeof error.detail === 'string') return error.detail
    
    if (error.detail?.message) return error.detail.message
    
    return JSON.stringify(error.detail)
  }

  if (error?.message) return error.message

  return 'An error occurred. Please try again.'
}

export function isNetworkError(error) {
  if (!error) return false
  return (
    error?.message?.includes('network') ||
    error?.message?.includes('fetch') ||
    error?.message?.includes('Failed to fetch') ||
    error?.message?.includes('Network request failed') ||
    error?.name === 'TypeError'
  )
}

export function isTimeoutError(error) {
  if (!error) return false
  return (
    error?.message?.includes('timeout') ||
    error?.message?.includes('timed out')
  )
}

export function isAuthError(error) {
  if (!error) return false
  const status = error?.status || error?.response?.status
  return status === 401 || status === 403
}
