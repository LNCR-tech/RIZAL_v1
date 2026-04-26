import { Capacitor } from '@capacitor/core'
import { initializeDashboardSession } from '@/composables/useDashboardSession.js'
import { hasPrivilegedPendingFace } from '@/services/localAuth.js'
import { hasStoredSessionToken } from '@/services/sessionPersistence.js'

const DEFAULT_REFRESH_INTERVAL_MS = 30000
const MIN_REFRESH_INTERVAL_MS = 10000

let started = false
let timerId = null
let refreshInFlight = false
let lastRefreshAt = 0

function resolveRefreshIntervalMs() {
  const configuredValue = Number(import.meta.env.VITE_REALTIME_REFRESH_INTERVAL_MS)
  if (Number.isFinite(configuredValue) && configuredValue > 0) {
    return Math.max(MIN_REFRESH_INTERVAL_MS, configuredValue)
  }

  return DEFAULT_REFRESH_INTERVAL_MS
}

function shouldRefresh() {
  if (!hasStoredSessionToken() || hasPrivilegedPendingFace()) return false
  if (typeof document !== 'undefined' && document.visibilityState === 'hidden') return false
  return true
}

async function refreshDashboardSession({ force = true } = {}) {
  if (refreshInFlight || !shouldRefresh()) return

  refreshInFlight = true
  try {
    await initializeDashboardSession(force)
    lastRefreshAt = Date.now()
  } catch {
    // Session expiry and API errors are handled by the session/API layers.
  } finally {
    refreshInFlight = false
  }
}

function scheduleNextRefresh() {
  if (typeof window === 'undefined') return

  window.clearInterval(timerId)
  timerId = window.setInterval(() => {
    refreshDashboardSession({ force: true })
  }, resolveRefreshIntervalMs())
}

function refreshIfStale() {
  const intervalMs = resolveRefreshIntervalMs()
  if (Date.now() - lastRefreshAt < intervalMs) return
  refreshDashboardSession({ force: true })
}

export function startRealtimeSessionSync() {
  if (started || typeof window === 'undefined') return
  started = true

  scheduleNextRefresh()

  window.addEventListener('focus', refreshIfStale)
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
      refreshIfStale()
    }
  })

  if (Capacitor.isNativePlatform()) {
    import('@capacitor/app')
      .then(({ App: CapApp }) => {
        CapApp.addListener('appStateChange', ({ isActive }) => {
          if (isActive) {
            refreshIfStale()
          }
        })
      })
      .catch(() => null)
  }
}
