// ROMUSIC Service Worker — Offline Shell & Asset Caching
const CACHE_NAME = 'romusic-v1';
const PRECACHE_ASSETS = [
    '/',
    '/static/css/style.css',
    '/static/js/player.js',
    '/static/js/app.js',
    '/static/manifest.json',
    '/static/images/romusic_logo.svg'
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(PRECACHE_ASSETS);
        }).then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.map((key) => {
                    if (key !== CACHE_NAME) {
                        return caches.delete(key);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // Bypass audio streaming & API search requests so we always fetch live audio
    if (url.pathname.startsWith('/api/stream') || url.pathname.startsWith('/api/yt/search')) {
        return;
    }

    // Network-first strategy for dynamic pages, fallback to cache
    if (event.request.mode === 'navigate') {
        event.respondWith(
            fetch(event.request).catch(() => {
                return caches.match('/');
            })
        );
        return;
    }

    // Cache-first for static assets
    event.respondWith(
        caches.match(event.request).then((cachedResponse) => {
            if (cachedResponse) {
                return cachedResponse;
            }
            return fetch(event.request);
        })
    );
});

