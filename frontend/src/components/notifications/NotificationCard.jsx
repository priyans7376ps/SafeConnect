import { useNavigate } from 'react-router-dom';

export default function NotificationCard({ notification, onMarkRead }) {
  const navigate = useNavigate();
  const isEmergencyAlert = notification.notification_type === 'EMERGENCY_ALERT';

  return (
    <div className={`info-card notification-card ${isEmergencyAlert ? 'notification-emergency' : ''} ${notification.is_read ? 'muted' : ''}`}>
      <div className="card-header-row">
        <strong className="notification-title">
          {isEmergencyAlert && <span className="notif-icon" aria-hidden="true">🚨 </span>}
          {notification.title}
        </strong>
        {!notification.is_read && <span className="status-pill active">Unread</span>}
      </div>

      <p className="notification-message">{notification.message}</p>

      <div className="meta-row">
        <span className={`notif-type-label ${isEmergencyAlert ? 'notif-type-emergency' : ''}`}>
          {notification.notification_type}
        </span>
        <span>{new Date(notification.created_at).toLocaleString()}</span>
      </div>

      <div className="notif-actions">
        {isEmergencyAlert && notification.emergency_id && (
          <button
            className="button button-primary notif-view-btn"
            type="button"
            onClick={() => navigate(`/emergency/${notification.emergency_id}`)}
          >
            View Emergency
          </button>
        )}
        {!notification.is_read && (
          <button
            className="text-button"
            type="button"
            onClick={() => onMarkRead(notification.id)}
          >
            Mark as read
          </button>
        )}
      </div>
    </div>
  );
}
