import { useEffect, useState } from 'react';
import LocationCard from '../components/location/LocationCard';
import Loading from '../components/common/Loading';
import Button from '../components/common/Button';
import { useLocation } from '../hooks/useLocation';

export default function LiveLocation() {
  const { location, loading, refreshLocation, updateLocation } = useLocation();
  const [coords, setCoords] = useState({ latitude: '', longitude: '', accuracy: '' });

  useEffect(() => {
    refreshLocation();
  }, []);

  const handleUseBrowserLocation = () => {
    if (!navigator.geolocation) {
      alert('Geolocation is not supported in this browser.');
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const payload = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
          address: 'Current browser location',
        };
        setCoords({
          latitude: payload.latitude,
          longitude: payload.longitude,
          accuracy: payload.accuracy,
        });
        updateLocation(payload).catch(() => {});
      },
      () => {
        alert('Location access denied.');
      }
    );
  };

  return (
    <div className="page-shell">
      <div className="page-header">
        <div>
          <p className="eyebrow">Tracking</p>
          <h1>Live location</h1>
        </div>
        <Button onClick={handleUseBrowserLocation}>Update location</Button>
      </div>

      <div className="panel-card section-gap">
        {loading ? <Loading /> : <LocationCard location={location || { latitude: coords.latitude || 0, longitude: coords.longitude || 0, accuracy: coords.accuracy || 0, address: 'Current location' }} />}
      </div>
    </div>
  );
}
