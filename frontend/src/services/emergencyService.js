import api from './api';

export const createEmergency = async (payload) => {
  const { data } = await api.post('/emergencies', payload);
  return data;
};

export const getEmergencies = async () => {
  const { data } = await api.get('/emergencies');
  return data;
};

export const getEmergencyById = async (id) => {
  const { data } = await api.get(`/emergencies/${id}`);
  return data;
};

export const updateEmergency = async (id, payload) => {
  const { data } = await api.put(`/emergencies/${id}`, payload);
  return data;
};

export const resolveEmergency = async (id) => {
  const { data } = await api.post(`/emergencies/${id}/resolve`);
  return data;
};

export const cancelEmergency = async (id) => {
  const { data } = await api.post(`/emergencies/${id}/cancel`);
  return data;
};
