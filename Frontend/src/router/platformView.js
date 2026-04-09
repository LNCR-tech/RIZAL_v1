import { defineAsyncComponent, h } from 'vue'
import { storeToRefs } from 'pinia'
import { useDeviceStore } from '@/stores/device.js'

const viewModules = import.meta.glob('../views/**/*.vue')

function resolveLoader(path) {
  return viewModules[`../views/${path}.vue`] || null
}

export function createPlatformView(viewPath, options = {}) {
  const desktopPath = options.desktopPath || `desktop/${viewPath}`
  const mobilePath = options.mobilePath || `mobile/${viewPath}`
  const legacyPath = options.legacyPath || viewPath

  const desktopLoader = resolveLoader(desktopPath) || resolveLoader(legacyPath)
  const mobileLoader = resolveLoader(mobilePath) || resolveLoader(legacyPath)

  if (!desktopLoader || !mobileLoader) {
    throw new Error(
      `[platformView] Missing view "${viewPath}". Expected platform files under src/views/desktop or src/views/mobile, or a legacy fallback at src/views/${legacyPath}.vue.`
    )
  }

  const DesktopComponent = defineAsyncComponent(desktopLoader)
  const MobileComponent = defineAsyncComponent(mobileLoader)

  return {
    name: `Platform${String(viewPath).replace(/[^a-zA-Z0-9]/g, '')}`,
    inheritAttrs: false,
    setup(_, { attrs, slots }) {
      const deviceStore = useDeviceStore()
      const { isMobile } = storeToRefs(deviceStore)

      return () => h(
        isMobile.value ? MobileComponent : DesktopComponent,
        attrs,
        slots,
      )
    },
  }
}

