const DEFAULT_API_BASE_URL = 'https://sas-deploy-production.up.railway.app'

function getBrowserOrigin() {
  if (typeof window !== 'undefined' && window.location?.origin) {
    return window.location.origin
  }

  return 'http://localhost:5173'
}

export function resolveApiBaseUrl(baseUrl = '') {
  const resolved = String(baseUrl || import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL).trim()
  return resolved.replace(/\/+$/, '')
}

export function resolveAbsoluteApiBaseUrl(baseUrl = '') {
  const resolved = resolveApiBaseUrl(baseUrl)

  if (/^[a-z][a-z0-9+.-]*:\/\//i.test(resolved)) {
    return resolved
  }

  if (resolved.startsWith('/')) {
    return `${getBrowserOrigin()}${resolved}`
  }

  return resolved
}

export function isNgrokApiBaseUrl(baseUrl = '') {
  try {
    const hostname = new URL(resolveAbsoluteApiBaseUrl(baseUrl)).hostname.toLowerCase()
    return /(?:^|\.)ngrok(?:-free)?\.(?:app|dev|io)$/.test(hostname)
  } catch {
    return false
  }
}

