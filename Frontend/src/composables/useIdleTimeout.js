import { onBeforeUnmount, onMounted, ref } from 'vue'

const DEFAULT_TIMEOUT_MS = 10 * 60 * 1000 // 10 minutes

export function useIdleTimeout(callback, options = {}) {
  const timeoutMs = options.timeoutMs || DEFAULT_TIMEOUT_MS
  const isIdle = ref(false)
  let timeoutId = null
  let lastActivity = Date.now()

  const events = ['mousemove', 'keydown', 'wheel', 'touchstart', 'click']

  function handleActivity() {
    lastActivity = Date.now()
    if (isIdle.value) {
      isIdle.value = false
    }
    resetTimer()
  }

  // Throttle activity updates to at most once per second for performance
  let throttleTimer = null
  function throttledHandleActivity() {
    if (throttleTimer) return
    throttleTimer = setTimeout(() => {
      throttleTimer = null
      handleActivity()
    }, 1000)
  }

  function resetTimer() {
    if (timeoutId) {
      clearTimeout(timeoutId)
    }
    
    timeoutId = setTimeout(() => {
      isIdle.value = true
      if (typeof callback === 'function') {
        callback()
      }
    }, timeoutMs)
  }

  function start() {
    if (typeof window === 'undefined') return
    
    events.forEach((event) => {
      window.addEventListener(event, throttledHandleActivity, { passive: true })
    })
    
    lastActivity = Date.now()
    isIdle.value = false
    resetTimer()
  }

  function stop() {
    if (typeof window === 'undefined') return
    
    events.forEach((event) => {
      window.removeEventListener(event, throttledHandleActivity, { passive: true })
    })
    
    if (throttleTimer) {
      clearTimeout(throttleTimer)
      throttleTimer = null
    }
    if (timeoutId) {
      clearTimeout(timeoutId)
      timeoutId = null
    }
  }

  // Lifecycle
  onMounted(() => {
    if (options.immediate !== false) {
      start()
    }
  })

  onBeforeUnmount(() => {
    stop()
  })

  return {
    isIdle,
    start,
    stop,
    reset: handleActivity,
  }
}
