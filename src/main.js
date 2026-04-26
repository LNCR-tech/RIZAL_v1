import { createApp } from 'vue'
import { Capacitor } from '@capacitor/core'
import { createPinia } from 'pinia'
import router from '@/router/index.js'
import App from './App.vue'
import './assets/css/main.css'

import { loadTheme, applyTheme } from '@/config/theme.js'
import { clearDashboardSession, initializeDashboardSession } from '@/composables/useDashboardSession.js'
import { installAppErrorHandling, scheduleNonCriticalStartupTask } from '@/services/appBootstrap.js'
import { startDocumentBrandingSync } from '@/services/documentBranding.js'
import { startNativeEventNotificationSync } from '@/services/eventNotificationSync.js'
import { getStoredAuthMeta, hasPrivilegedPendingFace } from '@/services/localAuth.js'
import { registerAuraServiceWorker, startMobileFullscreenSync } from '@/services/mobileFullscreen.js'
import { startPwaInstallSync } from '@/services/pwaInstall.js'
import { startRealtimeSessionSync } from '@/services/realtimeSessionSync.js'
import { bootstrapStoredSessionPersistence, hasStoredSessionToken } from '@/services/sessionPersistence.js'
import { SESSION_EXPIRED_EVENT } from '@/services/sessionExpiry.js'
import { initializeStoredFontSize } from '@/services/userPreferences.js'
import { initializeDeviceStore } from '@/stores/device.js'

function resolveBootstrapThemeSettings() {
  const authMeta = getStoredAuthMeta()
  if (!authMeta) return null

  const hasBrandingSeed = (
    authMeta.schoolId != null
    || authMeta.schoolName
    || authMeta.logoUrl
    || authMeta.primaryColor
    || authMeta.secondaryColor
    || authMeta.accentColor
  )

  if (!hasBrandingSeed) return null

  return {
    school_id: authMeta.schoolId ?? null,
    school_name: authMeta.schoolName ?? null,
    school_code: authMeta.schoolCode ?? null,
    logo_url: authMeta.logoUrl ?? null,
    primary_color: authMeta.primaryColor ?? null,
    secondary_color: authMeta.secondaryColor ?? null,
    accent_color: authMeta.accentColor ?? null,
  }
}

bootstrapStoredSessionPersistence()
initializeStoredFontSize()
applyTheme(loadTheme(resolveBootstrapThemeSettings()))

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
initializeDeviceStore(pinia)
app.use(router)
installAppErrorHandling(app, router)
app.mount('#app')

scheduleNonCriticalStartupTask(() => startDocumentBrandingSync(router))
scheduleNonCriticalStartupTask(() => startPwaInstallSync())
scheduleNonCriticalStartupTask(() => registerAuraServiceWorker())
scheduleNonCriticalStartupTask(() => startMobileFullscreenSync())
scheduleNonCriticalStartupTask(() => startNativeEventNotificationSync())
scheduleNonCriticalStartupTask(() => startRealtimeSessionSync())

// Session expiry listener
if (typeof window !== 'undefined') {
  window.addEventListener(SESSION_EXPIRED_EVENT, () => {
    clearDashboardSession()

    if (router.currentRoute.value?.name !== 'Login') {
      router.replace({ name: 'Login' }).catch(() => null)
    }
  })
}

// Pre-initialize session if token exists
if (hasStoredSessionToken() && !hasPrivilegedPendingFace()) {
  scheduleNonCriticalStartupTask(() => initializeDashboardSession().catch(() => null), {
    timeoutMs: 500,
  })
}

// --- Capacitor Native Initialization ---
if (Capacitor.isNativePlatform()) {
  // Android back button handler
  import('@capacitor/app').then(({ App: CapApp }) => {
    CapApp.addListener('backButton', ({ canGoBack }) => {
      if (canGoBack) {
        router.back()
      } else {
        // On root screens, minimize app instead of exiting
        CapApp.minimizeApp().catch(() => null)
      }
    })

    // Re-sync session when app returns to foreground
    CapApp.addListener('appStateChange', ({ isActive }) => {
      if (isActive && hasStoredSessionToken()) {
        initializeDashboardSession().catch(() => null)
      }
    })
  }).catch(() => null)

  // Keyboard behavior — scroll focused input into view
  import('@capacitor/keyboard').then(({ Keyboard }) => {
    Keyboard.setAccessoryBarVisible({ isVisible: true }).catch(() => null)
    Keyboard.setScroll({ isDisabled: false }).catch(() => null)

    // When keyboard shows, scroll the focused input into view
    Keyboard.addListener('keyboardWillShow', () => {
      setTimeout(() => {
        const activeEl = document.activeElement
        if (activeEl && (activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA')) {
          activeEl.scrollIntoView({ behavior: 'smooth', block: 'center' })
        }
      }, 100)
    })
  }).catch(() => null)
}

// Cross-tab session sync (for web — logout in one tab logs out all)
if (typeof window !== 'undefined' && !Capacitor.isNativePlatform()) {
  window.addEventListener('storage', (event) => {
    if (event.key === 'aura_token' && !event.newValue) {
      clearDashboardSession()
      if (router.currentRoute.value?.name !== 'Login') {
        router.replace({ name: 'Login' }).catch(() => null)
      }
    }
  })
}
