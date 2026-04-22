import { defineAsyncComponent, h } from 'vue'
import { storeToRefs } from 'pinia'
import { useDeviceStore } from '@/stores/device.js'
import AppBootLoader from '@/components/ui/AppBootLoader.vue'
import AppRouteErrorState from '@/components/ui/AppRouteErrorState.vue'
import { setAppFatalError } from '@/services/appBootstrap.js'

const viewModules = import.meta.glob('../views/**/*.vue')
const ASYNC_VIEW_TIMEOUT_MS = 15000

function resolveLoader(path) {
  return viewModules[`../views/${path}.vue`] || null
}

function isChunkLoadError(error) {
  const message = String(error?.message || error || '')
  return /Failed to fetch dynamically imported module|Importing a module script failed|Loading chunk [\d]+ failed|error loading dynamically imported module/i.test(message)
}

function createAsyncViewComponent(loader, viewLabel) {
  return defineAsyncComponent({
    loader,
    loadingComponent: AppBootLoader,
    errorComponent: AppRouteErrorState,
    delay: 120,
    timeout: ASYNC_VIEW_TIMEOUT_MS,
    suspensible: false,
    onError(error, retry, fail, attempts) {
      if (isChunkLoadError(error) && attempts <= 1) {
        retry()
        return
      }

      setAppFatalError(error, `loading ${viewLabel}`)
      fail(error)
    },
  })
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

  const desktopLabel = `${viewPath} desktop view`
  const mobileLabel = `${viewPath} mobile view`
  const DesktopComponent = createAsyncViewComponent(desktopLoader, desktopLabel)
  const MobileComponent = createAsyncViewComponent(mobileLoader, mobileLabel)

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

