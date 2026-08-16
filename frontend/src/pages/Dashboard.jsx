import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import EmergencyButton from '../components/emergency/EmergencyButton';
import EmergencyCard from '../components/emergency/EmergencyCard';
import EmptyState from '../components/common/EmptyState';
import Loading from '../components/common/Loading';
import NotificationBadge from '../components/notifications/NotificationBadge';
import { useAuth } from '../hooks/useAuth';
import { useEmergency } from '../hooks/useEmergency';
import { getNotifications } from '../services/notificationService';

export default function Dashboard() {
  const { user } = useAuth();
  const { activeEmergency, emergencies, loading, refreshEmergencies, create } = useEmergency();

  useEffect(() => {
    refreshEmergencies();
  }, []);

  const handleSos = async () => {
    await create({ emergency_type: 'Medical', description: 'SOS requested from dashboard', priority: 'CRITICAL' });
  };

  return (
    <div className="page-shell">
      <div className="page-header">
        <div>
          <p className="eyebrow">Overview</p>
          <h1>Welcome, {user?.name || 'User'}</h1>
        </div>
        <EmergencyButton label="SOS" onClick={handleSos} />
      </div>

      <div className="dashboard-grid">
        <div className="panel-card">
          <h3>Current emergency status</h3>
          {activeEmergency ? (
            <div>
              <p><strong>{activeEmergency.emergency_type}</strong></p>
              <p>{activeEmergency.description}</p>
              <Link to={`/emergency/${activeEmergency.id}`} className="text-link">Open details</Link>
            </div>
          ) : (
            <p>No active emergency. You are safe.</p>
          )}
        </div>

        <div className="panel-card">
          <h3>Notifications</h3>
          <NotificationBadge count={2} />
          <p>Check recent updates and alerts.</p>
        </div>

        <div className="panel-card">
          <h3>Trusted contacts</h3>
          <p>Keep your emergency network in sync.</p>
          <Link to="/trusted-contacts" className="text-link">Manage contacts</Link>
        </div>
      </div>

      <div className="panel-card section-gap">
        <h3>Recent emergencies</h3>
        {loading ? <Loading /> : emergencies.length ? (
          emergencies.slice(0, 3).map((emergency) => <EmergencyCard key={emergency.id} emergency={emergency} />)
        ) : (
          <EmptyState title="No emergencies yet" message="Create your first emergency if needed." />
        )}
      </div>
    </div>
  );
}
