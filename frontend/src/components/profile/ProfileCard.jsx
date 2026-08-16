export default function ProfileCard({ user }) {
  if (!user) return null;

  return (
    <div className="info-card">
      <h3>Profile</h3>
      <p><strong>Name:</strong> {user.name}</p>
      <p><strong>Email:</strong> {user.email}</p>
      <p><strong>Phone:</strong> {user.phone}</p>
      <p><strong>Status:</strong> {user.is_active ? 'Active' : 'Inactive'}</p>
    </div>
  );
}
