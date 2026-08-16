// Service Worker for SafeConnect Web Push Notifications (Phase 8)

self.addEventListener('push', (event) => {
  let payload = {};
  if (event.data) {
    try {
      payload = event.data.json();
    } catch (e) {
      payload = { title: 'SafeConnect Emergency Alert', body: event.data.text() };
    }
  }

  const title = payload.title || 'SafeConnect Safety Alert';
  const options = {
    body: payload.body || 'A safety alert requires your attention.',
    icon: payload.icon || '/favicon.ico',
    badge: '/favicon.ico',
    tag: payload.data?.notification_type || 'safeconnect-alert',
    data: payload.data || { url: '/notifications' },
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const targetUrl = event.notification.data?.url || '/';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windowClients) => {
      for (const client of windowClients) {
        if (client.url.includes(targetUrl) && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(targetUrl);
      }
    })
  );
});
