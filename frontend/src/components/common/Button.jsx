export default function Button({ children, type = 'button', variant = 'primary', onClick, disabled = false, className = '' }) {
  const styles = {
    primary: 'button-primary',
    secondary: 'button-secondary',
    danger: 'button-danger',
  };

  return (
    <button type={type} className={`button ${styles[variant]} ${className}`.trim()} onClick={onClick} disabled={disabled}>
      {children}
    </button>
  );
}
