const DEFAULT_ASSISTANT_BASE_URL = '/__assistant__'

function getRuntimeConfig() {
  if (typeof window === 'undefined') return {}
  const runtimeConfig = window.__AURA_RUNTIME_CONFIG__
  return runtimeConfig && typeof runtimeConfig === 'object' ? runtimeConfig : {}
}

function normalizeBaseUrl(value = '') {
  return String(value || '').trim().replace(/\/+$/, '')
}

function getBrowserOrigin() {
  if (typeof window !== 'undefined' && window.location?.origin) {
    return window.location.origin
  }

  return 'http://localhost:5173'
}

export function resolveAssistantBaseUrl(baseUrl = '') {
  const runtimeConfig = getRuntimeConfig()
  const candidate = normalizeBaseUrl(
    baseUrl
    || runtimeConfig.assistantBaseUrl
    || runtimeConfig.assistant_base_url
    || runtimeConfig.assistantApiBaseUrl
    || runtimeConfig.assistant_api_base_url
    || import.meta.env.VITE_ASSISTANT_BASE_URL
    || ''
  )

  return candidate || DEFAULT_ASSISTANT_BASE_URL
}

export function resolveAbsoluteAssistantBaseUrl(baseUrl = '') {
  const resolved = resolveAssistantBaseUrl(baseUrl)

  if (/^[a-z][a-z0-9+.-]*:\/\//i.test(resolved)) {
    return resolved
  }

  if (resolved.startsWith('/')) {
    return `${getBrowserOrigin()}${resolved}`
  }

  return resolved
}
