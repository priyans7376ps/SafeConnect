import Button from '../common/Button';

export default function EmergencyButton({ label = 'SOS', onClick }) {
  return <Button className="emergency-button" variant="danger" onClick={onClick}>{label}</Button>;
}
