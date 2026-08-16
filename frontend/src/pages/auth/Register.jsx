import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AuthLayout from '../../components/common/AuthLayout';
import { useAuth } from '../../hooks/useAuth';

export default function Register() {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [form, setForm] = useState({ name: '', email: '', phone: '', password: '', confirmPassword: '' });
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');

    if (!form.name || !form.email || !form.phone || !form.password) {
      setError('All fields are required');
      return;
    }

    if (form.password !== form.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    try {
      setIsSubmitting(true);
      await register({
        name: form.name,
        email: form.email,
        phone: form.phone,
        password: form.password,
      });
      navigate('/dashboard');
    } catch (err) {
      setError(err.message || 'Registration failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AuthLayout
      title="Create account"
      subtitle="Join SafeConnect"
      footerText="Already have an account?"
      footerLinkText="Login"
      footerLinkTo="/login"
    >
      <form onSubmit={handleSubmit} className="auth-form-body">
        <div className="auth-field-group">
          <label htmlFor="reg-name" className="auth-field-label">Full name</label>
          <input id="reg-name" name="name" value={form.name} onChange={handleChange}
            placeholder="Your full name" required className="auth-input" />
        </div>

        <div className="auth-field-group">
          <label htmlFor="reg-email" className="auth-field-label">Email</label>
          <input id="reg-email" type="email" name="email" value={form.email} onChange={handleChange}
            placeholder="you@example.com" required className="auth-input" />
        </div>

        <div className="auth-field-group">
          <label htmlFor="reg-phone" className="auth-field-label">Phone</label>
          <input id="reg-phone" name="phone" value={form.phone} onChange={handleChange}
            placeholder="+1 555 123 4567" required className="auth-input" />
        </div>

        <div className="auth-field-group">
          <label htmlFor="reg-password" className="auth-field-label">Password</label>
          <input id="reg-password" type="password" name="password" value={form.password} onChange={handleChange}
            placeholder="Minimum 6 characters" required className="auth-input" />
        </div>

        <div className="auth-field-group">
          <label htmlFor="reg-confirm" className="auth-field-label">Confirm password</label>
          <input id="reg-confirm" type="password" name="confirmPassword" value={form.confirmPassword} onChange={handleChange}
            placeholder="Repeat password" required className="auth-input" />
        </div>

        {error && <div className="auth-error-msg" role="alert">{error}</div>}

        <button type="submit" disabled={isSubmitting} className="auth-submit-btn">
          {isSubmitting ? 'Creating account…' : 'Register'}
        </button>
      </form>
    </AuthLayout>
  );
}
