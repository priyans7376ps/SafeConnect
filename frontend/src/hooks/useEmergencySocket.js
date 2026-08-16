import { useEffect, useRef, useState } from 'react';
import { io } from 'socket.io-client';
import { getLatestEmergencyLocation } from '../services/locationService';

const SOCKET_SERVER_URL = import.meta.env.VITE_SOCKET_URL || 'http://localhost:5000';

export function useEmergencySocket(emergencyId) {
  const [connectionState, setConnectionState] = useState('DISCONNECTED'); // CONNECTING, CONNECTED, DISCONNECTED, RECONNECTING, ERROR
  const [latestLocation, setLatestLocation] = useState(null);
  const [emergencyEnded, setEmergencyEnded] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [joinedRoom, setJoinedRoom] = useState(false);

  const socketRef = useRef(null);

  useEffect(() => {
    if (!emergencyId) {
      setConnectionState('DISCONNECTED');
      return;
    }

    const token = localStorage.getItem('safeconnect_token');
    if (!token) {
      setConnectionState('ERROR');
      setStatusMessage('Authentication required for live location updates');
      return;
    }

    // Initial fetch of latest location via REST API (source of truth)
    getLatestEmergencyLocation(emergencyId)
      .then((res) => {
        if (res.data?.location) {
          setLatestLocation(res.data.location);
        }
      })
      .catch(() => {
        // May fail if no location recorded yet or not authorized to view location
      });

    setConnectionState('CONNECTING');
    setStatusMessage('Connecting to live location...');

    const socket = io(SOCKET_SERVER_URL, {
      auth: { token },
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });

    socketRef.current = socket;

    socket.on('connect', () => {
      setConnectionState('CONNECTED');
      setStatusMessage('Live location connected.');
      // Request to join the emergency room
      socket.emit('join_emergency', { emergency_id: emergencyId, token });
    });

    socket.on('joined_emergency', () => {
      setJoinedRoom(true);
      setStatusMessage('Connected to emergency live tracking room.');
    });

    socket.on('location_update', (data) => {
      if (data && data.latitude && data.longitude) {
        setLatestLocation({
          emergency_id: data.emergency_id,
          latitude: data.latitude,
          longitude: data.longitude,
          accuracy: data.accuracy,
          timestamp: data.timestamp,
        });
      }
    });

    socket.on('emergency_ended', (data) => {
      setEmergencyEnded(true);
      setStatusMessage(`Emergency has ended (${data?.status || 'RESOLVED'}).`);
    });

    socket.on('error', (err) => {
      const msg = typeof err === 'string' ? err : err?.message || 'WebSocket error';
      setStatusMessage(msg);
    });

    socket.on('connect_error', () => {
      setConnectionState('ERROR');
      setStatusMessage('Connection error. Retrying...');
    });

    socket.on('disconnect', (reason) => {
      setJoinedRoom(false);
      if (reason === 'io server disconnect') {
        setConnectionState('DISCONNECTED');
        setStatusMessage('Disconnected from server.');
      } else {
        setConnectionState('RECONNECTING');
        setStatusMessage('Connection interrupted. Reconnecting...');
      }
    });

    return () => {
      socket.disconnect();
      socketRef.current = null;
    };
  }, [emergencyId]);

  return {
    connectionState,
    latestLocation,
    emergencyEnded,
    statusMessage,
    joinedRoom,
  };
}
