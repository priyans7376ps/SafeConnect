import { NavLink } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import Button from './Button';

export default function Navbar() {
  const { user, logout } = useAuth();

  return (
    <header className="topbar">
      <div className="brand-wrap">
        <div className="brand-mark">S</div>
        <div>
          <div className="brand-title">SafeConnect</div>
          <small className="brand-subtitle">Emergency dashboard</small>
        </div>
      </div>

      <nav className="topnav">
        <NavLink to="/dashboard">Dashboard</NavLink>
        <NavLink to="/emergency">Emergency</NavLink>
        <NavLink to="/live-location">Location</NavLink>
        <NavLink to="/notifications">Notifications</NavLink>
        <NavLink to="/profile">Profile</NavLink>
      </nav>

      <div className="user-actions">
        {user ? <span className="user-badge">{user.name}</span> : null}
        <Button variant="secondary" onClick={logout}>Logout</Button>
      </div>
    </header>
  );
}
