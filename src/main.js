import { createApp } from 'vue'
import router from '@/router/index.js'
import App from './App.vue'
import './assets/css/main.css'

// Apply the theme immediately from mock data (swap with API response in production)
import { loadTheme, applyTheme } from '@/config/theme.js'
import { mockCurrentUser, mockRtuSettings, mockJrmsuSettings } from '@/data/mockData.js'

// Automatically apply the theme (handles normal users, super admin, and impersonation)
const currentTheme = loadTheme()
applyTheme(currentTheme)

const app = createApp(App)
app.use(router)
app.mount('#app')
