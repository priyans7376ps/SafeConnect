export default function NotificationBadge({ count }) {
  return <span className="notification-badge">{count || 0}</span>;
}
