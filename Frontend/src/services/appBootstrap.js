import { ref } from 'vue'

const CHUNK_RELOAD_TARGET_KEY = 'aura_chunk_reload_target'
let handlersInstalled = false
let _isNavigating = false

export const appFatalErrorMessage = ref('')

function normalizeErrorMessage(error, context = '') {
  const baseMessage =
    error?.message ||
    error?.reason?.message ||
    error?.reason ||
    (typeof error === 'string' ? error : '') ||
    'Aura hit an unexpected startup error.'

  const cleanedMessage = String(baseMessage || '').trim()
  if (!cleanedMessage) {
    return context ? `Aura hit an unexpected startup error while ${context}.` : 'Aura hit an unexpected startup error.'
  }

  return context ? `${cleanedMessage} (${context})` : cleanedMessage
}

function isChunkLoadError(error) {
  const message = String(
    error?.message ||
    error?.reason?.message ||
    error?.reason ||
    error ||
    ''
  )

  return /Failed to fetch dynamically imported module|Importing a module script failed|Loading chunk [\d]+ failed|error loading dynamically imported module/i.test(message)
}

function isPostNavigationError(message) {
  return (
    message.includes('component is unmounted') ||
    message.includes('Unhandled error during execution') ||
    message.includes('onBeforeUnmount') ||
    message.includes('onUnmounted') ||
    message.includes('inject() can only be used inside setup') ||
    message.includes('getCurrentInstance') ||
    message.includes('AbortError') ||
    message.includes('The user aborted') ||
    message.includes('Navigation cancelled') ||
    message.includes('Avoided redundant navigation')
  )
}

function clearChunkReloadTarget() {
  if (typeof window === 'undefined') return
  window.sessionStorage?.removeItem(CHUNK_RELOAD_TARGET_KEY)
}

async function attemptChunkRecovery(targetPath = '') {
  if (typeof window === 'undefined') return false

  const normalizedTarget = String(targetPath || window.location.pathname || '/').trim() || '/'
  const previousTarget = window.sessionStorage?.getItem(CHUNK_RELOAD_TARGET_KEY)

  if (previousTarget === normalizedTarget) {
    clearChunkReloadTarget()
    return false
  }

  window.sessionStorage?.setItem(CHUNK_RELOAD_TARGET_KEY, normalizedTarget)
  window.location.assign(normalizedTarget)
  return true
}

export function clearAppFatalError() {
  appFatalErrorMessage.value = ''
}

export function setAppFatalError(error, context = '') {
  appFatalErrorMessage.value = normalizeErrorMessage(error, context)
}

export function scheduleNonCriticalStartupTask(task, options = {}) {
  const { timeoutMs = 250 } = options
  if (typeof window === 'undefined') {
    Promise.resolve().then(task).catch(() => null)
    return
  }

  const runTask = () => Promise.resolve().then(task).catch(() => null)

  if (typeof window.requestIdleCallback === 'function') {
    window.requestIdleCallback(runTask, { timeout: timeoutMs })
    return
  }

  window.setTimeout(runTask, 0)
}

export function installAppErrorHandling(app, router) {
  if (handlersInstalled) return
  handlersInstalled = true

  const handleError = async (error, context = '', targetPath = '') => {
    // Never show fatal screen during or after navigation
    if (_isNavigating) return
    if (isChunkLoadError(error) && await attemptChunkRecovery(targetPath)) {
      return
    }
    setAppFatalError(error, context)
  }

  app.config.errorHandler = (error, instance, info) => {
    const message = String(error?.message || '')
    if (isPostNavigationError(message)) {
      console.warn('Aura suppressed post-navigation error:', message)
      return
    }
    console.error('Aura Vue error:', error, info, instance)
    handleError(error, info, router?.currentRoute?.value?.fullPath || '')
  }

  router.onError((error, to) => {
    console.error('Aura router error:', error)
    handleError(error, 'loading the next screen', to?.fullPath || '')
  })

  router.beforeEach(() => {
    _isNavigating = true
    clearAppFatalError()
  })

  router.afterEach(() => {
    clearChunkReloadTarget()
    clearAppFatalError()
    // Keep navigation guard active for 2s to absorb any in-flight
    // background promises from the previous page that resolve late
    setTimeout(() => { _isNavigating = false }, 2000)
  })

  if (typeof window !== 'undefined') {
    window.addEventListener('error', (event) => {
      if (_isNavigating) return
      console.error('Aura window error:', event.error || event.message)
      handleError(event.error || event.message, 'starting the app', window.location.pathname)
    })

    window.addEventListener('unhandledrejection', (event) => {
      if (_isNavigating) return
      const message = String(event.reason?.message || event.reason || '')
      if (isPostNavigationError(message)) return
      console.error('Aura unhandled rejection:', event.reason)
      handleError(event.reason, 'starting the app', router?.currentRoute?.value?.fullPath || window.location.pathname)
    })
  }
}
