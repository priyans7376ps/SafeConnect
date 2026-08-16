import { useState } from 'react';
import Button from '../common/Button';
import Input from '../common/Input';

export default function EmergencyForm({ onSubmit, isSubmitting, initialValues }) {
  const [form, setForm] = useState(
    initialValues || {
      emergency_type: 'Medical',
      description: '',
      priority: 'HIGH',
    }
  );

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
        <label className="field-label">Emergency type</label>
        <select name="emergency_type" value={form.emergency_type} onChange={handleChange} className="input">
          <option value="Medical">Medical</option>
          <option value="Security">Security</option>
          <option value="Fire">Fire</option>
          <option value="Natural Disaster">Natural Disaster</option>
        </select>
      </div>

      <div className="field-group">
        <label className="field-label">Description</label>
        <textarea
          name="description"
          value={form.description}
          onChange={handleChange}
          placeholder="Describe the emergency"
          className="textarea"
          rows="4"
        />
      </div>

      <div className="field-group">
        <label className="field-label">Priority</label>
        <select name="priority" value={form.priority} onChange={handleChange} className="input">
          <option value="LOW">Low</option>
          <option value="MEDIUM">Medium</option>
          <option value="HIGH">High</option>
          <option value="CRITICAL">Critical</option>
        </select>
      </div>

      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Submitting...' : 'Create emergency'}
      </Button>
    </form>
  );
}
