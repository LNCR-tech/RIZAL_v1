import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath, URL } from 'node:url'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const rawProxyTarget = String(env.VITE_BACKEND_PROXY_TARGET || '').trim().replace(/\/+$/, '')
  const proxyTarget = normalizeProxyTarget(rawProxyTarget)

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
