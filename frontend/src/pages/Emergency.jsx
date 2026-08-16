import { useEffect, useRef } from 'react';
import EmergencyButton from '../components/emergency/EmergencyButton';
import EmergencyCard from '../components/emergency/EmergencyCard';
import EmergencyForm from '../components/emergency/EmergencyForm';
import Loading from '../components/common/Loading';
import EmptyState from '../components/common/EmptyState';
import { useEmergency } from '../hooks/useEmergency';
import { useLocationTracking } from '../hooks/useLocationTracking';

export default function Emergency() {
  const { emergencies, loading, refreshEmergencies, create, activeEmergency, resolve, cancel } =
    useEmergency();
  const { tracking, gpsError, lastCoords, startTracking, stopTracking } = useLocationTracking();

  // Track whether we are currently submitting a create action
  const submittingRef = useRef(false);

  // ── Lifecycle: start/stop tracking as activeEmergency changes ─────────────
  useEffect(() => {
    if (activeEmergency && activeEmergency.status === 'ACTIVE') {
      startTracking(activeEmergency.id);
    } else {
      stopTracking();
    }
    // Cleanup when component unmounts — clears the GPS watcher
    return () => {
      stopTracking();
    };
  }, [activeEmergency?.id, activeEmergency?.status]);

  // ── Load on mount ──────────────────────────────────────────────────────────
  useEffect(() => {
    refreshEmergencies();
  }, []);

  // ── Handlers ──────────────────────────────────────────────────────────────
  const handleCreate = async (payload) => {
    if (submittingRef.current) return;
    submittingRef.current = true;
    try {
      await create(payload);
    } finally {
      submittingRef.current = false;
    }
  };

  const handleResolve = async () => {
    stopTracking(); // stop GPS before API call so no stale updates are sent
    await resolve(activeEmergency.id);
  };

  const handleCancel = async () => {
    stopTracking();
    await cancel(activeEmergency.id);
  };

  // ── Tracking status banner ─────────────────────────────────────────────────
  const TrackingBanner = () => {
    if (!activeEmergency) return null;
    return (
      <div className={`tracking-banner ${tracking ? 'tracking-active' : 'tracking-inactive'}`}>
        <span className="tracking-dot" aria-hidden="true" />
        <span className="tracking-label">
          Location Sharing:{' '}
          <strong>{tracking ? 'ACTIVE' : 'INACTIVE'}</strong>
        </span>
        {tracking && <span className="tracking-status-text">Live location sharing is active.</span>}
        {!tracking && activeEmergency.status === 'ACTIVE' && (
          <span className="tracking-status-text">Live location sharing has stopped.</span>
        )}
        {gpsError && <span className="tracking-error">{gpsError}</span>}
        {tracking && lastCoords && (
          <span className="tracking-coords">
            {lastCoords.latitude.toFixed(5)}, {lastCoords.longitude.toFixed(5)}
            {lastCoords.accuracy ? ` (±${Math.round(lastCoords.accuracy)}m)` : ''}
          </span>
        )}
      </div>
    );
  };

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="page-shell">
      <div className="page-header">
        <div>
          <p className="eyebrow">Emergency</p>
          <h1>Emergency center</h1>
        </div>
        <EmergencyButton
          label="SOS"
          onClick={() =>
            handleCreate({
              emergency_type: 'Medical',
              description: 'Immediate SOS requested',
              priority: 'CRITICAL',
            })
          }
        />
      </div>

      <div className="panel-card section-gap">
        <h3>Create emergency</h3>
        <EmergencyForm onSubmit={handleCreate} isSubmitting={submittingRef.current} />
      </div>

      <div className="panel-card section-gap">
        <h3>Active alert</h3>
        {activeEmergency ? (
          <div>
            <EmergencyCard emergency={activeEmergency} />
            <TrackingBanner />
            <div className="button-row">
              <button
                className="button button-secondary"
                type="button"
                onClick={handleResolve}
              >
                Reached safely
              </button>
              <button
                className="button button-danger"
                type="button"
                onClick={handleCancel}
              >
                Cancel emergency
              </button>
            </div>
          </div>
        ) : (
          <EmptyState title="No active emergency" message="Create an emergency or wait for updates." />
        )}
      </div>

      <div className="panel-card section-gap">
        <h3>Recent emergencies</h3>
        {loading ? (
          <Loading />
        ) : emergencies.length ? (
          emergencies.map((emergency) => (
            <EmergencyCard key={emergency.id} emergency={emergency} />
          ))
        ) : (
          <EmptyState title="No incidents" message="Your emergency history appears empty." />
        )}
      </div>
    </div>
  );
}
