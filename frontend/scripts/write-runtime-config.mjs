import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const outputPath = path.resolve(projectRoot, process.argv[2] || 'dist/runtime-config.js')

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

function parsePositiveNumber(value) {
  const normalized = Number(value)
  return Number.isFinite(normalized) && normalized > 0 ? normalized : null
}

function readFirstAbsoluteUrl(values = []) {
  for (const value of values) {
    const normalized = normalizeAbsoluteUrl(value)
    if (normalized) return normalized
  }

  return ''
}

const PROJECT_ENV_FILES = [
  '.env',
  '.env.local',
  '.env.development.local',
  '.env.docker',
]

const env = PROJECT_ENV_FILES.reduce((acc, relativePath) => ({
  ...acc,
  ...loadEnvFile(path.join(projectRoot, relativePath)),
}), {})

Object.assign(env, process.env)

const runtimeConfig = {}

const nativeApiBaseUrl = normalizeAbsoluteUrl(
  env.VITE_NATIVE_API_BASE_URL || env.VITE_BACKEND_PROXY_TARGET
)

const webApiBaseUrl = readFirstAbsoluteUrl([
  env.AURA_API_BASE_URL
  || '',
  env.VITE_WEB_API_BASE_URL || '',
  env.VITE_API_BASE_URL || '',
  nativeApiBaseUrl,
])

if (webApiBaseUrl) {
  runtimeConfig.apiBaseUrl = webApiBaseUrl
}

if (nativeApiBaseUrl) {
  runtimeConfig.nativeApiBaseUrl = nativeApiBaseUrl
}

const apiTimeoutMs = parsePositiveNumber(env.VITE_API_TIMEOUT_MS)
if (apiTimeoutMs != null) {
  runtimeConfig.apiTimeoutMs = apiTimeoutMs
}

const importApiTimeoutMs = parsePositiveNumber(env.VITE_IMPORT_API_TIMEOUT_MS)
if (importApiTimeoutMs != null) {
  runtimeConfig.importApiTimeoutMs = importApiTimeoutMs
}

const fileContents = [
  'window.__AURA_RUNTIME_CONFIG__ = Object.assign(',
  '  window.__AURA_RUNTIME_CONFIG__ || {},',
  `  ${JSON.stringify(runtimeConfig, null, 2)}`,
  ')',
  '',
].join('\n')

fs.mkdirSync(path.dirname(outputPath), { recursive: true })
fs.writeFileSync(outputPath, fileContents, 'utf-8')
console.log(`Wrote runtime config to ${outputPath}`)
