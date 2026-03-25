self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open('aura-shell-v1').then((cache) => {
      return cache.addAll([
        '/',
        '/manifest.webmanifest',
        '/pwa-192.png',
        '/pwa-512.png',
        '/pwa-maskable-512.png',
      ])
    })
  )

  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== 'aura-shell-v1')
          .map((key) => caches.delete(key))
      )
    ).then(() => self.clients.claim())
  )
})

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return

  const requestUrl = new URL(event.request.url)
  if (requestUrl.origin !== self.location.origin) return

  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() => caches.match('/'))
    )
    return
  }

  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) return cachedResponse
      return fetch(event.request)
    })
  )
})
