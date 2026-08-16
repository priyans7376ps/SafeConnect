import { createContext, useMemo, useState } from 'react';
import { cancelEmergency, createEmergency, getEmergencies, resolveEmergency } from '../services/emergencyService';

export const EmergencyContext = createContext(null);

export function EmergencyProvider({ children }) {
  const [activeEmergency, setActiveEmergency] = useState(null);
  const [emergencies, setEmergencies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const refreshEmergencies = async () => {
    try {
      setLoading(true);
      const response = await getEmergencies();
      const list = response.data.emergencies || [];
      setEmergencies(list);
      const active = list.find((item) => item.status === 'ACTIVE') || null;
      setActiveEmergency(active);
      setError('');
      return list;
    } catch (err) {
      setError(err.message || 'Unable to load emergencies');
      return [];
    } finally {
      setLoading(false);
    }
  };

  const create = async (payload) => {
    try {
      setLoading(true);
      const response = await createEmergency(payload);
      const emergency = response.data.emergency;
      setActiveEmergency(emergency);
      setEmergencies((current) => [emergency, ...current]);
      setError('');
      return emergency;
    } catch (err) {
      setError(err.message || 'Unable to create emergency');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const resolve = async (id) => {
    try {
      setLoading(true);
      const response = await resolveEmergency(id);
      const emergency = response.data.emergency;
      setActiveEmergency(null);
      setEmergencies((current) => current.map((item) => (item.id === id ? emergency : item)));
      setError('');
      return emergency;
    } catch (err) {
      setError(err.message || 'Unable to resolve emergency');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const cancel = async (id) => {
    try {
      setLoading(true);
      const response = await cancelEmergency(id);
      const emergency = response.data.emergency;
      setActiveEmergency(null);
      setEmergencies((current) => current.map((item) => (item.id === id ? emergency : item)));
      setError('');
      return emergency;
    } catch (err) {
      setError(err.message || 'Unable to cancel emergency');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const value = useMemo(
    () => ({ activeEmergency, emergencies, loading, error, setError, refreshEmergencies, create, resolve, cancel }),
    [activeEmergency, emergencies, loading, error]
  );

  return <EmergencyContext.Provider value={value}>{children}</EmergencyContext.Provider>;
}
