import { Link } from 'react-router-dom';
import EmergencyStatus from './EmergencyStatus';

export default function EmergencyCard({ emergency }) {
  if (!emergency) {
    return null;
  }

  return (
    <div className="info-card">
      <div className="card-header-row">
        <strong>{emergency.emergency_type}</strong>
        <EmergencyStatus emergency={emergency} />
      </div>
      <p>{emergency.description}</p>
      <div className="meta-row">
        <span>Priority: {emergency.priority}</span>
        <span>{new Date(emergency.created_at).toLocaleString()}</span>
      </div>
      <Link to={`/emergency/${emergency.id}`} className="text-link">View details</Link>
    </div>
  );
}
