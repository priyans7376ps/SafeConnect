export default function LocationStatus({ location }) {
  if (!location) return <span className="status-pill neutral">Location unavailable</span>;

  return <span className="status-pill active">Tracking</span>;
}
