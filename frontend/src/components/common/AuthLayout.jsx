import { Link } from 'react-router-dom';

export default function AuthLayout({
  title,
  subtitle,
  children,
  footerText,
  footerLinkText,
  footerLinkTo,
  showForgotPassword = false,
}) {
  return (
    <div className="auth-page">
      <div className="auth-container">

        {/* ── Left Panel: Branding ── */}
        <div className="auth-brand-section">
          <div className="auth-brand-content">

            {/* Logo + Name */}
            <div className="auth-brand-header">
              <div className="auth-logo-icon" aria-hidden="true">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" strokeWidth="2.5"
                  strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                  <path d="M9 12l2 2 4-4" />
                </svg>
              </div>
              <span className="auth-brand-name">SafeConnect</span>
            </div>

            {/* Badge + Headline */}
            <div className="auth-hero-text">
              <span className="auth-badge">COMMUNITY NETWORK SECURITY</span>
              <h1 className="auth-tagline">
                Stay connected.<br />
                <span className="text-gradient">Stay safe.</span>
              </h1>
              <p className="auth-supporting-text">
                One community. One tap. Help when and where it matters most.
              </p>
            </div>

            {/* Feature List */}
            <div className="auth-features">
              <div className="auth-feature-item">
                <div className="feature-icon" aria-hidden="true">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                    <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
                  </svg>
                </div>
                <div>
                  <strong>Instant SOS Broadcast</strong>
                  <p>Alert nearby community members instantly in emergencies</p>
                </div>
              </div>

              <div className="auth-feature-item">
                <div className="feature-icon" aria-hidden="true">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 22s-8-4.5-8-11.8A8 8 0 0 1 12 2a8 8 0 0 1 8 8.2c0 7.3-8 11.8-8 11.8z"/>
                    <circle cx="12" cy="10" r="3"/>
                  </svg>
                </div>
                <div>
                  <strong>Live Location Protection</strong>
                  <p>Private location updates during active emergencies only</p>
                </div>
              </div>

              <div className="auth-feature-item">
                <div className="feature-icon" aria-hidden="true">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                    <circle cx="9" cy="7" r="4"/>
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                    <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                  </svg>
                </div>
                <div>
                  <strong>Team Messaging</strong>
                  <p>Coordinate with your trusted contacts and community group</p>
                </div>
              </div>
            </div>

          </div>
        </div>

        {/* ── Right Panel: Auth Card ── */}
        <div className="auth-form-section">
          <div className="auth-card">
            <div className="auth-card-header">
              <h2>{title}</h2>
              <p className="auth-subtitle">{subtitle}</p>
            </div>

            {children}

            {footerText && (
              <p className="auth-footer">
                {footerText}{' '}
                <Link to={footerLinkTo} className="auth-footer-link">
                  {footerLinkText}
                </Link>
              </p>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
