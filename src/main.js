import { createApp } from 'vue'
import router from '@/router/index.js'
import App from './App.vue'
import './assets/css/main.css'

import { loadTheme, applyTheme } from '@/config/theme.js'
import { initializeDashboardSession } from '@/composables/useDashboardSession.js'
import { startDocumentBrandingSync } from '@/services/documentBranding.js'

applyTheme(loadTheme())

const app = createApp(App)
app.use(router)
app.mount('#app')

startDocumentBrandingSync(router)

initializeDashboardSession().catch(() => null)
