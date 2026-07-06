const CACHE_NAME = 'eoris-v1';
const ASSETS = [
    '/',
    '/scanner',
    '/static/css/style.css',
    '/static/css/fonts.css',
    '/static/js/app.js',
    '/static/manifest.json'
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            return cache.addAll(ASSETS);
        })
    );
});

self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request).then(cachedResponse => {
            if (cachedResponse) {
                return cachedResponse;
            }

            return fetch(event.request).then(response => {
                // If it is a local font file, dynamically cache it
                if (event.request.url.includes('/static/fonts/')) {
                    return caches.open(CACHE_NAME).then(cache => {
                        cache.put(event.request, response.clone());
                        return response;
                    });
                }
                return response;
            });
        })
    );
});
