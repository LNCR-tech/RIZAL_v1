import { resolveAbsoluteApiBaseUrl } from '@/services/backendBaseUrl.js'

const BACKEND_MEDIA_PREFIXES = [
  '/media/',
  'media/',
  '/uploads/',
  'uploads/',
]

export function resolveBackendMediaUrl(value, baseUrl = '') {
  const normalized = String(value || '').trim()
  if (!normalized) return null

  if (
    /^(?:[a-z][a-z0-9+.-]*:)?\/\//i.test(normalized) ||
    normalized.startsWith('data:') ||
    normalized.startsWith('blob:')
  ) {
    return normalized
  }

  if (BACKEND_MEDIA_PREFIXES.some((prefix) => normalized.startsWith(prefix))) {
    const safeBaseUrl = resolveAbsoluteApiBaseUrl(baseUrl)
    return `${safeBaseUrl}/${normalized.replace(/^\/+/, '')}`
  }

  return normalized
}
