import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath, URL } from 'node:url'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const base = resolveBasePath(env)
  const rawProxyTarget = String(env.VITE_BACKEND_PROXY_TARGET || '').trim().replace(/\/+$/, '')
  const proxyTarget = normalizeProxyTarget(rawProxyTarget)

  return {
    base,
    plugins: [
      vue(),
      tailwindcss(),
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: proxyTarget
      ? {
          host: '0.0.0.0',
          allowedHosts: ['.ngrok-free.app', '.ngrok-free.dev'],
          proxy: {
            '/__backend__': {
              target: proxyTarget,
              changeOrigin: true,
              secure: true,
              rewrite: (path) => path.replace(/^\/__backend__/, ''),
              headers: {
                'ngrok-skip-browser-warning': 'true',
              },
            },
          },
        }
      : {
          host: '0.0.0.0',
          allowedHosts: ['.ngrok-free.app', '.ngrok-free.dev'],
        },
  }
})

function resolveBasePath(env = {}) {
  const configuredBasePath = String(
    env.VITE_APP_BASE_PATH
    || process.env.VITE_APP_BASE_PATH
    || ''
  ).trim()

  if (configuredBasePath) {
    return normalizeBasePath(configuredBasePath)
  }

  if (process.env.GITHUB_ACTIONS === 'true' && process.env.GITHUB_REPOSITORY) {
    const [, repositoryName = ''] = String(process.env.GITHUB_REPOSITORY).split('/')
    if (repositoryName) {
      return `/${repositoryName}/`
    }
  }

  return '/'
}

function normalizeBasePath(value = '/') {
  const normalized = String(value || '/').trim()

  if (!normalized || normalized === '/') {
    return '/'
  }

  return `/${normalized.replace(/^\/+|\/+$/g, '')}/`
}

function normalizeProxyTarget(target) {
  if (!target) return ''

  try {
    const url = new URL(target)
    if (url.pathname === '/api') {
      url.pathname = ''
      return url.toString().replace(/\/+$/, '')
    }
    return url.toString().replace(/\/+$/, '')
  } catch {
    return target
  }
}
