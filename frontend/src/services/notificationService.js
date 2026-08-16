import api from './api';

export const getNotifications = async () => {
  const { data } = await api.get('/notifications');
  return data;
};

export const getUnreadNotifications = async () => {
  const { data } = await api.get('/notifications/unread');
  return data;
};

export const markNotificationAsRead = async (id) => {
  const { data } = await api.put(`/notifications/${id}/read`);
  return data;
};

export const markAllNotificationsRead = async () => {
  const { data } = await api.put('/notifications/read-all');
  return data;
};
