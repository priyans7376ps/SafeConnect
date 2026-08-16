import api from './api';

export const createEmergencyResponse = async (emergencyId, payload = {}) => {
  const { data } = await api.post(`/responses/emergency/${emergencyId}`, payload);
  return data;
};

export const getEmergencyResponses = async (emergencyId) => {
  const { data } = await api.get(`/responses/emergency/${emergencyId}`);
  return data;
};
