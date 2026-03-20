import { resolveAbsoluteApiBaseUrl } from '@/services/backendBaseUrl.js'

const BACKEND_MEDIA_PREFIXES = [
  '/media/',
  'media/',
  '/uploads/',
  'uploads/',
]

export function resolveBackendMediaUrl(value, baseUrl = '') {
  return resolveBackendMediaCandidates(value, baseUrl)[0] || null
}

export function resolveBackendMediaCandidates(values = [], baseUrl = '') {
  const seen = new Set()

  return (Array.isArray(values) ? values : [values])
    .flatMap((value) => expandBackendMediaVariants(value, baseUrl))
    .filter((value) => {
      if (!value || seen.has(value)) return false
      seen.add(value)
      return true
    })
}

export function withMediaCacheKey(value, key) {
  const normalized = String(value || '').trim()
  if (!normalized || key == null || key === '') return normalized

  const separator = normalized.includes('?') ? '&' : '?'
  return `${normalized}${separator}v=${encodeURIComponent(String(key))}`
}

function expandBackendMediaVariants(value, baseUrl = '') {
  const normalized = String(value || '').trim()
  if (!normalized) return []

  if (normalized.startsWith('data:') || normalized.startsWith('blob:')) {
    return [normalized]
  }

  if (/^(?:[a-z][a-z0-9+.-]*:)?\/\//i.test(normalized)) {
    try {
      const url = new URL(normalized)
      const pathVariants = buildMediaPathVariants(url.pathname)
      if (!pathVariants.length) return [normalized]

      return pathVariants.map((pathname) => {
        const next = new URL(url.toString())
        next.pathname = pathname
        return next.toString()
      })
    } catch {
      return [normalized]
    }
  }

  if (BACKEND_MEDIA_PREFIXES.some((prefix) => normalized.startsWith(prefix))) {
    const safeBaseUrl = resolveAbsoluteApiBaseUrl(baseUrl)
    return buildMediaPathVariants(`/${normalized.replace(/^\/+/, '')}`)
      .map((pathname) => `${safeBaseUrl}${pathname}`)
  }

  return [normalized]
}

function buildMediaPathVariants(pathname) {
  const normalized = `/${String(pathname || '').replace(/^\/+/, '')}`
  const match = normalized.match(/^(.*?)(\/(?:api\/)?(?:media|uploads)\/.*)$/)
  if (!match) return [normalized]

  const prefix = match[1] || ''
  const mediaPath = match[2] || ''
  const baseVariant = `${prefix}${mediaPath.startsWith('/api/') ? mediaPath.replace(/^\/api/, '') : mediaPath}`
  const apiVariant = `${prefix}${mediaPath.startsWith('/api/') ? mediaPath : `/api${mediaPath}`}`

  return [apiVariant, baseVariant].filter(Boolean)
}
