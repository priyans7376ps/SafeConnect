import { useState } from 'react';
import { getLatestLocation, saveLocation } from '../services/locationService';

export function useLocation() {
  const [location, setLocation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const refreshLocation = async () => {
    try {
      setLoading(true);
      const response = await getLatestLocation();
      setLocation(response.data.location);
      setError('');
      return response.data.location;
    } catch (err) {
      setError(err.message || 'Unable to load location');
      return null;
    } finally {
      setLoading(false);
    }
  };

  const updateLocation = async (payload) => {
    try {
      setLoading(true);
      const response = await saveLocation(payload);
      setLocation(response.data.location);
      setError('');
      return response.data.location;
    } catch (err) {
      setError(err.message || 'Unable to update location');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { location, loading, error, refreshLocation, updateLocation };
}
