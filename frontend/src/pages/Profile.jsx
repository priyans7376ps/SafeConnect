import { useEffect, useState } from 'react';
import ProfileCard from '../components/profile/ProfileCard';
import ProfileForm from '../components/profile/ProfileForm';
import Loading from '../components/common/Loading';
import { useAuth } from '../hooks/useAuth';
import api from '../services/api';

export default function Profile() {
  const { user, setError } = useAuth();
  const [profile, setProfile] = useState(user);
  const [loading, setLoading] = useState(true);

  const fetchProfile = async () => {
    try {
      const { data } = await api.get('/users/profile');
      setProfile(data.data.user);
    } catch (err) {
      setError(err.message || 'Profile unavailable');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  const handleUpdate = async (values) => {
    const { data } = await api.put('/users/profile', values);
    setProfile(data.data.user);
  };

  if (loading) return <Loading />;

  return (
    <div className="page-shell">
      <div className="page-header">
        <div>
          <p className="eyebrow">Account</p>
          <h1>Profile</h1>
        </div>
      </div>

      <div className="profile-grid">
        <div className="panel-card"><ProfileCard user={profile} /></div>
        <div className="panel-card"><ProfileForm user={profile} onSubmit={handleUpdate} /></div>
      </div>
    </div>
  );
}
