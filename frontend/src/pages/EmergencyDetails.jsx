import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import Loading from '../components/common/Loading';
import LiveEmergencyMap from '../components/location/LiveEmergencyMap';
import { useEmergencySocket } from '../hooks/useEmergencySocket';
import { useOnlineStatus } from '../hooks/useOnlineStatus';
import { cancelEmergency, getEmergencyById, resolveEmergency } from '../services/emergencyService';
import { registerServiceWorkerAndPush } from '../services/pushService';
import { createEmergencyResponse, getEmergencyResponses } from '../services/responseService';

function getCurrentUserId() {
  try {
    const userStr = localStorage.getItem('safeconnect_user');
    if (userStr) {
      const user = JSON.parse(userStr);
      if (user && user.id) return user.id;
    }
    const token = localStorage.getItem('safeconnect_token');
    if (token) {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.sub ? parseInt(payload.sub, 10) : null;
    }
  } catch (e) {
    return null;
  }
  return null;
}

export default function EmergencyDetails() {
  const { id } = useParams();
  const [emergency, setEmergency] = useState(null);
  const [responses, setResponses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [submittingResponse, setSubmittingResponse] = useState(false);
  const [offlineResolvePending, setOfflineResolvePending] = useState(false);
  const [pushStatus, setPushStatus] = useState('');

  const isOnline = useOnlineStatus();
  const currentUserId = getCurrentUserId();

  const { connectionState, latestLocation, emergencyEnded, statusMessage } = useEmergencySocket(
    emergency?.status === 'ACTIVE' ? id : null
  );

  const fetchEmergency = async () => {
    try {
      const response = await getEmergencyById(id);
      setEmergency(response.data.emergency);

      try {
        const respRes = await getEmergencyResponses(id);
        setResponses(respRes.data.responses || []);
      } catch (err) {
        setResponses([]);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmergency();
  }, [id]);

  // Handle offline resolution retry when connection returns
  useEffect(() => {
    if (isOnline && offlineResolvePending && emergency?.status === 'ACTIVE') {
      setOfflineResolvePending(false);
      handleResolve();
    }
  }, [isOnline, offlineResolvePending, emergency]);

  // Automatically register Web Push subscription if supported
  useEffect(() => {
    registerServiceWorkerAndPush().then((res) => {
      if (res.success) {
        setPushStatus('Push Notifications Enabled');
      }
    });
  }, []);

  const handleResolve = async () => {
    if (!isOnline) {
      setOfflineResolvePending(true);
      return;
    }
    try {
      await resolveEmergency(id);
      setOfflineResolvePending(false);
      fetchEmergency();
    } catch (err) {
      alert(err.message || 'Unable to resolve emergency');
    }
  };

  const handleCancel = async () => {
    if (!isOnline) {
      alert('Internet connection lost. Please connect to cancel emergency.');
      return;
    }
    await cancelEmergency(id);
    fetchEmergency();
  };

  const handleHelp = async () => {
    if (submittingResponse) return;
    if (!isOnline) {
      alert('Internet connection lost. Please connect to send your response.');
      return;
    }
    try {
      setSubmittingResponse(true);
      const result = await createEmergencyResponse(id, { message: message || 'I can help' });
      setMessage('');
      alert(result.message || 'Response submitted successfully! You are now an authorized responder.');
      await fetchEmergency();
    } catch (error) {
      alert(error.message || 'Unable to submit response');
    } finally {
      setSubmittingResponse(false);
    }
  };

  if (loading) return <Loading />;
  if (!emergency) return <div className="page-shell"><div className="panel-card">Emergency not found.</div></div>;

  const isOwner = currentUserId && emergency.user_id === currentUserId;
  const isEmergencyActive = emergency.status === 'ACTIVE' && !emergencyEnded;
  const myResponse = responses.find((r) => r.responder_id === currentUserId);
  const hasResponded = Boolean(myResponse);

  // Stale location check (> 2 minutes old)
  let isStaleLocation = false;
  let timeAgoText = '';
  if (latestLocation?.timestamp) {
    const elapsedMs = Date.now() - new Date(latestLocation.timestamp).getTime();
    const elapsedMins = Math.floor(elapsedMs / 60000);
    if (elapsedMins >= 2) {
      isStaleLocation = true;
      timeAgoText = `Last location received ${elapsedMins} minute${elapsedMins === 1 ? '' : 's'} ago`;
    }
  }

  const getStatusBadge = () => {
    if (!isOnline) {
      return <span className="status-indicator disconnected">🔴 Internet Connection Lost</span>;
    }
    if (!isEmergencyActive) {
      return <span className="status-indicator ended">⚪ Emergency Ended / Stopped</span>;
    }
    if (isStaleLocation) {
      return <span className="status-indicator connecting">🟡 {timeAgoText}</span>;
    }
    if (connectionState === 'CONNECTED') {
      return <span className="status-indicator active">🟢 Live location active</span>;
    }
    if (connectionState === 'CONNECTING') {
      return <span className="status-indicator connecting">🟡 Connecting to live location...</span>;
    }
    if (connectionState === 'RECONNECTING') {
      return <span className="status-indicator reconnecting">🟡 Connection interrupted. Reconnecting...</span>;
    }
    return <span className="status-indicator disconnected">🔴 Live location disconnected</span>;
  };

  return (
    <div className="page-shell">
      {/* ── Network Connection Status Banner (Phase 9) ── */}
      {!isOnline && (
        <div className="network-offline-banner" style={{ background: '#ef4444', color: 'white', padding: '0.6rem 1rem', borderRadius: '10px', marginBottom: '1rem', fontWeight: 600, fontSize: '0.9rem' }}>
          🔴 Internet Connection Lost — Offline mode active. Pending updates will synchronize when connection recovers.
        </div>
      )}

      <div className="panel-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
          <h1>{emergency.emergency_type}</h1>
          {!isEmergencyActive && (
            <span className="status-pill ended" style={{ background: 'rgba(239, 68, 68, 0.15)', color: '#fca5a5', padding: '0.35rem 0.85rem', borderRadius: '999px', fontWeight: 600 }}>
              ✅ Emergency Resolved
            </span>
          )}
        </div>
        <p>{emergency.description}</p>
        <div className="detail-grid">
          <div><strong>Status:</strong> {emergencyEnded ? 'RESOLVED' : emergency.status}</div>
          <div><strong>Priority:</strong> {emergency.priority}</div>
          <div><strong>Created:</strong> {new Date(emergency.created_at).toLocaleString()}</div>
          <div><strong>Resolved:</strong> {emergency.resolved_at ? new Date(emergency.resolved_at).toLocaleString() : 'N/A'}</div>
        </div>

        {/* ── Responders Summary Banner ── */}
        {responses.length > 0 && (
          <div className="responders-banner" style={{ background: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.25)', borderRadius: '12px', padding: '0.75rem 1rem', margin: '0.75rem 0' }}>
            <div style={{ fontWeight: 600, color: '#60a5fa' }}>
              🤝 {responses.length} {responses.length === 1 ? 'person is' : 'people are'} helping
            </div>
            <div style={{ fontSize: '0.82rem', color: '#94a3b8', marginTop: '0.25rem' }}>
              Responders: {responses.map((r) => r.responder_name).join(', ')}
            </div>
          </div>
        )}

        {/* ── Phase 4 & Phase 5 & Phase 9: Live Map + Real-Time Location + Stale Status ── */}
        <div className="section-gap">
          <div className="live-map-header-row" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem', flexWrap: 'wrap', gap: '0.5rem' }}>
            <h3 style={{ margin: 0 }}>Live Emergency Map</h3>
            {getStatusBadge()}
          </div>

          <LiveEmergencyMap
            latitude={latestLocation?.latitude}
            longitude={latestLocation?.longitude}
            emergencyStatus={isEmergencyActive ? 'ACTIVE' : 'RESOLVED'}
            accuracy={latestLocation?.accuracy}
            timestamp={latestLocation?.timestamp}
          />

          {statusMessage && (
            <div className="tracking-status-text" style={{ marginTop: '0.5rem' }}>
              {statusMessage}
            </div>
          )}

          {isStaleLocation && (
            <div className="tracking-status-text" style={{ color: '#fbbf24', marginTop: '0.25rem' }}>
              ⚠️ Location updates are delayed. {timeAgoText}.
            </div>
          )}
        </div>

        {/* ── Phase 7 & Phase 9: Emergency Owner "REACHED SAFELY" Action ── */}
        {isOwner && isEmergencyActive && (
          <div className="button-row" style={{ marginTop: '1.25rem' }}>
            <button className="button button-secondary" type="button" onClick={handleResolve}>
              {offlineResolvePending ? 'Waiting for connection to resolve...' : 'REACHED SAFELY'}
            </button>
            <button className="button button-danger" type="button" onClick={handleCancel}>
              Cancel emergency
            </button>
          </div>
        )}

        {/* ── Phase 6: Responder "I CAN HELP" Action ── */}
        {!isOwner && isEmergencyActive && (
          <div className="section-gap" style={{ borderTop: '1px solid rgba(255, 255, 255, 0.1)', paddingTop: '1rem' }}>
            <h3>Respond</h3>
            {hasResponded ? (
              <div className="status-indicator active" style={{ fontSize: '0.95rem', padding: '0.6rem 1.2rem' }}>
                ✓ You are helping
              </div>
            ) : (
              <div>
                <textarea
                  value={message}
                  onChange={(event) => setMessage(event.target.value)}
                  rows="2"
                  placeholder="I can help"
                  className="text-input"
                  disabled={submittingResponse || !isOnline}
                />
                <div className="button-row" style={{ marginTop: '0.5rem' }}>
                  <button
                    className="button button-primary"
                    type="button"
                    onClick={handleHelp}
                    disabled={submittingResponse || !isOnline}
                  >
                    {submittingResponse ? 'Submitting...' : 'I CAN HELP'}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
