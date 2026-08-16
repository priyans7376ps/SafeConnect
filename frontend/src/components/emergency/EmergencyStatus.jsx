export default function EmergencyStatus({ emergency }) {
  if (!emergency) {
    return <div className="status-pill neutral">No active emergency</div>;
  }

  const statusClass = emergency.status?.toLowerCase() || 'active';
  return <span className={`status-pill ${statusClass}`}>{emergency.status}</span>;
}
