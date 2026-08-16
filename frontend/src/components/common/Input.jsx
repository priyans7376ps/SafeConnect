export default function Input({ label, type = 'text', value, onChange, name, placeholder, required = false, error, id }) {
  const inputId = id || (name ? `input-${name}` : undefined);
  return (
    <div className="field-group">
      {label && <label htmlFor={inputId} className="field-label">{label}</label>}
      <input
        id={inputId}
        type={type}
        name={name}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required={required}
        className={`input ${error ? 'input-error' : ''}`.trim()}
      />
      {error && <small className="field-error">{error}</small>}
    </div>
  );
}
