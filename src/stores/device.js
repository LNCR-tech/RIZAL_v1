import { defineStore } from 'pinia'
import {
  DESKTOP_PLATFORM,
  MOBILE_PLATFORM,
  detectRuntimePlatform,
} from '@/services/platform/deviceProfile.js'

let cleanupListeners = null

export const useDeviceStore = defineStore('device', {
  state: () => ({
    platform: DESKTOP_PLATFORM,
    strategy: 'viewport',
    viewportWidth: 1280,
    userAgent: '',
    initialized: false,
  }),
  getters: {
    isMobile: (state) => state.platform === MOBILE_PLATFORM,
    isDesktop: (state) => state.platform === DESKTOP_PLATFORM,
  },
  actions: {
    sync(options = {}) {
      const snapshot = detectRuntimePlatform(options)
      this.platform = snapshot.platform
      this.strategy = snapshot.strategy
      this.viewportWidth = snapshot.viewportWidth
      this.userAgent = snapshot.userAgent
      this.initialized = true
      return snapshot
    },
    initialize() {
      this.sync()

      if (typeof window === 'undefined') {
        return this
      }

      cleanupListeners?.()

      const handleViewportChange = () => {
        this.sync()
      }

      window.addEventListener('resize', handleViewportChange, { passive: true })
      window.addEventListener('orientationchange', handleViewportChange, { passive: true })

      cleanupListeners = () => {
        window.removeEventListener('resize', handleViewportChange)
        window.removeEventListener('orientationchange', handleViewportChange)
      }

      return this
    },
  },
})

export function initializeDeviceStore(pinia) {
  const deviceStore = useDeviceStore(pinia)
  deviceStore.initialize()
  return deviceStore
}

