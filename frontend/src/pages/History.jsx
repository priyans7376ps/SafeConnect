import { useEffect, useState } from 'react';
import EmptyState from '../components/common/EmptyState';
import api from '../services/api';

export default function History() {
  const [emergencies, setEmergencies] = useState([]);

  useEffect(() => {
    const fetchHistory = async () => {
      const { data } = await api.get('/emergencies');
      setEmergencies(data.data.emergencies || []);
    };
    fetchHistory();
  }, []);

  return (
    <div className="page-shell">
      <div className="page-header">
        <div>
          <p className="eyebrow">History</p>
          <h1>Emergency history</h1>
        </div>
      </div>

      <div className="panel-card section-gap">
        {emergencies.length ? (
          emergencies.map((item) => (
            <div key={item.id} className="info-card">
              <div className="card-header-row">
                <strong>{item.emergency_type}</strong>
                <span className={`status-pill ${item.status.toLowerCase()}`}>{item.status}</span>
              </div>
              <p>{item.description}</p>
              <div className="meta-row">
                <span>Priority: {item.priority}</span>
                <span>{new Date(item.created_at).toLocaleString()}</span>
              </div>
            </div>
          ))
        ) : (
          <EmptyState title="No history yet" message="Your emergency timeline is empty." />
        )}
      </div>
    </div>
  );
}
