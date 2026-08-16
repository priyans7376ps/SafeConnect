import { useEffect, useState } from 'react';
import Button from '../components/common/Button';
import EmptyState from '../components/common/EmptyState';
import { useAuth } from '../hooks/useAuth';
import api from '../services/api';

export default function TrustedContacts() {
  const { user } = useAuth();
  const [contacts, setContacts] = useState([]);
  const [form, setForm] = useState({ name: '', phone: '', email: '', relationship: '', is_primary: false });
  const [loading, setLoading] = useState(false);

  const fetchContacts = async () => {
    try {
      setLoading(true);
      const { data } = await api.get('/contacts');
      setContacts(data.data.contacts || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchContacts();
  }, []);

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target;
    setForm((current) => ({ ...current, [name]: type === 'checkbox' ? checked : value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    await api.post('/contacts', form);
    setForm({ name: '', phone: '', email: '', relationship: '', is_primary: false });
    fetchContacts();
  };

  const handleDelete = async (id) => {
    await api.delete(`/contacts/${id}`);
    fetchContacts();
  };

  return (
    <div className="page-shell">
      <div className="page-header">
        <div>
          <p className="eyebrow">Safety circle</p>
          <h1>Trusted contacts</h1>
        </div>
      </div>

      <div className="panel-card section-gap">
        <h3>Add contact</h3>
        <form className="card-form" onSubmit={handleSubmit}>
          <div className="field-group">
            <label className="field-label">Name</label>
            <input className="input" name="name" value={form.name} onChange={handleChange} />
          </div>
          <div className="field-group">
            <label className="field-label">Phone</label>
            <input className="input" name="phone" value={form.phone} onChange={handleChange} />
          </div>
          <div className="field-group">
            <label className="field-label">Email</label>
            <input className="input" name="email" value={form.email} onChange={handleChange} />
          </div>
          <div className="field-group">
            <label className="field-label">Relationship</label>
            <input className="input" name="relationship" value={form.relationship} onChange={handleChange} />
          </div>
          <label className="checkbox-row">
            <input type="checkbox" name="is_primary" checked={form.is_primary} onChange={handleChange} />
            Primary contact
          </label>
          <Button type="submit">Add contact</Button>
        </form>
      </div>

      <div className="panel-card section-gap">
        <h3>Your contacts</h3>
        {loading ? <p>Loading...</p> : contacts.length ? (
          contacts.map((contact) => (
            <div className="info-card" key={contact.id}>
              <div className="card-header-row">
                <strong>{contact.name}</strong>
                {contact.is_primary && <span className="status-pill active">Primary</span>}
              </div>
              <p>{contact.relationship}</p>
              <p>{contact.phone}</p>
              <p>{contact.email || 'No email provided'}</p>
              <div className="button-row">
                <button className="button button-secondary" type="button" onClick={() => handleDelete(contact.id)}>Remove</button>
              </div>
            </div>
          ))
        ) : (
          <EmptyState title="No trusted contacts" message="Add trusted contacts to your safety plan." />
        )}
      </div>
    </div>
  );
}
