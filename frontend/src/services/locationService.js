import api from './api';

export const saveLocation = async (payload) => {
  const { data } = await api.post('/locations', payload);
  return data;
};

export const getLocations = async () => {
  const { data } = await api.get('/locations');
  return data;
};

export const getLatestLocation = async () => {
  const { data } = await api.get('/locations/latest');
  return data;
};

export const saveEmergencyLocation = async (emergencyId, payload) => {
  const { data } = await api.post(`/locations/emergency/${emergencyId}`, payload);
  return data;
};

export const getLatestEmergencyLocation = async (emergencyId) => {
  const { data } = await api.get(`/locations/emergency/${emergencyId}/latest`);
  return data;
};
