/**
 * My Habbit Tracker — Progressive Web App Service Worker (Pillar 5, #18)
 * Implements resilient caching, offline navigation fallback, and stale-while-revalidate for static assets.
 */

const CACHE_NAME = 'habittracker-cache-v1';
const OFFLINE_URL = '/offline/';

const PRECACHE_ASSETS = [
  '/static/css/main.css',
  '/static/js/app.js',
  '/static/js/vendor/tailwindcss.js',
  '/static/js/vendor/lucide.js',
  '/static/images/logo.svg',
  '/static/images/logo.png',
  '/static/images/icon-192.png',
  '/static/manifest.json',
  '/offline/'
];

// Install Event: Precache essential static assets & offline fallback
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(PRECACHE_ASSETS).catch((err) => {
        console.warn('PWA Precache warning (some assets may be dynamic):', err);
      });
    })
  );
  self.skipWaiting();
});

// Activate Event: Cleanup stale caches
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
    })
  );
  self.clients.claim();
});

// Fetch Event: Network-first for navigation, stale-while-revalidate for static files
self.addEventListener('fetch', (event) => {
  const request = event.request;

  // Handle HTML navigation requests
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request).catch(() => {
        return caches.match(OFFLINE_URL).then((response) => {
          return response || new Response('You are currently offline. Please reconnect to access My Habbit Tracker.', {
            headers: { 'Content-Type': 'text/html' }
          });
        });
      })
    );
    return;
  }

  // Handle static assets (CSS, JS, Fonts, Images)
  if (request.url.includes('/static/')) {
    event.respondWith(
      caches.match(request).then((cachedResponse) => {
        const fetchPromise = fetch(request).then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const responseToCache = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(request, responseToCache);
            });
          }
          return networkResponse;
        }).catch(() => cachedResponse);

        return cachedResponse || fetchPromise;
      })
    );
  }
});
