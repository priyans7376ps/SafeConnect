import { useEffect, useState } from 'react';
import { MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Custom Leaflet DivIcon for emergency marker (uses 🚨 emoji and animated glow)
const emergencyIcon = L.divIcon({
  className: 'custom-emergency-marker-wrapper',
  html: `
    <div className="custom-emergency-marker" style="
      background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
      color: white;
      width: 40px;
      height: 40px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 18px rgba(239, 68, 68, 0.65), 0 0 0 3px rgba(255, 255, 255, 0.95);
      font-size: 20px;
      cursor: pointer;
    ">
      🚨
    </div>
  `,
  iconSize: [40, 40],
  iconAnchor: [20, 20],
  popupAnchor: [0, -22],
});

// Helper component to update map view position when center changes
function RecenterMap({ center }) {
  const map = useMap();
  useEffect(() => {
    if (center && center[0] !== undefined && center[1] !== undefined) {
      map.panTo(center, { animate: true, duration: 0.8 });
    }
  }, [center, map]);
  return null;
}

export default function LiveEmergencyMap({
  latitude,
  longitude,
  emergencyStatus = 'ACTIVE',
  accuracy,
  timestamp,
  height = '350px',
}) {
  const [autoRecenter, setAutoRecenter] = useState(true);

  const hasValidCoords =
    latitude !== null &&
    latitude !== undefined &&
    longitude !== null &&
    longitude !== undefined &&
    !(latitude === 0 && longitude === 0);

  if (!hasValidCoords) {
    return (
      <div className="map-placeholder-card">
        <div className="map-placeholder-content">
          <span className="map-placeholder-icon">🗺️</span>
          <p className="map-placeholder-text">Waiting for live location...</p>
          <span className="map-placeholder-subtext">Location will appear here as soon as coordinates are transmitted.</span>
        </div>
      </div>
    );
  }

  const position = [latitude, longitude];

  return (
    <div className="live-map-wrapper" style={{ position: 'relative', width: '100%', borderRadius: '16px', overflow: 'hidden' }}>
      <div className="map-controls-overlay">
        <button
          type="button"
          className="button button-secondary map-recenter-btn"
          onClick={() => setAutoRecenter(true)}
        >
          📍 Center on Live Location
        </button>
      </div>

      <MapContainer
        center={position}
        zoom={15}
        scrollWheelZoom={true}
        style={{ height, width: '100%', borderRadius: '16px' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {autoRecenter && <RecenterMap center={position} />}

        <Marker position={position} icon={emergencyIcon}>
          <Popup>
            <div className="map-popup-card">
              <strong>Emergency Location</strong>
              <div style={{ fontSize: '0.82rem', marginTop: '0.25rem', color: '#475569' }}>
                <div>Lat: {latitude.toFixed(6)}</div>
                <div>Lng: {longitude.toFixed(6)}</div>
                {accuracy && <div>Accuracy: ±{Math.round(accuracy)}m</div>}
                {timestamp && <div>Updated: {new Date(timestamp).toLocaleTimeString()}</div>}
              </div>
            </div>
          </Popup>
        </Marker>
      </MapContainer>
    </div>
  );
}
