import { Capacitor } from '@capacitor/core'
import { clearStoredAuthMeta, getStoredAuthMeta } from '@/services/localAuth.js'

const SESSION_TOKEN_STORAGE_KEY = 'aura_token'
const USER_ROLES_STORAGE_KEY = 'aura_user_roles'
const DASHBOARD_CACHE_STORAGE_KEY = 'aura_dashboard_cache_v1'
const NATIVE_RUNTIME_SESSION_KEY = 'aura_native_runtime_session'

function normalizeRoleKey(role = '') {
  const normalizedRole = String(role || '')
    .trim()
    .toLowerCase()
    .replace(/_/g, '-')

  return normalizedRole === 'campus-admin' ? 'school-it' : normalizedRole
}

function getStoredRoleKeys(meta = getStoredAuthMeta()) {
  if (!Array.isArray(meta?.roles)) return []
  return meta.roles.map((role) => normalizeRoleKey(role)).filter(Boolean)
}

export function shouldPersistStoredSession(meta = getStoredAuthMeta()) {
  const roleKeys = getStoredRoleKeys(meta)
  return !roleKeys.includes('school-it') && !roleKeys.includes('admin')
}

function decodeBase64UrlJson(value = '') {
  try {
    const normalized = String(value || '').replace(/-/g, '+').replace(/_/g, '/')
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, '=')
    return JSON.parse(atob(padded))
  } catch {
    return null
  }
}

function isExpiredJwt(token = '', skewMs = 30000) {
  const parts = String(token || '').split('.')
  if (parts.length !== 3) return false

  const payload = decodeBase64UrlJson(parts[1])
  const expirationSeconds = Number(payload?.exp)
  if (!Number.isFinite(expirationSeconds)) return false

  return Date.now() >= (expirationSeconds * 1000) - skewMs
}

export function clearStoredSessionArtifacts() {
  if (typeof window === 'undefined' || typeof window.localStorage === 'undefined') {
    return
  }

  window.localStorage.removeItem(SESSION_TOKEN_STORAGE_KEY)
  window.localStorage.removeItem(USER_ROLES_STORAGE_KEY)
  window.localStorage.removeItem(DASHBOARD_CACHE_STORAGE_KEY)
  window.sessionStorage?.removeItem?.(NATIVE_RUNTIME_SESSION_KEY)
  clearStoredAuthMeta()
}

export function markCurrentRuntimeSession() {
  if (typeof window === 'undefined' || typeof window.sessionStorage === 'undefined') {
    return
  }

  try {
    window.sessionStorage.setItem(NATIVE_RUNTIME_SESSION_KEY, '1')
  } catch {
    // Ignore sessionStorage failures and keep auth usable.
  }
}

function hasCurrentRuntimeSession() {
  if (typeof window === 'undefined' || typeof window.sessionStorage === 'undefined') {
    return false
  }

  try {
    return window.sessionStorage.getItem(NATIVE_RUNTIME_SESSION_KEY) === '1'
  } catch {
    return false
  }
}

export function bootstrapStoredSessionPersistence() {
  if (!Capacitor.isNativePlatform()) return
  if (shouldPersistStoredSession()) return
  if (hasCurrentRuntimeSession()) return

  clearStoredSessionArtifacts()
}

export function readStoredSessionToken() {
  bootstrapStoredSessionPersistence()

  if (typeof window === 'undefined' || typeof window.localStorage === 'undefined') {
    return ''
  }

  const token = String(window.localStorage.getItem(SESSION_TOKEN_STORAGE_KEY) || '')
  if (token && isExpiredJwt(token)) {
    clearStoredSessionArtifacts()
    return ''
  }

  return token
}

export function hasStoredSessionToken() {
  return Boolean(readStoredSessionToken())
}
