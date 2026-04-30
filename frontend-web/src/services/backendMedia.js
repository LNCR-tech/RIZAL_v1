import { resolveAbsoluteApiBaseUrl } from '@/services/backendBaseUrl.js'

const BACKEND_MEDIA_PREFIXES = [
  '/media/',
  'media/',
  '/uploads/',
  'uploads/',
]
const mediaProbeCache = new Map()

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

export async function resolveLoadableMediaUrl(values = [], baseUrl = '') {
  const candidates = resolveBackendMediaCandidates(values, baseUrl)
  if (!candidates.length) return null

  for (const candidate of candidates) {
    if (await canLoadMediaUrl(candidate)) {
      return candidate
    }
  }

  return null
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
      const pathVariants = buildAbsoluteUrlPathVariants(url.pathname)
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

  if (looksLikeBackendAssetPath(normalized)) {
    const safeBaseUrl = resolveAbsoluteApiBaseUrl(baseUrl)
    const assetPath = ensureLeadingSlash(normalized)

    return [
      ...buildBackendAssetPathVariants(assetPath).map((pathname) => `${safeBaseUrl}${pathname}`),
      assetPath,
    ]
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

  // Static media mounts in the backend are served from the non-/api path first
  // (for example, school logos default to /media/school-logos/*). We still
  // keep the /api-prefixed variant as a fallback for deployments that proxy
  // those assets differently, but the canonical static path should win.
  return [baseVariant, apiVariant].filter(Boolean)
}

function canLoadMediaUrl(value) {
  const normalized = String(value || '').trim()
  if (!normalized) return Promise.resolve(false)

  if (
    normalized.startsWith('data:')
    || normalized.startsWith('blob:')
    || typeof window === 'undefined'
  ) {
    return Promise.resolve(true)
  }

  const cached = mediaProbeCache.get(normalized)
  if (cached) return cached

  const probe = new Promise((resolve) => {
    const image = new Image()
    let settled = false

    const finish = (result) => {
      if (settled) return
      settled = true
      image.onload = null
      image.onerror = null
      resolve(result)
    }

    image.decoding = 'async'
    image.referrerPolicy = 'strict-origin-when-cross-origin'
    image.onload = () => finish(true)
    image.onerror = () => finish(false)
    image.src = normalized
  })

  mediaProbeCache.set(normalized, probe)
  return probe
}

function looksLikeBackendAssetPath(pathname) {
  const normalized = ensureLeadingSlash(pathname)
  if (!normalized || normalized === '/') return false

  const withoutQuery = normalized.split('?')[0].split('#')[0]
  if (!withoutQuery.includes('/')) return false

  return /\.[a-z0-9]{2,8}$/i.test(withoutQuery)
}

function ensureLeadingSlash(pathname) {
  return `/${String(pathname || '').replace(/^\/+/, '')}`
}

function buildBackendAssetPathVariants(pathname) {
  const normalized = ensureLeadingSlash(pathname)
  const apiVariant = normalized.startsWith('/api/') ? normalized : `/api${normalized}`
  return [normalized, apiVariant]
}

function buildAbsoluteUrlPathVariants(pathname) {
  const normalized = ensureLeadingSlash(pathname)
  const mediaVariants = buildMediaPathVariants(normalized)
  if (mediaVariants.length > 1 || BACKEND_MEDIA_PREFIXES.some((prefix) => normalized.startsWith(ensureLeadingSlash(prefix)))) {
    return mediaVariants
  }

  if (looksLikeBackendAssetPath(normalized)) {
    return buildBackendAssetPathVariants(normalized)
  }

  return [normalized]
}
