import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import AuthLayout from '../../components/common/AuthLayout';
import { useAuth } from '../../hooks/useAuth';

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [form, setForm] = useState({ email: '', password: '' });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');

    if (!form.email || !form.password) {
      setError('Please enter both email and password');
      return;
    }

    try {
      setIsSubmitting(true);
      await login(form);
      navigate('/dashboard');
    } catch (err) {
      setError(err.message || 'Login failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Sign in to SafeConnect"
      footerText="Need an account?"
      footerLinkText="Create one"
      footerLinkTo="/register"
    >
      <form onSubmit={handleSubmit} className="auth-form-body">
        {/* Email */}
        <div className="auth-field-group">
          <label htmlFor="login-email" className="auth-field-label">Email</label>
          <input
            id="login-email"
            type="email"
            name="email"
            value={form.email}
            onChange={handleChange}
            placeholder="username@email.com"
            required
            className="auth-input"
          />
        </div>

        {/* Password + Forgot */}
        <div className="auth-field-group">
          <div className="auth-label-row">
            <label htmlFor="login-password" className="auth-field-label">Password</label>
            <Link to="/forgot-password" className="auth-forgot-link">Forgot password?</Link>
          </div>
          <input
            id="login-password"
            type="password"
            name="password"
            value={form.password}
            onChange={handleChange}
            placeholder="••••••••"
            required
            className="auth-input"
          />
        </div>

        {error && <div className="auth-error-msg" role="alert">{error}</div>}

        <button type="submit" disabled={isSubmitting} className="auth-submit-btn">
          {isSubmitting ? 'Signing in…' : 'Login'}
        </button>
      </form>
    </AuthLayout>
  );
}
