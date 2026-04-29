import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const configOutputPath = path.join(projectRoot, 'capacitor.config.json')

function loadEnvFile(filePath) {
  if (!fs.existsSync(filePath)) return {}

  const content = fs.readFileSync(filePath, 'utf-8')
  return content.split(/\r?\n/).reduce((acc, line) => {
    const trimmed = line.trim()
    if (!trimmed || trimmed.startsWith('#')) return acc

    const separatorIndex = trimmed.indexOf('=')
    if (separatorIndex <= 0) return acc

    const key = trimmed.slice(0, separatorIndex).trim()
    const rawValue = trimmed.slice(separatorIndex + 1).trim()
    if (!key) return acc

    acc[key] = rawValue.replace(/^['"]|['"]$/g, '')
    return acc
  }, {})
}

const PROJECT_ENV_FILES = [
  '.env',
  '.env.local',
  '.env.development.local',
  '.env.docker',
]

function readProjectEnvLayers() {
  return PROJECT_ENV_FILES.map((relativePath) => loadEnvFile(path.join(projectRoot, relativePath)))
}

function mergeEnvLayers(layers = []) {
  return layers.reduce((acc, layer) => ({
    ...acc,
    ...layer,
  }), {})
}

function normalizeAbsoluteUrl(value = '') {
  const normalized = String(value || '').trim().replace(/\/+$/, '')
  if (!/^https?:\/\//i.test(normalized)) return ''

  try {
    const url = new URL(normalized)
    if (url.pathname === '/api') {
      url.pathname = ''
    }
    return url.toString().replace(/\/+$/, '')
  } catch {
    return ''
  }
}

function collectConfiguredApiHostnames(envLayers = []) {
  const hostnames = []

  envLayers.forEach((layer) => {
    ;[
      layer?.VITE_NATIVE_API_BASE_URL,
      layer?.VITE_BACKEND_PROXY_TARGET,
      layer?.VITE_API_BASE_URL,
    ].forEach((value) => {
      const normalized = normalizeAbsoluteUrl(value)
      if (!normalized) return

      try {
        hostnames.push(new URL(normalized).hostname)
      } catch {
        // Ignore malformed absolute URLs.
      }
    })
  })

  return Array.from(new Set(hostnames))
}

const projectEnvLayers = readProjectEnvLayers()
const env = {
  ...mergeEnvLayers(projectEnvLayers),
  ...process.env,
}

const nativeApiBaseUrl = normalizeAbsoluteUrl(
  env.VITE_NATIVE_API_BASE_URL || env.VITE_BACKEND_PROXY_TARGET
)

if (!nativeApiBaseUrl) {
  console.warn(
    'Aura Android build warning: no native API base URL is configured. Set VITE_NATIVE_API_BASE_URL or VITE_BACKEND_PROXY_TARGET before building the pilot APK.'
  )
} else if (nativeApiBaseUrl.startsWith('http://')) {
  console.warn(
    'Aura Android build warning: native API base URL is using cleartext HTTP. Use an HTTPS ngrok tunnel for pilot testing.'
  )
}

const allowNavigation = Array.from(
  new Set(
    [
      ...collectConfiguredApiHostnames([
        ...projectEnvLayers,
        process.env,
      ]),
      nativeApiBaseUrl ? new URL(nativeApiBaseUrl).hostname : null,
      '*.railway.app',
      '*.ngrok-free.dev',
      '*.ngrok.dev',
      '*.ngrok-free.app',
      '*.ngrok.app',
    ].filter(Boolean)
  )
)

const config = {
  appId: 'com.aura.app',
  appName: 'Aura',
  webDir: 'dist',
  server: {
    androidScheme: 'https',
    allowNavigation,
  },
  android: {
    path: '../frontend-apk/android',
    allowMixedContent: nativeApiBaseUrl.startsWith('http://'),
  },
  plugins: {
    CapacitorHttp: {
      enabled: true,
    },
    SplashScreen: {
      launchAutoHide: false,
      launchShowDuration: 2400,
      launchFadeOutDuration: 150,
      androidScaleType: 'CENTER_CROP',
      backgroundColor: '#050505',
      splashFullScreen: true,
      splashImmersive: true,
    },
    StatusBar: {
      style: 'LIGHT',
      backgroundColor: '#050505',
    },
    Keyboard: {
      resize: 'none',
      resizeOnFullScreen: false,
    },
    LocalNotifications: {
      smallIcon: 'ic_stat_aura',
      iconColor: '#76FF03',
    },
  },
}

fs.writeFileSync(configOutputPath, `${JSON.stringify(config, null, 2)}\n`, 'utf-8')
console.log(`Wrote Capacitor config to ${configOutputPath}`)
