export default function LocationCard({ location }) {
  if (!location) return null;

  return (
    <div className="info-card">
      <h3>Location</h3>
      <p>Latitude: {location.latitude}</p>
      <p>Longitude: {location.longitude}</p>
      <p>Accuracy: {location.accuracy || 'N/A'}m</p>
      <p>Address: {location.address || 'Not available'}</p>
    </div>
  );
}
