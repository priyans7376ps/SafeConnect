/**
 * useLocationTracking
 *
 * Manages browser GPS watchPosition for an active emergency with bounded local retry queue.
 *
 * Tracking strategy:
 *   - Uses navigator.geolocation.watchPosition() for continuous GPS.
 *   - Throttles API writes: a backend call is sent at most once every
 *     THROTTLE_MS (default 8 000 ms = 8 seconds) OR when the position
 *     moves more than DISTANCE_THRESHOLD_M (default 10 metres).
 *   - Network errors do NOT stop the tracker; failed location updates are stored
 *     in a bounded local queue (max 10 items) and retried when network recovers.
 *
 * Limitations (documented):
 *   - Tracking stops when the browser tab is closed or the process is
 *     killed. True background tracking requires a native/mobile app.
 *   - If the device GPS is disabled or the browser denies permission,
 *     tracking will not start and a clear error message is shown.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { saveEmergencyLocation } from '../services/locationService';

const THROTTLE_MS = 8_000;
const DISTANCE_THRESHOLD_M = 10;
const MAX_QUEUE_SIZE = 10;

function haversineMetres(lat1, lon1, lat2, lon2) {
  const R = 6_371_000;
  const toRad = (d) => (d * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

export function useLocationTracking() {
  const [tracking, setTracking] = useState(false);
  const [gpsError, setGpsError] = useState('');
  const [lastCoords, setLastCoords] = useState(null);
  const [pendingRetryCount, setPendingRetryCount] = useState(0);

  const watchIdRef = useRef(null);
  const emergencyIdRef = useRef(null);
  const lastSentAtRef = useRef(0);
  const lastSentCoordsRef = useRef(null);
  const retryQueueRef = useRef([]); // Bounded queue for unsent fixes when offline

  /** Drain pending retry queue sequentially when connection recovers. */
  const drainRetryQueue = useCallback(async () => {
    if (retryQueueRef.current.length === 0 || !emergencyIdRef.current) return;

    const itemsToRetry = [...retryQueueRef.current];
    retryQueueRef.current = [];
    setPendingRetryCount(0);

    for (const coords of itemsToRetry) {
      try {
        await saveEmergencyLocation(emergencyIdRef.current, {
          latitude: coords.latitude,
          longitude: coords.longitude,
          accuracy: coords.accuracy,
        });
        lastSentAtRef.current = Date.now();
        lastSentCoordsRef.current = coords;
      } catch (err) {
        // Re-queue if still offline
        if (retryQueueRef.current.length < MAX_QUEUE_SIZE) {
          retryQueueRef.current.push(coords);
          setPendingRetryCount(retryQueueRef.current.length);
        }
        break; // Stop draining on first failure
      }
    }
  }, []);

  /** Listen for browser online event to trigger queue drain. */
  useEffect(() => {
    const handleOnline = () => {
      if (retryQueueRef.current.length > 0) {
        drainRetryQueue();
      }
    };
    window.addEventListener('online', handleOnline);
    return () => window.removeEventListener('online', handleOnline);
  }, [drainRetryQueue]);

  /** Send one location update to the backend (with bounded retry queue on network failure). */
  const sendLocation = useCallback(
    async (coords) => {
      if (!emergencyIdRef.current) return;
      try {
        await saveEmergencyLocation(emergencyIdRef.current, {
          latitude: coords.latitude,
          longitude: coords.longitude,
          accuracy: coords.accuracy,
        });
        lastSentAtRef.current = Date.now();
        lastSentCoordsRef.current = coords;
        setGpsError('');

        // Also drain any older queued fixes
        if (retryQueueRef.current.length > 0) {
          drainRetryQueue();
        }
      } catch (err) {
        console.warn('[LocationTracking] Failed to send location fix:', err?.message);
        setGpsError('Connection issue. Location fix queued for retry…');

        // Queue unsent fix (avoiding duplicate identical positions)
        const queue = retryQueueRef.current;
        const lastInQueue = queue[queue.length - 1];
        const isDuplicate =
          lastInQueue &&
          lastInQueue.latitude === coords.latitude &&
          lastInQueue.longitude === coords.longitude;

        if (!isDuplicate) {
          if (queue.length >= MAX_QUEUE_SIZE) {
            queue.shift(); // Evict oldest fix if queue full
          }
          queue.push(coords);
          setPendingRetryCount(queue.length);
        }
      }
    },
    [drainRetryQueue]
  );

  const onPosition = useCallback(
    (position) => {
      const coords = {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy: position.coords.accuracy,
      };
      setLastCoords(coords);

      const now = Date.now();
      const timeSinceLastSend = now - lastSentAtRef.current;
      const prev = lastSentCoordsRef.current;

      const movedFarEnough =
        !prev ||
        haversineMetres(prev.latitude, prev.longitude, coords.latitude, coords.longitude) >=
          DISTANCE_THRESHOLD_M;

      const timeThrottleExpired = timeSinceLastSend >= THROTTLE_MS;

      if (timeThrottleExpired || movedFarEnough) {
        sendLocation(coords);
      }
    },
    [sendLocation]
  );

  const onGpsError = useCallback((error) => {
    switch (error.code) {
      case error.PERMISSION_DENIED:
        setGpsError('Location permission is required to share your live location.');
        break;
      case error.POSITION_UNAVAILABLE:
        setGpsError('Location information is currently unavailable. Please check GPS.');
        break;
      case error.TIMEOUT:
        setGpsError('Location request timed out. Retrying…');
        break;
      default:
        setGpsError('An unknown location error occurred.');
    }
  }, []);

  const startTracking = useCallback(
    (emergencyId) => {
      if (watchIdRef.current !== null) return;
      if (!navigator.geolocation) {
        setGpsError('Geolocation is not supported by your browser.');
        return;
      }

      emergencyIdRef.current = emergencyId;
      lastSentAtRef.current = 0;
      lastSentCoordsRef.current = null;
      retryQueueRef.current = [];
      setPendingRetryCount(0);

      const watchId = navigator.geolocation.watchPosition(onPosition, onGpsError, {
        enableHighAccuracy: true,
        maximumAge: 5_000,
        timeout: 15_000,
      });

      watchIdRef.current = watchId;
      setTracking(true);
      setGpsError('');
    },
    [onPosition, onGpsError]
  );

  const stopTracking = useCallback(() => {
    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current);
      watchIdRef.current = null;
    }
    emergencyIdRef.current = null;
    lastSentAtRef.current = 0;
    lastSentCoordsRef.current = null;
    retryQueueRef.current = [];
    setPendingRetryCount(0);
    setTracking(false);
    setLastCoords(null);
  }, []);

  return {
    tracking,
    gpsError,
    lastCoords,
    pendingRetryCount,
    startTracking,
    stopTracking,
  };
}
