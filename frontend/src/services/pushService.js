import api from './api';

function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

export const registerServiceWorkerAndPush = async () => {
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
    return { success: false, message: 'Web Push not supported by this browser' };
  }

  try {
    const registration = await navigator.serviceWorker.register('/sw.js');

    if (Notification.permission === 'denied') {
      return { success: false, message: 'Notification permission denied by user' };
    }

    let permission = Notification.permission;
    if (permission === 'default') {
      permission = await Notification.requestPermission();
    }

    if (permission !== 'granted') {
      return { success: false, message: 'Notification permission not granted' };
    }

    // Public VAPID key (from env or fallback)
    const publicVapidKey = import.meta.env.VITE_VAPID_PUBLIC_KEY || '';

    let subscription;
    if (publicVapidKey) {
      const convertedKey = urlBase64ToUint8Array(publicVapidKey);
      subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: convertedKey,
      });
    } else {
      subscription = await registration.pushManager.getSubscription();
      if (!subscription) {
        // Create standard subscription if no vapid key configured in dev
        subscription = await registration.pushManager.subscribe({
          userVisibleOnly: true,
        }).catch(() => null);
      }
    }

    if (subscription) {
      const subJson = subscription.toJSON();
      await api.post('/notifications/push-subscription', {
        endpoint: subJson.endpoint,
        keys: subJson.keys,
        user_agent: navigator.userAgent,
      });
      return { success: true, subscription };
    }

    return { success: false, message: 'Unable to create push subscription' };
  } catch (error) {
    return { success: false, message: error.message || 'Push registration failed' };
  }
};
