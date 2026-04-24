import { defineAsyncComponent, h } from 'vue'
import { storeToRefs } from 'pinia'
import { useDeviceStore } from '@/stores/device.js'

const viewModules = import.meta.glob('../views/**/*.vue')
const modulePromiseCache = new Map()

function resolveLoader(path) {
  return viewModules[`../views/${path}.vue`] || null
}

function resolvePlatformSpec(viewPath, options = {}) {
  const desktopPath = options.desktopPath || `desktop/${viewPath}`
  const mobilePath = options.mobilePath || `mobile/${viewPath}`
  const legacyPath = options.legacyPath || viewPath

  const resolvedDesktopPath = resolveLoader(desktopPath) ? desktopPath : legacyPath
  const resolvedMobilePath = resolveLoader(mobilePath) ? mobilePath : legacyPath
  const desktopLoader = resolveLoader(resolvedDesktopPath)
  const mobileLoader = resolveLoader(resolvedMobilePath)

  if (!desktopLoader || !mobileLoader) {
    throw new Error(
      `[platformView] Missing view "${viewPath}". Expected platform files under src/views/desktop or src/views/mobile, or a legacy fallback at src/views/${legacyPath}.vue.`
    )
  }

  return {
    desktopPath: resolvedDesktopPath,
    desktopLoader,
    mobilePath: resolvedMobilePath,
    mobileLoader,
  }
}

function isRetriableImportError(error) {
  const message = String(error?.message || error || '')
  return /Failed to fetch dynamically imported module|Importing a module script failed|Loading chunk [\d]+ failed|error loading dynamically imported module/i.test(message)
}

function loadViewModule(path, loader) {
  if (!modulePromiseCache.has(path)) {
    const request = Promise.resolve()
      .then(() => loader())
      .catch((error) => {
        modulePromiseCache.delete(path)
        throw error
      })

    modulePromiseCache.set(path, request)
  }

  return modulePromiseCache.get(path)
}

function createAsyncView(path, loader) {
  return defineAsyncComponent({
    loader: () => loadViewModule(path, loader),
    delay: 80,
    timeout: 20000,
    onError(error, retry, fail, attempts) {
      if (attempts < 2 && isRetriableImportError(error)) {
        setTimeout(() => retry(), 160 * attempts)
        return
      }

      fail(error)
    },
  })
}

export function preloadPlatformView(viewPath, options = {}) {
  const { desktopPath, desktopLoader, mobilePath, mobileLoader } = resolvePlatformSpec(viewPath, options)

  return Promise.all([
    loadViewModule(desktopPath, desktopLoader),
    loadViewModule(mobilePath, mobileLoader),
  ])
}

export function preloadPlatformViews(entries = []) {
  return Promise.all(
    entries.map((entry) => (
      Array.isArray(entry)
        ? preloadPlatformView(entry[0], entry[1] || {})
        : preloadPlatformView(entry)
    ))
  )
}

export function createPlatformView(viewPath, options = {}) {
  const { desktopPath, desktopLoader, mobilePath, mobileLoader } = resolvePlatformSpec(viewPath, options)
  const DesktopComponent = createAsyncView(desktopPath, desktopLoader)
  const MobileComponent = createAsyncView(mobilePath, mobileLoader)

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
