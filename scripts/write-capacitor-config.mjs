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

function readProjectEnv() {
  const envFiles = [
    '.env',
    '.env.local',
    '.env.development.local',
    '.env.docker',
  ]

  return envFiles.reduce((acc, relativePath) => {
    return {
      ...acc,
      ...loadEnvFile(path.join(projectRoot, relativePath)),
    }
  }, {})
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

const env = {
  ...readProjectEnv(),
  ...process.env,
}

const nativeApiBaseUrl = normalizeAbsoluteUrl(
  env.VITE_NATIVE_API_BASE_URL || env.VITE_BACKEND_PROXY_TARGET
)

const allowNavigation = Array.from(
  new Set(
    [
      nativeApiBaseUrl ? new URL(nativeApiBaseUrl).hostname : null,
      '*.railway.app',
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
    allowMixedContent: nativeApiBaseUrl.startsWith('http://'),
  },
  plugins: {
    CapacitorHttp: {
      enabled: true,
    },
    SplashScreen: {
      launchAutoHide: true,
      launchShowDuration: 2000,
      androidScaleType: 'CENTER_CROP',
      backgroundColor: '#EBEBEB',
      splashFullScreen: true,
      splashImmersive: true,
    },
    StatusBar: {
      style: 'LIGHT',
      backgroundColor: '#EBEBEB',
    },
    Keyboard: {
      resize: 'none',
      resizeOnFullScreen: false,
    },
  },
}

fs.writeFileSync(configOutputPath, `${JSON.stringify(config, null, 2)}\n`, 'utf-8')
console.log(`Wrote Capacitor config to ${configOutputPath}`)
