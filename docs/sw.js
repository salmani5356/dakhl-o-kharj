/* سرویس‌ورکر خرج‌نگار: همه‌چیز را کش می‌کند تا کاملاً آفلاین کار کند.
   هر بار index.html عوض شد، عدد VERSION را بالا ببر تا گوشی نسخهٔ جدید را بگیرد. */
const VERSION = 'spendbook-v3-5';
const FILES = [
  './', './index.html', './manifest.webmanifest',
  './icons/icon-192.png', './icons/icon-512.png', './icons/maskable-512.png',
  './fonts/Vazirmatn-Regular.woff2', './fonts/Vazirmatn-Bold.woff2',
  './fonts/poppins-latin-400-normal.woff2', './fonts/poppins-latin-700-normal.woff2'
];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(VERSION).then(c => c.addAll(FILES)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== VERSION).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== location.origin) return;
  // صفحه‌ها: اول شبکه (برای گرفتن نسخهٔ جدید)، اگر نبود از کش
  if (req.mode === 'navigate') {
    e.respondWith(fetch(req).then(r => { const cp = r.clone(); caches.open(VERSION).then(c => c.put('./index.html', cp)); return r; })
      .catch(() => caches.match('./index.html')));
    return;
  }
  // بقیه: اول کش
  e.respondWith(caches.match(req).then(h => h || fetch(req).then(r => { const cp = r.clone(); caches.open(VERSION).then(c => c.put(req, cp)); return r; })));
});
