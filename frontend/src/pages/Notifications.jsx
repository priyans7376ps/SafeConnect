import { useEffect, useState } from 'react';
import EmptyState from '../components/common/EmptyState';
import NotificationCard from '../components/notifications/NotificationCard';
import api from '../services/api';

export default function Notifications() {
  const [notifications, setNotifications] = useState([]);

  const fetchNotifications = async () => {
    const { data } = await api.get('/notifications');
    setNotifications(data.data.notifications || []);
  };

  useEffect(() => {
    fetchNotifications();
  }, []);

  const handleRead = async (id) => {
    await api.put(`/notifications/${id}/read`);
    fetchNotifications();
  };

  const handleMarkAllRead = async () => {
    await api.put('/notifications/read-all');
    fetchNotifications();
  };

  return (
    <div className="page-shell">
      <div className="page-header">
        <div>
          <p className="eyebrow">Alerts</p>
          <h1>Notifications</h1>
        </div>
        <button className="button button-secondary" type="button" onClick={handleMarkAllRead}>Mark all read</button>
      </div>

      <div className="panel-card section-gap">
        {notifications.length ? (
          notifications.map((notification) => (
            <NotificationCard key={notification.id} notification={notification} onMarkRead={handleRead} />
          ))
        ) : (
          <EmptyState title="No notifications" message="You have no alerts right now." />
        )}
      </div>
    </div>
  );
}
