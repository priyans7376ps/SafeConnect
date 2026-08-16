import { useState } from 'react';
import Button from '../common/Button';

export default function ProfileForm({ user, onSubmit, isSubmitting }) {
  const [form, setForm] = useState({
    name: user?.name || '',
    email: user?.email || '',
    phone: user?.phone || '',
  });

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    onSubmit(form);
  };

  return (
    <form className="card-form" onSubmit={handleSubmit}>
      <div className="field-group">
        <label className="field-label">Name</label>
        <input name="name" className="input" value={form.name} onChange={handleChange} />
      </div>
      <div className="field-group">
        <label className="field-label">Email</label>
        <input name="email" type="email" className="input" value={form.email} onChange={handleChange} />
      </div>
      <div className="field-group">
        <label className="field-label">Phone</label>
        <input name="phone" className="input" value={form.phone} onChange={handleChange} />
      </div>
      <Button type="submit" disabled={isSubmitting}>{isSubmitting ? 'Saving...' : 'Save changes'}</Button>
    </form>
  );
}
