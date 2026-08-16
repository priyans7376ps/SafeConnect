import { NavLink } from 'react-router-dom';

const links = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/emergency', label: 'Emergency' },
  { to: '/live-location', label: 'Live Location' },
  { to: '/trusted-contacts', label: 'Trusted Contacts' },
  { to: '/notifications', label: 'Notifications' },
  { to: '/history', label: 'History' },
  { to: '/profile', label: 'Profile' },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-title">Navigation</div>
      <ul className="sidebar-list">
        {links.map((item) => (
          <li key={item.to}>
            <NavLink className={({ isActive }) => (isActive ? 'sidebar-link active' : 'sidebar-link')} to={item.to}>
              {item.label}
            </NavLink>
          </li>
        ))}
      </ul>
    </aside>
  );
}
