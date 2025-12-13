// Service Worker for Codefyn
const CACHE_NAME = 'codefyn-v1.0';
const urlsToCache = [
  '/',
  '/static/css/main.min.css',
  '/static/js/app.min.js',
  // Add other critical assets here
];

// Install event
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        return cache.addAll(urlsToCache);
      })
  );
});

// Fetch event
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Return cached version or fetch from network
        return response || fetch(event.request);
      })
  );
});