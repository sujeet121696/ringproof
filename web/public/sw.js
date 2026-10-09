// Ringproof service worker: makes the dashboard installable and lets the app shell open offline.
// It never touches /api or /ws: risk checks need the network, and family memory lives in IndexedDB,
// not in this cache. Bump VERSION to drop old caches.
const VERSION = 'v1'
const CACHE = `ringproof-${VERSION}`
const IMMUTABLE = ['/assets/', '/fonts/', '/icons/']
const SHELL = ['/', '/manifest.webmanifest', '/favicon.svg', '/logo-mark.svg', '/theme-init.js']

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()))
})

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  )
})

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url)
  if (e.request.method !== 'GET' || url.origin !== location.origin) return
  if (url.pathname.startsWith('/api') || url.pathname.startsWith('/ws')) return

  // Built files (hashed names), fonts and icons never change under the same URL: cache first.
  if (IMMUTABLE.some((p) => url.pathname.startsWith(p))) {
    e.respondWith(caches.match(e.request).then((hit) => hit || fetchAndKeep(e.request, e.request)))
    return
  }

  // Everything else (the page, manifest, theme script): network first so a deploy shows up at once;
  // the cached copy is the offline fallback. All pages share the one shell, cached as '/'.
  const key = e.request.mode === 'navigate' ? '/' : e.request
  e.respondWith(fetchAndKeep(e.request, key).catch(() => caches.match(key)))
})

function fetchAndKeep(request, key) {
  return fetch(request).then((res) => {
    if (res.ok) {
      const copy = res.clone()
      caches.open(CACHE).then((c) => c.put(key, copy))
    }
    return res
  })
}
