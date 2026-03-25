import { createApp } from 'vue'
import router from '@/router/index.js'
import App from './App.vue'
import './assets/css/main.css'

import { loadTheme, applyTheme } from '@/config/theme.js'
import { clearDashboardSession, initializeDashboardSession } from '@/composables/useDashboardSession.js'
import { startDocumentBrandingSync } from '@/services/documentBranding.js'
import { hasPrivilegedPendingFace } from '@/services/localAuth.js'
import { registerAuraServiceWorker, startMobileFullscreenSync } from '@/services/mobileFullscreen.js'
import { SESSION_EXPIRED_EVENT } from '@/services/sessionExpiry.js'

applyTheme(loadTheme())

const app = createApp(App)
app.use(router)
app.mount('#app')

startDocumentBrandingSync(router)
registerAuraServiceWorker()
startMobileFullscreenSync()

if (typeof window !== 'undefined') {
  window.addEventListener(SESSION_EXPIRED_EVENT, () => {
    clearDashboardSession()

    if (router.currentRoute.value?.name !== 'Login') {
      router.replace({ name: 'Login' }).catch(() => null)
    }
  })
}

if (localStorage.getItem('aura_token') && !hasPrivilegedPendingFace()) {
  initializeDashboardSession().catch(() => null)
}
