import { ref } from 'vue'
import { Capacitor } from '@capacitor/core'

const MIN_VISIBLE_MS = 2400

export const bootSplashVisible = ref(true)

let appReady = false
let playbackReady = false
let nativeSplashReleased = !Capacitor.isNativePlatform()
let nativeSplashHideRequested = false
let dismissTimer = null
let visibleStartedAt = null

function now() {
  return typeof performance !== 'undefined' ? performance.now() : Date.now()
}

async function releaseNativeSplash() {
  if (!Capacitor.isNativePlatform() || nativeSplashReleased || nativeSplashHideRequested) {
    return
  }

  nativeSplashHideRequested = true

  try {
    const { SplashScreen } = await import('@capacitor/splash-screen')
    await SplashScreen.hide()
  } catch {
    // Ignore native splash failures so the web overlay can still dismiss.
  } finally {
    nativeSplashReleased = true
    scheduleDismiss()
  }
}

function scheduleDismiss() {
  if (!bootSplashVisible.value || !appReady || !playbackReady || !nativeSplashReleased) {
    return
  }

  if (dismissTimer) {
    clearTimeout(dismissTimer)
  }

  if (visibleStartedAt == null) {
    visibleStartedAt = now()
  }

  const remaining = Math.max(0, MIN_VISIBLE_MS - (now() - visibleStartedAt))
  dismissTimer = window.setTimeout(() => {
    bootSplashVisible.value = false
    dismissTimer = null
  }, remaining)
}

export function notifyBootSplashMounted() {
  if (!Capacitor.isNativePlatform()) {
    nativeSplashReleased = true
    scheduleDismiss()
    return
  }

  window.requestAnimationFrame(() => {
    window.setTimeout(() => {
      void releaseNativeSplash()
    }, 40)
  })
}

export function markBootSplashReady() {
  appReady = true
  scheduleDismiss()
}

export function markBootSplashPlaybackReady() {
  if (playbackReady) {
    return
  }

  playbackReady = true
  visibleStartedAt = now()
  scheduleDismiss()
}
