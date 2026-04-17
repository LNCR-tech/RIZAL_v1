import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath, URL } from 'node:url'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const rawBackendProxyTarget = String(env.VITE_BACKEND_PROXY_TARGET || '').trim().replace(/\/+$/, '')
  const rawAssistantProxyTarget = String(env.VITE_ASSISTANT_PROXY_TARGET || '').trim().replace(/\/+$/, '')
  const backendProxyTarget = normalizeProxyTarget(rawBackendProxyTarget)
  const assistantProxyTarget = normalizeProxyTarget(rawAssistantProxyTarget)
  const hasProxy = Boolean(backendProxyTarget || assistantProxyTarget)

  return {
    plugins: [
      vue(),
      tailwindcss(),
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: hasProxy
      ? {
          host: '0.0.0.0',
          allowedHosts: ['.ngrok-free.app', '.ngrok-free.dev'],
          proxy: {
            ...(backendProxyTarget
              ? {
                  '/__backend__': {
                    target: backendProxyTarget,
                    changeOrigin: true,
                    secure: true,
                    rewrite: (path) => path.replace(/^\/__backend__/, ''),
                    headers: {
                      'ngrok-skip-browser-warning': 'true',
                    },
                  },
                }
              : {}),
            ...(assistantProxyTarget
              ? {
                  '/__assistant__': {
                    target: assistantProxyTarget,
                    changeOrigin: true,
                    secure: true,
                    rewrite: (path) => path.replace(/^\/__assistant__/, ''),
                    headers: {
                      'ngrok-skip-browser-warning': 'true',
                    },
                  },
                }
              : {}),
          },
        }
      : {
          host: '0.0.0.0',
          allowedHosts: ['.ngrok-free.app', '.ngrok-free.dev'],
        },
  }
})

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
